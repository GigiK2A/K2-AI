"""Connettori esterni: senza credenziali devono degradare a [] (graceful),
mai sollevare. Telegram no-op senza token. Endpoint integrazioni elenca lo stato."""
import os

import pytest

from aios.sources.connectors import all_connectors, CONNECTOR_ENV
from aios.notify import telegram


ALL_ENV = sorted({e for envs in CONNECTOR_ENV.values() for e in envs} |
                 {"TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "COMPETITOR_URLS"})


@pytest.fixture
def no_creds(monkeypatch):
    for e in ALL_ENV:
        monkeypatch.delenv(e, raising=False)
    yield


def test_every_connector_returns_empty_without_creds(no_creds):
    tools = all_connectors()
    assert tools, "nessun connettore registrato"
    for t in tools:
        out = t.run()
        assert out == [], f"{t.name} non degrada a [] senza credenziali (ha dato {out!r})"


def test_connectors_are_readonly_no_action():
    for t in all_connectors():
        assert t.readonly is True
        assert t.action_type is None  # solo lettura, nessuna azione che muta stato


def test_connector_env_map_covers_tool_names():
    names = {t.name for t in all_connectors()}
    # ogni tool (tranne eventuali extra) ha la sua mappa env per il pannello Settings
    for n in names:
        assert n in CONNECTOR_ENV, f"manca CONNECTOR_ENV per {n}"


def test_telegram_disabled_without_token(no_creds):
    assert telegram.enabled() is False
    # nessuna di queste deve sollevare quando disabilitato
    telegram.send_text("ciao")
    telegram.send_approval_card(1, "t", "b")
    telegram.poll_decisions(lambda x: None, lambda x: None, once=True)


def test_integrations_endpoint_lists_status():
    from aios.kernel import Kernel
    from aios.api.app import create_app
    from fastapi.testclient import TestClient
    app = create_app(Kernel(), platform=None)
    r = TestClient(app).get("/api/integrations")
    assert r.status_code == 200
    data = r.json()
    names = {d["nome"] for d in data}
    assert "Stripe (ricavi)" in names and "Telegram" in names
    assert all("connesso" in d and "env" in d for d in data)
