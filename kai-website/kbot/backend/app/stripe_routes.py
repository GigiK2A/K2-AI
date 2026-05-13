from __future__ import annotations

import os

import httpx
import stripe
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

import app.auth as _auth
from app.auth import extract_token_from_header

router = APIRouter()


def _get_stripe():
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    return stripe


@router.post("/api/stripe/checkout")
async def create_checkout(authorization: str | None = Header(None)):
    token = extract_token_from_header(authorization)
    user = _auth.extract_clerk_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Login richiesto")
    if user.has_paid:
        raise HTTPException(status_code=400, detail="Hai già accesso ai download")

    price_id = os.getenv("STRIPE_PRICE_ID", "")
    if not price_id:
        raise HTTPException(status_code=500, detail="Stripe non configurato")

    _get_stripe()
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{frontend_url}?payment=success",
        cancel_url=f"{frontend_url}?payment=cancelled",
        metadata={"clerk_user_id": user.clerk_user_id},
    )
    return JSONResponse({"url": session.url})


@router.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        _get_stripe()
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except stripe.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Firma webhook non valida")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        clerk_user_id = session.get("metadata", {}).get("clerk_user_id")
        if clerk_user_id:
            clerk_secret = os.getenv("CLERK_SECRET_KEY", "")
            async with httpx.AsyncClient() as c:
                await c.patch(
                    f"https://api.clerk.com/v1/users/{clerk_user_id}/metadata",
                    headers={"Authorization": f"Bearer {clerk_secret}"},
                    json={"public_metadata": {"has_paid": True}},
                )

    return JSONResponse({"received": True})
