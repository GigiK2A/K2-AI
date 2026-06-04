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
    for service_id, blueprint_id in CATALOGO_CHIUSO.items():
        bp, src = assets.load_blueprint(blueprint_id)
        services.append({
            "service_id": service_id,
            "blueprint_id": blueprint_id,
            "nome": (bp or {}).get("titolo", service_id),
            "blueprint_source": src,
        })
    return {
        "engine_version": ENGINE_VERSION,
        "grounding_snapshot_version": assets.snapshot_version(),
        "services": services,
    }


@app.post("/v1/deliverables", status_code=202, dependencies=[Depends(require_bearer)])
def create_deliverable(body: DeliverableBody, bg: BackgroundTasks, response: Response):
    # Entitlement: Phase-1 controlla solo presenza (verifica JWT reale = G1).
    if not body.entitlement_token:
        response.status_code = 402
        return {"status": "payment_required", "service_id": body.service_id}

    # Routing sincrono (per restituire subito refuse out_of_catalog).
    try:
        blueprint_id, confidence = pipeline.route(body.service_id)
    except pipeline.Refuse as r:
        response.status_code = 422
        return {"status": "refused", "reason": r.reason, "message": r.message}

    job_id = jobs.create(body.service_id, blueprint_id, confidence)
    bg.add_task(pipeline.run, job_id, body.service_id, body.inputs)
    return {"job_id": job_id, "status": "routed",
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
