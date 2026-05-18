"""POST /api/kbot/generate-pdf — LLM analysis → HTML → Playwright PDF → Storage + email.

Auth model:
- If INTERNAL_API_KEY env is set and the caller provides matching `x-internal-key`,
  the request is accepted (used by Stripe webhook server-to-server).
- Otherwise, the session must either:
  - be `status='paid'`, OR
  - be called with `test_mode: true` AND not already paid (developer convenience).
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import re

from ..lib import sessions
from ..lib.analysis import generate_analysis_json
from ..lib.analytics import track_server
from ..lib.auth import AuthUser, optional_user
from ..lib.email import send_report_ready_email
from ..lib.pdf_renderer import render_pdf
from ..lib.storage import upload_pdf
from ..settings import INTERNAL_API_KEY, STORAGE_REPORTS_BUCKET


def _make_friendly_filename(analysis: dict, session: dict) -> str:
    """Genera filename leggibile dal titolo report invece di UUID.

    Es: "Audit SEO Tecnico — K2-AI" → "audit-seo-tecnico-k2-ai-20260518.pdf"
    Fallback su 'report-{date}' se titolo mancante.
    """
    title = (analysis.get("meta", {}) or {}).get("title") or "report"
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", title.lower())
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)[:60].strip("-") or "report"
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{slug}-{date_str}.pdf"

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
    storage_path = _make_friendly_filename(analysis, session)
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
            pdf_filename=storage_path,
        )
        if not sent:
            log.warning("Report email not sent for session %s", session["id"])

    track_server(
        distinct_id=session["id"],
        event="report_generated",
        properties={
            "tier": "paid" if not body.testMode else "test",
            "test_mode": body.testMode,
        },
    )

    return {
        "pdf_url": public_url,
        "cached": False,
        "test_mode": body.testMode,
        "session": sessions.public_session(updated),
    }


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/generate-pdf/stream")
async def generate_pdf_stream(
    body: GeneratePdfBody,
    user: Optional[AuthUser] = Depends(optional_user),
    x_internal_key: Optional[str] = Header(default=None),
):
    """SSE variant: emette stage events real-time durante la generazione."""
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

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

    cached_url = session.get("pdf_url")
    if cached_url and not body.testMode:
        async def cached_gen() -> AsyncGenerator[str, None]:
            yield _sse({"stage": "cached", "progress": 100, "pdf_url": cached_url})
        return StreamingResponse(cached_gen(), media_type="text/event-stream")

    async def event_gen() -> AsyncGenerator[str, None]:
        loop = asyncio.get_running_loop()

        # Heartbeat: progress lineare durante l'analisi LLM (lo stage più lungo).
        analysis_done = asyncio.Event()
        analysis_result: dict = {}

        async def heartbeat():
            start = time.monotonic()
            # Sonnet con web_search dura tipicamente 30-90s. Mappiamo 0→60% in 70s.
            target_duration = 70.0
            while not analysis_done.is_set():
                elapsed = time.monotonic() - start
                pct = min(60, int(60 * elapsed / target_duration))
                stage_text = (
                    "Ricerche web in corso..." if pct < 25
                    else "Analisi dati e benchmark..." if pct < 45
                    else "Strutturazione del report..."
                )
                yield _sse({"stage": stage_text, "progress": max(5, pct)})
                try:
                    await asyncio.wait_for(analysis_done.wait(), timeout=2.0)
                    return
                except asyncio.TimeoutError:
                    continue

        def run_analysis():
            try:
                analysis_result["data"] = generate_analysis_json(session)
            except Exception as exc:
                analysis_result["error"] = str(exc)
            finally:
                loop.call_soon_threadsafe(analysis_done.set)

        # Start LLM analysis in a thread (bloccante)
        asyncio.create_task(asyncio.to_thread(run_analysis))

        async for chunk in heartbeat():
            yield chunk

        if "error" in analysis_result:
            yield _sse({"stage": "error", "progress": 0, "error": f"analisi fallita: {analysis_result['error']}"})
            return
        analysis = analysis_result["data"]

        yield _sse({"stage": "Rendering PDF...", "progress": 65})
        try:
            pdf_bytes = render_pdf(analysis, session_id=session["id"])
        except Exception as exc:
            log.exception("PDF render failed")
            yield _sse({"stage": "error", "progress": 0, "error": f"rendering: {exc}"})
            return

        yield _sse({"stage": "Caricamento su storage...", "progress": 88})
        storage_path = _make_friendly_filename(analysis, session)
        try:
            public_url = await asyncio.to_thread(
                upload_pdf,
                bucket=STORAGE_REPORTS_BUCKET,
                path=storage_path,
                content=pdf_bytes,
            )
        except Exception as exc:
            log.exception("Upload failed")
            yield _sse({"stage": "error", "progress": 0, "error": f"upload: {exc}"})
            return

        patch = {"pdf_url": public_url}
        if not body.testMode:
            patch["status"] = "paid"
            patch["paid_at"] = datetime.now(timezone.utc).isoformat()
        updated = sessions.update_session(session["id"], patch)

        recipient = session.get("email") or (user.email if user else None)
        if recipient and not body.testMode:
            try:
                await asyncio.to_thread(
                    send_report_ready_email,
                    to_email=recipient,
                    report_url=public_url,
                    report_title=analysis.get("meta", {}).get("title") or "Report operativo",
                    pdf_bytes=pdf_bytes,
                    pdf_filename=storage_path,
                )
            except Exception:
                log.warning("Email send failed")

        track_server(
            distinct_id=session["id"],
            event="report_generated",
            properties={"tier": "paid" if not body.testMode else "test", "test_mode": body.testMode, "stream": True},
        )

        yield _sse({
            "stage": "Pronto",
            "progress": 100,
            "pdf_url": public_url,
            "session": sessions.public_session(updated),
        })

    return StreamingResponse(event_gen(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})
