"""Tool `get_antenna` — DB seed antenne TLC."""

from __future__ import annotations

import hashlib
import json

from pydantic import BaseModel, Field

from .data.antenne_db import cerca_antenna, lista_antenne
from .schemas import CalcResult, TraceStep


class GetAntennaInput(BaseModel):
    modello: str = Field(..., description="Designazione antenna, es. 'Kathrein 80010622'")


class GetAntennaOutput(CalcResult):
    trovato: bool = False
    famiglia: str | None = None
    altezza_mm: float | None = None
    larghezza_mm: float | None = None
    profondita_mm: float | None = None
    area_frontale_m2: float | None = None
    C_d: float | None = None
    peso_kg: float | None = None
    bande: list[str] | None = None
    suggerimenti: list[str] = []


def lookup_antenna(inp: GetAntennaInput) -> GetAntennaOutput:
    h = hashlib.sha256(json.dumps(inp.model_dump(), sort_keys=True).encode()).hexdigest()[:16]
    out = GetAntennaOutput(tool="get_antenna", inputs_hash=h)

    d = cerca_antenna(inp.modello)
    if d is None:
        out.trovato = False
        out.warnings.append(f"Modello '{inp.modello}' non in DB seed.")
        out.suggerimenti = lista_antenne()
        out.out_of_scope = True
        out.out_of_scope_reason = (
            "DB antenne seed contiene ~13 modelli più comuni. Per modelli mancanti, "
            "fornire datasheet (h × w × d, area frontale, C_d, peso) come input manuale al solver."
        )
        return out

    out.trovato = True
    out.famiglia = d["famiglia"]
    out.altezza_mm = d["altezza_mm"]
    out.larghezza_mm = d["larghezza_mm"]
    out.profondita_mm = d["profondita_mm"]
    out.area_frontale_m2 = d["area_frontale_m2"]
    out.C_d = d["C_d"]
    out.peso_kg = d["peso_kg"]
    out.bande = d["bande"]
    out.primary_value = d["area_frontale_m2"]
    out.primary_unit = "m²"

    out.trace.append(TraceStep(
        label="antenna",
        formula="lookup(modello)",
        substitution=(
            f"{inp.modello}: A_ref={d['area_frontale_m2']:.3f} m², C_d={d['C_d']}, "
            f"peso={d['peso_kg']} kg ({d['famiglia']})"
        ),
        value=d["area_frontale_m2"], unit="m²",
        norm_ref="Datasheet costruttore + DB seed K2A v0.1",
    ))
    return out
