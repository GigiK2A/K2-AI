"""GET /api/kbot/status?id=... — lightweight polling endpoint."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..lib import sessions

router = APIRouter()


@router.get("/status")
def status(id: str = Query(..., min_length=8)):
    session = sessions.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    return {
        "status": session.get("status"),
        "pdf_url": session.get("pdf_url"),
    }
