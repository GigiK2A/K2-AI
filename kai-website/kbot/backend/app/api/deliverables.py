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

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..lib import engine, sessions, catalog, entitlement
from ..lib.auth import AuthUser, optional_user, require_user
from ..lib.supabase_admin import get_admin_client

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
    if session.get("status") != "paid":
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

    # Persisti il job sulla sessione per il polling successivo.
    sessions.update_session(body.sessionId, {"deliverable_job_id": res.get("job_id"),
                                             "deliverable_service": body.servizioId})
    return res


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
