"""Agent logs repository."""

from __future__ import annotations

from typing import Any, Iterable

from core import notion_board
from db.client import get_service_client
from repositories._common import safely


class AgentLogsRepository:
    """Reads from `agent_logs` table / Notion "Log AI" DB."""

    def list_recent(self, limit: int = 500) -> list[dict[str, Any]]:
        if notion_board.notion_enabled():
            return safely(
                [],
                lambda: notion_board.list_agent_logs(limit=limit),
                "Errore lettura log Notion",
            )
        client = get_service_client()
        return safely(
            [],
            lambda: client.table("agent_logs")
            .select(
                "id,task_id,agent,action,status,llm_model,created_at,output_summary"
            )
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
            .data
            or [],
            "Errore lettura attività log",
        )

    def list_since(self, since_iso: str) -> list[dict[str, Any]]:
        """Supabase path — agent+created_at only, used for today/yesterday splits."""
        if notion_board.notion_enabled():
            return []
        client = get_service_client()
        return safely(
            [],
            lambda: client.table("agent_logs")
            .select("agent,created_at")
            .gte("created_at", since_iso)
            .execute()
            .data
            or [],
            "Errore lettura log intervallo",
        )

    def list_between(
        self, start_iso: str, end_iso: str
    ) -> list[dict[str, Any]]:
        if notion_board.notion_enabled():
            return []
        client = get_service_client()
        return safely(
            [],
            lambda: client.table("agent_logs")
            .select("agent,created_at")
            .gte("created_at", start_iso)
            .lt("created_at", end_iso)
            .execute()
            .data
            or [],
            "Errore lettura log intervallo",
        )

    def list_summary(self, limit: int = 200) -> list[dict[str, Any]]:
        """Lightweight projection used by agents list view."""
        if notion_board.notion_enabled():
            return safely(
                [],
                lambda: notion_board.list_agent_logs(limit=limit),
                "Errore lettura log agenti Notion",
            )
        client = get_service_client()
        return safely(
            [],
            lambda: (
                client.table("agent_logs")
                .select("agent,created_at,output_summary,status")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
                .data
                or []
            ),
            "Errore lettura log agenti",
        )

    def list_for_agents(
        self, related_names: Iterable[str], limit: int = 200
    ) -> list[dict[str, Any]]:
        names_set = set(related_names)
        if notion_board.notion_enabled():
            return safely(
                [],
                lambda: [
                    row
                    for row in notion_board.list_agent_logs(limit=500)
                    if row.get("agent") in names_set
                ][:limit],
                f"Errore caricamento log agente Notion {sorted(names_set)}",
            )
        client = get_service_client()
        names_list = list(names_set)
        return safely(
            [],
            lambda: (
                client.table("agent_logs")
                .select("*")
                .in_("agent", names_list)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
                .data
                or []
            ),
            f"Errore caricamento log agente {names_list}",
        )
