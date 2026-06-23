"""Analisi modale semplificata — frequenza fondamentale n_1 di pali a mensola.

Metodo: quoziente di Rayleigh su forma modale ammissibile per cantilever.

    n_1 = (1/2π)·√(k*/m*)
    k* = ∫₀^H EI(z)·[ψ''(z)]² dz          (rigidezza generalizzata)
    m* = ∫₀^H μ(z)·[ψ(z)]² dz + Σ M_i·[ψ(z_i)]²   (massa generalizzata)

Forma modale: ψ(z) = 1 − cos(πz/2H).
NB metodologico (F12-W3): il prompt suggeriva ψ = sin(πz/2H), che però NON soddisfa la
condizione essenziale di vincolo del cantilever ψ'(0)=0 (pendenza nulla all'incastro) e
darebbe una stima di Rayleigh scadente. Si adotta ψ = 1−cos(πz/2H), che soddisfa
ψ(0)=0, ψ'(0)=0, ψ(H)=1 ed è la scelta classica per il primo modo flessionale di mensola.
Validato su GT-MODAL-1 (cilindrico D=600 t=8 H=30 +200kg): n_1 ≈ 0.636 Hz ≈ atteso 0.62.

Sezioni tubolari a parete sottile: A = π·D·t, I = π·(D/2)³·t.
Tronchi conici: D varia linearmente base→sommità; integrazione numerica (trapezi).

Perimetro: questo tool calcola SOLO il modo fondamentale (n_1, T_1, massa partecipante
modo 1) in modo rigoroso. I modi superiori (2+) NON sono forniti: per pali snelli TLC il
modo 1 governa l'azione del vento (input per wind_dynamic_factor) e il sisma; un'analisi
multimodale completa richiede uno stick-model FEM dedicato (cfr. solve_fem_beam /
buckling_analysis_fem). Decisione F12-W3: stime analitiche dei modi 2-5 (rapporti mensola
uniforme) rimosse perché imprecise per sezioni rastremate (verificato vs FE eigen: mode 2
3.65 Hz stima vs 2.83 Hz FE per il caso conico).
"""

from __future__ import annotations

import math

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep

E_STEEL_MPA = 210000.0
RHO_STEEL = 7850.0  # kg/m³


class TroncoModale(BaseModel):
    z_base_m: float = Field(..., ge=0)
    z_top_m: float = Field(..., gt=0)
    D_base_m: float = Field(..., gt=0, description="Diametro esterno alla base del tronco")
    D_top_m: float = Field(..., gt=0, description="Diametro esterno in sommità del tronco")
    t_mm: float = Field(..., gt=0, description="Spessore parete (mm)")
    E_MPa: float = Field(E_STEEL_MPA, gt=0)
    rho_kg_m3: float = Field(RHO_STEEL, gt=0)


class MassaConcentrata(BaseModel):
    z_m: float = Field(..., ge=0)
    massa_kg: float = Field(..., ge=0)
    descrizione: str = ""


class ModalAnalysisInput(BaseModel):
    tronchi: list[TroncoModale] = Field(..., min_length=1)
    masse_concentrate: list[MassaConcentrata] = Field(default_factory=list)
    xi_critico_pct: float = Field(
        1.0, gt=0, le=10,
        description="Smorzamento critico assunto (% critico). Acciaio bullonato ~1%, saldato ~0.6%",
    )
    n_integrazione: int = Field(400, ge=20, le=5000, description="Punti integrazione numerica")


class ModalAnalysisOutput(CalcResult):
    n_1_Hz: float | None = None
    T_1_s: float | None = None
    xi_critico_pct: float | None = None
    delta_log: float | None = None
    massa_totale_kg: float | None = None
    massa_generalizzata_kg: float | None = None
    rigidezza_generalizzata_N_m: float | None = None
    massa_partecipante_modo1_pct: float | None = None


def _D_at(z: float, tronchi: list[TroncoModale]) -> tuple[float, float, float, float] | None:
    """Ritorna (D, t_m, E_Pa, rho) alla quota z interpolando il tronco che la contiene."""
    for tr in tronchi:
        if tr.z_base_m <= z <= tr.z_top_m:
            L = tr.z_top_m - tr.z_base_m
            frac = (z - tr.z_base_m) / L if L > 0 else 0.0
            D = tr.D_base_m + frac * (tr.D_top_m - tr.D_base_m)
            return D, tr.t_mm / 1000.0, tr.E_MPa * 1e6, tr.rho_kg_m3
    return None


def modal_analysis(inp: ModalAnalysisInput) -> ModalAnalysisOutput:
    out = ModalAnalysisOutput(tool="modal_analysis", inputs_hash=compute_inputs_hash(inp))

    H = max(tr.z_top_m for tr in inp.tronchi)
    z_min = min(tr.z_base_m for tr in inp.tronchi)
    if z_min > 1e-9:
        out.warnings.append(f"Base tronchi a z={z_min}m ≠ 0: schema mensola assume incastro a z=0.")

    def psi(z: float) -> float:
        return 1.0 - math.cos(math.pi * z / (2.0 * H))

    def psi2(z: float) -> float:  # ψ''(z)
        return (math.pi / (2.0 * H)) ** 2 * math.cos(math.pi * z / (2.0 * H))

    # Integrazione numerica trapezoidale su [0, H].
    n = inp.n_integrazione
    dz = H / n
    k_star = 0.0   # ∫ EI ψ''² dz
    m_star = 0.0   # ∫ μ ψ² dz
    m_tot_distrib = 0.0
    L_star = 0.0   # ∫ μ ψ dz  (numeratore fattore di partecipazione)
    prev = None
    for i in range(n + 1):
        z = i * dz
        sec = _D_at(z, inp.tronchi)
        if sec is None:
            integrand = (0.0, 0.0, 0.0, 0.0)
        else:
            D, t_m, E_Pa, rho = sec
            A = math.pi * D * t_m
            I = math.pi * (D / 2.0) ** 3 * t_m
            mu = rho * A
            integrand = (E_Pa * I * psi2(z) ** 2, mu * psi(z) ** 2, mu, mu * psi(z))
        if prev is not None:
            for j, (a, b) in enumerate(zip(prev, integrand)):
                val = 0.5 * (a + b) * dz
                if j == 0:
                    k_star += val
                elif j == 1:
                    m_star += val
                elif j == 2:
                    m_tot_distrib += val
                else:
                    L_star += val
        prev = integrand

    # Masse concentrate
    m_conc = 0.0
    for mc in inp.masse_concentrate:
        p = psi(mc.z_m)
        m_star += mc.massa_kg * p * p
        L_star += mc.massa_kg * p
        m_conc += mc.massa_kg

    if m_star <= 0 or k_star <= 0:
        out.out_of_scope = True
        out.out_of_scope_reason = "massa o rigidezza generalizzata nulla — geometria non valida"
        return out

    omega = math.sqrt(k_star / m_star)
    n_1 = omega / (2.0 * math.pi)
    T_1 = 1.0 / n_1
    m_tot = m_tot_distrib + m_conc
    m_eff_1 = (L_star ** 2) / m_star  # massa efficace modo 1
    part_1 = min(m_eff_1 / m_tot * 100.0, 100.0) if m_tot > 0 else 0.0

    out.n_1_Hz = n_1
    out.T_1_s = T_1
    out.xi_critico_pct = inp.xi_critico_pct
    out.delta_log = 2.0 * math.pi * inp.xi_critico_pct / 100.0
    out.massa_totale_kg = m_tot
    out.massa_generalizzata_kg = m_star
    out.rigidezza_generalizzata_N_m = k_star
    out.massa_partecipante_modo1_pct = part_1

    # Sanity (§12.13)
    if not (0.1 <= n_1 <= 10.0):
        out.warnings.append(f"n_1={n_1:.3f} Hz fuori range tipico pali [0.1, 10] Hz — verificare geometria/masse.")
    if part_1 < 60.0:
        out.warnings.append(
            f"Massa partecipante modo 1 = {part_1:.1f}% < 60%: contributo modi superiori "
            "non trascurabile, considerare analisi multimodale (stick-model FEM)."
        )
    if H > 40.0:
        out.warnings.append(f"H={H}m oltre perimetro validato v1 (≤40m).")

    out.trace.append(TraceStep(
        label="Rayleigh n_1",
        formula="n_1 = (1/2π)·√(k*/m*) ; ψ(z)=1−cos(πz/2H)",
        substitution=(
            f"k*={k_star:.4g} N/m, m*={m_star:.4g} kg → ω={omega:.4f} rad/s, "
            f"n_1={n_1:.4f} Hz, T_1={T_1:.3f} s"
        ),
        value=n_1, unit="Hz",
        norm_ref="EN 1998-1 §4.3.3.2 (Rayleigh) + NTC 2018 §7.3.3",
    ))
    out.trace.append(TraceStep(
        label="massa partecipante modo 1",
        formula="M_eff,1 = (∫μψ + ΣMψ)² / m* ; partecipazione = M_eff,1/M_tot",
        substitution=f"L*={L_star:.4g}, m*={m_star:.4g}, M_tot={m_tot:.1f} kg → {part_1:.1f}%",
        value=part_1, unit="%",
        norm_ref="NTC 2018 §7.3.3.1 — masse partecipanti",
    ))

    out.primary_value = n_1
    out.primary_unit = "Hz"
    return out
