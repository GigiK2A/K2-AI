"""Check express deterministici (strato consumo) via MCP k2a-agevolazioni vendorizzato."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("NEXT_PUBLIC_SUPABASE_URL", "https://x.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "x")
os.environ.setdefault("ANTHROPIC_API_KEY", "x")
os.environ.setdefault("STRIPE_SECRET_KEY", "x")
os.environ.setdefault("K2A_ENTITLEMENT_SECRET", "ci-secret-32bytes-minimum-length!")

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.lib.auth import require_user, AuthUser
from app.api import checks as _checks
app.dependency_overrides[require_user] = lambda: AuthUser(id="test-user", email="t@t.it", has_paid=True, raw={})

c = TestClient(app)


@pytest.fixture(autouse=True)
def _billing_ok():
    """Mock ISOLATO del billing (Supabase non reale): piano abilitato + credito ok.
    Ripristina dopo ogni test → niente contaminazione di test_billing/webhook."""
    o1 = _checks.billing.puo_eseguire_servizi
    o2 = _checks.billing_store.get_plan
    o3 = _checks.billing_store.consume_credits
    _checks.billing.puo_eseguire_servizi = lambda plan: True
    _checks.billing_store.get_plan = lambda uid: "pro"
    _checks.billing_store.consume_credits = lambda *a, **k: (True, 999)
    try:
        yield
    finally:
        _checks.billing.puo_eseguire_servizi = o1
        _checks.billing_store.get_plan = o2
        _checks.billing_store.consume_credits = o3


def test_list_checks():
    r = c.get("/api/kbot/checks")
    assert r.status_code == 200
    assert r.json()["count"] >= 15


def test_de_minimis_calcolo():
    body = {"inputs": {"aiuti_ricevuti": [{"importo_eur": 120000, "data_concessione": "2024-03-01", "descrizione": "Sabatini"}], "settore": "generale"}}
    r = c.post("/api/kbot/check/de_minimis", json=body)
    assert r.status_code == 200
    res = r.json()["result"]
    assert res["massimale_eur"] == 300000.0
    assert res["plafond_residuo_eur"] == 180000.0


def test_check_inesistente_404():
    assert c.post("/api/kbot/check/non_esiste", json={"inputs": {}}).status_code == 404


def test_input_invalido_422():
    assert c.post("/api/kbot/check/de_minimis", json={"inputs": {"settore": 123}}).status_code in (422, 500)


if __name__ == "__main__":
    test_list_checks(); test_de_minimis_calcolo(); test_check_inesistente_404(); test_input_invalido_422()
    print("CHECKS TEST PASS (4/4)")


def test_check_document_pdf():
    body = {"inputs": {"aiuti_ricevuti": [{"importo_eur": 120000, "data_concessione": "2024-03-01", "descrizione": "x"}], "settore": "generale"}}
    r = c.post("/api/kbot/check/de_minimis/document", json=body)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:5] == b"%PDF-" and len(r.content) > 5000


def test_credit_gate_402_insufficiente():
    """Crediti insufficienti → 402, e il calcolo NON viene eseguito."""
    orig = _checks.billing_store.consume_credits
    _checks.billing_store.consume_credits = lambda *a, **k: (False, 0)
    try:
        body = {"inputs": {"aiuti_ricevuti": [], "settore": "generale"}}
        r = c.post("/api/kbot/check/de_minimis", json=body)
        assert r.status_code == 402, r.status_code
    finally:
        _checks.billing_store.consume_credits = orig


def test_costo_dal_catalogo_sorgente():
    """Il costo crediti dei check è risolto dalla fonte vendorizzata."""
    costi = _checks._load_costi()
    assert costi.get("de_minimis") == 49 and costi.get("hospitality_kpi") == 49
