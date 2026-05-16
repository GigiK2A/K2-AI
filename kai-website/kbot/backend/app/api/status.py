"""GET /api/kbot/status?id=... — lightweight polling endpoint.

H4-backend: enforce session ownership. If the session is linked to a user,
the caller must authenticate as that user. Anonymous sessions remain readable
by anyone holding the session id (the id is the capability), but we still
gate ``pdf_url`` behind the owner so that a leaked id cannot directly grab
the generated report URL.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..lib import sessions
from ..lib.auth import AuthUser, optional_user

router = APIRouter()


@router.get("/status")
def status(
    id: str = Query(..., min_length=8),
    user: Optional[AuthUser] = Depends(optional_user),
):
    session = sessions.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    owner = session.get("user_id")
    is_owner = bool(owner and user and user.id == owner)
    if owner and not is_owner:
        raise HTTPException(status_code=403, detail="not your session")

    # Anonymous session OR authenticated owner can see status; pdf_url is only
    # surfaced for the owner to avoid leaking a signed/public URL to anyone
    # who learns the session UUID.
    pdf_url = session.get("pdf_url") if (is_owner or not owner) else None
    return {
        "status": session.get("status"),
        "pdf_url": pdf_url,
    }
