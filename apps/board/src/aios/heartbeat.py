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

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from typing import Any, Optional

DEFAULT_INTERVAL_SECONDS = 86_400   # 1 giorno (mantiene il comportamento storico)
STATE_TABLE = "aios_heartbeats"


class HeartbeatScheduler:
    """Decide quali agenti sono dovuti a un dato istante, per intervallo per-agente."""

    def __init__(self, intervals: dict[str, int], default_seconds: int = DEFAULT_INTERVAL_SECONDS,
                 client: Any = None, sfasa: bool = False) -> None:
        self._intervals = {k: int(v) for k, v in intervals.items()}
        self._default = int(default_seconds)
        self._client = client
        # Politica di risveglio. False = storica (dovuto appena passa l'intervallo, tutti
        # insieme se sono partiti insieme). True = ognuno ha la SUA ora dentro
        # l'intervallo. Default False per non cambiare il contratto di chi costruisce lo
        # scheduler a mano; `from_env` la accende, cioè in produzione.
        self._sfasa = bool(sfasa)
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
        # in produzione i reparti si sfasano: senza, arrivano tutte le notifiche
        # insieme una volta al giorno (segnalato dall'owner il 19 ago 2026).
        sfasa = os.environ.get("AIOS_SFASA_RISVEGLI", "1").strip() not in ("0", "false", "no")
        return cls(intervals, default, client, sfasa=sfasa)

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
    def sfasamento(self, domain: str) -> int:
        """Offset stabile del dominio dentro il suo intervallo.

        Senza questo il branco resta sincronizzato per sempre: al primo giro nessun
        dominio ha uno stato, quindi partono TUTTI insieme; `mark_ran` scrive la stessa
        ora per tutti e 24 ore dopo sono di nuovo tutti dovuti nello stesso tick. Il
        risultato, dal lato dell'owner, è una raffica di notifiche una volta al giorno
        invece di un'azienda che lavora durante la giornata.

        L'offset viene dal nome del dominio (stabile fra i riavvii, nessuno stato in
        più) e distribuisce le soglie lungo l'intervallo."""
        intervallo = max(1, self.interval_for(domain))
        digest = hashlib.sha1(domain.encode("utf-8")).hexdigest()[:8]
        return int(digest, 16) % intervallo

    def finestra(self, domain: str) -> float:
        """Ampiezza della finestra di risveglio: dentro questa il reparto parte.
        Deve essere >= di un tick del loop (30 min) o il risveglio verrebbe saltato."""
        return min(max(1.0, self.interval_for(domain) * 0.1), 3600.0)

    def _dovuto_sfasato(self, domain: str, last: float, now_epoch: float) -> bool:
        """«Ognuno ha la sua ora»: il reparto parte nella sua finestra dentro
        l'intervallo, non appena scattano N secondi dall'ultima volta.

        Tre regole: mai prima del 90% dell'intervallo (nessun giro doppio); recupero
        forzato oltre il 150% (un tick perso per un riavvio non deve costare un giorno);
        altrimenti solo dentro la propria finestra."""
        intervallo = max(1, self.interval_for(domain))
        trascorso = now_epoch - last
        if trascorso < intervallo * 0.9:
            return False
        if trascorso >= intervallo * 1.5:
            return True
        return ((now_epoch + self.sfasamento(domain)) % intervallo) < self.finestra(domain)

    def due(self, domains: list[str], now_epoch: float) -> list[str]:
        """Domini dovuti adesso. Con `sfasa` ognuno ha la sua ora (vedi
        `_dovuto_sfasato`), altrimenti vale la regola storica dell'intervallo secco."""
        self._hydrate(domains)
        out: list[str] = []
        for d in domains:
            last = self._last.get(d)
            if last is None:
                out.append(d)            # mai partito: parte subito
            elif self._sfasa:
                if self._dovuto_sfasato(d, last, now_epoch):
                    out.append(d)
            elif (now_epoch - last) >= self.interval_for(d):
                out.append(d)
        return out

    def mark_ran(self, domain: str, now_epoch: float) -> None:
        self._last[domain] = now_epoch
        self._persist(domain, now_epoch)

    def next_due_in(self, domain: str, now_epoch: float) -> float:
        """Secondi al prossimo battito (0 = dovuto ora). Per cockpit/debug.

        Usa la stessa soglia di `due()`: se qui si calcolasse il semplice
        intervallo-meno-trascorso, il cockpit mostrerebbe un battito che non arriva."""
        last = self._last.get(domain)
        if last is None:
            return 0.0
        if not self._sfasa:
            return max(0.0, self.interval_for(domain) - (now_epoch - last))
        intervallo = max(1, self.interval_for(domain))
        t = now_epoch
        for _ in range(int(intervallo // max(1.0, self.finestra(domain))) + 2):
            if self._dovuto_sfasato(domain, last, t):
                return max(0.0, t - now_epoch)
            t += self.finestra(domain)
        return max(0.0, intervallo - (now_epoch - last))
