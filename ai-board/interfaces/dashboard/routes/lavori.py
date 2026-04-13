from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from loguru import logger

from core import notion_board
from db.client import get_service_client
from interfaces.dashboard.routes import base_context, parse_datetime, render, safely

router = APIRouter()

STATUS_META: dict[str, dict] = {
    "pending":  {"label": "In attesa",  "badge": "bg-amber-50 text-amber-700",   "dot": "bg-amber-400"},
    "running":  {"label": "In corso",   "badge": "bg-blue-50 text-blue-700",     "dot": "bg-blue-400"},
    "draft":    {"label": "Draft",      "badge": "bg-violet-50 text-violet-700", "dot": "bg-violet-400"},
    "review":   {"label": "In review",  "badge": "bg-orange-50 text-orange-700", "dot": "bg-orange-400"},
    "approved": {"label": "Approvato",  "badge": "bg-emerald-50 text-emerald-700", "dot": "bg-emerald-400"},
    "done":     {"label": "Completato", "badge": "bg-gray-100 text-gray-500",    "dot": "bg-gray-400"},
    "rejected": {"label": "Rifiutato",  "badge": "bg-rose-50 text-rose-700",     "dot": "bg-rose-400"},
    "error":    {"label": "Errore",     "badge": "bg-rose-50 text-rose-700",     "dot": "bg-rose-400"},
}

SOURCE_LABEL: dict[str, str] = {
    "website_contact_form": "Form contatti",
    "website_k_bot":        "K-BOT",
    "founder":              "Founder",
    "telegram":             "Telegram",
}

AGENT_LABEL: dict[str, str] = {
    "chief_of_staff":     "Chief of Staff",
    "solution_architect": "Solution Architect",
    "content_engine":     "Content Engine",
    "sales_enablement":   "Sales",
    "finance_kpi":        "Finance",
    "lead_generation":    "Sales",
    "market_intelligence":"Market Intel",
    "orchestrator":       "Orchestrator",
    "legal":              "Legal",
    "geo_seo":            "Geo SEO",
}

PRIORITY_LABEL = {1: "Critico", 2: "Alta", 3: "Media", 4: "Bassa", 5: "Minima"}
PRIORITY_CLASS = {
    1: "text-rose-600",
    2: "text-orange-500",
    3: "text-amber-500",
    4: "text-gray-400",
    5: "text-gray-300",
}

PRIORITY_TO_PIPELINE_SCORE = {1: 9, 2: 8, 3: 6, 4: 5, 5: 4}


def _enrich_task(task: dict) -> dict:
    status = task.get("status", "pending")
    meta = STATUS_META.get(status, STATUS_META["pending"])
    priority = task.get("priority") or 3
    return {
        **task,
        "status_label":  meta["label"],
        "status_badge":  meta["badge"],
        "status_dot":    meta["dot"],
        "agent_label":   AGENT_LABEL.get(task.get("assigned_to", ""), task.get("assigned_to", "—")),
        "source_label":  SOURCE_LABEL.get(task.get("requested_by", ""), task.get("requested_by", "—")),
        "priority_label": PRIORITY_LABEL.get(priority, "Media"),
        "priority_class": PRIORITY_CLASS.get(priority, "text-gray-400"),
        "created_fmt":   _fmt_date(task.get("created_at")),
    }


def _fmt_date(value: str | None) -> str:
    dt = parse_datetime(value)
    if not dt:
        return "—"
    return dt.strftime("%d/%m/%y %H:%M")


def _load_tasks(status_filter: str | None = None) -> list[dict]:
    if notion_board.notion_enabled():
        return [_enrich_task(row) for row in safely([], lambda: notion_board.list_tasks(status_filter), "Errore lettura tasks Notion")]

    client = get_service_client()
    query = client.table("tasks").select(
        "id,title,description,assigned_to,requested_by,status,priority,notes,created_at,updated_at"
    ).order("created_at", desc=True).limit(200)
    if status_filter and status_filter != "all":
        query = query.eq("status", status_filter)
    rows = safely([], lambda: query.execute().data or [], "Errore lettura tasks")
    return [_enrich_task(row) for row in rows]


def _status_counts() -> dict[str, int]:
    if notion_board.notion_enabled():
        rows = safely([], lambda: notion_board.list_tasks(), "Errore conteggio tasks Notion")
        counts: dict[str, int] = {}
        for row in rows:
            s = row.get("status", "pending")
            counts[s] = counts.get(s, 0) + 1
        return counts

    client = get_service_client()
    rows = safely(
        [],
        lambda: client.table("tasks").select("status").execute().data or [],
        "Errore conteggio tasks",
    )
    counts: dict[str, int] = {}
    for row in rows:
        s = row.get("status", "pending")
        counts[s] = counts.get(s, 0) + 1
    return counts


FILTER_TABS = [
    {"key": "all",      "label": "Tutti"},
    {"key": "pending",  "label": "In attesa"},
    {"key": "running",  "label": "In corso"},
    {"key": "review",   "label": "In review"},
    {"key": "done",     "label": "Completati"},
]

AGENT_OPTIONS = [
    ("chief_of_staff",     "Chief of Staff"),
    ("solution_architect", "Solution Architect"),
    ("content_engine",     "Content Engine"),
    ("sales_enablement",   "Sales"),
    ("finance_kpi",        "Finance"),
]


@router.get("/lavori")
async def lavori_page(request: Request, status: str = "all"):
    tasks = _load_tasks(status)
    counts = _status_counts()
    context = base_context(request, active_page="lavori", page_title="Lavori")
    context.update({
        "tasks": tasks,
        "counts": counts,
        "active_filter": status,
        "filter_tabs": FILTER_TABS,
        "agent_options": AGENT_OPTIONS,
        "total": counts.get("all") or sum(counts.values()),
    })
    return render(request, "lavori.html", context)


@router.post("/lavori")
async def create_task(
    request: Request,
    title: str = Form(...),
    description: str = Form(default=""),
    assigned_to: str = Form(default="chief_of_staff"),
    priority: int = Form(default=3),
):
    if notion_board.notion_enabled():
        notion_board.create_task(title, description, assigned_to, priority)
        return RedirectResponse(url="/lavori", status_code=303)

    client = get_service_client()
    now = datetime.now(UTC).isoformat()
    client.table("tasks").insert({
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description or None,
        "assigned_to": assigned_to,
        "requested_by": "founder",
        "status": "pending",
        "priority": priority,
        "created_at": now,
        "updated_at": now,
    }).execute()
    return RedirectResponse(url="/lavori", status_code=303)


@router.post("/lavori/{task_id}/status")
async def update_task_status(request: Request, task_id: str, new_status: str = Form(...)):
    if notion_board.notion_enabled():
        notion_board.update_task_status(task_id, new_status)
        return RedirectResponse(url=request.headers.get("referer", "/lavori"), status_code=303)

    client = get_service_client()
    client.table("tasks").update({
        "status": new_status,
        "updated_at": datetime.now(UTC).isoformat(),
    }).eq("id", task_id).execute()
    return RedirectResponse(url=request.headers.get("referer", "/lavori"), status_code=303)


@router.post("/lavori/{task_id}/to-pipeline")
async def move_task_to_pipeline(request: Request, task_id: str):
    if notion_board.notion_enabled():
        notion_board.create_lead_from_task(task_id)
        return RedirectResponse(url="/pipeline", status_code=303)

    return RedirectResponse(url=request.headers.get("referer", "/lavori"), status_code=303)

    return RedirectResponse(url="/pipeline", status_code=303)


@router.post("/lavori/{task_id}/delete")
async def delete_task(request: Request, task_id: str):
    if notion_board.notion_enabled():
        notion_board.archive_task(task_id)
        return RedirectResponse(url=request.headers.get("referer", "/lavori"), status_code=303)

    client = get_service_client()
    client.table("tasks").delete().eq("id", task_id).execute()
    return RedirectResponse(url=request.headers.get("referer", "/lavori"), status_code=303)
