"""POST /api/kbot/session — create session, optionally linked to authenticated user.
POST /api/kbot/session/{id}/link-user — link an anonymous session to a logged-in user.
GET  /api/kbot/session/{id} — fetch session (public projection).
GET  /api/kbot/sessions — list sessions of the authenticated user (dashboard).
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..lib import sessions
from ..lib.analytics import track_server
from ..lib.auth import AuthUser, optional_user, require_user
from ..lib.limiter import limiter

router = APIRouter()


class CreateSessionBody(BaseModel):
    serviceId: Optional[str] = Field(default=None, alias="service_id")
    mode: Optional[str] = None

    class Config:
        populate_by_name = True


@router.post("/session")
@limiter.limit("20/minute")
def create_session(
    request: Request,
    body: CreateSessionBody,
    user: Optional[AuthUser] = Depends(optional_user),
):
    row = sessions.create_session(
        service_id=body.serviceId,
        mode=body.mode,
        user_id=user.id if user else None,
    )
    track_server(
        distinct_id=row["id"],
        event="session_created",
        properties={
            "service_id": body.serviceId,
            "mode": body.mode,
            "authed": bool(user),
        },
    )
    payload: dict = {"session_id": row["id"], "session": sessions.public_session(row)}
    # Anonymous sessions get a one-time link_token; the browser must hold it
    # and present it back to /session/{id}/link-user to claim the session
    # after login (H-6 — prevents takeover by anyone who learns the session UUID).
    if row.get("link_token"):
        payload["link_token"] = row["link_token"]
    return payload


@router.get("/session/{session_id}")
def get_session(session_id: str, user: Optional[AuthUser] = Depends(optional_user)):
    row = sessions.get_session(session_id)
    if not row:
        raise HTTPException(status_code=404, detail="session not found")
    # If session is owned by someone else, refuse unless caller owns it.
    owner = row.get("user_id")
    if owner and (not user or user.id != owner):
        raise HTTPException(status_code=403, detail="not your session")
    return {"session": sessions.public_session(row)}


@router.get("/sessions")
def list_my_sessions(user: AuthUser = Depends(require_user)) -> dict:
    rows = sessions.list_user_sessions(user.id, limit=50)
    return {
        "sessions": [sessions.public_session(r) for r in rows],
        "stats": {
            "total": len(rows),
            "paid": sum(1 for r in rows if r.get("status") == "paid"),
            "with_pdf": sum(1 for r in rows if r.get("pdf_url")),
        },
        "account": {
            "email": user.email,
            "has_paid": user.has_paid,
        },
    }


class LinkUserBody(BaseModel):
    link_token: Optional[str] = Field(default=None, alias="linkToken")

    class Config:
        populate_by_name = True


@router.post("/session/{session_id}/link-user")
def link_user(
    session_id: str,
    body: LinkUserBody,
    user: AuthUser = Depends(require_user),
):
    row = sessions.get_session(session_id)
    if not row:
        raise HTTPException(status_code=404, detail="session not found")
    existing_owner = row.get("user_id")
    if existing_owner:
        if existing_owner == user.id:
            return {"session": sessions.public_session(row)}
        raise HTTPException(status_code=409, detail="session already linked to another user")
    # H-6: anonymous → user claim requires the link_token issued at session
    # creation. Without it, anyone who knows the session UUID could claim it.
    if not body.link_token:
        raise HTTPException(status_code=400, detail="link_token required")
    updated = sessions.claim_session_with_token(session_id, user.id, body.link_token)
    if not updated:
        raise HTTPException(status_code=403, detail="invalid link_token")
    return {"session": sessions.public_session(updated)}
