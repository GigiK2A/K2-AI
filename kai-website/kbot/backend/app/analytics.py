from __future__ import annotations

import asyncio
from typing import Any

from app.supabase_client import _get_client


async def _insert_event(event_type: str, payload: dict, clerk_user_id: str | None, session_id: str | None) -> None:
    try:
        client = _get_client()
        client.table("analytics_events").insert({
            "event_type": event_type,
            "clerk_user_id": clerk_user_id,
            "session_id": session_id,
            "payload": payload,
        }).execute()
    except Exception:
        pass


def track_event(
    event_type: str,
    payload: dict[str, Any] | None = None,
    clerk_user_id: str | None = None,
    session_id: str | None = None,
) -> None:
    """Fire-and-forget: non blocca mai la risposta HTTP."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_insert_event(event_type, payload or {}, clerk_user_id, session_id))
        else:
            loop.run_until_complete(_insert_event(event_type, payload or {}, clerk_user_id, session_id))
    except Exception:
        pass
