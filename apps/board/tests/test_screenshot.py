"""Endpoint /api/screenshot (HTML→PNG per n8n): contratto + auth X-API-Key."""
from fastapi.testclient import TestClient

from aios.kernel import Kernel
from aios.api.app import create_app

_BODY = {"html": "<h1>test</h1>", "width": 1080, "height": 1350}


def _client():
    return TestClient(create_app(Kernel()))


def test_screenshot_missing_key_401(monkeypatch):
    monkeypatch.setenv("SCREENSHOT_API_KEY", "segreto")
    r = _client().post("/api/screenshot", json=_BODY)
    assert r.status_code == 401


def test_screenshot_wrong_key_401(monkeypatch):
    monkeypatch.setenv("SCREENSHOT_API_KEY", "segreto")
    r = _client().post("/api/screenshot", json=_BODY, headers={"X-API-Key": "sbagliata"})
    assert r.status_code == 401


def test_screenshot_no_env_key_401(monkeypatch):
    # senza SCREENSHOT_API_KEY configurata, nessuna chiave è valida → 401
    monkeypatch.delenv("SCREENSHOT_API_KEY", raising=False)
    r = _client().post("/api/screenshot", json=_BODY, headers={"X-API-Key": "qualcosa"})
    assert r.status_code == 401


def test_screenshot_good_key_passes_auth(monkeypatch):
    # chiave giusta → auth OK; senza Chromium (CI) il renderer non c'è → 503 (non 401).
    monkeypatch.setenv("SCREENSHOT_API_KEY", "segreto")
    r = _client().post("/api/screenshot", json=_BODY, headers={"X-API-Key": "segreto"})
    assert r.status_code in (200, 503)
    assert r.status_code != 401


def test_shots_mounted():
    # la cartella pubblica /shots è montata (file inesistente → 404, non 405/route assente)
    assert _client().get("/shots/inesistente.png").status_code == 404
