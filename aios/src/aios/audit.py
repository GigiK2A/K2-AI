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
