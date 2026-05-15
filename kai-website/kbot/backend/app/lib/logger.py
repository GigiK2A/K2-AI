"""Structured-logging bootstrap for the K-BOT FastAPI backend.

Call ``configure_logging()`` once at app startup. After that, every module that
does ``import logging; log = logging.getLogger(__name__)`` will emit JSON lines
on stderr in production, or human-readable lines locally.

Also wires Sentry if ``SENTRY_DSN`` is set. No-op otherwise.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any


class _JsonFormatter(logging.Formatter):
    """Render LogRecord as a single JSON line.

    Standard fields: ``ts``, ``level``, ``logger``, ``msg``.
    Anything passed via ``extra={...}`` is merged at the top level.
    Exceptions are serialized as ``error`` (type) + ``error_msg``.
    """

    _RESERVED = {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "asctime", "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Merge any extra=... fields the caller passed.
        for key, value in record.__dict__.items():
            if key in self._RESERVED or key.startswith("_"):
                continue
            try:
                json.dumps(value)  # only include JSON-serializable extras
                payload[key] = value
            except (TypeError, ValueError):
                payload[key] = repr(value)
        if record.exc_info:
            exc_type = record.exc_info[0]
            exc_val = record.exc_info[1]
            payload["error"] = exc_type.__name__ if exc_type else "Exception"
            payload["error_msg"] = str(exc_val) if exc_val else ""
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    """Configure root logger. Idempotent (safe to call repeatedly)."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    fmt = os.getenv("LOG_FORMAT", "json").lower()

    root = logging.getLogger()
    # Remove existing handlers so reloads don't double-print.
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stderr)
    if fmt == "json":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet down noisy libs.
    for noisy in ("httpx", "urllib3", "supabase", "stripe"):
        logging.getLogger(noisy).setLevel(max(level, logging.WARNING))


def init_sentry() -> bool:
    """Initialize Sentry SDK if SENTRY_DSN is set. Returns True if active."""
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        logging.getLogger(__name__).warning(
            "SENTRY_DSN set but sentry-sdk not installed — install with `pip install 'sentry-sdk[fastapi]'`"
        )
        return False
    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("APP_ENV", "production"),
        release=os.getenv("APP_RELEASE", "kbot@local"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        send_default_pii=False,
        integrations=[FastApiIntegration(), StarletteIntegration()],
    )
    return True
