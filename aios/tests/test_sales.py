from aios.kernel import Kernel, ExecOutcome
from aios.llm import FakeLLM
from aios.founder import default_founder_model
from aios.agents.domain import DomainAgent
from aios.agents.sales_config import SALES_CONFIG
from aios.sources.sales import lead_tools


class FakeClient:
    def select(self, table, params):
        assert table in ("pipeline_leads", "board_memos", "kbot_conversions",
                         "board_revenue_events")
        if table == "board_memos":
            return [{"subject": "call Acme", "body": "interessati", "tags": [],
                     "created_at": "2026-06-01"}]
        if table in ("kbot_conversions", "board_revenue_events"):
            return []
        return [{"id": 1, "name": "Mario Rossi", "company": "Acme", "status": "qualificato",
                 "score": 8, "next_action": None, "pain_point": "troppe email", "notes": ""}]


def test_lead_tool_reads_pipeline_leads():
    k = Kernel()
    for t in lead_tools(FakeClient()):
        k.register_tool(t)
    res = k.execute("leggi_lead", actor="vendite", args={})
    assert res.outcome == ExecOutcome.EXECUTED
    assert res.result[0]["name"] == "Mario Rossi"


def test_sales_agent_proposes_from_real_leads():
    k = Kernel()
    for t in lead_tools(FakeClient()):
        k.register_tool(t)
    llm = FakeLLM(responses=['{"proposte":[{"tipo":"followup","titolo":"Richiama Mario Rossi","contenuto":"...","motivo":"score 8, fermo"}]}'])
    agent = DomainAgent(kernel=k, llm=llm, founder=default_founder_model(), config=SALES_CONFIG)
    res = agent.run()
    assert len(res.approval_ids) == 1
    assert k.approvals.pending()[0].action_key == SALES_CONFIG.action.key
    _, user = llm.calls[-1]
    assert "Mario Rossi" in user
