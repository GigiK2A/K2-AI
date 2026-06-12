from aios.approvals import ApprovalQueue, Approval, ApprovalStatus


def test_enqueue_returns_pending():
    q = ApprovalQueue()
    appr = q.enqueue(action_key="marketing.social.publish_post",
                     actor="marketing_agent", payload={"caption": "ciao"})
    assert isinstance(appr, Approval)
    assert appr.status == ApprovalStatus.PENDING
    assert q.pending()[0].id == appr.id


def test_approve_removes_from_pending_and_is_clean():
    q = ApprovalQueue()
    appr = q.enqueue(action_key="a.b", actor="x", payload={})
    resolved = q.approve(appr.id)
    assert resolved.status == ApprovalStatus.APPROVED
    assert resolved.clean is True
    assert q.pending() == []


def test_edit_then_approve_is_not_clean():
    q = ApprovalQueue()
    appr = q.enqueue(action_key="a.b", actor="x", payload={"caption": "ciao"})
    resolved = q.approve(appr.id, edited_payload={"caption": "ciao corretto"})
    assert resolved.status == ApprovalStatus.APPROVED
    assert resolved.clean is False
    assert resolved.payload == {"caption": "ciao corretto"}


def test_reject_is_not_clean():
    q = ApprovalQueue()
    appr = q.enqueue(action_key="a.b", actor="x", payload={})
    resolved = q.reject(appr.id, reason="off-brand")
    assert resolved.status == ApprovalStatus.REJECTED
    assert resolved.clean is False
    assert resolved.reason == "off-brand"
