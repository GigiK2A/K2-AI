"""POST /api/kbot/report — deterministic report data builder (no LLM).

PHASE 2 STUB: returns the V2 summary stored in collected_data as report skeleton.
Full ReportData transformer will replace this in phase 2.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..lib import sessions
from ..lib.auth import AuthUser, optional_user

router = APIRouter()


class ReportBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")

    class Config:
        populate_by_name = True


@router.post("/report")
def build_report(body: ReportBody, user: Optional[AuthUser] = Depends(optional_user)):
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    owner = session.get("user_id")
    if owner and (not user or user.id != owner):
        raise HTTPException(status_code=403, detail="not your session")

    collected = dict(session.get("collected_data") or {})
    extracted = collected.get("extractedData") or {}

    # Minimal report skeleton until ReportData transformer is ported.
    report_data = {
        "serviceId": collected.get("service_id"),
        "summary": collected.get("summary") or extracted.get("summary"),
        "recommendedTier": collected.get("recommendedTier"),
        "extractedData": extracted,
    }

    collected["reportData"] = report_data
    collected["report"] = report_data
    updated = sessions.update_session(
        body.sessionId,
        {"collected_data": collected, "status": "report_ready"},
    )
    return {"reportData": report_data, "session": sessions.public_session(updated)}
