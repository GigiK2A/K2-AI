"""Watchdog n8n: classificazione + riavvio transitori (con tetto) + proposta strutturali."""
import aios.n8n_watchdog as wd


def _enable(monkeypatch):
    monkeypatch.setattr(wd, "n8n_api_enabled", lambda: True)


def _err_exec(msg, node="Nodo X"):
    return {"data": {"resultData": {"error": {"message": msg, "node": {"name": node}}}}}


def test_classify():
    assert wd.classify("getaddrinfo ENOTFOUND / timeout") == "transient"
    assert wd.classify("502 Bad Gateway") == "transient"
    assert wd.classify("is_transient true, riprova") == "transient"
    assert wd.classify("2207032 impossibile creare") == "transient"
    assert wd.classify("401 Unauthorized: token expired") == "structural"
    assert wd.classify("campo obbligatorio mancante") == "structural"
    assert wd.classify("") == "structural"


def test_disabled_returns_error(monkeypatch):
    monkeypatch.setattr(wd, "n8n_api_enabled", lambda: False)
    assert wd.check_and_heal()["ok"] is False


def test_all_success_no_restart(monkeypatch):
    _enable(monkeypatch)
    calls = []
    r = wd.check_and_heal(
        list_exec=lambda **k: {"ok": True, "esecuzioni": [
            {"id": "1", "workflowId": "A", "status": "success"},
            {"id": "2", "workflowId": "B", "status": "success"}]},
        get_exec=lambda i: {}, list_wf=lambda: [], restart=lambda *a, **k: calls.append(a) or {"ok": True, "via": "webhook"},
        now=1_000_000)
    assert r["ok"] and r["in_ordine"] == 2 and not r["riavviati"] and not r["proposte"]
    assert calls == []


def test_transient_gets_restarted(monkeypatch):
    _enable(monkeypatch)
    fired = []
    r = wd.check_and_heal(
        list_exec=lambda **k: {"ok": True, "esecuzioni": [
            {"id": "9", "workflowId": "A", "status": "error"}]},
        get_exec=lambda i: _err_exec("connect ETIMEDOUT graph.facebook.com"),
        list_wf=lambda: [{"id": "A", "name": "Formazione"}],
        restart=lambda wid, name=None, **k: fired.append((wid, name)) or {"ok": True, "via": "webhook"},
        now=1_000_000)
    assert len(r["riavviati"]) == 1 and r["riavviati"][0]["workflow"] == "Formazione"
    assert r["riavviati"][0]["riavviato"] is True and not r["proposte"]
    assert fired and fired[0] == ("A", "Formazione")   # restart(workflow_id, name)


def test_deep_meta_2207032_classified_transient_and_restarted(monkeypatch):
    # n8n mette 'Bad request' generico in error.message, ma il vero codice Meta (2207032)
    # vive in error.messages[]. Il watchdog deve scavarlo → transitorio → RIAVVIO.
    _enable(monkeypatch)
    raw = ('400 - "{\\"error\\":{\\"message\\":\\"Fatal\\",\\"error_subcode\\":2207032,'
           '\\"is_transient\\":false,\\"error_user_title\\":\\"Impossibile creare il '
           'contenuto multimediale\\"}}"')
    execdata = {"data": {"resultData": {"error": {
        "message": "Bad request - please check your parameters",
        "description": "Fatal", "messages": [raw],
        "node": {"name": "Spot — Upload IG Container"}}}}}
    fired = []
    r = wd.check_and_heal(
        list_exec=lambda **k: {"ok": True, "esecuzioni": [
            {"id": "9", "workflowId": "S", "status": "error"}]},
        get_exec=lambda i: execdata,
        list_wf=lambda: [{"id": "S", "name": "07 — Spotlight"}],
        restart=lambda wid, name=None, **k: fired.append((wid, name)) or {"ok": True, "via": "webhook"},
        now=1_000_000)
    # il codice profondo è emerso e classificato transitorio → riavviato, non proposto
    msg, node = wd._extract_error(execdata)
    assert "2207032" in msg and wd.classify(msg) == "transient"
    assert len(r["riavviati"]) == 1 and not r["proposte"]
    assert fired == [("S", "07 — Spotlight")]


def test_structural_proposed_not_restarted(monkeypatch):
    _enable(monkeypatch)
    fired = []
    r = wd.check_and_heal(
        list_exec=lambda **k: {"ok": True, "esecuzioni": [
            {"id": "9", "workflowId": "B", "status": "error"}]},
        get_exec=lambda i: _err_exec("401 Unauthorized: credential expired", node="HTTP IG"),
        list_wf=lambda: [{"id": "B", "name": "Spotlight"}],
        restart=lambda *a, **k: fired.append(a) or {"ok": True, "via": "webhook"},
        now=1_000_000)
    assert fired == []                      # NON riavviato
    assert len(r["proposte"]) == 1
    p = r["proposte"][0]
    assert p["tipo"] == "strutturale" and p["nodo"] == "HTTP IG" and "credenziale" in p["suggerimento"]


def test_retry_cap_stops_restart(monkeypatch):
    _enable(monkeypatch)

    class LogClient:
        def select(self, table, params):    # già 2 riavvii oggi
            return [{"id": 1}, {"id": 2}]
        def insert(self, table, row):
            return [row]

    fired = []
    r = wd.check_and_heal(
        log_client=LogClient(), retry_cap=2,
        list_exec=lambda **k: {"ok": True, "esecuzioni": [
            {"id": "9", "workflowId": "A", "status": "error"}]},
        get_exec=lambda i: _err_exec("timeout"),
        list_wf=lambda: [{"id": "A", "name": "Formazione"}],
        restart=lambda *a, **k: fired.append(a) or {"ok": True, "via": "webhook"},
        now=1_000_000)
    assert fired == []                      # tetto raggiunto → non riavvia più
    assert r["proposte"] and r["proposte"][0]["tipo"] == "retry_esaurito"


def test_stuck_running_is_proposed(monkeypatch):
    _enable(monkeypatch)
    from datetime import datetime, timezone
    now = 1_000_000.0
    old = datetime.fromtimestamp(now - 60 * 60, tz=timezone.utc).isoformat()  # 60 min fa
    r = wd.check_and_heal(
        list_exec=lambda **k: {"ok": True, "esecuzioni": [
            {"id": "9", "workflowId": "A", "status": "running", "startedAt": old}]},
        get_exec=lambda i: {}, list_wf=lambda: [{"id": "A", "name": "Newsletter"}],
        restart=lambda *a, **k: {"ok": True, "via": "webhook"}, now=now)
    assert r["proposte"] and r["proposte"][0]["tipo"] == "bloccato"
