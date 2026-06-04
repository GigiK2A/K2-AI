# AIOS Fase 0 — Kernel Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the testable in-memory core of the K2-AI AIOS kernel — the autonomy ladder, audit log, kill-switch, tool registry, approval queue, and a Kernel facade that wires them — as a standalone Python library.

**Architecture:** Pure Python library, no DB/UI/network. The kernel mediates every action: a tool call is consulted against the autonomy policy (L0 deny / L1 queue-for-approval / L2-L3 execute), the kill-switch can block everything, and every decision is appended to an immutable audit log. Storage is an in-memory implementation behind a narrow interface so Postgres persistence can be swapped in later (Fase 1) without touching kernel logic.

**Tech Stack:** Python 3.12, pytest, dataclasses + enums (no external runtime deps in Fase 0).

---

## File Structure

```
aios/
├── pyproject.toml                 # package + pytest config
├── src/aios/
│   ├── __init__.py                # version + public exports
│   ├── autonomy.py                # AutonomyLevel enum, ActionType, promotion threshold
│   ├── audit.py                   # AuditRecord, AuditLog (append-only)
│   ├── killswitch.py              # KillSwitch (global block flag)
│   ├── policy.py                  # PolicyState, PolicyEngine (check + record_outcome + promotion)
│   ├── approvals.py               # Approval, ApprovalQueue (approve/edit/reject)
│   ├── tools.py                   # Tool, ToolRegistry
│   └── kernel.py                  # Kernel facade (execute → wires policy+audit+killswitch+queue)
└── tests/
    ├── test_autonomy.py
    ├── test_audit.py
    ├── test_killswitch.py
    ├── test_policy.py
    ├── test_approvals.py
    ├── test_tools.py
    └── test_kernel.py
```

**Responsibility per file:** each kernel concern is one module with one job. `kernel.py` is the only module that imports the others; the rest are independent and unit-testable in isolation.

---

### Task 1: Project scaffold

**Files:**
- Create: `aios/pyproject.toml`
- Create: `aios/src/aios/__init__.py`
- Create: `aios/tests/test_smoke.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "aios"
version = "0.0.1"
description = "K2-AI AIOS kernel core"
requires-python = ">=3.12"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[project.optional-dependencies]
dev = ["pytest>=8"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 2: Write `src/aios/__init__.py`**

```python
__version__ = "0.0.1"
```

- [ ] **Step 3: Write smoke test `tests/test_smoke.py`**

```python
import aios


def test_version():
    assert aios.__version__ == "0.0.1"
```

- [ ] **Step 4: Create venv, install, run**

Run:
```bash
cd aios && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]" && .venv/bin/pytest -q
```
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
echo "aios/.venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo ".pytest_cache/" >> .gitignore
git add aios/pyproject.toml aios/src/aios/__init__.py aios/tests/test_smoke.py .gitignore
git commit -m "feat(aios): scaffold kernel package"
```

---

### Task 2: Autonomy levels and action types

**Files:**
- Create: `aios/src/aios/autonomy.py`
- Test: `aios/tests/test_autonomy.py`

- [ ] **Step 1: Write the failing test**

```python
from aios.autonomy import AutonomyLevel, ActionType, DEFAULT_PROMOTION_THRESHOLD


def test_levels_are_ordered():
    assert AutonomyLevel.L0_OBSERVE < AutonomyLevel.L1_PROPOSE
    assert AutonomyLevel.L1_PROPOSE < AutonomyLevel.L2_ROUTINE
    assert AutonomyLevel.L2_ROUTINE < AutonomyLevel.L3_AUTO


def test_action_type_key():
    at = ActionType(domain="marketing", capability="social.publish_post")
    assert at.key == "marketing.social.publish_post"


def test_default_threshold():
    assert DEFAULT_PROMOTION_THRESHOLD == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aios && .venv/bin/pytest tests/test_autonomy.py -q`
Expected: FAIL with "No module named 'aios.autonomy'".

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

DEFAULT_PROMOTION_THRESHOLD = 10


class AutonomyLevel(IntEnum):
    L0_OBSERVE = 0
    L1_PROPOSE = 1
    L2_ROUTINE = 2
    L3_AUTO = 3


@dataclass(frozen=True)
class ActionType:
    domain: str
    capability: str

    @property
    def key(self) -> str:
        return f"{self.domain}.{self.capability}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd aios && .venv/bin/pytest tests/test_autonomy.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add aios/src/aios/autonomy.py aios/tests/test_autonomy.py
git commit -m "feat(aios): autonomy levels and action types"
```

---

### Task 3: Audit log (append-only)

**Files:**
- Create: `aios/src/aios/audit.py`
- Test: `aios/tests/test_audit.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aios && .venv/bin/pytest tests/test_audit.py -q`
Expected: FAIL with "No module named 'aios.audit'".

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AuditRecord:
    seq: int
    action_key: str
    event: str
    actor: str
    detail: dict[str, Any]


class AuditLog:
    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def append(self, *, action_key: str, event: str, actor: str,
               detail: dict[str, Any]) -> AuditRecord:
        rec = AuditRecord(seq=len(self._records) + 1, action_key=action_key,
                          event=event, actor=actor, detail=dict(detail))
        self._records.append(rec)
        return rec

    def records(self) -> list[AuditRecord]:
        return list(self._records)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd aios && .venv/bin/pytest tests/test_audit.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add aios/src/aios/audit.py aios/tests/test_audit.py
git commit -m "feat(aios): append-only audit log"
```

---

### Task 4: Kill-switch

**Files:**
- Create: `aios/src/aios/killswitch.py`
- Test: `aios/tests/test_killswitch.py`

- [ ] **Step 1: Write the failing test**

```python
from aios.killswitch import KillSwitch


def test_starts_disengaged():
    ks = KillSwitch()
    assert ks.engaged is False


def test_engage_and_release():
    ks = KillSwitch()
    ks.engage(reason="manual stop")
    assert ks.engaged is True
    assert ks.reason == "manual stop"
    ks.release()
    assert ks.engaged is False
    assert ks.reason is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aios && .venv/bin/pytest tests/test_killswitch.py -q`
Expected: FAIL with "No module named 'aios.killswitch'".

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations


class KillSwitch:
    def __init__(self) -> None:
        self._engaged = False
        self._reason: str | None = None

    @property
    def engaged(self) -> bool:
        return self._engaged

    @property
    def reason(self) -> str | None:
        return self._reason

    def engage(self, *, reason: str) -> None:
        self._engaged = True
        self._reason = reason

    def release(self) -> None:
        self._engaged = False
        self._reason = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd aios && .venv/bin/pytest tests/test_killswitch.py -q`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add aios/src/aios/killswitch.py aios/tests/test_killswitch.py
git commit -m "feat(aios): global kill-switch"
```

---

### Task 5: Policy engine — level lookup and decision

**Files:**
- Create: `aios/src/aios/policy.py`
- Test: `aios/tests/test_policy.py`

- [ ] **Step 1: Write the failing test**

```python
from aios.autonomy import ActionType, AutonomyLevel
from aios.policy import PolicyEngine, Decision

AT = ActionType("marketing", "social.publish_post")


def test_unknown_action_defaults_to_l0():
    pe = PolicyEngine()
    assert pe.level_for(AT) == AutonomyLevel.L0_OBSERVE


def test_decision_l0_is_deny():
    pe = PolicyEngine()
    assert pe.decide(AT) == Decision.DENY


def test_decision_l1_is_propose():
    pe = PolicyEngine()
    pe.set_level(AT, AutonomyLevel.L1_PROPOSE)
    assert pe.decide(AT) == Decision.PROPOSE


def test_decision_l2_and_l3_are_execute():
    pe = PolicyEngine()
    pe.set_level(AT, AutonomyLevel.L2_ROUTINE)
    assert pe.decide(AT) == Decision.EXECUTE
    pe.set_level(AT, AutonomyLevel.L3_AUTO)
    assert pe.decide(AT) == Decision.EXECUTE
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aios && .venv/bin/pytest tests/test_policy.py -q`
Expected: FAIL with "No module named 'aios.policy'".

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from aios.autonomy import ActionType, AutonomyLevel, DEFAULT_PROMOTION_THRESHOLD


class Decision(Enum):
    DENY = auto()
    PROPOSE = auto()
    EXECUTE = auto()


@dataclass
class PolicyState:
    level: AutonomyLevel = AutonomyLevel.L0_OBSERVE
    streak: int = 0
    capped_at: AutonomyLevel = AutonomyLevel.L3_AUTO


class PolicyEngine:
    def __init__(self, *, promotion_threshold: int = DEFAULT_PROMOTION_THRESHOLD) -> None:
        self._states: dict[str, PolicyState] = {}
        self._threshold = promotion_threshold

    def _state(self, action: ActionType) -> PolicyState:
        return self._states.setdefault(action.key, PolicyState())

    def level_for(self, action: ActionType) -> AutonomyLevel:
        return self._state(action).level

    def set_level(self, action: ActionType, level: AutonomyLevel) -> None:
        self._state(action).level = level

    def decide(self, action: ActionType) -> Decision:
        level = self.level_for(action)
        if level == AutonomyLevel.L0_OBSERVE:
            return Decision.DENY
        if level == AutonomyLevel.L1_PROPOSE:
            return Decision.PROPOSE
        return Decision.EXECUTE
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd aios && .venv/bin/pytest tests/test_policy.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add aios/src/aios/policy.py aios/tests/test_policy.py
git commit -m "feat(aios): policy engine level lookup and decision"
```

---

### Task 6: Policy engine — outcomes, promotion, caps

**Files:**
- Modify: `aios/src/aios/policy.py`
- Test: `aios/tests/test_policy.py` (add tests)

- [ ] **Step 1: Write the failing tests (append to `tests/test_policy.py`)**

```python
def test_clean_approvals_promote_l1_to_l2():
    pe = PolicyEngine(promotion_threshold=3)
    pe.set_level(AT, AutonomyLevel.L1_PROPOSE)
    for _ in range(3):
        pe.record_outcome(AT, clean=True)
    assert pe.level_for(AT) == AutonomyLevel.L2_ROUTINE


def test_correction_resets_streak():
    pe = PolicyEngine(promotion_threshold=3)
    pe.set_level(AT, AutonomyLevel.L1_PROPOSE)
    pe.record_outcome(AT, clean=True)
    pe.record_outcome(AT, clean=False)
    pe.record_outcome(AT, clean=True)
    assert pe.level_for(AT) == AutonomyLevel.L1_PROPOSE


def test_cap_blocks_auto_promotion():
    pe = PolicyEngine(promotion_threshold=2)
    pe.set_level(AT, AutonomyLevel.L1_PROPOSE)
    pe.set_cap(AT, AutonomyLevel.L1_PROPOSE)  # money/contracts style cap
    for _ in range(5):
        pe.record_outcome(AT, clean=True)
    assert pe.level_for(AT) == AutonomyLevel.L1_PROPOSE


def test_no_auto_promotion_beyond_l2():
    pe = PolicyEngine(promotion_threshold=2)
    pe.set_level(AT, AutonomyLevel.L2_ROUTINE)
    for _ in range(10):
        pe.record_outcome(AT, clean=True)
    assert pe.level_for(AT) == AutonomyLevel.L2_ROUTINE  # L2->L3 is manual only
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd aios && .venv/bin/pytest tests/test_policy.py -q`
Expected: FAIL with "PolicyEngine has no attribute 'record_outcome'".

- [ ] **Step 3: Add implementation to `policy.py`**

Add `set_cap` and `record_outcome` methods to `PolicyEngine`:

```python
    def set_cap(self, action: ActionType, cap: AutonomyLevel) -> None:
        self._state(action).capped_at = cap

    def record_outcome(self, action: ActionType, *, clean: bool) -> None:
        state = self._state(action)
        if not clean:
            state.streak = 0
            return
        state.streak += 1
        # auto-promotion only L1 -> L2, never beyond, never past the cap
        if (state.level == AutonomyLevel.L1_PROPOSE
                and state.capped_at >= AutonomyLevel.L2_ROUTINE
                and state.streak >= self._threshold):
            state.level = AutonomyLevel.L2_ROUTINE
            state.streak = 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd aios && .venv/bin/pytest tests/test_policy.py -q`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add aios/src/aios/policy.py aios/tests/test_policy.py
git commit -m "feat(aios): autonomy promotion, streaks, and caps"
```

---

### Task 7: Approval queue

**Files:**
- Create: `aios/src/aios/approvals.py`
- Test: `aios/tests/test_approvals.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aios && .venv/bin/pytest tests/test_approvals.py -q`
Expected: FAIL with "No module named 'aios.approvals'".

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class ApprovalStatus(Enum):
    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()


@dataclass
class Approval:
    id: int
    action_key: str
    actor: str
    payload: dict[str, Any]
    status: ApprovalStatus = ApprovalStatus.PENDING
    clean: bool = False
    reason: str | None = None


class ApprovalQueue:
    def __init__(self) -> None:
        self._items: dict[int, Approval] = {}
        self._next_id = 1

    def enqueue(self, *, action_key: str, actor: str,
                payload: dict[str, Any]) -> Approval:
        appr = Approval(id=self._next_id, action_key=action_key,
                        actor=actor, payload=dict(payload))
        self._items[appr.id] = appr
        self._next_id += 1
        return appr

    def pending(self) -> list[Approval]:
        return [a for a in self._items.values()
                if a.status == ApprovalStatus.PENDING]

    def approve(self, approval_id: int,
                edited_payload: dict[str, Any] | None = None) -> Approval:
        appr = self._items[approval_id]
        appr.status = ApprovalStatus.APPROVED
        if edited_payload is not None:
            appr.payload = dict(edited_payload)
            appr.clean = False
        else:
            appr.clean = True
        return appr

    def reject(self, approval_id: int, *, reason: str) -> Approval:
        appr = self._items[approval_id]
        appr.status = ApprovalStatus.REJECTED
        appr.clean = False
        appr.reason = reason
        return appr
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd aios && .venv/bin/pytest tests/test_approvals.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add aios/src/aios/approvals.py aios/tests/test_approvals.py
git commit -m "feat(aios): approval queue with approve/edit/reject"
```

---

### Task 8: Tool registry

**Files:**
- Create: `aios/src/aios/tools.py`
- Test: `aios/tests/test_tools.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest

from aios.autonomy import ActionType
from aios.tools import Tool, ToolRegistry


def test_register_and_get():
    reg = ToolRegistry()
    tool = Tool(name="publish_post",
                action_type=ActionType("marketing", "social.publish_post"),
                run=lambda **kw: {"published": True})
    reg.register(tool)
    assert reg.get("publish_post") is tool


def test_readonly_tool_has_no_action_type():
    reg = ToolRegistry()
    tool = Tool(name="read_insights", action_type=None, readonly=True,
                run=lambda **kw: {"reach": 1000})
    reg.register(tool)
    assert reg.get("read_insights").readonly is True


def test_duplicate_name_raises():
    reg = ToolRegistry()
    tool = Tool(name="dup", action_type=None, readonly=True, run=lambda **kw: None)
    reg.register(tool)
    with pytest.raises(ValueError):
        reg.register(tool)


def test_unknown_tool_raises():
    reg = ToolRegistry()
    with pytest.raises(KeyError):
        reg.get("missing")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aios && .venv/bin/pytest tests/test_tools.py -q`
Expected: FAIL with "No module named 'aios.tools'".

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from aios.autonomy import ActionType


@dataclass
class Tool:
    name: str
    action_type: ActionType | None
    run: Callable[..., Any]
    readonly: bool = False


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(name)
        return self._tools[name]

    def names(self) -> list[str]:
        return list(self._tools)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd aios && .venv/bin/pytest tests/test_tools.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add aios/src/aios/tools.py aios/tests/test_tools.py
git commit -m "feat(aios): tool registry"
```

---

### Task 9: Kernel facade

**Files:**
- Create: `aios/src/aios/kernel.py`
- Modify: `aios/src/aios/__init__.py` (export public API)
- Test: `aios/tests/test_kernel.py`

- [ ] **Step 1: Write the failing test**

```python
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
    # clean approval advances the reliability streak
    assert k.policy._state(PUBLISH).streak == 1


def test_rejecting_approval_does_not_run_and_resets_streak():
    k, calls = _kernel_with_publish()
    k.policy.set_level(PUBLISH, AutonomyLevel.L1_PROPOSE)
    res = k.execute("publish_post", actor="marketing_agent", args={"caption": "ciao"})
    run_res = k.resolve_approval(res.approval_id, approve=False, reason="off-brand")
    assert run_res.outcome == ExecOutcome.DENIED
    assert calls == []
    assert k.policy._state(PUBLISH).streak == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd aios && .venv/bin/pytest tests/test_kernel.py -q`
Expected: FAIL with "No module named 'aios.kernel'".

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from aios.approvals import ApprovalQueue
from aios.audit import AuditLog
from aios.autonomy import ActionType
from aios.killswitch import KillSwitch
from aios.policy import Decision, PolicyEngine
from aios.tools import Tool, ToolRegistry


class ExecOutcome(Enum):
    EXECUTED = auto()
    QUEUED = auto()
    DENIED = auto()


@dataclass
class ExecResult:
    outcome: ExecOutcome
    result: Any = None
    approval_id: int | None = None


class Kernel:
    def __init__(self, *, promotion_threshold: int = 10) -> None:
        self.tools = ToolRegistry()
        self.policy = PolicyEngine(promotion_threshold=promotion_threshold)
        self.audit = AuditLog()
        self.killswitch = KillSwitch()
        self.approvals = ApprovalQueue()

    def register_tool(self, tool: Tool) -> None:
        self.tools.register(tool)

    def _run(self, tool: Tool, actor: str, args: dict[str, Any],
             action_key: str) -> ExecResult:
        result = tool.run(**args)
        self.audit.append(action_key=action_key, event="executed",
                          actor=actor, detail={"args": args})
        return ExecResult(outcome=ExecOutcome.EXECUTED, result=result)

    def execute(self, name: str, *, actor: str, args: dict[str, Any]) -> ExecResult:
        tool = self.tools.get(name)
        action_key = tool.action_type.key if tool.action_type else f"readonly.{tool.name}"

        if tool.readonly or tool.action_type is None:
            result = tool.run(**args)
            self.audit.append(action_key=action_key, event="read",
                              actor=actor, detail={"args": args})
            return ExecResult(outcome=ExecOutcome.EXECUTED, result=result)

        if self.killswitch.engaged:
            self.audit.append(action_key=action_key, event="blocked_killswitch",
                              actor=actor, detail={"reason": self.killswitch.reason})
            return ExecResult(outcome=ExecOutcome.DENIED)

        decision = self.policy.decide(tool.action_type)
        if decision == Decision.DENY:
            self.audit.append(action_key=action_key, event="denied",
                              actor=actor, detail={"args": args})
            return ExecResult(outcome=ExecOutcome.DENIED)

        if decision == Decision.PROPOSE:
            appr = self.approvals.enqueue(action_key=action_key, actor=actor, payload=args)
            self.audit.append(action_key=action_key, event="proposed",
                              actor=actor, detail={"approval_id": appr.id, "args": args})
            return ExecResult(outcome=ExecOutcome.QUEUED, approval_id=appr.id)

        return self._run(tool, actor, args, action_key)

    def resolve_approval(self, approval_id: int, *, approve: bool,
                         edited_payload: dict[str, Any] | None = None,
                         reason: str | None = None) -> ExecResult:
        pending = {a.id: a for a in self.approvals.pending()}
        appr = pending[approval_id]
        action = ActionType(*appr.action_key.split(".", 1))

        if not approve:
            self.approvals.reject(approval_id, reason=reason or "rejected")
            self.policy.record_outcome(action, clean=False)
            self.audit.append(action_key=appr.action_key, event="rejected",
                              actor=appr.actor, detail={"reason": reason})
            return ExecResult(outcome=ExecOutcome.DENIED)

        resolved = self.approvals.approve(approval_id, edited_payload=edited_payload)
        self.policy.record_outcome(action, clean=resolved.clean)
        tool_name = self._tool_for_action(appr.action_key)
        tool = self.tools.get(tool_name)
        return self._run(tool, appr.actor, resolved.payload, appr.action_key)

    def _tool_for_action(self, action_key: str) -> str:
        for name in self.tools.names():
            tool = self.tools.get(name)
            if tool.action_type and tool.action_type.key == action_key:
                return name
        raise KeyError(action_key)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd aios && .venv/bin/pytest tests/test_kernel.py -q`
Expected: 7 passed.

- [ ] **Step 5: Update `src/aios/__init__.py` public exports**

```python
__version__ = "0.0.1"

from aios.autonomy import ActionType, AutonomyLevel
from aios.kernel import Kernel, ExecOutcome, ExecResult
from aios.tools import Tool

__all__ = [
    "__version__",
    "ActionType",
    "AutonomyLevel",
    "Kernel",
    "ExecOutcome",
    "ExecResult",
    "Tool",
]
```

- [ ] **Step 6: Run full suite**

Run: `cd aios && .venv/bin/pytest -q`
Expected: all tests pass (smoke + autonomy + audit + killswitch + policy + approvals + tools + kernel).

- [ ] **Step 7: Commit**

```bash
git add aios/src/aios/kernel.py aios/src/aios/__init__.py aios/tests/test_kernel.py
git commit -m "feat(aios): kernel facade wiring policy, audit, killswitch, approvals"
```

---

## Self-Review

**Spec coverage (Fase 0 scope — §6 "Fase 0" + §4 autonomy ladder + §2 modules ⑤⑥):**
- Module ⑤ Tool Mgr → Task 8 ✅
- Module ⑥ Access/Policy + autonomy ladder L0–L3 → Tasks 5, 6 ✅
- Kill-switch (§4) → Task 4 ✅
- Audit log (§2, §4 "ogni azione → audit log") → Task 3 ✅
- Approval queue / Human Approval Queue (§4 L1, §9 cockpit) → Task 7 ✅
- Promotion by clean-streak, caps for money/contracts (§4) → Task 6 ✅
- Kernel facade tying it together (§2) → Task 9 ✅
- **Deferred to later plans (correctly out of Fase 0 scope):** Context Mgr ②, Memory Mgr ③, Storage Mgr ④ Postgres persistence, Scheduler ①, Founder Model ⑦, Next.js cockpit (§9), Telegram, Marketing agents (§5). These are noted in the spec as Fase 1.

**Placeholder scan:** no TBD/TODO; every code step shows full code; every command has expected output.

**Type consistency:** `ActionType.key` (Task 2) parsed back via `ActionType(*key.split(".", 1))` in Task 9 — consistent with `domain.capability` form. `Approval.clean` (Task 7) consumed by `record_outcome(clean=...)` (Task 6) in Task 9. `Decision` enum (Task 5) consumed in Task 9. `ExecOutcome`/`ExecResult` defined and used in Task 9 only. Consistent.

**Note on `ActionType` round-trip:** capability may itself contain dots (`social.publish_post`), so Task 9 uses `split(".", 1)` to split only on the first dot (domain vs capability). Verified against `key` definition in Task 2.
