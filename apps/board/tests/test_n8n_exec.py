"""n8n: verifica esecuzioni (partite? errori?)."""
from aios.sources import n8n


def test_list_executions_status(monkeypatch):
    monkeypatch.setattr(n8n, "_api", lambda m, p, **k: {"ok": True, "data": {"data": [
        {"id": "1", "workflowId": "w", "status": "success", "startedAt": "t1"},
        {"id": "2", "workflowId": "w", "finished": False, "stoppedAt": "t2"},  # → error
    ]}})
    r = n8n.list_executions("w")
    assert r["ok"] and r["totale"] == 2 and r["errori"] == 1
    assert r["esecuzioni"][0]["status"] == "success"
    assert r["esecuzioni"][1]["status"] == "error"


def test_list_executions_degrades_without_api(monkeypatch):
    monkeypatch.setattr(n8n, "_api", lambda m, p, **k: {"ok": False, "errore": "no api"})
    r = n8n.list_executions()
    assert r["ok"] is False and r["esecuzioni"] == []
