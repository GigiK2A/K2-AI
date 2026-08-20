"""Test ermetici per il metering costi + budget hard-stop (billing.py).

Nessun DB, nessun segreto: il CostMeter aggrega in memoria. L'integrazione col
gate è verificata su un agente reale (MarketingAgent) con FakeLLM.
"""
from __future__ import annotations

import json

import pytest

from aios import billing
from aios.billing import CostMeter, attribute, cost_eur


@pytest.fixture(autouse=True)
def _reset_meter():
    """Ogni test parte da un meter pulito e non inquina gli altri."""
    billing.set_meter(CostMeter())
    yield
    billing.set_meter(CostMeter())


# ── pricing ───────────────────────────────────────────────────────────────────
def test_cost_eur_haiku_and_sonnet_differ():
    # Haiku (1/5 USD/Mtok) < Sonnet (3/15) a parità di token
    haiku = cost_eur("claude-haiku-4-5-20251001", 1_000_000, 1_000_000)
    sonnet = cost_eur("claude-sonnet-4-6", 1_000_000, 1_000_000)
    assert haiku > 0
    assert sonnet > haiku


def test_cost_eur_unknown_and_local_is_zero():
    assert cost_eur("gpt-oss:120b", 5000, 5000) == 0.0
    assert cost_eur("", 10, 10) == 0.0


def test_cost_eur_prefix_match():
    # match per prefisso: "claude-haiku-4-5-2025..." → tabella "claude-haiku-4-5"
    exact = cost_eur("claude-haiku-4-5", 1_000_000, 0)
    prefixed = cost_eur("claude-haiku-4-5-20251001", 1_000_000, 0)
    assert exact == prefixed > 0


# ── metering + attribuzione ────────────────────────────────────────────────────
def test_record_attributes_to_context_actor():
    m = CostMeter()
    billing.set_meter(m)
    with attribute("finance_agent"):
        billing.record_usage("claude-haiku-4-5", 1_000_000, 1_000_000)
    assert m.spent("finance_agent") > 0
    assert m.spent("marketing_agent") == 0


def test_record_without_context_goes_to_system():
    m = CostMeter()
    billing.set_meter(m)
    billing.record_usage("claude-haiku-4-5", 1000, 1000)
    assert m.spent("system") >= 0  # tracciato, magari arrotonda a ~0 ma la chiave esiste
    assert ("system", m.status("system").period) in m._spend


def test_spend_accumulates():
    m = CostMeter()
    for _ in range(3):
        m.record_usage("claude-sonnet-4-6", 500_000, 500_000, actor="x")
    one = cost_eur("claude-sonnet-4-6", 500_000, 500_000)
    assert m.spent("x") == pytest.approx(one * 3, rel=1e-6)


# ── budget gate ─────────────────────────────────────────────────────────────────
def test_gate_under_budget_not_over():
    m = CostMeter(budgets={"x": 100.0})
    m.record_usage("claude-haiku-4-5", 1000, 1000, actor="x")
    st = m.check("x")
    assert not st.over
    assert st.remaining_eur is not None and st.remaining_eur < 100.0


def test_gate_blocks_when_spent_reaches_cap():
    m = CostMeter(budgets={"x": 0.0})   # tetto 0 → sempre oltre
    assert m.check("x").over is True


def test_default_cap_applies_to_unlisted_actor():
    m = CostMeter(default_cap=0.0)
    assert m.check("chiunque").over is True
    m2 = CostMeter()   # nessun tetto
    assert m2.check("chiunque").over is False
    assert m2.check("chiunque").cap_eur is None


def test_status_ratio_and_near():
    m = CostMeter(budgets={"x": 10.0}, warn_ratio=0.8)
    # forzo una spesa nota: 8 EUR
    m._spend[("x", m.status("x").period)] = 8.0
    st = m.status("x")
    assert st.ratio == pytest.approx(0.8)
    assert st.near(0.8) is True
    assert st.over is False


def test_report_shape():
    m = CostMeter(budgets={"a": 5.0})
    m.record_usage("claude-haiku-4-5", 1000, 1000, actor="a")
    rows = m.report(["a"])
    assert rows and rows[0]["actor"] == "a"
    assert set(rows[0]) >= {"actor", "spent_eur", "cap_eur", "remaining_eur", "over", "warn"}


# ── persistenza best-effort su client fittizio ──────────────────────────────────
class _FakeClient:
    def __init__(self):
        self.inserts = []
        self.upserts = []
        self._state = []

    def select(self, table, params):
        return self._state if table == CostMeter.STATE_TABLE else []

    def insert(self, table, row):
        self.inserts.append((table, row))
        return [row]

    def upsert(self, table, row, *, on_conflict):
        self.upserts.append((table, row, on_conflict))
        return [row]


def test_persist_writes_ledger_and_state():
    c = _FakeClient()
    m = CostMeter(c, budgets={"x": 100.0})
    m.record_usage("claude-sonnet-4-6", 1_000_000, 1_000_000, actor="x")
    assert any(t == CostMeter.LEDGER_TABLE for t, _ in c.inserts)
    assert any(t == CostMeter.STATE_TABLE for t, _, _ in c.upserts)


def test_hydrate_from_state_on_read():
    c = _FakeClient()
    period = billing.CostMeter().status("x").period
    c._state = [{"spent_eur": 42.0}]
    m = CostMeter(c, budgets={"x": 100.0})
    # senza record, la spesa arriva dal running-state persistito
    assert m.spent("x") == 42.0
    assert m.check("x").remaining_eur == pytest.approx(58.0)


def test_metering_never_raises_on_bad_client():
    class Boom:
        def select(self, *a, **k): raise RuntimeError("db down")
        def insert(self, *a, **k): raise RuntimeError("db down")
        def upsert(self, *a, **k): raise RuntimeError("db down")
    m = CostMeter(Boom(), budgets={"x": 1.0})
    # non deve sollevare: la contabilità degrada, la completion LLM sopravvive
    assert m.record_usage("claude-haiku-4-5", 10, 10, actor="x") >= 0.0


# ── integrazione: hard-stop reale su un agente ──────────────────────────────────
def test_agent_over_budget_does_not_call_llm():
    from aios.kernel import Kernel
    from aios.llm import FakeLLM
    from aios.agents.marketing import MarketingAgent

    billing.set_meter(CostMeter(budgets={"marketing_agent": 0.0}))  # tetto 0 → bloccato
    k = Kernel()
    llm = FakeLLM(responses=[json.dumps({"proposte": [{"tipo": "x", "titolo": "t",
                                                        "contenuto": "c", "motivo": "m"}]})])
    agent = MarketingAgent(kernel=k, llm=llm, founder=_founder(), discover_competitors=False)
    res = agent.run()
    assert res.proposals == []          # nessuna proposta
    assert res.approval_ids == []
    assert llm.calls == []              # e soprattutto: LLM MAI chiamato → zero spesa


def test_agent_under_budget_runs_normally():
    from aios.llm import FakeLLM
    from aios.agents.marketing import MarketingAgent

    billing.set_meter(CostMeter(budgets={"marketing_agent": 100.0}))
    k = _kernel_with_fake_sensors()
    llm = FakeLLM(responses=[json.dumps({"proposte": []})])
    agent = MarketingAgent(kernel=k, llm=llm, founder=_founder(), discover_competitors=False)
    agent.run()
    assert llm.calls, "sotto budget l'agente deve interpellare l'LLM"


def _kernel_with_fake_sensors():
    from aios.kernel import Kernel
    from aios.tools import Tool
    k = Kernel()
    k.register_tool(Tool(name="leggi_servizi", action_type=None, readonly=True,
                         run=lambda **_: [{"Servizio": "Automazioni"}]))
    k.register_tool(Tool(name="leggi_topics", action_type=None, readonly=True,
                         run=lambda **_: [{"Tema": "RAG per PMI"}]))
    k.register_tool(Tool(name="leggi_profilo_ig", action_type=None, readonly=True,
                         run=lambda **_: {"username": "k2_ai.it", "followers_count": 5}))
    k.register_tool(Tool(name="leggi_post_ig", action_type=None, readonly=True,
                         run=lambda **_: [{"caption": "x", "like_count": 2}]))
    return k


def _founder():
    from aios.founder import default_founder_model
    return default_founder_model()


# ── OpenAI nel listino ────────────────────────────────────────────────────────
# Fino al 20 ago 2026 il listino aveva solo Anthropic mentre la catena era già su
# OpenAI: ogni chiamata a gpt-4o costava zero, quindi non consumava budget e il
# hard-stop di AIOS_AGENT_BUDGETS non poteva scattare. Il board spendeva senza tetto.

def test_i_modelli_openai_hanno_un_prezzo():
    for m in ("gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o3-mini", "o4-mini"):
        assert cost_eur(m, 1_000_000, 1_000_000) > 0, f"{m} fatturato zero"


def test_mini_costa_meno_del_modello_pieno():
    # Il prefisso più lungo, non il primo: "gpt-4o-mini" comincia anche per "gpt-4o".
    # Col match sul primo, il mini veniva fatturato al prezzo del grande.
    pieno = cost_eur("gpt-4o", 1_000_000, 1_000_000)
    mini = cost_eur("gpt-4o-mini", 1_000_000, 1_000_000)
    assert 0 < mini < pieno


def test_prezzo_indipendente_dall_ordine_del_listino():
    from aios import billing as b
    ordinato = dict(sorted(b._PRICING_USD.items()))
    originale = b._PRICING_USD
    try:
        b._PRICING_USD = ordinato        # riordinare il listino non deve cambiare i prezzi
        assert b._price_for("gpt-4o-mini") == (0.15, 0.60)
        assert b._price_for("gpt-4o") == (2.50, 10.0)
    finally:
        b._PRICING_USD = originale


def test_snapshot_di_versione_dei_modelli_openai():
    # OpenAI appende la data alla versione: gpt-4o-mini-2024-07-18 deve costare
    # come gpt-4o-mini, non zero.
    assert cost_eur("gpt-4o-mini-2024-07-18", 1_000_000, 0) == cost_eur(
        "gpt-4o-mini", 1_000_000, 0) > 0


def test_il_budget_si_esaurisce_spendendo_su_openai():
    # La prova che conta: con OpenAI il tetto mensile dell'agente scatta davvero.
    meter = CostMeter(budgets={"vendite_agent": 0.50})
    billing.set_meter(meter)
    assert meter.check("vendite_agent").over is False
    with attribute("vendite_agent"):
        billing.record_usage("gpt-4o", 1_000_000, 0)   # ~2,30 EUR, oltre il tetto
    stato = meter.check("vendite_agent")
    assert stato.spent_eur > 0.50
    assert stato.over is True


def test_il_locale_resta_gratis_e_non_consuma_budget():
    meter = CostMeter(budgets={"vendite_agent": 0.50})
    billing.set_meter(meter)
    with attribute("vendite_agent"):
        billing.record_usage("gpt-oss:120b", 5_000_000, 5_000_000)
    assert meter.check("vendite_agent").spent_eur == 0.0
    assert meter.check("vendite_agent").over is False
