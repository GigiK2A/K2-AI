"""Supabase JWT validation.

Modern Supabase projects sign access tokens with asymmetric keys (ECC P-256 / ES256
or RSA / RS256) and expose the public keys via a JWKS endpoint. This module fetches
that JWKS, caches it, and validates incoming Bearer tokens against it.

A legacy fallback to HS256 with a shared secret is kept for older projects that
still use the symmetric flow.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

import jwt
from jwt import PyJWKClient
from fastapi import Header, HTTPException, status

from ..settings import SUPABASE_JWT_JWKS_URL, SUPABASE_JWT_SECRET

log = logging.getLogger(__name__)

_JWKS_CACHE_TTL = 600  # seconds
_jwks_client: Optional[PyJWKClient] = None
_jwks_loaded_at: float = 0.0


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: Optional[str]
    has_paid: bool
    raw: dict


def _get_jwks_client() -> Optional[PyJWKClient]:
    global _jwks_client, _jwks_loaded_at
    if not SUPABASE_JWT_JWKS_URL:
        return None
    now = time.time()
    if _jwks_client and (now - _jwks_loaded_at) < _JWKS_CACHE_TTL:
        return _jwks_client
    _jwks_client = PyJWKClient(SUPABASE_JWT_JWKS_URL, cache_keys=True)
    _jwks_loaded_at = now
    return _jwks_client


def _decode(token: str) -> dict:
    """Try JWKS first (asymmetric), fall back to HS256 if the project is legacy."""
    last_exc: Optional[Exception] = None

    jwks = _get_jwks_client()
    if jwks is not None:
        try:
            signing_key = jwks.get_signing_key_from_jwt(token).key
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg", "ES256")
            return jwt.decode(
                token,
                signing_key,
                algorithms=[alg],
                audience="authenticated",
                options={"verify_exp": True, "verify_aud": True},
            )
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            log.debug("JWKS decode failed: %s", exc)

    if SUPABASE_JWT_SECRET:
        try:
            return jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_exp": True, "verify_aud": True},
            )
        except Exception as exc:  # noqa: BLE001
            last_exc = exc

    if last_exc:
        raise last_exc
    raise RuntimeError(
        "No Supabase JWT verification configured: set SUPABASE_JWT_JWKS_URL or SUPABASE_JWT_SECRET"
    )


def _payload_to_user(payload: dict) -> AuthUser:
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("token missing sub claim")
    email = payload.get("email")
    app_meta = payload.get("app_metadata") or {}
    user_meta = payload.get("user_metadata") or {}
    has_paid = bool(app_meta.get("has_paid") or user_meta.get("has_paid"))
    return AuthUser(id=user_id, email=email, has_paid=has_paid, raw=payload)


def _extract_token(header_value: Optional[str]) -> Optional[str]:
    if not header_value:
        return None
    parts = header_value.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip() or None
    return header_value.strip() or None


def require_user(authorization: Optional[str] = Header(default=None)) -> AuthUser:
    """FastAPI dependency: 401 if no valid Supabase JWT."""
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing token")
    try:
        return _payload_to_user(_decode(token))
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"invalid token: {exc}")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


def optional_user(authorization: Optional[str] = Header(default=None)) -> Optional[AuthUser]:
    """FastAPI dependency: returns AuthUser if token is valid, else None. Never raises."""
    token = _extract_token(authorization)
    if not token:
        return None
    try:
        return _payload_to_user(_decode(token))
    except Exception:
        return None
