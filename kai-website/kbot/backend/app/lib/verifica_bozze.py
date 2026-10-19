"""Verificatore delle BOZZE prima dell'invio: se l'utente ha chiesto di scrivere un testo e la risposta non lo contiene,
una seconda chiamata al modello con l'istruzione di scriverlo ORA.

Perché: anche con la regola delle bozze nel prompt (lib/indici_e_bozze) il modello locale, 1 volta su 6, risponde a
«scrivimi una lettera di diffida» con una domanda («chi sei? sei un'impresa?», «hai già ricevuto una contestazione?»)
invece di scrivere la lettera (misurato il 19/10/2026: 20 lettere su 24 in locale, 0 su 1 in produzione). Spostare la
regola o rafforzarla non ha cambiato nulla di misurabile: serve un controllo in codice, come per il blocco
CONSULENZA_SUMMARY (`_ensure_summary_block`).

`contiene_bozza` è volutamente generosa (basta qualche segnale di lettera/contratto/verbale): un falso «manca» costa una
chiamata in più, un falso «c'è» lascia la domanda com'è oggi. KBOT_VERIFICA_BOZZE=0 spegne.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Optional

from .indici_e_bozze import _GATE_BOZZA, REGOLA_BOZZE

log = logging.getLogger(__name__)

_MARCATORI = [
    r"\boggetto\s*:", r"\bspett\.?(?:le|mo)?\b", r"\begregi[o]?\b", r"\bgent\.?(?:le|mo|ma)\b", r"\bgentilissim\w+",
    r"\bbuongiorno\b", r"\bbuonasera\b", r"\bsalve\b", r"con la presente", r"distinti saluti|cordiali saluti|in fede",
    r"\bpremesso che\b", r"\ble parti\b[^.\n]{0,50}(?:convengono|si impegnano|dichiarano)", r"\bil sottoscritto\b|\bla sottoscritta\b",
    r"\bart\.\s*1\b[.\s]", r"\bpec\b[^.\n]{0,40}\[", r"\[(?:data|luogo|nome|indirizzo|firma|termine)[^\]]{0,40}\]",
]

ISTRUZIONE = (
    "Scrivi ORA la bozza completa che ho richiesto. Non fare domande e non commentare: comincia direttamente dalla bozza. "
    "Dove manca un dato usa un segnaposto tra parentesi quadre ([data], [indirizzo PEC del destinatario], [tuo nome e "
    "ruolo]); se un'ipotesi è incerta (tipo di rapporto, destinatario) scegli la più probabile e dichiarala in una riga "
    "DOPO la bozza. Non inventare nomi, indirizzi, partite IVA, importi o date."
)


def richiesta_bozza(ultimo_utente: str) -> bool:
    return bool(_GATE_BOZZA.search(ultimo_utente or ""))


def contiene_bozza(testo: str) -> bool:
    """True se il testo ha i segnali di una lettera/contratto/verbale scritto (non solo domande o commenti)."""
    t = testo or ""
    n = sum(1 for m in _MARCATORI if re.search(m, t, re.I))
    return n >= 2 or (n >= 1 and len(t) >= 700)


def assicura(client, modello: str, system_prompt: str, messages: list, raw_text: str, ultimo_utente: str) -> str:
    """`raw_text` se contiene già la bozza (o non era richiesta); altrimenti il testo di una seconda chiamata, se
    quest'ultimo contiene la bozza; altrimenti `raw_text`. Non solleva mai."""
    if os.getenv("KBOT_VERIFICA_BOZZE", "1") == "0" or not richiesta_bozza(ultimo_utente) or contiene_bozza(raw_text):
        return raw_text
    try:
        resp = client.messages.create(
            model=modello, max_tokens=4000, system=system_prompt + REGOLA_BOZZE,
            messages=list(messages) + [{"role": "assistant", "content": (raw_text or "Ok.")[:3000]},
                                       {"role": "user", "content": ISTRUZIONE}],
            timeout=120.0)
        nuovo = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text").strip()
        if nuovo and contiene_bozza(nuovo):
            log.info("kbot: bozza richiesta ma assente → rigenerata con istruzione esplicita")
            return nuovo
        log.warning("kbot: bozza assente anche dopo la seconda chiamata (resta la prima risposta)")
    except Exception:
        log.warning("kbot: verificatore bozze fallito (fail-open)", exc_info=True)
    return raw_text
