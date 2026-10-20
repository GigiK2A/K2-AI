"""Rete di sicurezza: una risposta che si ferma a metà frase viene completata (una sola volta).

Misurato il 20/10/2026 sul backend locale: su 36 turni, 1 risposta interrotta a metà frase («…Qui invece la rettific»)
con `stop_reason=end_turn` e solo 285 token in uscita. Non è `max_tokens`, non è il contesto del modello (65.536) e non è
un timeout: il modello emette la fine-turno a metà frase e il server la riporta come una fine normale. Sui log di
produzione (30 turni) lo stop era sempre end_turn: da lì non si distingue. Qui si riconosce il testo che finisce a metà
frase e si chiede UNA continuazione; se non serve o fallisce, la risposta resta com'era. KBOT_TAGLIO_GUARD=0 spegne.
"""
from __future__ import annotations

import logging
import os
import re

log = logging.getLogger(__name__)

MIN_CARATTERI = 200
_ELENCO = re.compile(r"^\s*(?:[-*•–]|\d+[.)]|#{1,6}\s|\|)")
_FINE_OK = tuple(".?!:;)»”\"'*…]")


def e_troncata(testo: str) -> bool:
    """True se l'ultimo paragrafo di prosa finisce a metà frase (lettera, cifra o virgola senza chiusura)."""
    t = (testo or "").rstrip()
    if len(t) < MIN_CARATTERI or "```" in t[-400:]:
        return False
    ultima = t.splitlines()[-1].strip()
    if not ultima or _ELENCO.match(ultima) or len(ultima) < 25:
        return False                                  # elenchi puntati, titoli, righe brevi: possono non avere il punto
    if ultima.endswith(_FINE_OK):
        return False
    return bool(re.search(r"[\wàèéìòù,]$", ultima))


def completa(client, modello: str, system_prompt: str, messages: list, raw_text: str) -> str:
    """`raw_text` completato con una continuazione se era interrotto a metà frase; altrimenti invariato. Non solleva mai."""
    if os.getenv("KBOT_TAGLIO_GUARD", "1") == "0" or not e_troncata(raw_text):
        return raw_text
    log.warning("taglio_guard: risposta interrotta a metà frase (car=%d, coda=%r): chiedo la continuazione",
                len(raw_text), raw_text[-60:])
    try:
        r = client.messages.create(
            model=modello, max_tokens=1500, system=system_prompt,
            messages=list(messages) + [
                {"role": "assistant", "content": raw_text.rstrip()},
                {"role": "user", "content": "La tua risposta si è interrotta a metà frase. Continua ESATTAMENTE da dove ti sei "
                                            "fermato, senza ripetere ciò che hai già scritto e senza premesse, e concludila."}],
            timeout=60.0)
        extra = "".join(getattr(b, "text", "") for b in r.content if getattr(b, "type", "") == "text").strip()
        if not extra:
            return raw_text
        ultimo = raw_text.rstrip().split()[-1].lower() if raw_text.strip() else ""
        if extra.lower().startswith(ultimo) and len(ultimo) > 3:
            extra = extra[len(ultimo):].lstrip()      # la continuazione ha ripetuto l'ultima parola
        sep = "" if raw_text.endswith((" ", "\n")) or extra[:1] in ",.;:)!?" else " "
        return raw_text.rstrip() + sep + extra
    except Exception:
        log.warning("taglio_guard: continuazione fallita (fail-open)", exc_info=True)
        return raw_text
