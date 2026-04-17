"""Pipeline leads repository."""

from __future__ import annotations

from typing import Any

from core import notion_board
from db.client import get_service_client
from repositories._common import safely


class PipelineRepository:
    """Reads from `pipeline_leads` table / Notion "Pipeline Lead" DB."""

    def list_leads(self) -> list[dict[str, Any]]:
        if notion_board.notion_enabled():
            return safely(
                [],
                notion_board.list_pipeline_leads,
                "Errore lettura pipeline Notion",
            )
        client = get_service_client()
        return safely(
            [],
            lambda: client.table("pipeline_leads").select("*").execute().data or [],
            "Errore lettura pipeline",
        )
