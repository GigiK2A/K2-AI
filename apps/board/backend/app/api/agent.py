"""Giuseppina agent API.

POST /api/agent/chat        — stream SSE with tool-use loop
GET  /api/agent/conversations
GET  /api/agent/conversations/{id}
POST /api/agent/conversations/{id}/title  — set title (optional)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.loop import run_agent
from app.db.client import get_supabase
from app.deps import require_auth

router = APIRouter(prefix="/api/agent", tags=["agent"], dependencies=[Depends(require_auth)])
log = logging.getLogger(__name__)

TABLE = "board_agent_conversations"


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None


# ── Conversation persistence ────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _load_conversation(sb, conv_id: str) -> Optional[Dict[str, Any]]:
    res = sb.table(TABLE).select("*").eq("id", conv_id).limit(1).execute()
    rows = res.data or []
    return rows[0] if rows else None


def _create_conversation(sb, first_user_message: str) -> Dict[str, Any]:
    title = first_user_message.strip().splitlines()[0][:80] if first_user_message else "Nuova conversazione"
    res = (
        sb.table(TABLE)
        .insert({"title": title, "messages": []})
        .execute()
    )
    return (res.data or [{}])[0]


def _save_conversation(sb, conv_id: str, messages: List[Dict[str, Any]]) -> None:
    sb.table(TABLE).update(
        {"messages": messages, "updated_at": _now_iso()}
    ).eq("id", conv_id).execute()


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/conversations")
def list_conversations() -> Dict[str, Any]:
    sb = get_supabase()
    res = (
        sb.table(TABLE)
        .select("id, title, created_at, updated_at")
        .order("updated_at", desc=True)
        .limit(50)
        .execute()
    )
    return {"conversations": res.data or []}


@router.get("/conversations/{conv_id}")
def get_conversation(conv_id: UUID) -> Dict[str, Any]:
    sb = get_supabase()
    row = _load_conversation(sb, str(conv_id))
    if not row:
        raise HTTPException(status_code=404, detail="conversation not found")
    return row


@router.post("/chat")
async def chat(body: ChatRequest):
    sb = get_supabase()

    # Resolve or create conversation
    if body.conversation_id:
        conv = _load_conversation(sb, str(body.conversation_id))
        if not conv:
            raise HTTPException(status_code=404, detail="conversation not found")
    else:
        conv = _create_conversation(sb, body.message)

    conv_id = conv["id"]
    history: List[Dict[str, Any]] = conv.get("messages") or []

    async def event_stream():
        # Tell the client the conversation id (especially when new).
        yield f"data: {json.dumps({'type': 'conversation', 'id': conv_id})}\n\n"

        final_messages: List[Dict[str, Any]] = list(history) + [
            {"role": "user", "content": body.message}
        ]

        try:
            async for sse_event in run_agent(history, body.message):
                # Intercept the terminal `done` event to capture full message list
                # for persistence — but still forward it to the client.
                if sse_event.startswith("data: "):
                    try:
                        payload = json.loads(sse_event[6:].strip())
                        if payload.get("type") == "done" and isinstance(payload.get("messages"), list):
                            final_messages = payload["messages"]
                    except (ValueError, TypeError):
                        pass
                yield sse_event
        except Exception as exc:  # noqa: BLE001
            log.exception("agent.stream_error")
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

        # Persist updated conversation
        try:
            _save_conversation(sb, conv_id, final_messages)
        except Exception:  # noqa: BLE001
            log.exception("agent.persist_error")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
