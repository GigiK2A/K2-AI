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
_FINE_OK = tuple(".?!:;)»”\"'*]")
_ELLISSI = ("…", "...")


def e_troncata(testo: str) -> bool:
    """True se l'ultimo paragrafo di prosa finisce a metà frase (lettera, cifra o virgola senza chiusura)."""
    t = (testo or "").rstrip()
    if len(t) < MIN_CARATTERI or "```" in t[-400:]:
        return False
    ultima = t.splitlines()[-1].strip()
    if ultima.endswith(_ELLISSI) and len(ultima) >= 12:
        return True                                   # «…» in fondo: il testo è stato amputato (anche dentro un elenco)
    if not ultima or _ELENCO.match(ultima) or len(ultima) < 25:
        return False                                  # elenchi puntati, titoli, righe brevi: possono non avere il punto
    if ultima.endswith(_FINE_OK):
        return False
    return bool(re.search(r"[\wàèéìòù,]$", ultima))


_META = re.compile(r"visualizzazion|ultima frase|riprend\w+ da l|interrott|troncat|tagliat|era gi[àa] complet|"
                   r"non (?:era|è|sembra)\w* (?:stata )?(?:interrott|troncat)|scus[ai]|mi dispiace", re.I)
_STOP_FINITO = ("end_turn", "stop_sequence")
_STOP_TAGLIATO = ("max_tokens", "model_context_window_exceeded", "length")


def serve_continuazione(raw_text: str, stop_reason) -> bool:
    """Il testo va completato? Con lo `stop_reason` dell'API la risposta è: TAGLIATA (max_tokens/contesto) → sì; FINITA dal modello
    (end_turn) → no, salvo l'ellissi finale che segnala una storia imitata male; senza stop_reason (percorsi di prova, gateway
    che non lo riportano) resta l'euristica sul testo. 10/11/2026: l'euristica da sola chiamava «interrotta» una risposta completa
    senza punto finale e il modello rispondeva con un messaggio sul troncamento, appeso in coda all'analisi."""
    t = (raw_text or "").rstrip()
    if stop_reason in _STOP_TAGLIATO:
        return len(t) >= MIN_CARATTERI
    if stop_reason in _STOP_FINITO:
        return len(t) >= MIN_CARATTERI and t.splitlines()[-1].strip().endswith(_ELLISSI)
    return e_troncata(raw_text)


def completa(client, modello: str, system_prompt: str, messages: list, raw_text: str, stop_reason=None) -> str:
    """`raw_text` completato con una continuazione se era interrotto; altrimenti invariato. Non solleva mai."""
    if os.getenv("KBOT_TAGLIO_GUARD", "1") == "0" or not serve_continuazione(raw_text, stop_reason):
        return raw_text
    if raw_text.rstrip().endswith(_ELLISSI):
        raw_text = raw_text.rstrip().rstrip("….").rstrip()
    log.warning("taglio_guard: risposta interrotta (stop_reason=%s, car=%d, coda=%r): chiedo la continuazione",
                stop_reason, len(raw_text), raw_text[-60:])
    try:
        r = client.messages.create(
            model=modello, max_tokens=1500, system=system_prompt,
            messages=list(messages) + [
                {"role": "assistant", "content": raw_text.rstrip()},
                {"role": "user", "content": "La tua risposta potrebbe essersi interrotta a metà frase. Se è davvero interrotta, continua "
                                            "ESATTAMENTE dalla parola dove ti sei fermato, senza ripetere nulla e senza premesse, e "
                                            "concludila. Se la risposta era GIÀ completa, rispondi soltanto: OK_COMPLETA"}],
            timeout=60.0)
        extra = "".join(getattr(b, "text", "") for b in r.content if getattr(b, "type", "") == "text").strip()
        if not extra or "OK_COMPLETA" in extra or _META.search(extra):
            return raw_text                                # niente da aggiungere, oppure un commento sul troncamento: mai in coda
        ultimo = raw_text.rstrip().split()[-1].lower() if raw_text.strip() else ""
        if extra.lower().startswith(ultimo) and len(ultimo) > 3:
            extra = extra[len(ultimo):].lstrip()      # la continuazione ha ripetuto l'ultima parola
        sep = "" if raw_text.endswith((" ", "\n")) or extra[:1] in ",.;:)!?" else " "
        return raw_text.rstrip() + sep + extra
    except Exception:
        log.warning("taglio_guard: continuazione fallita (fail-open)", exc_info=True)
        return raw_text
