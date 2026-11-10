"""Pulizia del testo che l'utente vede e che si esporta: entità HTML, CSS/tag accidentali, codifica doppia, caratteri invisibili.

Deterministica, idempotente, senza toccare i caratteri legittimi (accenti, apostrofi e virgolette tipografiche, €, segni matematici, `<`/`>` di un
confronto, elenchi e tabelle) né il CODICE (blocchi ```). I marcatori del documento (<<<DOCUMENTO: …>>>) non sono tag e restano.

Nata dal collaudo del 10/11/2026 (CSS in cima al PDF, `&#x27;`/`&nbsp;`/`&egrave;` letterali): vedi tests/test_testo_pulito.py.
"""
from __future__ import annotations

import html as _html
import re

_FENCE = re.compile(r"(```[\s\S]*?```|~~~[\s\S]*?~~~)")
_BLOCCHI_MORTI = re.compile(r"(?is)<\s*(style|script)\b[^>]*>.*?<\s*/\s*\1\s*>|<!--.*?-->")
_TAG_NOTI = r"(?:html|head|body|title|meta|link|style|script|div|span|p|br|hr|ul|ol|li|table|thead|tbody|tr|td|th|h[1-6]|b|i|u|strong|em|font|a|img|section|article|header|footer|center|small|sup|sub|code|pre|blockquote)"
_BR = re.compile(rf"(?i)<\s*br\s*/?\s*>")
_FINE_BLOCCO = re.compile(rf"(?i)<\s*/\s*(?:p|div|li|tr|h[1-6]|section|article|blockquote)\s*>")
_APRI_BLOCCO = re.compile(rf"(?i)(?<!\n)<\s*(?:p|div|tr|h[1-6]|section|article|blockquote)\b[^<>]*>")
_LI = re.compile(r"(?i)<\s*li\b[^<>]*>")
_TAG = re.compile(rf"(?i)</?\s*{_TAG_NOTI}\b(?:\s[^<>]*)?/?>")
_ENT_DOPPIA = re.compile(r"&amp;(#\d+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]{1,9});")
_ENT = re.compile(r"&(#\d+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]{1,9});")
_INVISIBILI = re.compile("[​-‍⁠﻿�­]")
_CONTROLLI = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MOJIBAKE = re.compile("[ÂÃ][\u0080-¿]|â€|â‚")
_UNI_ESC = re.compile(r"\\u([0-9a-fA-F]{4})")


def decodifica_entita(t: str, tieni_xml: bool = False) -> str:
    """Entità → caratteri. `tieni_xml=True` (per ReportLab/HTML) lascia &amp; &lt; &gt; come entità e riconverte < > & ottenuti da entità numeriche."""
    t = _ENT_DOPPIA.sub(r"&\1;", t)

    def rep(m):
        ch = _html.unescape(m.group(0))
        if ch == m.group(0):
            return ch                                    # entità sconosciuta: resta com'è
        if tieni_xml:
            if m.group(1) in ("amp", "lt", "gt"):
                return m.group(0)
            if ch in "&<>":
                return {"&": "&amp;", "<": "&lt;", ">": "&gt;"}[ch]
        return ch.replace(" ", " ")

    return _ENT.sub(rep, t)


def _pulisci_segmento(t: str) -> str:
    originale = t
    t = _pulisci_interno(t)
    testa = len(originale) - len(originale.lstrip("\n"))
    coda = len(originale) - len(originale.rstrip("\n"))
    return "\n" * testa + t.strip("\n") + "\n" * coda


def _pulisci_interno(t: str) -> str:
    if _MOJIBAKE.search(t):
        try:
            rifatto = t.encode("cp1252", errors="strict").decode("utf-8")
            t = rifatto
        except (UnicodeEncodeError, UnicodeDecodeError):
            try:
                t = t.encode("latin-1", errors="strict").decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
    if "\\u" in t:
        t = _UNI_ESC.sub(lambda m: chr(int(m.group(1), 16)), t)
    t = _BLOCCHI_MORTI.sub("", t)
    if "<" in t:
        t = _BR.sub("\n", t)
        t = _LI.sub("\n- ", t)
        t = _FINE_BLOCCO.sub("\n", t)
        t = _APRI_BLOCCO.sub("\n", t)
        t = _TAG.sub("", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
    if "&" in t:
        t = decodifica_entita(t)
    t = t.replace(" ", " ").replace(" ", " ")
    t = _INVISIBILI.sub("", t)
    t = _CONTROLLI.sub("", t)
    t = re.sub(r"(?<=\S) {2,}(?=\S)", " ", t)           # uno spazio + &nbsp; = due spazi: se ne tiene uno (il rientro a inizio riga resta)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t


def pulisci(testo: str) -> str:
    """Testo pulito per chat, documento ed esportazioni. Il codice (blocchi ```) resta com'è."""
    if not testo:
        return testo or ""
    pezzi = _FENCE.split(testo)
    return "".join(p if i % 2 else _pulisci_segmento(p) for i, p in enumerate(pezzi))
