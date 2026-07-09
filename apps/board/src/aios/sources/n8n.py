"""Connettore n8n: braccio esecutore per le azioni ESTERNE (pubblicare un post,
aggiornare un sistema terzo, ...). L'AIOS propone/valuta; n8n esegue l'effetto reale
con le proprie credenziali. Env-gated: senza N8N_WEBHOOK_URL degrada con un esito
'non configurato' (nessun errore, nessun side-effect).

Sicurezza:
- e' un'azione con action_type -> passa dal perimetro (coda L1 / conferma chat).
- POST solo verso N8N_WEBHOOK_URL (impostato dall'operatore, non da contenuti non fidati);
  schema http/https forzato (anti-SSRF base).
- payload opaco; opzionale header di firma N8N_WEBHOOK_TOKEN.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any
from urllib.parse import urlparse

from aios.autonomy import ActionType
from aios.tools import Tool

N8N_ACTION = ActionType("integrazioni", "n8n.esegui")


def n8n_enabled() -> bool:
    return bool(os.environ.get("N8N_WEBHOOK_URL"))


def trigger_n8n(workflow: str, payload: dict[str, Any] | None = None,
                timeout: int = 20) -> dict[str, Any]:
    url = os.environ.get("N8N_WEBHOOK_URL", "").strip()
    if not url:
        return {"ok": False, "errore": "n8n non configurato (manca N8N_WEBHOOK_URL nel .env)"}
    if urlparse(url).scheme not in ("http", "https"):
        return {"ok": False, "errore": "N8N_WEBHOOK_URL non valido (solo http/https)"}
    body = json.dumps({"workflow": workflow, "payload": payload or {}}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    tok = os.environ.get("N8N_WEBHOOK_TOKEN")
    if tok:
        headers["X-AIOS-Token"] = tok
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
            raw = r.read().decode("utf-8", "replace")
        return {"ok": True, "stato": "inviato a n8n", "workflow": workflow,
                "risposta": raw[:500]}
    except Exception as exc:  # rete/n8n giù: esito tracciato, niente crash
        return {"ok": False, "errore": str(exc)[:200]}


def n8n_tool() -> Tool:
    """Tool azione: esegue un workflow n8n. Registrato sempre (degrada se non configurato)."""
    def _run(workflow: str = "default", payload: dict | None = None, **_) -> dict:
        return trigger_n8n(workflow, payload or {})
    return Tool(name="esegui_n8n", action_type=N8N_ACTION, run=_run)


# ----------------------------------------------------------------------------
# GESTIONE WORKFLOW via n8n Public API (lettura + modifica). Env-gated:
#   N8N_API_URL  es: https://<host>/api/v1
#   N8N_API_KEY  (Settings → n8n API → Create API Key)
# Le SCRITTURE (create/update/activate/deactivate) passano dal perimetro: l'AI
# propone, l'umano conferma. DELETE non e' esposta (mai cancellazione automatica).
# ----------------------------------------------------------------------------
def n8n_api_enabled() -> bool:
    return bool(os.environ.get("N8N_API_URL") and os.environ.get("N8N_API_KEY"))


def _api(method: str, path: str, body: dict | None = None, timeout: int = 25) -> dict[str, Any]:
    base = os.environ.get("N8N_API_URL", "").strip().rstrip("/")
    key = os.environ.get("N8N_API_KEY", "").strip()
    if not base or not key:
        return {"ok": False, "errore": "n8n API non configurata (N8N_API_URL/N8N_API_KEY)"}
    if urlparse(base).scheme not in ("http", "https"):
        return {"ok": False, "errore": "N8N_API_URL non valido (solo http/https)"}
    url = base + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"X-N8N-API-KEY": key, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
            raw = r.read().decode("utf-8", "replace")
        return {"ok": True, "data": json.loads(raw) if raw else {}}
    except Exception as exc:
        return {"ok": False, "errore": str(exc)[:200]}


def list_workflows() -> list[dict[str, Any]]:
    """Sola lettura: id, nome, attivo dei workflow su n8n (per dare contesto all'AI)."""
    r = _api("GET", "/workflows")
    if not r.get("ok"):
        return []
    items = (r.get("data") or {}).get("data") or r.get("data") or []
    out = []
    for w in items if isinstance(items, list) else []:
        out.append({"id": w.get("id"), "name": w.get("name"),
                    "active": w.get("active"), "nodes": len(w.get("nodes") or [])})
    return out


def get_workflow(workflow_id: str) -> dict[str, Any]:
    r = _api("GET", f"/workflows/{workflow_id}")
    return r.get("data", {}) if r.get("ok") else r


def manage_workflow(op: str, *, workflow_id: str | None = None,
                    definition: dict | None = None) -> dict[str, Any]:
    """Esegue una modifica ai workflow. op: create|update|activate|deactivate.
    DELETE non e' permessa. Usata SOLO dopo conferma umana (perimetro chat)."""
    op = (op or "").lower()
    if op == "create":
        if not isinstance(definition, dict):
            return {"ok": False, "errore": "definition mancante"}
        return _api("POST", "/workflows", definition)
    if op == "update":
        if not workflow_id or not isinstance(definition, dict):
            return {"ok": False, "errore": "workflow_id o definition mancante"}
        return _api("PUT", f"/workflows/{workflow_id}", definition)
    if op in ("activate", "deactivate"):
        if not workflow_id:
            return {"ok": False, "errore": "workflow_id mancante"}
        return _api("POST", f"/workflows/{workflow_id}/{op}")
    return {"ok": False, "errore": f"operazione '{op}' non permessa (mai delete)"}


def _n8n_base() -> str:
    """Base host di n8n (senza /api/v1), per costruire gli URL /webhook/<path>."""
    base = os.environ.get("N8N_API_URL", "").strip().rstrip("/")
    for suf in ("/api/v1", "/api"):
        if base.endswith(suf):
            return base[: -len(suf)]
    return base


def workflow_webhook(workflow_id: str) -> tuple[str | None, str]:
    """(url, metodo) del webhook-trigger di produzione del workflow, dalla definizione.
    Il metodo di default di un webhook n8n è GET (httpMethod assente); usare quello sbagliato
    dà 404. Ritorna (None, 'GET') se non c'è un webhook trigger."""
    wf = get_workflow(workflow_id)
    if not isinstance(wf, dict):
        return None, "GET"
    for n in (wf.get("nodes") or []):
        t = str(n.get("type", "")).lower()
        if "webhook" in t and "respond" not in t:      # trigger, non 'Respond to Webhook'
            p = n.get("parameters") or {}
            path = p.get("path")
            method = str(p.get("httpMethod") or "GET").upper()
            base = _n8n_base()
            if path and base:
                return f"{base}/webhook/{path}", method
    return None, "GET"


def restart_workflow(workflow_id: str, name: str | None = None,
                     payload: dict | None = None, timeout: int = 25) -> dict[str, Any]:
    """Ri-esegue un workflow: preferisce il SUO webhook trigger, col METODO giusto (di solito
    GET), così ri-esegue davvero quello specifico; fallback all'esecutore per nome. Usata dal
    watchdog per i fallimenti transitori (con tetto ai retry a monte)."""
    url, method = None, "GET"
    try:
        url, method = workflow_webhook(workflow_id)
    except Exception:
        url = None
    if url:
        if method == "GET":
            req = urllib.request.Request(url, method="GET")
        else:
            body = json.dumps({"source": "watchdog", "reason": "retry_transitorio",
                               "payload": payload or {}}).encode("utf-8")
            req = urllib.request.Request(url, data=body, method=method,
                                         headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
                r.read()
            return {"ok": True, "via": "webhook", "metodo": method, "workflow_id": workflow_id}
        except Exception as exc:
            return {"ok": False, "via": "webhook", "metodo": method, "errore": str(exc)[:200]}
    out = trigger_n8n(name or workflow_id, payload or {})   # fallback: esecutore per nome
    return {"ok": bool(out.get("ok")), "via": "executor", "errore": out.get("errore")}


def n8n_workflows_tool() -> Tool:
    """Sensore readonly: elenco workflow n8n (degrada a [] senza API)."""
    return Tool(name="leggi_n8n_workflows", action_type=None, readonly=True,
                run=lambda **_: list_workflows())


def list_executions(workflow_id: str | None = None, solo_errori: bool = False,
                    limit: int = 20) -> dict[str, Any]:
    """Esecuzioni recenti dei workflow: per verificare se sono PARTITI e con che ESITO
    (success/error/running). `solo_errori`=True filtra i falliti. Serve N8N_API_URL/KEY."""
    lim = max(1, min(int(limit or 20), 100))
    path = f"/executions?limit={lim}"
    if workflow_id:
        path += f"&workflowId={workflow_id}"
    if solo_errori:
        path += "&status=error"
    r = _api("GET", path)
    if not r.get("ok"):
        return {"ok": False, "errore": r.get("errore"), "esecuzioni": []}
    items = (r.get("data") or {}).get("data") or []
    out = []
    for e in items if isinstance(items, list) else []:
        # n8n recenti espongono 'status'; nei più vecchi lo deduciamo da finished
        status = e.get("status")
        if not status:
            status = "success" if e.get("finished") else ("error" if e.get("stoppedAt") else "running")
        out.append({"id": e.get("id"), "workflowId": e.get("workflowId"),
                    "status": status, "startedAt": e.get("startedAt"),
                    "stoppedAt": e.get("stoppedAt"), "mode": e.get("mode")})
    errori = sum(1 for x in out if str(x["status"]).lower() in ("error", "failed", "crashed"))
    return {"ok": True, "totale": len(out), "errori": errori, "esecuzioni": out}


def get_execution(execution_id: str) -> dict[str, Any]:
    """Dettaglio di una esecuzione (con dati) — per capire QUALE nodo ha dato errore."""
    r = _api("GET", f"/executions/{execution_id}?includeData=true")
    return r.get("data", {}) if r.get("ok") else r


def n8n_executions_tool() -> Tool:
    """Sensore readonly: esecuzioni recenti (partite? errori?). Degrada senza API."""
    return Tool(name="leggi_n8n_esecuzioni", action_type=None, readonly=True,
                run=lambda workflow_id=None, solo_errori=False, limit=20, **_:
                    list_executions(workflow_id, bool(solo_errori), limit))
