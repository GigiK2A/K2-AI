"""Controlli di sicurezza dell'API: auth sui GET con dati, header, fail-closed."""
import pytest
from fastapi.testclient import TestClient

from aios.kernel import Kernel
from aios.api.app import create_app


def _client():
    return TestClient(create_app(Kernel(), platform=None))


def test_get_endpoints_require_auth_when_token_set(monkeypatch):
    monkeypatch.setenv("AIOS_API_TOKEN", "segreto-forte")
    c = _client()
    for path in ("/api/approvals", "/api/activity", "/api/insights",
                 "/api/deliverables", "/api/integrations", "/api/domain/finance"):
        r = c.get(path)
        assert r.status_code == 401, f"{path} non protetto (atteso 401, dato {r.status_code})"
        r2 = c.get(path, headers={"Authorization": "Bearer segreto-forte"})
        assert r2.status_code == 200, f"{path} rifiuta token valido"


def test_get_open_in_dev_without_token(monkeypatch):
    monkeypatch.delenv("AIOS_API_TOKEN", raising=False)
    c = _client()
    assert c.get("/api/approvals").status_code == 200  # dev locale: aperto


def test_wrong_token_rejected(monkeypatch):
    monkeypatch.setenv("AIOS_API_TOKEN", "giusto")
    c = _client()
    r = c.get("/api/approvals", headers={"Authorization": "Bearer sbagliato"})
    assert r.status_code == 401


def test_security_headers_present():
    c = _client()
    r = c.get("/api/overview")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"


def test_mutations_require_auth(monkeypatch):
    monkeypatch.setenv("AIOS_API_TOKEN", "k")
    c = _client()
    assert c.post("/api/approvals/1/approve", json={}).status_code == 401
    assert c.post("/api/agents/finance/run", json={}).status_code == 401
