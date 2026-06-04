# AIOS Fase 1a — Persistent Kernel (Supabase) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the AIOS kernel durable memory: audit log, policy state, and approvals persist to Supabase Postgres so nothing is lost on restart, while the in-memory mode stays the default for fast tests.

**Architecture:** A dependency-injection seam. Each stateful component (`AuditLog`, `PolicyEngine`, `ApprovalQueue`) delegates storage to a *backend* it receives in its constructor, defaulting to an in-memory backend that reproduces today's behavior exactly (so all 38 Fase 0 tests stay green). Parallel Postgres backends implement the same protocols using psycopg3 against three already-created tables (`aios_audit`, `aios_policy_state`, `aios_approvals`). The `Kernel` gains a `Kernel.with_postgres(dsn)` constructor that wires the Postgres backends.

**Tech Stack:** Python 3.12, pytest, psycopg3 (`psycopg[binary]`) — first runtime dependency, required for Postgres access. Supabase project KAI (`uiuvwzrmrdqbfajguuab`), tables already migrated.

**DB is already provisioned.** Tables `aios_audit`, `aios_policy_state`, `aios_approvals` exist in KAI with RLS enabled (service-role only). This plan does NOT create tables.

**Integration tests** connect via a `AIOS_TEST_DATABASE_URL` env var and are **skipped when it is not set** (so the suite stays green offline). Each integration test isolates itself with a unique `action_key` prefix and cleans up its own rows.

---

## File Structure

```
aios/src/aios/
├── db.py                      # NEW: psycopg connection helper (reads DSN)
├── store/
│   ├── __init__.py            # NEW: backend protocols + exports
│   ├── memory.py              # NEW: in-memory backends (default)
│   └── postgres.py            # NEW: Postgres backends
├── audit.py                   # MODIFY: AuditLog delegates to an AuditBackend
├── policy.py                  # MODIFY: PolicyEngine delegates to a PolicyStateStore
├── approvals.py               # MODIFY: ApprovalQueue delegates to an ApprovalBackend
└── kernel.py                  # MODIFY: add Kernel.with_postgres(dsn)
aios/tests/
├── test_store_memory.py       # NEW: in-memory backends behave like the originals
├── test_store_postgres.py     # NEW: integration (skipped without AIOS_TEST_DATABASE_URL)
└── (existing tests unchanged — must stay green)
```

**Backward-compatibility rule for every MODIFY:** new constructor parameters are keyword-only WITH defaults that select the in-memory backend. No existing call site or test changes. Run the full suite after each task to confirm 38 (then more) green.

---

### Task 1: Add psycopg dependency and connection helper

**Files:**
- Modify: `aios/pyproject.toml`
- Create: `aios/src/aios/db.py`
- Test: `aios/tests/test_db.py`

- [ ] **Step 1: Add the dependency to `aios/pyproject.toml`**

Add a `dependencies` array under `[project]` (place it right after the `requires-python` line):
```toml
dependencies = ["psycopg[binary]>=3.1"]
```

- [ ] **Step 2: Write the failing test `aios/tests/test_db.py`**

```python
import pytest

from aios.db import dsn_from_env, MissingDSNError


def test_dsn_from_env_reads_var(monkeypatch):
    monkeypatch.setenv("AIOS_TEST_DATABASE_URL", "postgresql://x")
    assert dsn_from_env("AIOS_TEST_DATABASE_URL") == "postgresql://x"


def test_dsn_from_env_missing_raises(monkeypatch):
    monkeypatch.delenv("AIOS_TEST_DATABASE_URL", raising=False)
    with pytest.raises(MissingDSNError):
        dsn_from_env("AIOS_TEST_DATABASE_URL")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd aios && .venv/bin/pip install -e ".[dev]" && .venv/bin/pytest tests/test_db.py -q`
Expected: FAIL ("No module named 'aios.db'"). (The pip install also pulls psycopg.)

- [ ] **Step 4: Write `aios/src/aios/db.py`**

```python
from __future__ import annotations

import os


class MissingDSNError(RuntimeError):
    """Raised when a required database DSN env var is not set."""


def dsn_from_env(var_name: str) -> str:
    dsn = os.environ.get(var_name)
    if not dsn:
        raise MissingDSNError(f"environment variable {var_name} is not set")
    return dsn
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd aios && .venv/bin/pytest tests/test_db.py -q`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/pyproject.toml aios/src/aios/db.py aios/tests/test_db.py
git commit -m "feat(aios): add psycopg dependency and DSN helper"
```

---

### Task 2: Backend protocols + in-memory backends

**Files:**
- Create: `aios/src/aios/store/__init__.py`
- Create: `aios/src/aios/store/memory.py`
- Test: `aios/tests/test_store_memory.py`

This extracts the storage behavior currently embedded in `AuditLog`/`PolicyEngine`/`ApprovalQueue` into reusable backends. The protocols define exactly what Postgres must also implement.

- [ ] **Step 1: Write the failing test `aios/tests/test_store_memory.py`**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aios && .venv/bin/pytest tests/test_store_memory.py -q`
Expected: FAIL ("No module named 'aios.store'").

- [ ] **Step 3: Write `aios/src/aios/store/__init__.py` (protocols)**

```python
from __future__ import annotations

from typing import Any, Protocol

from aios.audit import AuditRecord
from aios.approvals import Approval
from aios.policy import PolicyState


class AuditBackend(Protocol):
    def append(self, *, action_key: str, event: str, actor: str,
               detail: dict[str, Any]) -> AuditRecord: ...
    def list_records(self) -> list[AuditRecord]: ...


class PolicyStateStore(Protocol):
    def get(self, action_key: str) -> PolicyState: ...
    def save(self, action_key: str, state: PolicyState) -> None: ...


class ApprovalBackend(Protocol):
    def add(self, *, action_key: str, actor: str,
            payload: dict[str, Any]) -> Approval: ...
    def get(self, approval_id: int) -> Approval: ...
    def pending(self) -> list[Approval]: ...
    def save(self, approval: Approval) -> None: ...
```

- [ ] **Step 4: Write `aios/src/aios/store/memory.py`**

```python
from __future__ import annotations

from dataclasses import replace
from typing import Any

from aios.audit import AuditRecord
from aios.approvals import Approval, ApprovalStatus
from aios.policy import PolicyState


class InMemoryAuditBackend:
    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def append(self, *, action_key: str, event: str, actor: str,
               detail: dict[str, Any]) -> AuditRecord:
        rec = AuditRecord(seq=len(self._records) + 1, action_key=action_key,
                          event=event, actor=actor, detail=dict(detail))
        self._records.append(rec)
        return rec

    def list_records(self) -> list[AuditRecord]:
        return list(self._records)


class InMemoryPolicyStateStore:
    def __init__(self) -> None:
        self._states: dict[str, PolicyState] = {}

    def get(self, action_key: str) -> PolicyState:
        return self._states.setdefault(action_key, PolicyState())

    def save(self, action_key: str, state: PolicyState) -> None:
        self._states[action_key] = state


class InMemoryApprovalBackend:
    def __init__(self) -> None:
        self._items: dict[int, Approval] = {}
        self._next_id = 1

    def add(self, *, action_key: str, actor: str,
            payload: dict[str, Any]) -> Approval:
        appr = Approval(id=self._next_id, action_key=action_key,
                        actor=actor, payload=dict(payload))
        self._items[appr.id] = appr
        self._next_id += 1
        return appr

    def get(self, approval_id: int) -> Approval:
        if approval_id not in self._items:
            raise KeyError(f"unknown approval_id: {approval_id}")
        return self._items[approval_id]

    def pending(self) -> list[Approval]:
        return [a for a in self._items.values()
                if a.status == ApprovalStatus.PENDING]

    def save(self, approval: Approval) -> None:
        self._items[approval.id] = approval
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd aios && .venv/bin/pytest tests/test_store_memory.py -q`
Expected: 3 passed.

- [ ] **Step 6: Run the FULL suite (no regressions yet — nothing else changed)**

Run: `cd aios && .venv/bin/pytest -q`
Expected: all previously-green tests still pass (40 now).

- [ ] **Step 7: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/store/__init__.py aios/src/aios/store/memory.py aios/tests/test_store_memory.py
git commit -m "feat(aios): storage backend protocols and in-memory backends"
```

---

### Task 3: Refactor AuditLog / PolicyEngine / ApprovalQueue to delegate to backends

**Files:**
- Modify: `aios/src/aios/audit.py`
- Modify: `aios/src/aios/policy.py`
- Modify: `aios/src/aios/approvals.py`

**CRITICAL:** Keep all existing public behavior and signatures. New constructor params are keyword-only with in-memory defaults. After this task the full suite (40) must still pass with ZERO test edits.

- [ ] **Step 1: Refactor `aios/src/aios/audit.py`**

Keep `AuditRecord` exactly as-is. Replace the `AuditLog` class body so it delegates to a backend (default in-memory), preserving the `append(*, action_key, event, actor, detail)` and `records()` API:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from aios.store import AuditBackend


@dataclass(frozen=True)
class AuditRecord:
    seq: int
    action_key: str
    event: str
    actor: str
    detail: dict[str, Any]


class AuditLog:
    def __init__(self, backend: "AuditBackend | None" = None) -> None:
        if backend is None:
            from aios.store.memory import InMemoryAuditBackend
            backend = InMemoryAuditBackend()
        self._backend = backend

    def append(self, *, action_key: str, event: str, actor: str,
               detail: dict[str, Any]) -> AuditRecord:
        return self._backend.append(action_key=action_key, event=event,
                                    actor=actor, detail=detail)

    def records(self) -> list[AuditRecord]:
        return self._backend.list_records()
```

- [ ] **Step 2: Refactor `aios/src/aios/policy.py`**

Keep `Decision` and `PolicyState` as-is. Change `PolicyEngine` to use a `PolicyStateStore` (default in-memory) instead of an internal dict. Every method that reads/mutates state must `get` then `save`:

```python
    def __init__(self, *, promotion_threshold: int = DEFAULT_PROMOTION_THRESHOLD,
                 store=None) -> None:
        if store is None:
            from aios.store.memory import InMemoryPolicyStateStore
            store = InMemoryPolicyStateStore()
        self._store = store
        self._threshold = promotion_threshold

    def _state(self, action: ActionType) -> PolicyState:
        return self._store.get(action.key)

    def level_for(self, action: ActionType) -> AutonomyLevel:
        return self._state(action).level

    def set_level(self, action: ActionType, level: AutonomyLevel) -> None:
        state = self._state(action)
        state.level = level
        state.streak = 0
        self._store.save(action.key, state)

    def decide(self, action: ActionType) -> Decision:
        level = self.level_for(action)
        if level == AutonomyLevel.L0_OBSERVE:
            return Decision.DENY
        if level == AutonomyLevel.L1_PROPOSE:
            return Decision.PROPOSE
        return Decision.EXECUTE

    def set_cap(self, action: ActionType, cap: AutonomyLevel) -> None:
        state = self._state(action)
        state.capped_at = cap
        self._store.save(action.key, state)

    def record_outcome(self, action: ActionType, *, clean: bool) -> None:
        state = self._state(action)
        if not clean:
            state.streak = 0
            self._store.save(action.key, state)
            return
        state.streak += 1
        if (state.level == AutonomyLevel.L1_PROPOSE
                and state.capped_at >= AutonomyLevel.L2_ROUTINE
                and state.streak >= self._threshold):
            state.level = AutonomyLevel.L2_ROUTINE
            state.streak = 0
        self._store.save(action.key, state)
```

Note: existing tests call `pe._state(AT).streak` after operations — still valid, `_state` now reads from the store. The in-memory store returns the same mutable object, so this is behavior-preserving.

- [ ] **Step 3: Refactor `aios/src/aios/approvals.py`**

Keep `ApprovalStatus` and `Approval` as-is. Change `ApprovalQueue` to delegate to an `ApprovalBackend` (default in-memory), preserving the `enqueue(*, action_key, actor, payload)`, `pending()`, `get()`, `approve()`, `reject()` API:

```python
    def __init__(self, backend=None) -> None:
        if backend is None:
            from aios.store.memory import InMemoryApprovalBackend
            backend = InMemoryApprovalBackend()
        self._backend = backend

    def enqueue(self, *, action_key: str, actor: str,
                payload: dict[str, Any]) -> Approval:
        return self._backend.add(action_key=action_key, actor=actor, payload=payload)

    def get(self, approval_id: int) -> Approval:
        return self._backend.get(approval_id)

    def pending(self) -> list[Approval]:
        return self._backend.pending()

    def approve(self, approval_id: int,
                edited_payload: dict[str, Any] | None = None) -> Approval:
        appr = self._backend.get(approval_id)
        appr.status = ApprovalStatus.APPROVED
        if edited_payload is not None:
            appr.payload = dict(edited_payload)
            appr.clean = False
        else:
            appr.clean = True
        self._backend.save(appr)
        return appr

    def reject(self, approval_id: int, *, reason: str) -> Approval:
        appr = self._backend.get(approval_id)
        appr.status = ApprovalStatus.REJECTED
        appr.clean = False
        appr.reason = reason
        self._backend.save(appr)
        return appr
```

- [ ] **Step 4: Run the FULL suite — must be green with no test edits**

Run: `cd aios && .venv/bin/pytest -q`
Expected: all tests pass (40). If any fail, the refactor broke behavior — fix the source, do NOT edit tests.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/audit.py aios/src/aios/policy.py aios/src/aios/approvals.py
git commit -m "refactor(aios): components delegate to injectable storage backends"
```

---

### Task 4: Postgres backends

**Files:**
- Create: `aios/src/aios/store/postgres.py`
- (no unit test here; covered by the integration test in Task 5)

- [ ] **Step 1: Write `aios/src/aios/store/postgres.py`**

```python
from __future__ import annotations

from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from aios.audit import AuditRecord
from aios.approvals import Approval, ApprovalStatus
from aios.policy import PolicyState
from aios.autonomy import AutonomyLevel


class _Base:
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn


class PostgresAuditBackend(_Base):
    def append(self, *, action_key: str, event: str, actor: str,
               detail: dict[str, Any]) -> AuditRecord:
        with self._conn.cursor() as cur:
            cur.execute(
                "insert into aios_audit (action_key, event, actor, detail) "
                "values (%s, %s, %s, %s) returning seq",
                (action_key, event, actor, Jsonb(detail)),
            )
            seq = cur.fetchone()[0]
        self._conn.commit()
        return AuditRecord(seq=seq, action_key=action_key, event=event,
                           actor=actor, detail=dict(detail))

    def list_records(self) -> list[AuditRecord]:
        with self._conn.cursor() as cur:
            cur.execute("select seq, action_key, event, actor, detail "
                        "from aios_audit order by seq")
            rows = cur.fetchall()
        return [AuditRecord(seq=r[0], action_key=r[1], event=r[2],
                            actor=r[3], detail=r[4]) for r in rows]


class PostgresPolicyStateStore(_Base):
    def get(self, action_key: str) -> PolicyState:
        with self._conn.cursor() as cur:
            cur.execute("select level, streak, capped_at from aios_policy_state "
                        "where action_key = %s", (action_key,))
            row = cur.fetchone()
        if row is None:
            return PolicyState()
        return PolicyState(level=AutonomyLevel(row[0]), streak=row[1],
                           capped_at=AutonomyLevel(row[2]))

    def save(self, action_key: str, state: PolicyState) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                "insert into aios_policy_state (action_key, level, streak, capped_at) "
                "values (%s, %s, %s, %s) "
                "on conflict (action_key) do update set "
                "level = excluded.level, streak = excluded.streak, "
                "capped_at = excluded.capped_at, updated_at = now()",
                (action_key, int(state.level), state.streak, int(state.capped_at)),
            )
        self._conn.commit()


class PostgresApprovalBackend(_Base):
    def add(self, *, action_key: str, actor: str,
            payload: dict[str, Any]) -> Approval:
        with self._conn.cursor() as cur:
            cur.execute(
                "insert into aios_approvals (action_key, actor, payload) "
                "values (%s, %s, %s) returning id",
                (action_key, actor, Jsonb(payload)),
            )
            new_id = cur.fetchone()[0]
        self._conn.commit()
        return Approval(id=new_id, action_key=action_key, actor=actor,
                        payload=dict(payload))

    def get(self, approval_id: int) -> Approval:
        with self._conn.cursor() as cur:
            cur.execute("select id, action_key, actor, payload, status, clean, reason "
                        "from aios_approvals where id = %s", (approval_id,))
            row = cur.fetchone()
        if row is None:
            raise KeyError(f"unknown approval_id: {approval_id}")
        return Approval(id=row[0], action_key=row[1], actor=row[2], payload=row[3],
                        status=ApprovalStatus[row[4]], clean=row[5], reason=row[6])

    def pending(self) -> list[Approval]:
        with self._conn.cursor() as cur:
            cur.execute("select id, action_key, actor, payload, status, clean, reason "
                        "from aios_approvals where status = 'PENDING' order by id")
            rows = cur.fetchall()
        return [Approval(id=r[0], action_key=r[1], actor=r[2], payload=r[3],
                         status=ApprovalStatus[r[4]], clean=r[5], reason=r[6])
                for r in rows]

    def save(self, approval: Approval) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                "update aios_approvals set payload = %s, status = %s, clean = %s, "
                "reason = %s, resolved_at = case when %s <> 'PENDING' then now() "
                "else resolved_at end where id = %s",
                (Jsonb(approval.payload), approval.status.name, approval.clean,
                 approval.reason, approval.status.name, approval.id),
            )
        self._conn.commit()
```

- [ ] **Step 2: Verify it imports cleanly**

Run: `cd aios && .venv/bin/python -c "import aios.store.postgres; print('ok')"`
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/store/postgres.py
git commit -m "feat(aios): postgres storage backends"
```

---

### Task 5: Kernel.with_postgres + integration test

**Files:**
- Modify: `aios/src/aios/kernel.py` (add classmethod)
- Test: `aios/tests/test_store_postgres.py`

- [ ] **Step 1: Add `with_postgres` classmethod to `Kernel` in `aios/src/aios/kernel.py`**

Add this import at the top (with the others): `import psycopg`. Then add inside the `Kernel` class:

```python
    @classmethod
    def with_postgres(cls, dsn: str, *, promotion_threshold: int = 10) -> "Kernel":
        from aios.store.postgres import (
            PostgresAuditBackend, PostgresPolicyStateStore, PostgresApprovalBackend,
        )
        conn = psycopg.connect(dsn)
        k = cls(promotion_threshold=promotion_threshold)
        k.audit = AuditLog(PostgresAuditBackend(conn))
        k.policy = PolicyEngine(promotion_threshold=promotion_threshold,
                                store=PostgresPolicyStateStore(conn))
        k.approvals = ApprovalQueue(PostgresApprovalBackend(conn))
        k._conn = conn
        return k
```

(The default `__init__` still builds in-memory components; `with_postgres` swaps in the Postgres-backed ones. `AuditLog`, `PolicyEngine`, `ApprovalQueue` are already imported in kernel.py.)

- [ ] **Step 2: Write the integration test `aios/tests/test_store_postgres.py`**

```python
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
    # unique capability per run so rows never collide with real/other test data
    action = ActionType("test", f"persist.{uuid.uuid4().hex}")
    calls = []
    k.register_tool(Tool(name="do_it", action_type=action,
                         run=lambda **kw: calls.append(kw) or {"ok": True}))
    yield k, action, calls
    # cleanup our rows
    with k._conn.cursor() as cur:
        cur.execute("delete from aios_audit where action_key = %s", (action.key,))
        cur.execute("delete from aios_policy_state where action_key = %s", (action.key,))
        cur.execute("delete from aios_approvals where action_key = %s", (action.key,))
    k._conn.commit()
    k._conn.close()


def test_full_arc_persists(kernel_and_action):
    k, action, calls = kernel_and_action

    # L0 → denied
    assert k.execute("do_it", actor="t", args={}).outcome == ExecOutcome.DENIED

    # promote to L1, propose, approve cleanly → executes and records streak
    k.policy.set_level(action, AutonomyLevel.L1_PROPOSE)
    res = k.execute("do_it", actor="t", args={"x": 1})
    assert res.outcome == ExecOutcome.QUEUED
    run = k.resolve_approval(res.approval_id, approve=True)
    assert run.outcome == ExecOutcome.EXECUTED
    assert calls == [{"x": 1}]

    # state persisted: re-read via a fresh kernel/connection
    k2 = Kernel.with_postgres(DSN)
    try:
        assert k2.policy.level_for(action) == AutonomyLevel.L1_PROPOSE
        assert k2.policy._state(action).streak == 1
        events = [r.event for r in k2.audit.records() if r.action_key == action.key]
        assert "denied" in events and "proposed" in events and "executed" in events
    finally:
        k2._conn.close()
```

- [ ] **Step 3: Run the integration test (requires DB access)**

If `AIOS_TEST_DATABASE_URL` is set to the KAI Postgres connection string:
Run: `cd aios && AIOS_TEST_DATABASE_URL="$AIOS_TEST_DATABASE_URL" .venv/bin/pytest tests/test_store_postgres.py -q`
Expected: 1 passed.

If the env var is NOT available to you, run `cd aios && .venv/bin/pytest tests/test_store_postgres.py -q` and confirm it reports **skipped** (not failed). Report DONE_WITH_CONCERNS noting the live run was not executed.

- [ ] **Step 4: Run the full suite**

Run: `cd aios && .venv/bin/pytest -q`
Expected: all pass; the postgres test passes or is skipped.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/kernel.py aios/tests/test_store_postgres.py
git commit -m "feat(aios): Kernel.with_postgres + persistence integration test"
```

---

## Self-Review

**Spec coverage:** Storage Mgr ④ persistence (spec §2) → Tasks 2-5. Postgres source of truth (spec §2 "DB / source of truth: Postgres su Supabase EU") → KAI project, `aios_` tables. In-memory default preserved for tests → Task 3 backward-compat rule.

**Placeholder scan:** none — all code complete, all commands explicit.

**Type consistency:** `AuditBackend`/`PolicyStateStore`/`ApprovalBackend` protocols (Task 2) match the method signatures used by `AuditLog`/`PolicyEngine`/`ApprovalQueue` after refactor (Task 3) and implemented by Postgres backends (Task 4). `ApprovalStatus[name]` / `.name` round-trip used consistently. `AutonomyLevel(int)` ↔ `int(level)` round-trip in policy store. `Approval`/`AuditRecord`/`PolicyState` dataclasses reused, not redefined.

**Risk note:** Task 3 is the only behavior-risk task (refactor under green tests). Mitigation: in-memory backends in Task 2 replicate the exact original logic; full suite must pass with zero test edits after Task 3.

**Live-DB note:** integration test self-isolates by unique `action_key` and cleans up; skipped without `AIOS_TEST_DATABASE_URL` so offline runs stay green. Tables already provisioned in KAI (RLS on, service-role only).
