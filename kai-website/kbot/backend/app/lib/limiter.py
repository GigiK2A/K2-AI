"""Shared SlowAPI Limiter instance.

Kept in its own module to avoid circular imports between api/* and main.py.

The FastAPI process sits behind a Node proxy (server.js), so the immediate
peer is always 127.0.0.1. We must honour ``X-Forwarded-For`` to get the real
client IP for rate limiting.
"""
from __future__ import annotations

from slowapi import Limiter


def _real_ip(request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        # X-Forwarded-For: client, proxy1, proxy2 — leftmost is original client.
        return fwd.split(",")[0].strip() or "unknown"
    client = getattr(request, "client", None)
    return client.host if client and getattr(client, "host", None) else "unknown"


limiter = Limiter(key_func=_real_ip)
