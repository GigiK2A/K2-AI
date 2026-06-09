"""Lookup clausole normative CEI / DPR."""
from __future__ import annotations
import json
from pathlib import Path
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "clausole_cei.json").read_text())


class LookupCeiInput(BaseModel):
    chiave: str = Field(...)


class ListClausoleInput(BaseModel):
    pass


def lookup_cei(inp: LookupCeiInput) -> dict:
    k = inp.chiave.strip()
    if k not in _DATA:
        return {"error": f"Chiave '{k}' non trovata.", "available": sorted(_DATA.keys())}
    return {"chiave": k, **_DATA[k]}


def list_clausole(_: ListClausoleInput) -> dict:
    return {"clausole_disponibili": sorted(_DATA.keys()), "totale": len(_DATA)}
