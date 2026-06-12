import os
import uuid

import pytest

from aios.autonomy import ActionType, AutonomyLevel
from aios.kernel import Kernel, ExecOutcome
from aios.tools import Tool

DSN = os.environ.get("AIOS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="AIOS_TEST_DATABASE_URL not set")


@pytest.fixture
def kernel_and_action():
    k = Kernel.with_postgres(DSN)
    action = ActionType("test", f"persist.{uuid.uuid4().hex}")
    calls = []
    k.register_tool(Tool(name="do_it", action_type=action,
                         run=lambda **kw: calls.append(kw) or {"ok": True}))
    yield k, action, calls
    with k._conn.cursor() as cur:
        cur.execute("delete from aios_audit where action_key = %s", (action.key,))
        cur.execute("delete from aios_policy_state where action_key = %s", (action.key,))
        cur.execute("delete from aios_approvals where action_key = %s", (action.key,))
    k._conn.commit()
    k._conn.close()


def test_full_arc_persists(kernel_and_action):
    k, action, calls = kernel_and_action

    assert k.execute("do_it", actor="t", args={}).outcome == ExecOutcome.DENIED

    k.policy.set_level(action, AutonomyLevel.L1_PROPOSE)
    res = k.execute("do_it", actor="t", args={"x": 1})
    assert res.outcome == ExecOutcome.QUEUED
    run = k.resolve_approval(res.approval_id, approve=True)
    assert run.outcome == ExecOutcome.EXECUTED
    assert calls == [{"x": 1}]

    k2 = Kernel.with_postgres(DSN)
    try:
        assert k2.policy.level_for(action) == AutonomyLevel.L1_PROPOSE
        assert k2.policy._state(action).streak == 1
        events = [r.event for r in k2.audit.records() if r.action_key == action.key]
        assert "denied" in events and "proposed" in events and "executed" in events
    finally:
        k2._conn.close()
