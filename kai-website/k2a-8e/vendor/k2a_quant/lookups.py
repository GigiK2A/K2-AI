"""Lookup multipli settoriali e dati paese (Damodaran-style snapshot)."""
from __future__ import annotations
import json
from pathlib import Path
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "industry_multiples.json").read_text())


class LookupMultiplesInput(BaseModel):
    sector: str = Field(..., description="Chiave settore. Usa list_sectors per opzioni.")


class LookupCountryInput(BaseModel):
    country: str = Field(..., description="italy | germany | france | spain | us")


def lookup_multiples(inp: LookupMultiplesInput) -> dict:
    s = inp.sector.lower().strip()
    if s not in _DATA["sectors"]:
        return {"error": f"Settore '{s}' non trovato.", "available": list(_DATA["sectors"].keys())}
    return {"sector": s, "metrics": _DATA["sectors"][s], "source": _DATA["_source"]}


def lookup_country(inp: LookupCountryInput) -> dict:
    c = inp.country.lower().strip()
    if c not in _DATA["country_data"]:
        return {"error": f"Paese '{c}' non trovato.", "available": list(_DATA["country_data"].keys())}
    return {"country": c, "data": _DATA["country_data"][c], "source": _DATA["_source"]}


class ListSectorsInput(BaseModel):
    pass


def list_sectors(_: ListSectorsInput) -> dict:
    return {"sectors": list(_DATA["sectors"].keys()), "count": len(_DATA["sectors"])}
