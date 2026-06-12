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
