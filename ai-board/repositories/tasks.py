"""Tasks repository (Notion-only at present)."""

from __future__ import annotations

from typing import Any

from core import notion_board
from repositories._common import safely


class TasksRepository:
    """Reads from Notion "Task" DB. Supabase path has no direct equivalent."""

    def list_tasks(self) -> list[dict[str, Any]]:
        if not notion_board.notion_enabled():
            return []
        return safely(
            [],
            notion_board.list_tasks,
            "Errore lettura tasks Notion",
        )
