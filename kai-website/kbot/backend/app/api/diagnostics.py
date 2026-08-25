"""GET /api/kbot/diagnostics — health check for the extraction stack.

Pings the four hard runtime dependencies (Supabase, Anthropic, pdfplumber,
Playwright) and reports versions of the core Python packages. Used by
uptime probes and by us when "PDFs aren't extracting" suddenly happens.

Rate-limited (10/min) to discourage automated scraping. Bearer auth via
INTERNAL_API_KEY is ALWAYS required: senza la variabile configurata l'endpoint
risponde 503 invece di aprirsi (fail-closed). Il liveness pubblico è /health.

Never leaks secrets: we report presence/absence of env vars, not values.
"""
from __future__ import annotations

import logging
import os
import platform
import secrets
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict

import anthropic as _anthropic
from fastapi import APIRouter, Header, HTTPException, Request

from ..lib.limiter import limiter
from ..settings import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, INTERNAL_API_KEY

router = APIRouter()
log = logging.getLogger(__name__)


def _check_supabase() -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        from ..lib.supabase_admin import get_admin_client

        client = get_admin_client()
        client.table("kbot_sessions").select("id").limit(1).execute()
        return {"status": "ok", "latency_ms": int((time.perf_counter() - t0) * 1000)}
    except Exception as exc:
        return {"status": "error", "error": exc.__class__.__name__, "msg": str(exc)[:200]}


def _check_anthropic() -> Dict[str, Any]:
    if not ANTHROPIC_API_KEY:
        return {"status": "error", "error": "MissingApiKey"}
    t0 = time.perf_counter()
    try:
        client = _anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
            timeout=10.0,
        )
        return {
            "status": "ok",
            "model": ANTHROPIC_MODEL,
            "latency_ms": int((time.perf_counter() - t0) * 1000),
        }
    except Exception as exc:
        return {"status": "error", "error": exc.__class__.__name__, "msg": str(exc)[:200]}


def _check_pdfplumber() -> Dict[str, Any]:
    try:
        import pdfplumber  # noqa: F401

        return {"status": "ok", "version": getattr(pdfplumber, "__version__", "unknown")}
    except Exception as exc:
        return {"status": "error", "error": exc.__class__.__name__, "msg": str(exc)[:200]}


def _check_reportlab() -> Dict[str, Any]:
    try:
        import reportlab  # noqa: F401

        return {"status": "ok", "version": getattr(reportlab, "Version", "unknown")}
    except ImportError:
        return {"status": "missing"}
    except Exception as exc:
        return {"status": "error", "error": exc.__class__.__name__, "msg": str(exc)[:200]}


def _pkg_version(name: str) -> str:
    try:
        from importlib.metadata import version

        return version(name)
    except Exception:
        return "unknown"


def _aggregate_status(checks: Dict[str, Dict[str, Any]]) -> str:
    statuses = [v.get("status") for v in checks.values()]
    if all(s == "ok" for s in statuses):
        return "ok"
    # supabase or anthropic broken = error; only reportlab/pdfplumber = degraded
    critical = {"supabase", "anthropic"}
    if any(checks.get(k, {}).get("status") == "error" for k in critical):
        return "error"
    return "degraded"


@router.get("/diagnostics")
@limiter.limit("10/minute")
def diagnostics(
    request: Request,
    authorization: str | None = Header(default=None),
):
    # Bearer auth SEMPRE richiesta. Prima era condizionata a `if INTERNAL_API_KEY:`,
    # cioè un deploy che dimentica la variabile pubblicava l'endpoint: la presenza di
    # un segreto non può decidere SE autenticare. Senza chiave configurata l'endpoint
    # non si serve affatto (503) — fail-closed. Il liveness pubblico è /health.
    if not INTERNAL_API_KEY:
        raise HTTPException(status_code=503, detail="diagnostics non configurato")
    if not secrets.compare_digest(authorization or "", f"Bearer {INTERNAL_API_KEY}"):
        raise HTTPException(status_code=401, detail="unauthorized")

    checks = {
        "supabase": _check_supabase(),
        "anthropic": _check_anthropic(),
        "pdfplumber": _check_pdfplumber(),
        "reportlab": _check_reportlab(),
    }

    packages = {
        name: _pkg_version(name)
        for name in ("anthropic", "supabase", "pdfplumber", "fastapi", "sentry-sdk", "posthog")
    }

    env_present = {
        "SENTRY_DSN": bool(os.getenv("SENTRY_DSN")),
        "POSTHOG_API_KEY": bool(os.getenv("POSTHOG_API_KEY")),
        "INTERNAL_API_KEY": bool(INTERNAL_API_KEY),
        "ANTHROPIC_API_KEY": bool(ANTHROPIC_API_KEY),
    }

    return {
        "status": _aggregate_status(checks),
        "checks": checks,
        "packages": packages,
        "env": env_present,
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "ts": datetime.now(timezone.utc).isoformat(),
    }
