"""Typed payloads exchanged between services and controllers.

`TypedDict` is used rather than `dataclass` so the payloads remain
directly usable as Jinja template contexts without conversion.
"""

from __future__ import annotations

from typing import Any, TypedDict


class PipelineRow(TypedDict):
    key: str
    label: str
    count: int
    border_class: str
    is_won: bool


class ActivityItem(TypedDict, total=False):
    approval_id: str | None
    agent: str | None
    status: str | None
    title: str
    preview: str
    created_at: str | None
    time_ago: str
    border_class: str
    accent_class: str
    icon: str
    emoji: str


class HomeData(TypedDict):
    today_label: str
    pending_approvals: int
    pending_created_today: int
    active_agents_today: int
    active_agents_delta: int
    pipeline_leads: int
    pipeline_created_week: int
    tasks_done_week: int
    tasks_done_change_pct: int
    activity_feed: list[ActivityItem]
    pipeline_summary: dict[str, int]
    pipeline_rows: list[PipelineRow]


class AgentRow(TypedDict):
    name: str
    display_name: str
    role: str
    provider: str
    last_run: str | None
    last_output_preview: str
    status: str
    detail_slug: str


class AgentMeta(TypedDict):
    slug: str
    name: str
    internal_name: str
    display_name: str
    role: str
    goal: str
    instructions: list[str]
    provider: str
    model: str
    fallback_provider: str
    fallback_model: str
    status: str
    status_meta: dict[str, str]


class AgentHistoryPage(TypedDict):
    history: list[dict[str, Any]]
    page: int
    total: int
    per_page: int
    agent_name: str
    internal_agent_name: str
    filter_status: str | None
