"""Tutti i domini di dominio (Finance, Operations, Legal, HR) + Vendite ricco:
ogni config è valida, i suoi sensori esistono e l'agente propone a L1 leggendo
dati reali (simulati con un fake client)."""
from aios.kernel import Kernel
from aios.autonomy import AutonomyLevel
from aios.llm import FakeLLM
from aios.founder import default_founder_model
from aios.agents.domain import DomainAgent

from aios.sources.sales import lead_tools
from aios.sources.domains import (finance_tools, operations_tools,
                                  legal_tools, hr_tools)
from aios.agents.sales_config import SALES_CONFIG
from aios.agents.finance_config import FINANCE_CONFIG
from aios.agents.operations_config import OPERATIONS_CONFIG
from aios.agents.legal_config import LEGAL_CONFIG
from aios.agents.hr_config import HR_CONFIG


class FakeClient:
    """Restituisce una riga marcatore per ogni tabella, registra gli insert."""
    def __init__(self):
        self.rows = []

    def select(self, table, params):
        return [{"_tabella": table, "marker": f"DATO_{table}"}]

    def insert(self, table, row):
        r = {"id": len(self.rows) + 1, **row}
        self.rows.append(r)
        return [r]


CASES = [
    (SALES_CONFIG, lead_tools, "vendite.azione", "proponi_vendite"),
    (FINANCE_CONFIG, finance_tools, "finance.azione", "proponi_finance"),
    (OPERATIONS_CONFIG, operations_tools, "operations.azione", "proponi_operations"),
    (LEGAL_CONFIG, legal_tools, "legal.azione", "proponi_legal"),
    (HR_CONFIG, hr_tools, "hr.azione", "proponi_hr"),
]


def _kernel(client, factory):
    k = Kernel()
    for t in factory(client):
        k.register_tool(t)
    return k


def test_each_domain_sensors_exist_and_match_config():
    client = FakeClient()
    for cfg, factory, _, _ in CASES:
        k = _kernel(client, factory)
        names = set(k.tools.names())
        for sensor_name, _args in cfg.sensors:
            assert sensor_name in names, f"{cfg.name}: sensore {sensor_name} mancante"


def test_each_domain_proposes_at_L1_with_real_data():
    for cfg, factory, action_key, tool_name in CASES:
        client = FakeClient()
        k = _kernel(client, factory)
        llm = FakeLLM(responses=[
            '{"proposte":[{"tipo":"azione","titolo":"T","contenuto":"C","motivo":"M"}]}'])
        agent = DomainAgent(kernel=k, llm=llm, founder=default_founder_model(),
                            config=cfg, deliverable_client=client)
        res = agent.run()
        assert len(res.approval_ids) == 1, f"{cfg.name}: nessuna proposta"
        pend = k.approvals.pending()
        assert pend[0].action_key == action_key
        assert k.policy.level_for(cfg.action) == AutonomyLevel.L1_PROPOSE
        # i dati reali del primo sensore sono finiti nel prompt
        first_table_marker = f"DATO_"
        _, user = llm.calls[-1]
        assert first_table_marker in user, f"{cfg.name}: dati non nel prompt"
        # all'approvazione scrive il deliverable col dominio giusto
        k.resolve_approval(res.approval_ids[0], approve=True)
        assert any(r.get("dominio") == cfg.name for r in client.rows)


def test_all_domain_configs_have_distinct_tools_and_actions():
    tools = [c[3] for c in CASES]
    actions = [c[2] for c in CASES]
    assert len(set(tools)) == len(tools)
    assert len(set(actions)) == len(actions)
