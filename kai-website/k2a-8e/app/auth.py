"""Bearer auth backend-to-backend. Supporta 2 chiavi per rotazione (G6)."""
from __future__ import annotations

from fastapi import Header, HTTPException

from .settings import API_KEY, API_KEY_NEXT


def require_bearer(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer")
    token = authorization.split(" ", 1)[1].strip()
    valid = {k for k in (API_KEY, API_KEY_NEXT) if k}
    if token not in valid:
        raise HTTPException(status_code=403, detail="bad key")
