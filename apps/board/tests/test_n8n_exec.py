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


def test_workflow_webhook_url_from_definition(monkeypatch):
    monkeypatch.setenv("N8N_API_URL", "https://n8n.example.com/api/v1")
    monkeypatch.setattr(n8n, "get_workflow", lambda wid: {"nodes": [
        {"type": "n8n-nodes-base.scheduleTrigger", "parameters": {}},
        {"type": "n8n-nodes-base.webhook", "parameters": {"path": "90362198-abc"}},
    ]})
    assert n8n.workflow_webhook_url("X") == "https://n8n.example.com/webhook/90362198-abc"


def test_workflow_webhook_url_none_without_webhook(monkeypatch):
    monkeypatch.setenv("N8N_API_URL", "https://n8n.example.com/api/v1")
    monkeypatch.setattr(n8n, "get_workflow", lambda wid: {"nodes": [
        {"type": "n8n-nodes-base.scheduleTrigger", "parameters": {}}]})
    assert n8n.workflow_webhook_url("X") is None


def test_restart_prefers_webhook(monkeypatch):
    monkeypatch.setattr(n8n, "workflow_webhook_url", lambda wid: "https://n8n/webhook/p")
    seen = {}
    class R:
        def read(self): return b"ok"
        def __enter__(self): return self
        def __exit__(self, *a): return False
    monkeypatch.setattr(n8n.urllib.request, "urlopen",
                        lambda req, timeout=25: seen.update(url=req.full_url) or R())
    out = n8n.restart_workflow("W", "Spotlight")
    assert out["ok"] and out["via"] == "webhook" and seen["url"] == "https://n8n/webhook/p"


def test_restart_falls_back_to_executor(monkeypatch):
    monkeypatch.setattr(n8n, "workflow_webhook_url", lambda wid: None)
    monkeypatch.setattr(n8n, "trigger_n8n", lambda name, payload=None: {"ok": True})
    out = n8n.restart_workflow("W", "Spotlight")
    assert out["ok"] and out["via"] == "executor"
