"""Capacità portante generale fondazione superficiale — Brinch-Hansen / Vesić (18 fattori).

Formula trinomia completa (EN 1997-1 Annex D + Vesić 1973):

  q_ult = c·N_c·s_c·d_c·i_c·g_c·b_c
        + q·N_q·s_q·d_q·i_q·g_q·b_q
        + 0.5·γ·B·N_γ·s_γ·d_γ·i_γ·g_γ·b_γ

con i 18 fattori correttivi: forma (s), profondità (d), inclinazione carico (i),
pendenza terreno (g), inclinazione base fondazione (b), per ciascuno dei 3 termini c/q/γ.

Chiude **Issue #002**: `check_foundation` usa una Brinch-Hansen SEMPLIFICATA senza i fattori
s/d/i/g/b (cautelativa per carico verticale, non-cautelativa per carichi inclinati). Questo
tool fornisce la forma completa, necessaria per edilizia / carichi inclinati significativi.

Fattori di portanza Vesić (coincidono col foglio K2A 27): N_q=e^(π·tanφ)·tan²(45+φ/2),
N_c=(N_q−1)/tanφ, N_γ=2·(N_q+1)·tanφ.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep


class CheckBrinchHansenInput(BaseModel):
    c_k_kPa: float = Field(0.0, ge=0, description="Coesione caratteristica")
    phi_k_deg: float = Field(..., ge=0, le=50, description="Angolo attrito caratteristico")
    gamma_k_kN_m3: float = Field(18.0, gt=0, description="Peso specifico terreno")
    foundation_B_m: float = Field(..., gt=0, description="Lato minore (efficace) B'")
    foundation_L_m: float = Field(..., gt=0, description="Lato maggiore (efficace) L'")
    foundation_depth_m: float = Field(..., ge=0, description="D — profondità piano di posa")
    V_Ed_kN: float = Field(..., gt=0, description="Carico verticale di progetto")
    H_Ed_kN: float = Field(0.0, ge=0, description="Carico orizzontale di progetto (in dir. B)")
    ground_slope_deg: float = Field(0.0, ge=0, lt=90, description="β — pendenza terreno")
    foundation_slope_deg: float = Field(0.0, ge=0, lt=90, description="η — inclinazione base")
    gamma_R: float = Field(2.3, gt=0, description="Fattore parziale R (Approccio 2 NTC §6.4.2.1)")


class CheckBrinchHansenOutput(CalcResult):
    N_c: float | None = None
    N_q: float | None = None
    N_gamma: float | None = None
    s_c: float | None = None; s_q: float | None = None; s_gamma: float | None = None
    d_c: float | None = None; d_q: float | None = None; d_gamma: float | None = None
    i_c: float | None = None; i_q: float | None = None; i_gamma: float | None = None
    g_c: float | None = None; g_q: float | None = None; g_gamma: float | None = None
    b_c: float | None = None; b_q: float | None = None; b_gamma: float | None = None
    q_ult_kPa: float | None = None
    q_d_kPa: float | None = None
    q_overburden_kPa: float | None = None
    safety_factor_against_capacity: float | None = None


def check_brinch_hansen(inp: CheckBrinchHansenInput) -> CheckBrinchHansenOutput:
    out = CheckBrinchHansenOutput(tool="check_brinch_hansen", inputs_hash=compute_inputs_hash(inp))

    if inp.phi_k_deg < 0 or inp.phi_k_deg > 50:
        raise ValueError("phi_k fuori range [0,50]°.")

    phi = math.radians(inp.phi_k_deg)
    c = inp.c_k_kPa
    B, L, D = inp.foundation_B_m, inp.foundation_L_m, inp.foundation_depth_m
    gamma = inp.gamma_k_kN_m3
    q = gamma * D                      # sovraccarico (overburden)
    out.q_overburden_kPa = q
    A = B * L
    BL = B / L
    tanphi = math.tan(phi)

    # --- Fattori di portanza (Vesić) ---
    if phi > 1e-6:
        Nq = math.exp(math.pi * tanphi) * math.tan(math.pi / 4 + phi / 2) ** 2
        Nc = (Nq - 1.0) / tanphi
        Ng = 2.0 * (Nq + 1.0) * tanphi
    else:
        Nq, Nc, Ng = 1.0, 5.14, 0.0
    out.N_q, out.N_c, out.N_gamma = Nq, Nc, Ng

    # --- Forma (Vesić) ---
    s_c = 1.0 + (Nq / Nc) * BL if phi > 1e-6 else 1.0 + 0.2 * BL
    s_q = 1.0 + BL * tanphi
    s_g = max(1.0 - 0.4 * BL, 0.6)
    out.s_c, out.s_q, out.s_gamma = s_c, s_q, s_g

    # --- Profondità (Brinch-Hansen) ---
    k = D / B if D <= B else math.atan(D / B)
    d_c = 1.0 + 0.4 * k
    d_q = 1.0 + 2.0 * tanphi * (1.0 - math.sin(phi)) ** 2 * k
    d_g = 1.0
    out.d_c, out.d_q, out.d_gamma = d_c, d_q, d_g

    # --- Inclinazione carico (Vesić), H in direzione B ---
    H = inp.H_Ed_kN
    V = inp.V_Ed_kN
    m = (2.0 + BL) / (1.0 + BL)
    denom = V + A * c / tanphi if phi > 1e-6 else None
    if phi > 1e-6:
        ratio = max(0.0, 1.0 - H / denom)
        i_q = ratio ** m
        i_g = ratio ** (m + 1.0)
        i_c = i_q - (1.0 - i_q) / (Nc * tanphi)
    else:
        i_c = 1.0 - m * H / (A * c * Nc) if (c > 0 and A > 0) else 1.0
        i_q = 1.0
        i_g = 1.0
    i_c = max(i_c, 0.0); i_q = max(i_q, 0.0); i_g = max(i_g, 0.0)
    out.i_c, out.i_q, out.i_gamma = i_c, i_q, i_g

    # --- Pendenza terreno (β) ---
    beta = math.radians(inp.ground_slope_deg)
    if phi > 1e-6:
        g_q = (1.0 - math.tan(beta)) ** 2
        g_g = g_q
        g_c = g_q - (1.0 - g_q) / (Nc * tanphi)
    else:
        g_q = g_g = 1.0
        g_c = 1.0 - 2.0 * beta / (math.pi + 2.0)
    g_c = max(g_c, 0.0); g_q = max(g_q, 0.0); g_g = max(g_g, 0.0)
    out.g_c, out.g_q, out.g_gamma = g_c, g_q, g_g

    # --- Inclinazione base fondazione (η) ---
    eta = math.radians(inp.foundation_slope_deg)
    if phi > 1e-6:
        b_q = (1.0 - eta * tanphi) ** 2
        b_g = b_q
        b_c = b_q - (1.0 - b_q) / (Nc * tanphi)
    else:
        b_q = b_g = 1.0
        b_c = 1.0 - 2.0 * eta / (math.pi + 2.0)
    b_c = max(b_c, 0.0); b_q = max(b_q, 0.0); b_g = max(b_g, 0.0)
    out.b_c, out.b_q, out.b_gamma = b_c, b_q, b_g

    # --- q_ult trinomia completa ---
    term_c = c * Nc * s_c * d_c * i_c * g_c * b_c
    term_q = q * Nq * s_q * d_q * i_q * g_q * b_q
    term_g = 0.5 * gamma * B * Ng * s_g * d_g * i_g * g_g * b_g
    q_ult = term_c + term_q + term_g
    out.q_ult_kPa = q_ult
    out.q_d_kPa = q_ult / inp.gamma_R

    out.trace.append(TraceStep(
        label="fattori di portanza (Vesić)",
        formula="N_q=e^(π·tanφ)·tan²(45+φ/2) ; N_c=(N_q−1)/tanφ ; N_γ=2(N_q+1)·tanφ",
        substitution=f"φ={inp.phi_k_deg}° → N_c={Nc:.2f}, N_q={Nq:.2f}, N_γ={Ng:.2f}",
        value=Nq, unit="-", norm_ref="Vesić 1973 / EN 1997-1 Annex D",
    ))
    out.trace.append(TraceStep(
        label="fattori correttivi (18)",
        formula="s/d/i/g/b per c/q/γ",
        substitution=(
            f"s=({s_c:.3f},{s_q:.3f},{s_g:.3f}) d=({d_c:.3f},{d_q:.3f},{d_g:.3f}) "
            f"i=({i_c:.3f},{i_q:.3f},{i_g:.3f}) g=({g_c:.3f},{g_q:.3f},{g_g:.3f}) "
            f"b=({b_c:.3f},{b_q:.3f},{b_g:.3f})"
        ),
        value=i_g, unit="-", norm_ref="Brinch-Hansen 1970 / Vesić 1973",
    ))
    out.trace.append(TraceStep(
        label="q_ult / q_d",
        formula="q_ult = c·N_c·(s·d·i·g·b)_c + q·N_q·(...)_q + 0.5·γ·B·N_γ·(...)_γ ; q_d=q_ult/γ_R",
        substitution=(
            f"term_c={term_c:.1f} + term_q={term_q:.1f} + term_γ={term_g:.1f} = "
            f"q_ult={q_ult:.1f} kPa → q_d={out.q_d_kPa:.1f} kPa (γ_R={inp.gamma_R})"
        ),
        value=out.q_d_kPa, unit="kPa", norm_ref="EN 1997-1 Annex D + NTC §6.4.2.1",
    ))

    # capacità vs carico applicato (pressione media)
    q_applied = V / A
    out.safety_factor_against_capacity = q_ult / q_applied if q_applied > 0 else float("inf")

    # Sanity rules (§12.13)
    if q_ult < q:
        raise ValueError(
            f"q_ult ({q_ult:.1f}) < sovraccarico q ({q:.1f}): impossibile fisicamente, input incoerente."
        )
    if inp.H_Ed_kN / inp.V_Ed_kN > 0.5:
        out.warnings.append(
            f"Inclinazione H/V={inp.H_Ed_kN/inp.V_Ed_kN:.2f} estrema (>0.5): verificare applicabilità "
            "del metodo (possibile scorrimento governante)."
        )
    if i_g < 0.5:
        out.warnings.append(
            f"Fattore i_γ={i_g:.2f} < 0.5: il carico inclinato riduce drasticamente la portanza — "
            "il metodo semplificato (check_foundation, Issue #002) sovrastimerebbe q_ult qui."
        )

    out.primary_value = out.q_d_kPa
    out.primary_unit = "kPa"
    return out
