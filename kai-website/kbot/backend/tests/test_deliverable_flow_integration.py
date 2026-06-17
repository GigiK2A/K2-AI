"""Integrazione del flusso /deliverables/auto: routing → gate entitlement →
chiamata motore → risposta, mockato ai CONFINI (Supabase/8e/autofill). Valida che
i pezzi lavorino INSIEME senza crediti: il bug 'marketing→LegalBoost DD' non passa
piu nemmeno attraverso l'endpoint, il paywall gate, e l'advisor resta non-vendibile.
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("NEXT_PUBLIC_SUPABASE_URL", "https://x.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "x")
os.environ.setdefault("ANTHROPIC_API_KEY", "x")
os.environ.setdefault("K2A_ENTITLEMENT_SECRET", "test-secret-integration")

import pytest  # noqa: E402
from fastapi import HTTPException  # noqa: E402

import app.api.deliverables as d  # noqa: E402


def _setup(monkeypatch, *, status="paid", collected=None):
    session = {"id": "sess-int-1", "user_id": None, "status": status,
               "collected_data": collected or {}}

    async def fake_get_form(servizio_id):
        return {"campi": []}

    created = {}

    async def fake_create(*, service_id, inputs, entitlement_token, tier, auth_level):
        created["service_id"] = service_id
        created["entitlement_present"] = bool(entitlement_token)
        return {"job_id": "job-int-1", "status": "routed"}

    monkeypatch.setattr(d.sessions, "get_session", lambda sid: session)
    monkeypatch.setattr(d.sessions, "update_session", lambda sid, patch: {**session, **patch})
    monkeypatch.setattr(d.engine, "get_form", fake_get_form)
    monkeypatch.setattr(d.engine, "create_deliverable", fake_create)
    monkeypatch.setattr(d.autofill, "extract_inputs", lambda *a, **k: {})
    return created


def test_marketing_conversation_routes_to_strategyboost_not_legaldd(monkeypatch):
    # riepilogo di una chat di marketing (col termine 'acquisizione clienti' che
    # prima dirottava su LegalBoost DD) — niente boost_suggerito → routing nell'endpoint
    collected = {"extractedData": {"reportType": "analisi marketing",
                                   "objective": "brand awareness, acquisizione clienti",
                                   "scope": "edilizia, rinnovabili, tlc"}}
    created = _setup(monkeypatch, status="paid", collected=collected)
    res = asyncio.run(d.auto_deliverable(d.AutoBody(session_id="sess-int-1"), user=None))
    assert res["servizio_id"] == "checkup_marketing", res
    assert created["service_id"] == "checkup_marketing"
    assert created["entitlement_present"] is True  # sessione paid → entitlement mintato


def test_unpaid_session_returns_402_checkout(monkeypatch):
    collected = {"extractedData": {"reportType": "analisi marketing", "objective": "awareness"}}
    _setup(monkeypatch, status="active", collected=collected)  # NON paid
    with pytest.raises(HTTPException) as ei:
        asyncio.run(d.auto_deliverable(d.AutoBody(session_id="sess-int-1"), user=None))
    assert ei.value.status_code == 402
    assert ei.value.detail.get("reason") == "payment_required"
    assert ei.value.detail.get("servizio_id") == "checkup_marketing"


def test_advisor_routing_blocked_non_vendibile(monkeypatch):
    # se l'intento spinge su una valutazione strategica, il routing NON sceglie
    # checkup_advisor (gated): il fallback e checkup_controllo (vendibile).
    collected = {"extractedData": {"reportType": "strategia e crescita",
                                   "objective": "business plan, espansione"}}
    created = _setup(monkeypatch, status="paid", collected=collected)
    res = asyncio.run(d.auto_deliverable(d.AutoBody(session_id="sess-int-1"), user=None))
    assert res["servizio_id"] != "checkup_advisor"  # mai l'advisor gated
    assert created["service_id"] == res["servizio_id"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
