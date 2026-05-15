"""Centralized logging configuration for ai-board.

- In production (``LOG_FORMAT=json``) emits one JSON object per line on stderr.
- Locally (default) keeps loguru's pretty colored format.
- Wires Sentry only when ``SENTRY_DSN`` is set (no-op otherwise).

Existing callers continue to use ``from loguru import logger`` — this module
just changes the sink and adds structured serialization.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import timezone
from typing import Any

from loguru import logger


def _json_sink(message: Any) -> None:
    """Serialize a loguru Message as a single JSON line on stderr."""
    record = message.record
    payload = {
        "ts": record["time"].astimezone(timezone.utc).isoformat(),
        "level": record["level"].name.lower(),
        "logger": record["name"],
        "msg": record["message"],
    }
    # Merge structured extras the caller passed via logger.bind(...) or extra=.
    extras = record.get("extra") or {}
    for k, v in extras.items():
        try:
            json.dumps(v)
            payload[k] = v
        except (TypeError, ValueError):
            payload[k] = repr(v)
    if record["exception"] is not None:
        exc = record["exception"]
        payload["error"] = exc.type.__name__ if exc.type else "Exception"
        payload["error_msg"] = str(exc.value) if exc.value else ""
    sys.stderr.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stderr.flush()


def configure_logging(level: str | None = None) -> None:
    """Idempotently configure loguru. Call once at app startup."""
    level_name = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    fmt = os.getenv("LOG_FORMAT", "pretty").lower()

    logger.remove()
    if fmt == "json":
        logger.add(_json_sink, level=level_name, enqueue=False)
    else:
        logger.add(sys.stderr, level=level_name)


def init_sentry() -> bool:
    """Wire Sentry SDK when SENTRY_DSN is present. Returns True if active."""
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    try:
        import sentry_sdk
    except ImportError:
        logger.warning(
            "SENTRY_DSN set but sentry-sdk not installed — pip install sentry-sdk"
        )
        return False
    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("APP_ENV", "production"),
        release=os.getenv("APP_RELEASE", "ai-board@local"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        send_default_pii=False,
    )
    return True
