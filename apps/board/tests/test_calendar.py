from aios.kernel import Kernel, ExecOutcome
from aios.autonomy import AutonomyLevel
from aios.sources.calendar import calendar_tools, CALENDAR_ACTION


class FakeClient:
    def __init__(self):
        self.rows = []
        self._id = 0

    def select(self, table, params):
        return list(self.rows)

    def insert(self, table, row):
        self._id += 1
        r = {"id": self._id, **row}
        self.rows.append(r)
        return [r]


def _kernel_with_calendar():
    k = Kernel()
    c = FakeClient()
    for t in calendar_tools(c):
        k.register_tool(t)
    k.policy.set_level(CALENDAR_ACTION, AutonomyLevel.L1_PROPOSE)
    k.policy.set_cap(CALENDAR_ACTION, AutonomyLevel.L1_PROPOSE)
    return k, c


def test_read_calendar_is_readonly():
    k, c = _kernel_with_calendar()
    c.rows = [{"id": 1, "canale": "instagram", "titolo": "x"}]
    res = k.execute("leggi_calendario", actor="m", args={})
    assert res.outcome == ExecOutcome.EXECUTED and res.result[0]["titolo"] == "x"


def test_schedule_is_L1_and_queues_then_writes_on_approval():
    k, c = _kernel_with_calendar()
    args = {"canale": "instagram", "titolo": "Post agenti email",
            "bozza": "70% email gestite...", "data_programmata": "2026-06-11"}
    res = k.execute("programma_contenuto", actor="marketing_agent", args=args)
    assert res.outcome == ExecOutcome.QUEUED
    assert c.rows == []
    run = k.resolve_approval(res.approval_id, approve=True)
    assert run.outcome == ExecOutcome.EXECUTED
    assert len(c.rows) == 1 and c.rows[0]["titolo"] == "Post agenti email"
    assert c.rows[0]["stato"] == "approvato"


def test_calendar_action_capped_at_L1():
    k, c = _kernel_with_calendar()
    k.execute("programma_contenuto", actor="m", args={"canale": "blog", "titolo": "t"})
    assert k.policy.level_for(CALENDAR_ACTION) == AutonomyLevel.L1_PROPOSE
