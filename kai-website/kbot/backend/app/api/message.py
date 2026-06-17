"""POST /api/kbot/message — chat turn against an existing session.

Mirror of api/kbot/message.ts in the site.
"""
from __future__ import annotations

import json
import logging
import re as _re
from typing import List, Optional

import anthropic
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
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

# Rileva URL incollati in chat anche SENZA schema: http(s)://, www., o dominio nudo
# con TLD comune (es. "studioX.com", "sito.it/pagina"). Evita le email (lookbehind @).
_URL_RE = _re.compile(
    r"(?:https?://|www\.)[^\s<>\"')\]]{2,}"
    r"|(?<![@\w/.])(?:[a-z0-9](?:[a-z0-9-]{0,40}[a-z0-9])?\.)+"
    r"(?:it|com|net|org|io|eu|ai|co|info|biz|dev|app|cloud|online|shop|store|tech|me|uk|de|fr|es|us|gov|edu|news|agency|studio|consulting|email)"
    r"(?:/[^\s<>\"')\]]*)?",
    _re.IGNORECASE)
_MAX_AUTO_URLS = 2  # max URLs to auto-fetch per message turn


def _normalize_url(u: str) -> str:
    u = (u or "").strip().rstrip(".,;:!?)>]\"'")
    if not u.lower().startswith(("http://", "https://")):
        u = "https://" + u
    return u


def _extract_urls(text: str) -> list[str]:
    seen, out = set(), []
    for m in _URL_RE.findall(text or ""):
        nu = _normalize_url(m)
        if nu.lower() not in seen:
            seen.add(nu.lower()); out.append(nu)
    return out[:_MAX_AUTO_URLS]


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
    forcedSkills: Optional[List[str]] = Field(default=None, alias="forced_skills")

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

    # Persist forced skills (UI may toggle them on/off) into collected_data.
    if body.forcedSkills is not None:
        forced = [s for s in (body.forcedSkills or []) if isinstance(s, str) and s.strip()]
        collected["forced_skills"] = forced

    session_for_prompt = {**session, "collected_data": collected, "messages": merged_messages}
    skills = resolve_skills_for_session(session_for_prompt)
    # Merge user-forced skills on top (deduped, order-preserving).
    forced_skills: list[str] = list(collected.get("forced_skills") or [])
    if forced_skills:
        seen = set(skills)
        for fs in forced_skills:
            if fs and fs not in seen:
                skills.append(fs)
                seen.add(fs)
    system_prompt = build_system_prompt_v2(skills, session_for_prompt)
    history = compact_messages(merged_messages, MAX_HISTORY_MESSAGES, MAX_MESSAGE_CHARS)

    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    try:
        result = client.messages.create(
            model=ANTHROPIC_MODEL,
            # max_tokens generoso: serve per i report finali. 1200 era ok per
            # chat brevi ma segava i report a metà.
            max_tokens=8000,
            system=system_prompt,
            messages=history,
            timeout=120.0,
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
        # Selettore di catalogo: a fine conversazione pre-seleziona il Boost 8e da
        # generare (non sovrascrive un boost già suggerito da tag pillar del sito).
        # Mostra il pannello (boost_suggerito) solo dopo qualche scambio reale, non
        # al 1° messaggio: il bot a volte emette il riepilogo troppo presto.
        _user_turns = sum(1 for _m in (merged_messages or []) if isinstance(_m, dict) and _m.get("role") == "user")
        # Ricalcola a OGNI turno (>=3): la suggestion segue l'intento CORRENTE e
        # auto-corregge un routing stantio (bug giu 2026: marketing → LegalBoost DD).
        # Eccezione: se il boost viene dal TAG PILLAR del sito (tag_pillar settato),
        # lo preserviamo (è il contesto della pagina da cui arriva l'utente).
        if _user_turns >= 3 and not collected.get("tag_pillar"):
            try:
                from ..lib import catalog as _catalog
                _boost = _catalog.suggest_boost(summary)
                if _boost:
                    collected["boost_suggerito"] = _boost["id"]
                    collected["boost_suggerito_label"] = _boost.get("label")
            except Exception:
                pass  # il routing non deve mai bloccare la chat

    # Always expose the skills used in this turn so the UI can render them.
    existing_extracted = dict(collected.get("extractedData") or {})
    existing_extracted["used_skills"] = list(skills)
    collected["extractedData"] = existing_extracted

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


# ---------------------------------------------------------------------------
# Streaming variant (Server-Sent Events).
# ---------------------------------------------------------------------------


async def _prepare_turn(body: MessageBody, user: Optional[AuthUser]):
    """Shared setup: load session, append user msg, fetch URLs, build prompt."""
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    _check_ownership(session, user)

    new_msgs = _new_user_messages(body)
    if not new_msgs:
        raise HTTPException(status_code=400, detail="empty message")

    collected = dict(session.get("collected_data") or {})
    incoming_service = normalize_service_id(body.serviceId)
    if incoming_service:
        collected["service_id"] = incoming_service

    merged_messages = sessions.append_messages(session, new_msgs)
    last_user_text = new_msgs[-1]["content"] if new_msgs else ""
    collected = await _auto_fetch_urls(last_user_text, collected)

    session_for_prompt = {**session, "collected_data": collected, "messages": merged_messages}
    skills = resolve_skills_for_session(session_for_prompt)
    system_prompt = build_system_prompt_v2(skills, session_for_prompt)
    history = compact_messages(merged_messages, MAX_HISTORY_MESSAGES, MAX_MESSAGE_CHARS)

    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    return session, merged_messages, collected, system_prompt, history, skills


def _persist_assistant_turn(
    session: dict,
    body_session_id: str,
    merged_messages: list,
    collected: dict,
    raw_text: str,
    skills: Optional[List[str]] = None,
) -> tuple[str, Optional[dict], dict]:
    """Apply summary extraction + persist assistant message. Returns (user_visible, summary, updated_session)."""
    summary = extract_summary(raw_text)
    user_visible = normalize_assistant_reply(strip_summary_block(raw_text))

    updated_messages = sessions.append_messages(
        {**session, "messages": merged_messages},
        [{"role": "assistant", "content": user_visible}],
    )
    if summary:
        collected.update(
            {k: v for k, v in summary.items() if v is not None and v != ""}
        )
        collected["extractedData"] = {**(collected.get("extractedData") or {}), **summary}
        collected["analysis_ready"] = True
        # Selettore di catalogo: a fine conversazione pre-seleziona il Boost 8e da
        # generare (non sovrascrive un boost già suggerito da tag pillar del sito).
        # Mostra il pannello (boost_suggerito) solo dopo qualche scambio reale, non
        # al 1° messaggio: il bot a volte emette il riepilogo troppo presto.
        _user_turns = sum(1 for _m in (merged_messages or []) if isinstance(_m, dict) and _m.get("role") == "user")
        # Ricalcola a OGNI turno (>=3): la suggestion segue l'intento CORRENTE e
        # auto-corregge un routing stantio (bug giu 2026: marketing → LegalBoost DD).
        # Eccezione: se il boost viene dal TAG PILLAR del sito (tag_pillar settato),
        # lo preserviamo (è il contesto della pagina da cui arriva l'utente).
        if _user_turns >= 3 and not collected.get("tag_pillar"):
            try:
                from ..lib import catalog as _catalog
                _boost = _catalog.suggest_boost(summary)
                if _boost:
                    collected["boost_suggerito"] = _boost["id"]
                    collected["boost_suggerito_label"] = _boost.get("label")
            except Exception:
                pass  # il routing non deve mai bloccare la chat

    # Always expose skills used in this turn so the UI panel can render them
    # (mirror of the non-streaming branch — era assente nello stream).
    if skills is not None:
        existing_extracted = dict(collected.get("extractedData") or {})
        existing_extracted["used_skills"] = list(skills)
        collected["extractedData"] = existing_extracted

    new_step = int(session.get("step") or 1) + 1
    updated = sessions.update_session(
        body_session_id,
        {
            "messages": updated_messages,
            "collected_data": collected,
            "step": new_step,
        },
    )
    return user_visible, summary, updated


def _sse(event_data: dict) -> str:
    return f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"


@router.post("/message/stream")
@limiter.limit("30/minute")
async def post_message_stream(
    request: Request,
    body: MessageBody,
    user: Optional[AuthUser] = Depends(optional_user),
):
    session, merged_messages, collected, system_prompt, history, skills = await _prepare_turn(body, user)
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    async def event_gen():
        raw_buffer: list[str] = []
        try:
            # Anthropic SDK sync streaming context manager — iterate token deltas.
            with client.messages.stream(
                model=ANTHROPIC_MODEL,
                max_tokens=8000,
                system=system_prompt,
                messages=history,
                timeout=120.0,
            ) as stream:
                for text_chunk in stream.text_stream:
                    if await request.is_disconnected():
                        log.info("kbot stream: client disconnected mid-response")
                        return
                    if not text_chunk:
                        continue
                    raw_buffer.append(text_chunk)
                    yield _sse({"delta": text_chunk})
                final = stream.get_final_message()
                usage = getattr(final, "usage", None)
        except anthropic.APITimeoutError:
            log.exception("Anthropic stream timeout")
            yield _sse({"error": "K-BOT è temporaneamente lento, riprova tra qualche secondo."})
            return
        except anthropic.APIError:
            log.exception("Anthropic stream error")
            yield _sse({"error": "Errore upstream temporaneo. Riprova."})
            return
        except Exception:
            log.exception("Unexpected stream error")
            yield _sse({"error": "Errore imprevisto durante lo stream."})
            return

        raw_text = "".join(raw_buffer)
        track_server(
            distinct_id=body.sessionId,
            event="message_processed",
            properties={
                "role": "assistant",
                "tokens_in": getattr(usage, "input_tokens", None) if usage else None,
                "tokens_out": getattr(usage, "output_tokens", None) if usage else None,
                "model": ANTHROPIC_MODEL,
                "stream": True,
            },
        )
        try:
            user_visible, summary, updated = _persist_assistant_turn(
                session, body.sessionId, merged_messages, collected, raw_text, skills
            )
        except Exception:
            log.exception("Failed to persist streamed assistant turn")
            yield _sse({"error": "Errore salvataggio risposta."})
            return

        yield _sse(
            {
                "done": True,
                "message": user_visible,
                "summary": summary,
                "nextAction": "show_summary" if summary else "continue",
                "session": sessions.public_session(updated),
            }
        )

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
