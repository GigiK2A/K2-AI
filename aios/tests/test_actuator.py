"""Attuatore L1: perimetro di sicurezza + esecuzione su approvazione."""
import pytest

from aios.actuator import apply_action, validate, ActuatorError
from aios.kernel import Kernel
from aios.llm import FakeLLM
from aios.founder import default_founder_model
from aios.agents.domain import DomainAgent, DomainConfig
from aios.autonomy import ActionType
from aios.tools import Tool


class FakeClient:
    def __init__(self):
        self.inserts = []
        self.updates = []

    def select(self, table, params):
        return [{"id": "L1", "name": "Mario"}]

    def insert(self, table, row):
        self.inserts.append((table, row))
        return [{"id": 1, **row}]

    def update(self, table, filters, patch):
        self.updates.append((table, filters, patch))
        return [{"id": 1, **patch}]


# ---- validate / perimetro ----
def test_block_delete():
    with pytest.raises(ActuatorError):
        validate({"tabella": "pipeline_leads", "op": "delete", "dati": {"x": 1}})


def test_block_money_table():
    with pytest.raises(ActuatorError):
        validate({"tabella": "board_revenue_events", "op": "insert", "dati": {"amount_cents": 1}})


def test_block_non_allowlisted():
    with pytest.raises(ActuatorError):
        validate({"tabella": "qualcosa", "op": "insert", "dati": {"x": 1}})


def test_block_kbot_user_data():
    with pytest.raises(ActuatorError):
        validate({"tabella": "kbot_sessions", "op": "update", "match": {"id": 1}, "dati": {"x": 1}})


def test_update_requires_match():
    with pytest.raises(ActuatorError):
        validate({"tabella": "pipeline_leads", "op": "update", "dati": {"score": 9}})


def test_op_not_allowed_on_table():
    # finance_journal consente solo insert
    with pytest.raises(ActuatorError):
        validate({"tabella": "finance_journal", "op": "update", "match": {"id": 1}, "dati": {"x": 1}})


# ---- apply_action ----
def test_apply_insert():
    c = FakeClient()
    out = apply_action(c, {"tabella": "board_tasks", "op": "insert", "dati": {"title": "x"}})
    assert out["ok"] and c.inserts and c.inserts[0][0] == "board_tasks"


def test_apply_update_adds_eq_prefix():
    c = FakeClient()
    out = apply_action(c, {"tabella": "pipeline_leads", "op": "update",
                           "match": {"id": "L1"}, "dati": {"score": 9}})
    assert out["ok"]
    table, filters, patch = c.updates[0]
    assert table == "pipeline_leads" and filters["id"] == "eq.L1" and patch["score"] == 9


# ---- end-to-end: esegue SOLO all'approvazione ----
def _agent(client, llm):
    k = Kernel()
    k.register_tool(Tool(name="leggi_x", action_type=None, readonly=True,
                         run=lambda **_: client.select("pipeline_leads", {})))
    cfg = DomainConfig(name="vendite", action=ActionType("vendite", "azione"),
                       tool_name="proponi_vendite", sensors=[("leggi_x", {})],
                       system="test", skill_focus=[], knowledge_query="")
    return k, DomainAgent(kernel=k, llm=llm, founder=default_founder_model(),
                          config=cfg, deliverable_client=client)


def test_action_runs_only_after_approval():
    client = FakeClient()
    llm = FakeLLM(responses=[
        '{"proposte":[{"tipo":"qualification","titolo":"Aggiorna score","contenuto":"...",'
        '"motivo":"score basso","azione":{"tabella":"pipeline_leads","op":"update",'
        '"match":{"id":"L1"},"dati":{"score":9}}}]}'])
    k, agent = _agent(client, llm)
    res = agent.run()
    # in coda: nessuna scrittura ancora
    assert client.updates == []
    k.resolve_approval(res.approval_ids[0], approve=True)
    # dopo approvazione: scrittura eseguita
    assert client.updates and client.updates[0][0] == "pipeline_leads"


def test_ensure_action_fallback_when_missing():
    from aios.agents.domain import _ensure_action
    az = _ensure_action({"tipo": "x", "titolo": "Sollecita lead", "contenuto": "c", "motivo": "m"})
    assert az["tabella"] == "board_tasks" and az["op"] == "insert"
    assert az["dati"]["title"] == "Sollecita lead"


def test_ensure_action_keeps_valid_llm_action():
    from aios.agents.domain import _ensure_action
    good = {"tabella": "pipeline_leads", "op": "update", "match": {"id": "L1"}, "dati": {"score": 9}}
    assert _ensure_action({"titolo": "t", "azione": good}) is good


def test_ensure_action_replaces_invalid_action():
    from aios.agents.domain import _ensure_action
    bad = {"tabella": "board_revenue_events", "op": "insert", "dati": {"a": 1}}
    az = _ensure_action({"titolo": "t", "contenuto": "c", "azione": bad})
    assert az["tabella"] == "board_tasks"  # vietata → sostituita con fallback sicuro


def test_every_proposal_gets_valid_action_after_run():
    from aios.actuator import validate
    client = FakeClient()
    # una proposta SENZA azione → deve comunque avere azione valida dopo run()
    llm = FakeLLM(responses=['{"proposte":[{"tipo":"kpi","titolo":"Report","contenuto":"c","motivo":"m"}]}'])
    k, agent = _agent(client, llm)
    res = agent.run()
    for p in res.proposals:
        validate(p["azione"])  # non solleva = valida


def test_invalid_action_does_not_crash_approval():
    client = FakeClient()
    llm = FakeLLM(responses=[
        '{"proposte":[{"tipo":"x","titolo":"t","contenuto":"c","motivo":"m",'
        '"azione":{"tabella":"board_revenue_events","op":"insert","dati":{"a":1}}}]}'])
    k, agent = _agent(client, llm)
    res = agent.run()
    out = k.resolve_approval(res.approval_ids[0], approve=True)
    # nessuna scrittura sulla tabella vietata, e l'approvazione non è crashata
    assert client.inserts == [] or all(t != "board_revenue_events" for t, _ in client.inserts)
