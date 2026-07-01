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


def test_pdf_download_streams_bytes_from_engine(monkeypatch):
    fetch = _fake_fetch(b"%PDF-1.4 fake", "application/pdf")
    monkeypatch.setattr(d.engine, "fetch_output", fetch)
    resp = asyncio.run(d.deliverable_pdf("job-x"))
    assert resp.body == b"%PDF-1.4 fake"
    assert resp.media_type == "application/pdf"
    assert fetch.calls == [("job-x", "pdf")]  # ha chiesto il PDF all'8e via HTTP


def test_pdf_download_404_when_engine_missing(monkeypatch):
    async def _f(job_id, fmt="pdf"):
        raise d.engine.EngineError("not_found")
    monkeypatch.setattr(d.engine, "fetch_output", _f)
    with pytest.raises(HTTPException) as ei:
        asyncio.run(d.deliverable_pdf("job-x"))
    assert ei.value.status_code == 404


def test_xlsx_download_fetches_json_and_renders(monkeypatch):
    # deliverable minimale che il renderer xlsx sa gestire (nessun foglio obbligatorio).
    fetch = _fake_fetch(b'{"titolo":"X","sezioni":[]}', "application/json")
    monkeypatch.setattr(d.engine, "fetch_output", fetch)
    resp = asyncio.run(d.deliverable_xlsx("job-x"))
    assert fetch.calls == [("job-x", "json")]  # scarica il JSON, non un path locale
    assert resp.media_type == \
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert resp.body  # ha prodotto un workbook non vuoto
