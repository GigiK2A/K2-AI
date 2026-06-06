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

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..lib import engine, sessions, catalog
from ..lib.auth import AuthUser, optional_user

router = APIRouter()
log = logging.getLogger(__name__)


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


def _mint_entitlement(session: dict, servizio_id: str) -> Optional[str]:
    """Phase-1: entitlement placeholder se il servizio risulta pagato.

    TODO (G1): sostituire con JWT firmato {sub,service_id,tier,jti,exp} verificato
    stateless dall'8e. Vedi docs/interfaccia-kbot-8e.md §9.
    """
    if session.get("status") == "paid":
        return f"phase1-{session.get('id')}-{servizio_id}"
    return None


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

    entitlement = _mint_entitlement(session, body.servizioId)
    if not entitlement:
        raise HTTPException(status_code=402, detail="servizio non pagato")

    # L'8e instrada per service_id (chiave manifest = id catalog, stessa fonte
    # k2a-catalogo); è l'8e a risolvere service_id→blueprint internamente.
    try:
        res = await engine.create_deliverable(
            service_id=body.servizioId,
            inputs=body.inputs,
            entitlement_token=entitlement,
            tier=servizio.get("tipo"),
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


@router.get("/deliverables/{job_id}")
async def status(job_id: str):
    try:
        return await engine.get_deliverable(job_id)
    except engine.EngineError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/engine/health")
async def engine_health():
    return await engine.health()
