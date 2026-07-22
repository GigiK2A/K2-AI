"""GET/PUT dati azienda dell'account (ragione sociale, P.IVA, ATECO, forma giuridica,
settore, dipendenti, fatturato, sede). Impostati una volta in dashboard / al signup e presi
dall'account: non vanno reinseriti in ogni chat (il prompt li inietta via profilo).

Store: kbot_client_memory.profile.anagrafica (vedi lib/profile.py). JWT Supabase richiesto.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from ..lib import profile as profile_lib
from ..lib.auth import AuthUser, require_user

router = APIRouter()
log = logging.getLogger(__name__)


class CompanyProfile(BaseModel):
    # tutti opzionali: l'utente compila ciò che vuole; vuoto = rimuove il campo
    model_config = ConfigDict(extra="ignore")
    ragione_sociale: Optional[str] = None
    partita_iva: Optional[str] = None
    codice_ateco: Optional[str] = None
    forma_giuridica: Optional[str] = None
    settore: Optional[str] = None
    dipendenti: Optional[str] = None
    fatturato: Optional[str] = None
    citta: Optional[str] = None


@router.get("/profile")
def get_profile(user: AuthUser = Depends(require_user)) -> dict:
    """Dati azienda salvati sull'account. Al primo accesso li inizializza dai metadati del
    signup (nome azienda/settore) → il nuovo utente trova già qualcosa di precompilato."""
    try:
        ana = profile_lib.load_anagrafica(user.id)
        if not ana:
            ana = profile_lib.seed_from_metadata(user.id, (user.raw or {}).get("user_metadata"))
        return {"profile": ana}
    except Exception:
        log.warning("profile GET fallita (fail-open → vuoto)", exc_info=True)
        return {"profile": {}}


@router.put("/profile")
def put_profile(body: CompanyProfile, user: AuthUser = Depends(require_user)) -> dict:
    """Salva/aggiorna i dati azienda dell'account. Campo vuoto → rimosso."""
    try:
        saved = profile_lib.save_anagrafica(user.id, body.model_dump(exclude_unset=True))
        return {"profile": saved}
    except Exception:
        log.exception("profile PUT fallita")
        raise HTTPException(status_code=502, detail="salvataggio profilo non riuscito, riprova")
