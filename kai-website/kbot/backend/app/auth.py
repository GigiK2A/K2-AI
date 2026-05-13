from __future__ import annotations

import os
from dataclasses import dataclass

import jwt
from jwt import PyJWKClient


@dataclass
class ClerkUser:
    clerk_user_id: str
    has_paid: bool


_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        url = os.getenv("CLERK_JWKS_URL", "")
        if not url:
            raise RuntimeError("CLERK_JWKS_URL non configurato")
        _jwks_client = PyJWKClient(url, cache_keys=True)
    return _jwks_client


def _decode_token(token: str) -> dict | None:
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_exp": True},
        )
    except Exception:
        return None


def extract_clerk_user(token: str | None) -> ClerkUser | None:
    if not token:
        return None
    payload = _decode_token(token)
    if not payload:
        return None
    clerk_user_id = payload.get("sub")
    if not clerk_user_id:
        return None
    meta = payload.get("public_metadata") or payload.get("publicMetadata") or {}
    has_paid = bool(meta.get("has_paid", False))
    return ClerkUser(clerk_user_id=clerk_user_id, has_paid=has_paid)


def extract_token_from_header(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization[7:]
