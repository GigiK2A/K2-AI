"""Gestione dei fascicoli da parte dell'utente (elenco, apertura, correzione e cancellazione di voci/fascicoli).

Il modello può solo leggere e salvare con conferma (lib/fascicoli); correggere o eliminare è azione dell'utente, qui. JWT obbligatorio:
ogni operazione è filtrata per user_id nel codice, un id altrui risponde 404.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from ..lib import fascicoli
from ..lib.auth import AuthUser, require_user

router = APIRouter()


class VocePatch(BaseModel):
    model_config = ConfigDict(extra="ignore")
    testo: Optional[str] = None
    valore: Optional[str] = None
    verifica: Optional[str] = None


@router.get("/fascicoli")
def elenco(user: AuthUser = Depends(require_user)):
    return {"fascicoli": [{k: f.get(k) for k in ("id", "tipo", "codice", "titolo", "stato", "updated_at")} for f in fascicoli.elenco(user.id)]}


@router.get("/fascicoli/{fid}")
def apri(fid: str, user: AuthUser = Depends(require_user)):
    f = fascicoli.trova(user.id, fid)
    if not f:
        raise HTTPException(status_code=404, detail="fascicolo non trovato")
    return {"fascicolo": {k: f.get(k) for k in ("id", "tipo", "codice", "titolo", "stato", "updated_at")},
            "voci": fascicoli.voci(user.id, str(f["id"])),
            "documenti": [{k: d.get(k) for k in ("id", "name", "type", "size")} for d in fascicoli.documenti(user.id, str(f["id"]))]}


@router.patch("/fascicoli/{fid}/voci/{vid}")
def correggi(fid: str, vid: str, body: VocePatch, user: AuthUser = Depends(require_user)):
    if not fascicoli.correggi_voce(user.id, fid, vid, body.model_dump(exclude_none=True)):
        raise HTTPException(status_code=404, detail="voce non trovata")
    return {"ok": True}


@router.delete("/fascicoli/{fid}/voci/{vid}")
def elimina_voce(fid: str, vid: str, user: AuthUser = Depends(require_user)):
    if not fascicoli.elimina_voce(user.id, fid, vid):
        raise HTTPException(status_code=404, detail="voce non trovata")
    return {"ok": True}


@router.delete("/fascicoli/{fid}")
def elimina(fid: str, user: AuthUser = Depends(require_user)):
    if not fascicoli.elimina_fascicolo(user.id, fid):
        raise HTTPException(status_code=404, detail="fascicolo non trovato")
    return {"ok": True}
