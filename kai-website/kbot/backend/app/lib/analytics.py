"""Server-side analytics helper for the K-BOT FastAPI backend.

PostHog Cloud EU, anonymous mode. The `distinct_id` we send is the K-BOT
session UUID — never a user_id, never an email, never an IP. This keeps the
data flowing through the same identity space as the browser-side events
without identifying any real person.

Calls are best-effort: any failure (missing key, network blip, SDK import
error) is silently swallowed so analytics CAN NEVER break a chat turn or a
PDF generation.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

try:  # SDK is optional at runtime — keeps the test environment lean.
    from posthog import Posthog  # type: ignore
except Exception:  # pragma: no cover — defensive
    Posthog = None  # type: ignore

log = logging.getLogger(__name__)

_client: Optional["Posthog"] = None
_init_attempted = False


def _get_client() -> Optional["Posthog"]:
    global _client, _init_attempted
    if _client is not None:
        return _client
    if _init_attempted:
        return None
    _init_attempted = True

    key = (os.getenv("POSTHOG_API_KEY") or "").strip()
    if not key or Posthog is None:
        return None
    host = (os.getenv("POSTHOG_HOST") or "https://eu.i.posthog.com").strip()
    try:
        _client = Posthog(
            project_api_key=key,
            host=host,
            disable_geoip=False,
        )
    except Exception as exc:  # pragma: no cover — defensive
        log.warning("PostHog client init failed: %s", exc)
        _client = None
    return _client


def track_server(
    distinct_id: str,
    event: str,
    properties: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire-and-forget server-side event. Never raises."""
    client = _get_client()
    if not client or not distinct_id:
        return
    try:
        client.capture(
            distinct_id=str(distinct_id),
            event=event,
            properties=properties or {},
        )
    except Exception:
        # never let analytics break the request
        pass
