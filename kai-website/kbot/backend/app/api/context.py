"""POST /api/kbot/context/remove — drop a single file or URL from session context.

Body: {session_id, type: "file"|"url", id_or_name}
- For files: matches against `collected_data.uploaded_files` by path or name.
- For URLs: matches against `collected_data.analyzed_urls` by url or hostname.
"""
from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..lib import sessions
from ..lib.auth import AuthUser, optional_user
from ..lib.limiter import limiter

router = APIRouter()
log = logging.getLogger(__name__)


class RemoveContextBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    type: str  # "file" | "url"
    idOrName: str = Field(..., alias="id_or_name")

    class Config:
        populate_by_name = True


@router.post("/context/remove")
@limiter.limit("30/minute")
def remove_context(
    request: Request,
    body: RemoveContextBody,
    user: Optional[AuthUser] = Depends(optional_user),
):
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    owner = session.get("user_id")
    if owner and (not user or user.id != owner):
        raise HTTPException(status_code=403, detail="not your session")

    collected = dict(session.get("collected_data") or {})
    target = (body.idOrName or "").strip()
    if not target:
        raise HTTPException(status_code=400, detail="id_or_name is required")

    removed = False
    if body.type == "file":
        files = list(collected.get("uploaded_files") or [])
        new_files = [
            f for f in files
            if f.get("path") != target and f.get("name") != target
        ]
        removed = len(new_files) != len(files)
        collected["uploaded_files"] = new_files
    elif body.type == "url":
        urls = list(collected.get("analyzed_urls") or [])
        def _host(u: str) -> str:
            try:
                return (urlparse(u).hostname or "").lower()
            except Exception:
                return ""
        target_host = _host(target)
        new_urls = [
            u for u in urls
            if u.get("url") != target and (not target_host or _host(u.get("url", "")) != target_host)
        ]
        removed = len(new_urls) != len(urls)
        collected["analyzed_urls"] = new_urls
    else:
        raise HTTPException(status_code=400, detail="type must be 'file' or 'url'")

    if not removed:
        raise HTTPException(status_code=404, detail="item not found in context")

    sessions.update_session(body.sessionId, {"collected_data": collected})
    return {"ok": True, "removed": target, "type": body.type}
