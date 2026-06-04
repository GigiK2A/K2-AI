from fastapi.testclient import TestClient
from aios.kernel import Kernel
from aios.autonomy import ActionType, AutonomyLevel
from aios.tools import Tool
from aios.api.app import create_app

ACT = ActionType("marketing", "content.proposta")


def _kernel_one_pending():
    k = Kernel()
    k.register_tool(Tool(name="proponi_marketing", action_type=ACT, run=lambda **kw: kw))
    k.policy.set_level(ACT, AutonomyLevel.L1_PROPOSE); k.policy.set_cap(ACT, AutonomyLevel.L1_PROPOSE)
    k.execute("proponi_marketing", actor="a", args={"titolo": "T"})
    return k


def test_no_auth_required_when_token_unset(monkeypatch):
    monkeypatch.delenv("AIOS_API_TOKEN", raising=False)
    c = TestClient(create_app(_kernel_one_pending()))
    aid = c.get("/api/approvals").json()[0]["id"]
    assert c.post(f"/api/approvals/{aid}/reject", json={"reason": "x"}).json()["outcome"] == "DENIED"


def test_auth_enforced_when_token_set(monkeypatch):
    monkeypatch.setenv("AIOS_API_TOKEN", "secretXYZ")
    c = TestClient(create_app(_kernel_one_pending()))
    aid = c.get("/api/approvals").json()[0]["id"]
    # missing token -> 401
    assert c.post(f"/api/approvals/{aid}/reject", json={"reason": "x"}).status_code == 401
    # correct token -> ok
    r = c.post(f"/api/approvals/{aid}/reject", json={"reason": "x"},
               headers={"Authorization": "Bearer secretXYZ"})
    assert r.status_code == 200


def test_run_unknown_domain_is_generic(monkeypatch):
    monkeypatch.delenv("AIOS_API_TOKEN", raising=False)
    class FP:
        def domains(self): return ["marketing"]
        def run(self, d):
            raise KeyError(d)
        def deliverables(self): return []
    c = TestClient(create_app(Kernel(), platform=FP()))
    assert c.post("/api/agents/finance/run").json() == {"error": "dominio non valido"}
