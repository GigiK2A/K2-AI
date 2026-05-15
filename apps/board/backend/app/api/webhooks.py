"""Public webhook endpoints — NO auth (third parties cannot send our session cookie).

Currently only Stripe is wired up. Signature verification is enforced via the
Stripe SDK; idempotency relies on the `external_id` unique constraint of
`board_revenue_events`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional

import stripe
from fastapi import APIRouter, Header, HTTPException, Request

from app.db.client import get_supabase
from app.lib.logger import get_logger
from app.settings import get_settings

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

log = get_logger(__name__)

REVENUE_TABLE = "board_revenue_events"


def _from_unix(ts: Optional[int]) -> str:
    if ts is None:
        return datetime.now(tz=timezone.utc).isoformat()
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Read a field from either a plain dict or a Stripe StripeObject.

    Stripe SDK objects override attribute access but support item access.
    """
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    try:
        return obj[key]
    except (KeyError, TypeError):
        return default


def _to_jsonable(obj: Any) -> Any:
    """Best-effort conversion of Stripe SDK objects into plain JSON values."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    to_dict = getattr(obj, "to_dict_recursive", None)
    if callable(to_dict):
        return to_dict()
    if isinstance(obj, Mapping):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    return str(obj)


def _payment_intent_to_row(pi: Any, *, status: str) -> Dict[str, Any]:
    customer = _get(pi, "customer")
    return {
        "external_id": _get(pi, "id"),
        "amount_cents": int(_get(pi, "amount") or 0),
        "currency": (_get(pi, "currency") or "eur").lower(),
        "status": status,
        "occurred_at": _from_unix(_get(pi, "created")),
        "customer_email": _get(pi, "receipt_email"),
        "customer_id": customer if isinstance(customer, str) else None,
        "description": _get(pi, "description"),
        "raw": _to_jsonable(pi),
    }


def _charge_to_row(charge: Any, *, status: str) -> Dict[str, Any]:
    # Refund events come through as `charge.refunded` — we key on the underlying
    # payment_intent so the original row gets updated rather than duplicated.
    pi_id = _get(charge, "payment_intent") or _get(charge, "id")
    customer = _get(charge, "customer")
    billing = _get(charge, "billing_details") or {}
    return {
        "external_id": pi_id,
        "amount_cents": int(_get(charge, "amount") or 0),
        "currency": (_get(charge, "currency") or "eur").lower(),
        "status": status,
        "occurred_at": _from_unix(_get(charge, "created")),
        "customer_email": _get(charge, "receipt_email") or _get(billing, "email"),
        "customer_id": customer if isinstance(customer, str) else None,
        "description": _get(charge, "description"),
        "raw": _to_jsonable(charge),
    }


def _upsert_revenue(row: Dict[str, Any]) -> None:
    if not row.get("external_id"):
        log.warning("stripe.webhook.skip_no_external_id", extra={"row": row})
        return
    sb = get_supabase()
    sb.table(REVENUE_TABLE).upsert(row, on_conflict="external_id").execute()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(default=None, alias="Stripe-Signature"),
) -> Dict[str, Any]:
    settings = get_settings()
    secret = settings.stripe_webhook_secret
    if not secret:
        # Misconfiguration — refuse rather than silently accept unverified events.
        raise HTTPException(status_code=503, detail="stripe_webhook_secret_not_configured")
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="missing_signature")

    body = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=body, sig_header=stripe_signature, secret=secret
        )
    except (stripe.error.SignatureVerificationError, ValueError) as exc:  # type: ignore[attr-defined]
        log.warning("stripe.webhook.invalid_signature", extra={"err": str(exc)})
        raise HTTPException(status_code=400, detail="invalid_signature") from exc

    event_type = _get(event, "type")
    data_object = _get(_get(event, "data") or {}, "object") or {}

    log.info(
        "stripe.webhook.received",
        extra={"event_type": event_type, "event_id": _get(event, "id")},
    )

    if event_type == "payment_intent.succeeded":
        _upsert_revenue(_payment_intent_to_row(data_object, status="succeeded"))
    elif event_type == "payment_intent.payment_failed":
        _upsert_revenue(_payment_intent_to_row(data_object, status="failed"))
    elif event_type == "charge.refunded":
        _upsert_revenue(_charge_to_row(data_object, status="refunded"))
    else:
        # Acknowledge unknown events so Stripe doesn't retry forever.
        log.info("stripe.webhook.ignored", extra={"event_type": event_type})

    return {"ok": True}
