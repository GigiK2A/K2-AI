"""Approvals repository — hides Notion/Supabase split behind one API."""

from __future__ import annotations

from typing import Any, Iterable

from core import notion_board
from db.client import get_service_client
from repositories._common import safely


class ApprovalsRepository:
    """Read access to the `approvals` table / Notion "Approvazioni" DB."""

    def list_pending(self) -> list[dict[str, Any]]:
        if notion_board.notion_enabled():
            return safely(
                [],
                lambda: notion_board.list_approvals(["draft", "review"]),
                "Errore lettura draft Notion",
            )
        client = get_service_client()
        return safely(
            [],
            lambda: client.table("approvals")
            .select("id,task_id,agent,status,content_preview,created_at")
            .in_("status", ["draft", "review"])
            .execute()
            .data
            or [],
            "Errore lettura draft pendenti",
        )

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        if notion_board.notion_enabled():
            return safely(
                [],
                lambda: notion_board.list_approvals(limit=limit),
                "Errore lettura attività approvals Notion",
            )
        client = get_service_client()
        return safely(
            [],
            lambda: client.table("approvals")
            .select(
                "id,task_id,agent,status,content_preview,created_at,reviewed_at"
            )
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
            .data
            or [],
            "Errore lettura attività approval",
        )

    def list_approved(self) -> list[dict[str, Any]]:
        """Supabase-only: used when Notion is disabled."""
        if notion_board.notion_enabled():
            return []
        client = get_service_client()
        return safely(
            [],
            lambda: client.table("approvals")
            .select("id,status,reviewed_at,created_at")
            .eq("status", "approved")
            .execute()
            .data
            or [],
            "Errore lettura approvals approvati",
        )

    def list_pending_for_agents(
        self, related_names: Iterable[str]
    ) -> list[dict[str, Any]]:
        names_set = set(related_names)
        if notion_board.notion_enabled():
            return safely(
                [],
                lambda: [
                    item
                    for item in notion_board.list_approvals(["draft", "review"])
                    if item.get("agent") in names_set
                ],
                f"Errore lettura approvals agente Notion {sorted(names_set)}",
            )
        client = get_service_client()
        names_list = list(names_set)
        return safely(
            [],
            lambda: client.table("approvals")
            .select("*")
            .in_("agent", names_list)
            .in_("status", ["draft", "review"])
            .order("created_at", desc=True)
            .execute()
            .data
            or [],
            f"Errore lettura approvals agente {names_list}",
        )

    def list_for_task_ids(self, task_ids: Iterable[str]) -> list[dict[str, Any]]:
        ids = [tid for tid in task_ids if tid]
        if not ids:
            return []
        if notion_board.notion_enabled():
            return safely(
                [],
                lambda: [
                    row
                    for row in notion_board.list_approvals(limit=500)
                    if row.get("task_id") in set(ids)
                ],
                "Errore caricamento approvals per task_ids Notion",
            )
        client = get_service_client()
        return safely(
            [],
            lambda: client.table("approvals")
            .select(
                "id,task_id,status,full_content,founder_notes,created_at,reviewed_at"
            )
            .in_("task_id", ids)
            .execute()
            .data
            or [],
            "Errore caricamento approvals per task_ids",
        )

    def list_for_agents(
        self, related_names: Iterable[str]
    ) -> list[dict[str, Any]]:
        names_set = set(related_names)
        if notion_board.notion_enabled():
            return safely(
                [],
                lambda: [
                    row
                    for row in notion_board.list_approvals(limit=500)
                    if row.get("agent") in names_set
                ],
                f"Errore caricamento approvals agente Notion {sorted(names_set)}",
            )
        # Supabase path loads via task_ids in caller; noop fallback.
        return []

    def recent_draft_for_agents(
        self, related_names: Iterable[str], since_iso: str
    ) -> list[dict[str, Any]]:
        """Supabase-only quick check for a recent draft in a window."""
        if notion_board.notion_enabled():
            # Notion path is handled at service level because it needs
            # datetime comparison, keep parity explicit.
            return []
        client = get_service_client()
        names_list = list(set(related_names))
        return safely(
            [],
            lambda: (
                client.table("approvals")
                .select("id")
                .in_("agent", names_list)
                .eq("status", "draft")
                .gte("created_at", since_iso)
                .limit(1)
                .execute()
                .data
                or []
            ),
            f"Errore lettura stato agente {names_list}",
        )
