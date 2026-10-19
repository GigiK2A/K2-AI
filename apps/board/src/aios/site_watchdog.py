"""Controllo dall'esterno del sito K2-AI: avvisa su Telegram quando qualcosa si ferma.

Perché sta nel board: è un servizio Railway SEPARATO dal sito, già collegato a Telegram. Un sito che
muore non può avvisare da solo (è quello che è successo: backend giù, `/api/health` a 200, nessuno se
n'è accorto). Il controllo è volutamente superficiale — niente chiamate al modello, quindi nessun
costo e nessun carico sulla GPU:

- sito:       GET https://www.k2-ai.it/api/health        → 200 (503 = un processo figlio è giù)
- backend K-BOT (Python, dietro il sito): GET /api/kbot/diagnostics → 200 o 401 (502/timeout = giù)
- motore 8e:  GET /health                                → 200
- modello:    GET <funnel>/health/liveliness             → 200 (solo se SITE_WATCHDOG_LLM_URL è impostata)

Un guasto si segnala dopo FAIL_THRESHOLD controlli consecutivi falliti (default 2 → ~2 minuti), si
ripete ogni REMIND_MIN minuti finché dura, e si chiude con un messaggio di ripristino.

Variabili: SITE_WATCHDOG=0 spegne · SITE_WATCHDOG_INTERVAL (s, default 60) · SITE_WATCHDOG_SITE_URL ·
SITE_WATCHDOG_8E_URL · SITE_WATCHDOG_LLM_URL · TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID (già presenti).
"""
from __future__ import annotations

import os
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Optional

FAIL_THRESHOLD = int(os.environ.get("SITE_WATCHDOG_FAILS", "2"))
REMIND_MIN = int(os.environ.get("SITE_WATCHDOG_REMIND_MIN", "30"))
_UA = "Mozilla/5.0 (K2-AI site watchdog)"


@dataclass(frozen=True)
class Target:
    name: str
    url: str
    ok_codes: tuple = (200,)
    note: str = ""


def default_targets() -> list[Target]:
    site = os.environ.get("SITE_WATCHDOG_SITE_URL", "https://www.k2-ai.it").rstrip("/")
    eng = os.environ.get("SITE_WATCHDOG_8E_URL", "https://k2-ai-8e-production.up.railway.app").rstrip("/")
    out = [
        Target("sito", f"{site}/api/health", (200,), "503 = un processo del sito è giù"),
        Target("backend K-BOT", f"{site}/api/kbot/diagnostics", (200, 401), "502 = backend Python giù"),
        Target("motore 8e", f"{eng}/health", (200,)),
    ]
    llm = os.environ.get("SITE_WATCHDOG_LLM_URL", "").rstrip("/")
    if llm:
        out.append(Target("modello (shim/Funnel)", f"{llm}/health/liveliness", (200,),
                          "il PC con lo shim potrebbe essere spento o senza rete"))
    return out


def probe(t: Target, timeout: float = 15.0) -> tuple[bool, str]:
    """(ok, dettaglio). Mai eccezioni: un errore di rete è un esito 'giù'."""
    req = urllib.request.Request(t.url, headers={"User-Agent": _UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {str(e)[:80]}"
    ms = int((time.time() - t0) * 1000)
    return code in t.ok_codes, f"HTTP {code} in {ms} ms"


@dataclass
class _State:
    fails: int = 0
    down_since: Optional[float] = None
    last_alert: Optional[float] = None
    detail: str = ""


@dataclass
class Monitor:
    targets: list
    notify: Callable[[str], None]
    probe_fn: Callable[[Target], tuple] = probe
    clock: Callable[[], float] = time.time
    state: dict = field(default_factory=dict)

    def tick(self) -> list[str]:
        """Un giro di controlli. Ritorna i messaggi inviati (utile ai test)."""
        sent: list[str] = []
        for t in self.targets:
            st = self.state.setdefault(t.name, _State())
            ok, detail = self.probe_fn(t)
            now = self.clock()
            if ok:
                if st.down_since is not None and st.last_alert is not None:
                    mins = max(1, int((now - st.down_since) / 60))
                    sent.append(f"🟢 {t.name}: di nuovo raggiungibile dopo circa {mins} min ({detail}).")
                st.fails, st.down_since, st.last_alert, st.detail = 0, None, None, detail
                continue
            st.fails += 1
            st.detail = detail
            if st.down_since is None:
                st.down_since = now
            if st.fails < FAIL_THRESHOLD:
                continue
            if st.last_alert is None:
                sent.append(f"🔴 {t.name} NON risponde ({detail}). {t.note}".strip())
                st.last_alert = now
            elif now - st.last_alert >= REMIND_MIN * 60:
                mins = int((now - st.down_since) / 60)
                sent.append(f"🔴 {t.name} è giù da circa {mins} min ({detail}).")
                st.last_alert = now
        for m in sent:
            try:
                self.notify(m)
            except Exception:  # noqa: BLE001 — un invio fallito non deve fermare il controllo
                pass
        return sent


def run_forever(monitor: Optional[Monitor] = None, interval: Optional[float] = None) -> None:
    if os.environ.get("SITE_WATCHDOG", "1") == "0":
        return
    from aios.notify import telegram
    mon = monitor or Monitor(default_targets(), telegram.send_text)
    every = interval or float(os.environ.get("SITE_WATCHDOG_INTERVAL", "60"))
    print(f"[site-watchdog] attivo: {len(mon.targets)} controlli ogni {every:.0f}s "
          f"(Telegram {'sì' if telegram.enabled() else 'NO — manca token/chat'})", flush=True)
    while True:
        try:
            mon.tick()
        except Exception as e:  # noqa: BLE001
            print(f"[site-watchdog] errore nel giro: {e!r}", flush=True)
        time.sleep(every)


def start_thread() -> threading.Thread:
    th = threading.Thread(target=run_forever, daemon=True, name="site-watchdog")
    th.start()
    return th
