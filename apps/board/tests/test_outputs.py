from aios.kernel import Kernel, ExecOutcome
from aios.autonomy import AutonomyLevel
from aios.agents.marketing import PROPOSE_ACTION
from aios.sources.outputs import output_tool


class FakeClient:
    def __init__(self):
        self.rows = []

    def insert(self, table, row):
        assert table == "aios_marketing_outputs"
        r = {"id": len(self.rows) + 1, **row}
        self.rows.append(r)
        return [r]


def _kernel(client):
    k = Kernel()
    k.register_tool(output_tool(client))
    k.policy.set_level(PROPOSE_ACTION, AutonomyLevel.L1_PROPOSE)
    k.policy.set_cap(PROPOSE_ACTION, AutonomyLevel.L1_PROPOSE)
    return k


def test_proposal_is_queued_then_written_on_approval():
    c = FakeClient()
    k = _kernel(c)
    res = k.execute("proponi_marketing", actor="marketing_agent",
                    args={"tipo": "caption", "titolo": "T", "contenuto": "C", "motivo": "M"})
    assert res.outcome == ExecOutcome.QUEUED
    assert c.rows == []                              # nothing written while pending
    run = k.resolve_approval(res.approval_id, approve=True)
    assert run.outcome == ExecOutcome.EXECUTED
    assert len(c.rows) == 1
    assert c.rows[0]["titolo"] == "T" and c.rows[0]["tipo"] == "caption"
    assert c.rows[0]["stato"] == "approvato"


def test_rejected_proposal_writes_nothing():
    c = FakeClient()
    k = _kernel(c)
    res = k.execute("proponi_marketing", actor="m",
                    args={"tipo": "fix", "titolo": "X", "contenuto": "Y", "motivo": "Z"})
    k.resolve_approval(res.approval_id, approve=False, reason="no")
    assert c.rows == []
