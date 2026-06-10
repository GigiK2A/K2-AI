"""Verifica entitlement JWT (membrana G1) — stateless, segreto condiviso col K-BOT.

L'8e verifica firma + scadenza + che il service_id del token corrisponda alla
richiesta. Niente chiamate al K-BOT. Se il segreto non è configurato (dev),
si accetta qualunque token non vuoto (modalità permissiva) per non bloccare i test.
"""
from __future__ import annotations

import logging
from typing import Optional

from .settings import ENTITLEMENT_SECRET, ENTITLEMENT_DEV

log = logging.getLogger("8e.entitlement")


def verify(token: Optional[str], service_id: str) -> tuple[bool, str]:
    """Ritorna (ok, motivo). ok=False con motivo se token invalido/scaduto/mismatch."""
    if not token:
        return False, "missing"

    if not ENTITLEMENT_SECRET:
        # FAIL-CLOSED: senza segreto si RIFIUTA (altrimenti una misconfig in prod
        # bypassa il pagamento). Permissivo solo con opt-in esplicito K2A_8E_ENTITLEMENT_DEV.
        if ENTITLEMENT_DEV:
            return True, "dev-no-secret"
        log.error("K2A_ENTITLEMENT_SECRET non configurato e non in dev → entitlement RIFIUTATO")
        return False, "not_configured"

    try:
        import jwt
    except ImportError:
        log.error("PyJWT non installato: impossibile verificare entitlement")
        return False, "jwt_unavailable"

    try:
        claims = jwt.decode(
            token, ENTITLEMENT_SECRET, algorithms=["HS256"],
            audience="k2a-8e", issuer="k2a-kbot",
            options={"require": ["exp", "iat"]},
        )
    except jwt.ExpiredSignatureError:
        return False, "expired"
    except jwt.InvalidTokenError as exc:
        return False, f"invalid: {exc}"

    if claims.get("service_id") != service_id:
        return False, "service_mismatch"
    return True, "ok"
