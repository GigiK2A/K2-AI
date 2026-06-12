"""GET /api/kbot/billing/me — stato billing dell'utente (piano + saldo crediti).
POST /api/kbot/billing/consume — consuma crediti per un Check express (strato Consumo).

Read-side per il frontend (badge crediti, gating piani). La scrittura crediti
avviene via webhook (acquisti) o qui per il consumo di un check.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..lib import billing, billing_store, catalog
from ..lib.auth import AuthUser, require_user

router = APIRouter()


@router.get("/billing/me")
def billing_me(user: AuthUser = Depends(require_user)):
    plan = billing_store.get_plan(user.id)
    p = billing.piano(plan)
    return {
        "plan": plan,
        "label": p["label"],
        "crediti": billing_store.credit_balance(user.id),
        "crediti_mese": p["crediti_mese"],
        "sconto_boost_pct": p["sconto_boost_pct"],
        "servizi_eseguibili": p["servizi_eseguibili"],
        "modello": billing.load_model(catalog.load_catalog()),
    }


class ConsumeBody(BaseModel):
    servizio_id: str


@router.post("/billing/consume")
def billing_consume(body: ConsumeBody, user: AuthUser = Depends(require_user)):
    """Consuma i crediti per un servizio di strato Consumo (Check express).
    I Boost NON passano da qui (si pagano a prezzo). 402 se crediti insufficienti."""
    servizio = catalog.get_servizio(body.servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="servizio non a catalogo")
    if not billing.puo_eseguire_servizi(billing_store.get_plan(user.id)):
        raise HTTPException(status_code=403, detail="piano Free: i servizi non sono eseguibili")
    costo = billing.costo_crediti(servizio)
    if costo is None:
        raise HTTPException(status_code=409, detail="questo servizio non si paga a crediti (è un Boost a prezzo)")
    ok, saldo = billing_store.consume_credits(user.id, costo, reason="consume", ref=body.servizio_id)
    if not ok:
        raise HTTPException(status_code=402, detail={"error": "insufficient_credits",
                                                     "saldo": saldo, "costo": costo})
    return {"ok": True, "saldo": saldo, "costo": costo, "servizio_id": body.servizio_id}
