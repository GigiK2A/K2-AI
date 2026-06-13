from aios.audit import AuditLog, AuditRecord


def test_append_and_list():
    log = AuditLog()
    rec = log.append(action_key="marketing.social.publish_post",
                     event="proposed", actor="marketing_agent", detail={"post_id": 7})
    assert isinstance(rec, AuditRecord)
    assert rec.seq == 1
    assert log.records()[0].event == "proposed"


def test_seq_is_monotonic():
    log = AuditLog()
    log.append(action_key="a.b", event="executed", actor="x", detail={})
    second = log.append(action_key="a.b", event="executed", actor="x", detail={})
    assert second.seq == 2


def test_records_is_a_copy():
    log = AuditLog()
    log.append(action_key="a.b", event="executed", actor="x", detail={})
    log.records().clear()
    assert len(log.records()) == 1
