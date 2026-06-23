"""Smorzamento aerodinamico δ_a — EN 1991-1-4 §F.5.

Per strutture snelle esposte al vento, lo smorzamento totale è:
    δ_tot = δ_s (strutturale) + δ_a (aerodinamico) + δ_d (dispositivi speciali)

Smorzamento aerodinamico (decremento logaritmico), EN 1991-1-4 eq. F.16:
    δ_a = c_f · ρ · b · v_m(z_s) / (2 · n_1 · m_e)

dove:
  c_f  = coefficiente di forza nella direzione del vento (≈0.6-1.2 per cilindro)
  ρ    = densità aria (1.25 kg/m³)
  b    = larghezza di riferimento (diametro per cilindro) [m]
  v_m  = velocità media del vento alla quota di riferimento z_s [m/s]
  n_1  = frequenza propria fondamentale [Hz]
  m_e  = massa equivalente per unità di lunghezza [kg/m]

Output: δ_a e δ_tot = δ_s + δ_a, da passare a wind_dynamic_factor come smorzamento_totale_log.
NB: nessuna modifica a wind_dynamic_factor (riceve δ_tot come input).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep


class CheckAerodynamicDampingInput(BaseModel):
    c_f: float = Field(..., gt=0, le=2.5, description="Coefficiente di forza (≈0.6-1.2 cilindro)")
    b_m: float = Field(..., gt=0, description="Larghezza di riferimento (diametro)")
    v_m_ms: float = Field(..., ge=0, description="Velocità media vento alla quota z_s")
    n_1_Hz: float = Field(..., gt=0, description="Frequenza propria fondamentale")
    m_e_kg_m: float = Field(..., gt=0, description="Massa equivalente per unità di lunghezza")
    delta_s_log: float = Field(
        0.012, ge=0.001, le=0.10,
        description="Smorzamento strutturale logaritmico (≈0.012 acciaio, 0.030 c.a.)",
    )
    delta_d_log: float = Field(0.0, ge=0.0, le=0.20, description="Smorzamento dispositivi speciali")
    rho_aria_kg_m3: float = 1.25


class CheckAerodynamicDampingOutput(CalcResult):
    delta_a_log: float | None = None
    delta_s_log: float | None = None
    delta_tot_log: float | None = None
    xi_a_pct: float | None = None
    frazione_aerodinamica: float | None = None


def check_aerodynamic_damping(inp: CheckAerodynamicDampingInput) -> CheckAerodynamicDampingOutput:
    out = CheckAerodynamicDampingOutput(
        tool="check_aerodynamic_damping", inputs_hash=compute_inputs_hash(inp))

    # δ_a = c_f · ρ · b · v_m / (2 · n_1 · m_e)   (EN 1991-1-4 eq. F.16)
    delta_a = inp.c_f * inp.rho_aria_kg_m3 * inp.b_m * inp.v_m_ms / (
        2.0 * inp.n_1_Hz * inp.m_e_kg_m)
    delta_tot = inp.delta_s_log + delta_a + inp.delta_d_log

    out.delta_a_log = delta_a
    out.delta_s_log = inp.delta_s_log
    out.delta_tot_log = delta_tot
    # rapporto di smorzamento ξ ≈ δ/(2π)
    import math
    out.xi_a_pct = delta_a / (2.0 * math.pi) * 100.0
    out.frazione_aerodinamica = delta_a / delta_tot if delta_tot > 0 else 0.0

    out.trace.append(TraceStep(
        label="δ_a aerodinamico",
        formula="δ_a = c_f·ρ·b·v_m/(2·n_1·m_e)",
        substitution=(
            f"c_f={inp.c_f}, ρ={inp.rho_aria_kg_m3}, b={inp.b_m}m, v_m={inp.v_m_ms}m/s, "
            f"n_1={inp.n_1_Hz}Hz, m_e={inp.m_e_kg_m}kg/m → δ_a={delta_a:.5f}"
        ),
        value=delta_a, unit="-", norm_ref="EN 1991-1-4 §F.5 eq. F.16",
    ))
    out.trace.append(TraceStep(
        label="δ totale",
        formula="δ_tot = δ_s + δ_a + δ_d",
        substitution=(
            f"= {inp.delta_s_log} + {delta_a:.5f} + {inp.delta_d_log} = {delta_tot:.5f} "
            f"(aerodinamico {out.frazione_aerodinamica:.1%})"
        ),
        value=delta_tot, unit="-", norm_ref="EN 1991-1-4 §F.5 — da usare in c_sc_d",
    ))

    # Sanity rules (§12.13)
    if delta_a < 0:
        raise ValueError("δ_a negativo: input incoerente.")
    if delta_a > inp.delta_s_log:
        out.warnings.append(
            f"δ_a={delta_a:.4f} > δ_s={inp.delta_s_log}: lo smorzamento aerodinamico domina "
            "(insolito per acciaio a velocità ordinarie; verificare v_m e m_e)."
        )
    if out.frazione_aerodinamica > 0.5:
        out.warnings.append(
            "Smorzamento aerodinamico > 50% del totale: la stima di c_sc_d è sensibile a v_m, "
            "valutare scenari di velocità."
        )

    out.primary_value = delta_tot
    out.primary_unit = "-"
    return out
