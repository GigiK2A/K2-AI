"""Legacy shim — agents logic moved to `controllers.agents_controller` and
`services.agents_service`.

Kept as a backward-compat facade: re-exports the router and provides the
old private helpers (`_agent_meta`, `_load_agents_data`, ...) that other
route modules still consume. New code should import from
`controllers` / `services` directly.
"""

from __future__ import annotations

from controllers.agents_controller import router  # noqa: F401
from services.agents_service import (
    AgentsService,
    RUN_REGISTRY,  # noqa: F401 (legacy re-export)
    resolve_agent_slug as _resolve_agent_slug,  # noqa: F401
)

_service = AgentsService()


def _load_agents_data() -> list[dict]:
    return _service.list_agents()


def _agent_meta(agent_slug: str) -> dict:
    return _service.agent_meta(agent_slug)


def _load_agent_history_page(
    agent_slug: str, page: int = 1, status_filter: str | None = None
) -> dict:
    return _service.load_history_page(
        agent_slug, page=page, status_filter=status_filter
    )


def _load_agent_chat_turns(agent_slug: str, limit: int = 12) -> list[dict]:
    return _service.load_chat_turns(agent_slug, limit=limit)


def _build_chat_history_context(agent_slug: str, limit: int = 6) -> list[dict]:
    return _service.build_chat_history_context(agent_slug, limit=limit)


def _agent_chat_panel_payload(
    agent_slug: str, chat_error: str | None = None
) -> dict:
    return _service.chat_panel_payload(agent_slug, chat_error=chat_error)


async def _collect_chat_attachments(form, channel: str, agent_slug: str):
    return await _service.collect_chat_attachments(
        form, channel=channel, agent_slug=agent_slug
    )


__all__ = [
    "router",
    "RUN_REGISTRY",
    "_agent_meta",
    "_agent_chat_panel_payload",
    "_build_chat_history_context",
    "_collect_chat_attachments",
    "_load_agents_data",
    "_load_agent_chat_turns",
    "_load_agent_history_page",
    "_resolve_agent_slug",
]
