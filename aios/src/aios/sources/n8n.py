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
