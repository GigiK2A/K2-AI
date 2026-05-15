"""Read-only PostHog ingestion for ai-board analytics.

Talks to the PostHog Cloud EU query API (HogQL) using a Personal API key.
No mutation, no writes back to PostHog. The scheduler job
(`agents/scheduler_tasks/posthog_sync.py`) snapshots the rolled-up output
into Supabase so the /analytics dashboard can render fast.

Settings (core/config.py):
- posthog_personal_api_key — Personal API key with project read access
- posthog_project_id       — numeric project id
- posthog_host             — defaults to https://eu.i.posthog.com
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

import httpx
from loguru import logger

from core.config import settings


# ───────────────────────── PostHog HTTP ──────────────────────────


def _api_base() -> str | None:
    host = getattr(settings, "posthog_host", "https://eu.i.posthog.com") or ""
    project_id = getattr(settings, "posthog_project_id", None)
    if not host or not project_id:
        return None
    return f"{host.rstrip('/')}/api/projects/{project_id}"


def _auth_headers() -> dict[str, str] | None:
    key = (getattr(settings, "posthog_personal_api_key", None) or "").strip()
    if not key:
        return None
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def fetch_recent_events(since_hours: int = 24, limit: int = 1000) -> list[dict[str, Any]]:
    """Return the most recent events from PostHog. Empty list when not configured."""
    base = _api_base()
    headers = _auth_headers()
    if not base or not headers:
        logger.info("PostHog ingest: skipping — config missing")
        return []

    # HogQL — bounded by `since_hours` and `limit`. We pull a small set of
    # fields only (event name, props, timestamp, distinct_id) to keep the
    # response small. Properties is returned as a JSON object.
    query = {
        "query": {
            "kind": "HogQLQuery",
            "query": (
                "SELECT event, properties, timestamp, distinct_id "
                "FROM events "
                f"WHERE timestamp > now() - INTERVAL {int(since_hours)} HOUR "
                "ORDER BY timestamp DESC "
                f"LIMIT {int(limit)}"
            ),
        }
    }

    url = f"{base}/query/"
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=query)
            resp.raise_for_status()
            payload = resp.json()
    except Exception as exc:
        logger.warning(f"PostHog ingest: query failed — {exc}")
        return []

    results = payload.get("results") or []
    # PostHog HogQL returns rows as arrays in column order.
    columns = ["event", "properties", "timestamp", "distinct_id"]
    rows: list[dict[str, Any]] = []
    for row in results:
        if isinstance(row, list) and len(row) >= 4:
            rows.append(dict(zip(columns, row)))
        elif isinstance(row, dict):
            rows.append(row)
    return rows


# ───────────────────────── Aggregations ──────────────────────────


def _props(ev: dict[str, Any]) -> dict[str, Any]:
    p = ev.get("properties")
    if isinstance(p, dict):
        return p
    return {}


def compute_profile_stats(events: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Count `profile_click` events per `profile_id` (P01, P02, ...)."""
    counter: Counter[str] = Counter()
    for ev in events:
        if ev.get("event") != "profile_click":
            continue
        pid = _props(ev).get("profile_id")
        if isinstance(pid, str) and pid:
            counter[pid] += 1
    return dict(counter)


def compute_kbot_funnel(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Compute K-BOT funnel counts and conversion rates.

    Funnel: kbot_open → kbot_message_sent → kbot_report_requested → report_generated.
    Each step counts UNIQUE distinct_ids that fired the event in the window.
    """
    by_event: dict[str, set[str]] = {
        "kbot_open": set(),
        "kbot_message_sent": set(),
        "kbot_report_requested": set(),
        "report_generated": set(),
    }
    for ev in events:
        name = ev.get("event")
        did = ev.get("distinct_id")
        if name in by_event and isinstance(did, str) and did:
            by_event[name].add(did)

    opens = len(by_event["kbot_open"])
    msgs = len(by_event["kbot_message_sent"])
    reqs = len(by_event["kbot_report_requested"])
    gens = len(by_event["report_generated"])

    def _ratio(num: int, den: int) -> float:
        return round(num / den, 4) if den else 0.0

    return {
        "counts": {
            "kbot_open": opens,
            "kbot_message_sent": msgs,
            "kbot_report_requested": reqs,
            "report_generated": gens,
        },
        "rates": {
            "open_to_message": _ratio(msgs, opens),
            "message_to_request": _ratio(reqs, msgs),
            "request_to_report": _ratio(gens, reqs),
            "overall": _ratio(gens, opens),
        },
    }
