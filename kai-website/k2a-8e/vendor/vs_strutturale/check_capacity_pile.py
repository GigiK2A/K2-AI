"""Capacità portante assiale di un palo singolo — EN 1997-1 §7 (metodo statico).

R_c,k = R_b,k + R_s,k
  - R_b,k = q_b · A_b           (resistenza alla punta)
  - R_s,k = Σ f_s,i · π·D · h_i  (resistenza laterale per strato)

Correlazioni (metodo statico, documentate e riproducibili):
  - Punta argilla (non drenata):  q_b = N_c · c_u ,  N_c = 9 (Skempton, pali profondi)
  - Punta sabbia (drenata):       q_b = N_q · σ'_v,punta ,  N_q = e^(π·tanφ)·tan²(45°+φ/2)
  - Laterale argilla (α-method, API RP2A): f_s = α·c_u
        ψ = c_u/σ'_v ; α = 0.5·ψ^-0.5 (ψ≤1) | 0.5·ψ^-0.25 (ψ>1) , α≤1
  - Laterale sabbia (β-method):   f_s = β·σ'_v , β = K·tanδ , δ = φ , con cap f_s ≤ f_s,lim

Fattori di installazione (pile_type): infisso/trivellato/cfa → K_laterale e moltiplicatore punta.
Progetto: R_c,d = R_c,k / γ_R  (EN 1997 §7.6.2 — γ_R modello, default 1.35 DA2 pali trivellati).

Out-of-scope: pali in roccia/socket (→ check_micropali), carico laterale/momento (→ check_brinch_hansen
per fondazioni superficiali), terreni con falda artesiana. Carico assiale verticale, terreni
argilla/sabbia stratificati.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep

GAMMA_W = 9.81  # kN/m³ peso specifico acqua

# Fattori installazione: (moltiplicatore punta, K laterale)
PILE_TYPE_FACTORS = {
    "infisso":     {"base_mult": 1.0, "K": 1.0},   # driven — sposta/addensa
    "trivellato":  {"base_mult": 0.8, "K": 0.7},   # bored — rilassamento
    "cfa":         {"base_mult": 0.9, "K": 0.9},    # continuous flight auger
}


class SoilLayer(BaseModel):
    spessore_m: float = Field(..., gt=0, description="Spessore strato")
    tipo: Literal["argilla", "sabbia"] = Field(..., description="argilla (c_u) o sabbia (φ)")
    gamma_kN_m3: float = Field(18.0, gt=0, description="Peso specifico naturale")
    c_u_kPa: float = Field(0.0, ge=0, description="Coesione non drenata (argilla)")
    phi_deg: float = Field(0.0, ge=0, le=50, description="Angolo attrito (sabbia)")
    f_s_lim_kPa: float = Field(120.0, gt=0, description="Limite attrito laterale (sabbia)")


class CheckCapacityPileInput(BaseModel):
    pile_diameter_mm: float = Field(..., gt=0)
    pile_length_m: float = Field(..., gt=0)
    pile_type: Literal["infisso", "trivellato", "cfa"] = "trivellato"
    soil_profile: list[SoilLayer] = Field(..., min_length=1)
    water_table_m: float = Field(999.0, ge=0, description="Profondità falda dal p.c. (999=assente)")
    gamma_R: float = Field(1.35, gt=0, description="Fattore parziale resistenza EN 1997 §7.6.2")


class CheckCapacityPileOutput(CalcResult):
    R_b_k_kN: float | None = None
    R_s_k_kN: float | None = None
    R_c_k_kN: float | None = None
    R_c_d_kN: float | None = None
    q_b_kPa: float | None = None
    base_fraction: float | None = None


def _alpha_API(c_u: float, sigma_v: float) -> float:
    if sigma_v <= 0 or c_u <= 0:
        return 0.5
    psi = c_u / sigma_v
    alpha = 0.5 * psi ** -0.5 if psi <= 1.0 else 0.5 * psi ** -0.25
    return min(alpha, 1.0)


def check_capacity_pile(inp: CheckCapacityPileInput) -> CheckCapacityPileOutput:
    out = CheckCapacityPileOutput(tool="check_capacity_pile", inputs_hash=compute_inputs_hash(inp))

    D = inp.pile_diameter_mm / 1000.0
    L = inp.pile_length_m
    A_b = math.pi * D * D / 4.0
    perim = math.pi * D
    fac = PILE_TYPE_FACTORS[inp.pile_type]

    # Profondità totale profilo
    prof_tot = sum(s.spessore_m for s in inp.soil_profile)
    if prof_tot < L - 1e-6:
        out.warnings.append(
            f"Profilo terreno ({prof_tot:.1f} m) più corto del palo ({L:.1f} m): "
            "l'ultimo strato è esteso fino alla punta."
        )

    # Integrazione σ'_v e attrito laterale strato per strato (fino a z=L)
    R_s = 0.0
    z_top = 0.0
    sigma_v_top = 0.0  # tensione efficace a z_top
    tip_layer = inp.soil_profile[-1]
    sigma_v_tip = 0.0

    for i, layer in enumerate(inp.soil_profile):
        z_bot = z_top + layer.spessore_m
        # limita all'estensione del palo
        z_bot_eff = min(z_bot, L)
        if z_bot_eff <= z_top:
            break
        h = z_bot_eff - z_top
        z_mid = 0.5 * (z_top + z_bot_eff)

        # tensione efficace a z_mid e z_bot_eff (γ' sotto falda)
        gpr = layer.gamma_kN_m3 - (GAMMA_W if z_mid > inp.water_table_m else 0.0)
        sigma_v_mid = sigma_v_top + gpr * (z_mid - z_top)
        gpr_bot = layer.gamma_kN_m3 - (GAMMA_W if z_bot_eff > inp.water_table_m else 0.0)
        sigma_v_bot = sigma_v_top + gpr_bot * (z_bot_eff - z_top)

        if layer.tipo == "argilla":
            alpha = _alpha_API(layer.c_u_kPa, sigma_v_mid)
            f_s = alpha * layer.c_u_kPa
        else:  # sabbia
            K = fac["K"]
            delta = math.radians(layer.phi_deg)
            beta = K * math.tan(delta)
            f_s = min(beta * sigma_v_mid, layer.f_s_lim_kPa)

        R_s += f_s * perim * h
        out.trace.append(TraceStep(
            label=f"strato {i+1} ({layer.tipo})",
            formula="f_s·π·D·h" + (" ; f_s=α·c_u" if layer.tipo == "argilla" else " ; f_s=β·σ'_v"),
            substitution=f"z={z_top:.1f}-{z_bot_eff:.1f}m, σ'_v,mid={sigma_v_mid:.1f} kPa, f_s={f_s:.1f} kPa",
            value=f_s * perim * h, unit="kN", norm_ref="EN 1997-1 §7.6 (α/β-method)",
        ))

        if z_bot >= L - 1e-9:
            tip_layer = layer
            sigma_v_tip = sigma_v_bot
            sigma_v_top = sigma_v_bot
            z_top = z_bot_eff
            break
        sigma_v_top = sigma_v_bot
        z_top = z_bot_eff
    else:
        # palo più lungo del profilo: estendi ultimo strato
        tip_layer = inp.soil_profile[-1]
        extra = L - z_top
        if extra > 0:
            gpr = tip_layer.gamma_kN_m3 - (GAMMA_W if (z_top + extra/2) > inp.water_table_m else 0.0)
            sigma_v_mid = sigma_v_top + gpr * (extra / 2)
            if tip_layer.tipo == "argilla":
                f_s = _alpha_API(tip_layer.c_u_kPa, sigma_v_mid) * tip_layer.c_u_kPa
            else:
                f_s = min(fac["K"] * math.tan(math.radians(tip_layer.phi_deg)) * sigma_v_mid,
                          tip_layer.f_s_lim_kPa)
            R_s += f_s * perim * extra
            sigma_v_tip = sigma_v_top + gpr * extra

    # Resistenza punta
    if tip_layer.tipo == "argilla":
        q_b = 9.0 * tip_layer.c_u_kPa * fac["base_mult"]
        base_ref = "q_b = 9·c_u (Skempton)"
    else:
        phi = math.radians(tip_layer.phi_deg)
        Nq = math.exp(math.pi * math.tan(phi)) * (math.tan(math.pi/4 + phi/2)) ** 2
        q_b = Nq * sigma_v_tip * fac["base_mult"]
        base_ref = f"q_b = N_q·σ'_v,punta (N_q={Nq:.1f})"

    R_b = q_b * A_b
    out.q_b_kPa = q_b
    out.R_b_k_kN = R_b
    out.R_s_k_kN = R_s
    R_c_k = R_b + R_s
    out.R_c_k_kN = R_c_k
    out.R_c_d_kN = R_c_k / inp.gamma_R
    out.base_fraction = R_b / R_c_k if R_c_k > 0 else 0.0

    out.trace.append(TraceStep(
        label="punta R_b,k",
        formula="R_b,k = q_b·A_b",
        substitution=f"{base_ref}, A_b={A_b:.3f} m² → R_b,k={R_b:.1f} kN",
        value=R_b, unit="kN", norm_ref="EN 1997-1 §7.6",
    ))
    out.trace.append(TraceStep(
        label="R_c,k / R_c,d",
        formula="R_c,k = R_b,k + R_s,k ; R_c,d = R_c,k/γ_R",
        substitution=f"R_c,k={R_c_k:.1f} kN, γ_R={inp.gamma_R} → R_c,d={out.R_c_d_kN:.1f} kN",
        value=out.R_c_d_kN, unit="kN", norm_ref="EN 1997-1 §7.6.2",
    ))

    # Sanity rules (§12.13)
    if R_c_k < 0:
        raise ValueError("R_c,k negativa: input incoerente.")
    if out.base_fraction < 0.05:
        out.warnings.append(
            f"Resistenza punta trascurabile (R_b/R_c={out.base_fraction:.2%}): "
            "verificare profondità di infissione / strato di punta."
        )
    if D > 2.0:
        out.warnings.append(
            f"Diametro {D:.2f} m oltre il range pali standard: verificare pali di grande diametro."
        )
    if any(layer.tipo == "argilla" and layer.c_u_kPa > 400 for layer in inp.soil_profile):
        out.warnings.append(
            "c_u > 400 kPa (roccia tenera/socket): metodo statico per terreni non applicabile, "
            "usare check_micropali / socket in roccia."
        )

    out.primary_value = out.R_c_d_kN
    out.primary_unit = "kN"
    return out
