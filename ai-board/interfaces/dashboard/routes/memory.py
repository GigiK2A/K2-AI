from collections import defaultdict

from fastapi import APIRouter, Form, Request

from core import notion_board
from core.memory import set_memory
from db.client import get_service_client
from interfaces.dashboard.routes import base_context, parse_form_value, render, safely

router = APIRouter()


def _load_memory_data(selected_category: str | None = None) -> dict:
    if notion_board.notion_enabled():
        rows = safely([], notion_board.list_memory_items, "Errore caricamento shared memory Notion")
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            grouped[row.get("category", "custom")].append(row)
        category = selected_category or (next(iter(grouped.keys()), "business"))
        return {
            "categories": dict(grouped),
            "selected_category": category,
            "items": grouped.get(category, []),
        }

    client = get_service_client()
    rows = safely(
        [],
        lambda: client.table("shared_memory").select("key,value,category,updated_at,updated_by").order("category").execute().data or [],
        "Errore caricamento shared memory",
    )

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row.get("category", "custom")].append(row)

    category = selected_category or (next(iter(grouped.keys()), "business"))
    return {
        "categories": dict(grouped),
        "selected_category": category,
        "items": grouped.get(category, []),
    }


@router.get("/memory")
async def memory_page(request: Request, category: str | None = None):
    context = base_context(
        request,
        active_page="memory",
        page_title="Memoria Condivisa",
        page_subtitle="Contesto persistente del board, organizzato per categorie",
    )
    context["full_canvas"] = True
    context["suppress_page_header"] = True
    context.update(_load_memory_data(category))
    return render(request, "memory.html", context)


@router.get("/memory/{category}")
async def memory_category(request: Request, category: str):
    context = base_context(request, active_page="memory", page_title="Memoria Condivisa")
    context.update(_load_memory_data(category))
    return render(request, "partials/memory_list.html", context)


@router.post("/memory/{key:path}")
async def memory_update(request: Request, key: str, value: str = Form(...), category: str = Form(...)):
    parsed_value = parse_form_value(value)
    set_memory(key, parsed_value, category=category)

    context = base_context(request, active_page="memory", page_title="Memoria Condivisa")
    context.update(_load_memory_data(category))
    return render(request, "partials/memory_list.html", context)
