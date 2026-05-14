"""POST /api/kbot/message — chat turn against an existing session.

Mirror of api/kbot/message.ts in the site.
"""
from __future__ import annotations

import logging
from typing import List, Optional

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..lib import sessions
from ..lib.auth import AuthUser, optional_user
from ..lib.prompts import (
    build_system_prompt_v2,
    compact_messages,
    extract_summary,
    normalize_assistant_reply,
    strip_summary_block,
)
from ..lib.services import normalize_service_id, resolve_skills_for_session
from ..settings import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    MAX_HISTORY_MESSAGES,
    MAX_MESSAGE_CHARS,
)

router = APIRouter()
log = logging.getLogger(__name__)


class MessageBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    serviceId: Optional[str] = Field(default=None, alias="service_id")
    message: Optional[str] = None
    messages: Optional[List[dict]] = None

    class Config:
        populate_by_name = True


def _check_ownership(session: dict, user: Optional[AuthUser]) -> None:
    owner = session.get("user_id")
    if owner and (not user or user.id != owner):
        raise HTTPException(status_code=403, detail="not your session")


def _new_user_messages(body: MessageBody) -> List[dict]:
    if body.message and body.message.strip():
        return [{"role": "user", "content": body.message.strip()}]
    if body.messages:
        return [
            {"role": m.get("role", "user"), "content": str(m.get("content") or "")}
            for m in body.messages
            if str(m.get("content") or "").strip()
        ]
    return []


@router.post("/message")
def post_message(body: MessageBody, user: Optional[AuthUser] = Depends(optional_user)):
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    _check_ownership(session, user)

    new_msgs = _new_user_messages(body)
    if not new_msgs:
        raise HTTPException(status_code=400, detail="empty message")

    # Override service_id if provided this turn.
    collected = dict(session.get("collected_data") or {})
    incoming_service = normalize_service_id(body.serviceId)
    if incoming_service:
        collected["service_id"] = incoming_service

    merged_messages = sessions.append_messages(session, new_msgs)
    session_for_prompt = {**session, "collected_data": collected, "messages": merged_messages}
    skills = resolve_skills_for_session(session_for_prompt)
    system_prompt = build_system_prompt_v2(skills, session_for_prompt)
    history = compact_messages(merged_messages, MAX_HISTORY_MESSAGES, MAX_MESSAGE_CHARS)

    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    try:
        result = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1200,
            system=system_prompt,
            messages=history,
        )
    except anthropic.APIError as exc:
        log.exception("Anthropic API error")
        raise HTTPException(status_code=502, detail=f"upstream error: {exc}")

    raw_text = "".join(
        block.text for block in result.content if getattr(block, "type", "") == "text"
    )
    summary = extract_summary(raw_text)
    user_visible = normalize_assistant_reply(strip_summary_block(raw_text))

    # Persist updated state.
    updated_messages = sessions.append_messages(
        {**session, "messages": merged_messages},
        [{"role": "assistant", "content": user_visible}],
    )
    if summary:
        collected.update(
            {
                k: v
                for k, v in summary.items()
                if v is not None and v != ""
            }
        )
        collected["extractedData"] = {**(collected.get("extractedData") or {}), **summary}
        collected["analysis_ready"] = True

    new_step = int(session.get("step") or 1) + 1
    updated = sessions.update_session(
        body.sessionId,
        {
            "messages": updated_messages,
            "collected_data": collected,
            "step": new_step,
        },
    )

    return {
        "message": user_visible,
        "summary": summary,
        "nextAction": "show_summary" if summary else "continue",
        "session": sessions.public_session(updated),
    }
