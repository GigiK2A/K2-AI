"""Tests for the Stripe webhook endpoint.

We stub Supabase entirely (the route is the unit under test) and forge a
signed payload the way Stripe itself does so signature verification runs
through the real SDK path.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.settings import get_settings

WEBHOOK_SECRET = "whsec_test_secret_for_unit_tests_only"


def _sign(payload: str, secret: str, timestamp: int | None = None) -> str:
    ts = timestamp or int(time.time())
    signed = f"{ts}.{payload}"
    sig = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


@pytest.fixture(autouse=True)
def _override_settings():
    """Force a known webhook secret into the cached Settings singleton."""
    settings = get_settings()
    original = settings.stripe_webhook_secret
    object.__setattr__(settings, "stripe_webhook_secret", WEBHOOK_SECRET)
    try:
        yield
    finally:
        object.__setattr__(settings, "stripe_webhook_secret", original)


class _FakeSupabase:
    """Captures upsert calls; ignores everything else."""

    def __init__(self) -> None:
        self.upserts: List[Dict[str, Any]] = []

    def table(self, _name: str) -> "_FakeSupabase":
        return self

    def upsert(self, row: Dict[str, Any], on_conflict: str | None = None) -> "_FakeSupabase":
        # Idempotency in the real DB is enforced by the unique key; we simulate
        # it here by de-duplicating on `external_id`.
        existing = next(
            (r for r in self.upserts if r.get("external_id") == row.get("external_id")),
            None,
        )
        if existing is not None:
            existing.update(row)
        else:
            self.upserts.append(dict(row))
        return self

    def execute(self) -> MagicMock:
        return MagicMock(data=[])


def _payment_intent_payload(*, event_id: str = "evt_1", pi_id: str = "pi_123") -> Dict[str, Any]:
    return {
        "id": event_id,
        "object": "event",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": pi_id,
                "object": "payment_intent",
                "amount": 1900,
                "currency": "eur",
                "status": "succeeded",
                "created": 1_700_000_000,
                "receipt_email": "luigi@example.com",
                "customer": "cus_abc",
                "description": "K-BOT Tier 0",
            }
        },
    }


def test_invalid_signature_returns_400() -> None:
    client = TestClient(app)
    payload = json.dumps(_payment_intent_payload())
    res = client.post(
        "/api/webhooks/stripe",
        content=payload,
        headers={"Stripe-Signature": "t=1,v1=deadbeef"},
    )
    assert res.status_code == 400


def test_payment_intent_succeeded_upserts_row() -> None:
    fake = _FakeSupabase()
    payload = json.dumps(_payment_intent_payload())
    signature = _sign(payload, WEBHOOK_SECRET)

    with patch("app.api.webhooks.get_supabase", return_value=fake):
        client = TestClient(app)
        res = client.post(
            "/api/webhooks/stripe",
            content=payload,
            headers={"Stripe-Signature": signature},
        )

    assert res.status_code == 200
    assert res.json() == {"ok": True}
    assert len(fake.upserts) == 1
    row = fake.upserts[0]
    assert row["external_id"] == "pi_123"
    assert row["amount_cents"] == 1900
    assert row["status"] == "succeeded"
    assert row["customer_email"] == "luigi@example.com"


def test_idempotent_same_event_only_one_row() -> None:
    fake = _FakeSupabase()
    payload = json.dumps(_payment_intent_payload(event_id="evt_dup", pi_id="pi_dup"))
    signature = _sign(payload, WEBHOOK_SECRET)

    with patch("app.api.webhooks.get_supabase", return_value=fake):
        client = TestClient(app)
        for _ in range(2):
            res = client.post(
                "/api/webhooks/stripe",
                content=payload,
                headers={"Stripe-Signature": _sign(payload, WEBHOOK_SECRET)},
            )
            assert res.status_code == 200

    assert len(fake.upserts) == 1
    assert fake.upserts[0]["external_id"] == "pi_dup"
    _ = signature  # silence unused
