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

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

# vendor/ in path per importare il package compute di Luca senza installarlo
_VENDOR = Path(__file__).resolve().parents[2] / "vendor"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

router = APIRouter()

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
def list_checks() -> dict:
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
def run_check(service_id: str, body: CheckBody) -> dict:
    """Esegue un check express deterministico. Valida gli input contro il modello
    Pydantic del tool, calcola, ritorna l'output strutturato. Nessun LLM."""
    meta = _REGISTRY.get(service_id)
    if not meta:
        raise HTTPException(status_code=404,
                            detail=f"check '{service_id}' non disponibile (calcolo). "
                                   f"Disponibili: {sorted(_REGISTRY)}")
    try:
        inp = meta["input_model"](**body.inputs)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"input non valido: {exc}")
    try:
        out = meta["fn"](inp)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"calcolo fallito: {exc}")
    result = out.model_dump(mode="json") if isinstance(out, BaseModel) else out
    return {"service_id": service_id, "strato": "consumo", "deterministico": True,
            "result": result}


@router.post("/check/{service_id}/document")
def run_check_document(service_id: str, body: CheckBody) -> Response:
    """Esegue il check e ritorna il PDF deliverable D1 (deterministico, no LLM)."""
    meta = _REGISTRY.get(service_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"check '{service_id}' non disponibile")
    try:
        inp = meta["input_model"](**body.inputs)
        out = meta["fn"](inp)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"calcolo/input non valido: {exc}")
    result = out.model_dump(mode="json") if isinstance(out, BaseModel) else out
    from ..lib.check_renderer import render_check_pdf
    label = service_id.replace("_", " ").title()
    pdf = render_check_pdf(service_id, label, body.inputs, result)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{service_id}.pdf"'})
