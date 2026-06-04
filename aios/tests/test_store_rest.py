from aios.autonomy import AutonomyLevel
from aios.policy import PolicyState
from aios.approvals import ApprovalStatus
from aios.store.rest import RestAuditBackend, RestPolicyStateStore, RestApprovalBackend


class FakeClient:
    def __init__(self):
        self.tables = {"aios_audit": [], "aios_policy_state": [], "aios_approvals": []}
        self._seq = 0
        self._id = 0

    def select(self, table, params):
        rows = self.tables[table]
        for k, v in params.items():
            if k in ("select", "order"):
                continue
            if isinstance(v, str) and v.startswith("eq."):
                want = v[3:]
                rows = [r for r in rows if str(r.get(k)) == want]
        return list(rows)

    def insert(self, table, row):
        row = dict(row)
        if table == "aios_audit":
            self._seq += 1
            row["seq"] = self._seq
        if table == "aios_approvals":
            self._id += 1
            row["id"] = self._id
            row.setdefault("status", "PENDING")
            row.setdefault("clean", False)
            row.setdefault("reason", None)
        self.tables[table].append(row)
        return [row]

    def upsert(self, table, row, *, on_conflict):
        rows = self.tables[table]
        for r in rows:
            if r.get(on_conflict) == row.get(on_conflict):
                r.update(row)
                return [r]
        rows.append(dict(row))
        return [row]

    def update(self, table, filters, patch):
        target = filters.get("id", "").replace("eq.", "")
        out = []
        for r in self.tables[table]:
            if str(r.get("id")) == target:
                r.update(patch)
                out.append(r)
        return out


def test_audit_roundtrip():
    b = RestAuditBackend(FakeClient())
    r1 = b.append(action_key="a.b", event="executed", actor="x", detail={"n": 1})
    r2 = b.append(action_key="a.b", event="denied", actor="x", detail={})
    assert r1.seq == 1 and r2.seq == 2
    recs = b.list_records()
    assert [r.event for r in recs] == ["executed", "denied"]
    assert recs[0].detail == {"n": 1}


def test_policy_state_roundtrip_and_default():
    s = RestPolicyStateStore(FakeClient())
    assert s.get("marketing.x").level == AutonomyLevel.L0_OBSERVE
    st = PolicyState(level=AutonomyLevel.L1_PROPOSE, streak=3, capped_at=AutonomyLevel.L1_PROPOSE)
    s.save("marketing.x", st)
    got = s.get("marketing.x")
    assert got.level == AutonomyLevel.L1_PROPOSE and got.streak == 3
    assert got.capped_at == AutonomyLevel.L1_PROPOSE


def test_approval_roundtrip():
    b = RestApprovalBackend(FakeClient())
    a = b.add(action_key="a.b", actor="x", payload={"k": "v"})
    assert a.id == 1 and a.status == ApprovalStatus.PENDING
    assert b.get(1).payload == {"k": "v"}
    assert [x.id for x in b.pending()] == [1]
    a.status = ApprovalStatus.APPROVED
    a.clean = True
    b.save(a)
    assert b.pending() == []
    assert b.get(1).status == ApprovalStatus.APPROVED
