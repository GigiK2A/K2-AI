"""POST /api/kbot/checkout — Stripe Checkout Session for premium report unlock.

Requires STRIPE_SECRET_KEY. If unset the endpoint returns 503 (not configured),
so that the rest of the system stays usable during development.
"""
from __future__ import annotations

import logging
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from ..lib import sessions
from ..lib.auth import AuthUser, optional_user
from ..settings import (
    FRONTEND_URL,
    REPORT_PRICE_EUR_CENTS,
    SITE_URL,
    STRIPE_API_VERSION,
    STRIPE_SECRET_KEY,
)

router = APIRouter()
log = logging.getLogger(__name__)


class CheckoutBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    email: Optional[EmailStr] = None

    class Config:
        populate_by_name = True


def _stripe_client() -> stripe:
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    stripe.api_key = STRIPE_SECRET_KEY
    if STRIPE_API_VERSION:
        stripe.api_version = STRIPE_API_VERSION
    return stripe


@router.post("/checkout")
def checkout(body: CheckoutBody, user: Optional[AuthUser] = Depends(optional_user)):
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    owner = session.get("user_id")
    if owner and (not user or user.id != owner):
        raise HTTPException(status_code=403, detail="not your session")

    if session.get("status") == "paid":
        raise HTTPException(status_code=409, detail="already paid")

    sclient = _stripe_client()

    # Capture email (prefer body > user > existing).
    email = (body.email or (user.email if user else None) or session.get("email") or "").strip() or None
    if email and email != session.get("email"):
        sessions.update_session(body.sessionId, {"email": email})

    return_base = FRONTEND_URL or SITE_URL
    success_url = f"{return_base}/?kbot_paid=1&session={body.sessionId}&cs={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{return_base}/?kbot_cancelled=1&session={body.sessionId}"

    try:
        checkout_session = sclient.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            client_reference_id=body.sessionId,
            metadata={"kbot_session_id": body.sessionId},
            customer_email=email,
            line_items=[
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": REPORT_PRICE_EUR_CENTS,
                        "product_data": {
                            "name": "Report operativo K2-AI",
                            "description": "Documento PDF con priorità, azioni operative, roadmap e KPI di misura.",
                        },
                    },
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except stripe.error.StripeError as exc:
        log.exception("Stripe error")
        raise HTTPException(status_code=502, detail=f"stripe error: {exc.user_message or str(exc)}")

    sessions.update_session(
        body.sessionId,
        {"stripe_session_id": checkout_session.id},
    )
    return {"checkout_url": checkout_session.url}
