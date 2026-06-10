"""Compute layer universale: ~135 tool deterministici degli MCP ecosistema vendorizzati."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for k, v in {"NEXT_PUBLIC_SUPABASE_URL": "https://x.supabase.co", "SUPABASE_SERVICE_ROLE_KEY": "x",
             "ANTHROPIC_API_KEY": "x", "STRIPE_SECRET_KEY": "x", "INTERNAL_API_KEY": "x",
             "K2A_ENTITLEMENT_SECRET": "ci-secret-32bytes-minimum-length!"}.items():
    os.environ.setdefault(k, v)
from fastapi.testclient import TestClient
from app.main import app
from app.lib.auth import require_user, AuthUser
app.dependency_overrides[require_user] = lambda: AuthUser(id="test-user", email="t@t.it", has_paid=True, raw={})
c = TestClient(app)


def test_tools_listed():
    j = c.get("/api/kbot/tools").json()
    assert j["count"] >= 110
    # domini di CALCOLO presenti (norme-tecniche escluso: text-retrieval, serve DB)
    for d in ("agevolazioni", "finanza", "elettrico", "strutturale"):
        assert d in j["per_dominio"]


def test_dcf_compute():
    inp = {"fcf": [100000, 110000, 120000, 130000, 140000], "wacc": 0.10,
           "terminal_method": "gordon", "g_perpetual": 0.02, "net_debt": 50000}
    r = c.post("/api/kbot/tool/finanza/dcf.compute_dcf", json={"inputs": inp})
    assert r.status_code == 200
    assert r.json()["result"]["enterprise_value"] > 0


def test_validation_422():
    r = c.post("/api/kbot/tool/finanza/dcf.compute_dcf", json={"inputs": {"fcf": [1], "wacc": 0.1, "terminal_method": "X"}})
    assert r.status_code == 422


def test_unknown_404():
    assert c.post("/api/kbot/tool/x/y.z", json={"inputs": {}}).status_code == 404


if __name__ == "__main__":
    test_tools_listed(); test_dcf_compute(); test_validation_422(); test_unknown_404()
    print("COMPUTE TEST PASS (4/4)")
