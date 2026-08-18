from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

import psycopg

from aios.approvals import ApprovalQueue, ApprovalStatus
from aios.audit import AuditLog
from aios.autonomy import ActionType
from aios.killswitch import KillSwitch
from aios.policy import Decision, PolicyEngine
from aios.tools import Tool, ToolRegistry


class ExecOutcome(Enum):
    EXECUTED = auto()
    QUEUED = auto()
    DENIED = auto()


def esito_effettivo(result: Any) -> dict[str, Any] | None:
    """Estrae l'esito REALE di una run dal valore di ritorno del tool.

    L'attuatore non solleva: incapsula i fallimenti in result['attuatore'] (vedi
    agents/domain.py). Senza questa estrazione un'azione fallita risulterebbe
    'executed' identica a una riuscita — ed è così che Telegram, il cockpit e
    l'audit finivano per dichiarare successi mai avvenuti. Ritorna None se il
    tool non riporta un esito strutturato (nulla da dire).
    """
    if not isinstance(result, dict):
        return None
    att = result.get("attuatore")
    if not isinstance(att, dict):
        return None
    out: dict[str, Any] = {"ok": bool(att.get("ok"))}
    for campo in ("errore", "tabella", "op", "canale", "workflow"):
        if att.get(campo):
            out[campo] = str(att[campo])[:200]
    if att.get("righe") is not None:
        righe = att["righe"]
        out["righe"] = len(righe) if isinstance(righe, list) else righe
    return out


@dataclass
class ExecResult:
    outcome: ExecOutcome
    result: Any = None
    approval_id: int | None = None

    @property
    def esito(self) -> dict[str, Any] | None:
        """Esito reale dell'attuatore, se il tool ne ha riportato uno."""
        return esito_effettivo(self.result)

    @property
    def eseguita_davvero(self) -> bool:
        """True solo se l'azione è arrivata a destinazione. Un'azione che l'attuatore
        ha rifiutato o non è riuscita a compiere è EXECUTED per il kernel ma NON
        eseguita davvero: chi riporta all'umano deve distinguere i due casi."""
        if self.outcome != ExecOutcome.EXECUTED:
            return False
        es = self.esito
        return True if es is None else bool(es.get("ok"))


class Kernel:
    def __init__(self, *, promotion_threshold: int = 10) -> None:
        self.tools = ToolRegistry()
        self.policy = PolicyEngine(promotion_threshold=promotion_threshold)
        self.audit = AuditLog()
        self.killswitch = KillSwitch()
        self.approvals = ApprovalQueue()

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

    def register_tool(self, tool: Tool) -> None:
        self.tools.register(tool)

    def _run(self, tool: Tool, actor: str, args: dict[str, Any],
             action_key: str) -> ExecResult:
        try:
            result = tool.run(**args)
        except Exception as exc:
            self.audit.append(action_key=action_key, event="error",
                              actor=actor, detail={"error": str(exc)})
            raise
        # L'esito dell'attuatore va in audit: senza, un'azione fallita lascia la
        # stessa traccia di una riuscita e il fallimento diventa invisibile.
        detail: dict[str, Any] = {"args": args}
        esito = esito_effettivo(result)
        if esito is not None:
            detail["esito"] = esito
        self.audit.append(action_key=action_key,
                          event="executed" if (esito is None or esito.get("ok")) else "failed",
                          actor=actor, detail=detail)
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
        appr = self.approvals.get(approval_id)  # raises KeyError if id never existed
        if appr.status != ApprovalStatus.PENDING:
            raise ValueError(
                f"approval {approval_id} is already {appr.status.name}")

        if self.killswitch.engaged:
            self.audit.append(action_key=appr.action_key, event="blocked_killswitch",
                              actor=appr.actor, detail={"reason": self.killswitch.reason})
            return ExecResult(outcome=ExecOutcome.DENIED)

        if not re.match(r"^[a-z_]+\.[a-z_.]+$", appr.action_key):
            raise ValueError(f"action_key non valido: {appr.action_key!r}")
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
