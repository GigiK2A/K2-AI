from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Path as FPath, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from aios.kernel import Kernel

_STATIC = Path(__file__).parent / "static"


def _require_auth(request: Request) -> None:
    token = os.environ.get("AIOS_API_TOKEN", "")
    if not token:
        return  # auth disabled (dev/test); production MUST set AIOS_API_TOKEN
    header = request.headers.get("authorization", "")
    expected = f"Bearer {token}"
    if not (header and secrets.compare_digest(header, expected)):
        raise HTTPException(status_code=401, detail="Unauthorized")


class ResolveBody(BaseModel):
    edited_payload: dict[str, Any] | None = None
    reason: str | None = None


def create_app(kernel: Kernel, platform: Any = None) -> FastAPI:
    app = FastAPI(title="K2-AI Operating System")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.environ.get("AIOS_ALLOWED_ORIGIN", "http://127.0.0.1:8800")],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", response_class=HTMLResponse)
    def root() -> HTMLResponse:
        html = (_STATIC / "cockpit.html").read_text(encoding="utf-8")
        return HTMLResponse(html, headers={
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
        })

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

    @app.get("/api/insights")
    def insights() -> dict[str, Any]:
        # Everything here is read THROUGH the agent's own sensor tools (kernel),
        # never hardcoded. Each tool is L0 read-only; missing/erroring tools are skipped.
        names = set(kernel.tools.names())
        out: dict[str, Any] = {}
        wanted = {
            "profilo": ("leggi_profilo_ig", {}),
            "insight": ("leggi_insight_ig", {}),
            "post": ("leggi_post_ig", {"limit": 6}),
            "servizi": ("leggi_servizi", {}),
            "topics": ("leggi_topics", {}),
        }
        for key, (tool, args) in wanted.items():
            if tool not in names:
                continue
            try:
                out[key] = kernel.execute(tool, actor="cockpit", args=args).result
            except Exception as exc:  # sensor offline / rate-limited — surface, don't crash
                out[key] = {"error": str(exc)}
        return out

    @app.get("/api/approvals")
    def approvals() -> list[dict[str, Any]]:
        return [{"id": a.id, "action_key": a.action_key, "actor": a.actor,
                 "status": a.status.name, "payload": a.payload}
                for a in kernel.approvals.pending()]

    @app.post("/api/approvals/{approval_id}/approve")
    def approve(
        approval_id: Annotated[int, FPath(gt=0)],
        body: ResolveBody,
        _=Depends(_require_auth),
    ) -> dict[str, Any]:
        res = kernel.resolve_approval(approval_id, approve=True,
                                      edited_payload=body.edited_payload)
        return {"outcome": res.outcome.name}

    @app.post("/api/approvals/{approval_id}/reject")
    def reject(
        approval_id: Annotated[int, FPath(gt=0)],
        body: ResolveBody,
        _=Depends(_require_auth),
    ) -> dict[str, Any]:
        res = kernel.resolve_approval(approval_id, approve=False,
                                      reason=body.reason or "rejected")
        return {"outcome": res.outcome.name}

    @app.get("/api/domini")
    def domini():
        return {"domini": platform.domains() if platform else []}

    @app.post("/api/agents/{domain}/run")
    def run_agent(domain: str, _=Depends(_require_auth)):
        if platform is None:
            return {"error": "no platform"}
        try:
            return platform.run(domain)
        except KeyError:
            return {"error": "dominio non valido"}

    @app.get("/api/deliverables")
    def deliverables():
        if platform is None:
            return []
        return platform.deliverables()

    return app
