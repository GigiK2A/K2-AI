"""Analisi statica non lineare (pushover) — metodo N2 (Fajfar) — EN 1998-1 §4.3.3.4 + Annex B.

Procedura N2:
  1. Curva di capacità MDOF (δ_top, V_base) + forma modale φ (φ_top=1) + masse m_i.
  2. Fattore di trasformazione  Γ = Σ(m_i·φ_i) / Σ(m_i·φ_i²) ;  m* = Σ(m_i·φ_i).
  3. Sistema SDOF equivalente:  F* = V_base/Γ ,  d* = δ_top/Γ.
  4. Bilineare equi-energia (Annex B): F_y* = F* al meccanismo (ultimo) ;
     d_y* = 2·(d_m* − E_m*/F_y*) ;  k* = F_y*/d_y* ;  T* = 2π·√(m*·d_y*/F_y*).
  5. Domanda elastica: S_e(T*) dallo spettro ;  d_et* = S_e(T*)·(T*/2π)².
  6. Target SDOF:
       T* ≥ T_C →  d_t* = d_et*  (equal displacement)
       T* < T_C →  d_t* = (d_et*/q*)·[1 + (q*−1)·T_C/T*] ≥ d_et* ,  q* = S_e(T*)·m*/F_y*
  7. Target MDOF:  d_t = Γ·d_t* .  Duttilità richiesta μ = d_t*/d_y*.
  8. Verifica: d_t ≤ d_capacità (spostamento ultimo della curva).

EN-puro (nessun anchor K2A: le strutture TLC sono cantilever lineari, pushover non usato da K2A).
"""

from __future__ import annotations

import math

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep

G = 9.81  # m/s²


class CheckPushoverInput(BaseModel):
    capacity_curve: list[tuple[float, float]] = Field(
        ..., min_length=2, description="Lista (δ_top [m], V_base [kN]) crescente in δ"
    )
    masses_kg: list[float] = Field(..., min_length=1, description="Masse m_i ai punti modali")
    mode_shape: list[float] = Field(..., min_length=1, description="φ_i normalizzata (φ_top=1)")
    # Spettro elastico (g) — parametri per S_e(T*)
    ag_g: float = Field(..., gt=0)
    S: float = Field(..., gt=0, description="S = S_S·S_T")
    F0: float = Field(2.5, ge=2.0, le=3.5)
    Tc_s: float = Field(..., gt=0)
    Td_s: float = Field(2.0, gt=0)
    eta_smorz: float = Field(1.0, gt=0, description="η smorzamento (1.0 per ξ=5%)")
    d_capacity_m: float | None = Field(None, gt=0, description="Spostamento ultimo (default ultimo punto)")


class CheckPushoverOutput(CalcResult):
    Gamma: float | None = None
    m_star_kg: float | None = None
    F_y_star_kN: float | None = None
    d_y_star_m: float | None = None
    T_star_s: float | None = None
    Se_Tstar_g: float | None = None
    d_et_star_m: float | None = None
    d_t_star_m: float | None = None
    target_displacement_m: float | None = None
    V_t_kN: float | None = None
    mu_demand: float | None = None
    q_star: float | None = None
    safety_check: bool = False


def check_pushover(inp: CheckPushoverInput) -> CheckPushoverOutput:
    out = CheckPushoverOutput(tool="check_pushover", inputs_hash=compute_inputs_hash(inp))

    if len(inp.masses_kg) != len(inp.mode_shape):
        raise ValueError("masses_kg e mode_shape devono avere stessa lunghezza.")
    curve = sorted(inp.capacity_curve, key=lambda p: p[0])
    if curve[0][0] > 1e-9:
        curve = [(0.0, 0.0)] + curve

    # 2) Γ e m*
    m_phi = sum(m * f for m, f in zip(inp.masses_kg, inp.mode_shape))
    m_phi2 = sum(m * f * f for m, f in zip(inp.masses_kg, inp.mode_shape))
    Gamma = m_phi / m_phi2
    m_star = m_phi  # kg (con φ_top=1)
    out.Gamma = Gamma
    out.m_star_kg = m_star

    # 3) SDOF curve
    sdof = [(d / Gamma, V / Gamma) for d, V in curve]  # (d* [m], F* [kN])
    d_m = sdof[-1][0]
    F_y = sdof[-1][1]  # forza al meccanismo (plateau/ultimo)

    # 4) bilineare equi-energia: E_m* = area sotto F*-d* (trapezi)
    E_m = 0.0
    for (d0, f0), (d1, f1) in zip(sdof[:-1], sdof[1:]):
        E_m += 0.5 * (f0 + f1) * (d1 - d0)   # kN·m
    d_y = 2.0 * (d_m - E_m / F_y) if F_y > 0 else 0.0
    out.F_y_star_kN = F_y
    out.d_y_star_m = d_y

    # T* (m* in kg, F_y in kN=1000 N, d_y in m → k* in N/m)
    k_star = F_y * 1000.0 / d_y if d_y > 0 else float("inf")
    T_star = 2.0 * math.pi * math.sqrt(m_star / k_star) if k_star > 0 else 0.0
    out.T_star_s = T_star

    # 5) spettro elastico S_e(T*) [g]
    def S_e(T):
        Tb = inp.Tc_s / 3.0
        a = inp.ag_g * inp.S * inp.eta_smorz * inp.F0
        if T < Tb:
            return inp.ag_g * inp.S * inp.eta_smorz * inp.F0 * (
                T / Tb + 1.0 / (inp.eta_smorz * inp.F0) * (1.0 - T / Tb))
        if T < inp.Tc_s:
            return a
        if T < inp.Td_s:
            return a * (inp.Tc_s / T)
        return a * (inp.Tc_s * inp.Td_s / (T * T))

    Se = S_e(T_star)
    out.Se_Tstar_g = Se
    Se_ms2 = Se * G
    d_et = Se_ms2 * (T_star / (2.0 * math.pi)) ** 2  # m
    out.d_et_star_m = d_et

    # 6) target SDOF
    F_y_N = F_y * 1000.0
    q_star = Se_ms2 * m_star / F_y_N if F_y_N > 0 else float("inf")
    out.q_star = q_star
    if T_star >= inp.Tc_s:
        d_t_star = d_et
    else:
        d_t_star = (d_et / q_star) * (1.0 + (q_star - 1.0) * inp.Tc_s / T_star) if q_star > 1 else d_et
        d_t_star = max(d_t_star, d_et)
    out.d_t_star_m = d_t_star

    # 7) MDOF
    d_t = Gamma * d_t_star
    out.target_displacement_m = d_t
    out.mu_demand = d_t_star / d_y if d_y > 0 else float("inf")

    # V_t (interpola la curva MDOF al target)
    def interp_V(d):
        if d <= curve[0][0]:
            return curve[0][1]
        if d >= curve[-1][0]:
            return curve[-1][1]
        for (d0, v0), (d1, v1) in zip(curve[:-1], curve[1:]):
            if d0 <= d <= d1:
                return v0 + (v1 - v0) * (d - d0) / (d1 - d0)
        return curve[-1][1]
    out.V_t_kN = interp_V(d_t)

    d_cap = inp.d_capacity_m if inp.d_capacity_m else curve[-1][0]
    out.safety_check = d_t <= d_cap

    out.trace.append(TraceStep(
        label="SDOF + bilineare",
        formula="Γ=Σmφ/Σmφ² ; F_y*=F*(d_m) ; d_y*=2(d_m−E_m/F_y*) ; T*=2π√(m*d_y*/F_y*)",
        substitution=f"Γ={Gamma:.3f}, m*={m_star:.0f}kg, F_y*={F_y:.1f}kN, d_y*={d_y*1000:.1f}mm, T*={T_star:.3f}s",
        value=T_star, unit="s", norm_ref="EN 1998-1 Annex B (N2)",
    ))
    out.trace.append(TraceStep(
        label="target displacement",
        formula="d_et*=S_e(T*)(T*/2π)² ; d_t* (eq/short-period) ; d_t=Γ·d_t*",
        substitution=(
            f"S_e(T*)={Se:.4f}g, d_et*={d_et*1000:.1f}mm, q*={q_star:.2f}, "
            f"d_t*={d_t_star*1000:.1f}mm → d_t={d_t*1000:.1f}mm, μ={out.mu_demand:.2f}"
        ),
        value=d_t, unit="m", norm_ref="EN 1998-1 §4.3.3.4.2.6",
    ))
    out.trace.append(TraceStep(
        label="verifica capacità",
        formula="d_t ≤ d_capacità",
        substitution=f"d_t={d_t*1000:.1f}mm vs d_cap={d_cap*1000:.1f}mm → {'OK' if out.safety_check else 'NON VERIFICATO'}",
        value=d_t, unit="m", norm_ref="EN 1998-1 §4.3.3.4.2.6(2)",
    ))

    # Sanity rules (§12.13)
    if d_y <= 0:
        raise ValueError("d_y* ≤ 0: curva di capacità non idealizzabile (E_m troppo grande).")
    if abs(inp.mode_shape[-1] - 1.0) > 1e-6:
        out.warnings.append("mode_shape[-1] ≠ 1: la forma modale va normalizzata al nodo di controllo (top).")
    if out.mu_demand and out.mu_demand <= 1.0:
        out.warnings.append(
            f"μ_demand={out.mu_demand:.2f} ≤ 1: risposta elastica (no plasticizzazione richiesta)."
        )
    if not out.safety_check:
        out.warnings.append(
            f"d_t={d_t*1000:.1f}mm > d_capacità={d_cap*1000:.1f}mm: capacità di spostamento "
            "insufficiente, la struttura non raggiunge il performance point."
        )

    out.primary_value = d_t
    out.primary_unit = "m"
    return out
