"""Verifica taglio SLU sezione c.a. — EC2 §6.2 + NTC §4.1.2.3.5.

Senza armatura a taglio (EC2 §6.2.2 eq. 6.2):
  V_Rd,c = [C_Rd,c·k·(100·ρ_l·f_ck)^(1/3) + k_1·σ_cp]·b_w·d ≥ (v_min + k_1·σ_cp)·b_w·d
  C_Rd,c = 0.18/γ_c, k = 1+√(200/d) ≤ 2.0, ρ_l = As/(b_w·d) ≤ 0.02,
  v_min = 0.035·k^1.5·√f_ck.

Con staffe (EC2 §6.2.3, traliccio a inclinazione variabile):
  V_Rd,s = (A_sw/s)·z·f_ywd·cotθ
  V_Rd,max = α_cw·b_w·z·ν_1·f_cd/(cotθ + tanθ)
  V_Rd = min(V_Rd,s, V_Rd,max),  z = 0.9·d, ν_1 = 0.6·(1 − f_ck/250).
"""

from __future__ import annotations

import math

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep


class CheckRcShearInput(BaseModel):
    b_w_mm: float = Field(..., gt=0, description="Larghezza anima")
    d_mm: float = Field(..., gt=0, description="Altezza utile")
    As_long_mm2: float = Field(..., ge=0, description="Armatura longitudinale tesa ancorata")
    f_ck_MPa: float = Field(25.0, gt=0, le=90)
    V_Ed_kN: float = Field(..., description="Taglio di progetto")
    N_Ed_kN: float = Field(0.0, description="Sforzo normale (+ compressione → σ_cp>0)")
    A_c_mm2: float | None = Field(None, description="Area cls per σ_cp (default b_w·d)")
    # staffe (opzionali)
    Asw_mm2: float = Field(0.0, ge=0, description="Area un braccio staffa × n bracci")
    s_mm: float = Field(0.0, ge=0, description="Passo staffe (0 = nessuna staffa)")
    f_ywk_MPa: float = Field(450.0, gt=0)
    cot_theta: float = Field(2.5, ge=1.0, le=2.5, description="cotθ traliccio (1.0-2.5)")
    gamma_c: float = Field(1.5, gt=0)
    gamma_s: float = Field(1.15, gt=0)
    alpha_cw: float = Field(1.0, gt=0)


class CheckRcShearOutput(CalcResult):
    V_Rd_c_kN: float | None = None
    V_Rd_s_kN: float | None = None
    V_Rd_max_kN: float | None = None
    V_Rd_kN: float | None = None
    eta: float | None = None
    serve_armatura: bool = False
    governing: str = ""
    verifica_ok: bool = False


def check_rc_shear(inp: CheckRcShearInput) -> CheckRcShearOutput:
    out = CheckRcShearOutput(tool="check_rc_shear", inputs_hash=compute_inputs_hash(inp))

    b_w, d = inp.b_w_mm, inp.d_mm
    f_cd = inp.f_ck_MPa / inp.gamma_c
    z = 0.9 * d
    V_Ed = abs(inp.V_Ed_kN)

    # V_Rd,c
    C_Rd_c = 0.18 / inp.gamma_c
    k = min(1.0 + math.sqrt(200.0 / d), 2.0)
    rho_l = min(inp.As_long_mm2 / (b_w * d), 0.02)
    A_c = inp.A_c_mm2 if inp.A_c_mm2 else b_w * d
    sigma_cp = min(inp.N_Ed_kN * 1000.0 / A_c, 0.2 * f_cd) if inp.N_Ed_kN > 0 else 0.0
    k_1 = 0.15
    v_min = 0.035 * k ** 1.5 * math.sqrt(inp.f_ck_MPa)
    V_Rd_c = (C_Rd_c * k * (100.0 * rho_l * inp.f_ck_MPa) ** (1.0 / 3.0) + k_1 * sigma_cp) * b_w * d
    V_Rd_c = max(V_Rd_c, (v_min + k_1 * sigma_cp) * b_w * d) / 1000.0  # kN
    out.V_Rd_c_kN = V_Rd_c

    out.trace.append(TraceStep(
        label="V_Rd,c",
        formula="V_Rd,c = [C_Rd,c·k·(100·ρ_l·f_ck)^⅓ + k_1·σ_cp]·b_w·d ≥ (v_min+k_1·σ_cp)·b_w·d",
        substitution=f"k={k:.3f}, ρ_l={rho_l:.4f}, σ_cp={sigma_cp:.2f} → V_Rd,c={V_Rd_c:.1f} kN",
        value=V_Rd_c, unit="kN", norm_ref="EC2 §6.2.2 eq. 6.2 + NTC §4.1.2.3.5.1",
    ))

    has_stirrups = inp.Asw_mm2 > 0 and inp.s_mm > 0
    if has_stirrups:
        f_ywd = inp.f_ywk_MPa / inp.gamma_s
        cot = inp.cot_theta
        tan = 1.0 / cot
        nu_1 = 0.6 * (1.0 - inp.f_ck_MPa / 250.0)
        V_Rd_s = (inp.Asw_mm2 / inp.s_mm) * z * f_ywd * cot / 1000.0  # kN
        V_Rd_max = inp.alpha_cw * b_w * z * nu_1 * f_cd / (cot + tan) / 1000.0
        out.V_Rd_s_kN = V_Rd_s
        out.V_Rd_max_kN = V_Rd_max
        V_Rd = min(V_Rd_s, V_Rd_max)
        out.governing = "biella compressa (V_Rd,max)" if V_Rd_max < V_Rd_s else "staffe (V_Rd,s)"
        out.trace.append(TraceStep(
            label="V_Rd,s / V_Rd,max",
            formula="V_Rd,s=(A_sw/s)·z·f_ywd·cotθ ; V_Rd,max=α_cw·b_w·z·ν_1·f_cd/(cotθ+tanθ)",
            substitution=f"cotθ={cot}, ν_1={nu_1:.3f} → V_Rd,s={V_Rd_s:.1f}, V_Rd,max={V_Rd_max:.1f} kN",
            value=V_Rd, unit="kN", norm_ref="EC2 §6.2.3 + NTC §4.1.2.3.5.2",
        ))
    else:
        V_Rd = V_Rd_c
        out.governing = "cls non armato (V_Rd,c)"

    out.V_Rd_kN = V_Rd
    out.serve_armatura = V_Ed > V_Rd_c
    eta = V_Ed / V_Rd if V_Rd > 0 else float("inf")
    out.eta = eta
    out.verifica_ok = eta <= 1.0

    out.trace.append(TraceStep(
        label="η taglio",
        formula="η = V_Ed / V_Rd",
        substitution=f"V_Ed={V_Ed} kN, V_Rd={V_Rd:.1f} kN → η={eta:.3f} ({out.governing})",
        value=eta, unit="-", norm_ref="EC2 §6.2 + NTC §4.1.2.3.5",
    ))

    # Sanity rules (§12.13)
    if out.serve_armatura and not has_stirrups:
        out.warnings.append(
            f"V_Ed={V_Ed} kN > V_Rd,c={V_Rd_c:.1f} kN: armatura a taglio NECESSARIA "
            "(la sezione senza staffe NON verifica)."
        )
    if has_stirrups and out.V_Rd_max_kN and V_Ed > out.V_Rd_max_kN:
        out.warnings.append(
            "V_Ed > V_Rd,max: biella di cls compressa schiacciata — aumentare b_w o ridurre cotθ."
        )
    if eta > 5.0:
        out.warnings.append(f"η={eta:.1f} ≫ 1: taglio fortemente insufficiente.")

    out.primary_value = eta
    out.primary_unit = "-"
    return out
