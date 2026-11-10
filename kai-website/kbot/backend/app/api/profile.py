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


@router.get("/profile/memoria")
def get_memoria(user: AuthUser = Depends(require_user)) -> dict:
    """Cosa il K-BOT ha APPRESO dalle conversazioni (non verificato), con conversazione e data di origine: l'utente può
    vederlo e correggerlo. I dati confermati dell'account (PUT /profile) non compaiono qui."""
    try:
        return {"voci": profile_lib.memoria_appresa(user.id)}
    except Exception:
        log.warning("memoria GET fallita (fail-open → vuoto)", exc_info=True)
        return {"voci": []}


@router.delete("/profile/memoria")
def delete_memoria(user: AuthUser = Depends(require_user)) -> dict:
    """Il K-BOT dimentica tutto ciò che ha appreso dalle conversazioni (i dati confermati dell'account restano)."""
    try:
        profile_lib.dimentica(user.id)
        return {"ok": True}
    except Exception:
        log.exception("memoria DELETE fallita")
        raise HTTPException(status_code=502, detail="cancellazione non riuscita, riprova")


@router.delete("/profile/memoria/{chiave}")
def delete_memoria_voce(chiave: str, user: AuthUser = Depends(require_user)) -> dict:
    """Corregge la memoria: dimentica una singola voce appresa."""
    try:
        return {"rimosse": profile_lib.dimentica(user.id, chiave)}
    except Exception:
        log.exception("memoria DELETE voce fallita")
        raise HTTPException(status_code=502, detail="cancellazione non riuscita, riprova")
