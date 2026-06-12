"""Cedimenti di palo singolo e gruppo — metodo elastico — EN 1997-1 §7.4.2.

Palo singolo (cedimento in testa, carico di esercizio SLE):
  s_single = s_axial + s_base
    - s_axial = P·L / (2·A_p·E_p)         accorciamento elastico (carico medio ~P/2 per palo
                                           ad attrito; fattore 2 al denominatore)
    - s_base  = P·(1−ν_s²)·C_b / (E_s·D)   cedimento del terreno alla base (Boussinesq, piastra
                                           rigida circolare, C_b = π/4·0.85)
Gruppo (Poulos): s_group = R_s · s_single, con R_s = rapporto di cedimento di gruppo
  (input group_settlement_ratio; stima di default R_s ≈ √n_piles, cautelativa per sabbia).

Verifica SLE: s_group ≤ s_limit (EN 1997-1 §7.4.2 — limite di servizio).
"""

from __future__ import annotations

import math

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep

C_B = math.pi / 4.0 * 0.85  # fattore piastra rigida circolare (Boussinesq) ≈ 0.6675


class CheckSettlementInput(BaseModel):
    pile_diameter_mm: float = Field(..., gt=0)
    pile_length_m: float = Field(..., gt=0)
    P_head_kN: float = Field(..., gt=0, description="Carico di esercizio in testa (SLE)")
    E_pile_MPa: float = Field(30000.0, gt=0, description="Modulo elastico palo (cls ~30 GPa)")
    E_soil_MPa: float = Field(..., gt=0, description="Modulo elastico terreno (drenato)")
    nu_soil: float = Field(0.3, ge=0, le=0.5, description="Coeff. Poisson terreno")
    n_piles: int = Field(1, ge=1)
    group_settlement_ratio: float | None = Field(
        None, gt=0, description="R_s = s_group/s_single (default √n_piles)"
    )
    s_limit_mm: float = Field(25.0, gt=0, description="Limite SLE cedimento EN 1997 §7.4.2")


class CheckSettlementOutput(CalcResult):
    s_axial_mm: float | None = None
    s_base_mm: float | None = None
    s_single_mm: float | None = None
    R_s_group: float | None = None
    s_group_mm: float | None = None
    eta_SLE: float | None = None
    verifica_ok: bool = False


def check_settlement(inp: CheckSettlementInput) -> CheckSettlementOutput:
    out = CheckSettlementOutput(tool="check_settlement", inputs_hash=compute_inputs_hash(inp))

    D = inp.pile_diameter_mm / 1000.0
    L = inp.pile_length_m
    A_p = math.pi * D * D / 4.0
    P_N = inp.P_head_kN * 1000.0          # N
    E_p = inp.E_pile_MPa * 1.0e6          # Pa
    E_s = inp.E_soil_MPa * 1.0e6          # Pa

    # accorciamento elastico (m → mm)
    s_axial = P_N * L / (2.0 * A_p * E_p) * 1000.0
    # cedimento base (Boussinesq piastra rigida)
    s_base = P_N * (1.0 - inp.nu_soil ** 2) * C_B / (E_s * D) * 1000.0
    s_single = s_axial + s_base
    out.s_axial_mm = s_axial
    out.s_base_mm = s_base
    out.s_single_mm = s_single

    R_s = inp.group_settlement_ratio if inp.group_settlement_ratio else math.sqrt(inp.n_piles)
    out.R_s_group = R_s
    s_group = R_s * s_single
    out.s_group_mm = s_group

    out.eta_SLE = s_group / inp.s_limit_mm
    out.verifica_ok = out.eta_SLE <= 1.0

    out.trace.append(TraceStep(
        label="cedimento palo singolo",
        formula="s_single = P·L/(2·A_p·E_p) + P·(1−ν²)·C_b/(E_s·D)",
        substitution=(
            f"s_axial={s_axial:.3f} mm + s_base={s_base:.3f} mm = s_single={s_single:.3f} mm "
            f"(D={D:.2f}m, E_s={inp.E_soil_MPa} MPa)"
        ),
        value=s_single, unit="mm", norm_ref="Metodo elastico (Poulos-Davis / Boussinesq)",
    ))
    out.trace.append(TraceStep(
        label="cedimento gruppo + verifica SLE",
        formula="s_group = R_s·s_single ; η = s_group/s_limit",
        substitution=(
            f"R_s={R_s:.3f} (n={inp.n_piles}) → s_group={s_group:.3f} mm, "
            f"s_limit={inp.s_limit_mm} mm → η={out.eta_SLE:.3f} {'OK' if out.verifica_ok else 'NV'}"
        ),
        value=out.eta_SLE, unit="-", norm_ref="EN 1997-1 §7.4.2 (SLE)",
    ))

    # Sanity rules (§12.13)
    if s_single < 0:
        raise ValueError("Cedimento negativo: input incoerente.")
    if inp.E_soil_MPa < 2.0:
        out.warnings.append(
            f"E_soil={inp.E_soil_MPa} MPa molto basso (<2): terreno molto compressibile, "
            "verificare cedimenti di consolidazione a lungo termine (non inclusi)."
        )
    if s_base / s_single > 0.9:
        out.warnings.append(
            "Cedimento dominato dalla base (>90%): verificare ipotesi di palo ad attrito vs portante."
        )
    if out.eta_SLE > 1.0:
        out.warnings.append(
            f"Cedimento di gruppo {s_group:.1f} mm > limite SLE {inp.s_limit_mm} mm: "
            "NON verificato — aumentare n pali, lunghezza o ridurre carico."
        )

    out.primary_value = s_group
    out.primary_unit = "mm"
    return out
