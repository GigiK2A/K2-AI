"""
Servizio email per K2-AI.

Priorità:
  1. Resend  (RESEND_API_KEY impostata)  — via httpx, nessuna dipendenza extra
  2. SMTP    (SMTP_HOST + SMTP_USER + SMTP_PASSWORD) — via smtplib standard

Se nessuno è configurato l'invio viene saltato con un avviso in log.
"""
from __future__ import annotations

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import httpx
from loguru import logger

from core.config import settings

# ── Template email di conferma ────────────────────────────────────────────────

_CONFIRMATION_HTML = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Messaggio ricevuto — K2-AI</title>
<style>
  body {{ margin:0; padding:0; background:#0a0a0a; font-family:'Helvetica Neue',Arial,sans-serif; color:#e5e5e5; }}
  .wrap {{ max-width:560px; margin:40px auto; padding:0 16px; }}
  .card {{ background:#141414; border:1px solid #2a2a2a; padding:40px 40px 36px; }}
  .logo {{ font-size:13px; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:#888; margin-bottom:32px; }}
  h1 {{ font-size:22px; font-weight:600; color:#f5f5f5; margin:0 0 16px; letter-spacing:-.02em; line-height:1.3; }}
  p {{ font-size:15px; line-height:1.7; color:#aaa; margin:0 0 20px; }}
  .highlight {{ color:#f5f5f5; }}
  .divider {{ border:none; border-top:1px solid #2a2a2a; margin:28px 0; }}
  .detail-row {{ display:flex; gap:12px; margin-bottom:8px; font-size:14px; }}
  .detail-label {{ color:#555; min-width:80px; }}
  .detail-value {{ color:#ccc; }}
  .footer {{ margin-top:32px; font-size:12px; color:#444; line-height:1.6; }}
  .cta {{ display:inline-block; margin-top:24px; padding:12px 24px; background:#f5f5f5; color:#0a0a0a; font-size:13px; font-weight:600; text-decoration:none; letter-spacing:.04em; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <div class="logo">K2-AI</div>
    <h1>Messaggio ricevuto, {name}.</h1>
    <p>Abbiamo preso in carico la tua richiesta. <span class="highlight">Ti risponderemo entro 24 ore lavorative</span> all'indirizzo da cui hai scritto.</p>

    <hr class="divider">

    <div class="detail-row"><span class="detail-label">Nome</span><span class="detail-value">{name}</span></div>
    {company_row}
    <div class="detail-row"><span class="detail-label">Email</span><span class="detail-value">{email}</span></div>
    <div class="detail-row"><span class="detail-label">Messaggio</span><span class="detail-value" style="white-space:pre-wrap">{message_preview}</span></div>

    <hr class="divider">

    <p style="margin-bottom:8px">Nel frattempo puoi esplorare il nostro approccio:</p>
    <a href="https://k2-ai.it/metodo.html" class="cta">Scopri il metodo →</a>

    <div class="footer">
      <p style="margin:0">Questa è una conferma automatica. Non rispondere a questa email — usa il pulsante sopra o <a href="https://k2-ai.it/contatti.html" style="color:#666">contattaci dal sito</a>.</p>
      <p style="margin:8px 0 0">© 2025 K2-AI</p>
    </div>
  </div>
</div>
</body>
</html>"""

_CONFIRMATION_TEXT = """K2-AI — Messaggio ricevuto

Ciao {name},

abbiamo ricevuto la tua richiesta e ti risponderemo entro 24 ore lavorative.

---
Nome: {name}
{company_line}Email: {email}
Messaggio: {message_preview}
---

Nel frattempo puoi esplorare il nostro metodo: https://k2-ai.it/metodo.html

© 2025 K2-AI
"""


def _build_email_body(name: str, email: str, company_role: Optional[str], message: str) -> tuple[str, str]:
    """Restituisce (html, text) per la mail di conferma."""
    name_safe = name[:80]
    message_preview = message[:400] + ("…" if len(message) > 400 else "")
    company_row = (
        f'<div class="detail-row"><span class="detail-label">Azienda</span>'
        f'<span class="detail-value">{company_role[:120]}</span></div>'
        if company_role
        else ""
    )
    company_line = f"Azienda: {company_role[:120]}\n" if company_role else ""

    html = _CONFIRMATION_HTML.format(
        name=name_safe,
        email=email[:160],
        company_row=company_row,
        message_preview=message_preview,
    )
    text = _CONFIRMATION_TEXT.format(
        name=name_safe,
        email=email[:160],
        company_line=company_line,
        message_preview=message_preview,
    )
    return html, text


# ── Provider: Resend ──────────────────────────────────────────────────────────

async def _send_via_resend(to_email: str, subject: str, html: str, text: str) -> None:
    from_addr = settings.email_from
    payload: dict = {
        "from": from_addr,
        "to": [to_email],
        "subject": subject,
        "html": html,
        "text": text,
    }
    if settings.email_reply_to:
        payload["reply_to"] = settings.email_reply_to

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Resend API error {resp.status_code}: {resp.text[:300]}")
    logger.info(f"Email conferma inviata via Resend a {to_email}")


# ── Provider: SMTP ────────────────────────────────────────────────────────────

def _send_via_smtp(to_email: str, subject: str, html: str, text: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to_email
    if settings.email_reply_to:
        msg["Reply-To"] = settings.email_reply_to

    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    context = ssl.create_default_context()
    smtp_user = settings.smtp_user or ""
    smtp_password = settings.smtp_password or ""

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        if settings.smtp_tls:
            server.starttls(context=context)
        if smtp_user:
            server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user or settings.email_from, [to_email], msg.as_bytes())

    logger.info(f"Email conferma inviata via SMTP a {to_email}")


# ── Interfaccia pubblica ──────────────────────────────────────────────────────

def email_configured() -> bool:
    """True se almeno un provider email è configurato."""
    has_resend = bool(settings.resend_api_key and settings.resend_api_key.strip())
    has_smtp = bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)
    return has_resend or has_smtp


async def send_confirmation_email(
    *,
    to_email: str,
    name: str,
    company_role: Optional[str] = None,
    message: str,
) -> bool:
    """
    Invia la mail di conferma al visitatore.
    Restituisce True se l'invio ha avuto successo, False altrimenti.
    Non solleva eccezioni — gli errori vengono loggati.
    """
    if not email_configured():
        logger.debug("Nessun provider email configurato — conferma saltata")
        return False

    subject = f"K2-AI — Messaggio ricevuto, {name.split()[0] if name else 'ciao'}"
    html, text = _build_email_body(name=name, email=to_email, company_role=company_role, message=message)

    # Prova Resend per primo
    if settings.resend_api_key and settings.resend_api_key.strip():
        try:
            await _send_via_resend(to_email, subject, html, text)
            return True
        except Exception as exc:
            logger.warning(f"Resend fallito ({exc}), provo SMTP…")

    # Fallback SMTP
    if settings.smtp_host and settings.smtp_user and settings.smtp_password:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _send_via_smtp, to_email, subject, html, text)
            return True
        except Exception as exc:
            logger.error(f"SMTP fallito: {exc}")

    return False
