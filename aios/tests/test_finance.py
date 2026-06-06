"""Agente Finance: tutte le funzioni hanno una fonte (sensore) registrata e
l'agente propone a L1 leggendo i dati reali (simulati)."""
from aios.kernel import Kernel
from aios.autonomy import AutonomyLevel
from aios.llm import FakeLLM
from aios.founder import default_founder_model
from aios.agents.domain import DomainAgent
from aios.agents.finance_config import FINANCE_CONFIG
from aios.sources.domains import finance_tools, catalog_tools
from aios.sources.connectors import all_connectors


class FakeClient:
    def __init__(self):
        self.rows = []

    def select(self, table, params):
        return [{"_tab": table}]

    def insert(self, table, row):
        r = {"id": len(self.rows) + 1, **row}
        self.rows.append(r)
        return [r]


def _kernel(client):
    k = Kernel()
    for t in finance_tools(client):
        k.register_tool(t)
    for t in catalog_tools(client):
        k.register_tool(t)
    for t in all_connectors():
        k.register_tool(t)
    return k


def test_finance_sensors_for_each_function_exist():
    k = _kernel(FakeClient())
    names = set(k.tools.names())
    for sensor, _ in FINANCE_CONFIG.sensors:
        assert sensor in names, f"sensore finance mancante: {sensor}"


def test_new_finance_sensors_read_right_tables():
    client = FakeClient()
    k = _kernel(client)
    mapping = {"leggi_fatture": "invoices", "leggi_giornale": "finance_journal",
               "leggi_organico": "employees", "leggi_costi": "board_cost_items"}
    for sensor, table in mapping.items():
        out = k.execute(sensor, actor="t", args={}).result
        assert out and out[0]["_tab"] == table, f"{sensor} legge la tabella sbagliata"


def test_finance_agent_proposes_at_L1():
    client = FakeClient()
    k = _kernel(client)
    llm = FakeLLM(responses=[
        '{"proposte":[{"tipo":"revenue/MRR","titolo":"MRR","contenuto":"...","motivo":"dato reale"},'
        '{"tipo":"tax_compliance_IT","titolo":"IVA 16","contenuto":"...","motivo":"scadenza"}]}'])
    agent = DomainAgent(kernel=k, llm=llm, founder=default_founder_model(),
                        config=FINANCE_CONFIG, deliverable_client=client)
    res = agent.run()
    assert len(res.approval_ids) == 2
    assert k.approvals.pending()[0].action_key == "finance.azione"
    assert k.policy.level_for(FINANCE_CONFIG.action) == AutonomyLevel.L1_PROPOSE


def test_finance_covers_all_16_functions_in_prompt():
    # il system prompt enumera le 16 funzioni chiave
    sysp = FINANCE_CONFIG.system
    for fn in ["general_ledger", "accounts_payable", "accounts_receivable", "treasury",
               "fpa", "kpi", "month_end_close", "controllership", "tax_compliance_IT",
               "payroll", "revenue/MRR", "cost_control", "pricing/margin", "audit",
               "risk", "investor_relations"]:
        assert fn in sysp, f"funzione non dichiarata nel prompt finance: {fn}"
