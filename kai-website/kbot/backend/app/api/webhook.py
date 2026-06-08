"""POST /api/stripe/webhook — Stripe payment confirmation.

Triggers the PDF generation server-to-server via the internal generate-pdf endpoint.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
import stripe
from fastapi import APIRouter, Header, HTTPException, Request

from ..lib import sessions
from ..lib.supabase_admin import get_admin_client
from ..settings import (
    INTERNAL_API_KEY,
    REPORT_PRICE_EUR_CENTS,
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
)

router = APIRouter()
log = logging.getLogger(__name__)


def _internal_pdf_url(request: Request) -> str:
    # Same host the webhook was hit on.
    base = str(request.base_url).rstrip("/")
    return f"{base}/api/kbot/generate-pdf"


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(default=None, alias="stripe-signature"),
):
    if not (STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET):
        raise HTTPException(status_code=503, detail="Stripe not configured")

    body = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=body,
            sig_header=stripe_signature or "",
            secret=STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        log.warning("Stripe signature verification failed: %s", exc)
        raise HTTPException(status_code=400, detail="invalid signature")

    if event["type"] != "checkout.session.completed":
        return {"ok": True, "ignored": event["type"]}

    # Stripe SDK >=10 restituisce StripeObject che NON è dict subclass: .get()
    # solleva AttributeError. Usiamo .to_dict() per ottenere un vero dict.
    raw_obj = event["data"]["object"]
    obj = raw_obj.to_dict() if hasattr(raw_obj, "to_dict") else dict(raw_obj)
    metadata = obj.get("metadata") or {}
    kbot_session_id = obj.get("client_reference_id") or metadata.get("kbot_session_id")
    if not kbot_session_id:
        log.warning("Webhook missing kbot_session_id")
        return {"ok": True, "skipped": "no session id"}

    session = sessions.get_session(kbot_session_id)
    if not session:
        log.warning("Webhook for unknown session %s", kbot_session_id)
        return {"ok": True, "skipped": "unknown session"}

    email = obj.get("customer_email") or session.get("email")

    # --- Boost (deliverable 8e): metadata.servizio_id presente ---------------
    # Marca paid (sblocca l'entitlement per il documento completo) + registra
    # l'acquisto. NON genera il report 19€.
    servizio_id = metadata.get("servizio_id")
    if servizio_id:
        sessions.update_session(kbot_session_id, {
            "email": email, "stripe_session_id": obj.get("id"),
            "paid_at": datetime.now(timezone.utc).isoformat(), "status": "paid",
        })
        try:
            from ..lib import catalog
            servizio = catalog.get_servizio(servizio_id) or {}
            get_admin_client().table("kbot_purchases").insert({
                "user_id": session.get("user_id"),
                "kbot_session_id": kbot_session_id,
                "servizio_id": servizio_id,
                "servizio_tipo": servizio.get("tipo") or "servizio",
                "prezzo_pagato_cents": obj.get("amount_total") or 0,
                "stripe_session_id": obj.get("id"),
                "status": "paid",
                "catalog_version": str(catalog.catalog_version()),
            }).execute()
        except Exception as exc:
            log.warning("Failed to record kbot_purchases: %s", exc)
        return {"ok": True, "boost": servizio_id}

    # Idempotency: skip if already paid or pdf already generated.
    if session.get("status") == "paid" or session.get("pdf_url"):
        return {"ok": True, "skipped": "already processed"}

    sessions.update_session(
        kbot_session_id,
        {
            "email": email,
            "stripe_session_id": obj.get("id"),
            "paid_at": datetime.now(timezone.utc).isoformat(),
            "status": "paid",
        },
    )

    # Mark user as paid on Supabase auth (if linked).
    user_id = session.get("user_id")
    if user_id:
        try:
            client = get_admin_client()
            # supabase-py admin update on app_metadata
            client.auth.admin.update_user_by_id(user_id, {"app_metadata": {"has_paid": True}})
        except Exception as exc:
            log.warning("Failed to set has_paid on user %s: %s", user_id, exc)

    # Log conversion.
    try:
        get_admin_client().table("kbot_conversions").insert(
            {
                "session_id": kbot_session_id,
                "type": "path_a_paid",
                "amount_eur": REPORT_PRICE_EUR_CENTS / 100.0,
                "stripe_session_id": obj.get("id"),
                "email": email,
            }
        ).execute()
    except Exception as exc:
        log.warning("Failed to log kbot_conversions: %s", exc)

    # Trigger PDF generation server-to-server.
    if INTERNAL_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                await client.post(
                    _internal_pdf_url(request),
                    headers={"x-internal-key": INTERNAL_API_KEY},
                    json={"session_id": kbot_session_id},
                )
        except Exception as exc:
            log.warning("PDF generation trigger failed: %s", exc)

    return {"ok": True}
