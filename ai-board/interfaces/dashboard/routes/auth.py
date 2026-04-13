from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from core.board_auth import SESSION_COOKIE_NAME, authenticate_user, create_env_session, create_session, delete_session
from core.config import settings
from interfaces.dashboard.routes import render

router = APIRouter()


@router.get("/login")
async def login_page(request: Request, next: str = "/"):
    user = getattr(request.state, "board_user", None)
    if user:
        return RedirectResponse(url=next or "/", status_code=303)
    return render(
        request,
        "login.html",
        {
            "request": request,
            "next": next or "/",
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
    user = authenticate_user(email, password)
    if not user:
        return render(
            request,
            "login.html",
            {
                "request": request,
                "next": next or "/",
                "error": "Credenziali non valide o account non attivo.",
            },
        )

    if user.get("is_env"):
        token, expires_at = create_env_session(user, request)
    else:
        token, expires_at = create_session(user["id"], request)

    response = RedirectResponse(url=next or "/", status_code=303)
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
