"""Job store + runner per i Boost dell'AGENTE A2 (async, stesso contratto dell'8e).

L'8e traccia i suoi job nel suo processo; l'agente A2 (boost_agent) gira NEL backend
→ serve un registro locale. In-memory come l'8e (perso al restart: accettabile per la
finestra di polling). Il runner gira in un BackgroundTask FastAPI (fuori dal request
path → nessun timeout HTTP): estrae gli input, esegue l'agente (lento, LLM+MCP), poi
fa renderizzare il deliverable dall'8e (/v1/render, stesso CAGE del flusso normale) e
copia l'esito nel job — così pdf/json/poll passano dagli STESSI endpoint di serving.
"""
from __future__ import annotations

import logging
import threading
import uuid
from typing import Optional

log = logging.getLogger(__name__)

_PREFIX = "agt_"
_LOCK = threading.Lock()
_JOBS: dict[str, dict] = {}


def is_agent_job(job_id: str) -> bool:
    return str(job_id).startswith(_PREFIX)


def create(service_id: str) -> str:
    jid = _PREFIX + uuid.uuid4().hex[:12]
    with _LOCK:
        _JOBS[jid] = {"job_id": jid, "service_id": service_id, "status": "running",
                      "outputs": None, "source": "agent_a2"}
    return jid


def update(job_id: str, **fields) -> None:
    with _LOCK:
        if job_id in _JOBS:
            _JOBS[job_id].update(fields)


def get(job_id: str) -> Optional[dict]:
    with _LOCK:
        return dict(_JOBS[job_id]) if job_id in _JOBS else None


def run(job_id: str, session: dict, servizio_id: str, skill_text: str,
        sezioni: list, campi: list) -> None:
    """Background task SINCRONO: autofill → agente → render 8e → store. Fail-closed:
    ogni errore marca il job (refused/error), non solleva (è fuori dal request path)."""
    from . import autofill, boost_agent, engine
    try:
        inputs = autofill.extract_inputs(session, campi)
        res = boost_agent.run_boost_agent(skill_text, inputs, servizio_id, sezioni=sezioni)
        if not res.get("delivered"):
            update(job_id, status="refused", refusal_reason="agent_refused",
                   validation={"problemi": res.get("problemi"),
                               "deliverable_rejected": res.get("deliverable_rejected")})
            return
        # Render via 8e (/v1/render): stesso CAGE + enrich del flusso normale.
        rj = engine.render_deliverable_sync(servizio_id, res["deliverable"], inputs=inputs)
        update(job_id, status=rj.get("status", "rendered"), outputs=rj.get("outputs"),
               validation={**(rj.get("validation") or {}), "agent_metrics": res.get("metrics"),
                           "provenance_calls": len(res.get("provenance_calls") or [])},
               citazioni=rj.get("citazioni"), meta=rj.get("meta"))
    except engine.EngineRefused as r:
        update(job_id, status="refused", refusal_reason=r.reason, error=r.message)
    except Exception as exc:  # pragma: no cover — fail-closed, il poll vedrà 'error'
        log.exception("agent job %s fallito", job_id)
        update(job_id, status="error", error=str(exc)[:300])
