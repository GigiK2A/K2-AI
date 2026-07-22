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

# --- HOLD: l'utente vuole CONTINUARE la consulenza, NON generare (ancora) il report --
# Volontà esplicita che DEVE bloccare qualunque trigger automatico di generazione (review
# "calo ordini": il bot avviava la generazione subito dopo che l'utente aveva chiesto di
# ragionare ancora). Preciso: ancorato a verbi di generazione NEGATI o a richieste esplicite
# di approfondire, per non matchare la parola "report" incidentale.
HOLD_RE = re.compile(
    r"\bnon\s+(?:fare|generare|generi|crear\w*|produrre|prepar\w+|voglio|serve|mi\s+serve|"
    r"partire\s+con|avviare)\b[^.!?\n]{0,30}?\b(?:report|documento|pdf|analisi|nulla|niente)\b|"
    r"\b(?:niente|nessun|senza|no)\s+report\b|"
    r"\bnon\s+(?:ancora|adesso|subito)\b[^.!?\n]{0,20}?\breport\b|"
    r"\b(?:continuiamo|continua|proseguiamo|prosegui)\b[^.!?\n]{0,25}?"
    r"\b(?:ragion\w+|analizz\w+|consulenza|a\s+capire|discutere|approfond\w+)\b|"
    r"\bvoglio\s+approfondire\b|\bapprofondiamo\b|"
    r"\bprima\s+(?:di\s+(?:fare|generare|prepar\w+|redigere)[^.!?\n]{0,20}?\breport\b|"
    r"la\s+diagnosi|capiamo|capire|arriv\w+\s+alla\s+diagnosi|ragioniamo)|"
    r"\baspett\w+\s+a\s+(?:fare|generare|prepar\w+)\b|"
    r"\bsolo\s+un\s+(?:consiglio|parere|opinione)\b|"
    r"\brest\w+\s+in\s+chat\b",
    re.I)


# --- Decisione STRATEGICA vs domanda TECNICA (review consulente-first) ----------------
# Il consulente NON deve entrare in modalità specialista solo perché compare una keyword di
# dominio (licenziamento, contratto, privacy, fiscale…). Distingue «DEVO decidere se fare X»
# (strategico → resta consulente di direzione) da «COME faccio X / cosa dice la norma»
# (tecnico → lo specialista è pertinente).
_DECISION_RE = re.compile(
    r"\b(vorrei|voglio|dovrei|dobbiamo\s+decidere|devo\s+decidere|sto\s+(?:pensando|valutando)|"
    r"stavo\s+pensando|valut\w+\s+se|mi\s+chiedo\s+se|non\s+so\s+se|convien\w+|mi\s+convien\w+|"
    r"ha\s+senso|vale\s+la\s+pena|è\s+meglio|sarebbe\s+meglio|meglio\b[^.?!]{0,40}\bo\b|"
    r"pensavo\s+di|ho\s+intenzione\s+di|intendo\b|progetto\s+di)\b", re.I)
_TECHNICAL_RE = re.compile(
    r"\b(come\s+(?:si\s+|posso\s+|faccio\s+|devo\s+)?(?:fa|faccio|procedo|licenzio|redig\w+|"
    r"compilo|present\w+|calcolo|scriv\w+|imposto)|qual['’\s]*è\s+la\s+procedura|"
    r"quali\s+documenti|che\s+documenti|cosa\s+serve\s+per|quali\s+sono\s+i\s+(?:passi|passaggi|"
    r"requisiti|termini|adempimenti)|entro\s+quando|quanto\s+tempo\s+ho|che\s+iter|"
    r"è\s+(?:legale|obbligatorio|possibile)\b|posso\s+legalmente|cosa\s+dice\s+(?:la\s+legge|"
    r"il\s+ccnl|la\s+norma|il\s+codice))\b", re.I)


def is_strategic_decision(text: str) -> bool:
    """True se il messaggio è una DECISIONE strategica («conviene / dovrei / voglio fare X?»)
    e NON una domanda tecnica di procedura («come faccio X / cosa dice la norma»). In tal
    caso il bot resta consulente e la keyword di dominio NON determina la risposta."""
    t = (text or "").strip()
    if not t:
        return False
    return bool(_DECISION_RE.search(t)) and not bool(_TECHNICAL_RE.search(t))


# --- Il cliente PROPONE una strategia (review "proposta = ipotesi") --------------------
# Verbi-proposta di azione strategica: la proposta NON va implementata al volo, va prima
# VALIDATA (perché? il problema è reale? quali alternative?). Cattura anche le forme
# dichiarative («apro una filiale») oltre alle decisionali (già in is_strategic_decision).
_PROPOSAL_RE = re.compile(
    r"\b(aprir\w+|apro\b|apriamo\b|acquist\w+|comprar\w+|rilevar\w+|assum\w+|assunzion\w+|"
    r"investir\w+|investiment\w+|licenzi\w+|espander\w+|espansion\w+|delocalizz\w+|"
    r"automatizz\w+|automazion\w+|fonder\w+|fusion\w+|internazionalizz\w+|"
    r"lanciar\w+\s+(?:un|una|il|la|nuovo|nuova)\s+(?:prodotto|servizio|linea)|"
    r"nuovo\s+prodotto|nuova\s+sede|nuova\s+filiale|entrare\s+(?:nel|in un)\s+mercato|"
    r"vender\w+\s+(?:l['’ ]?azienda|la\s+(?:mia\s+)?azienda|l['’ ]?attività|la\s+società|"
    r"il\s+ramo|la\s+quota))\b",
    re.I)


def proposes_strategy(text: str) -> bool:
    """True se il cliente propone una STRATEGIA/azione concreta (aprire, acquistare,
    investire, assumere, licenziare, espandersi, delocalizzare, automatizzare, lanciare,
    vendere l'azienda…) e NON è una pura domanda tecnica di esecuzione. Attiva la modalità
    VALUTAZIONE (valida l'ipotesi + alternative), non l'implementazione."""
    t = (text or "").strip()
    if not t:
        return False
    return bool(_PROPOSAL_RE.search(t)) and not bool(_TECHNICAL_RE.search(t))


def wants_to_continue(text: str) -> bool:
    """True se l'utente chiede ESPLICITAMENTE di continuare la consulenza / non generare
    ancora il report. Un PROCEDI esplicito nello stesso messaggio ha la precedenza (gestito
    dal chiamante)."""
    t = (text or "").strip()
    if not t:
        return False
    return bool(HOLD_RE.search(t))


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

# --- Citazioni normative con NUMERO specifico non verificato (17 lug) ----------------
# In chat (K-BOT lite) NON esiste grounding normativo come nell'8e (normattiva.py):
# se il modello cita 'art. 2099-c c.c.' o 'artt. 62-63 del CCNL' lo fa A MEMORIA, senza
# verifica — e un numero di articolo sbagliato è un danno concreto per l'utente (bug
# reale osservato: entrambi gli esempi erano inventati). Il pattern individua QUALSIASI
# articolo con numero seguito da una fonte normativa (CCNL/codice civile/decreto/legge);
# il trattino tra numeri può essere quello esotico che gpt-oss usa nei range (U+2011 ecc,
# stesso bug visto nei PDF) quindi il character class lo copre.
# 'art(?:icol[oi]|t)?' copre TUTTE le forme: art / art. / artt / artt. / articolo /
# articoli — bug reale 17 lug: 'articolo 2099-c del Codice Civile' (inventato) sfuggiva
# perché la regex catturava solo 'art.'/'artt.' e non la parola estesa → bypass totale
# del sistema di verifica.
LEGAL_ARTICLE_RE = re.compile(
    r"\bart(?:icol[oi]|t)?\.?\s*\d+[\w\-‑–]*(?:\s*(?:,|e|[\-‑–])\s*\d+[\w\-‑–]*)?\s*"
    r"((?:del|dello|della|al|allo|alla|nel|nello|nella)\s+)?"
    r"(CCNL|contratto collettivo|c\.\s?c\.|codice civile|cod\.\s*civ\.?|"
    r"D\.\s?Lgs\.?\s*\d+[/.]\d+|L\.\s?\d+[/.]\d+)",
    re.IGNORECASE)

# --- Scrubber dello STREAM: i blocchi-macchina non si vedono mai in diretta -----------
# Bug UX (review chat): il modello chiude la prosa e poi streama DIAGNOSI_STATO /
# CONSULENZA_SUMMARY → l'utente vede il bot "continuare a ragionare" con JSON, e alla
# fine il messaggio viene sostituito dal testo ripulito. Qui i delta si FILTRANO alla
# fonte: appena inizia un marker, lo stream visibile si ferma (il testo completo continua
# ad accumularsi lato server per il post-processing). Un piccolo holdback gestisce i
# marker spezzati tra chunk.
_STREAM_MARKERS = ("CONSULENZA_SUMMARY", "DIAGNOSI_STATO")
_HOLDBACK = max(len(m) for m in _STREAM_MARKERS) - 1


class StreamScrubber:
    """Filtra i delta di uno stream: emette il testo visibile, trattiene i blocchi
    macchina. feed(chunk) → testo da emettere ("" se nulla). Dopo il primo marker
    non emette più nulla (i blocchi stanno in coda al messaggio per contratto)."""

    def __init__(self) -> None:
        self._pending = ""
        self._stopped = False

    def feed(self, chunk: str) -> str:
        if self._stopped or not chunk:
            return ""
        self._pending += chunk
        idx = min((i for i in (self._pending.find(m) for m in _STREAM_MARKERS) if i != -1),
                  default=-1)
        if idx != -1:
            out = self._pending[:idx].rstrip()
            self._pending, self._stopped = "", True
            return out
        if len(self._pending) > _HOLDBACK:
            out, self._pending = self._pending[:-_HOLDBACK], self._pending[-_HOLDBACK:]
            return out
        return ""

    def flush(self) -> str:
        """Coda residua a fine stream (mai un marker: quelli fermano prima)."""
        if self._stopped:
            return ""
        out, self._pending = self._pending, ""
        idx = min((i for i in (out.find(m) for m in _STREAM_MARKERS) if i != -1), default=-1)
        return out[:idx].rstrip() if idx != -1 else out


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


# --- Il turno FORNISCE analisi/raccomandazioni/conclusioni? (regola hard "2 iterazioni") --
# Indicatore OGGETTIVO (richiesta di Luca): se il bot ha già dato analisi/consigli/sintesi,
# la soglia per il report è superata. Due turni assistant consecutivi così → si genera
# (backstop deterministico: il modello locale continua a rimandare anche quando potrebbe già).
_ANALYSIS_RE = re.compile(
    r"\b(ti\s+consigli\w+|consigli\w+\s+di|ti\s+suggeris\w+|suggeris\w+\s+di|ti\s+convien\w+|"
    r"conviene\b|dovresti\b|in\s+sintesi|in\s+conclusione|riassumendo|le\s+opzioni\s+(?:sono|"
    r"principali|possibili)|i\s+passi\s+(?:da\s+)?(?:seguire|fare|sono)|"
    r"ecco\s+(?:cosa\s+fare|come\s+muovert\w+|i\s+passaggi|i\s+passi)|come\s+muovert\w+|"
    r"raccomand\w+|la\s+prima\s+cosa\s+(?:da\s+fare|è)|il\s+rischio\s+principale|"
    r"il\s+mio\s+consiglio|puoi\s+procedere\s+così)\b", re.I)


def _looks_like_action_list(text: str) -> bool:
    items = re.findall(r"(?m)^\s*(?:\d+[.)]\s|[-–•]\s)\S", text or "")
    return len(items) >= 2


def provides_analysis(text: str) -> bool:
    """True se il turno del bot contiene analisi/raccomandazioni/conclusioni sostanziali
    (non una semplice domanda di chiarimento)."""
    t = (text or "").strip()
    if len(t) < 60:                       # troppo corto per essere un'analisi
        return False
    if NOT_READY_RE.search(t):            # dichiara un gap bloccante → non è "pronto"
        return False
    return bool(_ANALYSIS_RE.search(t)) or (_looks_like_action_list(t) and len(t) > 200)
