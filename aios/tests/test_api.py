from fastapi.testclient import TestClient

from aios.kernel import Kernel
from aios.autonomy import ActionType, AutonomyLevel
from aios.tools import Tool
from aios.api.app import create_app

ACT = ActionType("marketing", "content.proposta")


def _kernel_with_one_pending():
    k = Kernel()
    calls = []
    k.register_tool(Tool(name="proponi_marketing", action_type=ACT,
                         run=lambda **kw: calls.append(kw) or {"ok": True}))
    k.policy.set_level(ACT, AutonomyLevel.L1_PROPOSE)
    k.policy.set_cap(ACT, AutonomyLevel.L1_PROPOSE)
    k.execute("proponi_marketing", actor="marketing_agent",
              args={"tipo": "caption", "titolo": "T", "contenuto": "C", "motivo": "M"})
    return k, calls


def test_overview_counts():
    k, _ = _kernel_with_one_pending()
    c = TestClient(create_app(k))
    r = c.get("/api/overview").json()
    assert r["pending_count"] == 1
    assert r["audit_count"] >= 1


def test_list_approvals():
    k, _ = _kernel_with_one_pending()
    c = TestClient(create_app(k))
    items = c.get("/api/approvals").json()
    assert len(items) == 1
    assert items[0]["payload"]["titolo"] == "T"
    assert items[0]["status"] == "PENDING"


def test_approve_runs_and_clears():
    k, calls = _kernel_with_one_pending()
    c = TestClient(create_app(k))
    aid = c.get("/api/approvals").json()[0]["id"]
    r = c.post(f"/api/approvals/{aid}/approve", json={})
    assert r.json()["outcome"] == "EXECUTED"
    assert calls == [{"tipo": "caption", "titolo": "T", "contenuto": "C", "motivo": "M"}]
    assert c.get("/api/approvals").json() == []


def test_reject_does_not_run():
    k, calls = _kernel_with_one_pending()
    c = TestClient(create_app(k))
    aid = c.get("/api/approvals").json()[0]["id"]
    r = c.post(f"/api/approvals/{aid}/reject", json={"reason": "off-brand"})
    assert r.json()["outcome"] == "DENIED"
    assert calls == []
    assert c.get("/api/approvals").json() == []


def test_edit_then_approve_uses_edited_payload():
    k, calls = _kernel_with_one_pending()
    c = TestClient(create_app(k))
    aid = c.get("/api/approvals").json()[0]["id"]
    c.post(f"/api/approvals/{aid}/approve",
           json={"edited_payload": {"tipo": "caption", "titolo": "T2"}})
    assert calls == [{"tipo": "caption", "titolo": "T2"}]


def test_root_serves_cockpit_html():
    k, _ = _kernel_with_one_pending()
    c = TestClient(create_app(k))
    r = c.get("/")
    assert r.status_code == 200 and "AI Operating System" in r.text
