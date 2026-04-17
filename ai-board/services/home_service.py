"""Home use-case: aggregate KPIs, pipeline and activity feed for the
dashboard landing page.

Extracted from `interfaces/dashboard/routes/home.py` (see `_load_home_data`
in git history). Business logic lives here; the controller only builds the
Jinja context and renders.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from core import notion_board
from core.orchestrator import resolve_agent_name
from repositories import (
    AgentLogsRepository,
    ApprovalsRepository,
    PipelineRepository,
    TasksRepository,
)
from services._time import format_home_date, parse_datetime, relative_time_it
from services.dto import ActivityItem, HomeData, PipelineRow

PIPELINE_ORDER: list[tuple[str, str, str, bool]] = [
    ("identified", "Identificazione", "border-slate-300", False),
    ("qualified", "Qualificazione", "border-slate-400", False),
    ("contacted", "Contatto", "border-indigo-300", False),
    ("call_scheduled", "Chiamata", "border-indigo-400", False),
    ("proposal_sent", "Proposta", "border-indigo-500", False),
    ("won", "Chiuso (Vinto)", "", True),
]

ACTIVITY_STYLE_MAP: dict[str, dict[str, str]] = {
    "content_engine": {
        "border": "border-rose-400",
        "accent": "bg-rose-50 text-rose-500",
        "icon": "edit_square",
        "emoji": "✍️",
    },
    "sales_enablement": {
        "border": "border-blue-400",
        "accent": "bg-blue-50 text-blue-500",
        "icon": "campaign",
        "emoji": "📈",
    },
    "chief_of_staff": {
        "border": "border-indigo-400",
        "accent": "bg-indigo-50 text-indigo-500",
        "icon": "hub",
        "emoji": "⚡",
    },
    "solution_architect": {
        "border": "border-violet-400",
        "accent": "bg-violet-50 text-violet-500",
        "icon": "architecture",
        "emoji": "🧩",
    },
    "finance_kpi": {
        "border": "border-emerald-400",
        "accent": "bg-emerald-50 text-emerald-500",
        "icon": "bar_chart",
        "emoji": "📊",
    },
}


class HomeService:
    def __init__(
        self,
        approvals: ApprovalsRepository | None = None,
        agent_logs: AgentLogsRepository | None = None,
        pipeline: PipelineRepository | None = None,
        tasks: TasksRepository | None = None,
    ) -> None:
        self._approvals = approvals or ApprovalsRepository()
        self._logs = agent_logs or AgentLogsRepository()
        self._pipeline = pipeline or PipelineRepository()
        self._tasks = tasks or TasksRepository()

    # ------------------------------------------------------------------ public
    def load_home_data(self) -> HomeData:
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        week_start = now - timedelta(days=7)
        previous_week_start = now - timedelta(days=14)

        approvals_pending = self._approvals.list_pending()

        if notion_board.notion_enabled():
            all_logs = self._logs.list_recent(limit=500)
            logs_today = [
                row
                for row in all_logs
                if (parse_datetime(row.get("created_at")) or now) >= today_start
            ]
            logs_yesterday = [
                row
                for row in all_logs
                if yesterday_start
                <= (parse_datetime(row.get("created_at")) or now)
                < today_start
            ]
            logs = all_logs[:50]
            approvals = self._approvals.list_recent(limit=20)
            approved_recent: list[dict[str, Any]] = []
        else:
            logs_today = self._logs.list_since(today_start.isoformat())
            logs_yesterday = self._logs.list_between(
                yesterday_start.isoformat(), today_start.isoformat()
            )
            logs = self._logs.list_recent(limit=50)
            approvals = self._approvals.list_recent(limit=20)
            approved_recent = self._approvals.list_approved()

        leads = self._pipeline.list_leads()
        tasks = self._tasks.list_tasks()

        approved_count, approved_previous_week = self._count_completed(
            tasks,
            approved_recent,
            now=now,
            week_start=week_start,
            previous_week_start=previous_week_start,
        )

        pipeline_summary = Counter(
            lead.get("status", "unknown") for lead in leads
        )
        pending_created_today = sum(
            1
            for item in approvals_pending
            if (parse_datetime(item.get("created_at")) or now) >= today_start
        )
        leads_created_week = sum(
            1
            for lead in leads
            if (parse_datetime(lead.get("created_at")) or now) >= week_start
        )
        active_agents_today = self._unique_active_agents(logs_today)
        active_agents_yesterday = self._unique_active_agents(logs_yesterday)
        active_agents_delta = active_agents_today - active_agents_yesterday
        task_completion_change = self._task_completion_change(
            approved_count, approved_previous_week
        )

        pipeline_rows: list[PipelineRow] = [
            {
                "key": key,
                "label": label,
                "count": pipeline_summary.get(key, 0),
                "border_class": border_class,
                "is_won": is_won,
            }
            for key, label, border_class, is_won in PIPELINE_ORDER
        ]
        activity_feed = self._build_activity_feed(approvals, logs, now)

        return {
            "today_label": format_home_date(now),
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

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _task_completion_change(current: int, previous: int) -> int:
        if previous <= 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100)

    @staticmethod
    def _unique_active_agents(rows: list[dict[str, Any]]) -> int:
        return len(
            {
                resolve_agent_name(row.get("agent")).value
                if row.get("agent")
                else None
                for row in rows
                if row.get("agent")
            }
        )

    @staticmethod
    def _count_completed(
        tasks: list[dict[str, Any]],
        approved_recent: list[dict[str, Any]],
        *,
        now: datetime,
        week_start: datetime,
        previous_week_start: datetime,
    ) -> tuple[int, int]:
        if notion_board.notion_enabled():
            completed_statuses = {"approved", "done"}
            approved_count = sum(
                1
                for task in tasks
                if task.get("status") in completed_statuses
                and (
                    parse_datetime(task.get("updated_at"))
                    or parse_datetime(task.get("created_at"))
                    or now
                )
                >= week_start
            )
            approved_previous_week = sum(
                1
                for task in tasks
                if task.get("status") in completed_statuses
                and previous_week_start
                <= (
                    parse_datetime(task.get("updated_at"))
                    or parse_datetime(task.get("created_at"))
                    or now
                )
                < week_start
            )
            return approved_count, approved_previous_week

        approved_count = 0
        approved_previous_week = 0
        for approval in approved_recent:
            reviewed_at = parse_datetime(
                approval.get("reviewed_at")
            ) or parse_datetime(approval.get("created_at"))
            if reviewed_at and reviewed_at >= week_start:
                approved_count += 1
            elif reviewed_at and reviewed_at >= previous_week_start:
                approved_previous_week += 1
        return approved_count, approved_previous_week

    @staticmethod
    def _activity_style(
        agent: str | None, status: str | None
    ) -> dict[str, str]:
        resolved = agent
        if agent:
            try:
                resolved = resolve_agent_name(agent).value
            except Exception:
                resolved = agent
        if resolved in ACTIVITY_STYLE_MAP:
            return ACTIVITY_STYLE_MAP[resolved]
        if status in {"approved", "done"}:
            return {
                "border": "border-emerald-400",
                "accent": "bg-emerald-50 text-emerald-500",
                "icon": "task_alt",
                "emoji": "✓",
            }
        if status in {"rejected", "error"}:
            return {
                "border": "border-rose-400",
                "accent": "bg-rose-50 text-rose-500",
                "icon": "cancel",
                "emoji": "!",
            }
        return {
            "border": "border-indigo-400",
            "accent": "bg-indigo-50 text-indigo-500",
            "icon": "draft",
            "emoji": "•",
        }

    @classmethod
    def _build_activity_feed(
        cls,
        approvals: list[dict[str, Any]],
        logs: list[dict[str, Any]],
        now: datetime,
    ) -> list[ActivityItem]:
        logs_by_task = {
            row.get("task_id"): row for row in logs if row.get("task_id")
        }
        approval_task_ids = {
            row.get("task_id") for row in approvals if row.get("task_id")
        }
        events: list[ActivityItem] = []

        for approval in approvals:
            linked_log = logs_by_task.get(approval.get("task_id"))
            style = cls._activity_style(
                approval.get("agent"), approval.get("status")
            )
            title = (linked_log or {}).get("action") or "Draft generato"
            preview = (
                approval.get("content_preview")
                or (linked_log or {}).get("output_summary")
                or "Nessuna anteprima disponibile."
            )
            events.append(
                {
                    "approval_id": approval.get("id"),
                    "agent": approval.get("agent"),
                    "status": approval.get("status"),
                    "title": title,
                    "preview": preview,
                    "created_at": approval.get("created_at"),
                    "time_ago": relative_time_it(
                        approval.get("created_at"), now
                    ),
                    "border_class": style["border"],
                    "accent_class": style["accent"],
                    "icon": style["icon"],
                    "emoji": style["emoji"],
                }
            )

        for row in logs:
            if row.get("task_id") and row.get("task_id") in approval_task_ids:
                continue
            style = cls._activity_style(row.get("agent"), row.get("status"))
            events.append(
                {
                    "approval_id": None,
                    "agent": row.get("agent"),
                    "status": row.get("status"),
                    "title": row.get("action") or "Attività agente",
                    "preview": row.get("output_summary")
                    or "Attività registrata nel board.",
                    "created_at": row.get("created_at"),
                    "time_ago": relative_time_it(row.get("created_at"), now),
                    "border_class": style["border"],
                    "accent_class": style["accent"],
                    "icon": style["icon"],
                    "emoji": style["emoji"],
                }
            )

        events.sort(
            key=lambda item: item.get("created_at") or "", reverse=True
        )
        return events[:4]
