from typing import Any, Iterable

from loguru import logger

from core import notion_board
from core.orchestrator import related_agent_names, resolve_agent_name
from core.text import truncate_text
from db.client import get_service_client
from db.models import AgentName

AGENT_CHAT_CONTENT_TYPES = {"agent_chat", "board_chat", "telegram_agent_chat"}
AGENT_CHAT_CHANNELS = {"agent_detail_chat", "board_chat", "telegram_agent_chat"}


def load_agent_conversation_turns(
    agent_name: AgentName | str,
    limit: int = 12,
    channels: Iterable[str] | None = None,
    content_types: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    canonical_name = resolve_agent_name(agent_name).value
    related_names = [item.value for item in related_agent_names(canonical_name)]
    if notion_board.notion_enabled():
        try:
            approvals = [
                item
                for item in notion_board.list_approvals(limit=max(limit * 10, 120))
                if item.get("agent") in related_names
            ]
        except Exception as exc:
            logger.warning(f"Errore caricamento storico conversazione Notion agente {canonical_name}: {exc}")
            return []

        allowed_channels = set(channels or AGENT_CHAT_CHANNELS)
        allowed_content_types = set(content_types or AGENT_CHAT_CONTENT_TYPES)
        approvals = [item for item in approvals if _is_conversation_item(item, allowed_channels, allowed_content_types)]
        approvals = approvals[:limit]

        turns: list[dict[str, Any]] = []
        for approval in reversed(approvals):
            full_approval = notion_board.get_approval(approval["id"]) or approval
            full_content = full_approval.get("full_content") or {}
            if not isinstance(full_content, dict):
                full_content = {}
            context_data = full_content.get("context") if isinstance(full_content.get("context"), dict) else {}
            turns.append(
                {
                    "task_id": full_approval.get("task_id"),
                    "approval_id": full_approval.get("id"),
                    "created_at": full_approval.get("created_at"),
                    "status": full_approval.get("status"),
                    "content_type": full_approval.get("content_type"),
                    "user_message": str(full_content.get("task") or ""),
                    "assistant_message": str(full_content.get("output") or full_approval.get("content_preview") or ""),
                    "attachments": context_data.get("attachments", []),
                    "llm_provider": None,
                    "llm_model": None,
                    "tokens_used": None,
                    "duration_ms": None,
                }
            )
        return turns

    client = get_service_client()

    try:
        approvals = (
            client.table("approvals")
            .select("*")
            .in_("agent", related_names)
            .order("created_at", desc=True)
            .limit(max(limit * 10, 120))
            .execute()
            .data
            or []
        )
    except Exception as exc:
        logger.warning(f"Errore caricamento storico conversazione agente {canonical_name}: {exc}")
        return []

    allowed_channels = set(channels or AGENT_CHAT_CHANNELS)
    allowed_content_types = set(content_types or AGENT_CHAT_CONTENT_TYPES)
    approvals = [item for item in approvals if _is_conversation_item(item, allowed_channels, allowed_content_types)]
    approvals = approvals[:limit]

    task_ids = [item.get("task_id") for item in approvals if item.get("task_id")]
    logs_by_task: dict[str, dict[str, Any]] = {}
    if task_ids:
        try:
            logs = (
                client.table("agent_logs")
                .select("task_id,llm_provider,llm_model,tokens_used,duration_ms,created_at,status")
                .in_("task_id", task_ids)
                .execute()
                .data
                or []
            )
            logs_by_task = {row.get("task_id"): row for row in logs if row.get("task_id")}
        except Exception as exc:
            logger.warning(f"Errore caricamento log conversazione agente {canonical_name}: {exc}")

    turns: list[dict[str, Any]] = []
    for approval in reversed(approvals):
        full_content = approval.get("full_content") or {}
        if not isinstance(full_content, dict):
            full_content = {}
        context_data = full_content.get("context") if isinstance(full_content.get("context"), dict) else {}
        log = logs_by_task.get(approval.get("task_id"), {})

        turns.append(
            {
                "task_id": approval.get("task_id"),
                "approval_id": approval.get("id"),
                "created_at": approval.get("created_at"),
                "status": approval.get("status"),
                "content_type": approval.get("content_type"),
                "user_message": str(full_content.get("task") or ""),
                "assistant_message": str(full_content.get("output") or ""),
                "attachments": context_data.get("attachments", []),
                "llm_provider": log.get("llm_provider"),
                "llm_model": log.get("llm_model"),
                "tokens_used": log.get("tokens_used"),
                "duration_ms": log.get("duration_ms"),
            }
        )
    return turns


def build_agent_conversation_context(
    agent_name: AgentName | str,
    limit: int = 10,
    channels: Iterable[str] | None = None,
    content_types: Iterable[str] | None = None,
    max_chars_per_message: int = 3000,
) -> list[dict[str, str]]:
    turns = load_agent_conversation_turns(
        agent_name=agent_name,
        limit=limit,
        channels=channels,
        content_types=content_types,
    )
    history: list[dict[str, str]] = []
    for turn in turns:
        user_message = str(turn.get("user_message") or "").strip()
        assistant_message = str(turn.get("assistant_message") or "").strip()
        if user_message:
            history.append({"role": "user", "content": truncate_text(user_message, max_chars_per_message)})
        if assistant_message:
            history.append({"role": "assistant", "content": truncate_text(assistant_message, max_chars_per_message)})
    return history


def _is_conversation_item(
    approval: dict[str, Any],
    allowed_channels: set[str],
    allowed_content_types: set[str],
) -> bool:
    content_type = str(approval.get("content_type") or "").strip()
    if content_type in allowed_content_types:
        return True

    full_content = approval.get("full_content") or {}
    if not isinstance(full_content, dict):
        return False
    context_data = full_content.get("context")
    if not isinstance(context_data, dict):
        return False

    channel = str(context_data.get("channel") or "").strip()
    if channel in allowed_channels:
        return True
    return False
