from __future__ import annotations

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
