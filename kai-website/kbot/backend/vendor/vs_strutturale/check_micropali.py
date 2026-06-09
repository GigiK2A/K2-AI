"""Verifica micropalo singolo e gruppo — FHWA NHI-05-039 + UNI EN 14199.

Resistenza geotecnica (bond grout-terreno nella zona bulbo):
    R_bond = π · D_perforazione · L_bulbo · α_bond
  α_bond = resistenza di aderenza grout-terreno (kPa), funzione di terreno + tipo iniezione
  FHWA (A: gravità, B: iniezione globale pressione, C: iniezione ripetuta IGU, D: IRS ripetuta).
  Compressione e trazione governate dal bond (punta trascurata per micropali — cautelativo).

Resistenza strutturale (armatura): N_steel = A_acciaio · f_yk / γ_s (barra o tubolare).

R_c,d = min(R_bond/γ_geo , N_steel).  Gruppo: R_group = η · n · R_singolo.

Anchor K2A: **nessun foglio K2A dedicato ai micropali** (i fogli 31/32 sono nodi flangia/montanti
di rinforzo, non bond di micropali). Il tool usa quindi il metodo FHWA standard; nessun trigger
di divergenza K2A↔FHWA (non esiste un metodo K2A da confrontare). Vedi decision log.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep

# Resistenza di aderenza grout-terreno α_bond [kPa] — valori rappresentativi (midpoint dei range
# FHWA NHI-05-039) per (terreno, tipo iniezione A/B/C/D). Override con valore da prova/scheda.
BOND_FHWA = {
    "argilla": {"A": 45.0, "B": 95.0, "C": 110.0, "D": 130.0},
    "sabbia":  {"A": 130.0, "B": 190.0, "C": 230.0, "D": 300.0},
    "ghiaia":  {"A": 200.0, "B": 280.0, "C": 340.0, "D": 420.0},
    "roccia":  {"A": 350.0, "B": 500.0, "C": 600.0, "D": 700.0},
}


class CheckMicropaliInput(BaseModel):
    D_perforazione_mm: float = Field(..., gt=0, description="Diametro perforazione/bulbo")
    L_bulbo_m: float = Field(..., gt=0, description="Lunghezza zona bulbo (bond length)")
    soil_type: Literal["argilla", "sabbia", "ghiaia", "roccia"] = "sabbia"
    fhwa_type: Literal["A", "B", "C", "D"] = "A"
    alpha_bond_kPa: float | None = Field(None, gt=0, description="Override α_bond (da prova/ETA)")
    A_acciaio_mm2: float = Field(..., gt=0, description="Area armatura (barra o tubolare)")
    f_yk_MPa: float = Field(450.0, gt=0, description="Snervamento acciaio armatura")
    gamma_s: float = Field(1.15, gt=0, description="Coeff. parziale acciaio")
    gamma_geo: float = Field(1.35, gt=0, description="Coeff. parziale resistenza geotecnica EN 1997")
    loading: Literal["compressione", "trazione"] = "compressione"
    N_Ed_kN: float = Field(0.0, ge=0, description="Carico assiale di progetto")
    n_micropali: int = Field(1, ge=1, description="Numero micropali nel gruppo")
    group_efficiency: float = Field(1.0, gt=0, le=1.0, description="Efficienza gruppo η")


class CheckMicropaliOutput(CalcResult):
    alpha_bond_used_kPa: float | None = None
    R_bond_kN: float | None = None
    R_bond_d_kN: float | None = None
    N_steel_Rd_kN: float | None = None
    R_single_d_kN: float | None = None
    R_group_d_kN: float | None = None
    governing: str = ""
    eta: float | None = None
    verifica_ok: bool = False


def check_micropali(inp: CheckMicropaliInput) -> CheckMicropaliOutput:
    out = CheckMicropaliOutput(tool="check_micropali", inputs_hash=compute_inputs_hash(inp))

    D = inp.D_perforazione_mm / 1000.0
    L = inp.L_bulbo_m
    alpha = inp.alpha_bond_kPa if inp.alpha_bond_kPa else BOND_FHWA[inp.soil_type][inp.fhwa_type]
    out.alpha_bond_used_kPa = alpha

    # Resistenza geotecnica (bond)
    R_bond = math.pi * D * L * alpha   # kN (D[m]·L[m]·kPa = kN)
    out.R_bond_kN = R_bond
    out.R_bond_d_kN = R_bond / inp.gamma_geo

    # Resistenza strutturale armatura
    N_steel = inp.A_acciaio_mm2 * inp.f_yk_MPa / inp.gamma_s / 1000.0  # kN
    out.N_steel_Rd_kN = N_steel

    R_single = min(out.R_bond_d_kN, N_steel)
    out.R_single_d_kN = R_single
    out.governing = "bond grout-terreno" if out.R_bond_d_kN <= N_steel else "armatura acciaio"

    out.R_group_d_kN = inp.group_efficiency * inp.n_micropali * R_single

    out.trace.append(TraceStep(
        label="bond grout-terreno",
        formula="R_bond = π·D·L·α_bond ; R_bond,d = R_bond/γ_geo",
        substitution=(
            f"D={D:.3f}m, L={L}m, α={alpha:.0f} kPa ({inp.soil_type}/{inp.fhwa_type}) → "
            f"R_bond={R_bond:.1f} kN, R_bond,d={out.R_bond_d_kN:.1f} kN"
        ),
        value=out.R_bond_d_kN, unit="kN", norm_ref="FHWA NHI-05-039 + UNI EN 14199",
    ))
    out.trace.append(TraceStep(
        label="armatura + R singolo",
        formula="N_steel = A·f_yk/γ_s ; R_single,d = min(R_bond,d, N_steel)",
        substitution=f"N_steel={N_steel:.1f} kN → R_single,d={R_single:.1f} kN (governa: {out.governing})",
        value=R_single, unit="kN", norm_ref="EN 1993-1-1 + EN 1997",
    ))
    out.trace.append(TraceStep(
        label="R gruppo",
        formula="R_group,d = η·n·R_single,d",
        substitution=f"= {inp.group_efficiency}·{inp.n_micropali}·{R_single:.1f} = {out.R_group_d_kN:.1f} kN",
        value=out.R_group_d_kN, unit="kN", norm_ref="EN 1997 §7.6.2.2 (gruppo)",
    ))

    if inp.N_Ed_kN > 0:
        out.eta = inp.N_Ed_kN / out.R_group_d_kN if out.R_group_d_kN > 0 else float("inf")
        out.verifica_ok = out.eta <= 1.0

    # Sanity rules (§12.13)
    if L < 3.0:
        out.warnings.append(
            f"Lunghezza bulbo L={L} m < 3 m: zona di bond ridotta, verificare minimo normativo "
            "(UNI EN 14199 raccomanda L_bulbo ≥ 3 m tipico)."
        )
    if inp.alpha_bond_kPa and not (20.0 <= inp.alpha_bond_kPa <= 1000.0):
        out.warnings.append(
            f"α_bond override={inp.alpha_bond_kPa} kPa fuori range FHWA tipico [20,1000]: verificare prova."
        )
    if inp.loading == "trazione":
        out.warnings.append(
            "Trazione: nessun contributo di punta (corretto per micropali); verificare anche "
            "ancoraggio armatura e fessurazione grout."
        )
    if out.governing == "armatura acciaio":
        out.warnings.append(
            "Governa l'armatura (acciaio): aumentare A_acciaio o ridurre carico; il bond geotecnico "
            "ha margine."
        )

    out.primary_value = out.R_group_d_kN
    out.primary_unit = "kN"
    return out
