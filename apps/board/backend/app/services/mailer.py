"""Resend email delivery — optional.

If RESEND_API_KEY is not set, send_email is a no-op that returns
{"sent": False, "reason": "..."} so callers can record state without
crashing.

We deliberately keep the import of `resend` lazy so the dependency is
not required at boot time (tests, dev) when the integration is off.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

from app.settings import get_settings

log = logging.getLogger(__name__)


def _md_to_html(md: str) -> str:
    """Tiny markdown→HTML pass — paragraphs, bold, lists, line breaks.

    We do not pull in a markdown library on purpose: the daily brief is
    a fairly mechanical document and we want zero extra deps for the
    optional Resend path.
    """
    # Escape HTML first.
    out = (
        md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    # Bold **text**.
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    # Headings.
    out = re.sub(r"^### (.+)$", r"<h3>\1</h3>", out, flags=re.MULTILINE)
    out = re.sub(r"^## (.+)$", r"<h2>\1</h2>", out, flags=re.MULTILINE)
    out = re.sub(r"^# (.+)$", r"<h1>\1</h1>", out, flags=re.MULTILINE)
    # Simple bullets.
    out = re.sub(r"^- (.+)$", r"<li>\1</li>", out, flags=re.MULTILINE)
    out = re.sub(r"(<li>.+</li>\n?)+", lambda m: f"<ul>{m.group(0)}</ul>", out)
    # Paragraphs from blank lines.
    paragraphs = [p.strip() for p in out.split("\n\n") if p.strip()]
    return "\n".join(
        p if p.startswith("<") else f"<p>{p.replace(chr(10), '<br>')}</p>"
        for p in paragraphs
    )


def send_email(
    *,
    to: str,
    subject: str,
    body_md: str,
    from_email: Optional[str] = None,
) -> Dict[str, Any]:
    """Send via Resend if configured, otherwise return a no-op result."""
    settings = get_settings()
    if not settings.resend_api_key:
        return {"sent": False, "reason": "RESEND_API_KEY not configured"}
    if not to:
        return {"sent": False, "reason": "no recipient"}

    try:
        import resend  # type: ignore

        resend.api_key = settings.resend_api_key
        params: Dict[str, Any] = {
            "from": from_email or settings.board_email_from,
            "to": [to],
            "subject": subject,
            "html": _md_to_html(body_md),
            "text": body_md,
        }
        result = resend.Emails.send(params)  # type: ignore[attr-defined]
        msg_id = (result or {}).get("id") if isinstance(result, dict) else None
        return {"sent": True, "id": msg_id}
    except Exception as exc:  # noqa: BLE001
        log.exception("mailer.send_failed", extra={"to": to})
        return {"sent": False, "reason": f"resend error: {exc}"}
