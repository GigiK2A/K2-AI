"""8e — API FastAPI (Phase-1). Contratto: docs/interfaccia-kbot-8e.md §1."""
from __future__ import annotations

from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from . import assets, jobs, pipeline
from .auth import require_bearer
from .settings import CATALOGO_CHIUSO, ENGINE_VERSION

app = FastAPI(title="K2-AI 8e", version=ENGINE_VERSION)


class DeliverableBody(BaseModel):
    service_id: str
    tier: Optional[str] = None
    inputs: dict = Field(default_factory=dict)
    entitlement_token: Optional[str] = None
    # Gate di erogazione (handoff W8): il LIVELLO è deciso dal gate stateful nel
    # K-BOT backend (registrazione/contatore/pagamento), l'8e lo riceve e compone
    # di conseguenza. PREVIEW = assaggio (score + criticità #1 + resto nascosto);
    # FULL = documento completo + file. Default FULL (retrocompat).
    auth_level: str = "FULL"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": ENGINE_VERSION,
        "snapshot_version": assets.snapshot_version(),
        "phase": "1",
    }


@app.get("/v1/catalog", dependencies=[Depends(require_bearer)])
def catalog():
    services = []
    for service_id, entry in CATALOGO_CHIUSO.items():
        skill = entry.get("skill")
        bp = assets.load_blueprint(skill) or {}
        services.append({
            "service_id": service_id,
            "blueprint_id": entry.get("blueprint_id"),
            "skill": skill,
            "nome": bp.get("pacchetto", {}).get("nome_commerciale", service_id),
        })
    return {
        "engine_version": ENGINE_VERSION,
        "grounding_snapshot_version": assets.snapshot_version(),
        "services": services,
    }


@app.post("/v1/deliverables", status_code=202, dependencies=[Depends(require_bearer)])
def create_deliverable(body: DeliverableBody, bg: BackgroundTasks, response: Response):
    auth_level = (body.auth_level or "FULL").upper()
    if auth_level not in ("PREVIEW", "FULL"):
        raise HTTPException(status_code=400, detail="auth_level ∈ {PREVIEW, FULL}")

    # FULL richiede entitlement (il gate documento nel K-BOT l'ha verificato e
    # rilasciato il token). PREVIEW è gratis entro quota: il gate preview nel
    # K-BOT ha già verificato registrazione + contatore → niente token.
    if auth_level == "FULL" and not body.entitlement_token:
        response.status_code = 402
        return {"status": "payment_required", "service_id": body.service_id}

    # Routing sincrono (per restituire subito refuse out_of_catalog).
    try:
        _skill, blueprint_id, confidence = pipeline.route(body.service_id)
    except pipeline.Refuse as r:
        response.status_code = 422
        return {"status": "refused", "reason": r.reason, "message": r.message}

    job_id = jobs.create(body.service_id, blueprint_id, confidence)
    bg.add_task(pipeline.run, job_id, body.service_id, body.inputs, auth_level)
    return {"job_id": job_id, "status": "routed", "auth_level": auth_level,
            "routed_blueprint": blueprint_id, "confidence": confidence}


@app.get("/v1/deliverables/{job_id}", dependencies=[Depends(require_bearer)])
def get_deliverable(job_id: str):
    j = jobs.get(job_id)
    if not j:
        raise HTTPException(status_code=404, detail="unknown job")
    return {
        "job_id": j["job_id"],
        "status": j["status"],
        "outputs": j.get("outputs"),
        "validation": j.get("validation"),
        "citazioni": j.get("citazioni", []),
        "refusal_reason": j.get("refusal_reason"),
        "error": j.get("error"),
        "meta": j.get("meta"),
    }
