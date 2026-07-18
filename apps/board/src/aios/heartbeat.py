"""Heartbeat per-agente — ogni agente si sveglia col suo ritmo (Paperclip #4).

Prima l'AIOS aveva UN solo battito globale: tutti e 6 gli agenti giravano una
volta al giorno, alla stessa ora. Paperclip dà a ogni agente il proprio heartbeat
("scheduled intervals — every 30 seconds, every hour, every day — you configure it").

Qui ogni dominio ha un intervallo (secondi); a ogni tick del loop di autonomia si
chiede allo scheduler quali agenti sono "dovuti" e si fanno partire SOLO quelli
(rispettando comunque il budget hard-stop: chi ha sforato il tetto non parte).

Opt-in e non-breaking: senza `AIOS_HEARTBEATS` il loop mantiene il vecchio batch
giornaliero. Con `AIOS_HEARTBEATS` impostato, subentra il ritmo per-agente.

Stato in memoria (last-run per dominio) + persistenza best-effort su `aios_heartbeats`
così un riavvio non rifà ripartire tutti gli agenti in blocco.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Optional

DEFAULT_INTERVAL_SECONDS = 86_400   # 1 giorno (mantiene il comportamento storico)
STATE_TABLE = "aios_heartbeats"


class HeartbeatScheduler:
    """Decide quali agenti sono dovuti a un dato istante, per intervallo per-agente."""

    def __init__(self, intervals: dict[str, int], default_seconds: int = DEFAULT_INTERVAL_SECONDS,
                 client: Any = None) -> None:
        self._intervals = {k: int(v) for k, v in intervals.items()}
        self._default = int(default_seconds)
        self._client = client
        self._last: dict[str, float] = {}
        self._hydrated = False

    # -- config ------------------------------------------------------------
    def interval_for(self, domain: str) -> int:
        return self._intervals.get(domain, self._default)

    @staticmethod
    def enabled() -> bool:
        """True se il ritmo per-agente è configurato (altrimenti: batch giornaliero)."""
        return bool(os.environ.get("AIOS_HEARTBEATS", "").strip())

    @classmethod
    def from_env(cls, client: Any = None) -> "HeartbeatScheduler":
        """Intervalli da env:
        - AIOS_HEARTBEATS = '{"marketing": 43200, "finance": 86400}'  (secondi per dominio)
        - AIOS_HEARTBEAT_DEFAULT_SECONDS = intervallo per i domini non elencati.
        """
        default = int(os.environ.get("AIOS_HEARTBEAT_DEFAULT_SECONDS",
                                     str(DEFAULT_INTERVAL_SECONDS)))
        intervals: dict[str, int] = {}
        raw = os.environ.get("AIOS_HEARTBEATS", "").strip()
        if raw:
            try:
                for dom, secs in json.loads(raw).items():
                    intervals[str(dom)] = int(secs)
            except Exception:
                pass
        return cls(intervals, default, client)

    # -- persistenza -------------------------------------------------------
    def _hydrate(self, domains: list[str]) -> None:
        if self._hydrated or self._client is None:
            return
        self._hydrated = True
        try:
            rows = self._client.select(STATE_TABLE, {"select": "actor,last_run_epoch"})
            for r in rows or []:
                actor = r.get("actor")
                if actor is not None and r.get("last_run_epoch") is not None:
                    self._last[str(actor)] = float(r["last_run_epoch"])
        except Exception:
            pass

    def _persist(self, domain: str, now_epoch: float) -> None:
        if self._client is None:
            return
        try:
            self._client.upsert(STATE_TABLE, {
                "actor": domain, "last_run_epoch": round(now_epoch, 3),
                "interval_seconds": self.interval_for(domain),
                "last_run_at": datetime.now(timezone.utc).isoformat()},
                on_conflict="actor")
        except Exception:
            pass

    # -- scheduling --------------------------------------------------------
    def due(self, domains: list[str], now_epoch: float) -> list[str]:
        """Domini il cui intervallo è scaduto (o mai partiti)."""
        self._hydrate(domains)
        out: list[str] = []
        for d in domains:
            last = self._last.get(d)
            if last is None or (now_epoch - last) >= self.interval_for(d):
                out.append(d)
        return out

    def mark_ran(self, domain: str, now_epoch: float) -> None:
        self._last[domain] = now_epoch
        self._persist(domain, now_epoch)

    def next_due_in(self, domain: str, now_epoch: float) -> float:
        """Secondi al prossimo battito (0 = dovuto ora). Per cockpit/debug."""
        last = self._last.get(domain)
        if last is None:
            return 0.0
        return max(0.0, self.interval_for(domain) - (now_epoch - last))
