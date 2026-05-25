"""Session-cookie auth — single user (Luigi).

- POST /api/auth/login   {username, password} → sets signed httpOnly cookie
- POST /api/auth/logout  → clears cookie
- GET  /api/auth/me      → current user info
- Dependency `require_auth` for protected endpoints.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

import bcrypt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import BaseModel

from app.settings import Settings, get_settings

_INSECURE_SESSION_SECRETS = {
    "",
    "dev-only-not-secure-change-me-in-production-please-32b",
}
_LOGIN_ATTEMPTS: Dict[str, Deque[float]] = defaultdict(deque)
_LOGIN_WINDOW_S = 15 * 60
_LOGIN_MAX_ATTEMPTS = 5


def _record_login_failure(ip: str) -> None:
    now = time.time()
    bucket = _LOGIN_ATTEMPTS[ip]
    while bucket and bucket[0] < now - _LOGIN_WINDOW_S:
        bucket.popleft()
    bucket.append(now)


def _is_login_rate_limited(ip: str) -> bool:
    now = time.time()
    bucket = _LOGIN_ATTEMPTS[ip]
    while bucket and bucket[0] < now - _LOGIN_WINDOW_S:
        bucket.popleft()
    return len(bucket) >= _LOGIN_MAX_ATTEMPTS


def _reset_login_attempts(ip: str) -> None:
    _LOGIN_ATTEMPTS.pop(ip, None)


# ── Serializer ───────────────────────────────────────────────────────────────

def _serializer(settings: Settings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.board_session_secret, salt="k2board.session.v1")


def _issue_session(settings: Settings, username: str) -> str:
    payload = {"u": username, "iat": int(time.time())}
    return _serializer(settings).dumps(payload)


def _read_session(settings: Settings, token: str) -> Optional[dict]:
    try:
        return _serializer(settings).loads(
            token, max_age=settings.board_session_max_age_seconds
        )
    except (BadSignature, SignatureExpired):
        return None


# ── Models ───────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class CurrentUser(BaseModel):
    username: str


# ── Dependencies ─────────────────────────────────────────────────────────────

def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Optional[CurrentUser]:
    token = request.cookies.get(settings.board_session_cookie_name)
    if not token:
        return None
    data = _read_session(settings, token)
    if not data:
        return None
    return CurrentUser(username=data.get("u", ""))


def require_auth(user: Optional[CurrentUser] = Depends(get_current_user)) -> CurrentUser:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="auth required")
    return user


# ── Router ───────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


@router.post("/login")
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> dict:
    if settings.is_production and settings.board_session_secret in _INSECURE_SESSION_SECRETS:
        # Refuse to mint sessions against the dev default — those tokens are
        # forgeable by anyone with the source code.
        raise HTTPException(status_code=500, detail="server misconfigured: session secret not set")

    ip = (request.client.host if request.client else "unknown") or "unknown"
    if _is_login_rate_limited(ip):
        raise HTTPException(status_code=429, detail="too many login attempts, retry later")

    if body.username != settings.board_username or not _verify_password(
        body.password, settings.board_password_hash
    ):
        _record_login_failure(ip)
        raise HTTPException(status_code=401, detail="invalid credentials")

    _reset_login_attempts(ip)
    token = _issue_session(settings, body.username)
    response.set_cookie(
        key=settings.board_session_cookie_name,
        value=token,
        max_age=settings.board_session_max_age_seconds,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/",
    )
    return {"ok": True, "user": {"username": body.username}}


@router.post("/logout")
def logout(response: Response, settings: Settings = Depends(get_settings)) -> dict:
    response.delete_cookie(settings.board_session_cookie_name, path="/")
    return {"ok": True}


@router.get("/me")
def me(user: CurrentUser = Depends(require_auth)) -> dict:
    return {"user": user.model_dump()}
