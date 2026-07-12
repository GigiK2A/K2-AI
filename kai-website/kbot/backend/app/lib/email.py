"""Resend email wrapper (sync, fire-and-forget pattern)."""
from __future__ import annotations

import base64
import html
import logging
from typing import Optional

import httpx

from ..settings import KBOT_NOTIFY_EMAIL, REPORT_FROM_EMAIL, RESEND_API_KEY

log = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


def send_report_ready_email(
    *,
    to_email: str,
    report_url: str,
    report_title: str,
    pdf_bytes: Optional[bytes] = None,
    pdf_filename: str = "report-k2ai.pdf",
) -> bool:
    """Send 'your report is ready' email with optional PDF attachment.

    Returns True if Resend accepted the message, False otherwise. Errors are
    logged but never raised (the report is already saved on Storage).
    """
    if not RESEND_API_KEY:
        log.warning("RESEND_API_KEY not configured — skipping email")
        return False
    if not to_email:
        log.info("No recipient email — skipping notification")
        return False

    # Il titolo può derivare da output LLM: va escapato prima di finire nell'HTML
    # dell'email (difesa contro iniezione di markup nel corpo del messaggio).
    safe_title = html.escape(report_title)
    safe_url = html.escape(report_url, quote=True)

    html_body = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif; color:#0F172A; max-width:540px;">
      <h2 style="color:#0F2544; font-size:20px; margin:0 0 16px;">Il tuo report K2-AI è pronto</h2>
      <p style="font-size:14px; line-height:1.6; margin:0 0 12px;">
        Ciao, abbiamo generato il documento <strong>{safe_title}</strong> con priorità,
        azioni operative e roadmap a partire dalla conversazione con K-BOT.
      </p>
      <p style="margin:18px 0;">
        <a href="{safe_url}" style="background:#C2410C; color:#fff; padding:10px 18px; border-radius:4px; text-decoration:none; font-weight:600; font-size:14px;">Apri il report (PDF)</a>
      </p>
      <p style="font-size:12px; color:#64748B; line-height:1.5; margin:24px 0 0;">
        Il link punta al PDF salvato su Supabase Storage. Conservalo: il report è tuo.<br>
        Se hai domande, rispondi a questa email o scrivici da
        <a href="https://www.k2-ai.it/contatti.html" style="color:#0F2544;">k2-ai.it/contatti</a>.
      </p>
    </div>
    """

    payload = {
        "from": REPORT_FROM_EMAIL,
        "to": [to_email],
        "subject": f"Report K2-AI pronto — {report_title}",
        "html": html_body.strip(),
    }
    if KBOT_NOTIFY_EMAIL:
        payload["bcc"] = [KBOT_NOTIFY_EMAIL]
    if pdf_bytes:
        payload["attachments"] = [
            {
                "filename": pdf_filename,
                "content": base64.b64encode(pdf_bytes).decode("ascii"),
            }
        ]

    try:
        resp = httpx.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json=payload,
            timeout=15,
        )
    except httpx.HTTPError as exc:
        log.error("Resend HTTP error: %s", exc)
        return False

    if resp.status_code >= 400:
        log.error("Resend rejected message: %s %s", resp.status_code, resp.text[:300])
        return False
    return True
