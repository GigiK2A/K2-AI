"""Agents use-case layer.

Aggregates metadata, status, history and chat helpers used by the agents
dashboard. The controller layer only does HTTP parsing + template rendering.
Ported from `interfaces/dashboard/routes/agents.py`.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from core import notion_board
from core.config import settings
from core.conversation import (
    build_agent_conversation_context,
    load_agent_conversation_turns,
)
from core.orchestrator import (
    AGENT_REGISTRY,
    related_agent_names,
    resolve_agent_name,
    run_agent,
)
from core.text import truncate_text
from db.models import AgentName, LLMProvider
from repositories import AgentLogsRepository, ApprovalsRepository
from services._time import compact_datetime, parse_datetime
from services.dto import AgentHistoryPage, AgentMeta, AgentRow

URL_SLUG_ALIASES: dict[str, str] = {
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

CHAT_UPLOADS_DIR = Path(__file__).resolve().parents[1] / "uploads" / "chat"
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

# Shared, process-local registry of running agent invocations.
RUN_REGISTRY: dict[str, dict[str, Any]] = {}


def _detail_slug(agent_name: str) -> str:
    return URL_SLUG_ALIASES.get(agent_name, agent_name)


def resolve_agent_slug(slug: str) -> tuple[str, str, AgentName]:
    internal_name = URL_SLUG_ALIASES.get(slug, slug)
    try:
        agent_enum = resolve_agent_name(AgentName(internal_name))
    except ValueError as exc:
        raise HTTPException(
            status_code=404, detail="Agente non trovato"
        ) from exc
    return _detail_slug(agent_enum.value), agent_enum.value, agent_enum


class AgentsService:
    def __init__(
        self,
        approvals: ApprovalsRepository | None = None,
        agent_logs: AgentLogsRepository | None = None,
    ) -> None:
        self._approvals = approvals or ApprovalsRepository()
        self._logs = agent_logs or AgentLogsRepository()

    # -------------------------------------------------------------- meta/list
    def list_agents(self) -> list[AgentRow]:
        logs = self._logs.list_summary(limit=200)
        latest_by_agent: dict[str, dict[str, Any]] = {}
        for row in logs:
            try:
                canonical = resolve_agent_name(row.get("agent")).value
            except Exception:
                canonical = row.get("agent")
            latest_by_agent.setdefault(canonical, row)

        rows: list[AgentRow] = []
        for name, cls in AGENT_REGISTRY.items():
            latest = latest_by_agent.get(name.value, {})
            provider = getattr(cls, "provider", LLMProvider.OPENAI)
            rows.append(
                {
                    "name": name.value,
                    "display_name": self._display_name(
                        _detail_slug(name.value)
                    ),
                    "role": getattr(cls, "role", ""),
                    "provider": provider.value
                    if isinstance(provider, LLMProvider)
                    else str(provider),
                    "last_run": latest.get("created_at"),
                    "last_output_preview": truncate_text(
                        latest.get("output_summary") or "", 80
                    ),
                    "status": self.agent_status(name.value),
                    "detail_slug": _detail_slug(name.value),
                }
            )
        return rows

    def agent_meta(self, agent_slug: str) -> AgentMeta:
        slug, internal_name, agent_enum = resolve_agent_slug(agent_slug)
        agent_class = AGENT_REGISTRY.get(agent_enum)
        provider = getattr(agent_class, "provider", LLMProvider.OPENAI)
        model = getattr(agent_class, "model", None)
        default_model = (
            "claude-sonnet-4-6"
            if provider == LLMProvider.ANTHROPIC
            else "gpt-4o"
        )
        fallback_provider = getattr(agent_class, "fallback_provider", None)
        if not isinstance(fallback_provider, LLMProvider):
            fallback_provider = (
                LLMProvider.OPENAI
                if provider == LLMProvider.ANTHROPIC
                else LLMProvider.ANTHROPIC
            )
        fallback_model = getattr(agent_class, "fallback_model", None) or (
            settings.default_anthropic_model
            if fallback_provider == LLMProvider.ANTHROPIC
            else settings.default_openai_model
        )
        status = self.agent_status(internal_name)
        return {
            "slug": slug,
            "name": slug,
            "internal_name": internal_name,
            "display_name": self._display_name(slug),
            "role": getattr(agent_class, "role", ""),
            "goal": getattr(agent_class, "goal", ""),
            "instructions": list(getattr(agent_class, "instructions", [])),
            "provider": provider.value
            if hasattr(provider, "value")
            else str(provider),
            "model": model or default_model,
            "fallback_provider": fallback_provider.value,
            "fallback_model": fallback_model,
            "status": status,
            "status_meta": self._status_meta(status),
        }

    # ---------------------------------------------------------------- status
    def agent_status(self, agent_name: str) -> str:
        canonical_name = resolve_agent_name(agent_name).value
        if any(
            item.get("agent_name") == canonical_name
            and item.get("state") == "running"
            for item in RUN_REGISTRY.values()
        ):
            return "running"

        recent_cutoff = datetime.now(UTC) - timedelta(hours=2)
        related_names = {
            item.value for item in related_agent_names(canonical_name)
        }

        if notion_board.notion_enabled():
            candidates = self._approvals.list_pending_for_agents(related_names)
            recent_draft = [
                item
                for item in candidates
                if (
                    parse_datetime(item.get("created_at"))
                    or datetime.min.replace(tzinfo=UTC)
                )
                >= recent_cutoff
            ]
            return "draft_ready" if recent_draft else "idle"

        recent_draft = self._approvals.recent_draft_for_agents(
            related_names, recent_cutoff.isoformat()
        )
        return "draft_ready" if recent_draft else "idle"

    # --------------------------------------------------------- pending/runs
    def list_agent_pending(self, agent_name: str) -> list[dict[str, Any]]:
        related_names = {
            item.value for item in related_agent_names(agent_name)
        }
        return self._approvals.list_pending_for_agents(related_names)

    def load_agent_runs(
        self, agent_slug: str, limit: int = 200
    ) -> dict[str, Any]:
        slug, internal_name, _ = resolve_agent_slug(agent_slug)
        related_names = {
            item.value for item in related_agent_names(internal_name)
        }

        logs = self._logs.list_for_agents(related_names, limit=limit)

        if notion_board.notion_enabled():
            approvals = self._approvals.list_for_agents(related_names)
        else:
            task_ids = [row.get("task_id") for row in logs if row.get("task_id")]
            approvals = self._approvals.list_for_task_ids(task_ids)

        approval_map = {
            row.get("task_id"): row for row in approvals if row.get("task_id")
        }
        rows: list[dict[str, Any]] = []
        for log in logs:
            approval = approval_map.get(log.get("task_id"))
            full_content = (
                approval.get("full_content") if isinstance(approval, dict) else {}
            )
            task_text = ""
            output_text = ""
            context_data: Any = None
            if isinstance(full_content, dict):
                task_text = str(full_content.get("task") or "")
                output_text = str(full_content.get("output") or "")
                context_data = full_content.get("context")
            if not task_text:
                task_text = str(log.get("action") or "")
            if not output_text:
                output_text = str(log.get("output_summary") or "")
            rows.append(
                {
                    **log,
                    "display_status": approval.get("status")
                    if approval
                    else log.get("status"),
                    "approval": approval,
                    "approval_id": approval.get("id") if approval else None,
                    "task_text": task_text,
                    "output_text": output_text,
                    "context_data": context_data,
                }
            )

        return {"slug": slug, "internal_name": internal_name, "rows": rows}

    def load_history_page(
        self,
        agent_slug: str,
        page: int = 1,
        status_filter: str | None = None,
    ) -> AgentHistoryPage:
        runs = self.load_agent_runs(agent_slug, limit=200)
        rows = runs["rows"]
        per_page = 10
        if status_filter:
            rows = [
                row
                for row in rows
                if (row.get("display_status") or row.get("status"))
                == status_filter
            ]
        total = len(rows)
        start = max(page - 1, 0) * per_page
        end = start + per_page
        return {
            "history": rows[start:end],
            "page": page,
            "total": total,
            "per_page": per_page,
            "agent_name": runs["slug"],
            "internal_agent_name": runs["internal_name"],
            "filter_status": status_filter,
        }

    # ----------------------------------------------------------------- chat
    def load_chat_turns(
        self, agent_slug: str, limit: int = 12
    ) -> list[dict[str, Any]]:
        _, internal_name, _ = resolve_agent_slug(agent_slug)
        return load_agent_conversation_turns(internal_name, limit=limit)

    def build_chat_history_context(
        self, agent_slug: str, limit: int = 6
    ) -> list[dict[str, Any]]:
        _, internal_name, _ = resolve_agent_slug(agent_slug)
        return build_agent_conversation_context(internal_name, limit=limit)

    def chat_panel_payload(
        self, agent_slug: str, chat_error: str | None = None
    ) -> dict[str, Any]:
        return {
            "agent": self.agent_meta(agent_slug),
            "chat_turns": self.load_chat_turns(agent_slug),
            "chat_error": chat_error,
        }

    async def collect_chat_attachments(
        self, form: Any, channel: str, agent_slug: str
    ) -> list[dict[str, Any]]:
        attachments: list[dict[str, Any]] = []
        timestamp_dir = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        target_dir = CHAT_UPLOADS_DIR / channel / agent_slug / timestamp_dir

        for key, value in form.multi_items():
            if (
                key != "attachments"
                or not hasattr(value, "filename")
                or not value.filename
            ):
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
                    "web_path": "/uploads/"
                    + str(
                        saved_path.relative_to(CHAT_UPLOADS_DIR.parent)
                    ).replace("\\", "/"),
                    "size_bytes": len(file_bytes),
                    "excerpt": self._attachment_excerpt(safe_name, file_bytes),
                }
            )
        return attachments

    # --------------------------------------------------------------- actions
    def start_run(self, agent_slug: str, task: str) -> dict[str, Any]:
        _, internal_name, _ = resolve_agent_slug(agent_slug)
        run_id = str(uuid4())
        RUN_REGISTRY[run_id] = {
            "run_id": run_id,
            "agent_name": internal_name,
            "task": task,
            "state": "running",
            "created_at": datetime.now(UTC).isoformat(),
            "result": None,
        }
        asyncio.create_task(self._run_agent_background(run_id, internal_name, task))
        return RUN_REGISTRY[run_id]

    def get_run(self, agent_slug: str, run_id: str) -> dict[str, Any]:
        _, internal_name, _ = resolve_agent_slug(agent_slug)
        run = RUN_REGISTRY.get(run_id)
        if not run or run.get("agent_name") != internal_name:
            raise HTTPException(status_code=404, detail="Run non trovato")
        return run

    async def run_content_engine(
        self,
        *,
        tipo_contenuto: str,
        obiettivo: str,
        nicchia_target: str,
        caso_studio: str,
        brief: str,
        numero_varianti: str,
    ) -> dict[str, Any]:
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
        return await asyncio.to_thread(
            run_agent, AgentName.CONTENT_ENGINE, task, generation_context
        )

    async def send_agent_chat(
        self,
        *,
        agent_slug: str,
        message: str,
        attachments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        slug, _, agent_enum = resolve_agent_slug(agent_slug)
        task = (
            message
            or "Analizza gli allegati caricati e rispondi in modo utile e operativo."
        )
        if attachments:
            task += "\n\n## Allegati caricati\n" + "\n".join(
                f"- {item['name']} ({item['size_bytes']} byte)"
                for item in attachments
            )

        chat_context = {
            "chat_history": self.build_chat_history_context(
                agent_slug, limit=12
            ),
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
        return await asyncio.to_thread(
            run_agent, agent_enum, task, chat_context
        )

    # ----------------------------------------------------------- detail page
    def build_detail_context(self, agent_slug: str) -> dict[str, Any]:
        agent = self.agent_meta(agent_slug)
        pending = self.list_agent_pending(agent["internal_name"])
        history = self.load_history_page(agent_slug, page=1)
        runs = self.load_agent_runs(agent_slug, limit=200)
        quick_history = self.agent_quick_history(runs["rows"])
        summary = self.agent_summary(runs["rows"])
        return {
            "agent": agent,
            "pending": pending,
            "pending_count": len(pending),
            "history": history["history"],
            "history_total": history["total"],
            "chat_turns": self.load_chat_turns(agent_slug),
            "quick_history": quick_history,
            "agent_summary": summary,
            "prompt_sections": self.system_prompt_sections(agent),
            "content_engine_cards": (
                self.content_engine_cards()
                if agent["internal_name"] == AgentName.CONTENT_ENGINE.value
                else []
            ),
            "content_engine_recent_outputs": (
                self.content_engine_recent_outputs(runs["rows"])
                if agent["internal_name"] == AgentName.CONTENT_ENGINE.value
                else []
            ),
            "suppress_page_header": True,
        }

    # ------------------------------------------------------------ utilities
    @staticmethod
    def detail_slug(agent_name: str) -> str:
        return _detail_slug(agent_name)

    @staticmethod
    def build_task_from_form(form: Any) -> str:
        parts: list[str] = []
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
            parts.append(f"{label}: {text}")
        return "\n".join(parts)

    @staticmethod
    def system_prompt_sections(agent: AgentMeta) -> list[dict[str, Any]]:
        sections: list[dict[str, Any]] = []
        if agent.get("goal"):
            sections.append(
                {
                    "title": "Missione Operativa",
                    "body": agent["goal"],
                    "accent": True,
                }
            )
        for index, instruction in enumerate(
            agent.get("instructions", [])[:4], start=1
        ):
            sections.append(
                {
                    "title": f"Linea Guida {index:02d}",
                    "body": instruction,
                    "accent": index == 1 and not sections,
                }
            )
        return sections or [
            {
                "title": "Prompt base",
                "body": "Nessuna istruzione disponibile.",
                "accent": True,
            }
        ]

    @staticmethod
    def content_engine_cards() -> list[dict[str, str]]:
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

    @classmethod
    def content_engine_recent_outputs(
        cls, rows: list[dict[str, Any]], limit: int = 4
    ) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        for row in rows:
            if len(items) >= limit:
                break
            task_text = str(row.get("task_text") or row.get("action") or "")
            if not task_text:
                continue
            parsed = cls._parse_content_engine_request(task_text)
            content_type = parsed.get("tipo contenuto", "Contenuto")
            status = row.get("display_status") or row.get("status") or "draft"
            title_prefix = (
                "Draft" if status in {"draft", "review"} else "Output"
            )
            variants = parsed.get("numero varianti")
            subtitle = f"Generato {compact_datetime(row.get('created_at'))}"
            if variants:
                subtitle += f" • {variants} varianti"
            icon = (
                "description"
                if "post" in content_type.lower()
                or "articolo" in content_type.lower()
                else "alternate_email"
            )
            items.append(
                {
                    "title": f"{title_prefix}: {content_type}",
                    "subtitle": subtitle,
                    "icon": icon,
                }
            )
        return items

    @classmethod
    def agent_quick_history(
        cls, rows: list[dict[str, Any]], limit: int = 3
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for row in rows[:limit]:
            status = row.get("display_status") or row.get("status")
            meta = cls._history_status_meta(status)
            title = (
                str(row.get("task_text") or row.get("action") or "Run agente")
                .replace("\n", " ")
                .strip()
            )
            items.append(
                {
                    "title": truncate_text(title, 26),
                    "meta_line": f"{compact_datetime(row.get('created_at'))} • {meta['subtitle']}",
                    "icon": meta["icon"],
                    "icon_box": meta["icon_box"],
                    "trailing_icon": meta["trailing_icon"],
                    "muted": status in {"error", "rejected"},
                }
            )
        return items

    @staticmethod
    def agent_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(rows)
        approved = sum(
            1
            for row in rows
            if (row.get("display_status") or row.get("status")) == "approved"
        )
        drafts = sum(
            1
            for row in rows
            if (row.get("display_status") or row.get("status"))
            in {"draft", "review"}
        )
        errors = sum(
            1
            for row in rows
            if (row.get("display_status") or row.get("status"))
            in {"error", "rejected"}
        )
        if approved:
            footer = f"{approved} approvati • {drafts} draft aperti"
        elif drafts:
            footer = f"{drafts} draft aperti • {errors} errori"
        else:
            footer = (
                f"{errors} errori registrati"
                if errors
                else "Nessun run registrato"
            )
        return {"title": "Totale Run Salvati", "value": total, "footer": footer}

    # -------------------------------------------------------------- internal
    @staticmethod
    def _display_name(agent_slug: str) -> str:
        return agent_slug.replace("_", " ").title()

    @staticmethod
    def _status_meta(status: str) -> dict[str, str]:
        if status == "draft_ready":
            return {
                "label": "Draft pronto",
                "class": "bg-amber-100 text-amber-700",
            }
        if status == "running":
            return {
                "label": "In esecuzione",
                "class": "bg-sky-100 text-sky-700",
            }
        return {
            "label": "Inattivo",
            "class": "bg-surface-container-high text-on-surface-variant",
        }

    @staticmethod
    def _parse_content_engine_request(task_text: str) -> dict[str, str]:
        parsed: dict[str, str] = {}
        for line in (task_text or "").splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            parsed[key.strip().lower()] = value.strip()
        return parsed

    @staticmethod
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

    @staticmethod
    def _attachment_excerpt(filename: str, content: bytes) -> str | None:
        suffix = Path(filename).suffix.lower()
        if suffix not in TEXT_ATTACHMENT_EXTENSIONS:
            return None
        text = content.decode("utf-8", errors="ignore").strip()
        if not text:
            return None
        return text[:12000]

    @staticmethod
    async def _run_agent_background(
        run_id: str, agent_name: str, task: str
    ) -> None:
        try:
            result = await asyncio.to_thread(
                run_agent, resolve_agent_name(agent_name), task
            )
            RUN_REGISTRY[run_id].update(
                {
                    "state": "done"
                    if result.get("status") != "error"
                    else "error",
                    "result": result,
                    "completed_at": datetime.now(UTC).isoformat(),
                }
            )
        except Exception as exc:
            RUN_REGISTRY[run_id].update(
                {
                    "state": "error",
                    "result": {
                        "status": "error",
                        "error": str(exc),
                        "agent": agent_name,
                    },
                    "completed_at": datetime.now(UTC).isoformat(),
                }
            )
