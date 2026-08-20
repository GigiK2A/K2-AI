from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aios.audit import AuditRecord
from aios.approvals import Approval, ApprovalStatus
from aios.autonomy import AutonomyLevel
from aios.policy import PolicyState


def _adesso() -> str:
    """Istante in ISO 8601 UTC. Il backend Postgres usa now() lato DB; via PostgREST
    il timestamp lo mette il chiamante, altrimenti la colonna resta a NULL."""
    return datetime.now(timezone.utc).isoformat()


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
        # Difesa: clamp level<=capped_at letto da DB (un eventuale tampering della
        # tabella non può alzare l'autonomia oltre il cap configurato).
        level, cap = int(r["level"]), int(r["capped_at"])
        return PolicyState(level=AutonomyLevel(min(level, cap)), streak=r["streak"],
                           capped_at=AutonomyLevel(cap))

    def save(self, action_key: str, state: PolicyState) -> None:
        # `updated_at` va scritto a mano: l'upsert PostgREST non tocca la colonna e
        # il default now() vale solo all'inserimento. In produzione la tabella diceva
        # 13 giugno per ogni azione, mesi dopo l'ultimo cambio di autonomia.
        self._c.upsert("aios_policy_state", {
            "action_key": action_key, "level": int(state.level),
            "streak": state.streak, "capped_at": int(state.capped_at),
            "updated_at": _adesso()},
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
        patch: dict[str, Any] = {
            "payload": approval.payload, "status": approval.status.name,
            "clean": approval.clean, "reason": approval.reason}
        # Come il backend Postgres: appena la decisione esce da PENDING si timbra
        # quando. Via REST non lo faceva nessuno e in produzione tutte le 835 righe
        # avevano resolved_at NULL — impossibile dire da quanto una decisione è ferma.
        if approval.status != ApprovalStatus.PENDING:
            patch["resolved_at"] = _adesso()
        self._c.update("aios_approvals", {"id": f"eq.{approval.id}"}, patch)
