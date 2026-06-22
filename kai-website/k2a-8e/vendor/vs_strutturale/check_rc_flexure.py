"""Verifica sezione in c.a. a flessione composta (N+M) SLU — EC2 §6.1 + NTC §4.1.2.1.

Sezione rettangolare b×h con armatura tesa As (a d) ed eventuale compressa As' (a d').
Equilibrio per piani: si cerca l'asse neutro x tale che N_int(x) = N_Ed, poi M_Rd.

Materiali:
- Calcestruzzo: stress block rettangolare EC2 §3.1.7(3): profondità λ·x, tensione η·f_cd.
  Per f_ck ≤ 50 MPa: λ=0.8, η=1.0, ε_cu=3.5‰. f_cd = α_cc·f_ck/γ_c.
- Acciaio: elasto-plastico EC2 §3.2.7: σ_s = min(E_s·ε_s, f_yd), f_yd = f_yk/γ_s.

Convenzione N: **positivo = trazione**, negativo = compressione.
"""

from __future__ import annotations


from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep

E_S_MPA = 200000.0
EPS_CU = 3.5e-3


class CheckRcFlexureInput(BaseModel):
    b_mm: float = Field(..., gt=0)
    h_mm: float = Field(..., gt=0)
    d_mm: float = Field(..., gt=0, description="Altezza utile (baricentro armatura tesa)")
    As_mm2: float = Field(..., ge=0, description="Area armatura tesa")
    As_comp_mm2: float = Field(0.0, ge=0, description="Area armatura compressa")
    d_comp_mm: float = Field(40.0, gt=0, description="Copriferro armatura compressa")
    f_ck_MPa: float = Field(25.0, gt=0, le=50, description="Resistenza cilindrica cls (≤C50)")
    f_yk_MPa: float = Field(450.0, gt=0, description="Snervamento acciaio (B450C=450)")
    N_Ed_kN: float = Field(0.0, description="Sforzo normale (+ trazione, − compressione)")
    M_Ed_kNm: float = Field(..., description="Momento di progetto")
    alpha_cc: float = Field(0.85, gt=0, le=1.0)
    gamma_c: float = Field(1.5, gt=0)
    gamma_s: float = Field(1.15, gt=0)


class CheckRcFlexureOutput(CalcResult):
    x_mm: float | None = None
    x_su_d: float | None = None
    M_Rd_kNm: float | None = None
    eta: float | None = None
    eps_s_tesa: float | None = None
    governing: str = ""
    verifica_ok: bool = False


def check_rc_flexure(inp: CheckRcFlexureInput) -> CheckRcFlexureOutput:
    out = CheckRcFlexureOutput(tool="check_rc_flexure", inputs_hash=compute_inputs_hash(inp))

    f_cd = inp.alpha_cc * inp.f_ck_MPa / inp.gamma_c
    f_yd = inp.f_yk_MPa / inp.gamma_s
    b, h, d, dc = inp.b_mm, inp.h_mm, inp.d_mm, inp.d_comp_mm
    lam, eta = 0.8, 1.0
    N_Ed_N = inp.N_Ed_kN * 1000.0

    def sigma_s(eps):  # acciaio elasto-plastico, segno con eps
        s = E_S_MPA * eps
        return max(-f_yd, min(f_yd, s))

    def N_int(x):
        # forze (trazione positiva)
        a = min(lam * x, h)
        F_c = eta * f_cd * b * a            # compressione (riduce trazione)
        eps_t = EPS_CU * (d - x) / x        # >0 trazione se x<d
        F_s = inp.As_mm2 * sigma_s(eps_t)   # + se tesa
        eps_c = EPS_CU * (x - dc) / x       # >0 compressione armatura sup
        F_sc = inp.As_comp_mm2 * sigma_s(-eps_c)  # compressione → negativo (riduce trazione)
        return F_s - F_c + F_sc

    # bisection su x ∈ [x_lo, x_hi]
    x_lo, x_hi = 1e-3, 5.0 * h
    n_lo, n_hi = N_int(x_lo), N_int(x_hi)
    # N_int decresce con x (più cls compresso → più "compressione")
    if (n_lo - N_Ed_N) * (n_hi - N_Ed_N) > 0:
        # nessuna radice nel range: caso limite (sezione tutta tesa o tutta compressa)
        x = x_lo if abs(n_lo - N_Ed_N) < abs(n_hi - N_Ed_N) else x_hi
    else:
        for _ in range(200):
            x = 0.5 * (x_lo + x_hi)
            if (N_int(x_lo) - N_Ed_N) * (N_int(x) - N_Ed_N) <= 0:
                x_hi = x
            else:
                x_lo = x
        x = 0.5 * (x_lo + x_hi)

    out.x_mm = x
    out.x_su_d = x / d
    eps_t = EPS_CU * (d - x) / x
    out.eps_s_tesa = eps_t

    # M_Rd attorno al baricentro geometrico (h/2)
    a = min(lam * x, h)
    F_c = eta * f_cd * b * a
    F_s = inp.As_mm2 * sigma_s(eps_t)
    eps_c = EPS_CU * (x - dc) / x
    F_sc = inp.As_comp_mm2 * sigma_s(-eps_c)
    z_c = h / 2.0 - a / 2.0
    M = F_c * z_c + F_s * (d - h / 2.0) - F_sc * (dc - h / 2.0)
    M_Rd = abs(M) / 1.0e6  # kN·m
    out.M_Rd_kNm = M_Rd
    eta_check = abs(inp.M_Ed_kNm) / M_Rd if M_Rd > 0 else float("inf")
    out.eta = eta_check
    out.verifica_ok = eta_check <= 1.0

    # governing failure
    if eps_t >= f_yd / E_S_MPA:
        out.governing = "acciaio (duttile, snervato)" if x / d < 0.45 else "acciaio (al limite)"
    else:
        out.governing = "calcestruzzo (fragile, acciaio non snervato)"

    out.trace.append(TraceStep(
        label="asse neutro",
        formula="bisection N_int(x)=N_Ed ; stress block λ=0.8, η=1.0 (f_ck≤50)",
        substitution=f"f_cd={f_cd:.2f}, f_yd={f_yd:.1f} → x={x:.1f}mm, x/d={x/d:.3f}, ε_s={eps_t*1000:.2f}‰",
        value=x, unit="mm", norm_ref="EC2 §3.1.7 + §6.1",
    ))
    out.trace.append(TraceStep(
        label="M_Rd / η",
        formula="M_Rd = momento interno attorno a h/2 ; η = M_Ed/M_Rd",
        substitution=f"M_Rd={M_Rd:.1f} kN·m, M_Ed={inp.M_Ed_kNm} → η={eta_check:.3f} ({out.governing})",
        value=eta_check, unit="-", norm_ref="EC2 §6.1 + NTC 2018 §4.1.2.1",
    ))

    # Sanity rules (§12.13)
    if inp.f_ck_MPa > 50:
        raise ValueError("f_ck > 50 MPa: usare diagramma per cls alta resistenza (fuori scope).")
    if x / d > 0.45:
        out.warnings.append(
            f"x/d={x/d:.2f} > 0.45: sezione poco duttile (rottura fragile lato cls), "
            "EC8/NTC §7.4.4 raccomanda x/d ≤ 0.45 (CD-B) o 0.25 (CD-A) in zona sismica."
        )
    if eps_t < f_yd / E_S_MPA and out.verifica_ok:
        out.warnings.append("Acciaio teso NON snervato a rottura: rottura fragile, ridurre As o aumentare h.")
    if out.eta and out.eta > 5.0:
        out.warnings.append(f"η={out.eta:.1f} ≫ 1: sezione fortemente insufficiente, ridimensionare.")

    out.primary_value = eta_check
    out.primary_unit = "-"
    return out
