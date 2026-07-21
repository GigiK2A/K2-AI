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
from fastapi import BackgroundTasks, HTTPException  # noqa: E402

import app.api.deliverables as d  # noqa: E402


def _setup(monkeypatch, *, status="paid", collected=None):
    session = {"id": "sess-int-1", "user_id": None, "status": status,
               "collected_data": collected or {}}

    async def fake_get_form(servizio_id):
        return {"campi": []}

    created = {}

    async def fake_create(*, service_id, inputs, entitlement_token, tier, auth_level, case_facts=None):
        created["service_id"] = service_id
        created["entitlement_present"] = bool(entitlement_token)
        return {"job_id": "job-int-1", "status": "routed"}

    monkeypatch.setattr(d.sessions, "get_session", lambda sid: session)
    monkeypatch.setattr(d.sessions, "update_session", lambda sid, patch: {**session, **patch})
    monkeypatch.setattr(d.engine, "get_form", fake_get_form)
    monkeypatch.setattr(d.engine, "create_deliverable", fake_create)
    # identità presente (sessione reale ha un nome dalla chat): così questi test esercitano
    # routing/paywall senza inciampare nel pre-flight needs_input (campi form vuoti = nessun
    # required mancante). I casi senza identità/required hanno i loro test dedicati.
    monkeypatch.setattr(d.autofill, "extract_inputs", lambda *a, **k: {"ragione_sociale": "ACME Srl"})
    return created


def test_marketing_conversation_routes_to_strategyboost_not_legaldd(monkeypatch):
    # riepilogo di una chat di marketing (col termine 'acquisizione clienti' che
    # prima dirottava su LegalBoost DD) — niente boost_suggerito → routing nell'endpoint
    collected = {"extractedData": {"reportType": "analisi marketing",
                                   "objective": "brand awareness, acquisizione clienti",
                                   "scope": "edilizia, rinnovabili, tlc"}}
    created = _setup(monkeypatch, status="paid", collected=collected)
    res = asyncio.run(d.auto_deliverable(d.AutoBody(session_id="sess-int-1"), BackgroundTasks(), user=None))
    assert res["servizio_id"] == "checkup_marketing", res
    assert created["service_id"] == "checkup_marketing"
    assert created["entitlement_present"] is True  # sessione paid → entitlement mintato


def test_unpaid_session_returns_402_checkout(monkeypatch):
    collected = {"extractedData": {"reportType": "analisi marketing", "objective": "awareness"}}
    _setup(monkeypatch, status="active", collected=collected)  # NON paid
    with pytest.raises(HTTPException) as ei:
        asyncio.run(d.auto_deliverable(d.AutoBody(session_id="sess-int-1"), BackgroundTasks(), user=None))
    assert ei.value.status_code == 402
    assert ei.value.detail.get("reason") == "payment_required"
    assert ei.value.detail.get("servizio_id") == "checkup_marketing"


def test_advisor_routing_blocked_non_vendibile(monkeypatch):
    # se l'intento spinge su una valutazione strategica, il routing NON sceglie
    # checkup_advisor (gated): il fallback e checkup_controllo (vendibile).
    collected = {"extractedData": {"reportType": "strategia e crescita",
                                   "objective": "business plan, espansione"}}
    created = _setup(monkeypatch, status="paid", collected=collected)
    res = asyncio.run(d.auto_deliverable(d.AutoBody(session_id="sess-int-1"), BackgroundTasks(), user=None))
    assert res["servizio_id"] != "checkup_advisor"  # mai l'advisor gated
    assert created["service_id"] == res["servizio_id"]


def test_missing_non_identity_field_generates_preliminary(monkeypatch):
    """Nuovo contratto: se manca un campo OBBLIGATORIO non-identità (e la ricerca web non
    l'ha riempito), NON si blocca più con 409 → si genera un REPORT PRELIMINARE
    (auth_level=PARTIAL): il cliente non esce mai a mani vuote (a pagamento come il completo).
    Il campo mancante diventa ipotesi etichettata, non un vicolo cieco."""
    collected = {"boost_suggerito": "checkup_marketing",
                 "extractedData": {"reportType": "analisi marketing", "objective": "awareness"}}
    session = {"id": "sess-int-1", "user_id": None, "status": "paid", "collected_data": collected}

    async def fake_get_form(servizio_id):
        return {"campi": [{"id": "obiettivo_strategico", "obbligatorio": True,
                           "label": "cosa vuole ottenere nei prossimi 1-3 anni"}]}

    created = {}

    async def fake_create(*, service_id, inputs, entitlement_token, tier, auth_level, case_facts=None):
        created["service_id"] = service_id
        created["auth_level"] = auth_level
        return {"job_id": "job-partial-1", "status": "routed"}

    monkeypatch.setattr(d.sessions, "get_session", lambda sid: session)
    monkeypatch.setattr(d.sessions, "update_session", lambda sid, patch: {**session, **patch})
    monkeypatch.setattr(d.engine, "get_form", fake_get_form)
    monkeypatch.setattr(d.engine, "create_deliverable", fake_create)
    # autofill estrae solo la ragione sociale; il required `obiettivo_strategico` resta assente.
    monkeypatch.setattr(d.autofill, "extract_inputs", lambda *a, **k: {"ragione_sociale": "ACME Srl"})

    res = asyncio.run(d.auto_deliverable(d.AutoBody(session_id="sess-int-1"), BackgroundTasks(), user=None))
    assert res["job_id"] == "job-partial-1"
    assert created["auth_level"] == "PARTIAL"   # generato in modalità preliminare, non 409


def test_all_required_present_proceeds_to_generation(monkeypatch):
    """Contro-prova: con i required presenti il pre-flight NON blocca e si genera."""
    collected = {"boost_suggerito": "checkup_marketing"}
    session = {"id": "sess-int-1", "user_id": None, "status": "paid", "collected_data": collected}

    async def fake_get_form(servizio_id):
        return {"campi": [{"id": "obiettivo_strategico", "obbligatorio": True, "label": "obiettivo"}]}

    created = {}

    async def fake_create(*, service_id, inputs, entitlement_token, tier, auth_level, case_facts=None):
        created["service_id"] = service_id
        return {"job_id": "job-int-2", "status": "routed"}

    monkeypatch.setattr(d.sessions, "get_session", lambda sid: session)
    monkeypatch.setattr(d.sessions, "update_session", lambda sid, patch: {**session, **patch})
    monkeypatch.setattr(d.engine, "get_form", fake_get_form)
    monkeypatch.setattr(d.engine, "create_deliverable", fake_create)
    monkeypatch.setattr(d.autofill, "extract_inputs",
                        lambda *a, **k: {"ragione_sociale": "ACME Srl", "obiettivo_strategico": "crescere del 30%"})

    res = asyncio.run(d.auto_deliverable(d.AutoBody(session_id="sess-int-1"), BackgroundTasks(), user=None))
    assert res["job_id"] == "job-int-2"
    assert created["service_id"] == "checkup_marketing"


def test_missing_identity_non_blocking_generates_partial(monkeypatch):
    """NUOVO contratto (review flusso deliverable): l'identità è personalizzazione, non un
    dato diagnostico → NON blocca più con 409. Si genera un PARTIAL con un placeholder
    DICHIARATO come assunzione (editabile), così 'utente ha confermato in chat' basta a
    produrre il deliverable senza una seconda domanda (caso di regressione)."""
    collected = {"boost_suggerito": "checkup_marketing",
                 "extractedData": {"businessType": "ecommerce_arredamento"}}
    session = {"id": "sess-int-1", "user_id": None, "status": "paid", "collected_data": collected}

    async def fake_get_form(servizio_id):
        return {"campi": [{"id": "obiettivo", "obbligatorio": True, "label": "obiettivo"}]}

    created = {}

    async def fake_create(*, service_id, inputs, entitlement_token, tier, auth_level, case_facts=None):
        created["service_id"] = service_id
        created["auth_level"] = auth_level
        created["ragione_sociale"] = inputs.get("ragione_sociale")
        created["intestazione_assunta"] = inputs.get("_intestazione_assunta")
        return {"job_id": "job-partial-id", "status": "routed"}

    monkeypatch.setattr(d.sessions, "get_session", lambda sid: session)
    monkeypatch.setattr(d.sessions, "update_session", lambda sid, patch: {**session, **patch})
    monkeypatch.setattr(d.engine, "get_form", fake_get_form)
    monkeypatch.setattr(d.engine, "create_deliverable", fake_create)
    monkeypatch.setattr(d, "_session_company", lambda s: None)  # nessun nome recuperabile
    # required presente, ma NESSUNA ragione sociale / descrizione → identità mancante
    monkeypatch.setattr(d.autofill, "extract_inputs", lambda *a, **k: {"obiettivo": "crescere"})

    res = asyncio.run(d.auto_deliverable(d.AutoBody(session_id="sess-int-1"), BackgroundTasks(), user=None))
    # NON 409: la generazione parte
    assert res["job_id"] == "job-partial-id"
    assert created["auth_level"] == "PARTIAL"
    assert created["intestazione_assunta"] is True
    # placeholder derivato dal businessType (non un dato inventato: assunzione etichettata)
    assert created["ragione_sociale"] and created["ragione_sociale"].lower() != "acme srl"


def test_required_fields_hint_injected_into_chat_prompt():
    """Part 3 — il prompt della chat espone i campi obbligatori del boost instradato,
    così il bot li raccoglie PRIMA di dichiararsi pronto (prevenzione)."""
    from app.lib.prompts import build_system_prompt_v2
    session = {"id": "s1", "collected_data": {}}
    base = build_system_prompt_v2([], session)
    with_hint = build_system_prompt_v2([], session,
                                       required_fields_hint="\nCAMPI OBBLIGATORI SENTINELLA_XYZ\n")
    assert "SENTINELLA_XYZ" not in base
    assert "SENTINELLA_XYZ" in with_hint


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
