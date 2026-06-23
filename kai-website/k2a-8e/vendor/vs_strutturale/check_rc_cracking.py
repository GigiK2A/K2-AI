"""Verifica fessurazione SLE sezione c.a. — EC2 §7.3.4 + NTC §4.1.2.2.4.

Apertura caratteristica delle fessure:
  w_k = s_r,max · (ε_sm − ε_cm)

  s_r,max = k_3·c + k_1·k_2·k_4·Φ/ρ_p,eff           (EC2 eq. 7.11)
            k_3=3.4, k_1=0.8 (aderenza migliorata), k_2=0.5 (flessione), k_4=0.425
  (ε_sm−ε_cm) = [σ_s − k_t·(f_ct,eff/ρ_p,eff)·(1+α_e·ρ_p,eff)] / E_s ≥ 0.6·σ_s/E_s  (eq. 7.9)
            k_t=0.4 (lungo termine), α_e=E_s/E_cm, f_ct,eff=f_ctm
  ρ_p,eff = A_s / A_c,eff,  A_c,eff = b·h_c,ef,  h_c,ef = min(2.5(h−d), (h−x)/3, h/2)

Limiti w_max (EC2 Tab. 7.1N / NTC §4.1.2.2.4) per combinazione quasi-permanente:
  X0/XC1 → 0.4 mm ; XC2/XC3/XC4 → 0.3 mm ; XD/XS → 0.2 mm.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep

E_S_MPA = 200000.0

W_MAX = {"X0": 0.4, "XC1": 0.4, "XC2": 0.3, "XC3": 0.3, "XC4": 0.3,
         "XD1": 0.2, "XD2": 0.2, "XS1": 0.2, "XS2": 0.2, "XS3": 0.2}


class CheckRcCrackingInput(BaseModel):
    b_mm: float = Field(..., gt=0)
    h_mm: float = Field(..., gt=0)
    d_mm: float = Field(..., gt=0)
    As_mm2: float = Field(..., gt=0)
    phi_mm: float = Field(..., gt=0, description="Diametro barre")
    c_mm: float = Field(..., gt=0, description="Copriferro netto")
    sigma_s_MPa: float = Field(..., gt=0, description="Tensione acciaio in esercizio (SLE)")
    f_ck_MPa: float = Field(25.0, gt=0, le=50)
    classe_esposizione: Literal[
        "X0", "XC1", "XC2", "XC3", "XC4", "XD1", "XD2", "XS1", "XS2", "XS3"] = "XC2"
    x_sle_mm: float | None = Field(None, description="Asse neutro SLE (fessurato). Default 0.35·d")
    k_1: float = Field(0.8, description="0.8 barre aderenza migliorata, 1.6 lisce")
    k_t: float = Field(0.4, description="0.4 carichi lunga durata, 0.6 breve")


class CheckRcCrackingOutput(CalcResult):
    f_ctm_MPa: float | None = None
    rho_p_eff: float | None = None
    s_r_max_mm: float | None = None
    eps_sm_eps_cm: float | None = None
    w_k_mm: float | None = None
    w_max_mm: float | None = None
    eta: float | None = None
    verifica_ok: bool = False


def check_rc_cracking(inp: CheckRcCrackingInput) -> CheckRcCrackingOutput:
    out = CheckRcCrackingOutput(tool="check_rc_cracking", inputs_hash=compute_inputs_hash(inp))

    b, h, d = inp.b_mm, inp.h_mm, inp.d_mm
    x = inp.x_sle_mm if inp.x_sle_mm else 0.35 * d
    f_ctm = 0.30 * inp.f_ck_MPa ** (2.0 / 3.0)  # ≤ C50
    f_cm = inp.f_ck_MPa + 8.0
    E_cm = 22000.0 * (f_cm / 10.0) ** 0.3
    alpha_e = E_S_MPA / E_cm
    out.f_ctm_MPa = f_ctm

    # area efficace a trazione
    h_c_ef = min(2.5 * (h - d), (h - x) / 3.0, h / 2.0)
    A_c_eff = b * h_c_ef
    rho_p_eff = inp.As_mm2 / A_c_eff
    out.rho_p_eff = rho_p_eff

    # (ε_sm − ε_cm)
    eps = (inp.sigma_s_MPa - inp.k_t * (f_ctm / rho_p_eff) * (1.0 + alpha_e * rho_p_eff)) / E_S_MPA
    eps = max(eps, 0.6 * inp.sigma_s_MPa / E_S_MPA)
    out.eps_sm_eps_cm = eps

    # s_r,max
    k_2, k_3, k_4 = 0.5, 3.4, 0.425
    s_r_max = k_3 * inp.c_mm + inp.k_1 * k_2 * k_4 * inp.phi_mm / rho_p_eff
    out.s_r_max_mm = s_r_max

    w_k = s_r_max * eps
    out.w_k_mm = w_k
    w_max = W_MAX[inp.classe_esposizione]
    out.w_max_mm = w_max
    eta = w_k / w_max
    out.eta = eta
    out.verifica_ok = eta <= 1.0

    out.trace.append(TraceStep(
        label="ρ_p,eff e (ε_sm−ε_cm)",
        formula="A_c,eff=b·h_c,ef ; (ε_sm−ε_cm)=[σ_s−k_t·(f_ctm/ρ)·(1+α_e·ρ)]/E_s ≥ 0.6σ_s/E_s",
        substitution=f"f_ctm={f_ctm:.2f}, h_c,ef={h_c_ef:.0f}mm, ρ_p,eff={rho_p_eff:.4f} → εsm−εcm={eps*1000:.3f}‰",
        value=eps, unit="-", norm_ref="EC2 §7.3.4 eq. 7.9",
    ))
    out.trace.append(TraceStep(
        label="w_k / verifica",
        formula="s_r,max=k_3·c+k_1·k_2·k_4·Φ/ρ_p,eff ; w_k=s_r,max·(ε_sm−ε_cm) ; η=w_k/w_max",
        substitution=f"s_r,max={s_r_max:.0f}mm → w_k={w_k:.3f}mm, w_max={w_max}mm ({inp.classe_esposizione}) → η={eta:.3f}",
        value=w_k, unit="mm", norm_ref="EC2 §7.3.4 eq.7.11 + NTC §4.1.2.2.4 Tab.4.1.IV",
    ))

    # Sanity rules (§12.13)
    if inp.c_mm > 0.5 * h:
        out.warnings.append(f"copriferro c={inp.c_mm}mm > h/2: input incoerente.")
    if w_k > 2.0 * w_max:
        out.warnings.append(
            f"w_k={w_k:.2f}mm ≫ w_max={w_max}mm: fessurazione eccessiva, aumentare As o ridurre Φ."
        )
    if inp.sigma_s_MPa > 0.8 * 450.0:
        out.warnings.append(
            f"σ_s={inp.sigma_s_MPa} MPa elevato (>0.8·f_yk): verificare combinazione SLE/limite tensioni §7.2."
        )

    out.primary_value = eta
    out.primary_unit = "-"
    return out
