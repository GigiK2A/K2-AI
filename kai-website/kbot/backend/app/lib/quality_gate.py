"""QUALITY ENGINE della chat K-BOT — passaggio critico sul turno PRIMA dell'invio.

Perché esiste (stress test lug 2026): la chat gira su un modello LOCALE (gpt-oss),
il cui giudizio consulenziale è più debole di Claude. Le regole nel system prompt
coprono i casi già visti; questo critico verifica OGNI turno "a rischio" contro le
4 regole trasversali emerse dagli eval, con un compito molto più semplice della
consulenza stessa (verificare una bozza ≪ condurre l'intake):

  1. STOP RULE / summary prematuro — report dichiarato/emesso con ipotesi
     alternative ancora aperte;
  2. diagnosi assertiva — qualificazioni ("possibile insolvenza", "responsabilità
     contrattuale") senza fatti verificati;
  3. misure drastiche — azioni irreversibili/specifiche a fatti non verificati
     (bloccare pagamenti/stipendi/accessi, PEC/diffide, read-only);
  4. profondità sproporzionata — promettere il "parere completo" con fatti sottili.

Design: PRE-FILTRO deterministico (il critico gira solo sui turni a rischio →
niente latenza sui turni banali), verdetto JSON, enforcement deterministico,
FAIL-OPEN (qualsiasi errore → il turno passa invariato: il gate non deve mai
rompere la chat). Disattivabile con KBOT_QUALITY_GATE=0.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

from .prompts import extract_summary, strip_summary_block

log = logging.getLogger(__name__)

ENABLED = (os.environ.get("KBOT_QUALITY_GATE", "1") or "1").lower() in ("1", "true", "yes")

# PRE-FILTRO: il critico gira SOLO se la bozza contiene un segnale a rischio
# (summary/readiness, qualificazioni diagnostiche, azioni potenzialmente drastiche,
# promesse di deliverable). Una semplice domanda di intake NON lo attiva.
_TRIGGER_RE = re.compile(
    r"CONSULENZA_SUMMARY|informazion\w+ sufficient\w+|sto generando|procedo con il report|"
    r"responsabilit\w+|insolvenz\w+|crisi di liquidit|frode|inadempim\w+|"
    r"diffida\w*|\bPEC\b|blocc(?:are|hi|o|ate)\b|sospendere|read.?only|sola lettura|"
    r"risarcim\w+|parere legale|report completo|procura", re.I)

_CRITIC_SYSTEM = (
    "Sei il QUALITY ENGINE di K2-AI: valuti la BOZZA di risposta di un consulente AI "
    "per PMI prima dell'invio al cliente. Verifica SOLO queste 4 regole:\n"
    "1) STOP RULE: un report si può annunciare/generare SOLO se il problema è identificato, "
    "le ipotesi alternative plausibili sono state discriminate con domande (es. un conto in "
    "rosso può essere crisi di liquidità/frode/errore; una telefonata riferita può essere "
    "lamentela/contestazione/richiesta infondata), i rischi sono valutabili e le prime azioni "
    "identificabili. Se la bozza dichiara 'informazioni sufficienti' o contiene il blocco "
    "CONSULENZA_SUMMARY ma le ipotesi sono ancora aperte → premature_summary=true e scrivi in "
    "missing_question LA singola domanda che meglio discrimina le ipotesi.\n"
    "2) DIAGNOSI: qualificazioni assertive (es. 'possibile insolvenza', 'responsabilità "
    "contrattuale') senza fatti verificati → assertive_diagnosis=true. Frame corretto: "
    "'possibile X da verificare', ipotesi elencate come aperte.\n"
    "3) AZIONI: misure drastiche o tecnicamente specifiche a fatti non verificati (bloccare "
    "pagamenti/stipendi/forniture/accessi, PEC o diffide, cartelle read-only, procura) → "
    "drastic_actions=true. Corrette: azioni conservative di verifica (estratto conto, "
    "contattare la banca, preservare documenti, non rispondere a caldo).\n"
    "4) PROFONDITÀ: promettere un 'parere/report completo' quando i fatti sono sottili (voce "
    "riferita, nessun documento visto) → depth_mismatch=true (andava proposto un triage "
    "preliminare dichiarato tale).\n"
    "Se ALMENO un flag è true, scrivi in 'rewrite' la versione corretta e BREVE della "
    "risposta (stesse informazioni utili; frame prudente; azioni conservative; se "
    "premature_summary chiudi con la domanda discriminante e NON includere il blocco "
    "CONSULENZA_SUMMARY). Se tutti i flag sono false: rewrite=null.\n"
    "Rispondi SOLO con l'oggetto JSON: {\"premature_summary\":bool,"
    "\"assertive_diagnosis\":bool,\"drastic_actions\":bool,\"depth_mismatch\":bool,"
    "\"missing_question\":string|null,\"rewrite\":string|null}"
)


def _parse_verdict(text: str) -> Optional[dict]:
    t = (text or "").strip()
    start, end = t.find("{"), t.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        v = json.loads(t[start:end + 1])
        return v if isinstance(v, dict) else None
    except json.JSONDecodeError:
        return None


def _compact_history(merged_messages: list, max_turns: int = 6, max_chars: int = 350) -> str:
    lines = []
    for m in (merged_messages or [])[-max_turns:]:
        if not isinstance(m, dict):
            continue
        role = "CLIENTE" if m.get("role") == "user" else "CONSULENTE"
        content = str(m.get("content") or "")[:max_chars]
        if content.strip():
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def review(client, model: str, merged_messages: list, raw_text: str) -> str:
    """Ritorna il testo del turno, eventualmente corretto dal critico. FAIL-OPEN."""
    if not ENABLED or not (raw_text or "").strip():
        return raw_text
    if not _TRIGGER_RE.search(raw_text):
        return raw_text  # turno a basso rischio: nessuna latenza extra
    try:
        user = (
            f"CONVERSAZIONE (ultimi turni):\n{_compact_history(merged_messages)}\n\n"
            f"BOZZA DA VALUTARE:\n{raw_text[:4000]}\n\nValuta e rispondi SOLO col JSON."
        )
        resp = client.messages.create(
            model=model, max_tokens=800,
            system=_CRITIC_SYSTEM,
            messages=[{"role": "user", "content": user}],
            timeout=90.0,
        )
        out = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        v = _parse_verdict(out)
        if not v:
            log.warning("quality_gate: verdetto non parsabile → pass-through")
            return raw_text
        flags = [k for k in ("premature_summary", "assertive_diagnosis",
                             "drastic_actions", "depth_mismatch") if v.get(k) is True]
        if not flags:
            return raw_text
        log.info("quality_gate: intervento %s", ",".join(flags))
        text = str(v.get("rewrite") or "").strip() or raw_text
        if v.get("premature_summary"):
            # enforcement deterministico: MAI un summary con ipotesi aperte,
            # qualunque cosa contenga il rewrite.
            text = strip_summary_block(text)
            q = str(v.get("missing_question") or "").strip()
            if q and q[:60].lower() not in text.lower():
                text = f"{text}\n\n{q}" if text else q
        elif extract_summary(raw_text) and not extract_summary(text):
            # il summary era legittimo (non prematuro) ma il rewrite l'ha perso →
            # lo si ri-appende per non rompere il flusso di generazione.
            m = re.search(r"CONSULENZA_SUMMARY_START[\s\S]*?CONSULENZA_SUMMARY_END", raw_text)
            if m:
                text = f"{text}\n\n{m.group(0)}"
        return text or raw_text
    except Exception:
        log.exception("quality_gate: errore critico → pass-through (fail-open)")
        return raw_text
