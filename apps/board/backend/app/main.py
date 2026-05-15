"""K2-Board backend — FastAPI entrypoint."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.auth import router as auth_router
from app.api import (
    approvals as approvals_api,
    contacts as contacts_api,
    leads as leads_api,
    meetings as meetings_api,
    memos as memos_api,
    overview as overview_api,
    revenue as revenue_api,
    tasks as tasks_api,
    webhooks as webhooks_api,
)
from app.lib.logger import configure_logging, get_logger
from app.settings import get_settings


def _maybe_init_sentry(dsn: str, environment: str) -> None:
    if not dsn:
        return
    try:
        import sentry_sdk  # type: ignore

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
    except Exception:  # pragma: no cover — never fail boot because of telemetry
        logging.getLogger(__name__).exception("sentry init failed")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(log_format=settings.log_format, level=settings.log_level)
    _maybe_init_sentry(settings.sentry_dsn, settings.environment)

    log = get_logger(__name__)
    log.info(
        "k2board.boot",
        extra={
            "version": __version__,
            "environment": settings.environment,
            "cors_origins": settings.cors_origins_list,
        },
    )

    app = FastAPI(
        title="K2-Board API",
        version=__version__,
        docs_url="/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(auth_router)
    app.include_router(contacts_api.router)
    app.include_router(leads_api.router)
    app.include_router(tasks_api.router)
    app.include_router(approvals_api.router)
    app.include_router(memos_api.router)
    app.include_router(meetings_api.router)
    app.include_router(revenue_api.router)
    app.include_router(overview_api.router)
    # Public — no auth (third-party signed callbacks).
    app.include_router(webhooks_api.router)

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    @app.get("/", tags=["meta"])
    def root() -> dict:
        return {"name": "k2-board-backend", "version": __version__, "docs": "/docs"}

    return app


app = create_app()
