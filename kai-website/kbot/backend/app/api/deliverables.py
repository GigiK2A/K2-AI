"""Endpoint deliverable: il K-BOT instrada all'8e e fa da proxy di stato.

POST /api/kbot/deliverables          → crea un job 8e per il servizio acquistato
GET  /api/kbot/deliverables/{job_id} → stato job (polling lato frontend)
GET  /api/kbot/engine/health         → liveness 8e (debug)

Entitlement (membrana G1): in Phase-1 il token è un placeholder. Quando il binding
billing→entitlement sarà pronto, il token JWT verrà rilasciato al pagamento e
verificato dall'8e. Qui si verifica solo che il servizio sia pagato sulla sessione.
"""
from __future__ import annotations

import logging
from typing import Optional

from datetime import datetime, timezone

import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .. import settings
from ..lib import engine, sessions, catalog, entitlement, autofill
from ..lib.auth import AuthUser, optional_user, require_user
from ..lib.storage import upload_pdf
from ..lib.supabase_admin import get_admin_client
from ..settings import STORAGE_REPORTS_BUCKET

router = APIRouter()
log = logging.getLogger(__name__)

PREVIEW_LIMIT_MESE = 2  # gate W8, A/B 2 vs 3 post-live


class DeliverableBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    servizioId: str = Field(..., alias="servizio_id")
    inputs: dict = Field(default_factory=dict)

    class Config:
        populate_by_name = True


def _check_ownership(session: dict, user: Optional[AuthUser]) -> None:
    owner = session.get("user_id")
    if owner and (not user or user.id != owner):
        raise HTTPException(status_code=403, detail="not your session")


def _mint_entitlement(session: dict, servizio_id: str, tier: Optional[str] = None) -> Optional[str]:
    """Entitlement JWT (G1) se il servizio risulta pagato. Firmato HS256, verificato
    stateless dall'8e. Fallback al placeholder solo se il segreto non è configurato
    (dev senza K2A_ENTITLEMENT_SECRET)."""
    # FREE MODE (K-BOT ufficiale senza paywall): genera anche senza pagamento
    # (token comunque mintato; l'8e con K2A_8E_ENTITLEMENT_DEV=true lo accetta).
    # Con KBOT_FREE_MODE=0 il gate "servizio non pagato" torna attivo.
    if session.get("status") != "paid" and not settings.KBOT_FREE_MODE:
        return None
    token = entitlement.mint(
        user_id=session.get("user_id"),
        service_id=servizio_id,
        tier=tier,
        session_id=str(session.get("id")),
    )
    return token or f"dev-unsigned-{session.get('id')}-{servizio_id}"


@router.post("/deliverables")
async def create(body: DeliverableBody, user: Optional[AuthUser] = Depends(optional_user)):
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    _check_ownership(session, user)

    servizio = catalog.get_servizio(body.servizioId)
    if not servizio:
        raise HTTPException(status_code=404, detail="servizio non a catalogo")

    # Solo i servizi generabili via 8e passano di qui; gli high-touch no.
    if not catalog.is_8e_generabile(body.servizioId):
        raise HTTPException(status_code=409,
                            detail="servizio non generabile via 8e (high-touch)")

    entitlement_token = _mint_entitlement(session, body.servizioId, tier=servizio.get("tipo"))
    if not entitlement_token:
        raise HTTPException(status_code=402, detail="servizio non pagato")

    # L'8e instrada per service_id (chiave manifest = id catalog, stessa fonte
    # k2a-catalogo); è l'8e a risolvere service_id→blueprint internamente.
    try:
        res = await engine.create_deliverable(
            service_id=body.servizioId,
            inputs=body.inputs,
            entitlement_token=entitlement_token,
            tier=servizio.get("tipo"),
            auth_level="FULL",
        )
    except engine.EnginePaymentRequired:
        raise HTTPException(status_code=402, detail="entitlement rifiutato dall'8e")
    except engine.EngineRefused as r:
        raise HTTPException(status_code=422, detail={"reason": r.reason, "message": r.message})
    except engine.EngineError as e:
        log.warning("8e error: %s", e)
        raise HTTPException(status_code=502, detail="motore non disponibile")

    # Persisti il job dentro collected_data (JSONB esistente), NON come colonne
    # top-level: deliverable_job_id/deliverable_service NON esistono come colonne
    # di kbot_sessions → un update con quei nomi darebbe 500. Il polling usa
    # comunque il job_id dalla response, non dalla sessione. Best-effort: un
    # fallimento di persistenza non deve far fallire la generazione già avviata.
    try:
        collected = dict(session.get("collected_data") or {})
        collected["deliverable_job_id"] = res.get("job_id")
        collected["deliverable_service"] = body.servizioId
        sessions.update_session(body.sessionId, {"collected_data": collected})
    except Exception:
        log.warning("persist deliverable job fallita (non bloccante)", exc_info=True)
    return res


class AutoBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    servizioId: Optional[str] = Field(default=None, alias="servizio_id")

    class Config:
        populate_by_name = True


@router.post("/deliverables/auto")
async def auto_deliverable(body: AutoBody, user: Optional[AuthUser] = Depends(optional_user)):
    """Genera il documento SENZA form: il boost è quello già instradato dalla chat
    (o ridedotto dal caso), e gli input 8e sono AUTO-COMPILATI dalla conversazione
    e dai file/bilanci caricati. È il flusso 'chiedi → raccogli → genera. Punto.'."""
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    _check_ownership(session, user)

    collected = dict(session.get("collected_data") or {})
    servizio_id = body.servizioId or collected.get("boost_suggerito")
    if not servizio_id:
        # ridedotto dal riepilogo/estratto della conversazione
        summary = {**(collected.get("extractedData") or {}), **collected}
        sug = catalog.suggest_boost(summary)
        servizio_id = sug["id"] if sug else None
    if not servizio_id or not catalog.is_8e_generabile(servizio_id):
        raise HTTPException(status_code=409, detail="nessun documento generabile per questa conversazione")
    servizio = catalog.get_servizio(servizio_id)

    # Campi richiesti dal boost → auto-compilazione dai dati della conversazione.
    try:
        form = await engine.get_form(servizio_id)
        campi = form.get("campi") or []
    except engine.EngineError:
        campi = []
    inputs = autofill.extract_inputs(session, campi)

    entitlement_token = _mint_entitlement(session, servizio_id, tier=servizio.get("tipo"))
    if not entitlement_token:
        raise HTTPException(status_code=402, detail="servizio non pagato")

    try:
        res = await engine.create_deliverable(
            service_id=servizio_id, inputs=inputs,
            entitlement_token=entitlement_token, tier=servizio.get("tipo"), auth_level="FULL",
        )
    except engine.EnginePaymentRequired:
        raise HTTPException(status_code=402, detail="entitlement rifiutato dall'8e")
    except engine.EngineRefused as r:
        raise HTTPException(status_code=422, detail={"reason": r.reason, "message": r.message})
    except engine.EngineError as e:
        log.warning("8e error: %s", e)
        raise HTTPException(status_code=502, detail="motore non disponibile")

    try:
        collected["deliverable_job_id"] = res.get("job_id")
        collected["deliverable_service"] = servizio_id
        collected["deliverable_label"] = servizio.get("label")
        sessions.update_session(body.sessionId, {"collected_data": collected})
    except Exception:
        log.warning("persist deliverable job (auto) fallita (non bloccante)", exc_info=True)

    return {**res, "servizio_id": servizio_id, "label": servizio.get("label")}


# --- Gate Preview (W8): gratis, max 2/mese, utente registrato -------------

class PreviewBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    servizioId: str = Field(..., alias="servizio_id")
    inputs: dict = Field(default_factory=dict)

    class Config:
        populate_by_name = True


@router.post("/preview")
async def create_preview(body: PreviewBody, user: AuthUser = Depends(require_user)):
    """Anteprima gratuita (score + criticità #1). Richiede utente registrato e
    consuma una delle 2 preview/mese. L'8e compone solo l'assaggio (auth PREVIEW).
    """
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    _check_ownership(session, user)

    if not catalog.is_8e_generabile(body.servizioId):
        raise HTTPException(status_code=409, detail="servizio non generabile via 8e")

    # Gate contatore: incremento atomico con cap (funzione SQL).
    ym = datetime.now(timezone.utc).strftime("%Y-%m")
    try:
        client = get_admin_client()
        rpc = client.rpc("kbot_preview_consume",
                         {"p_user": user.id, "p_ym": ym, "p_limit": PREVIEW_LIMIT_MESE}).execute()
        new_count = rpc.data
    except Exception as exc:
        log.warning("preview counter error: %s", exc)
        raise HTTPException(status_code=503, detail="contatore preview non disponibile")

    if new_count is None:
        # quota esaurita → invita al documento (Gate Documento)
        raise HTTPException(status_code=409,
                            detail={"reason": "preview_quota_exhausted",
                                    "limit": PREVIEW_LIMIT_MESE,
                                    "message": "Hai esaurito le anteprime gratuite del mese. "
                                               "Sblocca il documento completo."})

    servizio = catalog.get_servizio(body.servizioId)
    try:
        res = await engine.create_deliverable(
            service_id=body.servizioId,
            inputs=body.inputs,
            auth_level="PREVIEW",
            tier=(servizio or {}).get("tipo"),
        )
    except engine.EngineRefused as r:
        raise HTTPException(status_code=422, detail={"reason": r.reason, "message": r.message})
    except engine.EngineError as e:
        log.warning("8e preview error: %s", e)
        raise HTTPException(status_code=502, detail="motore non disponibile")

    return {**res, "preview_count": new_count, "preview_limit": PREVIEW_LIMIT_MESE}


@router.get("/deliverables/{job_id}")
async def status(job_id: str):
    try:
        return await engine.get_deliverable(job_id)
    except engine.EngineError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/deliverables/{job_id}/pdf")
async def deliverable_pdf(job_id: str):
    """Serve il PDF del deliverable generato dal motore 8e. Nel container unico 8e
    e backend kbot condividono il filesystem → il PDF si legge dal path locale
    prodotto dal 8e. Nessuna auth: job_id opaco, come lo status poll."""
    try:
        job = await engine.get_deliverable(job_id)
    except engine.EngineError as e:
        raise HTTPException(status_code=502, detail=str(e))
    if job.get("status") != "rendered":
        raise HTTPException(status_code=409, detail="documento non ancora pronto")
    pdf_path = (job.get("outputs") or {}).get("pdf_path")
    if not pdf_path or not os.path.isfile(pdf_path):
        raise HTTPException(status_code=404, detail="pdf non disponibile")
    # Sicurezza: solo file sotto la out-dir del motore 8e (niente path traversal).
    out_root = os.path.realpath(os.environ.get("K2A_8E_OUT_DIR", "/tmp/8e_out"))
    if not os.path.realpath(pdf_path).startswith(out_root + os.sep):
        raise HTTPException(status_code=403, detail="percorso non consentito")
    return FileResponse(pdf_path, media_type="application/pdf", filename="report-k2ai.pdf")


class SaveDeliverableBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    jobId: str = Field(..., alias="job_id")

    class Config:
        populate_by_name = True


@router.post("/deliverables/save")
async def save_deliverable(body: SaveDeliverableBody,
                           user: Optional[AuthUser] = Depends(optional_user)):
    """Rende DURATURO il deliverable 8e: carica il PDF (effimero in /tmp) su
    Supabase Storage e lo lega alla sessione → compare in dashboard/storico.
    Idempotente: se già salvato per questo job, ritorna l'URL esistente."""
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    _check_ownership(session, user)

    collected = dict(session.get("collected_data") or {})
    if collected.get("deliverable_saved_job") == body.jobId and session.get("pdf_url"):
        return {"pdf_url": session["pdf_url"], "cached": True}

    try:
        job = await engine.get_deliverable(body.jobId)
    except engine.EngineError as e:
        raise HTTPException(status_code=502, detail=str(e))
    if job.get("status") != "rendered":
        raise HTTPException(status_code=409, detail="documento non ancora pronto")
    pdf_path = (job.get("outputs") or {}).get("pdf_path")
    if not pdf_path or not os.path.isfile(pdf_path):
        raise HTTPException(status_code=404, detail="pdf non disponibile")
    out_root = os.path.realpath(os.environ.get("K2A_8E_OUT_DIR", "/tmp/8e_out"))
    if not os.path.realpath(pdf_path).startswith(out_root + os.sep):
        raise HTTPException(status_code=403, detail="percorso non consentito")

    with open(pdf_path, "rb") as f:
        content = f.read()
    public_url = upload_pdf(
        bucket=STORAGE_REPORTS_BUCKET,
        path=f"deliverables/{body.sessionId}/{body.jobId}.pdf",
        content=content,
    )
    # Label leggibile del servizio per la dashboard/storico.
    servizio_id = collected.get("deliverable_service") or ""
    servizio = catalog.get_servizio(servizio_id) if servizio_id else None
    collected["deliverable_saved_job"] = body.jobId
    collected["deliverable_pdf_url"] = public_url
    if servizio:
        collected["deliverable_label"] = servizio.get("label")
    sessions.update_session(body.sessionId, {"pdf_url": public_url, "collected_data": collected})
    return {"pdf_url": public_url}


@router.get("/deliverables/form/{servizio_id}")
async def deliverable_form(servizio_id: str):
    """Campi che il deliverable richiede — il frontend li mostra per raccogliere
    gli input del cliente prima di generare."""
    if not catalog.is_8e_generabile(servizio_id):
        raise HTTPException(status_code=409, detail="servizio non generabile via 8e")
    try:
        return await engine.get_form(servizio_id)
    except engine.EngineError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/engine/health")
async def engine_health():
    return await engine.health()


@router.get("/boost-catalog")
def boost_catalog():
    """Elenco dei servizi generabili via 8e (per il selettore nel pannello: se il
    routing automatico sbaglia, l'utente sceglie il documento giusto)."""
    items = []
    for s in catalog.lista_servizi():
        sid = s.get("id")
        if sid and catalog.is_8e_generabile(sid):
            items.append({
                "id": sid,
                "label": s.get("label") or sid,
                "ambito": s.get("ambito") or s.get("tipo") or "",
            })
    items.sort(key=lambda x: x["label"])
    return {"servizi": items}
