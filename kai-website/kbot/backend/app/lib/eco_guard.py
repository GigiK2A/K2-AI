"""Rete di sicurezza: la risposta non può essere il messaggio dell'utente ripetuto.

Segnalato il 20/10/2026 («ha restituito esattamente il messaggio dell'utente, senza rispondere»). Nei log di
produzione di quel turno non c'è un errore (stop_reason=end_turn, nessuna eccezione): è il modello che copia
l'ultimo messaggio. Qui si riconosce il caso (testo uguale o quasi), si registra un avviso con i numeri per
diagnosticarlo, e si rigenera UNA volta con un'istruzione esplicita; se la seconda risposta è ancora un'eco, o la
chiamata fallisce, si mostra un invito a riformulare invece dell'eco. KBOT_ECO_GUARD=0 spegne.
"""
from __future__ import annotations

import difflib
import logging
import os
import re
from typing import Optional

log = logging.getLogger(__name__)

SOGLIA = 0.92
MIN_CARATTERI = 20
INVITO = ("Non sono riuscito a elaborare bene la richiesta. Puoi riscriverla, anche con altre parole? "
          "Se c'erano dei numeri, scrivili di nuovo: li ricontrollo uno per uno.")


def _norm(t: str) -> str:
    return re.sub(r"[^\w€%,.]+", " ", (t or "").lower()).strip()


def e_eco(risposta: str, messaggio_utente: str) -> bool:
    """True se la risposta ripete (quasi) per intero il messaggio dell'utente."""
    u, r = _norm(messaggio_utente), _norm(risposta)
    if len(u) < MIN_CARATTERI or len(r) < MIN_CARATTERI:
        return False
    if r == u or r.startswith(u) and len(r) <= len(u) * 1.1:
        return True
    a, b = u[:2000], r[:2000]
    if abs(len(a) - len(b)) > 0.25 * max(len(a), len(b)):
        return False
    return difflib.SequenceMatcher(None, a, b).ratio() >= SOGLIA


def assicura(client, modello: str, system_prompt: str, messages: list, raw_text: str,
             ultimo_utente: str) -> str:
    """`raw_text` se non è un'eco; altrimenti una risposta rigenerata, o l'invito a riformulare. Non solleva mai."""
    if os.getenv("KBOT_ECO_GUARD", "1") == "0" or not e_eco(raw_text, ultimo_utente):
        return raw_text
    log.warning("eco_guard: la risposta ripete il messaggio dell'utente (car_risposta=%d car_utente=%d messaggi_in_storia=%d): "
                "rigenero", len(raw_text or ""), len(ultimo_utente or ""), len(messages or []))
    try:
        r = client.messages.create(
            model=modello, max_tokens=4000,
            system=system_prompt + "\n\nATTENZIONE: la risposta precedente ha RIPETUTO il messaggio dell'utente. "
                   "Non ripeterlo. Rispondi ORA alla sua richiesta: se ti chiede di ricontrollare dei calcoli, rifai i "
                   "calcoli passo per passo usando i dati già detti, dì dove avevi sbagliato e dai la versione corretta.",
            messages=list(messages), timeout=90.0)
        nuovo = "".join(getattr(b, "text", "") for b in r.content if getattr(b, "type", "") == "text").strip()
        if nuovo and not e_eco(nuovo, ultimo_utente):
            return nuovo
        log.warning("eco_guard: anche la seconda risposta è un'eco o vuota")
    except Exception:
        log.warning("eco_guard: rigenerazione fallita", exc_info=True)
    return INVITO
