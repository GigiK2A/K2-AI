"""SIGNALS — SSOT delle regex di governo della chat K-BOT.

Prima vivevano sparse in 3 file (message.py, prompts.py, quality_gate.py) con
divergenze già costate care: il bug «NON ho informazioni sufficienti» matchato
come readiness (fallback che forzava il report proprio quando il bot gestiva
bene l'incertezza) nasceva esattamente da una regex non testata in un file
laterale. Qui: una definizione, un test, tutti i consumatori importano da qui.

Testato in tests/test_intake_regression.py.
"""
from __future__ import annotations

import json
import re
from typing import Optional

# --- Trigger "procedi": l'utente chiede esplicitamente di generare ------------------
# PROCEDI_RE è VOLUTAMENTE largo (bypass soft del gate primo-turno: un falso positivo
# costa poco). Per l'ENFORCEMENT DURO (summary forzato dal server) serve la variante
# STRETTA sotto: qui "la procedura di licenziamento" o "come procediamo?" matcherebbero.
PROCEDI_RE = re.compile(
    r"\b(vai|proced\w*|fai il report|fammi il report|voglio il report( subito)?|"
    r"basta domande|salta le domande|fai senza domande|ok proced\w*|dai proced\w*)\b", re.I)

# Trigger STRETTO (eval 100, 17 lug: 7× 'dati… procedi' ignorati da gpt-oss → il summary
# va FORZATO dal server): richiesta esplicita di report, oppure imperativo procedi/vai
# come frase a sé (inizio/fine messaggio o dopo punteggiatura), MAI dentro sostantivi
# ('procedura') né in domande ('come procediamo?').
PROCEDI_HARD_RE = re.compile(
    r"(fai (?:il|un) report|fammi (?:il|un) report|voglio il report|genera(?:mi)? il report|"
    r"basta domande|salta le domande|fai senza domande|"
    r"(?:^|[.!;\n]\s*)(?:ok[, ]+|dai[, ]+|allora[, ]+)?(?:procedi(?:amo)?(?: pure)?|vai(?: pure)?)\s*[.!]?\s*$)",
    re.I)

# --- Readiness dichiarata dal bot ("ho abbastanza informazioni") ---------------------
READY_RE = re.compile(
    r"(informazion\w+ sufficient\w+|sufficient\w+ per (produrre|preparare|generare|una prima)|"
    r"procedo con il report|posso (gi[àa] )?prepar\w+ il report|genero il report|"
    r"sto generando|ho abbastanza (informazioni|dati)|dati sufficient\w+)", re.I)

# --- GUARDIA NEGAZIONE: "NON ho ancora informazioni sufficienti" NON è readiness -----
NOT_READY_RE = re.compile(
    r"non\s+(?:ho|ha|abbiamo|dispongo|disponiamo)\s+(?:ancora\s+)?(?:abbastanza\s+|sufficient\w+\s+)?"
    r"(?:informazioni|dati|elementi)|informazioni\s+non\s+(?:ancora\s+)?sufficient\w+|"
    r"non\s+(?:sono|bastano)\s+(?:ancora\s+)?sufficient\w+|mancano\s+(?:ancora\s+)?(?:informazioni|dati|elementi)|"
    r"prima\s+devo\s+chiarire|troppo\s+presto\s+per", re.I)

# --- Urgenza / crisi di continuità dichiarata dall'utente ----------------------------
# NB: niente marker DEBOLI tipo 'subito'/'quanto prima' da soli (eval-100 #92: «devo
# rispondere subito?» in una domanda semplice attivava il gate urgenza → contro-domanda
# invece della risposta). Le crisi vere portano segnali forti (sotto).
URGENT_RE = re.compile(
    r"\b(urgen\w+|emergenz\w+|entro (?:\d+|pochi|due|tre|dieci) "
    r"(?:or[ae]|giorn\w+|settiman\w+)|scaden\w+|continuit[àa]|rischi\w* di ferma\w+|"
    r"si ferma|blocc\w+|non ri\w+ a pagare|stipend\w+|liquidit[àa]|ricoverat\w+|"
    r"indisponibil\w+|nessuno (?:ha accesso|pu[òo]|riesce)|non abbiamo accesso|crisi)\b", re.I)

# --- Blocco CONSULENZA_SUMMARY (trigger di generazione) ------------------------------
# TOLLERANTE al formato: i modelli locali emettono spesso il blocco INLINE
# ("START {json} END" su una riga) — il vecchio regex pretendeva \n e l'estrazione
# falliva ANCHE col blocco presente (root cause del "report mai generato").
SUMMARY_RE = re.compile(r"CONSULENZA_SUMMARY_START\s*([\s\S]*?)\s*CONSULENZA_SUMMARY_END")

# --- Blocco DIAGNOSI_STATO (stato diagnostico esplicito, per-turno) -------------------
# Il bot mantiene le proprie ipotesi FUORI dalla propria "testa": le emette in un
# blocco nascosto a ogni turno, il server le persiste e le re-inietta nel prompt del
# turno successivo. Senza questo, ogni turno riparte da zero: oscillazioni, domande
# ripetute, stop rule "a sensazione".
DIAGNOSI_RE = re.compile(r"DIAGNOSI_STATO_START\s*([\s\S]*?)\s*DIAGNOSI_STATO_END")


def extract_json_block(regex: re.Pattern, text: str) -> Optional[dict]:
    """Estrae e parsa il primo blocco JSON delimitato dal regex. None se assente/rotto."""
    m = regex.search(text or "")
    if not m:
        return None
    raw = m.group(1).strip()
    s, e = raw.find("{"), raw.rfind("}")
    if s < 0 or e <= s:
        return None
    try:
        v = json.loads(raw[s:e + 1])
        return v if isinstance(v, dict) else None
    except json.JSONDecodeError:
        return None


def strip_block(regex: re.Pattern, text: str) -> str:
    return regex.sub("", text or "").strip()


# --- Gestione TOLLERANTE dei blocchi malformati (eval 100, 17 lug) --------------------
# gpt-oss a volte emette: (a) START senza END (troncamento max_tokens) → il regex a
# coppia non matcha e il blocco LEAKA in chat; (b) JSON + END senza START (orfano) →
# leak E summary perso. Qui: estrazione che recupera l'orfano e strip che rimuove
# entrambe le forme + qualunque riga residua col nome del marker (zero leak garantito).

def _try_parse_before(text: str, end_idx: int) -> Optional[tuple[int, dict]]:
    """Prova a parsare un oggetto JSON che TERMINA subito prima di end_idx: cammina
    all'indietro sulle '{' candidate (max 25 tentativi). Ritorna (start_idx, dict)."""
    prefix = text[:end_idx].rstrip()
    for _ in range(25):
        i = prefix.rfind("{")
        if i < 0:
            return None
        try:
            v = json.loads(prefix[i:])
            return (i, v) if isinstance(v, dict) else None
        except json.JSONDecodeError:
            prefix = prefix[:i]
    return None


def extract_block_tolerant(marker: str, regex: re.Pattern, text: str) -> Optional[dict]:
    """Come extract_json_block, ma recupera anche il blocco ORFANO (END senza START)
    e quello troncato con JSON comunque completo (START senza END)."""
    t = text or ""
    v = extract_json_block(regex, t)
    if v is not None:
        return v
    end = t.find(f"{marker}_END")
    if end >= 0:
        hit = _try_parse_before(t, end)
        if hit:
            return hit[1]
    start = t.find(f"{marker}_START")
    if start >= 0:
        raw = t[start + len(marker) + 6:]
        s, e = raw.find("{"), raw.rfind("}")
        if 0 <= s < e:
            try:
                v = json.loads(raw[s:e + 1])
                return v if isinstance(v, dict) else None
            except json.JSONDecodeError:
                return None
    return None


def strip_block_tolerant(marker: str, regex: re.Pattern, text: str) -> str:
    """Strip a prova di leak: blocco ben formato, START troncato (fino a fine testo),
    JSON+END orfano, e infine OGNI riga residua che contenga il nome del marker."""
    t = regex.sub("", text or "")
    start = t.find(f"{marker}_START")
    if start >= 0:
        t = t[:start]  # troncato: dal marker in poi è tutto macchina
    end = t.find(f"{marker}_END")
    if end >= 0:
        hit = _try_parse_before(t, end)
        cut_from = hit[0] if hit else max(t.rfind("\n", 0, end), 0)
        t = t[:cut_from] + t[end + len(marker) + 4:]
    if marker in t:  # backstop assoluto: via le righe residue col marker
        t = "\n".join(l for l in t.split("\n") if marker not in l)
    return t.strip()


def is_ready_declared(text: str) -> bool:
    """Readiness dichiarata E non negata — la coppia va SEMPRE usata insieme."""
    t = text or ""
    return bool(READY_RE.search(t)) and not NOT_READY_RE.search(t)
