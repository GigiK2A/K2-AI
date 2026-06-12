# AIOS Fase 1d — Supabase REST connection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`).

**Goal:** Let the AIOS talk to Supabase by itself over the REST API (PostgREST) with the service_role key — no Postgres password, bypasses RLS (same path n8n uses). Kernel state (audit, policy, approvals) and marketing content persist/read through REST.

**Architecture:** A `SupabaseREST` client wraps PostgREST (`/rest/v1/...`) with an injectable HTTP fetcher (stdlib urllib by default; fake in tests). REST-backed stores implement the SAME backend protocols already used by the kernel (`AuditBackend`, `PolicyStateStore`, `ApprovalBackend`), so `Kernel` works unchanged via injection. `Kernel.with_supabase_rest(url, service_key)` wires them. Content read via REST too. Everything unit-tested offline with a fake fetcher; live test needs `AIOS_SUPABASE_URL` + `AIOS_SUPABASE_SERVICE_KEY`.

**Tech Stack:** Python 3.12, pytest, stdlib urllib (no new dep). Tables already exist: `aios_audit`, `aios_policy_state`, `aios_approvals`, plus `servizi`/`topics`.

**Config (env):** `AIOS_SUPABASE_URL` (e.g. https://uiuvwzrmrdqbfajguuab.supabase.co), `AIOS_SUPABASE_SERVICE_KEY` (service_role JWT).

---

## File Structure
```
aios/src/aios/
├── supabase_rest.py          # SupabaseREST client (select/insert/update/upsert)
└── store/
    └── rest.py               # RestAuditBackend, RestPolicyStateStore, RestApprovalBackend
aios/tests/
├── test_supabase_rest.py     # client URL/headers/verb logic with fake fetcher
└── test_store_rest.py        # backends behave like in-memory, with fake client
```

---

### Task 1: SupabaseREST client

**Files:**
- Create: `aios/src/aios/supabase_rest.py`
- Test: `aios/tests/test_supabase_rest.py`

- [ ] **Step 1: test `aios/tests/test_supabase_rest.py`**

```python
import json
from aios.supabase_rest import SupabaseREST


class FakeHTTP:
    def __init__(self):
        self.requests = []
        self.responses = []
    def __call__(self, *, method, url, headers, body):
        self.requests.append({"method": method, "url": url, "headers": headers,
                              "body": json.loads(body) if body else None})
        return self.responses.pop(0) if self.responses else []


def client():
    http = FakeHTTP()
    c = SupabaseREST(url="https://x.supabase.co", service_key="KEY", fetch=http)
    return c, http


def test_select_builds_url_and_auth_headers():
    c, http = client()
    http.responses = [[{"id": 1}]]
    out = c.select("servizi", {"select": "*", "Stato": "eq.da usare"})
    assert out == [{"id": 1}]
    r = http.requests[0]
    assert r["method"] == "GET"
    assert r["url"].startswith("https://x.supabase.co/rest/v1/servizi?")
    assert "select=%2A" in r["url"] or "select=*" in r["url"]
    assert r["headers"]["apikey"] == "KEY"
    assert r["headers"]["Authorization"] == "Bearer KEY"


def test_insert_returns_representation():
    c, http = client()
    http.responses = [[{"id": 7, "action_key": "a.b"}]]
    out = c.insert("aios_audit", {"action_key": "a.b"})
    assert out == [{"id": 7, "action_key": "a.b"}]
    r = http.requests[0]
    assert r["method"] == "POST"
    assert r["headers"]["Prefer"] == "return=representation"
    assert r["body"] == {"action_key": "a.b"}


def test_upsert_sets_merge_prefer_and_on_conflict():
    c, http = client()
    http.responses = [[{"action_key": "a.b"}]]
    c.upsert("aios_policy_state", {"action_key": "a.b", "level": 1}, on_conflict="action_key")
    r = http.requests[0]
    assert r["method"] == "POST"
    assert "on_conflict=action_key" in r["url"]
    assert "resolution=merge-duplicates" in r["headers"]["Prefer"]


def test_update_uses_patch_and_filters():
    c, http = client()
    http.responses = [[{"id": 3, "status": "APPROVED"}]]
    c.update("aios_approvals", {"id": "eq.3"}, {"status": "APPROVED"})
    r = http.requests[0]
    assert r["method"] == "PATCH"
    assert "id=eq.3" in r["url"]
    assert r["body"] == {"status": "APPROVED"}
```

- [ ] **Step 2: run** `cd aios && .venv/bin/pytest tests/test_supabase_rest.py -q` → FAIL (no module).

- [ ] **Step 3: `aios/src/aios/supabase_rest.py`**

```python
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Callable

# fetch(method, url, headers, body) -> parsed JSON (list/dict)
HTTP = Callable[..., Any]


def _urllib_http(*, method: str, url: str, headers: dict[str, str],
                 body: str | None) -> Any:
    data = body.encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else []


class SupabaseRESTError(RuntimeError):
    pass


class SupabaseREST:
    def __init__(self, *, url: str, service_key: str, fetch: HTTP = _urllib_http) -> None:
        self._base = url.rstrip("/") + "/rest/v1"
        self._key = service_key
        self._fetch = fetch

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h = {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        }
        if extra:
            h.update(extra)
        return h

    def select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        qs = urllib.parse.urlencode(params, safe="*")
        url = f"{self._base}/{table}?{qs}"
        return self._fetch(method="GET", url=url, headers=self._headers(), body=None)

    def insert(self, table: str, row: dict[str, Any]) -> list[dict[str, Any]]:
        url = f"{self._base}/{table}"
        return self._fetch(method="POST", url=url,
                           headers=self._headers({"Prefer": "return=representation"}),
                           body=json.dumps(row))

    def upsert(self, table: str, row: dict[str, Any], *, on_conflict: str) -> list[dict[str, Any]]:
        url = f"{self._base}/{table}?on_conflict={on_conflict}"
        return self._fetch(method="POST", url=url,
                           headers=self._headers(
                               {"Prefer": "return=representation,resolution=merge-duplicates"}),
                           body=json.dumps(row))

    def update(self, table: str, filters: dict[str, str],
               patch: dict[str, Any]) -> list[dict[str, Any]]:
        qs = urllib.parse.urlencode(filters, safe="*")
        url = f"{self._base}/{table}?{qs}"
        return self._fetch(method="PATCH", url=url,
                           headers=self._headers({"Prefer": "return=representation"}),
                           body=json.dumps(patch))
```

- [ ] **Step 4: run** `cd aios && .venv/bin/pytest tests/test_supabase_rest.py -q` → 4 passed.
- [ ] **Step 5: full suite + commit**
```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/supabase_rest.py aios/tests/test_supabase_rest.py
git commit -m "feat(aios): Supabase REST client (PostgREST, service-role)"
```

---

### Task 2: REST-backed kernel stores + content + Kernel.with_supabase_rest

**Files:**
- Create: `aios/src/aios/store/rest.py`
- Modify: `aios/src/aios/kernel.py` (add `with_supabase_rest` classmethod)
- Test: `aios/tests/test_store_rest.py`

- [ ] **Step 1: test `aios/tests/test_store_rest.py`**

```python
from aios.autonomy import AutonomyLevel
from aios.policy import PolicyState
from aios.approvals import ApprovalStatus
from aios.store.rest import RestAuditBackend, RestPolicyStateStore, RestApprovalBackend


class FakeClient:
    """Mimics SupabaseREST with in-memory tables."""
    def __init__(self):
        self.tables = {"aios_audit": [], "aios_policy_state": [], "aios_approvals": []}
        self._seq = 0
        self._id = 0
    def select(self, table, params):
        rows = self.tables[table]
        # support action_key=eq.X and status=eq.X and id=eq.N
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
    assert s.get("marketing.x").level == AutonomyLevel.L0_OBSERVE  # default when absent
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
```

- [ ] **Step 2: run** `cd aios && .venv/bin/pytest tests/test_store_rest.py -q` → FAIL.

- [ ] **Step 3: `aios/src/aios/store/rest.py`**

```python
from __future__ import annotations

from typing import Any

from aios.audit import AuditRecord
from aios.approvals import Approval, ApprovalStatus
from aios.autonomy import AutonomyLevel
from aios.policy import PolicyState


class RestAuditBackend:
    def __init__(self, client: Any) -> None:
        self._c = client

    def append(self, *, action_key: str, event: str, actor: str,
               detail: dict[str, Any]) -> AuditRecord:
        rows = self._c.insert("aios_audit", {
            "action_key": action_key, "event": event, "actor": actor, "detail": detail})
        row = rows[0]
        return AuditRecord(seq=row["seq"], action_key=action_key, event=event,
                           actor=actor, detail=dict(detail))

    def list_records(self) -> list[AuditRecord]:
        rows = self._c.select("aios_audit", {"select": "*", "order": "seq.asc"})
        return [AuditRecord(seq=r["seq"], action_key=r["action_key"], event=r["event"],
                            actor=r["actor"], detail=r.get("detail") or {}) for r in rows]


class RestPolicyStateStore:
    def __init__(self, client: Any) -> None:
        self._c = client

    def get(self, action_key: str) -> PolicyState:
        rows = self._c.select("aios_policy_state",
                              {"select": "*", "action_key": f"eq.{action_key}"})
        if not rows:
            return PolicyState()
        r = rows[0]
        return PolicyState(level=AutonomyLevel(r["level"]), streak=r["streak"],
                           capped_at=AutonomyLevel(r["capped_at"]))

    def save(self, action_key: str, state: PolicyState) -> None:
        self._c.upsert("aios_policy_state", {
            "action_key": action_key, "level": int(state.level),
            "streak": state.streak, "capped_at": int(state.capped_at)},
            on_conflict="action_key")


class RestApprovalBackend:
    def __init__(self, client: Any) -> None:
        self._c = client

    def add(self, *, action_key: str, actor: str, payload: dict[str, Any]) -> Approval:
        rows = self._c.insert("aios_approvals", {
            "action_key": action_key, "actor": actor, "payload": payload})
        r = rows[0]
        return Approval(id=r["id"], action_key=action_key, actor=actor,
                        payload=dict(payload))

    def get(self, approval_id: int) -> Approval:
        rows = self._c.select("aios_approvals", {"select": "*", "id": f"eq.{approval_id}"})
        if not rows:
            raise KeyError(f"unknown approval_id: {approval_id}")
        r = rows[0]
        return Approval(id=r["id"], action_key=r["action_key"], actor=r["actor"],
                        payload=r.get("payload") or {},
                        status=ApprovalStatus[r["status"]], clean=r["clean"],
                        reason=r.get("reason"))

    def pending(self) -> list[Approval]:
        rows = self._c.select("aios_approvals",
                              {"select": "*", "status": "eq.PENDING", "order": "id.asc"})
        return [Approval(id=r["id"], action_key=r["action_key"], actor=r["actor"],
                         payload=r.get("payload") or {},
                         status=ApprovalStatus[r["status"]], clean=r["clean"],
                         reason=r.get("reason")) for r in rows]

    def save(self, approval: Approval) -> None:
        self._c.update("aios_approvals", {"id": f"eq.{approval.id}"}, {
            "payload": approval.payload, "status": approval.status.name,
            "clean": approval.clean, "reason": approval.reason})
```

- [ ] **Step 4: add `with_supabase_rest` to `Kernel` in `aios/src/aios/kernel.py`**

```python
    @classmethod
    def with_supabase_rest(cls, url: str, service_key: str, *,
                           promotion_threshold: int = 10) -> "Kernel":
        from aios.supabase_rest import SupabaseREST
        from aios.store.rest import (
            RestAuditBackend, RestPolicyStateStore, RestApprovalBackend,
        )
        client = SupabaseREST(url=url, service_key=service_key)
        k = cls(promotion_threshold=promotion_threshold)
        k.audit = AuditLog(RestAuditBackend(client))
        k.policy = PolicyEngine(promotion_threshold=promotion_threshold,
                                store=RestPolicyStateStore(client))
        k.approvals = ApprovalQueue(RestApprovalBackend(client))
        k._supabase = client
        return k
```

- [ ] **Step 5: run** `cd aios && .venv/bin/pytest tests/test_store_rest.py -q` → 3 passed.
- [ ] **Step 6: full suite + commit**
```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/store/rest.py aios/src/aios/kernel.py aios/tests/test_store_rest.py
git commit -m "feat(aios): REST-backed kernel stores + Kernel.with_supabase_rest"
```

---

### Task 3: REST content tools + live runner

**Files:**
- Modify: `aios/src/aios/sources/tools.py` (add `content_tools_rest`)
- Create: `aios/run_marketing_supabase.py`

- [ ] **Step 1: add to `aios/src/aios/sources/tools.py`**

```python
def content_tools_rest(client: Any) -> list[Tool]:
    return [
        Tool(name="leggi_servizi", action_type=None, readonly=True,
             run=lambda **_: client.select("servizi", {"select": "*", "order": "id.asc"})),
        Tool(name="leggi_topics", action_type=None, readonly=True,
             run=lambda **_: client.select("topics", {"select": "*", "order": "id.asc"})),
    ]
```

- [ ] **Step 2: create `aios/run_marketing_supabase.py`**

```python
"""Marketing agent fully on Supabase REST (state persists) + live IG + Claude.
Env: AIOS_SUPABASE_URL, AIOS_SUPABASE_SERVICE_KEY, AIOS_IG_TOKEN, ANTHROPIC_API_KEY.
Run: cd aios && set -a && . ./.env && set +a && .venv/bin/python run_marketing_supabase.py
"""
import os
from aios.kernel import Kernel
from aios.founder import default_founder_model
from aios.llm import AnthropicLLM
from aios.skills import SkillLibrary
from aios.sources.instagram import InstagramClient
from aios.sources.tools import content_tools_rest, instagram_tools
from aios.agents.marketing import MarketingAgent


def main() -> None:
    k = Kernel.with_supabase_rest(os.environ["AIOS_SUPABASE_URL"],
                                  os.environ["AIOS_SUPABASE_SERVICE_KEY"])
    for t in content_tools_rest(k._supabase):
        k.register_tool(t)
    ig = InstagramClient(token=os.environ["AIOS_IG_TOKEN"],
                         ig_user_id=os.environ.get("AIOS_IG_USER_ID", "17841429842127461"))
    for t in instagram_tools(ig):
        k.register_tool(t)

    fm = default_founder_model()
    posts = k.execute("leggi_post_ig", actor="bootstrap", args={"limit": 10}).result
    fm.voice_samples = [p.get("caption", "") for p in posts if p.get("caption")][:5]

    agent = MarketingAgent(kernel=k, llm=AnthropicLLM(), founder=fm, skills=SkillLibrary())
    result = agent.run()
    print(f"{len(result.proposals)} proposte scritte in Supabase (aios_approvals, L1).")
    for appr in k.approvals.pending():
        print(f"  [#{appr.id}] {appr.payload.get('tipo')}: {appr.payload.get('titolo')}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: verify parse** `cd aios && .venv/bin/python -c "import ast; ast.parse(open('run_marketing_supabase.py').read()); print('ok')"`
- [ ] **Step 4: full suite + commit**
```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/sources/tools.py aios/run_marketing_supabase.py
git commit -m "feat(aios): REST content tools + Supabase-backed marketing runner"
```

---

## Self-Review

**Spec coverage:** Postgres/Supabase as source of truth (spec §2) now reachable by the app via REST (service-role) — kernel state persists, content reads live. Same backend protocols as in-memory/postgres → Kernel unchanged.

**Placeholder scan:** none.

**Type consistency:** REST backends return the same `AuditRecord`/`PolicyState`/`Approval` types; `ApprovalStatus[name]`/`.name` round-trip; `AutonomyLevel(int)`/`int()` round-trip. `SupabaseREST` verbs (select/insert/upsert/update) match what the backends call.

**Live verification (controller):** with `AIOS_SUPABASE_URL` + `AIOS_SUPABASE_SERVICE_KEY` set, run `run_marketing_supabase.py` → proposals appear in `aios_approvals` (verify via MCP select). Until the service key is provided, only fake-fetcher unit tests run.
