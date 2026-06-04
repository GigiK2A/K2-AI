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
