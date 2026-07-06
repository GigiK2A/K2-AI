from __future__ import annotations

import os
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated, Any

import json
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Path as FPath, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from aios.kernel import Kernel

_STATIC = Path(__file__).parent / "static"

# --- Performance: cache TTL + letture sensori in parallelo --------------------
# Le viste del cockpit leggono molti sensori (ognuno = un giro su Supabase/IG/PostHog).
# In serie facevano ~6s. Qui: cache breve per navigazione istantanea + fan-out in
# thread per la prima lettura. Dati "vivi" entro pochi secondi (TTL corto).
_CACHE: dict[str, tuple[float, Any]] = {}


def _cached(key: str, ttl: float, producer):
    now = time.time()
    hit = _CACHE.get(key)
    if hit and (now - hit[0]) < ttl:
        return hit[1]
    val = producer()
    _CACHE[key] = (now, val)
    return val


def _invalidate_cache() -> None:
    _CACHE.clear()


def _parallel(funcs: dict):
    """funcs: {chiave: callable senza argomenti}. Esegue in parallelo (max 8),
    ritorna {chiave: risultato}; un errore diventa {'error': ...} per quella chiave."""
    if not funcs:
        return {}
    out: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=min(8, len(funcs))) as ex:
        futs = {k: ex.submit(fn) for k, fn in funcs.items()}
        for k, f in futs.items():
            try:
                out[k] = f.result()
            except Exception as exc:
                out[k] = {"error": str(exc)}
    return out


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


class CommandBody(BaseModel):
    text: str


class ChatStreamBody(BaseModel):
    text: str
    # "auto" (o assente) = il router sceglie un agente; lista di domini = quegli agenti
    # in parallelo (marketing, vendite, finance, operations, legal, hr).
    agents: list[str] | str | None = None
    # se presente, la conversazione è PERSISTENTE: carica lo storico e salva i turni.
    session_id: str | None = None


class ChatSessionBody(BaseModel):
    title: str | None = None
    agents: list[str] | str | None = None


class ConfirmBody(BaseModel):
    id: int


class ProspectBody(BaseModel):
    n: int = 5


class SendDraftBody(BaseModel):
    subject: str | None = None
    body: str | None = None


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

    @app.get("/health")
    def health() -> dict[str, str]:
        """Healthcheck pubblico (no auth) per Railway/Docker."""
        return {"status": "ok"}

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
        def _build() -> dict[str, Any]:
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
        return _cached("overview", 10, _build)

    @app.get("/api/insights")
    def insights(_=Depends(_require_auth)) -> dict[str, Any]:
        # Everything here is read THROUGH the agent's own sensor tools (kernel),
        # never hardcoded. Each tool is L0 read-only; missing/erroring tools are skipped.
        wanted = {
            "profilo": ("leggi_profilo_ig", {}),
            "insight": ("leggi_insight_ig", {}),
            "post": ("leggi_post_ig", {"limit": 6}),
            "servizi": ("leggi_servizi", {}),
            "topics": ("leggi_topics", {}),
            "iscritti": ("leggi_iscritti", {}),
            "newsletter": ("leggi_newsletter", {}),
            "analytics": ("leggi_analytics", {}),
            "prospects": ("leggi_prospects", {}),
            "competitor_trovati": ("leggi_competitor_trovati", {}),
            "ranking_seo": ("leggi_ranking_seo", {}),
            "funnel_web": ("leggi_funnel_web", {}),
        }

        def _build() -> dict[str, Any]:
            names = set(kernel.tools.names())
            funcs = {key: (lambda t=tool, a=args: kernel.execute(t, actor="cockpit", args=a).result)
                     for key, (tool, args) in wanted.items() if tool in names}
            return _parallel(funcs)  # sensori in parallelo invece che in serie

        return _cached("insights", 25, _build)

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
        _invalidate_cache()   # dato cambiato → cockpit lo vede subito
        out = {"outcome": res.outcome.name}
        if isinstance(res.result, dict) and "attuatore" in res.result:
            out["attuatore"] = res.result["attuatore"]   # esito scrittura reale
        return out

    @app.post("/api/approvals/{approval_id}/reject")
    def reject(
        approval_id: Annotated[int, FPath(gt=0)],
        body: ResolveBody,
        _=Depends(_require_auth),
    ) -> dict[str, Any]:
        res = kernel.resolve_approval(approval_id, approve=False,
                                      reason=body.reason or "rejected")
        _invalidate_cache()
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

        def _build() -> dict[str, Any]:
            names = set(kernel.tools.names())
            cfg = getattr(agent, "cfg", None)
            funcs = {}
            if cfg is not None:
                for tool, args in cfg.sensors:
                    if tool in names:
                        funcs[tool] = (lambda t=tool, a=args:
                                       kernel.execute(t, actor="cockpit", args=a).result)
            data = _parallel(funcs)  # sensori del dominio in parallelo
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

        return _cached(f"domain:{domain}", 25, _build)

    @app.post("/api/agents/{domain}/run")
    def run_agent(domain: str, _=Depends(_require_auth)):
        if platform is None:
            return {"error": "no platform"}
        try:
            res = platform.run(domain)
            _invalidate_cache()   # nuove proposte → visibili subito
            return res
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
            "n8n (esecutore esterno)": ["N8N_WEBHOOK_URL"],
            "n8n API (gestione workflow)": ["N8N_API_URL", "N8N_API_KEY"],
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

    @app.get("/api/company")
    def company(_=Depends(_require_auth)) -> dict[str, Any]:
        """Aggregati REALI per Overview/Agenti: coda decisioni, audit, deliverable,
        per-dominio + alcuni segnali letti dai sensori. Nessun dato inventato."""
        def _build() -> dict[str, Any]:
            pending = kernel.approvals.pending()
            records = kernel.audit.records()
            executed = sum(1 for r in records if r.event == "executed")
            domains = platform.domains() if platform else []
            per = {d: {"pending": 0, "deliverables": 0} for d in domains}
            for a in pending:
                d = a.action_key.split(".", 1)[0]
                if d in per:
                    per[d]["pending"] += 1
            try:
                deliv = platform.deliverables() if platform else []
            except Exception:
                deliv = []
            for x in deliv:
                d = x.get("dominio")
                if d in per:
                    per[d]["deliverables"] += 1
            names = set(kernel.tools.names())

            def _count_fn(tool: str):
                def _run():
                    if tool not in names:
                        return None
                    try:
                        r = kernel.execute(tool, actor="cockpit", args={}).result
                        return len(r) if isinstance(r, list) else None
                    except Exception:
                        return None
                return _run

            sig_tools = {"leads": "leggi_lead", "conversioni": "leggi_conversioni",
                         "iscritti": "leggi_iscritti_newsletter", "commesse": "leggi_commesse",
                         "task_operativi": "leggi_task_operativi", "clienti": "leggi_clienti"}
            signals = _parallel({k: _count_fn(t) for k, t in sig_tools.items()})  # in parallelo
            return {
                "pending_total": len(pending),
                "audit_total": len(records),
                "executed_total": executed,
                "deliverables_total": len(deliv),
                "domains": domains,
                "per_domain": per,
                "signals": signals,
            }

        return _cached("company", 25, _build)

    @app.post("/api/command")
    def command(body: CommandBody, _=Depends(_require_auth)) -> dict[str, Any]:
        """Chat a istruzioni: valuta e — interne subito, esterne/sensibili in conferma — esegue."""
        if platform is None or getattr(platform, "commands", None) is None:
            return {"fattibile": False, "risposta": "Comandi non disponibili.",
                    "valutazione": "", "eseguite": [], "da_confermare": [], "rifiutate": []}
        return platform.commands.handle(body.text, actor="cockpit").to_dict()

    def _chat_client():
        return getattr(kernel, "_supabase", None)

    @app.get("/api/chat/sessions")
    def chat_sessions(_=Depends(_require_auth)) -> list[dict[str, Any]]:
        """Elenco delle conversazioni salvate (più recenti prima)."""
        client = _chat_client()
        if client is None:
            return []
        try:
            return client.select("aios_chat_sessions",
                                  {"select": "id,title,agents,updated_at,created_at",
                                   "order": "updated_at.desc", "limit": "100"})
        except Exception:
            return []

    @app.post("/api/chat/sessions")
    def chat_session_create(body: ChatSessionBody,
                            _=Depends(_require_auth)) -> dict[str, Any]:
        """Crea una nuova conversazione vuota, ritorna il suo id."""
        client = _chat_client()
        if client is None:
            return {"error": "storage non disponibile"}
        row = {"title": (body.title or "Nuova chat")[:120],
               "agents": body.agents if body.agents is not None else "auto"}
        try:
            out = client.insert("aios_chat_sessions", row)
            return out[0] if out else {"error": "insert fallita"}
        except Exception as exc:
            return {"error": str(exc)[:160]}

    @app.get("/api/chat/sessions/{sid}")
    def chat_session_get(sid: str, _=Depends(_require_auth)) -> dict[str, Any]:
        """Una conversazione con tutti i suoi messaggi (in ordine)."""
        client = _chat_client()
        if client is None:
            return {"session": None, "messages": []}
        try:
            sess = client.select("aios_chat_sessions",
                                  {"select": "*", "id": f"eq.{sid}"})
            msgs = client.select("aios_chat_messages",
                                 {"select": "role,agent,content,created_at",
                                  "session_id": f"eq.{sid}", "order": "id.asc",
                                  "limit": "500"})
            return {"session": sess[0] if sess else None, "messages": msgs}
        except Exception as exc:
            return {"session": None, "messages": [], "error": str(exc)[:160]}

    @app.delete("/api/chat/sessions/{sid}")
    def chat_session_delete(sid: str, _=Depends(_require_auth)) -> dict[str, Any]:
        client = _chat_client()
        if client is None:
            return {"ok": False}
        try:
            client.delete("aios_chat_sessions", {"id": f"eq.{sid}"})  # cascade sui messaggi
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "errore": str(exc)[:160]}

    @app.post("/api/chat/stream")
    def chat_stream(body: ChatStreamBody, _=Depends(_require_auth)) -> StreamingResponse:
        """Chat multi-agente in streaming (SSE). Ogni evento è una riga `data: {...}`:
        start/thinking/tool/writing/delta/tool_run/done/error/all_done, taggato `agent`.
        Con `session_id` la conversazione è PERSISTENTE: carica lo storico (memoria
        per-agente) e salva il messaggio utente + le risposte di ogni agente.
        Le azioni sensibili finiscono in coda e si confermano via /api/command/confirm."""
        chat = getattr(platform, "chat", None) if platform is not None else None
        client = _chat_client()
        sid = (body.session_id or "").strip() or None

        def _sse(ev: dict) -> str:
            return "data: " + json.dumps(ev, ensure_ascii=False, default=str) + "\n\n"

        # Storico (per la memoria) + salvataggio del turno utente, PRIMA dello streaming.
        history: list[dict] = []
        first_msg = True
        if sid and client is not None:
            try:
                history = client.select("aios_chat_messages",
                                        {"select": "role,agent,content",
                                         "session_id": f"eq.{sid}", "order": "id.asc",
                                         "limit": "200"})
                first_msg = not history
            except Exception:
                history = []
            try:
                client.insert("aios_chat_messages",
                              {"session_id": sid, "role": "user", "content": body.text})
            except Exception:
                pass

        def gen():
            if chat is None:
                yield _sse({"phase": "error", "agent": "",
                            "error": "chat non disponibile"})
                return
            _invalidate_cache()   # eventuali scritture della chat → cockpit le vede dopo
            finals: dict[str, str] = {}
            try:
                for ev in chat.stream(body.text, body.agents, history):
                    if ev.get("phase") == "done" and ev.get("agent"):
                        finals[ev["agent"]] = ev.get("text") or ""
                    yield _sse(ev)
            except Exception as exc:
                yield _sse({"phase": "error", "agent": "", "error": str(exc)[:200]})
            # Persistenza post-streaming: risposte degli agenti + aggiornamento sessione.
            if sid and client is not None:
                for ag, txt in finals.items():
                    try:
                        client.insert("aios_chat_messages",
                                      {"session_id": sid, "role": "assistant",
                                       "agent": ag, "content": txt})
                    except Exception:
                        pass
                patch: dict[str, Any] = {
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "agents": body.agents if body.agents is not None else "auto"}
                if first_msg and body.text.strip():
                    patch["title"] = body.text.strip()[:80]
                try:
                    client.update("aios_chat_sessions", {"id": f"eq.{sid}"}, patch)
                except Exception:
                    pass

        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-store",
                                          "X-Accel-Buffering": "no"})

    @app.post("/api/command/confirm")
    def command_confirm(body: ConfirmBody, _=Depends(_require_auth)) -> dict[str, Any]:
        if platform is None or getattr(platform, "commands", None) is None:
            return {"ok": False, "errore": "non disponibile"}
        return platform.commands.confirm(body.id, actor="cockpit")

    @app.post("/api/marketing/prospect")
    def marketing_prospect(body: ProspectBody, _=Depends(_require_auth)) -> dict[str, Any]:
        """Cerca PMI in target (web), le qualifica, salva i qualificati con BOZZA.
        La bozza NON viene inviata: resta in marketing_prospects da rivedere."""
        if platform is None or getattr(platform, "prospector", None) is None:
            return {"errore": "prospecting non disponibile", "prospects": []}
        n = max(1, min(int(body.n or 5), 10))
        try:
            found = platform.prospector.find(n)
        except Exception as exc:
            return {"errore": str(exc)[:200], "prospects": []}
        from aios.actuator import apply_action
        from aios.prospecting import Prospector
        client = kernel._supabase
        salvati, out = 0, []
        for p in found:
            qualified = bool(p.get("in_target")) and int(p.get("fit_score") or 0) >= 60
            rec = {"company": p.get("company"), "sector": p.get("sector"),
                   "fit_score": p.get("fit_score"), "fit_reason": p.get("fit_reason"),
                   "contact_email": p.get("contact_email"), "in_target": p.get("in_target"),
                   "qualificato": qualified, "draft_subject": p.get("draft_subject"),
                   "draft_body": p.get("draft_body")}
            if qualified:
                try:
                    apply_action(client, {"tabella": "marketing_prospects", "op": "insert",
                                          "dati": Prospector.to_row(p)})
                    salvati += 1
                    rec["salvato"] = True
                    kernel.audit.append(action_key="marketing.prospect", event="executed",
                                        actor="cockpit", detail={"company": p.get("company")})
                except Exception as exc:
                    rec["salvato"] = False
                    rec["errore"] = str(exc)[:120]
            out.append(rec)
        return {"trovati": len(found), "salvati": salvati, "prospects": out}

    @app.post("/api/marketing/competitors")
    def marketing_competitors(body: ProspectBody, _=Depends(_require_auth)) -> dict[str, Any]:
        """L'agente cerca da solo i competitor italiani (web), li profila e li salva.
        Nessun URL fornito dall'umano: li trova l'AI. Dati readonly per il cockpit."""
        if platform is None or getattr(platform, "competitor_scout", None) is None:
            return {"errore": "competitor scout non disponibile", "competitors": []}
        n = max(1, min(int(body.n or 6), 12))
        try:
            found = platform.competitor_scout.find(n)
        except Exception as exc:
            return {"errore": str(exc)[:200], "competitors": []}
        from aios.actuator import apply_action
        from aios.competitor_scout import CompetitorScout
        client = kernel._supabase
        salvati, out = 0, []
        for c in found:
            rec = {"name": c.get("name"), "website": c.get("website"),
                   "offering": c.get("offering"), "positioning": c.get("positioning"),
                   "threat": c.get("threat"), "differentiation": c.get("differentiation")}
            try:
                apply_action(client, {"tabella": "marketing_competitors", "op": "insert",
                                      "dati": CompetitorScout.to_row(c)})
                salvati += 1
                rec["salvato"] = True
                kernel.audit.append(action_key="marketing.competitor", event="executed",
                                    actor="cockpit", detail={"name": c.get("name")})
            except Exception as exc:
                rec["salvato"] = False
                rec["errore"] = str(exc)[:120]
            out.append(rec)
        return {"trovati": len(found), "salvati": salvati, "competitors": out}

    @app.get("/api/conversations")
    def conversations(_=Depends(_require_auth)) -> list[dict[str, Any]]:
        if platform is None or getattr(platform, "conversations", None) is None:
            return []
        try:
            return platform.conversations.threads()
        except Exception:
            return []

    @app.post("/api/conversations/draft")
    def conversations_draft(body: ProspectBody, _=Depends(_require_auth)) -> dict[str, Any]:
        """Genera le BOZZE di risposta per i thread con l'ultima mail del cliente."""
        if platform is None or getattr(platform, "conversations", None) is None:
            return {"errore": "non disponibile"}
        return platform.conversations.draft_replies(limit=max(1, min(int(body.n or 5), 10)))

    @app.post("/api/conversations/followups")
    def conversations_followups(body: ProspectBody, _=Depends(_require_auth)) -> dict[str, Any]:
        """Bozze di follow-up commerciale per i lead del K-BOT (email, non convertiti)."""
        if platform is None or getattr(platform, "conversations", None) is None:
            return {"errore": "non disponibile"}
        return platform.conversations.draft_lead_followups(limit=max(1, min(int(body.n or 5), 10)))

    @app.post("/api/conversations/{draft_id}/send")
    def conversations_send(draft_id: str, body: SendDraftBody | None = None,
                           _=Depends(_require_auth)) -> dict[str, Any]:
        """Invia la bozza approvata (esterno via n8n). Il clic Approva È l'autorizzazione.
        Body opzionale {subject, body} per inviare la versione corretta (Modifica)."""
        if platform is None or getattr(platform, "conversations", None) is None:
            return {"ok": False, "errore": "non disponibile"}
        ov = None
        if body is not None and (body.subject or body.body):
            ov = {"subject": body.subject, "body": body.body}
        return platform.conversations.send(draft_id, actor="cockpit", override=ov)

    @app.post("/api/conversations/{draft_id}/discard")
    def conversations_discard(draft_id: str, _=Depends(_require_auth)) -> dict[str, Any]:
        if platform is None or getattr(platform, "conversations", None) is None:
            return {"ok": False, "errore": "non disponibile"}
        return platform.conversations.discard(draft_id)

    # HTML→PNG per n8n (slide Instagram): /api/screenshot + /shots statico pubblico
    try:
        from aios.api.screenshot import add_screenshot
        add_screenshot(app)
    except Exception:
        pass

    return app
