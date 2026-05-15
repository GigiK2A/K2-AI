"""Smoke tests — verify the app boots and the public meta endpoints answer."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_ok() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_root_returns_metadata() -> None:
    res = client.get("/")
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "k2-board-backend"


def test_protected_route_requires_auth() -> None:
    res = client.get("/api/leads/")
    assert res.status_code == 401


def test_auth_me_requires_auth() -> None:
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_openapi_lists_expected_resources() -> None:
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    # Spot-check one path per resource.
    for prefix in (
        "/api/auth/login",
        "/api/contacts/",
        "/api/leads/",
        "/api/tasks/",
        "/api/approvals/",
        "/api/memos/",
        "/api/meetings/",
        "/api/revenue/",
        "/api/overview/",
    ):
        assert prefix in paths, f"missing route: {prefix}"
