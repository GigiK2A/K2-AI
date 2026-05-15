"""POST /api/kbot/fetch-url — fetch a URL and store extracted content in the session."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..lib import sessions
from ..lib.auth import AuthUser, optional_user
from ..lib.url_fetcher import UrlFetchError, fetch_url_content

router = APIRouter()
log = logging.getLogger(__name__)

MAX_URLS_PER_SESSION = 5


class FetchUrlBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    url: str

    class Config:
        populate_by_name = True


@router.post("/fetch-url")
async def post_fetch_url(
    body: FetchUrlBody, user: Optional[AuthUser] = Depends(optional_user)
):
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    owner = session.get("user_id")
    if owner and (not user or user.id != owner):
        raise HTTPException(status_code=403, detail="not your session")

    collected = dict(session.get("collected_data") or {})
    existing_urls: list = list(collected.get("analyzed_urls") or [])

    # Check cache — if same URL already fetched this session, return it
    for entry in existing_urls:
        if entry.get("url") == body.url:
            return {
                "ok": True,
                "url": body.url,
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "cached": True,
            }

    if len(existing_urls) >= MAX_URLS_PER_SESSION:
        raise HTTPException(
            status_code=422,
            detail=f"Massimo {MAX_URLS_PER_SESSION} URL per sessione",
        )

    try:
        data = await fetch_url_content(body.url)
    except UrlFetchError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        log.warning("fetch_url failed for %s: %s", body.url, exc)
        raise HTTPException(status_code=502, detail=f"Impossibile raggiungere l'URL: {exc}")

    existing_urls.append(data)
    collected["analyzed_urls"] = existing_urls
    sessions.update_session(body.sessionId, {"collected_data": collected})

    return {
        "ok": True,
        "url": body.url,
        "title": data.get("title", ""),
        "summary": data.get("summary", ""),
        "cached": False,
    }
