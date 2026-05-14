"""POST /api/kbot/generate-pdf — LLM analysis → HTML → Playwright PDF → Storage + email.

Auth model:
- If INTERNAL_API_KEY env is set and the caller provides matching `x-internal-key`,
  the request is accepted (used by Stripe webhook server-to-server).
- Otherwise, the session must either:
  - be `status='paid'`, OR
  - be called with `test_mode: true` AND not already paid (developer convenience).
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from ..lib import sessions
from ..lib.analysis import generate_analysis_json
from ..lib.auth import AuthUser, optional_user
from ..lib.email import send_report_ready_email
from ..lib.pdf_renderer import render_pdf
from ..lib.storage import upload_pdf
from ..settings import INTERNAL_API_KEY, STORAGE_REPORTS_BUCKET

router = APIRouter()
log = logging.getLogger(__name__)


class GeneratePdfBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    testMode: bool = Field(default=False, alias="test_mode")

    class Config:
        populate_by_name = True


@router.post("/generate-pdf")
def generate_pdf(
    body: GeneratePdfBody,
    user: Optional[AuthUser] = Depends(optional_user),
    x_internal_key: Optional[str] = Header(default=None),
):
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    # Authorization rules.
    is_internal = bool(INTERNAL_API_KEY and x_internal_key == INTERNAL_API_KEY)
    is_owner = bool(session.get("user_id") and user and user.id == session["user_id"])
    has_paid_status = session.get("status") == "paid"

    if not is_internal:
        owner = session.get("user_id")
        if owner and not is_owner:
            raise HTTPException(status_code=403, detail="not your session")
        if not body.testMode and not has_paid_status:
            raise HTTPException(status_code=402, detail="payment required")
        if body.testMode and has_paid_status:
            raise HTTPException(status_code=403, detail="test_mode disabled on paid sessions")

    # Idempotency: if PDF already produced and not in test_mode, return cached.
    cached_url = session.get("pdf_url")
    if cached_url and not body.testMode:
        return {"pdf_url": cached_url, "cached": True}

    # 1. LLM analysis JSON.
    try:
        analysis = generate_analysis_json(session)
    except Exception as exc:
        log.exception("Analysis generation failed")
        raise HTTPException(status_code=502, detail=f"analysis failed: {exc}")

    # 2. PDF rendering.
    try:
        pdf_bytes = render_pdf(analysis, session_id=session["id"])
    except Exception as exc:
        log.exception("PDF rendering failed")
        raise HTTPException(status_code=500, detail=f"pdf rendering failed: {exc}")

    # 3. Upload to Supabase Storage.
    storage_path = f"kbot-{session['id']}-{int(time.time() * 1000)}.pdf"
    try:
        public_url = upload_pdf(
            bucket=STORAGE_REPORTS_BUCKET,
            path=storage_path,
            content=pdf_bytes,
        )
    except Exception as exc:
        log.exception("Storage upload failed")
        raise HTTPException(status_code=500, detail=f"storage upload failed: {exc}")

    # 4. Persist URL + status.
    patch = {"pdf_url": public_url}
    if not body.testMode:
        patch["status"] = "paid"
        patch["paid_at"] = datetime.now(timezone.utc).isoformat()
    updated = sessions.update_session(session["id"], patch)

    # 5. Send email if recipient available (best-effort).
    recipient = session.get("email") or (user.email if user else None)
    if recipient and not body.testMode:
        sent = send_report_ready_email(
            to_email=recipient,
            report_url=public_url,
            report_title=analysis.get("meta", {}).get("title") or "Report operativo",
            pdf_bytes=pdf_bytes,
            pdf_filename=f"k2ai-report-{session['id'][:8]}.pdf",
        )
        if not sent:
            log.warning("Report email not sent for session %s", session["id"])

    return {
        "pdf_url": public_url,
        "cached": False,
        "test_mode": body.testMode,
        "session": sessions.public_session(updated),
    }
