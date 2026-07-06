"""Check express (strato Consumo, D1) — calcolo DETERMINISTICO via MCP k2a-agevolazioni.

Questi servizi NON usano LLM né corpus normativo: sono calcoli puri (Pydantic in→out)
prodotti dai moduli vendorizzati in `vendor/k2a_agevolazioni`. Coprono i servizi
"consumo" del catalogo (de_minimis, sabatini, KPI settoriali, ecc.) — pagati a crediti.

Il registry è AUTO-DISCOVERED per introspezione: se Luca aggiunge un tool al package,
compare qui senza modifiche al codice. Mapping service_id (catalogo) → modulo tool.
"""
from __future__ import annotations

import inspect
import pkgutil
import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from ..lib.auth import AuthUser, require_user
from ..lib.limiter import limiter
from ..lib import billing, billing_store
from .compute import run_tool_safely

# vendor/ in path per importare il package compute di Luca senza installarlo
_VENDOR = Path(__file__).resolve().parents[2] / "vendor"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

router = APIRouter()

# Costo crediti dei Check (strato Consumo): dalla fonte di verità catalogo_documenti.json
# vendorizzata (la catalog.json generata l'ha persa). Cache a primo uso.
import json as _json
_SRC_CATALOG = _VENDOR / "k2a_agevolazioni" / "data" / "catalogo_documenti.json"
_COSTI: dict[str, int] = {}


def _load_costi() -> dict[str, int]:
    if _COSTI:
        return _COSTI
    try:
        tipi = _json.loads(_SRC_CATALOG.read_text(encoding="utf-8")).get("tipi", {})
        for sid, t in tipi.items():
            if t.get("strato") == "consumo" and t.get("costo_crediti") is not None:
                _COSTI[sid] = int(t["costo_crediti"])
    except Exception:
        pass
    return _COSTI


def _consuma_crediti(service_id: str, user: AuthUser) -> int:
    """Gate crediti server-side: piano abilitato + saldo sufficiente. 402/403 se no.
    Ritorna il saldo residuo. Idempotenza/no-doppio-addebito è responsabilità del flusso
    frontend (una chiamata per acquisto)."""
    if not billing.puo_eseguire_servizi(billing_store.get_plan(user.id)):
        raise HTTPException(status_code=403,
                            detail="piano Free: i servizi non sono eseguibili. Passa a Pro.")
    costo = _load_costi().get(service_id)
    if not costo:  # servizio non a crediti o costo ignoto → non eseguire a vuoto
        raise HTTPException(status_code=409,
                            detail=f"costo crediti non determinato per '{service_id}'")
    ok, saldo = billing_store.consume_credits(user.id, costo, reason="check", ref=service_id)
    if not ok:
        raise HTTPException(status_code=402,
                            detail={"error": "insufficient_credits", "saldo": saldo, "costo": costo})
    return saldo


def _refund_crediti(user: AuthUser, costo: int, service_id: str) -> None:
    """Ri-accredita i crediti di un check fallito DOPO l'addebito (tool 500/504): il
    cliente non deve pagare per un output che non riceve. Best-effort: un errore di
    rimborso non deve mascherare l'eccezione originale che stiamo per ri-sollevare."""
    if costo <= 0:
        return
    try:
        billing_store.grant_credits(user.id, costo, reason="refund", ref=service_id)
    except Exception:  # pragma: no cover - il refund non deve nascondere l'errore reale
        pass

# service_id del catalogo (strato consumo) → nome modulo nel package agevolazioni
SERVICE_TO_MODULE = {
    "de_minimis": "de_minimis",
    "nuova_sabatini": "nuova_sabatini",
    "credito_rd": "credito_rd",
    "cumulabilita": "cumulabilita",
    "bancabilita": "bancabilita",
    "riclassifica": "riclassifica",
    "crisi": "crisi_cndcec",
    "transizione_5_0": "transizione_5_0",
    "hospitality_kpi": "hospitality",
    "ristorazione_kpi": "ristorazione",
    "retail_kpi": "retail",
    "ecommerce_kpi": "ecommerce",
    "benessere_kpi": "benessere",
    "seo_onpage": "seo",
    "marketing_metriche": "marketing",
}


def _build_registry() -> dict[str, dict[str, Any]]:
    """Introspeziona i moduli del package: per ognuno trova la funzione-tool
    (1 parametro BaseModel) e il suo input-model. Robusto a `from __future__`."""
    reg: dict[str, dict[str, Any]] = {}
    try:
        import k2a_agevolazioni as pkg
    except Exception:
        return reg
    mod_names = {m.name for m in pkgutil.iter_modules(pkg.__path__)}
    for service_id, modname in SERVICE_TO_MODULE.items():
        if modname not in mod_names:
            continue
        try:
            mod = __import__(f"k2a_agevolazioni.{modname}", fromlist=["x"])
        except Exception:
            continue
        for fn_name, fn in inspect.getmembers(mod, inspect.isfunction):
            if fn.__module__ != mod.__name__ or fn_name.startswith("_"):
                continue
            try:
                sig = inspect.signature(fn, eval_str=True)
            except Exception:
                continue
            params = list(sig.parameters.values())
            if (len(params) == 1 and inspect.isclass(params[0].annotation)
                    and issubclass(params[0].annotation, BaseModel)):
                reg[service_id] = {"fn": fn, "input_model": params[0].annotation,
                                   "fn_name": fn_name, "module": modname}
                break
    return reg


_REGISTRY = _build_registry()


@router.get("/checks")
@limiter.limit("30/minute")
def list_checks(request: Request, user: AuthUser = Depends(require_user)) -> dict:
    """Elenco dei check express disponibili (calcolo locale, no LLM/crediti AI)."""
    return {
        "checks": [
            {"service_id": sid, "tool": meta["fn_name"], "module": meta["module"],
             "input_schema": meta["input_model"].model_json_schema()}
            for sid, meta in sorted(_REGISTRY.items())
        ],
        "count": len(_REGISTRY),
        "strato": "consumo",
        "motore": "k2a-agevolazioni (deterministico)",
    }


class CheckBody(BaseModel):
    inputs: dict[str, Any]


@router.post("/check/{service_id}")
@limiter.limit("20/minute")
def run_check(request: Request, service_id: str, body: CheckBody,
              user: AuthUser = Depends(require_user)) -> dict:
    """Esegue un check express deterministico. Valida gli input contro il modello
    Pydantic del tool, calcola, ritorna l'output strutturato. Nessun LLM."""
    meta = _REGISTRY.get(service_id)
    if not meta:
        raise HTTPException(status_code=404,
                            detail=f"check '{service_id}' non disponibile (calcolo). "
                                   f"Disponibili: {sorted(_REGISTRY)}")
    # valida l'input PRIMA di addebitare i crediti
    try:
        inp = meta["input_model"](**body.inputs)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"input non valido: {exc}")
    costo = _load_costi().get(service_id) or 0
    saldo = _consuma_crediti(service_id, user)  # gate crediti server-side (402/403)
    # I crediti sono già addebitati: se il tool solleva (500/504), rimborsa prima di
    # ri-sollevare, altrimenti il cliente paga per un output che non riceve.
    try:
        out = run_tool_safely(meta["fn"], inp)  # timeout + cap concorrenza
    except Exception:
        _refund_crediti(user, costo, service_id)
        raise
    result = out.model_dump(mode="json") if isinstance(out, BaseModel) else out
    return {"service_id": service_id, "strato": "consumo", "deterministico": True,
            "saldo_crediti": saldo, "result": result}


@router.post("/check/{service_id}/document")
@limiter.limit("10/minute")
def run_check_document(request: Request, service_id: str, body: CheckBody,
                       user: AuthUser = Depends(require_user)) -> Response:
    """Esegue il check e ritorna il PDF deliverable D1 (deterministico, no LLM)."""
    meta = _REGISTRY.get(service_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"check '{service_id}' non disponibile")
    try:
        inp = meta["input_model"](**body.inputs)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"input non valido: {exc}")
    costo = _load_costi().get(service_id) or 0
    _consuma_crediti(service_id, user)  # gate crediti server-side (402/403)
    # Rimborsa se il calcolo o il render sollevano dopo l'addebito (no output = no charge).
    try:
        out = run_tool_safely(meta["fn"], inp)  # timeout + cap concorrenza
        result = out.model_dump(mode="json") if isinstance(out, BaseModel) else out
        from ..lib.check_renderer import render_check_pdf
        label = service_id.replace("_", " ").title()
        pdf = render_check_pdf(service_id, label, body.inputs, result)
    except Exception:
        _refund_crediti(user, costo, service_id)
        raise
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{service_id}.pdf"'})
