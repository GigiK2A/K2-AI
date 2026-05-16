"""POST /api/kbot/message — chat turn against an existing session.

Mirror of api/kbot/message.ts in the site.
"""
from __future__ import annotations

import logging
import re as _re
from typing import List, Optional

import anthropic
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..lib import sessions
from ..lib.analytics import track_server
from ..lib.auth import AuthUser, optional_user
from ..lib.limiter import limiter
from ..lib.url_fetcher import UrlFetchError, fetch_url_content
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

_URL_RE = _re.compile(r"https?://[^\s<>\"']{6,}", _re.IGNORECASE)
_MAX_AUTO_URLS = 2  # max URLs to auto-fetch per message turn


def _extract_urls(text: str) -> list[str]:
    return list(dict.fromkeys(_URL_RE.findall(text or "")))[:_MAX_AUTO_URLS]


async def _auto_fetch_urls(text: str, collected: dict) -> dict:
    """Detect URLs in text, fetch any not already in session, return updated collected."""
    urls = _extract_urls(text)
    if not urls:
        return collected
    existing = {u.get("url") for u in (collected.get("analyzed_urls") or [])}
    new_entries = list(collected.get("analyzed_urls") or [])
    for url in urls:
        if url in existing:
            continue
        if len(new_entries) >= 5:
            break
        try:
            data = await fetch_url_content(url)
            new_entries.append(data)
            existing.add(url)
        except (UrlFetchError, Exception):
            pass  # silent — don't block the chat turn
    collected = dict(collected)
    collected["analyzed_urls"] = new_entries
    return collected


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
@limiter.limit("30/minute")
async def post_message(
    request: Request,
    body: MessageBody,
    user: Optional[AuthUser] = Depends(optional_user),
):
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

    # Auto-fetch any URLs the user just pasted
    last_user_text = new_msgs[-1]["content"] if new_msgs else ""
    collected = await _auto_fetch_urls(last_user_text, collected)

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
            timeout=60.0,
        )
    except anthropic.APITimeoutError:
        log.exception("Anthropic API timeout")
        raise HTTPException(status_code=504, detail="K-BOT è temporaneamente lento, riprova tra qualche secondo.")
    except anthropic.APIError:
        log.exception("Anthropic API error")
        raise HTTPException(status_code=502, detail="Errore upstream temporaneo. Riprova.")

    raw_text = "".join(
        block.text for block in result.content if getattr(block, "type", "") == "text"
    )
    usage = getattr(result, "usage", None)
    track_server(
        distinct_id=body.sessionId,
        event="message_processed",
        properties={
            "role": "assistant",
            "tokens_in": getattr(usage, "input_tokens", None) if usage else None,
            "tokens_out": getattr(usage, "output_tokens", None) if usage else None,
            "model": ANTHROPIC_MODEL,
        },
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
