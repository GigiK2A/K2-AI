"""Entitlement token (membrana G1) — emesso dal K-BOT, verificato dall'8e.

Il K-BOT, al pagamento verificato di un servizio, firma un JWT HS256 con segreto
condiviso (K2A_ENTITLEMENT_SECRET). L'8e lo verifica stateless (stessa chiave),
senza richiamare il K-BOT. Claim minimi + exp breve + anti-replay (jti).
"""
from __future__ import annotations

import secrets
import time
from typing import Optional

import jwt

from ..settings import ENTITLEMENT_SECRET, ENTITLEMENT_TTL_S


def mint(*, user_id: Optional[str], service_id: str, tier: Optional[str],
         session_id: str) -> Optional[str]:
    """Firma un entitlement per un servizio pagato. None se segreto non configurato."""
    if not ENTITLEMENT_SECRET:
        return None
    now = int(time.time())
    payload = {
        "sub": user_id or "anon",
        "service_id": service_id,
        "tier": tier,
        "kbot_session_id": session_id,
        "jti": secrets.token_urlsafe(12),
        "iat": now,
        "exp": now + ENTITLEMENT_TTL_S,
        "iss": "k2a-kbot",
        "aud": "k2a-8e",
    }
    return jwt.encode(payload, ENTITLEMENT_SECRET, algorithm="HS256")
