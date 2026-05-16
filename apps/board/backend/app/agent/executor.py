"""Tool dispatch for Giuseppina.

Read-only tools query Supabase directly. `propose_*` tools insert a
pending row into `board_approvals` (no other side-effects). `add_memo`
is the only allowed direct write outside approvals.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx

log = logging.getLogger(__name__)

MAX_FETCH_BYTES = 50_000


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _period_start(period: str) -> datetime:
    now = _now()
    if period == "ytd":
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    if period == "last_30d":
        return now - timedelta(days=30)
    # default mtd
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


async def execute_tool(name: str, args: Dict[str, Any], sb) -> Dict[str, Any]:
    """Dispatch a tool call. Returns a JSON-serializable result dict.

    `sb` is a Supabase service-role client.
    """
    try:
        if name == "list_leads":
            return _list_leads(sb, args)
        if name == "get_lead":
            return _get_lead(sb, args)
        if name == "search_contacts":
            return _search_contacts(sb, args)
        if name == "list_tasks":
            return _list_tasks(sb, args)
        if name == "list_pending_approvals":
            return _list_pending_approvals(sb)
        if name == "search_memos":
            return _search_memos(sb, args)
        if name == "get_revenue_summary":
            return _get_revenue_summary(sb, args)
        if name == "list_meetings":
            return _list_meetings(sb, args)
        if name == "fetch_url":
            return await _fetch_url(args)
        if name == "overview_snapshot":
            return _overview_snapshot(sb)

        # ── Propose-* tools — all funnel into board_approvals ───────────────
        if name == "propose_new_lead":
            return _propose_new_lead(sb, args)
        if name == "propose_lead_update":
            return _propose_lead_update(sb, args)
        if name == "propose_email_draft":
            return _propose_email_draft(sb, args)
        if name == "propose_proposta_commerciale":
            return _propose_proposta(sb, args)
        if name == "propose_task":
            return _propose_task(sb, args)

        if name == "add_memo":
            return _add_memo(sb, args)

        return {"error": f"unknown tool: {name}"}
    except Exception as exc:  # noqa: BLE001 — surface error back to model
        log.exception("agent.tool_error", extra={"tool": name})
        return {"error": str(exc)}


# ── Read-only impls ──────────────────────────────────────────────────────────

def _list_leads(sb, args: Dict[str, Any]) -> Dict[str, Any]:
    q = sb.table("board_leads").select(
        "id, title, status, value_eur, probability, source, next_action_at, updated_at, contact_id"
    )
    if args.get("status"):
        q = q.eq("status", args["status"])
    limit = int(args.get("limit") or 20)
    res = q.order("updated_at", desc=True).limit(limit).execute()
    return {"count": len(res.data or []), "leads": res.data or []}


def _get_lead(sb, args: Dict[str, Any]) -> Dict[str, Any]:
    lead = sb.table("board_leads").select("*").eq("id", args["id"]).limit(1).execute()
    rows = lead.data or []
    if not rows:
        return {"error": "lead non trovato"}
    lead_row = rows[0]
    contact = None
    if lead_row.get("contact_id"):
        cres = (
            sb.table("board_contacts")
            .select("*")
            .eq("id", lead_row["contact_id"])
            .limit(1)
            .execute()
        )
        if cres.data:
            contact = cres.data[0]
    return {"lead": lead_row, "contact": contact}


def _search_contacts(sb, args: Dict[str, Any]) -> Dict[str, Any]:
    query = (args.get("query") or "").strip()
    if not query:
        return {"contacts": []}
    like = f"%{query}%"
    # Supabase .or_ with ilike on multiple columns
    res = (
        sb.table("board_contacts")
        .select("id, company, person_name, email, phone, tags")
        .or_(f"company.ilike.{like},person_name.ilike.{like},email.ilike.{like}")
        .limit(20)
        .execute()
    )
    return {"count": len(res.data or []), "contacts": res.data or []}


def _list_tasks(sb, args: Dict[str, Any]) -> Dict[str, Any]:
    q = sb.table("board_tasks").select("id, title, status, priority, due_at, lead_id, notes")
    if args.get("status"):
        q = q.eq("status", args["status"])
    if args.get("due_within_days") is not None:
        until = _now() + timedelta(days=int(args["due_within_days"]))
        q = q.lte("due_at", until.isoformat()).not_.is_("due_at", "null")
    res = q.order("due_at", desc=False).limit(50).execute()
    return {"count": len(res.data or []), "tasks": res.data or []}


def _list_pending_approvals(sb) -> Dict[str, Any]:
    res = (
        sb.table("board_approvals")
        .select("id, kind, title, rationale, lead_id, contact_id, created_at")
        .eq("status", "pending")
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return {"count": len(res.data or []), "approvals": res.data or []}


def _search_memos(sb, args: Dict[str, Any]) -> Dict[str, Any]:
    query = (args.get("query") or "").strip()
    like = f"%{query}%"
    res = (
        sb.table("board_memos")
        .select("id, subject, body, tags, contact_id, lead_id, created_at")
        .or_(f"subject.ilike.{like},body.ilike.{like}")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    return {"count": len(res.data or []), "memos": res.data or []}


def _get_revenue_summary(sb, args: Dict[str, Any]) -> Dict[str, Any]:
    period = args.get("period", "mtd")
    start = _period_start(period)
    res = (
        sb.table("board_revenue_events")
        .select("amount_cents, status, occurred_at, kind")
        .gte("occurred_at", start.isoformat())
        .execute()
    )
    rows = res.data or []
    succeeded_cents = sum(int(r.get("amount_cents") or 0) for r in rows if r.get("status") == "succeeded")
    return {
        "period": period,
        "from": start.isoformat(),
        "to": _now().isoformat(),
        "succeeded_cents": succeeded_cents,
        "succeeded_eur": round(succeeded_cents / 100, 2),
        "event_count": len(rows),
    }


def _list_meetings(sb, args: Dict[str, Any]) -> Dict[str, Any]:
    from_date = args.get("from_date")
    to_date = args.get("to_date")
    start = (
        datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc)
        if from_date
        else _now()
    )
    end = (
        datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc)
        if to_date
        else start + timedelta(days=30)
    )
    res = (
        sb.table("board_meetings")
        .select("id, title, starts_at, ends_at, notes, lead_id, contact_id")
        .gte("starts_at", start.isoformat())
        .lte("starts_at", end.isoformat())
        .order("starts_at", desc=False)
        .limit(50)
        .execute()
    )
    return {"count": len(res.data or []), "meetings": res.data or []}


async def _fetch_url(args: Dict[str, Any]) -> Dict[str, Any]:
    url = args.get("url") or ""
    if not url.startswith(("http://", "https://")):
        return {"error": "url must start with http:// or https://"}
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "K2-Board/Giuseppina"})
        text = resp.text[:MAX_FETCH_BYTES]
        return {
            "url": str(resp.url),
            "status": resp.status_code,
            "content_type": resp.headers.get("content-type", ""),
            "text": text,
            "truncated": len(resp.text) > MAX_FETCH_BYTES,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"fetch failed: {exc}"}


def _overview_snapshot(sb) -> Dict[str, Any]:
    # Mirror /api/overview/ logic — keep it lean here to avoid coupling.
    now = _now()
    leads = sb.table("board_leads").select("id, status, value_eur, updated_at").execute().data or []
    by_status: Dict[str, int] = {}
    for ld in leads:
        st = ld.get("status") or ""
        by_status[st] = by_status.get(st, 0) + 1
    tasks_open = (
        sb.table("board_tasks")
        .select("id, due_at, status")
        .in_("status", ["todo", "doing"])
        .execute()
        .data
        or []
    )
    overdue = 0
    for t in tasks_open:
        due = t.get("due_at")
        if not due:
            continue
        try:
            d = datetime.fromisoformat(due.replace("Z", "+00:00"))
            if d < now:
                overdue += 1
        except (ValueError, AttributeError):
            pass
    pending = (
        sb.table("board_approvals")
        .select("id", count="exact")
        .eq("status", "pending")
        .execute()
        .count
        or 0
    )
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    rev_rows = (
        sb.table("board_revenue_events")
        .select("amount_cents, status, occurred_at")
        .eq("status", "succeeded")
        .gte("occurred_at", month_start.isoformat())
        .execute()
        .data
        or []
    )
    revenue_mtd_cents = sum(int(r.get("amount_cents") or 0) for r in rev_rows)
    return {
        "generated_at": now.isoformat(),
        "leads_total": len(leads),
        "leads_by_status": by_status,
        "tasks_open": len(tasks_open),
        "tasks_overdue": overdue,
        "approvals_pending": pending,
        "revenue_mtd_cents": revenue_mtd_cents,
    }


# ── Propose-* impls — all create a pending approval row ──────────────────────

def _insert_approval(sb, *, kind: str, title: str, body: str, rationale: Optional[str],
                     lead_id: Optional[str] = None, contact_id: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "kind": kind,
        "title": title,
        "body": body,
        "rationale": rationale,
        "status": "pending",
    }
    if lead_id:
        payload["lead_id"] = lead_id
    if contact_id:
        payload["contact_id"] = contact_id
    res = sb.table("board_approvals").insert(payload).execute()
    row = (res.data or [{}])[0]
    return {"approval_id": row.get("id"), "status": "pending_approval", "kind": kind}


def _propose_new_lead(sb, args: Dict[str, Any]) -> Dict[str, Any]:
    body_parts = [
        "PROPOSTA AGENTE — Nuovo lead",
        f"Titolo: {args['title']}",
        f"Source: {args['source']}",
    ]
    if args.get("contact_company"):
        body_parts.append(f"Azienda: {args['contact_company']}")
    if args.get("value_eur") is not None:
        body_parts.append(f"Valore stimato: € {args['value_eur']}")
    body_parts.append(f"\nRationale:\n{args['rationale']}")
    body_parts.append("\n[meta] tool=propose_new_lead")
    body_parts.append(f"[meta] payload={json.dumps(args, ensure_ascii=False)}")
    return _insert_approval(
        sb,
        kind="altro",
        title=f"Nuovo lead proposto: {args['title']}",
        body="\n".join(body_parts),
        rationale=args.get("rationale"),
    )


def _propose_lead_update(sb, args: Dict[str, Any]) -> Dict[str, Any]:
    body = (
        "PROPOSTA AGENTE — Modifica lead\n"
        f"Lead ID: {args['lead_id']}\n"
        f"Campi:\n{json.dumps(args['fields_json'], ensure_ascii=False, indent=2)}\n\n"
        f"Rationale:\n{args['rationale']}\n\n"
        f"[meta] tool=propose_lead_update\n"
        f"[meta] payload={json.dumps(args, ensure_ascii=False)}"
    )
    return _insert_approval(
        sb,
        kind="altro",
        title=f"Modifica lead {args['lead_id'][:8]}",
        body=body,
        rationale=args.get("rationale"),
        lead_id=args["lead_id"],
    )


def _propose_email_draft(sb, args: Dict[str, Any]) -> Dict[str, Any]:
    body = (
        f"PROPOSTA AGENTE — Draft email\n"
        f"To contact: {args['to_contact_id']}\n"
        f"Subject: {args['subject']}\n\n"
        f"---\n{args['body_markdown']}\n---\n\n"
        f"Rationale:\n{args['rationale']}\n\n"
        f"[meta] tool=propose_email_draft"
    )
    return _insert_approval(
        sb,
        kind="email",
        title=args["subject"],
        body=body,
        rationale=args.get("rationale"),
        contact_id=args["to_contact_id"],
    )


def _propose_proposta(sb, args: Dict[str, Any]) -> Dict[str, Any]:
    body = (
        f"PROPOSTA AGENTE — Proposta commerciale\n"
        f"Lead ID: {args['lead_id']}\n\n"
        f"---\n{args['body_markdown']}\n---\n\n"
        f"Rationale:\n{args['rationale']}\n\n"
        f"[meta] tool=propose_proposta_commerciale"
    )
    return _insert_approval(
        sb,
        kind="proposta",
        title=f"Proposta per lead {args['lead_id'][:8]}",
        body=body,
        rationale=args.get("rationale"),
        lead_id=args["lead_id"],
    )


def _propose_task(sb, args: Dict[str, Any]) -> Dict[str, Any]:
    body_parts = [
        "PROPOSTA AGENTE — Nuovo task",
        f"Titolo: {args['title']}",
        f"Priority: {args['priority']}",
    ]
    if args.get("due_at"):
        body_parts.append(f"Scadenza: {args['due_at']}")
    if args.get("lead_id"):
        body_parts.append(f"Lead collegato: {args['lead_id']}")
    body_parts.append(f"\nRationale:\n{args['rationale']}")
    body_parts.append(f"\n[meta] tool=propose_task")
    body_parts.append(f"[meta] payload={json.dumps(args, ensure_ascii=False)}")
    return _insert_approval(
        sb,
        kind="altro",
        title=f"Task: {args['title']}",
        body="\n".join(body_parts),
        rationale=args.get("rationale"),
        lead_id=args.get("lead_id"),
    )


def _add_memo(sb, args: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "subject": args["subject"],
        "body": args["body"],
        "tags": args.get("tags") or [],
    }
    if args.get("contact_id"):
        payload["contact_id"] = args["contact_id"]
    if args.get("lead_id"):
        payload["lead_id"] = args["lead_id"]
    res = sb.table("board_memos").insert(payload).execute()
    row = (res.data or [{}])[0]
    return {"memo_id": row.get("id"), "status": "created"}
