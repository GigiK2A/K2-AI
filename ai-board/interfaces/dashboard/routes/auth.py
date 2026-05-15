from __future__ import annotations

from urllib.parse import urlparse

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from core.board_auth import SESSION_COOKIE_NAME, authenticate_user, create_env_session, create_session, delete_session
from core.config import settings
from interfaces.dashboard.routes import render

router = APIRouter()


def _safe_next(next_url: str | None) -> str:
    """Validate the post-login redirect target to prevent open-redirect (audit H-3).

    Only allow same-origin relative paths starting with a single '/'.
    Reject protocol-relative URLs (//evil.com), URLs with scheme/netloc,
    backslashes, and anything containing ':' (catches javascript:, mailto:, etc).
    """
    if not next_url or not next_url.startswith("/"):
        return "/"
    if next_url.startswith("//") or "\\" in next_url or ":" in next_url:
        return "/"
    parsed = urlparse(next_url)
    if parsed.netloc or parsed.scheme:
        return "/"
    return next_url


@router.get("/login")
async def login_page(request: Request, next: str = "/"):
    safe_next = _safe_next(next)
    user = getattr(request.state, "board_user", None)
    if user:
        return RedirectResponse(url=safe_next, status_code=303)
    return render(
        request,
        "login.html",
        {
            "request": request,
            "next": safe_next,
            "error": None,
        },
    )


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form(default="/"),
):
    safe_next = _safe_next(next)
    user = authenticate_user(email, password)
    if not user:
        return render(
            request,
            "login.html",
            {
                "request": request,
                "next": safe_next,
                "error": "Credenziali non valide o account non attivo.",
            },
        )

    if user.get("is_env"):
        token, expires_at = create_env_session(user, request)
    else:
        token, expires_at = create_session(user["id"], request)

    response = RedirectResponse(url=safe_next, status_code=303)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        expires=expires_at,
        max_age=settings.board_session_hours * 3600,
    )
    return response


@router.post("/logout")
async def logout(request: Request):
    delete_session(request.cookies.get(SESSION_COOKIE_NAME))
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response
