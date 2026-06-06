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

    @app.middleware("http")
    async def _security_headers(request: Request, call_next):
        resp = await call_next(request)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers.setdefault("Cache-Control", "no-store")
        return resp

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
    def insights(_=Depends(_require_auth)) -> dict[str, Any]:
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
            "iscritti": ("leggi_iscritti", {}),
            "newsletter": ("leggi_newsletter", {}),
            "analytics": ("leggi_analytics", {}),
        }
        for key, (tool, args) in wanted.items():
            if tool not in names:
                continue
            try:
                out[key] = kernel.execute(tool, actor="cockpit", args=args).result
            except Exception as exc:  # sensor offline / rate-limited — surface, don't crash
                out[key] = {"error": str(exc)}
        return out

    @app.get("/api/activity")
    def activity(_=Depends(_require_auth)) -> list[dict[str, Any]]:
        recs = kernel.audit.records()
        out = [{"seq": r.seq, "action_key": r.action_key, "event": r.event,
                "actor": r.actor, "detail": r.detail} for r in recs]
        out.sort(key=lambda x: x["seq"], reverse=True)
        return out[:20]

    @app.get("/api/approvals")
    def approvals(_=Depends(_require_auth)) -> list[dict[str, Any]]:
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

    @app.get("/api/domain/{domain}")
    def domain_view(domain: str, _=Depends(_require_auth)) -> dict[str, Any]:
        """Vista per-dominio: dati reali letti dai sensori dell'agente +
        proposte (coda L1) + deliverable, tutti filtrati per dominio."""
        if platform is None:
            return {"error": "no platform"}
        agent = platform.agents.get(domain)
        if agent is None:
            return {"error": "dominio non valido"}
        names = set(kernel.tools.names())
        data: dict[str, Any] = {}
        cfg = getattr(agent, "cfg", None)
        if cfg is not None:
            for tool, args in cfg.sensors:
                if tool not in names:
                    continue
                try:
                    data[tool] = kernel.execute(tool, actor="cockpit", args=args).result
                except Exception as exc:
                    data[tool] = {"error": str(exc)}
        proposals = [{"id": a.id, "action_key": a.action_key, "payload": a.payload}
                     for a in kernel.approvals.pending()
                     if a.action_key.split(".", 1)[0] == domain]
        try:
            deliv = [d for d in platform.deliverables() if d.get("dominio") == domain]
        except Exception:
            deliv = []
        skills = list(getattr(cfg, "skill_focus", []) or []) if cfg else []
        return {"domain": domain, "data": data, "proposals": proposals,
                "deliverables": deliv, "skills": skills}

    @app.post("/api/agents/{domain}/run")
    def run_agent(domain: str, _=Depends(_require_auth)):
        if platform is None:
            return {"error": "no platform"}
        try:
            return platform.run(domain)
        except KeyError:
            return {"error": "dominio non valido"}

    @app.get("/api/integrations")
    def integrations(_=Depends(_require_auth)) -> list[dict[str, Any]]:
        """Stato integrazioni: quali credenziali sono presenti (connesso) o mancanti.
        Mostra che 'l'unica cosa mancante sono le credenziali'."""
        from aios.sources.connectors import CONNECTOR_ENV
        core = {
            "Supabase": ["AIOS_SUPABASE_URL", "AIOS_SUPABASE_SERVICE_KEY"],
            "Anthropic (LLM)": ["ANTHROPIC_API_KEY"],
            "Instagram": ["AIOS_IG_TOKEN"],
            "Telegram": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"],
            "API auth": ["AIOS_API_TOKEN"],
        }
        label = {
            "leggi_stripe_ricavi": "Stripe (ricavi)", "leggi_stripe_saldo": "Stripe (saldo)",
            "leggi_email_events": "Resend (email)", "leggi_ranking_seo": "Google Search Console",
            "leggi_funnel_web": "PostHog", "leggi_ads_meta": "Meta Ads",
            "leggi_ads_google": "Google Ads", "leggi_inbox": "Email inbox (IMAP)",
            "leggi_calendario_google": "Google Calendar", "leggi_competitor_web": "Competitor web",
        }
        out = []
        for name, envs in core.items():
            out.append({"nome": name, "tipo": "core",
                        "connesso": all(os.environ.get(e) for e in envs), "env": envs})
        for tool, envs in CONNECTOR_ENV.items():
            out.append({"nome": label.get(tool, tool), "tipo": "connettore",
                        "connesso": all(os.environ.get(e) for e in envs), "env": envs})
        return out

    @app.get("/api/deliverables")
    def deliverables(_=Depends(_require_auth)):
        if platform is None:
            return []
        return platform.deliverables()

    return app
