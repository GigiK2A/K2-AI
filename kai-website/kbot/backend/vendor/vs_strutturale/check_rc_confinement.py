"""Confinamento sismico c.a. — EC8 §5.4.3.2.2 + NTC 2018 §7.4.6.2.2.

Armatura di confinamento alle zone critiche per garantire duttilità in curvatura.

Rapporto meccanico volumetrico di staffe:
  ω_wd = (volume staffe / volume nucleo) · (f_yd / f_cd)
       = (A_st·L_st)/(A_core·s) · (f_yd/f_cd)

Verifica (NTC eq. 7.4.29 / EC8 eq. 5.15):
  α·ω_wd ≥ 30·μ_φ·ν_d·ε_sy,d·(b_c/b_0) − 0.035
e ω_wd ≥ ω_wd,min (0.08 CD-A, 0.04 CD-B per pilastri).
α = α_n·α_s (efficacia confinamento).

Spaziatura staffe s ≤ s_max (funzione di b_0, d_bL, classe duttilità).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep

E_S_MPA = 200000.0
OMEGA_WD_MIN = {"CD-A": 0.08, "CD-B": 0.04}


class CheckRcConfinementInput(BaseModel):
    A_st_mm2: float = Field(..., gt=0, description="Area di un braccio di staffa")
    L_st_mm: float = Field(..., gt=0, description="Lunghezza sviluppata totale staffe+legature per sezione")
    A_core_mm2: float = Field(..., gt=0, description="Area nucleo confinato (b_0·h_0)")
    s_mm: float = Field(..., gt=0, description="Passo staffe")
    f_ck_MPa: float = Field(25.0, gt=0, le=50)
    f_yk_MPa: float = Field(450.0, gt=0)
    nu_d: float = Field(..., ge=0, le=0.65, description="ν_d = N_Ed/(A_c·f_cd) sforzo normale normalizzato")
    mu_phi: float = Field(..., gt=0, description="Domanda di duttilità in curvatura μ_φ")
    b_c_mm: float = Field(..., gt=0, description="Larghezza lorda sezione")
    b_0_mm: float = Field(..., gt=0, description="Larghezza nucleo confinato")
    alpha_eff: float = Field(0.5, gt=0, le=1.0, description="α=α_n·α_s efficacia confinamento")
    classe_duttilita: Literal["CD-A", "CD-B"] = "CD-A"
    d_bL_mm: float = Field(20.0, gt=0, description="Diametro barre longitudinali")
    gamma_c: float = Field(1.5, gt=0)
    gamma_s: float = Field(1.15, gt=0)


class CheckRcConfinementOutput(CalcResult):
    omega_wd: float | None = None
    omega_wd_req: float | None = None
    omega_wd_min: float | None = None
    s_max_mm: float | None = None
    eta_confinamento: float | None = None
    eta_spaziatura: float | None = None
    verifica_ok: bool = False


def check_rc_confinement(inp: CheckRcConfinementInput) -> CheckRcConfinementOutput:
    out = CheckRcConfinementOutput(tool="check_rc_confinement", inputs_hash=compute_inputs_hash(inp))

    f_cd = 0.85 * inp.f_ck_MPa / inp.gamma_c
    f_yd = inp.f_yk_MPa / inp.gamma_s
    eps_sy = f_yd / E_S_MPA

    omega_wd = (inp.A_st_mm2 * inp.L_st_mm) / (inp.A_core_mm2 * inp.s_mm) * (f_yd / f_cd)
    out.omega_wd = omega_wd

    # richiesto (NTC eq. 7.4.29)
    omega_req = (30.0 * inp.mu_phi * inp.nu_d * eps_sy * (inp.b_c_mm / inp.b_0_mm) - 0.035) / inp.alpha_eff
    omega_req = max(omega_req, 0.0)
    out.omega_wd_req = omega_req
    omega_min = OMEGA_WD_MIN[inp.classe_duttilita]
    out.omega_wd_min = omega_min

    omega_target = max(omega_req, omega_min)
    eta_conf = omega_target / omega_wd if omega_wd > 0 else float("inf")
    out.eta_confinamento = eta_conf

    # spaziatura massima
    if inp.classe_duttilita == "CD-A":
        s_max = min(inp.b_0_mm / 3.0, 125.0, 6.0 * inp.d_bL_mm)
    else:
        s_max = min(inp.b_0_mm / 2.0, 175.0, 8.0 * inp.d_bL_mm)
    out.s_max_mm = s_max
    eta_s = inp.s_mm / s_max
    out.eta_spaziatura = eta_s

    out.verifica_ok = eta_conf <= 1.0 and eta_s <= 1.0

    out.trace.append(TraceStep(
        label="ω_wd",
        formula="ω_wd = (A_st·L_st)/(A_core·s)·(f_yd/f_cd)",
        substitution=f"f_cd={f_cd:.2f}, f_yd={f_yd:.1f} → ω_wd={omega_wd:.4f}",
        value=omega_wd, unit="-", norm_ref="NTC §7.4.6.2.2 + EC8 §5.4.3.2.2",
    ))
    out.trace.append(TraceStep(
        label="verifica confinamento + spaziatura",
        formula="ω_wd ≥ max(ω_wd,req, ω_wd,min) ; s ≤ s_max",
        substitution=(
            f"ω_req={omega_req:.4f}, ω_min={omega_min} → target={omega_target:.4f}, "
            f"η_conf={eta_conf:.3f}; s_max={s_max:.0f}mm, η_s={eta_s:.3f}"
        ),
        value=eta_conf, unit="-", norm_ref="NTC eq.7.4.29 + §7.4.6.2.2",
    ))

    # Sanity rules (§12.13)
    if inp.nu_d > 0.55 and inp.classe_duttilita == "CD-A":
        out.warnings.append(f"ν_d={inp.nu_d} > 0.55: limite NTC §7.4.4.2.2.1 per CD-A superato.")
    if eta_conf > 1.0:
        out.warnings.append(
            f"ω_wd={omega_wd:.3f} < richiesto {omega_target:.3f}: confinamento insufficiente, "
            "infittire staffe o aumentare bracci."
        )
    if eta_s > 1.0:
        out.warnings.append(
            f"s={inp.s_mm}mm > s_max={s_max:.0f}mm: passo staffe eccessivo per la classe {inp.classe_duttilita}."
        )

    out.primary_value = max(eta_conf, eta_s)
    out.primary_unit = "-"
    return out
