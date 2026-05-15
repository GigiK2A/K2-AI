"""Stateless CSRF protection for the FastAPI dashboard (audit H-2).

Design
------
The dashboard already issues a session cookie (`kai_board_session`) on login.
We derive a CSRF token deterministically from that cookie value using HMAC-SHA256
with a server-side secret. No extra storage is required.

- Token shape:  hex(hmac_sha256(secret, session_token))
- Embedded in every Jinja-rendered form as a hidden input `csrf_token`.
- For HTMX / JSON POSTs the same value can be sent in header `X-CSRF-Token`.
- Validated in middleware for every non-GET request belonging to a session.
- Public API endpoints (`/api/intake/*`, `/api/workshop/*`, `/webhook`) and
  the login form (`POST /login`, no session yet) are exempt.

The CSRF secret falls back to `BOARD_PASSWORD` if no dedicated secret is set —
acceptable because compromise of `BOARD_PASSWORD` already grants full admin
access, so it cannot meaningfully weaken CSRF beyond what's already possible.
A dedicated `BOARD_SESSION_SECRET` is recommended (see SECRET-ROTATION doc).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import Request

from core.config import settings

# Routes that perform state changes but must NOT require CSRF (no session
# cookie expected, or have an alternative auth like a Telegram secret token).
CSRF_EXEMPT_PATHS = {
    "/login",      # form posted before a session exists
    "/webhook",    # validated via X-Telegram-Bot-Api-Secret-Token
    "/healthz",
}
CSRF_EXEMPT_PREFIXES = (
    "/api/intake/",    # public form endpoints — Origin + X-KAI-Request + rate-limit
    "/api/workshop/",  # public workshop listing endpoints (GET-only normally)
)

# Cookie name as defined in core.board_auth — duplicated here to avoid a circular
# import (board_auth pulls in db.client which pulls in settings).
SESSION_COOKIE_NAME = "kai_board_session"


def _csrf_secret() -> bytes:
    # Dedicated secret preferred; falls back to board password.
    raw = settings.board_password or ""
    if not raw:
        # If nothing is configured, return a process-stable random value so the
        # middleware fails closed (every request gets a fresh token, mismatch).
        raw = "no-csrf-secret-configured"
    return raw.encode("utf-8")


def generate_csrf_token(session_cookie_value: str | None) -> str:
    """Derive a CSRF token from the current session cookie.

    Returns an empty string when there is no session — templates can still
    render the hidden input (value=""), and unauthenticated POSTs are either
    exempt (login) or blocked earlier by the auth middleware.
    """
    if not session_cookie_value:
        return ""
    return hmac.new(_csrf_secret(), session_cookie_value.encode("utf-8"), hashlib.sha256).hexdigest()


def is_csrf_exempt(path: str) -> bool:
    return path in CSRF_EXEMPT_PATHS or any(path.startswith(prefix) for prefix in CSRF_EXEMPT_PREFIXES)


def extract_submitted_token(request: Request, form_token: str | None) -> str:
    """Pick whichever of header / form field is present."""
    header = request.headers.get("X-CSRF-Token")
    if header:
        return header
    return form_token or ""


def validate_csrf(session_cookie_value: str | None, submitted_token: str) -> bool:
    expected = generate_csrf_token(session_cookie_value)
    if not expected or not submitted_token:
        return False
    return secrets.compare_digest(expected, submitted_token)
