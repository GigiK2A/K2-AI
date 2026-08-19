"""Memoria durevole del loop di autonomia.

`seen`, `seen_mail`, `last_agents_day`, `last_prospect_day` erano variabili Python: al
riavvio il loop ripartiva da zero e ti rimandava card già viste. Il 19 ago 2026 il
servizio è ripartito tre volte e tre volte hai ricevuto le stesse otto decisioni.

È il fattore 5 dei 12-Factor Agents (unify execution state and business state) e il
motivo per cui nel 2026 tutti stanno andando verso l'esecuzione durevole: uno stato che
non sopravvive al riavvio non è stato, è una cache.

Sta in `shared_memory` — tabella già in allowlist, schema {key, value, category,
updated_by} — così non serve nessuna DDL su una produzione a cui non abbiamo il DSN.
Tutto best-effort: se Supabase non risponde il loop funziona come prima, in memoria.
"""
from __future__ import annotations

import json
from typing import Any

CATEGORIA = "loop_stato"
LIMITE_ID = 500          # quanti id ricordare per chiave: oltre, i più vecchi cadono


class StatoLoop:
    """Insiemi di id già gestiti e marcatori di giornata, che sopravvivono al riavvio."""

    def __init__(self, client: Any = None) -> None:
        self._c = client
        self._cache: dict[str, Any] = {}

    # ---- lettura/scrittura grezza ----
    def _leggi(self, chiave: str) -> Any:
        if chiave in self._cache:
            return self._cache[chiave]
        val = None
        if self._c is not None:
            try:
                righe = self._c.select("shared_memory", {
                    "select": "value", "key": f"eq.{chiave}", "limit": "1"})
                if righe:
                    grezzo = righe[0].get("value")
                    val = json.loads(grezzo) if isinstance(grezzo, str) else grezzo
            except Exception:
                val = None
        self._cache[chiave] = val
        return val

    def _scrivi(self, chiave: str, valore: Any) -> None:
        self._cache[chiave] = valore
        if self._c is None:
            return
        riga = {"key": chiave, "value": json.dumps(valore, ensure_ascii=False),
                "category": CATEGORIA, "updated_by": "autonomy_loop"}
        try:
            esistente = self._c.select("shared_memory",
                                       {"select": "key", "key": f"eq.{chiave}", "limit": "1"})
            if esistente:
                self._c.update("shared_memory", {"key": f"eq.{chiave}"}, riga)
            else:
                self._c.insert("shared_memory", riga)
        except Exception:
            pass      # il loop continua in memoria: meglio card doppie che loop fermo

    # ---- insiemi di id già notificati ----
    def visti(self, nome: str) -> set:
        val = self._leggi(f"{CATEGORIA}:{nome}")
        return set(val) if isinstance(val, list) else set()

    def segna_visto(self, nome: str, ids: list) -> set:
        """Aggiunge id all'insieme e lo persiste. Ritorna l'insieme aggiornato."""
        insieme = self.visti(nome)
        insieme.update(ids)
        if len(insieme) > LIMITE_ID:
            # tiene i più recenti: gli id crescono, quindi bastano gli ultimi
            ordinati = sorted(insieme, key=lambda x: str(x))[-LIMITE_ID:]
            insieme = set(ordinati)
        self._scrivi(f"{CATEGORIA}:{nome}", sorted(insieme, key=lambda x: str(x)))
        return insieme

    # ---- marcatori "una volta al giorno" ----
    def giorno(self, nome: str) -> int | None:
        val = self._leggi(f"{CATEGORIA}:giorno:{nome}")
        return int(val) if isinstance(val, (int, float, str)) and str(val).isdigit() else None

    def segna_giorno(self, nome: str, yday: int) -> None:
        self._scrivi(f"{CATEGORIA}:giorno:{nome}", int(yday))
