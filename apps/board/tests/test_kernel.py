import pytest

from aios.autonomy import ActionType, AutonomyLevel
from aios.kernel import Kernel, ExecOutcome
from aios.tools import Tool

PUBLISH = ActionType("marketing", "social.publish_post")


def _kernel_with_publish():
    k = Kernel()
    calls = []
    k.register_tool(Tool(name="publish_post", action_type=PUBLISH,
                         run=lambda **kw: calls.append(kw) or {"ok": True}))
    return k, calls


def test_readonly_tool_always_executes():
    k = Kernel()
    k.register_tool(Tool(name="read_insights", action_type=None, readonly=True,
                         run=lambda **kw: {"reach": 1000}))
    res = k.execute("read_insights", actor="marketing_agent", args={})
    assert res.outcome == ExecOutcome.EXECUTED
    assert res.result == {"reach": 1000}


def test_l0_action_is_denied_and_audited():
    k, calls = _kernel_with_publish()
    res = k.execute("publish_post", actor="marketing_agent", args={"caption": "ciao"})
    assert res.outcome == ExecOutcome.DENIED
    assert calls == []
    assert k.audit.records()[-1].event == "denied"


def test_l1_action_is_queued_not_run():
    k, calls = _kernel_with_publish()
    k.policy.set_level(PUBLISH, AutonomyLevel.L1_PROPOSE)
    res = k.execute("publish_post", actor="marketing_agent", args={"caption": "ciao"})
    assert res.outcome == ExecOutcome.QUEUED
    assert calls == []
    assert k.approvals.pending()[0].id == res.approval_id
    assert k.audit.records()[-1].event == "proposed"


def test_l2_action_runs_immediately():
    k, calls = _kernel_with_publish()
    k.policy.set_level(PUBLISH, AutonomyLevel.L2_ROUTINE)
    res = k.execute("publish_post", actor="marketing_agent", args={"caption": "ciao"})
    assert res.outcome == ExecOutcome.EXECUTED
    assert calls == [{"caption": "ciao"}]
    assert k.audit.records()[-1].event == "executed"


def test_killswitch_blocks_execution():
    k, calls = _kernel_with_publish()
    k.policy.set_level(PUBLISH, AutonomyLevel.L2_ROUTINE)
    k.killswitch.engage(reason="stop")
    res = k.execute("publish_post", actor="marketing_agent", args={"caption": "ciao"})
    assert res.outcome == ExecOutcome.DENIED
    assert calls == []
    assert k.audit.records()[-1].event == "blocked_killswitch"


def test_resolving_approval_runs_tool_and_records_outcome():
    k, calls = _kernel_with_publish()
    k.policy.set_level(PUBLISH, AutonomyLevel.L1_PROPOSE)
    res = k.execute("publish_post", actor="marketing_agent", args={"caption": "ciao"})
    run_res = k.resolve_approval(res.approval_id, approve=True)
    assert run_res.outcome == ExecOutcome.EXECUTED
    assert calls == [{"caption": "ciao"}]
    assert k.policy._state(PUBLISH).streak == 1


def test_rejecting_approval_does_not_run_and_resets_streak():
    k, calls = _kernel_with_publish()
    k.policy.set_level(PUBLISH, AutonomyLevel.L1_PROPOSE)
    res = k.execute("publish_post", actor="marketing_agent", args={"caption": "ciao"})
    run_res = k.resolve_approval(res.approval_id, approve=False, reason="off-brand")
    assert run_res.outcome == ExecOutcome.DENIED
    assert calls == []
    assert k.policy._state(PUBLISH).streak == 0


def test_resolve_unknown_approval_raises_keyerror():
    k, _ = _kernel_with_publish()
    with pytest.raises(KeyError):
        k.resolve_approval(999, approve=True)


def test_double_resolve_raises_valueerror():
    k, calls = _kernel_with_publish()
    k.policy.set_level(PUBLISH, AutonomyLevel.L1_PROPOSE)
    res = k.execute("publish_post", actor="marketing_agent", args={"caption": "ciao"})
    k.resolve_approval(res.approval_id, approve=True)
    with pytest.raises(ValueError):
        k.resolve_approval(res.approval_id, approve=True)
    assert calls == [{"caption": "ciao"}]  # tool ran exactly once


def test_killswitch_blocks_queued_approval_execution():
    k, calls = _kernel_with_publish()
    k.policy.set_level(PUBLISH, AutonomyLevel.L1_PROPOSE)
    res = k.execute("publish_post", actor="marketing_agent", args={"caption": "ciao"})
    k.killswitch.engage(reason="stop")
    run_res = k.resolve_approval(res.approval_id, approve=True)
    assert run_res.outcome == ExecOutcome.DENIED
    assert calls == []  # tool did NOT run despite prior approval
    assert k.audit.records()[-1].event == "blocked_killswitch"


def test_raising_tool_is_audited_then_reraised():
    k = Kernel()
    boom = ActionType("marketing", "social.publish_post")
    def explode(**kw):
        raise RuntimeError("api down")
    k.register_tool(Tool(name="publish_post", action_type=boom, run=explode))
    k.policy.set_level(boom, AutonomyLevel.L2_ROUTINE)
    with pytest.raises(RuntimeError):
        k.execute("publish_post", actor="marketing_agent", args={"caption": "x"})
    assert k.audit.records()[-1].event == "error"
    assert k.audit.records()[-1].detail["error"] == "api down"
