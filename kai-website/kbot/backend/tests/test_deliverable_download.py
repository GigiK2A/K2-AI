"""Regression: il download dei deliverable NON legge dal filesystem locale.

L'8e gira in un container Railway SEPARATO dal backend K-BOT: /tmp NON è condiviso.
Prima gli endpoint facevano os.path.isfile(outputs['pdf_path']) su un path del
container 8e → 404 sistematico su OGNI download in produzione (job 'rendered' ma
file irraggiungibile). Ora scaricano i byte via engine.fetch_output (HTTP).

Copre anche il routing Bug B: una diagnosi strategica di crescita deve instradare
su StrategyBoost (checkup_marketing), non su ControlBoost (checkup_controllo).
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("NEXT_PUBLIC_SUPABASE_URL", "https://x.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "x")
os.environ.setdefault("ANTHROPIC_API_KEY", "x")
os.environ.setdefault("K2A_ENTITLEMENT_SECRET", "test-secret-download")

import pytest  # noqa: E402
from fastapi import HTTPException  # noqa: E402

import app.api.deliverables as d  # noqa: E402
from app.lib import catalog  # noqa: E402


# ---- Bug B: routing strategia/crescita → StrategyBoost -----------------------

def test_diagnosi_strategica_routes_to_strategyboost():
    # Il riepilogo di una chat di crescita/posizionamento: prima finiva su
    # checkup_controllo (cruscotto direzionale) e il form chiedeva mese/costi_operativi.
    summary = {"reportType": "diagnosi strategica crescita",
               "objective": "diversificare clientela, entry nuovi mercati, espansione"}
    servizio = catalog.suggest_boost(summary)
    assert servizio and servizio.get("id") == "checkup_marketing", servizio


# ---- Bug A: download via HTTP, non da filesystem locale ----------------------

def _fake_fetch(content: bytes, ctype: str):
    async def _f(job_id, fmt="pdf"):
        _f.calls.append((job_id, fmt))
        return content, ctype
    _f.calls = []
    return _f


def _bypass_c1_gate(monkeypatch):
    """C1 — i download ora passano da _authorize_job_download (sessione+owner+
    pagamento) prima di fetch_output. Questi test isolano il BEHAVIOUR di download
    via HTTP: mockano il gate su una sessione PAGATA (l'auth C1 è coperta a parte in
    test_e2e/test_security). Senza mock il gate tenterebbe una query Supabase reale."""
    monkeypatch.setattr(
        d, "_authorize_job_download",
        lambda job_id, user: {"id": "sess-x", "status": "paid", "collected_data": {}},
    )


def test_pdf_download_streams_bytes_from_engine(monkeypatch):
    _bypass_c1_gate(monkeypatch)
    fetch = _fake_fetch(b"%PDF-1.4 fake", "application/pdf")
    monkeypatch.setattr(d.engine, "fetch_output", fetch)
    resp = asyncio.run(d.deliverable_pdf("job-x"))
    assert resp.body == b"%PDF-1.4 fake"
    assert resp.media_type == "application/pdf"
    assert fetch.calls == [("job-x", "pdf")]  # ha chiesto il PDF all'8e via HTTP


def test_pdf_download_404_when_engine_missing(monkeypatch):
    _bypass_c1_gate(monkeypatch)
    # C4 — su not_found l'endpoint prova la copia durevole su Storage: qui non c'è.
    monkeypatch.setattr(d, "download_bytes", lambda **kw: None)

    async def _f(job_id, fmt="pdf"):
        raise d.engine.EngineError("not_found")
    monkeypatch.setattr(d.engine, "fetch_output", _f)
    with pytest.raises(HTTPException) as ei:
        asyncio.run(d.deliverable_pdf("job-x"))
    assert ei.value.status_code == 404


def test_save_deliverable_rifiuta_job_di_un_altro(monkeypatch):
    """C1 — /deliverables/save passava solo da _check_ownership sulla sessione del
    BODY: con una sessione propria (anche anonima) + il job_id di un altro cliente
    si otteneva il suo PDF pagato, ricaricato sul proprio prefisso di storage e
    restituito come signed URL. Ora il job va risolto alla sessione che lo possiede.
    """
    # Il job appartiene alla sessione della vittima…
    monkeypatch.setattr(
        d, "_authorize_job_download",
        lambda job_id, user: {"id": "sess-vittima", "status": "paid", "collected_data": {}},
    )
    called = {"fetch": 0}

    async def _f(job_id, fmt="pdf"):
        called["fetch"] += 1
        return b"%PDF", "application/pdf"
    monkeypatch.setattr(d.engine, "fetch_output", _f)

    # …ma l'attaccante lo chiede indicando la PROPRIA sessione.
    body = d.SaveDeliverableBody(session_id="sess-attaccante", job_id="job_abcdef123456")
    with pytest.raises(HTTPException) as ei:
        asyncio.run(d.save_deliverable(body, None))
    assert ei.value.status_code == 403
    assert called["fetch"] == 0  # il PDF non è mai stato scaricato dall'8e


def test_save_deliverable_job_id_malformato_bloccato():
    """Il job_id di /save arriva dal BODY (non da un path param): può contenere `/`
    e `..` e finirebbe nell'URL verso l'8e e nella chiave di storage."""
    for bad in ("../../etc/passwd", "job_x/../../altro", "", "job_NONHEX"):
        with pytest.raises(HTTPException) as ei:
            d._authorize_job_download(bad, None)
        assert ei.value.status_code == 403


def test_xlsx_download_fetches_json_and_renders(monkeypatch):
    _bypass_c1_gate(monkeypatch)
    # deliverable minimale che il renderer xlsx sa gestire (nessun foglio obbligatorio).
    fetch = _fake_fetch(b'{"titolo":"X","sezioni":[]}', "application/json")
    monkeypatch.setattr(d.engine, "fetch_output", fetch)
    resp = asyncio.run(d.deliverable_xlsx("job-x"))
    assert fetch.calls == [("job-x", "json")]  # scarica il JSON, non un path locale
    assert resp.media_type == \
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert resp.body  # ha prodotto un workbook non vuoto
