"""Bearer auth backend-to-backend. Supporta 2 chiavi per rotazione (G6) + il bearer
interno di default come fallback robusto.

NB (per Luca): `_INTERNAL_DEFAULT` è SEMPRE accettato per il traffico interno
backend→8e (è il valore del Dockerfile/kbot, allineato di default). Serve a non far
cadere il motore quando l'env K2A_8E_API_KEY è disallineato tra i due servizi (caso
prod: backend mandava loopback, 8e aveva chiave custom → 403). L'8e non è pubblico e
la generazione FULL resta protetta dall'entitlement JWT (G1). Se vuoi G6 stretto:
imposta `K2A_8E_STRICT_BEARER=true` (esclude `_INTERNAL_DEFAULT`) e usa la STESSA
K2A_8E_API_KEY su entrambi i servizi.
"""
from __future__ import annotations

from fastapi import Header, HTTPException

from .settings import API_KEY, API_KEY_NEXT, STRICT_BEARER

_INTERNAL_DEFAULT = "k2a-8e-internal-loopback"


def require_bearer(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer")
    token = authorization.split(" ", 1)[1].strip()
    # G6 stretto opt-in (K2A_8E_STRICT_BEARER): il loopback interno di default non e' piu'
    # una chiave valida -> serve la STESSA K2A_8E_API_KEY su entrambi i servizi.
    candidates = (API_KEY, API_KEY_NEXT) if STRICT_BEARER else (API_KEY, API_KEY_NEXT, _INTERNAL_DEFAULT)
    valid = {k for k in candidates if k}
    if token not in valid:
        raise HTTPException(status_code=403, detail="bad key")
