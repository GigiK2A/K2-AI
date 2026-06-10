"""Compute layer universale — TUTTI i tool deterministici degli MCP di Luca.

Auto-discovery su tutti i package vendorizzati (`backend/vendor/`): per ogni funzione
con firma `(input: BaseModel) -> ...` espone un endpoint. Calcolo puro, niente LLM,
niente corpus normativo. Copre l'intero strato di calcolo dell'ecosistema:
agevolazioni, quant (finanza), elettrico (CEI 64-8), strutturale (NTC 2018),
norme-tecniche.

Questi tool sono i "mattoni" dietro i Boost/Check: il kbot può chiamarli direttamente
(check express) o comporli (deliverable). Il registry è dinamico: nuovi tool che Luca
aggiunge compaiono senza modifiche al codice.
"""
from __future__ import annotations

import inspect
import pkgutil
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..lib.auth import AuthUser, require_user
from ..lib.limiter import limiter

_VENDOR = Path(__file__).resolve().parents[2] / "vendor"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

router = APIRouter()

# package vendorizzati → dominio
VENDOR_PACKAGES = {
    "k2a_agevolazioni": "agevolazioni",
    "k2a_quant": "finanza",
    "k2a_elettrico": "elettrico",
    "vs_strutturale": "strutturale",
    "k2a_norme_tecniche": "norme-tecniche",
}


# SICUREZZA: campi-input che indicano scrittura/lettura su filesystem. I tool che
# li espongono (generatori excel/docx/dxf/cad) NON vanno esposti via HTTP: un input
# come output_path="/app/app/main.py" = scrittura file arbitraria sul server.
# L'endpoint compute espone SOLO calcolo puro (in→out strutturato).
_FS_FIELD_HINTS = ("path", "dir", "file", "output", "dest", "folder", "percorso")


def _writes_filesystem(model: type) -> bool:
    try:
        fields = getattr(model, "model_fields", {})
    except Exception:
        return True  # in dubbio → escludi
    for fname in fields:
        fl = fname.lower()
        if any(h in fl for h in _FS_FIELD_HINTS):
            return True
    return False


def _discover() -> dict[str, dict[str, Any]]:
    """Scansiona i package vendorizzati e mappa tool_id → metadati. tool_id =
    '<dominio>/<modulo>.<funzione>'. Solo funzioni con 1 parametro BaseModel di
    CALCOLO PURO: i tool che scrivono file (campo path/output nell'input) sono
    ESCLUSI (rischio scrittura arbitraria)."""
    reg: dict[str, dict[str, Any]] = {}
    excluded = 0
    for pkg_name, dominio in VENDOR_PACKAGES.items():
        try:
            pkg = __import__(pkg_name, fromlist=["x"])
        except Exception:
            continue
        for mi in pkgutil.iter_modules(pkg.__path__):
            if mi.name in ("server", "__main__"):
                continue
            try:
                mod = __import__(f"{pkg_name}.{mi.name}", fromlist=["x"])
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
                    if _writes_filesystem(params[0].annotation):
                        excluded += 1
                        continue  # tool di I/O su file → non esporre
                    tool_id = f"{dominio}/{mi.name}.{fn_name}"
                    reg[tool_id] = {"fn": fn, "input_model": params[0].annotation,
                                    "dominio": dominio, "module": mi.name, "fn_name": fn_name}
    if excluded:
        import logging
        logging.getLogger(__name__).info("compute: esclusi %d tool con I/O su file", excluded)
    return reg


_REGISTRY = _discover()


@router.get("/tools")
@limiter.limit("30/minute")
def list_tools(request: Request, dominio: str | None = None,
               user: AuthUser = Depends(require_user)) -> dict:
    """Catalogo dei tool a calcolo disponibili nell'ecosistema (no LLM/crediti)."""
    from collections import Counter
    items = [
        {"tool_id": tid, "dominio": m["dominio"], "tool": m["fn_name"]}
        for tid, m in sorted(_REGISTRY.items())
        if dominio is None or m["dominio"] == dominio
    ]
    return {"tools": items, "count": len(items),
            "per_dominio": dict(Counter(m["dominio"] for m in _REGISTRY.values())),
            "motore": "MCP ecosistema K2-AI (deterministico, vendorizzato)"}


@router.get("/tool/{tool_id:path}/schema")
@limiter.limit("60/minute")
def tool_schema(request: Request, tool_id: str, user: AuthUser = Depends(require_user)) -> dict:
    m = _REGISTRY.get(tool_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"tool '{tool_id}' inesistente")
    return {"tool_id": tool_id, "input_schema": m["input_model"].model_json_schema()}


class ToolBody(BaseModel):
    inputs: dict[str, Any]


@router.post("/tool/{tool_id:path}")
@limiter.limit("20/minute")
def run_tool(request: Request, tool_id: str, body: ToolBody,
             user: AuthUser = Depends(require_user)) -> dict:
    """Esegue un tool a calcolo deterministico dell'ecosistema."""
    m = _REGISTRY.get(tool_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"tool '{tool_id}' inesistente")
    try:
        inp = m["input_model"](**body.inputs)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"input non valido: {exc}")
    try:
        out = m["fn"](inp)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"calcolo fallito: {exc}")
    result = out.model_dump(mode="json") if isinstance(out, BaseModel) else out
    return {"tool_id": tool_id, "dominio": m["dominio"], "deterministico": True, "result": result}
