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


def test_external_n8n_needs_confirm(monkeypatch):
    monkeypatch.delenv("N8N_WEBHOOK_URL", raising=False)   # test ermetico
    plan = {"valutazione": "serve pubblicare", "fattibile": True, "risposta": "ok",
            "azioni": [{"descrizione": "pubblica su IG", "esterna": True,
                        "n8n": {"workflow": "publish_ig", "payload": {"x": 1}}}]}
    r, client = _router(plan)
    res = r.handle("pubblica il post su instagram")
    assert not res.eseguite and len(res.da_confermare) == 1
    assert client.writes == []                      # niente eseguito senza conferma
    out = r.confirm(res.da_confermare[0]["id"])
    assert out["tipo"] == "n8n"                      # confermato -> tentato n8n
    assert out["ok"] is False                        # N8N_WEBHOOK_URL non configurato


def test_forbidden_control_plane_refused():
    # Piano di controllo (audit/policy/auth) resta vietato anche da chat.
    plan = {"valutazione": "x", "fattibile": True, "risposta": "ok",
            "azioni": [{"descrizione": "alza l'autonomia", "azione": {
                "tabella": "aios_policy_state", "op": "insert", "dati": {"level": 3}}}]}
    r, client = _router(plan)
    res = r.handle("alza la tua autonomia")
    assert not res.eseguite and len(res.rifiutate) == 1 and client.writes == []


def test_internal_money_executes_on_command():
    # Scelta owner: denaro interno (conversioni) scrivibile col solo comando.
    plan = {"valutazione": "registro la conversione", "fattibile": True, "risposta": "ok",
            "azioni": [{"descrizione": "registra conversione", "azione": {
                "tabella": "kbot_conversions", "op": "insert", "dati": {"amount_eur": 19}}}]}
    r, client = _router(plan)
    res = r.handle("registra una conversione kbot")
    assert len(res.eseguite) == 1 and not res.da_confermare
    assert client.writes and client.writes[0][1] == "kbot_conversions"


def test_forbidden_delete_refused():
    plan = {"valutazione": "x", "fattibile": True, "risposta": "ok",
            "azioni": [{"descrizione": "cancella task", "azione": {
                "tabella": "board_tasks", "op": "delete", "match": {"id": 1}, "dati": {"x": 1}}}]}
    r, client = _router(plan)
    res = r.handle("cancella i task")
    assert not res.eseguite and len(res.rifiutate) == 1 and client.writes == []


def test_internal_invoice_executes_now():
    # Nuova policy: tutto l'interno (fatture incluse) parte col solo comando, niente conferma.
    plan = {"valutazione": "x", "fattibile": True, "risposta": "ok",
            "azioni": [{"descrizione": "crea fattura", "azione": {
                "tabella": "invoices", "op": "insert", "dati": {"importo_eur": 100}}}]}
    r, client = _router(plan)
    res = r.handle("emetti una fattura")
    assert len(res.eseguite) == 1 and not res.da_confermare
    assert client.writes and client.writes[0][1] == "invoices"


def test_not_feasible_does_nothing():
    plan = {"valutazione": "non ha senso sui dati", "fattibile": False,
            "risposta": "Non lo farei", "azioni": []}
    r, client = _router(plan)
    res = r.handle("fai una cosa assurda")
    assert not res.fattibile and not res.eseguite and client.writes == []


def test_confirm_unknown_token():
    r, _ = _router({"valutazione": "", "fattibile": True, "risposta": "", "azioni": []})
    assert r.confirm(999)["ok"] is False


def test_n8n_manage_needs_confirm_never_auto(monkeypatch):
    monkeypatch.delenv("N8N_API_URL", raising=False)       # test ermetico
    monkeypatch.delenv("N8N_API_KEY", raising=False)
    plan = {"valutazione": "modifico l'automazione", "fattibile": True, "risposta": "ok",
            "azioni": [{"descrizione": "aggiorna workflow IG", "n8n_manage": {
                "op": "update", "workflow_id": "abc", "definition": {"name": "x", "nodes": []}}}]}
    r, client = _router(plan)
    res = r.handle("modifica il workflow n8n che pubblica i post")
    assert not res.eseguite and len(res.da_confermare) == 1 and client.writes == []
    out = r.confirm(res.da_confermare[0]["id"])
    assert out["tipo"] == "n8n_manage"
    assert out["ok"] is False        # N8N_API_URL/KEY non settati in test → niente effetto


def test_ddl_guard_blocks_destructive():
    from aios.actuator import validate_ddl, ActuatorError
    assert validate_ddl("ALTER TABLE kbot_profiles ADD COLUMN marketing_accepted_at timestamptz")
    # colonna che contiene 'delete' nel nome NON deve essere bloccata
    assert validate_ddl("ALTER TABLE x ADD COLUMN deleted_at timestamptz")
    for bad in ("DROP TABLE kbot_profiles", "TRUNCATE kbot_profiles",
                "ALTER TABLE x DROP COLUMN y", "DELETE FROM x"):
        try:
            validate_ddl(bad); assert False, f"non bloccato: {bad}"
        except ActuatorError:
            pass


def test_ddl_needs_confirm_then_executes(monkeypatch):
    monkeypatch.delenv("AIOS_DB_DSN", raising=False)  # niente DSN → no-op tracciato al confirm
    plan = {"valutazione": "aggiungo colonna", "fattibile": True, "risposta": "ok",
            "azioni": [{"descrizione": "aggiungi colonna audit", "azione": {
                "tipo": "ddl", "sql": "ALTER TABLE kbot_profiles ADD COLUMN audit_trail jsonb"}}]}
    r, client = _router(plan)
    res = r.handle("modifica lo schema di kbot_profiles aggiungendo audit_trail")
    # schema → MAI auto: la fa lei ma sotto conferma esplicita
    assert res.fattibile and not res.eseguite and len(res.da_confermare) == 1
    out = r.confirm(res.da_confermare[0]["id"])
    assert out["tipo"] == "interna" and out["ok"] is False  # AIOS_DB_DSN non configurato


def test_n8n_manage_delete_refused():
    plan = {"valutazione": "x", "fattibile": True, "risposta": "ok",
            "azioni": [{"descrizione": "elimina workflow", "n8n_manage": {
                "op": "delete", "workflow_id": "abc"}}]}
    r, client = _router(plan)
    res = r.handle("cancella il workflow n8n")
    assert not res.eseguite and not res.da_confermare and len(res.rifiutate) == 1
