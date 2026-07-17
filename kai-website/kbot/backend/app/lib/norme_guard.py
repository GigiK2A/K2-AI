"""Guardia normativa della CHAT — mai un articolo di legge non verificato all'utente.

Sistema (17 lug, richiesto da Luca: «devono mai esserci errori del genere»):
il modello locale cita articoli A MEMORIA e li sbaglia ('art. 2099-c c.c.' inesistente,
'artt. 62-63 del CCNL' mai indicato). La chat non ha il grounding normativo dell'8e —
quindi lo USA via rete: POST /v1/norme/verify sull'8e (corpus FTS5, 62k articoli).

Regola: una citazione con numero di articolo resta nel testo SOLO se il corpus la
verifica; tutto il resto viene de-specificato (resta la fonte, sparisce il numero).
FAIL-CLOSED su ogni errore/timeout/corpus assente: de-specifica tutto (il backstop
puro di prompts.sanitize_unverified_legal_citations). Mai fail-open.
KBOT_NORME_VERIFY=0 → salta la verifica remota (solo strip).
"""
from __future__ import annotations

import logging
import os
import re
import unicodedata
from typing import Optional

import httpx

from ..settings import ENGINE_8E_BASE_URL, ENGINE_8E_API_KEY
from . import signals
from .prompts import sanitize_unverified_legal_citations

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(6.0, connect=3.0)


def _verify_enabled() -> bool:
    return os.getenv("KBOT_NORME_VERIFY", "1") != "0" and bool(ENGINE_8E_BASE_URL)


def _verify_remote(testo: str) -> Optional[list[dict]]:
    """Citazioni verificate dal corpus 8e. None = verifica non disponibile (fail-closed
    a carico del chiamante). Lista (anche vuota) = verifica riuscita."""
    headers = {"Content-Type": "application/json"}
    if ENGINE_8E_API_KEY:
        headers["Authorization"] = f"Bearer {ENGINE_8E_API_KEY}"
    with httpx.Client(timeout=_TIMEOUT) as c:
        r = c.post(f"{ENGINE_8E_BASE_URL}/v1/norme/verify",
                   json={"testo": testo}, headers=headers)
    if r.status_code != 200:
        return None
    data = r.json()
    if not data.get("corpus_disponibile"):
        return None
    return [c for c in data.get("citazioni", []) if c.get("verificata")]


def _norm(s: str) -> str:
    """Normalizzazione per il confronto label↔span: minuscole, trattini esotici → '-',
    niente punti/spazi (così 'art. 2096 c.c.' combacia con 'art 2096 cc')."""
    s = unicodedata.normalize("NFKC", s or "").lower()
    s = re.sub(r"[‐‑‒–−]", "-", s)
    return re.sub(r"[.\s]", "", s)


def sanitize(text: str) -> str:
    """Testo visibile della chat → citazioni verificate INTATTE, il resto de-specificato."""
    if not text or not signals.LEGAL_ARTICLE_RE.search(text):
        return text  # nessuna citazione con numero → nessuna latenza extra
    verified: list[dict] = []
    if _verify_enabled():
        try:
            got = _verify_remote(text)
            if got is not None:
                verified = got
        except Exception:
            log.warning("norme_guard: verifica 8e fallita → fail-closed (strip)", exc_info=True)
    if not verified:
        return sanitize_unverified_legal_citations(text)

    keep = {_norm(c["label"]) for c in verified if c.get("label")}

    def repl(m: "re.Match") -> str:
        if _norm(m.group(0)) in keep or any(k and k in _norm(m.group(0)) for k in keep):
            return m.group(0)          # verificata dal corpus → resta col numero
        return _delegalize_span(m)

    return signals.LEGAL_ARTICLE_RE.sub(repl, text)


def _delegalize_span(match: "re.Match") -> str:
    fonte = (match.group(2) or "").strip().lower()
    if "ccnl" in fonte or "contratto collettivo" in fonte:
        return "il CCNL applicato"
    if "civile" in fonte or fonte.startswith("c.c") or fonte.startswith("c c") or "cod" in fonte:
        return "il codice civile"
    return "la normativa di riferimento"
