"""MOCK 8e — finto motore di generazione deliverable.

Implementa fedelmente il contratto `docs/interfaccia-kbot-8e.md §1` per
permettere a Luigi di sviluppare il client 8e, l'UI percorsi e l'upsell PRIMA
che l'8e reale esista. Quando l'8e vero è pronto, si fa swap cambiando solo
`K2A_8E_BASE_URL` nel backend K-BOT — zero modifiche al client.

NON è il motore reale: niente skill, niente grounding, niente Claude. Genera un
PDF placeholder e simula la macchina a stati del job in base al tempo trascorso.

Run:
    cd kbot/mock-8e
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8800

Auth: header `Authorization: Bearer <MOCK_8E_API_KEY>` (default "dev-key").
Trigger di refuse (per testare gli edge case dal client):
    - service_id == "force-refuse"          → 422 out_of_catalog
    - inputs.force == "low_confidence"       → 422 low_confidence
    - inputs.force == "validation_failed"    → job va in status refused
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

API_KEY = os.environ.get("MOCK_8E_API_KEY", "dev-key")
ENGINE_VERSION = "mock-0.1"
SNAPSHOT_VERSION = "mock-0.1"
CATALOG_VERSION = "0.1.0-interim"

# Tempi (s) di transizione di stato — accorcia per test veloci con MOCK_8E_FAST=1
FAST = os.environ.get("MOCK_8E_FAST", "0") in ("1", "true", "yes")
T_RUNNING = 1 if FAST else 3
T_VALIDATING = 2 if FAST else 6
T_RENDERED = 3 if FAST else 9

app = FastAPI(title="MOCK 8e", version=ENGINE_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # mock locale, non produzione
    allow_methods=["*"],
    allow_headers=["*"],
)

# Catalogo finto minimale (specchio ridotto di catalog.json) per GET /v1/catalog.
# Il mock NON legge catalog.json: simula "cosa l'8e sa generare".
_MOCK_CATALOG = {
    "check-pmi-express.check": {"label": "Check Express", "tier": "check"},
    "flusso-legalboost-pmi.boost": {"label": "LegalBoost", "tier": "boost"},
    "flusso-fiscoboost-pmi.boost": {"label": "FiscoBoost", "tier": "boost"},
    "flusso-advisorboost-pmi.boost": {"label": "AdvisorBoost", "tier": "boost"},
    "flusso-agevolazioni-pmi.boost": {"label": "Dossier Agevolazioni", "tier": "boost"},
    "analisi-settore-pmi.tappa": {"label": "Analisi settore", "tier": "tappa"},
    "analisi-bilancio-pmi.tappa": {"label": "Analisi bilancio", "tier": "tappa"},
    "posizionamento-pmi.tappa": {"label": "Posizionamento", "tier": "tappa"},
}

# Job store in-memory (il mock è stateful per processo; l'8e reale è stateless
# con storage dedicato — irrilevante per il client).
_JOBS: dict[str, dict] = {}

# PDF placeholder valido (1 pagina, "K2-AI MOCK DELIVERABLE").
_MOCK_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]"
    b"/Resources<</Font<</F1 5 0 R>>>>/Contents 4 0 R>>endobj\n"
    b"4 0 obj<</Length 78>>stream\n"
    b"BT /F1 24 Tf 60 760 Td (K2-AI MOCK DELIVERABLE) Tj "
    b"0 -36 Td /F1 12 Tf (placeholder - non e' il report reale) Tj ET\n"
    b"endstream endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"xref\n0 6\n0000000000 65535 f \n"
    b"trailer<</Root 1 0 R/Size 6>>\n"
    b"startxref\n0\n%%EOF"
)


def _check_auth(authorization: Optional[str]) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer")
    token = authorization.split(" ", 1)[1].strip()
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="bad key")


class DeliverableBody(BaseModel):
    service_id: str
    tier: Optional[str] = None
    inputs: dict = Field(default_factory=dict)
    entitlement_token: Optional[str] = None


@app.get("/health")
def health():
    return {"ok": True, "engine_version": ENGINE_VERSION, "mock": True}


@app.get("/v1/catalog")
def catalog(authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)
    return {
        "engine_version": ENGINE_VERSION,
        "grounding_snapshot_version": SNAPSHOT_VERSION,
        "catalog_version": CATALOG_VERSION,
        "blueprints": [
            {"blueprint_id": k, **v} for k, v in _MOCK_CATALOG.items()
        ],
    }


@app.post("/v1/deliverables", status_code=202)
def create_deliverable(
    body: DeliverableBody,
    response: Response,
    authorization: Optional[str] = Header(default=None),
):
    _check_auth(authorization)

    # Entitlement: il mock controlla solo presenza (l'8e reale verifica JWT — G1).
    if not body.entitlement_token:
        response.status_code = 402
        return {"status": "payment_required", "reason": "payment_required",
                "message": "entitlement_token mancante"}

    # Trigger di refuse per test del client.
    if body.service_id == "force-refuse":
        response.status_code = 422
        return {"status": "refused", "reason": "out_of_catalog",
                "message": f"service_id '{body.service_id}' non a catalogo"}
    if (body.inputs or {}).get("force") == "low_confidence":
        response.status_code = 422
        return {"status": "refused", "reason": "low_confidence",
                "message": "intent ambiguo, confidence < 0.4"}

    # Risolvi il blueprint dal service_id (il client manda service_id del catalog;
    # il mock accetta sia un blueprint_id diretto sia un alias noto).
    blueprint = body.service_id if body.service_id in _MOCK_CATALOG else None
    if blueprint is None:
        # prova mapping grossolano service_id → blueprint per i casi del catalog.json
        guess = {
            "check-express": "check-pmi-express.check",
            "flusso-legalboost-pmi": "flusso-legalboost-pmi.boost",
            "flusso-fiscoboost-pmi": "flusso-fiscoboost-pmi.boost",
            "flusso-advisorboost-pmi": "flusso-advisorboost-pmi.boost",
            "flusso-agevolazioni-pmi": "flusso-agevolazioni-pmi.boost",
            "ab-tappa-1": "check-pmi-express.check",
            "ab-tappa-2": "analisi-settore-pmi.tappa",
            "ab-tappa-3": "analisi-bilancio-pmi.tappa",
            "ab-tappa-4": "posizionamento-pmi.tappa",
            "ab-tappa-5": "flusso-advisorboost-pmi.boost",
        }.get(body.service_id)
        blueprint = guess

    if blueprint is None:
        # Il vero 8e instrada per service_id del catalog (manifest keyed = checkup_*,
        # check_*_express, ...). Il mock NON ha l'elenco completo: simula qualunque
        # service_id plausibile con un blueprint generico (la refuse esplicita resta
        # su service_id == "force-refuse", gestita sopra).
        blueprint = f"{body.service_id}.generic"

    job_id = "job_" + uuid.uuid4().hex[:12]
    _JOBS[job_id] = {
        "created_at": time.time(),
        "service_id": body.service_id,
        "blueprint": blueprint,
        "force_validation_fail": (body.inputs or {}).get("force") == "validation_failed",
    }
    return {"job_id": job_id, "status": "routed", "confidence": 0.92}


def _job_status(job: dict) -> str:
    elapsed = time.time() - job["created_at"]
    if elapsed < T_RUNNING:
        return "routed"
    if elapsed < T_VALIDATING:
        return "running"
    if elapsed < T_RENDERED:
        return "validating"
    return "refused" if job["force_validation_fail"] else "rendered"


@app.get("/v1/deliverables/{job_id}")
def get_deliverable(job_id: str, authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="unknown job")

    status = _job_status(job)
    base = {
        "job_id": job_id,
        "status": status,
        "engine_version": ENGINE_VERSION,
        "grounding_snapshot_version": SNAPSHOT_VERSION,
        "catalog_version": CATALOG_VERSION,
    }

    if status == "refused":
        return {**base, "refusal_reason": "validation_failed",
                "validation": {"L1": "PASS", "L2": "FAIL"},
                "outputs": None, "citazioni": []}

    if status != "rendered":
        return {**base, "outputs": None, "validation": None, "citazioni": []}

    # rendered → restituisci URL del mock (il client li tratta come opachi).
    dl = f"/v1/deliverables/{job_id}/download"
    return {
        **base,
        "outputs": {
            "html_url": f"{dl}?fmt=html",
            "pdf_url": f"{dl}?fmt=pdf",
            "bundle": [{"type": "json", "url": f"{dl}?fmt=json"}],
        },
        "validation": {"L1": "PASS", "L2": "PASS"},
        "citazioni": [
            {"campo": "esempio", "fonte": "MOCK", "coordinate": "art.0",
             "vigenza": "mock"}
        ],
        "refusal_reason": None,
    }


@app.get("/v1/deliverables/{job_id}/download")
def download(job_id: str, fmt: str = "pdf"):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="unknown job")
    if _job_status(job) != "rendered":
        raise HTTPException(status_code=409, detail="not ready")
    if fmt == "pdf":
        return Response(content=_MOCK_PDF, media_type="application/pdf")
    if fmt == "json":
        return {"mock": True, "service_id": job["service_id"], "blueprint": job["blueprint"]}
    return Response(content=b"<h1>K2-AI MOCK DELIVERABLE</h1>", media_type="text/html")
