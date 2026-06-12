"""POST /api/kbot/checkout — Stripe Checkout Session for premium report unlock.

Requires STRIPE_SECRET_KEY. If unset the endpoint returns 503 (not configured),
so that the rest of the system stays usable during development.
"""
from __future__ import annotations

import logging
import secrets
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from ..lib import sessions, catalog, billing, billing_store
from ..lib.auth import AuthUser, optional_user, require_user
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


class BoostCheckoutBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    servizioId: str = Field(..., alias="servizio_id")
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
    # H-7: do NOT embed the kbot session UUID in success/cancel URLs — query
    # params leak to referrers, analytics pixels, browser history. Use Stripe's
    # built-in {CHECKOUT_SESSION_ID} placeholder and a short-lived opaque
    # success_token stored on the session, which the frontend exchanges for
    # the real session id server-side after redirect.
    success_token = secrets.token_urlsafe(24)
    sessions.update_session(body.sessionId, {"success_token": success_token})
    success_url = f"{return_base}/?kbot_paid=1&t={success_token}&cs={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{return_base}/?kbot_cancelled=1&t={success_token}"

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


@router.post("/checkout/boost")
def checkout_boost(body: BoostCheckoutBody, user: Optional[AuthUser] = Depends(optional_user)):
    """Checkout per un Boost: prezzo DAL CATALOGO (mai hardcoded). Il webhook usa
    `servizio_id` nei metadata per registrare l'acquisto e abilitare il documento."""
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    owner = session.get("user_id")
    if owner and (not user or user.id != owner):
        raise HTTPException(status_code=403, detail="not your session")

    servizio = catalog.get_servizio(body.servizioId)
    if not servizio:
        raise HTTPException(status_code=404, detail="servizio non a catalogo")
    prezzo_base = int(servizio.get("prezzo_eur", 0))
    if prezzo_base <= 0:
        raise HTTPException(status_code=409, detail="prezzo servizio non valido")
    # Sconto abbonato (leva L3): -10% Pro / -20% Business. Senza login = pieno.
    plan = billing_store.get_plan(user.id) if user else "free"
    prezzo_scontato = billing.prezzo_boost_scontato(prezzo_base, plan)
    prezzo_cents = prezzo_scontato * 100

    sclient = _stripe_client()
    email = (body.email or (user.email if user else None) or session.get("email") or "").strip() or None
    return_base = FRONTEND_URL or SITE_URL
    success_token = secrets.token_urlsafe(24)
    sessions.update_session(body.sessionId, {"success_token": success_token})
    success_url = f"{return_base}/?kbot_paid=1&t={success_token}&cs={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{return_base}/?kbot_cancelled=1&t={success_token}"

    try:
        checkout_session = sclient.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            client_reference_id=body.sessionId,
            metadata={"kbot_session_id": body.sessionId, "servizio_id": body.servizioId,
                      "plan": plan, "prezzo_base_eur": str(prezzo_base)},
            customer_email=email,
            line_items=[{
                "quantity": 1,
                "price_data": {
                    "currency": "eur",
                    "unit_amount": prezzo_cents,
                    "product_data": {
                        "name": servizio.get("label", body.servizioId),
                        "description": servizio.get("prodotto_commerciale") or "Deliverable K2-AI",
                    },
                },
            }],
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except stripe.error.StripeError as exc:
        log.exception("Stripe error (boost)")
        raise HTTPException(status_code=502, detail=f"stripe error: {exc.user_message or str(exc)}")

    sessions.update_session(body.sessionId, {"stripe_session_id": checkout_session.id})
    return {"checkout_url": checkout_session.url, "prezzo_eur": prezzo_scontato,
            "prezzo_base_eur": prezzo_base, "plan": plan,
            "sconto_pct": billing.sconto_boost_pct(plan)}


# ============================ Abbonamenti (ricorrente) ======================
class SubscriptionCheckoutBody(BaseModel):
    plan: str  # 'pro' | 'business'
    email: Optional[EmailStr] = None


@router.post("/checkout/subscription")
def checkout_subscription(body: SubscriptionCheckoutBody, user: AuthUser = Depends(require_user)):
    """Abbonamento ricorrente mensile (Pro/Business). Crediti mensili e sconti
    boost gestiti dal webhook su `customer.subscription` / invoice."""
    p = billing.piano(body.plan)
    if body.plan not in ("pro", "business") or p["prezzo_mese_eur"] <= 0:
        raise HTTPException(status_code=400, detail="piano non valido")
    sclient = _stripe_client()
    email = (body.email or user.email or "").strip() or None
    return_base = FRONTEND_URL or SITE_URL
    try:
        cs = sclient.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            client_reference_id=user.id,
            metadata={"user_id": user.id, "plan": body.plan, "kind": "subscription"},
            subscription_data={"metadata": {"user_id": user.id, "plan": body.plan}},
            customer_email=email,
            line_items=[{
                "quantity": 1,
                "price_data": {
                    "currency": "eur",
                    "recurring": {"interval": "month"},
                    "unit_amount": p["prezzo_mese_eur"] * 100,
                    "product_data": {"name": f"K2-AI {p['label']}",
                                     "description": f"{p['crediti_mese']} crediti/mese · -{p['sconto_boost_pct']}% sui Boost"},
                },
            }],
            success_url=f"{return_base}/app/dashboard?sub=1",
            cancel_url=f"{return_base}/app/dashboard?sub=cancelled",
        )
    except stripe.error.StripeError as exc:
        log.exception("Stripe error (subscription)")
        raise HTTPException(status_code=502, detail=f"stripe error: {exc.user_message or str(exc)}")
    return {"checkout_url": cs.url, "plan": body.plan, "prezzo_mese_eur": p["prezzo_mese_eur"]}


# ============================ Pacchetti crediti ============================
class CreditsCheckoutBody(BaseModel):
    prezzoEur: int = Field(..., alias="prezzo_eur")  # 49 | 199 | 499
    email: Optional[EmailStr] = None

    class Config:
        populate_by_name = True


@router.post("/checkout/credits")
def checkout_credits(body: CreditsCheckoutBody, user: AuthUser = Depends(require_user)):
    """Acquisto pacchetto crediti una-tantum. I crediti pagano i Check express."""
    pack = billing.pacchetto_crediti(body.prezzoEur)
    if not pack:
        raise HTTPException(status_code=400, detail="pacchetto crediti inesistente")
    sclient = _stripe_client()
    email = (body.email or user.email or "").strip() or None
    return_base = FRONTEND_URL or SITE_URL
    try:
        cs = sclient.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            client_reference_id=user.id,
            metadata={"user_id": user.id, "kind": "credits",
                      "crediti": str(pack["crediti"]), "prezzo_eur": str(pack["prezzo_eur"])},
            customer_email=email,
            line_items=[{
                "quantity": 1,
                "price_data": {
                    "currency": "eur",
                    "unit_amount": pack["prezzo_eur"] * 100,
                    "product_data": {"name": f"{pack['crediti']} crediti K2-AI",
                                     "description": "Crediti per i Check express (1 cr = 1€)."},
                },
            }],
            success_url=f"{return_base}/app/dashboard?credits=1",
            cancel_url=f"{return_base}/app/dashboard?credits=cancelled",
        )
    except stripe.error.StripeError as exc:
        log.exception("Stripe error (credits)")
        raise HTTPException(status_code=502, detail=f"stripe error: {exc.user_message or str(exc)}")
    return {"checkout_url": cs.url, "crediti": pack["crediti"], "prezzo_eur": pack["prezzo_eur"]}
