"""Dashboard aggregate endpoint.

Returns the at-a-glance snapshot the frontend needs on the home view:
pipeline health, task urgency, pending approvals, MTD revenue, next meeting,
and a small set of high-signal alerts.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from app.db.client import get_supabase
from app.deps import require_auth

router = APIRouter(prefix="/api/overview", tags=["overview"], dependencies=[Depends(require_auth)])

ACTIVE_STATUSES = ("nuovo", "contatto", "proposta")
STALE_DAYS = 14


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _start_of_today_utc() -> datetime:
    n = _now()
    return n.replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_month_utc() -> datetime:
    n = _now()
    return n.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


@router.get("/")
def overview() -> Dict[str, Any]:
    sb = get_supabase()
    now = _now()
    today = _start_of_today_utc()
    week_end = today + timedelta(days=7)
    month_start = _start_of_month_utc()
    stale_cutoff = now - timedelta(days=STALE_DAYS)

    # ── Leads ────────────────────────────────────────────────────────────────
    leads_res = sb.table("board_leads").select(
        "id, title, status, value_eur, updated_at"
    ).execute()
    leads = leads_res.data or []

    by_status: Dict[str, int] = {}
    active_count = 0
    stale_count = 0
    active_leads: List[Dict[str, Any]] = []
    for ld in leads:
        st = ld.get("status") or ""
        by_status[st] = by_status.get(st, 0) + 1
        if st in ACTIVE_STATUSES:
            active_count += 1
            active_leads.append(ld)
            updated = ld.get("updated_at")
            if updated:
                try:
                    upd = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                    if upd < stale_cutoff:
                        stale_count += 1
                except (ValueError, AttributeError):
                    pass

    def _value(row: Dict[str, Any]) -> float:
        v = row.get("value_eur")
        try:
            return float(v) if v is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    high_value = sorted(active_leads, key=_value, reverse=True)[:5]

    # ── Tasks ────────────────────────────────────────────────────────────────
    tasks_res = sb.table("board_tasks").select(
        "id, title, due_at, status"
    ).in_("status", ["todo", "doing"]).execute()
    tasks = tasks_res.data or []

    overdue = 0
    today_count = 0
    this_week = 0
    for t in tasks:
        due = t.get("due_at")
        if not due:
            continue
        try:
            d = datetime.fromisoformat(due.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        if d < now:
            overdue += 1
        elif d < today + timedelta(days=1):
            today_count += 1
        if today <= d < week_end:
            this_week += 1

    # ── Approvals pending ────────────────────────────────────────────────────
    appr_res = (
        sb.table("board_approvals").select("id", count="exact").eq("status", "pending").execute()
    )
    approvals_pending = appr_res.count or 0

    # ── Revenue MTD ──────────────────────────────────────────────────────────
    rev_res = (
        sb.table("board_revenue_events")
        .select("amount_cents, status, occurred_at")
        .eq("status", "succeeded")
        .gte("occurred_at", month_start.isoformat())
        .execute()
    )
    revenue_mtd_cents = sum(int(r.get("amount_cents") or 0) for r in (rev_res.data or []))

    # ── Next meeting ─────────────────────────────────────────────────────────
    next_mtg_res = (
        sb.table("board_meetings")
        .select("*")
        .gte("starts_at", now.isoformat())
        .order("starts_at", desc=False)
        .limit(1)
        .execute()
    )
    next_meeting = (next_mtg_res.data or [None])[0]

    # ── Alerts (cheap, derived) ──────────────────────────────────────────────
    alerts: List[Dict[str, Any]] = []
    if overdue:
        alerts.append({
            "kind": "overdue_tasks",
            "title": f"{overdue} task in ritardo",
            "severity": "high",
        })
    if stale_count:
        alerts.append({
            "kind": "stale_leads",
            "title": f"{stale_count} lead fermi da oltre {STALE_DAYS} giorni",
            "severity": "medium",
        })
    if approvals_pending:
        alerts.append({
            "kind": "pending_approvals",
            "title": f"{approvals_pending} draft in attesa di approvazione",
            "severity": "medium",
        })

    return {
        "generated_at": now.isoformat(),
        "leads": {
            "active": active_count,
            "by_status": by_status,
            "stale_count": stale_count,
            "high_value": high_value,
        },
        "tasks": {
            "overdue": overdue,
            "today": today_count,
            "this_week": this_week,
        },
        "approvals_pending": approvals_pending,
        "revenue_mtd_cents": revenue_mtd_cents,
        "next_meeting": next_meeting,
        "alerts": alerts,
    }
