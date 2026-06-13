from aios.kernel import Kernel, ExecOutcome
from aios.autonomy import ActionType, AutonomyLevel
from aios.tools import Tool
from aios.llm import FakeLLM
from aios.founder import default_founder_model
from aios.agents.domain import DomainAgent, DomainConfig


def _cfg():
    return DomainConfig(
        name="vendite",
        action=ActionType("vendite", "azione"),
        tool_name="proponi_vendite",
        sensors=[("leggi_lead", {})],
        system="Sei il responsabile vendite di K2-AI. Proponi azioni sui lead.",
        skill_focus=[], knowledge_query="vendite lead")


def _kernel_with_lead():
    k = Kernel()
    k.register_tool(Tool(name="leggi_lead", action_type=None, readonly=True,
                         run=lambda **_: [{"name": "Mario Rossi", "status": "qualificato"}]))
    return k


def test_domain_agent_files_proposals_at_L1():
    k = _kernel_with_lead()
    llm = FakeLLM(responses=['{"proposte":[{"tipo":"followup","titolo":"Richiama Mario","contenuto":"...","motivo":"fermo da 7gg"}]}'])
    agent = DomainAgent(kernel=k, llm=llm, founder=default_founder_model(), config=_cfg())
    res = agent.run()
    assert len(res.approval_ids) == 1
    p = k.approvals.pending()
    assert len(p) == 1 and p[0].action_key == "vendite.azione"
    assert k.policy.level_for(_cfg().action) == AutonomyLevel.L1_PROPOSE
    # the lead data reached the prompt
    _, user = llm.calls[-1]
    assert "Mario Rossi" in user


def test_domain_agent_injects_knowledge():
    class KB:
        def search(self, q, k=5): return ["K2-AI vende automazione AI per PMI 5-50"]
    k = _kernel_with_lead()
    llm = FakeLLM(responses=['{"proposte":[]}'])
    agent = DomainAgent(kernel=k, llm=llm, founder=default_founder_model(), config=_cfg(), knowledge=KB())
    agent.run()
    _, user = llm.calls[-1]
    assert "automazione AI per PMI" in user


def test_domain_agent_writes_deliverable_on_approval():
    class FakeClient:
        def __init__(self): self.rows = []
        def insert(self, table, row):
            assert table == "aios_deliverables"
            r = {"id": len(self.rows)+1, **row}; self.rows.append(r); return [r]
    client = FakeClient()
    k = _kernel_with_lead()
    llm = FakeLLM(responses=['{"proposte":[{"tipo":"followup","titolo":"T","contenuto":"C","motivo":"M"}]}'])
    agent = DomainAgent(kernel=k, llm=llm, founder=default_founder_model(), config=_cfg(),
                        deliverable_client=client)
    res = agent.run()
    assert client.rows == []                       # nothing written while pending
    k.resolve_approval(res.approval_ids[0], approve=True)
    assert len(client.rows) == 1
    assert client.rows[0]["dominio"] == "vendite" and client.rows[0]["titolo"] == "T"
