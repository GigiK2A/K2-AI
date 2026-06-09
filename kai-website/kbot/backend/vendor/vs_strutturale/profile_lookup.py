"""Tool `get_profile` — recupera caratteristiche profilo strutturale.

Supporta:
  - Sezioni tubolari circolari cave commerciali EN 10210/10219
  - Sezioni tubolari da geometria libera (D, t)
  - Sezioni poligonali (D_inscritto, t, n_lati) tipiche pali TLC
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash

from typing import Literal

from pydantic import BaseModel, Field

from .data.profili_chs import (
    TAGLIE_CHS_COMMERCIALI,
    chs_proprieta,
    lookup_chs_commerciale,
    palo_poligonale_proprieta,
)
from .schemas import CalcResult, TraceStep


class GetProfileInput(BaseModel):
    tipo: Literal["commerciale", "tubolare_libero", "poligonale"]
    designazione: str | None = Field(None, description="Per tipo=commerciale, es. 'CHS 273.0x10'")
    D_ext_mm: float | None = Field(None, description="Per tubolare libero")
    D_inscritto_mm: float | None = Field(None, description="Per poligonale (apotema)")
    t_mm: float | None = None
    n_lati: int | None = Field(None, description="Per poligonale (8, 12, 16, 18, 24)")
    fy_MPa: float = Field(275.0, description="Tensione snervamento per classificazione")


class GetProfileOutput(CalcResult):
    designazione: str = ""
    D_ext_mm: float | None = None
    t_mm: float | None = None
    A_mm2: float | None = None
    I_mm4: float | None = None
    W_el_mm3: float | None = None
    W_pl_mm3: float | None = None
    i_mm: float | None = None
    peso_kg_m: float | None = None
    classe_sezione: int | None = None


def lookup_profile(inp: GetProfileInput) -> GetProfileOutput:
    out = GetProfileOutput(tool="get_profile", inputs_hash=compute_inputs_hash(inp))

    if inp.tipo == "commerciale":
        if not inp.designazione:
            raise ValueError("Per tipo=commerciale, fornire 'designazione'")
        sez = lookup_chs_commerciale(inp.designazione)
        norm = "EN 10210-2 / EN 10219-2 — sagomario tubolari cavi"
    elif inp.tipo == "tubolare_libero":
        if not (inp.D_ext_mm and inp.t_mm):
            raise ValueError("Per tubolare_libero, fornire D_ext_mm e t_mm")
        sez = chs_proprieta(inp.D_ext_mm, inp.t_mm)
        norm = "Anello circolare cavo — formule analitiche"
    elif inp.tipo == "poligonale":
        if not (inp.D_inscritto_mm and inp.t_mm and inp.n_lati):
            raise ValueError("Per poligonale: D_inscritto_mm, t_mm, n_lati")
        sez = palo_poligonale_proprieta(inp.D_inscritto_mm, inp.t_mm, inp.n_lati)
        norm = "Poligono regolare → equivalente circolare (n≥8)"
    else:
        raise ValueError(f"Tipo sconosciuto: {inp.tipo}")

    classe = sez.classe_sezione(inp.fy_MPa)

    out.designazione = sez.designazione
    out.D_ext_mm, out.t_mm = sez.D_ext_mm, sez.t_mm
    out.A_mm2, out.I_mm4 = sez.A_mm2, sez.I_mm4
    out.W_el_mm3, out.W_pl_mm3 = sez.W_el_mm3, sez.W_pl_mm3
    out.i_mm, out.peso_kg_m = sez.i_mm, sez.peso_kg_m
    out.classe_sezione = classe

    out.trace.append(TraceStep(
        label="proprietà geometriche",
        formula="A=π/4·(D²−d²); I=π/64·(D⁴−d⁴); W_el=I/(D/2); W_pl=(D³−d³)/6",
        substitution=(
            f"{sez.designazione}: A={sez.A_mm2:.1f} mm², I={sez.I_mm4:.2e} mm⁴, "
            f"W_el={sez.W_el_mm3:.1f} mm³, W_pl={sez.W_pl_mm3:.1f} mm³, "
            f"i={sez.i_mm:.2f} mm, peso={sez.peso_kg_m:.2f} kg/m"
        ),
        value=sez.A_mm2, unit="mm²", norm_ref=norm,
    ))
    out.trace.append(TraceStep(
        label="classe sezione",
        formula="d/t vs limiti EN 1993-1-1 Tab. 5.2: C1≤50ε², C2≤70ε², C3≤90ε²",
        substitution=f"d/t = {sez.D_ext_mm/sez.t_mm:.1f}, fy={inp.fy_MPa} → classe {classe}",
        value=classe, unit="-", norm_ref="EN 1993-1-1 §5.5 + Tab. 5.2",
    ))

    out.primary_value = sez.A_mm2
    out.primary_unit = "mm²"
    return out


def list_taglie_commerciali() -> list[str]:
    return list(TAGLIE_CHS_COMMERCIALI.keys())
