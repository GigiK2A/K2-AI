from fastapi.testclient import TestClient
from aios.kernel import Kernel
from aios.api.app import create_app


class FakePlatform:
    def __init__(self): self.ran = []
    def domains(self): return ["marketing", "vendite"]
    def run(self, domain):
        if domain not in ("marketing", "vendite"): raise KeyError(domain)
        self.ran.append(domain); return {"domain": domain, "proposte": 3, "calendario": 1}
    def deliverables(self): return [{"id": 1, "dominio": "vendite", "titolo": "Follow-up Mario"}]


def test_list_domains():
    c = TestClient(create_app(Kernel(), platform=FakePlatform()))
    assert c.get("/api/domini").json()["domini"] == ["marketing", "vendite"]


def test_run_agent():
    fp = FakePlatform()
    c = TestClient(create_app(Kernel(), platform=fp))
    r = c.post("/api/agents/marketing/run").json()
    assert r["proposte"] == 3 and fp.ran == ["marketing"]


def test_run_unknown_domain():
    c = TestClient(create_app(Kernel(), platform=FakePlatform()))
    assert c.post("/api/agents/finance/run").json() == {"error": "dominio non valido"}


def test_deliverables():
    c = TestClient(create_app(Kernel(), platform=FakePlatform()))
    assert c.get("/api/deliverables").json()[0]["dominio"] == "vendite"


def test_create_app_without_platform_still_works():
    c = TestClient(create_app(Kernel()))   # backward compat
    assert c.get("/api/domini").json()["domini"] == []
