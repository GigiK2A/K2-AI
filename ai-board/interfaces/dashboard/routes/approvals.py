from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import Response

from core import notion_board
from core.approval import approve, get_approval, reject
from db.client import get_service_client
from interfaces.dashboard.routes import base_context, pretty_json, render, safely
from interfaces.telegram.notifier import notify_sync, notify_system

router = APIRouter()


def _load_approvals() -> dict[str, list[dict]]:
    if notion_board.notion_enabled():
        pending = safely(
            [],
            lambda: notion_board.list_approvals(["draft", "review"]),
            "Errore lettura approvals Notion pending",
        )
        approved = safely(
            [],
            lambda: notion_board.list_approvals(["approved"], limit=20),
            "Errore lettura approvals Notion approved",
        )
        rejected = safely(
            [],
            lambda: notion_board.list_approvals(["rejected"], limit=20),
            "Errore lettura approvals Notion rejected",
        )
        return {"pending": pending, "approved": approved, "rejected": rejected}

    client = get_service_client()
    pending = safely(
        [],
        lambda: client.table("approvals").select("*").in_("status", ["draft", "review"]).order("created_at", desc=True).execute().data or [],
        "Errore lettura approvals pending",
    )
    approved = safely(
        [],
        lambda: client.table("approvals").select("*").eq("status", "approved").order("reviewed_at", desc=True).limit(20).execute().data or [],
        "Errore lettura approvals approved",
    )
    rejected = safely(
        [],
        lambda: client.table("approvals").select("*").eq("status", "rejected").order("reviewed_at", desc=True).limit(20).execute().data or [],
        "Errore lettura approvals rejected",
    )
    return {"pending": pending, "approved": approved, "rejected": rejected}


def _agent_run_feedback_context(message: str, approval_id: str, status: str) -> dict:
    return {
        "approval_feedback": {"status": status, "approval_id": approval_id, "message": message}
    }


@router.get("/approvals")
async def approvals_page(request: Request):
    context = base_context(
        request,
        active_page="approvals",
        page_title="Approvazioni",
        page_subtitle="Draft in revisione, storico approvazioni e rifiuti",
    )
    context["full_canvas"] = True
    context["suppress_page_header"] = True
    context.update(_load_approvals())
    return render(request, "approvals.html", context)


@router.get("/approvals/badge")
async def approvals_badge(request: Request):
    context = base_context(request, active_page="approvals", page_title="Approvazioni")
    return render(request, "partials/approvals_badge.html", context)


@router.post("/approvals/{approval_id}/approve")
async def approve_route(request: Request, approval_id: str, notes: str = Form(default="")):
    ok = approve(approval_id, notes or None)
    if not ok:
        raise HTTPException(status_code=500, detail="Errore approvazione")

    notify_sync(notify_system(f"Dashboard: draft {approval_id[:8]} approvato."))
    fragment = request.query_params.get("fragment")
    agent_name = request.query_params.get("agent_name")
    page = int(request.query_params.get("page", "1"))
    status_filter = request.query_params.get("status") or None

    if fragment == "history" and agent_name:
        from interfaces.dashboard.routes.agents import _load_agent_history_page

        context = base_context(request, active_page="agents", page_title="Dettaglio Agente")
        context.update(_load_agent_history_page(agent_name, page=page, status_filter=status_filter))
        return render(request, "partials/agent_history.html", context)

    if fragment == "agent_chat" and agent_name:
        from interfaces.dashboard.routes.agents import _agent_chat_panel_payload

        context = base_context(request, active_page="agents", page_title="Chat Agente")
        context.update(_agent_chat_panel_payload(agent_name))
        return render(request, "partials/agent_chat_panel.html", context)

    if fragment == "board_chat" and agent_name:
        from interfaces.dashboard.routes.board_chat import _board_chat_payload

        context = base_context(request, active_page="board_chat", page_title="Chat del Board")
        context.update(_board_chat_payload(agent_name))
        return render(request, "partials/board_chat_shell.html", context)

    if fragment == "project_detail":
        project_id = request.query_params.get("project_id")
        if project_id:
            from interfaces.dashboard.routes.lavori import _detail_context

            return render(request, "partials/project_detail_content.html", _detail_context(request, project_id))

    if fragment == "home_activity":
        from interfaces.dashboard.routes.home import _load_home_data

        context = base_context(request, active_page="home", page_title="Panoramica")
        context.update(_load_home_data())
        return render(request, "partials/activity_feed.html", context)

    if request.headers.get("HX-Target") in {"agent-run-result", "run-result"} or fragment == "detail_run":
        context = base_context(request, active_page="agents", page_title="Agenti AI Board")
        context.update(_agent_run_feedback_context("Draft approvato dalla dashboard.", approval_id, "approved"))
        return render(request, "partials/agent_run_result.html", context)

    context = base_context(request, active_page="approvals", page_title="Approvazioni")
    context.update(_load_approvals())
    return render(request, "partials/approvals_list.html", context)


@router.post("/approvals/{approval_id}/reject")
async def reject_route(request: Request, approval_id: str, notes: str = Form(default="")):
    ok = reject(approval_id, notes or None)
    if not ok:
        raise HTTPException(status_code=500, detail="Errore rifiuto")

    notify_sync(notify_system(f"Dashboard: draft {approval_id[:8]} rifiutato."))
    fragment = request.query_params.get("fragment")
    agent_name = request.query_params.get("agent_name")
    page = int(request.query_params.get("page", "1"))
    status_filter = request.query_params.get("status") or None

    if fragment == "history" and agent_name:
        from interfaces.dashboard.routes.agents import _load_agent_history_page

        context = base_context(request, active_page="agents", page_title="Dettaglio Agente")
        context.update(_load_agent_history_page(agent_name, page=page, status_filter=status_filter))
        return render(request, "partials/agent_history.html", context)

    if fragment == "agent_chat" and agent_name:
        from interfaces.dashboard.routes.agents import _agent_chat_panel_payload

        context = base_context(request, active_page="agents", page_title="Chat Agente")
        context.update(_agent_chat_panel_payload(agent_name))
        return render(request, "partials/agent_chat_panel.html", context)

    if fragment == "board_chat" and agent_name:
        from interfaces.dashboard.routes.board_chat import _board_chat_payload

        context = base_context(request, active_page="board_chat", page_title="Chat del Board")
        context.update(_board_chat_payload(agent_name))
        return render(request, "partials/board_chat_shell.html", context)

    if fragment == "project_detail":
        project_id = request.query_params.get("project_id")
        if project_id:
            from interfaces.dashboard.routes.lavori import _detail_context

            return render(request, "partials/project_detail_content.html", _detail_context(request, project_id))

    if fragment == "home_activity":
        from interfaces.dashboard.routes.home import _load_home_data

        context = base_context(request, active_page="home", page_title="Panoramica")
        context.update(_load_home_data())
        return render(request, "partials/activity_feed.html", context)

    if request.headers.get("HX-Target") in {"agent-run-result", "run-result"} or fragment == "detail_run":
        context = base_context(request, active_page="agents", page_title="Agenti AI Board")
        context.update(_agent_run_feedback_context("Draft rifiutato dalla dashboard.", approval_id, "rejected"))
        return render(request, "partials/agent_run_result.html", context)

    context = base_context(request, active_page="approvals", page_title="Approvazioni")
    context.update(_load_approvals())
    return render(request, "partials/approvals_list.html", context)


@router.get("/approvals/{approval_id}/full")
async def approval_full(request: Request, approval_id: str):
    approval = get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval non trovato")

    full_content = approval.get("full_content") or {}
    full_output = full_content.get("output") if isinstance(full_content, dict) else None
    task_text = full_content.get("task") if isinstance(full_content, dict) else None
    extra_context = full_content.get("context") if isinstance(full_content, dict) else None

    context = base_context(request, active_page="approvals", page_title="Approvazioni")
    context["approval"] = approval
    context["full_output"] = full_output
    context["task_text"] = task_text
    context["extra_context"] = extra_context
    context["full_content_json"] = pretty_json(full_content)
    return render(request, "partials/approval_full.html", context)


@router.get("/approvals/close-modal")
async def approval_close_modal() -> Response:
    return Response("")
