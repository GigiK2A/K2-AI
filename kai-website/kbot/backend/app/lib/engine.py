"""Client per il motore 8e (membrana docs/interfaccia-kbot-8e.md §1).

Il K-BOT NON genera deliverable: li richiede all'8e via questo client.
In dev punta al MOCK (kbot/mock-8e); in prod all'8e reale (kai-website/k2a-8e su
Railway). Swap = solo env K2A_8E_BASE_URL/K2A_8E_API_KEY.

API consumate:
  GET  /v1/catalog
  POST /v1/deliverables            → {job_id, status, confidence} | 402 | 422 refused
  GET  /v1/deliverables/{job_id}   → {status, outputs, validation, citazioni, ...}
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

import httpx

from ..settings import ENGINE_8E_BASE_URL, ENGINE_8E_API_KEY

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if ENGINE_8E_API_KEY:
        h["Authorization"] = f"Bearer {ENGINE_8E_API_KEY}"
    return h


class EngineError(Exception):
    pass


class EngineRefused(Exception):
    """L'8e ha rifiutato (route-or-refuse). reason ∈ out_of_catalog|low_confidence|..."""
    def __init__(self, reason: str, message: str):
        self.reason = reason
        self.message = message
        super().__init__(f"{reason}: {message}")


class EnginePaymentRequired(Exception):
    pass


async def create_deliverable(
    service_id: str, inputs: dict, entitlement_token: Optional[str] = None,
    tier: Optional[str] = None, auth_level: str = "FULL",
) -> dict:
    """POST /v1/deliverables. Ritorna {job_id, status, auth_level, confidence}.

    auth_level FULL → serve entitlement_token (gate documento); PREVIEW → gratis
    entro quota (gate preview già verificato dal chiamante). Solleva
    EnginePaymentRequired (402), EngineRefused (422), EngineError (altro).
    """
    payload: dict[str, Any] = {
        "service_id": service_id,
        "inputs": inputs,
        "auth_level": auth_level,
    }
    if entitlement_token:
        payload["entitlement_token"] = entitlement_token
    if tier:
        payload["tier"] = tier

    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.post(f"{ENGINE_8E_BASE_URL}/v1/deliverables",
                         json=payload, headers=_headers())

    if r.status_code == 202:
        return r.json()
    if r.status_code == 402:
        raise EnginePaymentRequired(r.json().get("service_id", service_id))
    if r.status_code == 422:
        body = r.json()
        raise EngineRefused(body.get("reason", "refused"), body.get("message", ""))
    raise EngineError(f"8e {r.status_code}: {r.text[:300]}")


def render_deliverable_sync(service_id: str, deliverable: dict, citazioni: Optional[list] = None,
                            inputs: Optional[dict] = None) -> dict:
    """POST /v1/render (SINCRONO) — renderizza un deliverable già generato (agente A2)
    → job 8e {status rendered|refused, outputs}. Sincrono perché chiamato dal background
    task dell'agente (già fuori dal request path). EngineRefused se il CAGE blocca."""
    payload: dict[str, Any] = {"service_id": service_id, "deliverable": deliverable,
                               "citazioni": citazioni or [], "inputs": inputs or {}}
    with httpx.Client(timeout=_TIMEOUT) as c:
        r = c.post(f"{ENGINE_8E_BASE_URL}/v1/render", json=payload, headers=_headers())
    if r.status_code == 422:
        body = r.json()
        raise EngineRefused(body.get("reason", "refused"), body.get("message", ""))
    if r.status_code != 200:
        raise EngineError(f"8e render {r.status_code}: {r.text[:300]}")
    return r.json()


async def get_deliverable(job_id: str) -> dict:
    """GET /v1/deliverables/{job_id}. Ritorna lo stato job."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.get(f"{ENGINE_8E_BASE_URL}/v1/deliverables/{job_id}", headers=_headers())
    if r.status_code == 404:
        raise EngineError("job non trovato")
    if r.status_code != 200:
        raise EngineError(f"8e {r.status_code}: {r.text[:300]}")
    return r.json()


_FORM_CACHE: dict[str, tuple[float, dict]] = {}
_FORM_TTL_S = 600  # 10 min: i form 8e sono semi-statici, ma un cambio schema lato 8e DEVE
                   # propagare al K-BOT. Prima la cache era eterna → uno schema aggiornato
                   # sull'8e restava stale all'infinito (finché il processo non riavviava).


async def get_form(service_id: str) -> dict:
    """Campi form richiesti dal deliverable (per raccolta input lato K-BOT).

    I form sono asset statici del blueprint → cache di processo CON TTL: la chat li
    interroga a ogni turno (per sapere COSA raccogliere) e non deve colpire l'8e ogni
    volta, ma un cambio schema 8e si propaga entro il TTL (vedi _FORM_TTL_S)."""
    ent = _FORM_CACHE.get(service_id)
    if ent is not None and (time.monotonic() - ent[0]) < _FORM_TTL_S:
        return ent[1]
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.get(f"{ENGINE_8E_BASE_URL}/v1/form/{service_id}", headers=_headers())
    if r.status_code == 404:
        raise EngineError("servizio sconosciuto")
    if r.status_code != 200:
        raise EngineError(f"8e form {r.status_code}: {r.text[:200]}")
    data = r.json()
    _FORM_CACHE[service_id] = (time.monotonic(), data)
    return data


async def get_catalog() -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.get(f"{ENGINE_8E_BASE_URL}/v1/catalog", headers=_headers())
    if r.status_code != 200:
        raise EngineError(f"8e catalog {r.status_code}: {r.text[:200]}")
    return r.json()


async def health() -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.get(f"{ENGINE_8E_BASE_URL}/health")
    return r.json() if r.status_code == 200 else {"status": "down", "code": r.status_code}
