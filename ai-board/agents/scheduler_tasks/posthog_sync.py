"""Hourly job that snapshots PostHog rollups into Supabase.

The aim is to keep the analytics dashboard fast and decoupled from PostHog
API availability. Every hour we:
  1. Pull the last 24h of events via PostHog HogQL.
  2. Roll them up into profile click counts + K-BOT funnel counts.
  3. Persist a row to `analytics_snapshots`.

If anything fails (no config, network error, Supabase missing) the job logs
a warning and returns False — it never raises into the scheduler.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from loguru import logger

from core.config import settings, supabase_configured
from services.posthog_ingest import (
    compute_kbot_funnel,
    compute_profile_stats,
    fetch_recent_events,
)


async def job_posthog_sync() -> bool:
    """Snapshot PostHog rollups into Supabase. Returns True on success."""
    if not getattr(settings, "posthog_personal_api_key", None):
        logger.debug("posthog_sync: skipping — POSTHOG_PERSONAL_API_KEY not set")
        return False
    if not supabase_configured():
        logger.warning("posthog_sync: skipping — Supabase not configured")
        return False

    try:
        events = fetch_recent_events(since_hours=24, limit=5000)
    except Exception as exc:
        logger.warning(f"posthog_sync: fetch failed — {exc}")
        return False

    profile_stats = compute_profile_stats(events)
    kbot_funnel = compute_kbot_funnel(events)

    snapshot: dict[str, Any] = {
        "ts": datetime.now(UTC).isoformat(),
        "profile_stats": profile_stats,
        "kbot_funnel": kbot_funnel,
        "events_processed": len(events),
    }

    try:
        from db.client import get_service_client

        client = get_service_client()
        client.table("analytics_snapshots").insert(snapshot).execute()
    except Exception as exc:
        logger.warning(f"posthog_sync: insert failed — {exc}")
        return False

    logger.info(
        "posthog_sync: snapshot stored (events={}, profiles={}, opens={})".format(
            len(events),
            len(profile_stats),
            kbot_funnel.get("counts", {}).get("kbot_open", 0),
        )
    )
    return True
