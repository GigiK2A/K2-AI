"""Handoff consulenza→generazione deliverable: trigger strutturato, stato persistente,
idempotenza, identità non bloccante (review flusso deliverable). I 10 casi A-J + il caso di
regressione e-commerce funnel. Mock ai CONFINI (Supabase/8e/autofill), nessun credito.
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("NEXT_PUBLIC_SUPABASE_URL", "https://x.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "x")
os.environ.setdefault("ANTHROPIC_API_KEY", "x")
os.environ.setdefault("K2A_ENTITLEMENT_SECRET", "test-secret-handoff")

import pytest  # noqa: E402
from fastapi import BackgroundTasks, HTTPException  # noqa: E402

import app.api.deliverables as d  # noqa: E402
from app.lib import summary_contract as SC  # noqa: E402
from app.lib import deliverable_state as DS  # noqa: E402


def _run(session_id="sess-h"):
    return asyncio.run(d.auto_deliverable(d.AutoBody(session_id=session_id),
                                          BackgroundTasks(), user=None))


def _setup(monkeypatch, collected, *, status="paid", inputs=None, create_calls=None):
    """Session con collected mutabile (update_session PERSISTE davvero → serve all'idempotenza)."""
    session = {"id": "sess-h", "user_id": None, "status": status, "collected_data": collected}

    def _update(sid, patch):
        if "collected_data" in patch:
            session["collected_data"] = patch["collected_data"]
        session.update({k: v for k, v in patch.items() if k != "collected_data"})
        return session

    async def fake_get_form(servizio_id):
        return {"campi": []}

    calls = create_calls if create_calls is not None else []

    async def fake_create(*, service_id, inputs, entitlement_token, tier, auth_level, case_facts=None):
        calls.append({"service_id": service_id, "auth_level": auth_level,
                      "ragione_sociale": inputs.get("ragione_sociale"),
                      "intestazione_assunta": inputs.get("_intestazione_assunta")})
        return {"job_id": f"job-{len(calls)}", "status": "routed"}

    monkeypatch.setattr(d.sessions, "get_session", lambda sid: session)
    monkeypatch.setattr(d.sessions, "update_session", _update)
    monkeypatch.setattr(d.engine, "get_form", fake_get_form)
    monkeypatch.setattr(d.engine, "create_deliverable", fake_create)
    monkeypatch.setattr(d, "_session_company", lambda s: None)
    monkeypatch.setattr(d.autofill, "extract_inputs",
                        lambda *a, **k: dict(inputs if inputs is not None else {"ragione_sociale": "ACME Srl"}))
    return session, calls


def _ed(**over):
    base = {"reportType": "analisi-funnel-e-commerce", "businessType": "ecommerce_arredamento",
            "objective": "capire il calo", "summary_version": "v-fixture",
            "generation": {"requested": True, "confirmedByUser": True, "requiredOutputs": ["pdf", "xlsx"]}}
    base.update(over)
    return base


# ── A — summary valido, utente confermato → UN solo job PDF+Excel ────────────────────────
def test_A_valid_confirmed_starts_one_job(monkeypatch):
    _, calls = _setup(monkeypatch, {"boost_suggerito": "checkup_marketing", "extractedData": _ed()})
    res = _run()
    assert res.get("job_id") and res.get("state") == DS.GENERATING
    assert len(calls) == 1                                   # un solo job


# ── B — summary valido, utente NON confermato (report_hold) → nessun job ─────────────────
def test_B_not_confirmed_hold_blocks_job(monkeypatch):
    _, calls = _setup(monkeypatch, {"boost_suggerito": "checkup_marketing",
                                    "report_hold": True, "extractedData": _ed()})
    with pytest.raises(HTTPException) as ei:
        _run()
    assert ei.value.status_code == 409
    assert ei.value.detail.get("reason") == "consulenza_aperta"
    assert len(calls) == 0                                   # nessun job


# ── C — valore parametrico "€X" non bloccante → generazione avviata ──────────────────────
def test_C_parametric_value_non_blocking(monkeypatch):
    # nota con un parametro da rendere editabile; identità mancante → PARTIAL, ma genera
    ed = _ed(notes="CPA medio €X (da stimare), margine medio ~%Y")
    _, calls = _setup(monkeypatch, {"boost_suggerito": "checkup_marketing", "extractedData": ed},
                      inputs={"obiettivo": "crescere"})   # niente ragione sociale
    res = _run()
    assert res.get("job_id")
    assert calls[0]["auth_level"] == "PARTIAL"
    assert calls[0]["intestazione_assunta"] is True         # identità assunta, non bloccante


# ── D — JSON non valido → INVALID_SUMMARY, nessun crash ──────────────────────────────────
def test_D_invalid_summary_no_crash():
    assert SC.validate_summary(["non", "un", "oggetto"])[0] is None
    assert SC.validate_summary("stringa")[0] is None
    from app.api.message import _apply_summary_contract
    c = {}
    _apply_summary_contract(c, "non-un-dict")               # non solleva
    assert DS.get_state(c) == DS.INVALID_SUMMARY


# ── E — doppia richiesta → un solo job (idempotenza) ─────────────────────────────────────
def test_E_double_request_single_job(monkeypatch):
    _, calls = _setup(monkeypatch, {"boost_suggerito": "checkup_marketing", "extractedData": _ed()})
    r1 = _run()
    r2 = _run()                                             # doppio click / retry
    assert len(calls) == 1                                  # UN solo job creato
    assert r2.get("idempotent") is True
    assert r2.get("job_id") == r1.get("job_id")


# ── F — PDF completato, Excel fallito → stato parziale, retry solo Excel ──────────────────
def test_F_partial_excel_failed_retry_only_excel():
    c = {}
    key = DS.idempotency_key("s", "v", ["pdf", "xlsx"])
    DS.mark_generating(c, key, ["pdf", "xlsx"])
    DS.set_output_status(c, "pdf", "rendered")
    DS.set_output_status(c, "xlsx", "failed")
    assert DS.reconcile_state(c) == DS.GENERATION_FAILED
    outs = DS.outputs_status(c)
    assert outs["pdf"] == "rendered" and outs["xlsx"] == "failed"   # solo xlsx da riprovare
    DS.set_output_status(c, "xlsx", "rendered")                     # retry riuscito
    assert DS.reconcile_state(c) == DS.COMPLETED


# ── G — refresh durante GENERATING → lo stato reale è persistente e recuperabile ─────────
def test_G_state_persistent_across_refresh():
    c = {}
    DS.mark_generating(c, DS.idempotency_key("s", "v", ["pdf"]), ["pdf"])
    c["deliverable_job_id"] = "job-x"
    # un "refresh" ricarica collected_data dal record → lo stato reale è ancora lì
    reloaded = dict(c)
    assert DS.get_state(reloaded) == DS.GENERATING
    assert reloaded.get("deliverable_job_id") == "job-x"


# ── H — output già completati → ritorna i file esistenti senza rigenerare ────────────────
def test_H_completed_returns_existing(monkeypatch):
    key = DS.idempotency_key("sess-h", "v-fixture", ["pdf", "xlsx"])
    collected = {"boost_suggerito": "checkup_marketing", "extractedData": _ed(),
                 "deliverable_state": DS.COMPLETED, "deliverable_idempotency_key": key,
                 "deliverable_job_id": "job-done",
                 "deliverable_outputs": {"pdf": "rendered", "xlsx": "rendered"}}
    _, calls = _setup(monkeypatch, collected)
    res = _run()
    assert res.get("idempotent") is True
    assert res.get("job_id") == "job-done"
    assert len(calls) == 0                                  # nessuna rigenerazione


# ── I — il modello scrive "scarica il deliverable" ma generation.requested=false → niente ─
def test_I_requested_false_no_generation(monkeypatch):
    ed = _ed(generation={"requested": False, "confirmedByUser": False, "requiredOutputs": ["pdf"]})
    _, calls = _setup(monkeypatch, {"boost_suggerito": "checkup_marketing", "extractedData": ed})
    with pytest.raises(HTTPException) as ei:
        _run()
    assert ei.value.status_code == 409
    assert ei.value.detail.get("reason") == "generation_not_requested"
    assert len(calls) == 0


# ── J — requested & confirmed true ma il testo non invita a generare → parte comunque ─────
def test_J_structured_trigger_independent_of_text(monkeypatch):
    # nessun "scarica"/"genera" nel testo: conta il PAYLOAD, non le parole
    ed = _ed(summary="Il calo si concentra sull'acquisizione a pagamento.",
             generation={"requested": True, "confirmedByUser": True, "requiredOutputs": ["pdf", "xlsx"]})
    _, calls = _setup(monkeypatch, {"boost_suggerito": "checkup_marketing", "extractedData": ed})
    res = _run()
    assert res.get("job_id") and len(calls) == 1


# ── REGRESSIONE — e-commerce funnel, utente confermato, SENZA nome azienda → PDF+Excel ───
def test_regression_ecommerce_funnel_generates(monkeypatch):
    """Dopo la validazione del summary la pipeline parte SENZA ulteriori domande, anche se
    manca la ragione sociale (identità non bloccante). Fixture del caso reale."""
    ed = _ed(
        reportType="analisi-funnel-e-commerce", businessType="ecommerce_arredamento",
        objective="spiegare il calo del 15% del fatturato",
        dataAvailable=("fatturato 2.8M; -15%; CR paid 2.3→1.7%; CR organico 2.6→2.4%; "
                       "AOV paid 142→137; ricorrenti 41→32%; annullamenti 3→7%; traffico stabile; "
                       "rimosso PayPal; spedizione mostrata tardi; mobile lento"),
        notes="AOV/CPA parametrici da rendere editabili nel modello Excel",
        summary_version="v-ecom-regr",
        generation={"requested": True, "confirmedByUser": True, "requiredOutputs": ["pdf", "xlsx"]})
    # NESSUNA ragione sociale né descrizione: autofill non la trova
    _, calls = _setup(monkeypatch, {"boost_suggerito": "checkup_seo", "extractedData": ed},
                      inputs={"obiettivo": "capire il calo"})
    res = _run()
    assert res.get("job_id"), "la generazione deve partire senza chiedere il nome azienda"
    assert res.get("state") == DS.GENERATING
    assert calls[0]["auth_level"] == "PARTIAL"              # PARTIAL con identità assunta
    assert calls[0]["intestazione_assunta"] is True
    assert len(calls) == 1                                  # un solo job (PDF+Excel dal bundle 8e)
