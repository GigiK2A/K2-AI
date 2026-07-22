"""OUTPUT QUALITY ENGINE — polish deterministico del testo visibile (review "AI Proof").

Il modello genera una BOZZA; il documento finale lo produce l'applicazione. Questo modulo
è l'ultimo miglio tra il modello e l'utente: qualunque cosa il modello emetta, l'utente
non deve mai vedere HTML, template, placeholder, artefatti tecnici, markdown rotto o
tipografia sporca.

Complementare (non duplicato) rispetto a ciò che esiste già:
  - normalize_assistant_reply  → fence/heading/tabelle/grassetti markdown
  - norme_guard / deadline_guard / finance_guard → contenuti (citazioni, scadenze, numeri)
  - quality_gate.review (LLM)  → qualità consulenziale sui turni a rischio
Qui: FORMA. Pipeline: HTML → artefatti tecnici → placeholder → tipografia → liste →
dedup → controlli finali (telemetria). Deterministico, idempotente, FAIL-OPEN: mai
un'eccezione al posto di una risposta. KBOT_OUTPUT_QUALITY=0 disattiva.
"""
from __future__ import annotations

import html as _html
import logging
import os
import re

log = logging.getLogger(__name__)


def _enabled() -> bool:
    return os.getenv("KBOT_OUTPUT_QUALITY", "1") != "0"


# ── 1 · HTML → testo (mai mostrare tag; convertire, non cancellare il contenuto) ─────────

_BLOCK_TAGS = re.compile(r"(?i)<\s*(?:/\s*)?(?:p|div|section|article|table|tr|ul|ol)\s*[^>]*>")
_BR = re.compile(r"(?i)<\s*br\s*/?\s*>")
_LI = re.compile(r"(?i)<\s*li\s*[^>]*>")
_BOLD = re.compile(r"(?i)<\s*(?:strong|b)\s*>(.*?)<\s*/\s*(?:strong|b)\s*>", re.S)
_ITAL = re.compile(r"(?i)<\s*(?:em|i)\s*>(.*?)<\s*/\s*(?:em|i)\s*>", re.S)
_SCRIPT = re.compile(r"(?i)<\s*(script|style)\b[^>]*>[\s\S]*?<\s*/\s*\1\s*>")
_COMMENT = re.compile(r"<!--[\s\S]*?-->|<!\[CDATA\[[\s\S]*?\]\]>")
_ANY_TAG = re.compile(r"</?[a-zA-Z][a-zA-Z0-9:-]*(?:\s[^<>]*)?/?>")


def strip_html(text: str) -> str:
    if "<" not in text:
        # niente tag, ma le ENTITÀ possono esserci comunque (&egrave; &amp; &nbsp;)
        return _html.unescape(text) if "&" in text else text
    t = _SCRIPT.sub("", text)
    t = _COMMENT.sub("", t)
    t = _BR.sub("\n", t)
    t = _LI.sub("\n- ", t)
    t = _BLOCK_TAGS.sub("\n", t)
    t = _BOLD.sub(r"\1", t)      # la chat è testo: il contenuto resta, il markup no
    t = _ITAL.sub(r"\1", t)
    t = _ANY_TAG.sub("", t)
    if "&" in t:
        t = _html.unescape(t)
    return t


# ── 2 · Artefatti tecnici (marker interni, UUID, stack trace, frammenti SSE) ─────────────

# qualunque blocco-macchina residuo (i marker noti sono già strippati a monte in modo
# tollerante; questo copre marker NUOVI/futuri o malformati: zero leak garantito)
_MARKER_LINE = re.compile(r"(?m)^.*\b[A-Z][A-Z0-9_]{3,}_(?:START|END)\b.*$")
_UUID_LINE = re.compile(
    r"(?m)^\s*[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\s*$", re.I)
_TRACE = re.compile(r"(?ms)^Traceback \(most recent call last\):.*?(?=\n\S|\Z)")
_TRACE_LINE = re.compile(r'(?m)^\s*File "[^"]+", line \d+.*$')
_SSE_LINE = re.compile(r"(?m)^\s*data:\s*\{.*$")


def strip_technical(text: str) -> str:
    t = _TRACE.sub("", text)
    t = _TRACE_LINE.sub("", t)
    t = _MARKER_LINE.sub("", t)
    t = _UUID_LINE.sub("", t)
    t = _SSE_LINE.sub("", t)
    return t


# ── 3 · Placeholder / template (mai {{var}}, ${var}, [INSERIRE], TODO, lorem, N/D) ───────

_TPL_VAR = re.compile(r"\{\{[^{}]{0,60}\}\}|\$\{[^{}]{0,60}\}")
_BRACKET_PH = re.compile(r"(?i)\[\s*(?:inserire|inserisci|placeholder|da\s+compilare|"
                         r"todo|nome(?:\s+\w+)?|valore|xxx+|\.{3})\s*[^\]]{0,40}\]")
_TODO_LINE = re.compile(r"(?im)^\s*(?:TODO|FIXME|XXX)\b[:\s].*$")
_TODO_INLINE = re.compile(r"(?i)\bTODO\s*:\s*[^.!?\n]*[.!?]?")
_LOREM = re.compile(r"(?is)lorem ipsum[^.!?\n]*[.!?]?")
_ND = re.compile(r"\bN/?D\b\.?")
# punteggiatura orfana lasciata dalle rimozioni ('di .', '..', ' ,') — NON tocca '...'
_ORPHAN_PUNCT = re.compile(r"(?<!\.)\.\s*\.(?!\.)")
_SPACE_DOT = re.compile(r" +\.(?!\.)")


def strip_placeholders(text: str) -> str:
    t = _TPL_VAR.sub("", text)
    t = _BRACKET_PH.sub("", t)
    t = _TODO_LINE.sub("", t)
    t = _TODO_INLINE.sub("", t)
    t = _LOREM.sub("", t)
    t = _ND.sub("da definire", t)
    t = _ORPHAN_PUNCT.sub(".", t)
    t = _SPACE_DOT.sub(".", t)
    return t


# ── 4 · Tipografia (unicode sporco, spazi, virgolette/apostrofi/trattini) ────────────────

_ZERO_WIDTH = re.compile("[​‌‍⁠﻿]")
_EXOTIC_DASH = re.compile("[‐‑‒]")   # trattini esotici → '-' (bug PDF noto)
_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_MULTI_NL = re.compile(r"\n{3,}")
_SPACE_BEFORE_PUNCT = re.compile(r" +([,;:.!?])")


def fix_typography(text: str) -> str:
    t = _ZERO_WIDTH.sub("", text)
    t = t.replace(" ", " ")
    t = _EXOTIC_DASH.sub("-", t)
    t = t.replace("’", "'").replace("‘", "'")       # apostrofi uniformi
    t = t.replace("“", "«").replace("”", "»")        # virgolette → caporali (stile K2A)
    t = _SPACE_BEFORE_PUNCT.sub(r"\1", t)
    t = _MULTI_SPACE.sub(" ", t)
    t = _MULTI_NL.sub("\n\n", t)
    return t


# ── 5 · Liste uniformi (mai •, -, * mescolati nello stesso elenco) ───────────────────────

_BULLET = re.compile(r"(?m)^(\s*)[•*–▪‣·]\s+")


def fix_lists(text: str) -> str:
    return _BULLET.sub(r"\1- ", text)


# ── 6 · Dedup (righe/paragrafi consecutivi identici) ─────────────────────────────────────


def dedupe(text: str) -> str:
    out, prev = [], None
    for line in text.split("\n"):
        key = line.strip().lower()
        if key and key == prev and len(key) > 12:
            continue                        # riga identica alla precedente → via
        out.append(line)
        if key:
            prev = key
    return "\n".join(out)


# ── 7 · Controlli finali (telemetria: cosa NON deve mai arrivare all'utente) ─────────────


def final_checks(text: str) -> list[str]:
    """Nomi dei controlli falliti (lista vuota = output pulito). Solo telemetria:
    il polish è già passato, qui si misura l'efficacia."""
    failed = []
    if _ANY_TAG.search(text):
        failed.append("html_tag")
    if _TPL_VAR.search(text):
        failed.append("template_var")
    if re.search(r"\b[A-Z][A-Z0-9_]{3,}_(?:START|END)\b", text):
        failed.append("marker_leak")
    if text.count("```") % 2 == 1:
        failed.append("unclosed_fence")
    if re.search(r"(?i)\blorem ipsum\b", text):
        failed.append("lorem")
    if re.search(r"\bN/?D\b", text):
        failed.append("nd_placeholder")
    return failed


# ── pipeline ─────────────────────────────────────────────────────────────────────────────


def polish(text: str) -> str:
    """La bozza del modello → il testo consegnabile. Idempotente, fail-open."""
    if not text or not _enabled():
        return text
    try:
        t = strip_html(text)
        t = strip_technical(t)
        t = strip_placeholders(t)
        t = fix_lists(t)
        t = fix_typography(t)
        t = dedupe(t)
        t = t.strip()
        failed = final_checks(t)
        if failed:
            log.warning("output_quality: controlli non superati dopo il polish: %s", failed)
        return t or text.strip()
    except Exception:
        log.exception("output_quality.polish fallito (fail-open: testo originale)")
        return text
