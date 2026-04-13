import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request

from core import notion_board
from core.config import settings
from core.conversation import build_agent_conversation_context, load_agent_conversation_turns
from core.orchestrator import AGENT_REGISTRY, related_agent_names, resolve_agent_name, run_agent
from db.client import get_service_client
from db.models import AgentName, LLMProvider
from interfaces.dashboard.routes import base_context, parse_datetime, render, safely, truncate

router = APIRouter()

RUN_REGISTRY: dict[str, dict] = {}
URL_SLUG_ALIASES = {
    "risk_human_review": AgentName.FINANCE_KPI.value,
    AgentName.OFFER_POSITIONING.value: AgentName.CONTENT_ENGINE.value,
    AgentName.BRAND_STRATEGY.value: AgentName.CONTENT_ENGINE.value,
    AgentName.MARKETING_STRATEGY.value: AgentName.CONTENT_ENGINE.value,
    AgentName.LEAD_GENERATION.value: AgentName.SALES_ENABLEMENT.value,
    AgentName.OUTREACH.value: AgentName.SALES_ENABLEMENT.value,
    AgentName.PROJECT_OPERATIONS.value: AgentName.CHIEF_OF_STAFF.value,
    AgentName.KNOWLEDGE.value: AgentName.CHIEF_OF_STAFF.value,
    AgentName.RISK_REVIEW.value: AgentName.FINANCE_KPI.value,
}
CHAT_UPLOADS_DIR = Path(__file__).resolve().parents[3] / "uploads" / "chat"
TEXT_ATTACHMENT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".csv",
    ".json",
    ".log",
    ".xml",
    ".html",
    ".htm",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".sql",
    ".yml",
    ".yaml",
}
MONTHS_SHORT_IT = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]


def _detail_slug(agent_name: str) -> str:
    return URL_SLUG_ALIASES.get(agent_name, agent_name)


def _resolve_agent_slug(slug: str) -> tuple[str, str, AgentName]:
    internal_name = URL_SLUG_ALIASES.get(slug, slug)
    try:
        agent_enum = resolve_agent_name(AgentName(internal_name))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Agente non trovato") from exc
    return _detail_slug(agent_enum.value), agent_enum.value, agent_enum


def _agent_display_name(agent_slug: str) -> str:
    return agent_slug.replace("_", " ").title()


def _status_meta(status: str) -> dict[str, str]:
    if status == "draft_ready":
        return {"label": "Draft pronto", "class": "bg-amber-100 text-amber-700"}
    if status == "running":
        return {"label": "In esecuzione", "class": "bg-sky-100 text-sky-700"}
    return {"label": "Inattivo", "class": "bg-surface-container-high text-on-surface-variant"}


def _compact_datetime(value: str | None) -> str:
    dt = parse_datetime(value)
    if not dt:
        return "—"
    return f"{dt.day:02d} {MONTHS_SHORT_IT[dt.month - 1]}, {dt.strftime('%H:%M')}"


def _agent_status(agent_name: str) -> str:
    canonical_name = resolve_agent_name(agent_name).value
    if any(item.get("agent_name") == canonical_name and item.get("state") == "running" for item in RUN_REGISTRY.values()):
        return "running"

    if notion_board.notion_enabled():
        recent_cutoff = datetime.now(UTC) - timedelta(hours=2)
        related_names = {item.value for item in related_agent_names(canonical_name)}
        recent_draft = safely(
            [],
            lambda: [
                item
                for item in notion_board.list_approvals(["draft", "review"])
                if item.get("agent") in related_names and (parse_datetime(item.get("created_at")) or datetime.min.replace(tzinfo=UTC)) >= recent_cutoff
            ],
            f"Errore lettura stato agente Notion {agent_name}",
        )
        return "draft_ready" if recent_draft else "idle"

    client = get_service_client()
    recent_cutoff = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    related_names = [item.value for item in related_agent_names(canonical_name)]
    recent_draft = safely(
        [],
        lambda: (
            client.table("approvals")
            .select("id")
            .in_("agent", related_names)
            .eq("status", "draft")
            .gte("created_at", recent_cutoff)
            .limit(1)
            .execute()
            .data
            or []
        ),
        f"Errore lettura stato agente {agent_name}",
    )
    return "draft_ready" if recent_draft else "idle"


def _agent_meta(agent_slug: str) -> dict:
    slug, internal_name, agent_enum = _resolve_agent_slug(agent_slug)
    agent_class = AGENT_REGISTRY.get(agent_enum)
    provider = getattr(agent_class, "provider", LLMProvider.OPENAI)
    model = getattr(agent_class, "model", None)
    default_model = "claude-sonnet-4-6" if provider == LLMProvider.ANTHROPIC else "gpt-4o"
    fallback_provider = getattr(agent_class, "fallback_provider", None)
    if not isinstance(fallback_provider, LLMProvider):
        fallback_provider = LLMProvider.OPENAI if provider == LLMProvider.ANTHROPIC else LLMProvider.ANTHROPIC
    fallback_model = getattr(agent_class, "fallback_model", None) or (
        settings.default_anthropic_model if fallback_provider == LLMProvider.ANTHROPIC else settings.default_openai_model
    )
    status = _agent_status(internal_name)
    return {
        "slug": slug,
        "name": slug,
        "internal_name": internal_name,
        "display_name": _agent_display_name(slug),
        "role": getattr(agent_class, "role", ""),
        "goal": getattr(agent_class, "goal", ""),
        "instructions": getattr(agent_class, "instructions", []),
        "provider": provider.value if hasattr(provider, "value") else str(provider),
        "model": model or default_model,
        "fallback_provider": fallback_provider.value,
        "fallback_model": fallback_model,
        "status": status,
        "status_meta": _status_meta(status),
    }


def _load_agents_data() -> list[dict]:
    if notion_board.notion_enabled():
        logs = safely([], lambda: notion_board.list_agent_logs(limit=200), "Errore lettura log agenti Notion")
    else:
        client = get_service_client()
        logs = safely(
            [],
            lambda: (
                client.table("agent_logs")
                .select("agent,created_at,output_summary,status")
                .order("created_at", desc=True)
                .limit(200)
                .execute()
                .data
                or []
            ),
            "Errore lettura log agenti",
        )

    latest_by_agent: dict[str, dict] = {}
    for row in logs:
        try:
            canonical = resolve_agent_name(row.get("agent")).value
        except Exception:
            canonical = row.get("agent")
        latest_by_agent.setdefault(canonical, row)

    agent_rows = []
    for name, cls in AGENT_REGISTRY.items():
        latest = latest_by_agent.get(name.value, {})
        provider = getattr(cls, "provider", LLMProvider.OPENAI)
        agent_rows.append(
            {
                "name": name.value,
                "display_name": _agent_display_name(_detail_slug(name.value)),
                "role": getattr(cls, "role", ""),
                "provider": provider.value if isinstance(provider, LLMProvider) else str(provider),
                "last_run": latest.get("created_at"),
                "last_output_preview": truncate(latest.get("output_summary") or "", 80),
                "status": _agent_status(name.value),
                "detail_slug": _detail_slug(name.value),
            }
        )
    return agent_rows


def _build_task_from_form(form) -> str:
    task_parts = []
    for key, value in form.multi_items():
        if key in {"csrf_token", "execution_mode"}:
            continue
        if hasattr(value, "filename"):
            continue
        text = str(value).strip()
        if not text:
            continue
        if text.lower() == "on":
            text = "Sì"
        label = key.replace("_", " ").capitalize()
        task_parts.append(f"{label}: {text}")
    return "\n".join(task_parts)


def _load_agent_pending(agent_name: str) -> list[dict]:
    if notion_board.notion_enabled():
        related_names = {item.value for item in related_agent_names(agent_name)}
        return safely(
            [],
            lambda: [item for item in notion_board.list_approvals(["draft", "review"]) if item.get("agent") in related_names],
            f"Errore lettura approvals agente Notion {agent_name}",
        )

    client = get_service_client()
    related_names = [item.value for item in related_agent_names(agent_name)]
    return safely(
        [],
        lambda: (
            client.table("approvals")
            .select("*")
            .in_("agent", related_names)
            .in_("status", ["draft", "review"])
            .order("created_at", desc=True)
            .execute()
            .data
            or []
        ),
        f"Errore lettura approvals agente {agent_name}",
    )


def _load_agent_runs(agent_slug: str, limit: int = 200) -> dict:
    slug, internal_name, _ = _resolve_agent_slug(agent_slug)
    if notion_board.notion_enabled():
        related_names = {item.value for item in related_agent_names(internal_name)}
        logs = safely(
            [],
            lambda: [row for row in notion_board.list_agent_logs(limit=500) if row.get("agent") in related_names][:limit],
            f"Errore caricamento log agente Notion {internal_name}",
        )
        approvals = safely(
            [],
            lambda: [row for row in notion_board.list_approvals(limit=500) if row.get("agent") in related_names],
            f"Errore caricamento approvals agente Notion {internal_name}",
        )
        approval_map = {row.get("task_id"): row for row in approvals if row.get("task_id")}
        rows = []
        for log in logs:
            approval = approval_map.get(log.get("task_id"))
            full_content = approval.get("full_content") if isinstance(approval, dict) else {}
            task_text = ""
            output_text = ""
            context_data = None
            if isinstance(full_content, dict):
                task_text = str(full_content.get("task") or "")
                output_text = str(full_content.get("output") or "")
                context_data = full_content.get("context")
            rows.append(
                {
                    **log,
                    "display_status": approval.get("status") if approval else log.get("status"),
                    "approval": approval,
                    "approval_id": approval.get("id") if approval else None,
                    "task_text": task_text or str(log.get("action") or ""),
                    "output_text": output_text or str(log.get("output_summary") or ""),
                    "context_data": context_data,
                }
            )
        return {"slug": slug, "internal_name": internal_name, "rows": rows}

    client = get_service_client()
    related_names = [item.value for item in related_agent_names(internal_name)]
    logs = safely(
        [],
        lambda: (
            client.table("agent_logs")
            .select("*")
            .in_("agent", related_names)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
            .data
            or []
        ),
        f"Errore caricamento log agente {internal_name}",
    )

    task_ids = [row.get("task_id") for row in logs if row.get("task_id")]
    approvals = []
    if task_ids:
        approvals = safely(
            [],
            lambda: (
                client.table("approvals")
                .select("id,task_id,status,full_content,founder_notes,created_at,reviewed_at")
                .in_("task_id", task_ids)
                .execute()
                .data
                or []
            ),
            f"Errore caricamento approvals agente {internal_name}",
        )

    approval_map = {row.get("task_id"): row for row in approvals if row.get("task_id")}
    rows = []
    for log in logs:
        approval = approval_map.get(log.get("task_id"))
        full_content = approval.get("full_content") if isinstance(approval, dict) else {}
        task_text = ""
        output_text = ""
        context_data = None
        if isinstance(full_content, dict):
            task_text = str(full_content.get("task") or "")
            output_text = str(full_content.get("output") or "")
            context_data = full_content.get("context")
        if not task_text:
            task_text = str(log.get("action") or "")
        if not output_text:
            output_text = str(log.get("output_summary") or "")
        display_status = approval.get("status") if approval else log.get("status")
        rows.append(
            {
                **log,
                "display_status": display_status,
                "approval": approval,
                "approval_id": approval.get("id") if approval else None,
                "task_text": task_text,
                "output_text": output_text,
                "context_data": context_data,
            }
        )

    return {"slug": slug, "internal_name": internal_name, "rows": rows}


def _load_agent_chat_turns(agent_slug: str, limit: int = 12) -> list[dict]:
    _, internal_name, _ = _resolve_agent_slug(agent_slug)
    return load_agent_conversation_turns(internal_name, limit=limit)


def _build_chat_history_context(agent_slug: str, limit: int = 6) -> list[dict]:
    _, internal_name, _ = _resolve_agent_slug(agent_slug)
    return build_agent_conversation_context(internal_name, limit=limit)


def _attachment_excerpt(filename: str, content: bytes) -> str | None:
    suffix = Path(filename).suffix.lower()
    if suffix not in TEXT_ATTACHMENT_EXTENSIONS:
        return None
    text = content.decode("utf-8", errors="ignore").strip()
    if not text:
        return None
    return text[:12000]


async def _collect_chat_attachments(form, channel: str, agent_slug: str) -> list[dict]:
    attachments: list[dict] = []
    timestamp_dir = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    target_dir = CHAT_UPLOADS_DIR / channel / agent_slug / timestamp_dir

    for key, value in form.multi_items():
        if key != "attachments" or not hasattr(value, "filename") or not value.filename:
            continue

        file_bytes = await value.read()
        safe_name = Path(value.filename).name
        target_dir.mkdir(parents=True, exist_ok=True)
        saved_path = target_dir / safe_name
        saved_path.write_bytes(file_bytes)

        attachments.append(
            {
                "name": safe_name,
                "path": str(saved_path),
                "web_path": "/uploads/" + str(saved_path.relative_to(CHAT_UPLOADS_DIR.parent)).replace("\\", "/"),
                "size_bytes": len(file_bytes),
                "excerpt": _attachment_excerpt(safe_name, file_bytes),
            }
        )

    return attachments


def _load_agent_history_page(agent_slug: str, page: int = 1, status_filter: str | None = None) -> dict:
    runs = _load_agent_runs(agent_slug, limit=200)
    slug = runs["slug"]
    internal_name = runs["internal_name"]
    rows = runs["rows"]
    per_page = 10

    if status_filter:
        rows = [row for row in rows if (row.get("display_status") or row.get("status")) == status_filter]

    total = len(rows)
    start = max(page - 1, 0) * per_page
    end = start + per_page

    return {
        "history": rows[start:end],
        "page": page,
        "total": total,
        "per_page": per_page,
        "agent_name": slug,
        "internal_agent_name": internal_name,
        "filter_status": status_filter,
    }


def _system_prompt_sections(agent: dict) -> list[dict]:
    sections = []
    if agent.get("goal"):
        sections.append({"title": "Missione Operativa", "body": agent["goal"], "accent": True})
    for index, instruction in enumerate(agent.get("instructions", [])[:4], start=1):
        sections.append({"title": f"Linea Guida {index:02d}", "body": instruction, "accent": index == 1 and not sections})
    return sections or [{"title": "Prompt base", "body": "Nessuna istruzione disponibile.", "accent": True}]


def _content_engine_cards() -> list[dict]:
    return [
        {
            "icon": "article",
            "title": "LinkedIn Posts",
            "body": "Focus su hook narrativi e formattazione aerea.",
        },
        {
            "icon": "mail",
            "title": "Newsletters",
            "body": "Approccio editoriale, tono confidenziale.",
        },
        {
            "icon": "shield",
            "title": "Case Studies",
            "body": "Data-driven, focus su problema/soluzione.",
        },
    ]


def _parse_content_engine_request(task_text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in (task_text or "").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip().lower()] = value.strip()
    return parsed


def _content_engine_recent_outputs(rows: list[dict], limit: int = 4) -> list[dict]:
    items: list[dict] = []
    for row in rows:
        if len(items) >= limit:
            break
        task_text = str(row.get("task_text") or row.get("action") or "")
        if not task_text:
            continue
        parsed = _parse_content_engine_request(task_text)
        content_type = parsed.get("tipo contenuto", "Contenuto")
        status = row.get("display_status") or row.get("status") or "draft"
        title_prefix = "Draft" if status in {"draft", "review"} else "Output"
        variants = parsed.get("numero varianti")
        subtitle = f"Generato {_compact_datetime(row.get('created_at'))}"
        if variants:
            subtitle += f" • {variants} varianti"
        items.append(
            {
                "title": f"{title_prefix}: {content_type}",
                "subtitle": subtitle,
                "icon": "description" if "post" in content_type.lower() or "articolo" in content_type.lower() else "alternate_email",
            }
        )
    return items


def _history_status_meta(status: str | None) -> dict[str, str]:
    value = status or "idle"
    if value == "approved":
        return {
            "icon": "check_circle",
            "icon_box": "bg-emerald-100 text-emerald-600",
            "trailing_icon": "download",
            "subtitle": "Approvato",
        }
    if value in {"draft", "review"}:
        return {
            "icon": "schedule",
            "icon_box": "bg-amber-100 text-amber-600",
            "trailing_icon": "visibility",
            "subtitle": "Draft",
        }
    if value in {"error", "rejected"}:
        return {
            "icon": "error",
            "icon_box": "bg-error-container/20 text-error",
            "trailing_icon": "refresh",
            "subtitle": "Fallito",
        }
    return {
        "icon": "history",
        "icon_box": "bg-slate-100 text-slate-500",
        "trailing_icon": "chevron_right",
        "subtitle": value.replace("_", " ").title(),
    }


def _agent_quick_history(rows: list[dict], limit: int = 3) -> list[dict]:
    items = []
    for row in rows[:limit]:
        status = row.get("display_status") or row.get("status")
        meta = _history_status_meta(status)
        title = str(row.get("task_text") or row.get("action") or "Run agente").replace("\n", " ").strip()
        items.append(
            {
                "title": truncate(title, 26),
                "meta_line": f"{_compact_datetime(row.get('created_at'))} • {meta['subtitle']}",
                "icon": meta["icon"],
                "icon_box": meta["icon_box"],
                "trailing_icon": meta["trailing_icon"],
                "muted": status in {"error", "rejected"},
            }
        )
    return items


def _agent_summary(rows: list[dict]) -> dict:
    total = len(rows)
    approved = sum(1 for row in rows if (row.get("display_status") or row.get("status")) == "approved")
    drafts = sum(1 for row in rows if (row.get("display_status") or row.get("status")) in {"draft", "review"})
    errors = sum(1 for row in rows if (row.get("display_status") or row.get("status")) in {"error", "rejected"})

    if approved:
        footer = f"{approved} approvati • {drafts} draft aperti"
    elif drafts:
        footer = f"{drafts} draft aperti • {errors} errori"
    else:
        footer = f"{errors} errori registrati" if errors else "Nessun run registrato"

    return {
        "title": "Totale Run Salvati",
        "value": total,
        "footer": footer,
    }


def _agent_chat_panel_payload(agent_slug: str, chat_error: str | None = None) -> dict:
    agent = _agent_meta(agent_slug)
    return {
        "agent": agent,
        "chat_turns": _load_agent_chat_turns(agent_slug),
        "chat_error": chat_error,
    }


async def _run_agent_background(run_id: str, agent_name: str, task: str) -> None:
    try:
        result = await asyncio.to_thread(run_agent, resolve_agent_name(agent_name), task)
        RUN_REGISTRY[run_id].update(
            {
                "state": "done" if result.get("status") != "error" else "error",
                "result": result,
                "completed_at": datetime.now(UTC).isoformat(),
            }
        )
    except Exception as exc:
        RUN_REGISTRY[run_id].update(
            {
                "state": "error",
                "result": {"status": "error", "error": str(exc), "agent": agent_name},
                "completed_at": datetime.now(UTC).isoformat(),
            }
        )


@router.get("/agents")
async def agents_page(request: Request, selected: str | None = Query(default=None)):
    agents = _load_agents_data()
    selected_name = selected or (agents[0]["name"] if agents else AgentName.ORCHESTRATOR.value)
    selected_agent = next((agent for agent in agents if agent["name"] == selected_name), agents[0] if agents else None)

    context = base_context(
        request,
        active_page="agents",
        page_title="Agenti AI Board",
        page_subtitle="Monitoraggio operativo e accesso rapido alle chat degli agenti del board",
    )
    context.update({"agents": agents, "selected_agent": selected_agent, "run": None})
    return render(request, "agents.html", context)


@router.post("/agents/{agent_name}/run")
async def run_agent_route(request: Request, agent_name: str):
    _, internal_name, _ = _resolve_agent_slug(agent_name)
    form = await request.form()
    task = str(form.get("task", "")).strip()
    if not task:
        task = _build_task_from_form(form)
    if not task:
        raise HTTPException(status_code=400, detail="Task non valido")

    run_id = str(uuid4())
    RUN_REGISTRY[run_id] = {
        "run_id": run_id,
        "agent_name": internal_name,
        "task": task,
        "state": "running",
        "created_at": datetime.now(UTC).isoformat(),
        "result": None,
    }
    asyncio.create_task(_run_agent_background(run_id, internal_name, task))

    context = base_context(request, active_page="agents", page_title="Agenti AI Board")
    context["run"] = RUN_REGISTRY[run_id]
    return render(request, "partials/agent_run_result.html", context)


@router.post("/agents/content_engine/generate")
async def content_engine_generate(request: Request):
    form = await request.form()
    tipo_contenuto = str(form.get("tipo_contenuto", "")).strip()
    obiettivo = str(form.get("obiettivo", "")).strip()
    nicchia_target = str(form.get("nicchia_target", "")).strip()
    caso_studio = str(form.get("caso_studio", "")).strip()
    brief = str(form.get("brief", "")).strip()
    numero_varianti = str(form.get("numero_varianti", "3")).strip() or "3"

    if not brief:
        context = base_context(request, active_page="agents", page_title="Content Engine")
        context["result"] = {"status": "error", "error": "Inserisci un brief prima di generare il contenuto."}
        return render(request, "partials/agent_run_result.html", context)

    task = "\n".join(
        [
            "Genera contenuti scritti pronti da usare.",
            f"Tipo contenuto: {tipo_contenuto or 'Post LinkedIn'}",
            f"Obiettivo: {obiettivo or 'Thought Leadership'}",
            f"Nicchia target: {nicchia_target or 'Generica'}",
            f"Caso studio: {caso_studio or 'Nessuno'}",
            f"Numero varianti: {numero_varianti}",
            f"Brief: {brief}",
            "Richiesta finale: produci testi completi, già scritti, concreti, senza placeholder e senza spiegazioni introduttive.",
        ]
    )

    generation_context = {
        "interface": "dashboard_content_engine",
        "channel": "content_engine_generator",
        "generation_request": {
            "tipo_contenuto": tipo_contenuto,
            "obiettivo": obiettivo,
            "nicchia_target": nicchia_target,
            "caso_studio": caso_studio,
            "numero_varianti": numero_varianti,
        },
    }
    result = await asyncio.to_thread(run_agent, AgentName.CONTENT_ENGINE, task, generation_context)

    context = base_context(request, active_page="agents", page_title="Content Engine")
    context["result"] = result
    return render(request, "partials/agent_run_result.html", context)


@router.get("/agents/{agent_name}/status")
async def agent_run_status(request: Request, agent_name: str, run_id: str):
    _, internal_name, _ = _resolve_agent_slug(agent_name)
    run = RUN_REGISTRY.get(run_id)
    if not run or run.get("agent_name") != internal_name:
        raise HTTPException(status_code=404, detail="Run non trovato")

    context = base_context(request, active_page="agents", page_title="Agenti AI Board")
    context["run"] = run
    return render(request, "partials/agent_run_result.html", context)


@router.get("/agents/{agent_name}/history")
async def agent_history_partial(request: Request, agent_name: str, page: int = 1, status: str | None = None):
    context = base_context(request, active_page="agents", page_title="Dettaglio Agente")
    context.update(_load_agent_history_page(agent_name, page=page, status_filter=status))
    return render(request, "partials/agent_history.html", context)


@router.get("/agents/{agent_name}/chat")
async def agent_chat_partial(request: Request, agent_name: str):
    context = base_context(request, active_page="agents", page_title="Chat Agente")
    context.update(_agent_chat_panel_payload(agent_name))
    return render(request, "partials/agent_chat_panel.html", context)


@router.post("/agents/{agent_name}/chat")
async def agent_chat_send(request: Request, agent_name: str):
    slug, _, agent_enum = _resolve_agent_slug(agent_name)
    form = await request.form()
    message = str(form.get("message", "")).strip()
    attachments = await _collect_chat_attachments(form, channel="agenti", agent_slug=slug)

    context = base_context(request, active_page="agents", page_title="Chat Agente")
    if not message and not attachments:
        context.update(_agent_chat_panel_payload(agent_name, chat_error="Scrivi un messaggio prima di inviare."))
        return render(request, "partials/agent_chat_panel.html", context)

    task = message or "Analizza gli allegati caricati e rispondi in modo utile e operativo."
    if attachments:
        task += "\n\n## Allegati caricati\n" + "\n".join(
            f"- {item['name']} ({item['size_bytes']} byte)" for item in attachments
        )

    chat_context = {
        "chat_history": _build_chat_history_context(agent_name, limit=12),
        "interface": "dashboard_agent_chat",
        "channel": "agent_detail_chat",
        "agent_slug": slug,
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
            "content_type": "agent_chat",
            "requested_by": "dashboard_agent_chat",
        },
    }
    result = await asyncio.to_thread(run_agent, agent_enum, task, chat_context)
    chat_error = result.get("error") if result.get("status") == "error" else None
    context.update(_agent_chat_panel_payload(agent_name, chat_error=chat_error))
    return render(request, "partials/agent_chat_panel.html", context)


@router.get("/agents/{agent_name}")
async def agent_detail(request: Request, agent_name: str):
    agent = _agent_meta(agent_name)
    pending = _load_agent_pending(agent["internal_name"])
    history = _load_agent_history_page(agent_name, page=1)
    runs = _load_agent_runs(agent_name, limit=200)
    quick_history = _agent_quick_history(runs["rows"])
    summary = _agent_summary(runs["rows"])

    context = base_context(
        request,
        active_page="agents",
        page_title=agent["display_name"],
        page_subtitle=agent["role"],
    )
    context.update(
        {
            "agent": agent,
            "pending": pending,
            "pending_count": len(pending),
            "history": history["history"],
            "history_total": history["total"],
            "chat_turns": _load_agent_chat_turns(agent_name),
            "quick_history": quick_history,
            "agent_summary": summary,
            "prompt_sections": _system_prompt_sections(agent),
            "content_engine_cards": _content_engine_cards() if agent["internal_name"] == AgentName.CONTENT_ENGINE.value else [],
            "content_engine_recent_outputs": _content_engine_recent_outputs(runs["rows"]) if agent["internal_name"] == AgentName.CONTENT_ENGINE.value else [],
            "suppress_page_header": True,
        }
    )
    return render(request, "agent_detail.html", context)
