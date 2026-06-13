from aios.autonomy import AutonomyLevel
from aios.policy import PolicyState
from aios.approvals import Approval, ApprovalStatus
from aios.store.memory import (
    InMemoryAuditBackend,
    InMemoryPolicyStateStore,
    InMemoryApprovalBackend,
)


def test_audit_backend_appends_with_monotonic_seq():
    b = InMemoryAuditBackend()
    r1 = b.append(action_key="a.b", event="executed", actor="x", detail={"n": 1})
    r2 = b.append(action_key="a.b", event="executed", actor="x", detail={})
    assert (r1.seq, r2.seq) == (1, 2)
    assert b.list_records()[0].detail == {"n": 1}
    b.list_records().clear()
    assert len(b.list_records()) == 2  # defensive copy


def test_policy_state_store_get_defaults_and_save():
    s = InMemoryPolicyStateStore()
    st = s.get("marketing.social.publish_post")
    assert st.level == AutonomyLevel.L0_OBSERVE and st.streak == 0
    st.level = AutonomyLevel.L1_PROPOSE
    st.streak = 4
    s.save("marketing.social.publish_post", st)
    assert s.get("marketing.social.publish_post").streak == 4


def test_approval_backend_add_get_and_list_pending():
    b = InMemoryApprovalBackend()
    appr = b.add(action_key="a.b", actor="x", payload={"k": "v"})
    assert appr.id == 1 and appr.status == ApprovalStatus.PENDING
    assert b.get(appr.id).payload == {"k": "v"}
    assert [a.id for a in b.pending()] == [appr.id]
    appr.status = ApprovalStatus.APPROVED
    b.save(appr)
    assert b.pending() == []
