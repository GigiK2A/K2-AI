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
