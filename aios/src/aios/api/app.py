from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from aios.kernel import Kernel

_STATIC = Path(__file__).parent / "static"


class ResolveBody(BaseModel):
    edited_payload: dict[str, Any] | None = None
    reason: str | None = None


def create_app(kernel: Kernel) -> FastAPI:
    app = FastAPI(title="K2-AI Operating System")

    @app.get("/", response_class=HTMLResponse)
    def root() -> str:
        return (_STATIC / "cockpit.html").read_text(encoding="utf-8")

    @app.get("/api/overview")
    def overview() -> dict[str, Any]:
        pending = kernel.approvals.pending()
        records = kernel.audit.records()
        executed = sum(1 for r in records if r.event == "executed")
        return {
            "pending_count": len(pending),
            "audit_count": len(records),
            "automations_done": executed,
            "agents": [
                {"name": "Marketing Agent", "status": "active", "accuracy": 88},
            ],
        }

    @app.get("/api/approvals")
    def approvals() -> list[dict[str, Any]]:
        return [{"id": a.id, "action_key": a.action_key, "actor": a.actor,
                 "status": a.status.name, "payload": a.payload}
                for a in kernel.approvals.pending()]

    @app.post("/api/approvals/{approval_id}/approve")
    def approve(approval_id: int, body: ResolveBody) -> dict[str, Any]:
        res = kernel.resolve_approval(approval_id, approve=True,
                                      edited_payload=body.edited_payload)
        return {"outcome": res.outcome.name}

    @app.post("/api/approvals/{approval_id}/reject")
    def reject(approval_id: int, body: ResolveBody) -> dict[str, Any]:
        res = kernel.resolve_approval(approval_id, approve=False,
                                      reason=body.reason or "rejected")
        return {"outcome": res.outcome.name}

    return app
