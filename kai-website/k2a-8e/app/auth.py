"""Bearer auth backend-to-backend. Supporta 2 chiavi per rotazione (G6).

SICUREZZA: nessuna credenziale di default. In passato il bearer `k2a-8e-internal-
loopback` era SEMPRE accettato (comodo ma noto pubblicamente: chiunque raggiungesse
l'8e passava l'auth). Ora la chiave va configurata esplicitamente via K2A_8E_API_KEY.

⚠ DEPLOY (per Luca): questo cambio richiede che la STESSA K2A_8E_API_KEY sia settata
sia sul backend kbot sia sul servizio 8e. Se nessuna chiave è configurata, l'8e
risponde 503 (misconfig) invece di accettare silenziosamente la vecchia default.
"""
from __future__ import annotations

from fastapi import Header, HTTPException

from .settings import API_KEY, API_KEY_NEXT


def require_bearer(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer")
    token = authorization.split(" ", 1)[1].strip()
    valid = {k for k in (API_KEY, API_KEY_NEXT) if k}
    if not valid:
        # Fail-closed: nessuna chiave configurata è una misconfig, non un via libero.
        raise HTTPException(status_code=503, detail="8e API key not configured")
    if token not in valid:
        raise HTTPException(status_code=403, detail="bad key")
