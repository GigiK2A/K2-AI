"""POST /api/kbot/followups — generate 3 short follow-up questions from recent turns.

Lightweight Claude call (max_tokens=200). Frontend calls this once after the
assistant emits a long report (>1500 chars) and caches the result on the
message itself.
"""
from __future__ import annotations

import logging
from typing import List, Optional

import anthropic
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..lib import sessions
from ..lib.auth import AuthUser, optional_user
from ..lib.limiter import limiter
from ..settings import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

router = APIRouter()
log = logging.getLogger(__name__)


class FollowUpsBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")

    class Config:
        populate_by_name = True


def _build_prompt(messages: list[dict]) -> str:
    tail = messages[-3:] if len(messages) > 3 else messages[:]
    lines: list[str] = []
    for m in tail:
        role = "Utente" if m.get("role") == "user" else "Assistant"
        content = str(m.get("content") or "").strip()
        if len(content) > 1200:
            content = content[:1200] + "…"
        lines.append(f"{role}: {content}")
    history = "\n\n".join(lines)
    return (
        "Sei un analista K2-AI. Sulla base degli ultimi turni qui sotto, "
        "genera ESATTAMENTE 3 domande di follow-up brevi (max 60 caratteri) "
        "che l'utente potrebbe voler chiedere. Una per riga, senza numerazione, "
        "senza virgolette, senza commenti.\n\n"
        f"--- TURNI ---\n{history}\n--- FINE ---\n\nLe 3 domande:"
    )


def _parse_lines(text: str) -> List[str]:
    out: list[str] = []
    for raw in (text or "").splitlines():
        s = raw.strip().lstrip("-•*0123456789.) ").strip().strip('"\'')
        if not s:
            continue
        if len(s) > 80:
            s = s[:80].rstrip()
        out.append(s)
        if len(out) == 3:
            break
    return out


@router.post("/followups")
@limiter.limit("20/minute")
def post_followups(
    request: Request,
    body: FollowUpsBody,
    user: Optional[AuthUser] = Depends(optional_user),
):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    owner = session.get("user_id")
    if owner and (not user or user.id != owner):
        raise HTTPException(status_code=403, detail="not your session")

    messages = list(session.get("messages") or [])
    if not messages:
        return {"followups": []}

    prompt = _build_prompt(messages)
    # FAST-FAIL (fix 524): i follow-up sono un EXTRA cosmetico (3 chip). Niente retry SDK e
    # timeout basso → la chiamata non può mai avvicinarsi al limite edge di Cloudflare (~100s)
    # e degradare in un 524. Peggio caso: pochi secondi, poi lista vuota. max_retries=0 sul
    # client evita il retry-storm di Anthropic quando è lento/rate-limited.
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, max_retries=0)
    try:
        result = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
            timeout=15.0,
        )
    except (anthropic.APITimeoutError, anthropic.APIError):
        # non è un errore da esporre: nessun follow-up, il frontend degrada in silenzio.
        log.info("follow-ups non disponibili (upstream lento/errore) — degrado a lista vuota")
        return {"followups": []}

    raw = "".join(b.text for b in result.content if getattr(b, "type", "") == "text")
    return {"followups": _parse_lines(raw)}
