"""Efficienza di gruppo di pali — Converse-Labarre + Feld — EN 1997 / letteratura.

Per effetto di interazione, la capacità di un gruppo di n pali è < n × capacità del singolo:
  R_group = η · n_piles · R_single

Metodi:
- **Converse-Labarre** (reticolo m×n):
    θ = atan(D/s) [°] ;  η = 1 − (θ/90)·[(m−1)·n + (n−1)·m] / (m·n)
- **Feld**: ogni palo riduce la capacità di 1/16 per ciascun palo adiacente (8-conn.);
    η = media sui pali di (1 − n_adiacenti/16).

Anchor K2A: `19_Verifica_fondazione.md` (gruppo pali / plinto su pali).
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep


class CheckPileGroupInput(BaseModel):
    n_rows_m: int = Field(..., ge=1, description="Numero pali per fila (m)")
    n_cols_n: int = Field(..., ge=1, description="Numero file (n)")
    spacing_m: float = Field(..., gt=0, description="Interasse pali s")
    pile_diameter_m: float = Field(..., gt=0, description="Diametro palo D")
    R_single_kN: float = Field(0.0, ge=0, description="Capacità palo singolo (opz., per R_group)")
    method: Literal["converse_labarre", "feld", "both"] = "converse_labarre"


class CheckPileGroupOutput(CalcResult):
    n_piles: int | None = None
    eta_converse_labarre: float | None = None
    eta_feld: float | None = None
    eta: float | None = None
    R_group_kN: float | None = None


def _converse_labarre(m: int, n: int, D: float, s: float) -> float:
    theta = math.degrees(math.atan(D / s))
    if m == 1 and n == 1:
        return 1.0
    eta = 1.0 - (theta / 90.0) * ((m - 1) * n + (n - 1) * m) / (m * n)
    return eta


def _feld(m: int, n: int) -> float:
    # ogni palo perde 1/16 per ciascun palo adiacente (connettività a 8 in griglia)
    tot = 0.0
    for i in range(m):
        for j in range(n):
            adj = 0
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    if di == 0 and dj == 0:
                        continue
                    if 0 <= i + di < m and 0 <= j + dj < n:
                        adj += 1
            tot += 1.0 - adj / 16.0
    return tot / (m * n)


def check_pile_group(inp: CheckPileGroupInput) -> CheckPileGroupOutput:
    out = CheckPileGroupOutput(tool="check_pile_group", inputs_hash=compute_inputs_hash(inp))
    m, n = inp.n_rows_m, inp.n_cols_n
    D, s = inp.pile_diameter_m, inp.spacing_m
    out.n_piles = m * n

    eta_cl = _converse_labarre(m, n, D, s)
    eta_fe = _feld(m, n)
    out.eta_converse_labarre = eta_cl
    out.eta_feld = eta_fe

    if inp.method == "converse_labarre":
        eta = eta_cl
    elif inp.method == "feld":
        eta = eta_fe
    else:  # both → il più cautelativo (minore)
        eta = min(eta_cl, eta_fe)
    out.eta = eta

    out.trace.append(TraceStep(
        label="Converse-Labarre",
        formula="θ=atan(D/s) ; η=1−(θ/90)·[(m−1)n+(n−1)m]/(mn)",
        substitution=f"m={m}, n={n}, D/s={D/s:.3f}, θ={math.degrees(math.atan(D/s)):.2f}° → η_CL={eta_cl:.4f}",
        value=eta_cl, unit="-", norm_ref="Converse-Labarre (gruppo pali)",
    ))
    out.trace.append(TraceStep(
        label="Feld",
        formula="η = media(1 − n_adiacenti/16)",
        substitution=f"m={m}, n={n} → η_Feld={eta_fe:.4f}",
        value=eta_fe, unit="-", norm_ref="Feld (gruppo pali)",
    ))

    if inp.R_single_kN > 0:
        out.R_group_kN = eta * out.n_piles * inp.R_single_kN
        out.trace.append(TraceStep(
            label="R_group",
            formula="R_group = η·n_piles·R_single",
            substitution=f"= {eta:.4f}·{out.n_piles}·{inp.R_single_kN:.1f} = {out.R_group_kN:.1f} kN",
            value=out.R_group_kN, unit="kN", norm_ref="EN 1997 §7.6.2.2 (gruppo)",
        ))

    # Sanity rules (§12.13)
    if not (0.0 < eta <= 1.0):
        out.warnings.append(f"η={eta:.3f} fuori (0,1]: verificare geometria (s troppo piccolo?).")
    if s / D < 3.0:
        out.warnings.append(
            f"Interasse s/D={s/D:.2f} < 3: gruppo fitto, possibile rottura a blocco — "
            "verificare anche capacità del blocco equivalente (EN 1997 §7.6.2.2)."
        )
    if s / D > 8.0:
        out.warnings.append(f"s/D={s/D:.1f} > 8: interazione trascurabile, η≈1 (verificare necessità gruppo).")

    out.primary_value = eta
    out.primary_unit = "-"
    return out
