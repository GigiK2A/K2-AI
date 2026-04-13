from fastapi import APIRouter, Query, Request

from core import notion_board
from db.client import get_service_client
from interfaces.dashboard.routes import base_context, is_htmx, render, safely

router = APIRouter()
PAGE_SIZE = 20


def _load_logs(agent_name: str | None, page: int) -> dict:
    if notion_board.notion_enabled():
        rows = safely([], lambda: notion_board.list_agent_logs(limit=500), "Errore caricamento logs Notion")
        agents_list = sorted({row.get("agent") for row in rows if row.get("agent")})
        if agent_name:
            rows = [row for row in rows if row.get("agent") == agent_name]
        total_count = len(rows)
        start = max(page - 1, 0) * PAGE_SIZE
        end = start + PAGE_SIZE
        return {
            "logs": rows[start:end],
            "agents_list": agents_list,
            "filter_agent": agent_name,
            "page": page,
            "page_size": PAGE_SIZE,
            "total_count": total_count,
            "has_prev": page > 1,
            "has_next": end < total_count,
        }

    client = get_service_client()
    rows = safely(
        [],
        lambda: client.table("agent_logs").select("*").order("created_at", desc=True).limit(500).execute().data or [],
        "Errore caricamento logs",
    )
    agents_list = sorted({row.get("agent") for row in rows if row.get("agent")})
    if agent_name:
        rows = [row for row in rows if row.get("agent") == agent_name]
    total_count = len(rows)
    start = max(page - 1, 0) * PAGE_SIZE
    end = start + PAGE_SIZE
    return {
        "logs": rows[start:end],
        "agents_list": agents_list,
        "filter_agent": agent_name,
        "page": page,
        "page_size": PAGE_SIZE,
        "total_count": total_count,
        "has_prev": page > 1,
        "has_next": end < total_count,
    }


@router.get("/logs")
async def logs_page(request: Request, agent: str | None = Query(default=None), page: int = Query(default=1, ge=1)):
    context = base_context(
        request,
        active_page="logs",
        page_title="Log Attività",
        page_subtitle="Storico esecuzioni, modelli LLM e tempi di risposta",
    )
    context["full_canvas"] = True
    context["suppress_page_header"] = True
    context.update(_load_logs(agent, page))
    if is_htmx(request):
        return render(request, "partials/logs_table.html", context)
    return render(request, "logs.html", context)
