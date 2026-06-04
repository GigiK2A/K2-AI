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

    def get(self, approval_id: int) -> Approval:
        if approval_id not in self._items:
            raise KeyError(f"unknown approval_id: {approval_id}")
        return self._items[approval_id]

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
