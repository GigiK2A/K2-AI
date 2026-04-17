"""Agents controller — thin FastAPI adapter on top of `AgentsService`."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from db.models import AgentName
from interfaces.dashboard.routes import base_context, render
from services import AgentsService
from services.agents_service import resolve_agent_slug

router = APIRouter()
_service = AgentsService()


@router.get("/agents")
async def agents_page(
    request: Request, selected: str | None = Query(default=None)
):
    agents = _service.list_agents()
    selected_name = selected or (
        agents[0]["name"] if agents else AgentName.ORCHESTRATOR.value
    )
    selected_agent = next(
        (agent for agent in agents if agent["name"] == selected_name),
        agents[0] if agents else None,
    )
    context = base_context(
        request,
        active_page="agents",
        page_title="Agenti AI Board",
        page_subtitle="Monitoraggio operativo e accesso rapido alle chat degli agenti del board",
    )
    context.update(
        {"agents": agents, "selected_agent": selected_agent, "run": None}
    )
    return render(request, "agents.html", context)


@router.post("/agents/{agent_name}/run")
async def run_agent_route(request: Request, agent_name: str):
    form = await request.form()
    task = str(form.get("task", "")).strip()
    if not task:
        task = AgentsService.build_task_from_form(form)
    if not task:
        raise HTTPException(status_code=400, detail="Task non valido")

    run = _service.start_run(agent_name, task)
    context = base_context(
        request, active_page="agents", page_title="Agenti AI Board"
    )
    context["run"] = run
    return render(request, "partials/agent_run_result.html", context)


@router.post("/agents/content_engine/generate")
async def content_engine_generate(request: Request):
    form = await request.form()
    tipo_contenuto = str(form.get("tipo_contenuto", "")).strip()
    obiettivo = str(form.get("obiettivo", "")).strip()
    nicchia_target = str(form.get("nicchia_target", "")).strip()
    caso_studio = str(form.get("caso_studio", "")).strip()
    brief = str(form.get("brief", "")).strip()
    numero_varianti = (
        str(form.get("numero_varianti", "3")).strip() or "3"
    )

    context = base_context(
        request, active_page="agents", page_title="Content Engine"
    )
    if not brief:
        context["result"] = {
            "status": "error",
            "error": "Inserisci un brief prima di generare il contenuto.",
        }
        return render(request, "partials/agent_run_result.html", context)

    result = await _service.run_content_engine(
        tipo_contenuto=tipo_contenuto,
        obiettivo=obiettivo,
        nicchia_target=nicchia_target,
        caso_studio=caso_studio,
        brief=brief,
        numero_varianti=numero_varianti,
    )
    context["result"] = result
    return render(request, "partials/agent_run_result.html", context)


@router.get("/agents/{agent_name}/status")
async def agent_run_status(request: Request, agent_name: str, run_id: str):
    run = _service.get_run(agent_name, run_id)
    context = base_context(
        request, active_page="agents", page_title="Agenti AI Board"
    )
    context["run"] = run
    return render(request, "partials/agent_run_result.html", context)


@router.get("/agents/{agent_name}/history")
async def agent_history_partial(
    request: Request,
    agent_name: str,
    page: int = 1,
    status: str | None = None,
):
    context = base_context(
        request, active_page="agents", page_title="Dettaglio Agente"
    )
    context.update(
        _service.load_history_page(
            agent_name, page=page, status_filter=status
        )
    )
    return render(request, "partials/agent_history.html", context)


@router.get("/agents/{agent_name}/chat")
async def agent_chat_partial(request: Request, agent_name: str):
    context = base_context(
        request, active_page="agents", page_title="Chat Agente"
    )
    context.update(_service.chat_panel_payload(agent_name))
    return render(request, "partials/agent_chat_panel.html", context)


@router.post("/agents/{agent_name}/chat")
async def agent_chat_send(request: Request, agent_name: str):
    slug, _, _ = resolve_agent_slug(agent_name)
    form = await request.form()
    message = str(form.get("message", "")).strip()
    attachments = await _service.collect_chat_attachments(
        form, channel="agenti", agent_slug=slug
    )

    context = base_context(
        request, active_page="agents", page_title="Chat Agente"
    )
    if not message and not attachments:
        context.update(
            _service.chat_panel_payload(
                agent_name,
                chat_error="Scrivi un messaggio prima di inviare.",
            )
        )
        return render(request, "partials/agent_chat_panel.html", context)

    result = await _service.send_agent_chat(
        agent_slug=agent_name,
        message=message,
        attachments=attachments,
    )
    chat_error = (
        result.get("error") if result.get("status") == "error" else None
    )
    context.update(
        _service.chat_panel_payload(agent_name, chat_error=chat_error)
    )
    return render(request, "partials/agent_chat_panel.html", context)


@router.get("/agents/{agent_name}")
async def agent_detail(request: Request, agent_name: str):
    detail = _service.build_detail_context(agent_name)
    agent = detail["agent"]
    context = base_context(
        request,
        active_page="agents",
        page_title=agent["display_name"],
        page_subtitle=agent["role"],
    )
    context.update(detail)
    return render(request, "agent_detail.html", context)
