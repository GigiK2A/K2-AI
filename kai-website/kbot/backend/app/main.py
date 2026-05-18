"""FastAPI entrypoint."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .api import (
    session, message, upload, report, checkout, generate_pdf, status, webhook,
    fetch_url, conversations, diagnostics,
)
from .lib.analytics import track_server
from .lib.limiter import limiter
from .lib.logger import configure_logging, init_sentry
from .settings import CORS_ORIGINS

log = logging.getLogger(__name__)

configure_logging()
_SENTRY_ON = init_sentry()

app = FastAPI(title="K2-AI K-BOT backend", version="2.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    """Last-resort exception handler: log + track to PostHog + return 500.

    HTTPException is handled by FastAPI's default machinery and never reaches
    here. Sentry (if enabled) auto-captures via its FastAPI integration.
    """
    log.exception("unhandled exception: %s %s", request.method, request.url.path)
    try:
        # distinct_id: prefer session header if any, else "anonymous".
        distinct = request.headers.get("x-kbot-session-id") or "anonymous"
        track_server(
            distinct_id=distinct,
            event="server_error",
            properties={
                "type": exc.__class__.__name__,
                "endpoint": request.url.path,
                "method": request.method,
                "msg": str(exc)[:500],
            },
        )
    except Exception:
        pass  # analytics must never mask the real error
    return JSONResponse(status_code=500, content={"detail": "internal server error"})


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "kbot", "sentry": _SENTRY_ON}


app.include_router(session.router, prefix="/api/kbot", tags=["session"])
app.include_router(message.router, prefix="/api/kbot", tags=["message"])
app.include_router(upload.router, prefix="/api/kbot", tags=["upload"])
app.include_router(report.router, prefix="/api/kbot", tags=["report"])
app.include_router(checkout.router, prefix="/api/kbot", tags=["checkout"])
app.include_router(generate_pdf.router, prefix="/api/kbot", tags=["pdf"])
app.include_router(status.router, prefix="/api/kbot", tags=["status"])
app.include_router(fetch_url.router, prefix="/api/kbot", tags=["fetch-url"])
app.include_router(conversations.router, prefix="/api/kbot", tags=["conversations"])
app.include_router(diagnostics.router, prefix="/api/kbot", tags=["diagnostics"])
app.include_router(webhook.router, prefix="/api", tags=["webhook"])
