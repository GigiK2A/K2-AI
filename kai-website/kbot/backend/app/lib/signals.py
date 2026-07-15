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
PROCEDI_RE = re.compile(
    r"\b(vai|proced\w*|fai il report|fammi il report|voglio il report( subito)?|"
    r"basta domande|salta le domande|fai senza domande|ok proced\w*|dai proced\w*)\b", re.I)

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
URGENT_RE = re.compile(
    r"\b(urgen\w+|emergenz\w+|subito|quanto prima|entro (?:\d+|pochi|due|tre|dieci) "
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


def is_ready_declared(text: str) -> bool:
    """Readiness dichiarata E non negata — la coppia va SEMPRE usata insieme."""
    t = text or ""
    return bool(READY_RE.search(t)) and not NOT_READY_RE.search(t)
