"""8e — API FastAPI (Phase-1). Contratto: docs/interfaccia-kbot-8e.md §1."""
from __future__ import annotations

from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, Field

from . import assets, jobs, pipeline, entitlement, ratelimit
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
    from .settings import ENTITLEMENT_SECRET, ANTHROPIC_API_KEY
    warnings = []
    if not ENTITLEMENT_SECRET:
        warnings.append("K2A_ENTITLEMENT_SECRET non configurato → entitlement permissivo (NON per produzione)")
    if not ANTHROPIC_API_KEY:
        warnings.append("ANTHROPIC_API_KEY non configurato → filiera offline (deliverable segnaposto)")
    return {
        "status": "ok",
        "version": ENGINE_VERSION,
        "snapshot_version": assets.snapshot_version(),
        "phase": "1",
        "entitlement": "enforced" if ENTITLEMENT_SECRET else "permissive",
        "filiera": "anthropic" if ANTHROPIC_API_KEY else "offline",
        "warnings": warnings,
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


@app.get("/v1/form/{service_id}", dependencies=[Depends(require_bearer)])
def get_form(service_id: str):
    """Campi form (form.json) che il deliverable richiede — il K-BOT li usa per
    raccogliere gli input dal cliente prima della generazione."""
    skill = assets.service_to_skill(service_id)
    if not skill:
        raise HTTPException(status_code=404, detail="service_id sconosciuto")
    form = assets.load_form(skill) or {}
    # form.json reale = JSON Schema (properties + required); ritorniamo i campi
    # in forma normalizzata per il frontend.
    props = form.get("properties", {})
    required = set(form.get("required", []))
    campi = []
    # Metadato comune a TUTTI i report. In passato non era richiesto dai form e
    # la copertina usciva come "Cliente / —" anche su documenti venduti.
    if "ragione_sociale" not in props:
        campi.append({
            "id": "ragione_sociale", "label": "Ragione sociale o nome del soggetto analizzato",
            "tipo": "string", "enum": None, "items_enum": None, "obbligatorio": True,
        })
    for name, spec in props.items():
        t = spec.get("type")
        t = t[0] if isinstance(t, list) else t
        campi.append({
            "id": name,
            "label": spec.get("description") or name.replace("_", " ").capitalize(),
            "tipo": t,
            "enum": spec.get("enum"),
            "items_enum": (spec.get("items") or {}).get("enum"),
            "obbligatorio": name in required,
        })
    return {"service_id": service_id, "skill": skill, "title": form.get("title"),
            "campi": campi, "schema": form}


@app.post("/v1/deliverables", status_code=202, dependencies=[Depends(require_bearer)])
def create_deliverable(body: DeliverableBody, bg: BackgroundTasks, response: Response,
                       authorization: str = Header(default="")):
    ratelimit.check(authorization[-16:] or "anon")  # per-chiave
    auth_level = (body.auth_level or "FULL").upper()
    if auth_level not in ("PREVIEW", "FULL"):
        raise HTTPException(status_code=400, detail="auth_level ∈ {PREVIEW, FULL}")

    # FULL richiede entitlement VALIDO (JWT firmato dal K-BOT, G1). PREVIEW è
    # gratis entro quota: il gate preview nel K-BOT ha già verificato.
    if auth_level == "FULL":
        ok, reason = entitlement.verify(body.entitlement_token, body.service_id)
        if not ok:
            response.status_code = 402
            return {"status": "payment_required", "service_id": body.service_id,
                    "reason": reason}

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
