"""Cronometro per fase e conteggio delle chiamate al modello di un turno.

Richiesto dall'audit del 20/10/2026 («aggiungi logging e metriche per capire dove si accumula la latenza»). Un turno di chat
passa da: preparazione (instradamento, prompt) → fonti (ricerca web proattiva + recupero delle norme) → generazione (token) →
verifica (guardie, controllo bozze, quality gate) → salvataggio. Ogni fase si misura con un orologio monotono e si registra in
una sola riga di log (`kbot timing: …`) e nell'evento finale dello stream (campo `timing`). `ClientContato` avvolge il client
Anthropic e conta le chiamate (e i token quando la risposta li riporta) senza cambiare chi lo usa.
"""
from __future__ import annotations

import time
from typing import Optional


class Cronometro:
    def __init__(self) -> None:
        self.t0 = time.monotonic()
        self.marche: dict = {}
        self.chiamate = 0
        self.token_in = 0
        self.token_out = 0
        self.elenco: list = []          # (istante, max_tokens) di ogni chiamata contata

    def segna(self, nome: str) -> float:
        t = round(time.monotonic() - self.t0, 3)
        self.marche.setdefault(nome, t)
        return t

    def conta(self, max_tokens: Optional[int] = None) -> None:
        self.chiamate += 1
        self.elenco.append((round(time.monotonic() - self.t0, 3), max_tokens))

    def aggiungi_uso(self, uso) -> None:
        try:
            self.token_in += int(getattr(uso, "input_tokens", 0) or 0)
            self.token_out += int(getattr(uso, "output_tokens", 0) or 0)
        except Exception:
            pass

    def riepilogo(self) -> dict:
        m = self.marche
        tot = round(time.monotonic() - self.t0, 3)

        def d(a: str, b: str) -> Optional[float]:
            return round(m[b] - m[a], 3) if a in m and b in m else None

        return {
            "preparazione_s": m.get("preparato"),
            "fonti_s": d("preparato", "fonti"),
            "primo_token_s": m.get("primo_token"),
            "primo_token_dopo_fonti_s": d("fonti", "primo_token"),
            "generazione_s": d("primo_token", "ultimo_token"),
            "verifica_s": d("ultimo_token", "verificato"),
            "salvataggio_s": d("verificato", "salvato"),
            "totale_s": tot,
            "chiamate_llm": self.chiamate,
            "token_in": self.token_in or None,
            "token_out": self.token_out or None,
        }

    def riga(self) -> str:
        return " ".join(f"{k}={v}" for k, v in self.riepilogo().items() if v is not None)


class _Messaggi:
    def __init__(self, messaggi, cron: Cronometro) -> None:
        self._m, self._c = messaggi, cron

    def create(self, *a, **k):
        self._c.conta(k.get("max_tokens"))
        r = self._m.create(*a, **k)
        self._c.aggiungi_uso(getattr(r, "usage", None))
        return r

    def stream(self, *a, **k):
        self._c.conta(k.get("max_tokens"))
        return self._m.stream(*a, **k)

    def __getattr__(self, nome):
        return getattr(self._m, nome)


class ClientContato:
    """Avvolge un client Anthropic: le chiamate a `messages.create` e `messages.stream` finiscono nel cronometro."""

    def __init__(self, client, cron: Cronometro) -> None:
        self._client = client
        self.messages = _Messaggi(client.messages, cron)

    def __getattr__(self, nome):
        return getattr(self._client, nome)
