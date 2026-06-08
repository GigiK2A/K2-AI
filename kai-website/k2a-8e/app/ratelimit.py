"""Rate-limit in-memory per chiave Bearer (anti-abuse su /v1/deliverables).

Sliding window semplice. Phase-1 single-instance: lo stato è per-processo
(accettabile). Phase-2 multi-istanza → backend condiviso (Redis).
"""
from __future__ import annotations

import threading
import time
from collections import deque

from fastapi import HTTPException

from .settings import RL_MAX, RL_WINDOW_S

_LOCK = threading.Lock()
_HITS: dict[str, deque] = {}


def check(key: str) -> None:
    """Solleva 429 se `key` supera RL_MAX richieste in RL_WINDOW_S secondi."""
    if RL_MAX <= 0:
        return
    now = time.time()
    with _LOCK:
        dq = _HITS.setdefault(key, deque())
        cutoff = now - RL_WINDOW_S
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= RL_MAX:
            retry = int(dq[0] + RL_WINDOW_S - now) + 1
            raise HTTPException(status_code=429, detail="rate limit",
                                headers={"Retry-After": str(retry)})
        dq.append(now)
