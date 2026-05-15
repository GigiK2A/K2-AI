"""/analytics — render the most recent analytics snapshot.

Reads from Supabase `analytics_snapshots` (populated by the hourly
`posthog_sync` job). No live calls to PostHog from this route.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from loguru import logger

from core.config import supabase_configured
from interfaces.dashboard.routes import base_context, render

router = APIRouter()


def _load_latest_snapshot() -> dict[str, Any] | None:
    if not supabase_configured():
        return None
    try:
        from db.client import get_service_client

        client = get_service_client()
        resp = (
            client.table("analytics_snapshots")
            .select("*")
            .order("ts", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        return rows[0] if rows else None
    except Exception as exc:
        logger.warning(f"analytics: load snapshot failed — {exc}")
        return None


@router.get("/analytics")
def analytics(request: Request):
    snapshot = _load_latest_snapshot()
    profile_stats: dict[str, int] = {}
    kbot_funnel: dict[str, Any] = {}
    ts: str | None = None
    events_processed = 0

    if snapshot:
        ts = snapshot.get("ts")
        profile_stats = snapshot.get("profile_stats") or {}
        kbot_funnel = snapshot.get("kbot_funnel") or {}
        events_processed = int(snapshot.get("events_processed") or 0)

    # Sort profile rows by clicks desc, top 10.
    sorted_profiles = sorted(
        ((k, int(v)) for k, v in profile_stats.items()),
        key=lambda kv: kv[1],
        reverse=True,
    )[:10]
    max_clicks = max((v for _, v in sorted_profiles), default=0)

    context = base_context(request, "analytics", "Analytics", "Misurazione anonima — PostHog Cloud EU")
    context.update(
        {
            "snapshot_ts": ts,
            "events_processed": events_processed,
            "profile_rows": sorted_profiles,
            "max_clicks": max_clicks,
            "funnel_counts": (kbot_funnel.get("counts") or {}),
            "funnel_rates": (kbot_funnel.get("rates") or {}),
            "has_data": snapshot is not None,
        }
    )
    return render(request, "analytics.html", context)
