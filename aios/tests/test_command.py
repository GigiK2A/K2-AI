"""Sicurezza della chat a istruzioni (CommandRouter):
- azioni interne sicure -> eseguite SUBITO
- esterne (n8n) / interne sensibili -> in CONFERMA, non eseguite finche' non confermi
- fuori perimetro (denaro/delete/non-allowlist) -> RIFIUTATE (mai eseguite)
"""
import json
from types import SimpleNamespace

from aios.kernel import Kernel
from aios.tools import Tool
from aios.command import CommandRouter
from aios.llm import FakeLLM


class FakeClient:
    def __init__(self):
        self.writes = []

    def insert(self, table, row):
        self.writes.append(("insert", table, row)); return [row]

    def update(self, table, filters, data):
        self.writes.append(("update", table, filters, data)); return [data]

    def select(self, table, params):
        return []


def _router(plan: dict):
    k = Kernel()
    client = FakeClient()
    k._supabase = client
    k.register_tool(Tool(name="leggi_calendario", action_type=None, readonly=True,
                         run=lambda **_: [{"id": 1, "bozza": "corta"}]))
    platform = SimpleNamespace(kernel=k, agents={}, commands=None)
    router = CommandRouter(platform, FakeLLM([json.dumps(plan)]))
    return router, client


def test_internal_safe_executes_now():
    plan = {"valutazione": "le allungo", "fattibile": True, "risposta": "ok",
            "azioni": [{"descrizione": "allunga bozza", "azione": {
                "tabella": "aios_content_calendar", "op": "update",
                "match": {"id": 1}, "dati": {"bozza": "testo molto piu' lungo e utile"}}}]}
    r, client = _router(plan)
    res = r.handle("allunga le caption dei post", actor="owner")
    assert res.fattibile
    assert len(res.eseguite) == 1 and not res.da_confermare and not res.rifiutate
    assert client.writes and client.writes[0][0] == "update"
    assert client.writes[0][1] == "aios_content_calendar"


def test_external_n8n_needs_confirm():
    plan = {"valutazione": "serve pubblicare", "fattibile": True, "risposta": "ok",
            "azioni": [{"descrizione": "pubblica su IG", "esterna": True,
                        "n8n": {"workflow": "publish_ig", "payload": {"x": 1}}}]}
    r, client = _router(plan)
    res = r.handle("pubblica il post su instagram")
    assert not res.eseguite and len(res.da_confermare) == 1
    assert client.writes == []                      # niente eseguito senza conferma
    out = r.confirm(res.da_confermare[0]["id"])
    assert out["tipo"] == "n8n"                      # confermato -> tentato n8n
    assert out["ok"] is False                        # N8N_WEBHOOK_URL non settato in test


def test_forbidden_money_refused():
    plan = {"valutazione": "x", "fattibile": True, "risposta": "ok",
            "azioni": [{"descrizione": "scrivi su conversioni", "azione": {
                "tabella": "kbot_conversions", "op": "insert", "dati": {"amount_eur": 99}}}]}
    r, client = _router(plan)
    res = r.handle("aumenta i ricavi")
    assert not res.eseguite and len(res.rifiutate) == 1 and client.writes == []


def test_forbidden_delete_refused():
    plan = {"valutazione": "x", "fattibile": True, "risposta": "ok",
            "azioni": [{"descrizione": "cancella task", "azione": {
                "tabella": "board_tasks", "op": "delete", "match": {"id": 1}, "dati": {"x": 1}}}]}
    r, client = _router(plan)
    res = r.handle("cancella i task")
    assert not res.eseguite and len(res.rifiutate) == 1 and client.writes == []


def test_sensitive_internal_needs_confirm_then_executes():
    plan = {"valutazione": "x", "fattibile": True, "risposta": "ok",
            "azioni": [{"descrizione": "crea fattura", "azione": {
                "tabella": "invoices", "op": "insert", "dati": {"importo_eur": 100}}}]}
    r, client = _router(plan)
    res = r.handle("emetti una fattura")
    assert not res.eseguite and len(res.da_confermare) == 1 and client.writes == []
    out = r.confirm(res.da_confermare[0]["id"])
    assert out["ok"] is True and client.writes[0][1] == "invoices"


def test_not_feasible_does_nothing():
    plan = {"valutazione": "non ha senso sui dati", "fattibile": False,
            "risposta": "Non lo farei", "azioni": []}
    r, client = _router(plan)
    res = r.handle("fai una cosa assurda")
    assert not res.fattibile and not res.eseguite and client.writes == []


def test_confirm_unknown_token():
    r, _ = _router({"valutazione": "", "fattibile": True, "risposta": "", "azioni": []})
    assert r.confirm(999)["ok"] is False
