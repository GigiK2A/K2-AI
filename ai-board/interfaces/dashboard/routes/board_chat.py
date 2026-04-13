import asyncio

from fastapi import APIRouter, Request

from core.orchestrator import run_agent
from interfaces.dashboard.routes import base_context, render
from interfaces.dashboard.routes.agents import (
    _agent_meta,
    _build_chat_history_context,
    _collect_chat_attachments,
    _load_agents_data,
    _load_agent_chat_turns,
    _resolve_agent_slug,
)

router = APIRouter()


def _board_agents() -> list[dict]:
    return [
        {
            "slug": agent["detail_slug"],
            "display_name": agent["display_name"],
            "provider": agent["provider"],
            "status": agent["status"],
        }
        for agent in _load_agents_data()
    ]


def _board_chat_payload(agent_slug: str, chat_error: str | None = None) -> dict:
    selected_slug, _, _ = _resolve_agent_slug(agent_slug)
    selected_agent = _agent_meta(selected_slug)
    return {
        "board_agents": _board_agents(),
        "selected_agent": selected_agent,
        "chat_turns": _load_agent_chat_turns(selected_slug),
        "chat_error": chat_error,
    }


@router.get("/board-chat")
async def board_chat_page(request: Request, agent: str = "orchestrator"):
    context = base_context(
        request,
        active_page="board_chat",
        page_title="Chat del Board",
        page_subtitle="Parla con qualunque agente del board da una chat centrale con storico persistente.",
    )
    context.update(_board_chat_payload(agent))
    return render(request, "board_chat.html", context)


@router.get("/board-chat/thread")
async def board_chat_thread(request: Request, agent: str = "orchestrator"):
    context = base_context(request, active_page="board_chat", page_title="Chat del Board")
    context.update(_board_chat_payload(agent))
    return render(request, "partials/board_chat_shell.html", context)


@router.post("/board-chat/send")
async def board_chat_send(request: Request):
    form = await request.form()
    agent_slug = str(form.get("agent_slug", "orchestrator")).strip() or "orchestrator"
    message = str(form.get("message", "")).strip()
    selected_slug, _, agent_enum = _resolve_agent_slug(agent_slug)
    attachments = await _collect_chat_attachments(form, channel="board", agent_slug=selected_slug)

    context = base_context(request, active_page="board_chat", page_title="Chat del Board")
    if not message and not attachments:
        context.update(_board_chat_payload(selected_slug, chat_error="Scrivi un messaggio prima di inviare."))
        return render(request, "partials/board_chat_shell.html", context)

    task = message or "Analizza gli allegati caricati e rispondi in modo utile e operativo."
    if attachments:
        task += "\n\n## Allegati caricati\n" + "\n".join(
            f"- {item['name']} ({item['size_bytes']} byte)" for item in attachments
        )

    chat_context = {
        "chat_history": _build_chat_history_context(selected_slug, limit=12),
        "interface": "dashboard_board_chat",
        "channel": "board_chat",
        "selected_agent": selected_slug,
        "attachments": [
            {
                "name": item["name"],
                "path": item["path"],
                "web_path": item["web_path"],
                "size_bytes": item["size_bytes"],
                "excerpt": item["excerpt"],
            }
            for item in attachments
        ],
        "__board": {
            "content_type": "board_chat",
            "requested_by": "dashboard_board_chat",
        },
    }
    result = await asyncio.to_thread(run_agent, agent_enum, task, chat_context)
    chat_error = result.get("error") if result.get("status") == "error" else None

    context.update(_board_chat_payload(selected_slug, chat_error=chat_error))
    return render(request, "partials/board_chat_shell.html", context)
