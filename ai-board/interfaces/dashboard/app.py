from pathlib import Path
from time import monotonic
import base64
import secrets

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from controllers import agents_router, home_router
from core.board_auth import SESSION_COOKIE_NAME, get_user_from_session
from core.config import get_allowed_origins, settings
from interfaces.dashboard.routes import admin, approvals, auth, board_chat, inbox, lavori, logs, memory, pipeline, public_intake, workshop

PUBLIC_INTAKE_PATHS = {"/api/intake/contact", "/api/intake/kbot-chat"}
AUTH_EXEMPT_PATHS = {"/healthz", "/webhook", "/login"}
AUTH_EXEMPT_PREFIXES = ("/api/intake", "/api/workshop")
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data:; "
        "font-src 'self' data: https://fonts.gstatic.com; "
        "connect-src 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "base-uri 'self'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def _apply_security_headers(request: Request, response: Response) -> Response:
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def _is_auth_exempt(path: str) -> bool:
    return path in AUTH_EXEMPT_PATHS or any(path.startswith(prefix) for prefix in AUTH_EXEMPT_PREFIXES)


def _parse_basic_auth(header_value: str | None) -> tuple[str, str] | None:
    if not header_value or not header_value.startswith("Basic "):
        return None
    try:
        decoded = base64.b64decode(header_value[6:], validate=True).decode("utf-8")
    except Exception:
        return None
    username, separator, password = decoded.partition(":")
    if not separator:
        return None
    return username, password


def _auth_challenge(request: Request) -> Response:
    return _apply_security_headers(
        request,
        Response(
            "Autenticazione richiesta",
            status_code=401,
            headers={"WWW-Authenticate": f'Basic realm="{settings.board_auth_realm}"'},
        ),
    )


def _is_valid_basic_auth(request: Request) -> bool:
    if not settings.board_password:
        return False
    credentials = _parse_basic_auth(request.headers.get("authorization"))
    if not credentials:
        return False
    username, password = credentials
    username_ok = secrets.compare_digest(username, settings.board_username)
    password_ok = secrets.compare_digest(password, settings.board_password)
    return username_ok and password_ok


def create_dashboard_app() -> FastAPI:
    app = FastAPI(title="AI Board Dashboard", docs_url=None, redoc_url=None)
    allowed_origins = set(get_allowed_origins())
    request_log: dict[tuple[str, str], list[float]] = {}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Accept", "X-KAI-Request"],
    )

    @app.middleware("http")
    async def harden_public_responses(request: Request, call_next):
        board_auth_required = settings.board_auth_enabled or settings.app_env == "production"
        if board_auth_required and not _is_auth_exempt(request.url.path):
            user = get_user_from_session(request.cookies.get(SESSION_COOKIE_NAME))
            if user:
                request.state.board_user = user
            elif _is_valid_basic_auth(request):
                request.state.board_user = {
                    "id": None,
                    "email": settings.board_username,
                    "display_name": "Admin emergenza",
                    "role": "admin",
                    "is_env": True,
                }
            else:
                accept = request.headers.get("accept", "")
                if request.method == "GET" and "text/html" in accept:
                    return RedirectResponse(url=f"/login?next={request.url.path}", status_code=303)
                if settings.board_password:
                    return _auth_challenge(request)
                return _apply_security_headers(
                    request,
                    Response("Board auth non configurata: imposta BOARD_PASSWORD o crea un account.", status_code=503),
                )
            user = getattr(request.state, "board_user", None)
            if user and user.get("role") == "viewer" and request.method not in {"GET", "HEAD", "OPTIONS"} and request.url.path != "/logout":
                return _apply_security_headers(
                    request,
                    Response("Account in sola lettura.", status_code=403),
                )

        if request.url.path in PUBLIC_INTAKE_PATHS:
            origin = request.headers.get("origin")
            if origin and origin not in allowed_origins:
                return _apply_security_headers(
                    request,
                    JSONResponse({"detail": "Origin non consentita"}, status_code=403),
                )

            if request.method == "POST":
                if request.headers.get("x-kai-request") != "fetch":
                    return _apply_security_headers(
                        request,
                        JSONResponse({"detail": "Richiesta non valida"}, status_code=403),
                    )

                now = monotonic()
                window_seconds = 60
                max_requests = 10 if request.url.path.endswith("/kbot-chat") else 6
                key = (_client_ip(request), request.url.path)
                recent = [stamp for stamp in request_log.get(key, []) if now - stamp < window_seconds]
                remaining = max(max_requests - len(recent) - 1, 0)

                if len(recent) >= max_requests:
                    return _apply_security_headers(
                        request,
                        JSONResponse(
                            {"detail": "Troppe richieste. Riprova tra poco."},
                            status_code=429,
                            headers={
                                "Retry-After": str(window_seconds),
                                "X-RateLimit-Limit": str(max_requests),
                                "X-RateLimit-Remaining": "0",
                            },
                        ),
                    )

                recent.append(now)
                request_log[key] = recent

        response = await call_next(request)
        _apply_security_headers(request, response)
        if request.url.path in PUBLIC_INTAKE_PATHS and request.method == "POST":
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    app.include_router(home_router)
    app.include_router(auth.router)
    app.include_router(board_chat.router)
    app.include_router(pipeline.router)
    app.include_router(agents_router)
    app.include_router(approvals.router)
    app.include_router(logs.router)
    app.include_router(memory.router)
    app.include_router(lavori.router)
    app.include_router(workshop.router)
    app.include_router(inbox.router)
    app.include_router(admin.router)
    app.include_router(public_intake.router)

    @app.get("/healthz")
    async def healthz() -> JSONResponse:
        return JSONResponse({"ok": True, "service": "ai-board"})

    uploads_dir = Path(__file__).resolve().parents[2] / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

    if settings.telegram_mode == "webhook" and settings.telegram_webhook_url:
        from interfaces.telegram.bot import process_webhook_payload

        @app.post("/webhook")
        async def telegram_webhook(request: Request) -> JSONResponse:
            payload = await request.json()
            await process_webhook_payload(payload)
            return JSONResponse({"ok": True})

    return app
