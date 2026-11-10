"""Gestione dei fascicoli da parte dell'utente (elenco, apertura, correzione e cancellazione di voci/fascicoli).

Il modello può solo leggere e salvare con conferma (lib/fascicoli); correggere o eliminare è azione dell'utente, qui. JWT obbligatorio:
ogni operazione è filtrata per user_id nel codice, un id altrui risponde 404.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from ..lib import fascicoli
from ..lib import fascicoli_versioni as V
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


class Consolida(BaseModel):
    model_config = ConfigDict(extra="ignore")
    riferimenti: Optional[list[str]] = None


@router.get("/fascicoli/{fid}/storico")
def storico(fid: str, record: str = "", alla_data: str = "", user: AuthUser = Depends(require_user)):
    f = fascicoli.trova(user.id, fid)
    if not f:
        raise HTTPException(status_code=404, detail="fascicolo non trovato")
    return {"storico": V.storico(user.id, str(f["id"]), record, alla_data)}


@router.get("/fascicoli/{fid}/duplicati")
def duplicati(fid: str, user: AuthUser = Depends(require_user)):
    f = fascicoli.trova(user.id, fid)
    if not f:
        raise HTTPException(status_code=404, detail="fascicolo non trovato")
    gr = V.duplicati(user.id, str(f["id"]))
    return {"gruppi": [{k: g[k] for k in ("riferimento", "duplicati", "fonti", "differenze")} for g in gr], "descrizione": V.descrivi_duplicati(gr)}


@router.post("/fascicoli/{fid}/consolida")
def consolida(fid: str, body: Consolida, user: AuthUser = Depends(require_user)):
    """Archivia i duplicati (non li cancella). L'azione è dell'utente: non passa dal modello."""
    f = fascicoli.trova(user.id, fid)
    if not f:
        raise HTTPException(status_code=404, detail="fascicolo non trovato")
    ctx = fascicoli.Contesto(user_id=user.id)
    return V.consolida(ctx, str(f["id"]), body.riferimenti, "utente")


@router.post("/fascicoli/eventi/{eid}/annulla")
def annulla(eid: str, user: AuthUser = Depends(require_user)):
    if not V.annulla_consolidamento(user.id, eid):
        raise HTTPException(status_code=404, detail="evento non trovato")
    return {"ok": True}


@router.get("/fascicoli/{fid}/documents/{doc_id}/view")
def vista(fid: str, doc_id: str, pag: int = 1, quote: str = "", zoom: float = 1.4, user: AuthUser = Depends(require_user)):
    """Apre nel visualizzatore un documento conservato nel fascicolo (stesso codice delle citazioni in chat)."""
    from .upload import vista_documento

    f = fascicoli.trova(user.id, fid)
    d = fascicoli.trova_documento(user.id, str(f["id"]), doc_id) if f else None
    if not d:
        raise HTTPException(status_code=404, detail="documento non trovato")
    return vista_documento(d, pag, quote, zoom)
