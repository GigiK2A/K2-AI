from collections import Counter
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Request

from core import notion_board
from core.orchestrator import resolve_agent_name
from db.client import get_service_client
from interfaces.dashboard.routes import base_context, parse_datetime, render, safely

router = APIRouter()

PIPELINE_ORDER = [
    ("identified", "Identificazione", "border-slate-300", False),
    ("qualified", "Qualificazione", "border-slate-400", False),
    ("contacted", "Contatto", "border-indigo-300", False),
    ("call_scheduled", "Chiamata", "border-indigo-400", False),
    ("proposal_sent", "Proposta", "border-indigo-500", False),
    ("won", "Chiuso (Vinto)", "", True),
]

WEEKDAYS_IT = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
MONTHS_IT = [
    "Gennaio",
    "Febbraio",
    "Marzo",
    "Aprile",
    "Maggio",
    "Giugno",
    "Luglio",
    "Agosto",
    "Settembre",
    "Ottobre",
    "Novembre",
    "Dicembre",
]

ACTIVITY_STYLE_MAP = {
    "content_engine": {"border": "border-rose-400", "accent": "bg-rose-50 text-rose-500", "icon": "edit_square", "emoji": "✍️"},
    "sales_enablement": {"border": "border-blue-400", "accent": "bg-blue-50 text-blue-500", "icon": "campaign", "emoji": "📈"},
    "chief_of_staff": {"border": "border-indigo-400", "accent": "bg-indigo-50 text-indigo-500", "icon": "hub", "emoji": "⚡"},
    "solution_architect": {"border": "border-violet-400", "accent": "bg-violet-50 text-violet-500", "icon": "architecture", "emoji": "🧩"},
    "finance_kpi": {"border": "border-emerald-400", "accent": "bg-emerald-50 text-emerald-500", "icon": "bar_chart", "emoji": "📊"},
}


def _format_home_date(value: datetime) -> str:
    return f"{WEEKDAYS_IT[value.weekday()]}, {value.day} {MONTHS_IT[value.month - 1]} {value.year}"


def _relative_time_it(value: str | datetime | None, now: datetime) -> str:
    dt = parse_datetime(value)
    if not dt:
        return "ora"

    delta = max(now - dt, timedelta())
    minutes = int(delta.total_seconds() // 60)
    if minutes <= 0:
        return "adesso"
    if minutes < 60:
        return f"{minutes} min fa"

    hours = minutes // 60
    if hours < 24:
        return f"{hours} ora fa" if hours == 1 else f"{hours} ore fa"

    days = hours // 24
    return f"{days} giorno fa" if days == 1 else f"{days} giorni fa"


def _activity_style(agent: str | None, status: str | None) -> dict[str, str]:
    if agent:
        try:
            agent = resolve_agent_name(agent).value
        except Exception:
            pass
    if agent in ACTIVITY_STYLE_MAP:
        return ACTIVITY_STYLE_MAP[agent]
    if status in {"approved", "done"}:
        return {"border": "border-emerald-400", "accent": "bg-emerald-50 text-emerald-500", "icon": "task_alt", "emoji": "✓"}
    if status in {"rejected", "error"}:
        return {"border": "border-rose-400", "accent": "bg-rose-50 text-rose-500", "icon": "cancel", "emoji": "!"}
    return {"border": "border-indigo-400", "accent": "bg-indigo-50 text-indigo-500", "icon": "draft", "emoji": "•"}


def _task_completion_change(current: int, previous: int) -> int:
    if previous <= 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100)


def _build_activity_feed(approvals: list[dict], logs: list[dict], now: datetime) -> list[dict]:
    logs_by_task = {row.get("task_id"): row for row in logs if row.get("task_id")}
    approval_task_ids = {row.get("task_id") for row in approvals if row.get("task_id")}
    events: list[dict] = []

    for approval in approvals:
        linked_log = logs_by_task.get(approval.get("task_id"))
        style = _activity_style(approval.get("agent"), approval.get("status"))
        title = (linked_log or {}).get("action") or "Draft generato"
        preview = approval.get("content_preview") or (linked_log or {}).get("output_summary") or "Nessuna anteprima disponibile."
        events.append(
            {
                "approval_id": approval.get("id"),
                "agent": approval.get("agent"),
                "status": approval.get("status"),
                "title": title,
                "preview": preview,
                "created_at": approval.get("created_at"),
                "time_ago": _relative_time_it(approval.get("created_at"), now),
                "border_class": style["border"],
                "accent_class": style["accent"],
                "icon": style["icon"],
                "emoji": style["emoji"],
            }
        )

    for row in logs:
        if row.get("task_id") and row.get("task_id") in approval_task_ids:
            continue
        style = _activity_style(row.get("agent"), row.get("status"))
        events.append(
            {
                "approval_id": None,
                "agent": row.get("agent"),
                "status": row.get("status"),
                "title": row.get("action") or "Attività agente",
                "preview": row.get("output_summary") or "Attività registrata nel board.",
                "created_at": row.get("created_at"),
                "time_ago": _relative_time_it(row.get("created_at"), now),
                "border_class": style["border"],
                "accent_class": style["accent"],
                "icon": style["icon"],
                "emoji": style["emoji"],
            }
        )

    events.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return events[:4]


def _load_home_data() -> dict:
    client = get_service_client()
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_start = now - timedelta(days=7)
    previous_week_start = now - timedelta(days=14)

    if notion_board.notion_enabled():
        approvals_pending = safely([], lambda: notion_board.list_approvals(["draft", "review"]), "Errore lettura draft Notion")
        all_logs = safely([], lambda: notion_board.list_agent_logs(limit=500), "Errore lettura log Notion")
        logs_today = [row for row in all_logs if (parse_datetime(row.get("created_at")) or now) >= today_start]
        logs_yesterday = [
            row
            for row in all_logs
            if yesterday_start <= (parse_datetime(row.get("created_at")) or now) < today_start
        ]
    else:
        approvals_pending = safely(
            [],
            lambda: client.table("approvals").select("id,task_id,agent,status,content_preview,created_at").in_("status", ["draft", "review"]).execute().data or [],
            "Errore lettura draft pendenti",
        )
        logs_today = safely(
            [],
            lambda: client.table("agent_logs").select("agent,created_at").gte("created_at", today_start.isoformat()).execute().data or [],
            "Errore lettura log odierni",
        )
        logs_yesterday = safely(
            [],
            lambda: client.table("agent_logs").select("agent,created_at").gte("created_at", yesterday_start.isoformat()).lt("created_at", today_start.isoformat()).execute().data or [],
            "Errore lettura log ieri",
        )
    leads = (
        safely([], notion_board.list_pipeline_leads, "Errore lettura pipeline Notion")
        if notion_board.notion_enabled()
        else safely(
            [],
            lambda: client.table("pipeline_leads").select("*").execute().data or [],
            "Errore lettura pipeline",
        )
    )
    tasks = safely([], notion_board.list_tasks, "Errore lettura tasks Notion") if notion_board.notion_enabled() else []
    if notion_board.notion_enabled():
        approved_recent = []
        approvals = safely([], lambda: notion_board.list_approvals(limit=20), "Errore lettura attività approvals Notion")
        logs = all_logs[:50]
    else:
        approved_recent = safely(
            [],
            lambda: client.table("approvals").select("id,status,reviewed_at,created_at").eq("status", "approved").execute().data or [],
            "Errore lettura approvals approvati",
        )
        approvals = safely(
            [],
            lambda: client.table("approvals").select("id,task_id,agent,status,content_preview,created_at,reviewed_at").order("created_at", desc=True).limit(20).execute().data or [],
            "Errore lettura attività approval",
        )
        logs = safely(
            [],
            lambda: client.table("agent_logs").select("id,task_id,agent,action,status,llm_model,created_at,output_summary").order("created_at", desc=True).limit(50).execute().data or [],
            "Errore lettura attività log",
        )

    if notion_board.notion_enabled():
        completed_statuses = {"approved", "done"}
        approved_count = sum(
            1
            for task in tasks
            if task.get("status") in completed_statuses
            and (parse_datetime(task.get("updated_at")) or parse_datetime(task.get("created_at")) or now) >= week_start
        )
        approved_previous_week = sum(
            1
            for task in tasks
            if task.get("status") in completed_statuses
            and previous_week_start <= (parse_datetime(task.get("updated_at")) or parse_datetime(task.get("created_at")) or now) < week_start
        )
    else:
        approved_count = 0
        approved_previous_week = 0
        for approval in approved_recent:
            reviewed_at = parse_datetime(approval.get("reviewed_at")) or parse_datetime(approval.get("created_at"))
            if reviewed_at and reviewed_at >= week_start:
                approved_count += 1
            elif reviewed_at and reviewed_at >= previous_week_start:
                approved_previous_week += 1

    pipeline_summary = Counter(lead.get("status", "unknown") for lead in leads)
    pending_created_today = sum(1 for item in approvals_pending if (parse_datetime(item.get("created_at")) or now) >= today_start)
    leads_created_week = sum(1 for lead in leads if (parse_datetime(lead.get("created_at")) or now) >= week_start)
    active_agents_today = len(
        {
            resolve_agent_name(row.get("agent")).value if row.get("agent") else None
            for row in logs_today
            if row.get("agent")
        }
    )
    active_agents_yesterday = len(
        {
            resolve_agent_name(row.get("agent")).value if row.get("agent") else None
            for row in logs_yesterday
            if row.get("agent")
        }
    )
    active_agents_delta = active_agents_today - active_agents_yesterday
    task_completion_change = _task_completion_change(approved_count, approved_previous_week)
    pipeline_rows = [
        {
            "key": key,
            "label": label,
            "count": pipeline_summary.get(key, 0),
            "border_class": border_class,
            "is_won": is_won,
        }
        for key, label, border_class, is_won in PIPELINE_ORDER
    ]
    activity_feed = _build_activity_feed(approvals, logs, now)

    return {
        "today_label": _format_home_date(now),
        "pending_approvals": len(approvals_pending),
        "pending_created_today": pending_created_today,
        "active_agents_today": active_agents_today,
        "active_agents_delta": active_agents_delta,
        "pipeline_leads": len(leads),
        "pipeline_created_week": leads_created_week,
        "tasks_done_week": approved_count,
        "tasks_done_change_pct": task_completion_change,
        "activity_feed": activity_feed,
        "pipeline_summary": dict(pipeline_summary),
        "pipeline_rows": pipeline_rows,
    }


@router.get("/")
async def home_page(request: Request):
    data = _load_home_data()
    context = base_context(
        request,
        active_page="home",
        page_title="Panoramica",
        page_subtitle=data["today_label"],
    )
    context.update(data)
    return render(request, "home.html", context)


@router.get("/partials/kpi")
async def home_kpi_partial(request: Request):
    data = _load_home_data()
    context = base_context(request, active_page="home", page_title="Panoramica")
    context.update(data)
    return render(request, "partials/kpi_cards.html", context)


@router.get("/partials/activity")
async def home_activity_partial(request: Request):
    data = _load_home_data()
    context = base_context(request, active_page="home", page_title="Panoramica")
    context.update(data)
    return render(request, "partials/activity_feed.html", context)
