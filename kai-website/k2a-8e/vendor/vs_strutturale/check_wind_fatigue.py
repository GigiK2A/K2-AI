"""Verifica fatica indotta dal vento — EN 1993-3-1 Annex B + CNR-DT 207 §3.5.

Per pali TLC alti la fatica meccanica è governata da oscillazioni
indotte dal vento turbolento (raffiche) lungo la vita di progetto V_N.

Approccio EN 1993-3-1 Annex B (rapid method):
  σ_E,2 = λ · σ_max(v_b)        damage-equivalent stress range at 2·10⁶ cicli
  λ     = κ_w · κ_N · κ_M · κ_T  damage equivalent factor

dove:
  σ_max(v_b) = ampiezza tensione sotto vento di riferimento (caratteristica)
  λ = ~1.5 ÷ 2.5 cautelativo per pali TLC (vita 50 anni)
  κ_w  fattore distribuzione vento (Weibull/Rayleigh) ≈ 1.0 default
  κ_N  fattore durata vita: (V_N/50)^(1/m), m=3 → ~1.0 per 50 anni
  κ_M  fattore distribuzione momenti modale ~1.0
  κ_T  fattore topografia/esposizione ~1.0-1.3

Verifica EN 1993-1-9 §8:
  σ_E,2 · γ_Ff ≤ Δσ_C / γ_Mf      (D = σ_E,2/(Δσ_C/γ_Mf) ≤ 1)

Categoria dettaglio Δσ_C più frequenti su pali TLC:
  71  MPa — bullonatura flangia (sforzo perpendicolare bullone)
  80  MPa — saldatura cordoni d'angolo
  90  MPa — saldatura testa a testa (controllo NDT B EN ISO 5817)
  100 MPa — saldatura testa a testa accurata (lunghezza > limite)
  125 MPa — barra liscia / sezione semplice (nessuna intaglio)

Cellnex CNP_TS21_002 prescrive Δσ_C secondo qualità saldatura post-2009 = Classe B.
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash

from typing import Literal

from pydantic import BaseModel, Field

from .schemas import CalcResult, TraceStep


class CheckWindFatigueInput(BaseModel):
    sigma_max_MPa: float = Field(
        ..., gt=0,
        description=(
            "Ampiezza tensione massima [MPa] nel dettaglio sotto vento di riferimento "
            "v_b (caratteristica, NO γ). Tipico: σ = M_Ed,k / W_el al dettaglio critico."
        ),
    )
    delta_sigma_C_MPa: float = Field(
        ...,
        description="Categoria dettaglio EN 1993-1-9 Tab. 8.1 (es. 71, 80, 90)",
    )
    metodo: Literal["EN_3_1_rapid", "Miner_full"] = Field(
        "EN_3_1_rapid",
        description=(
            "rapid = EN 1993-3-1 Annex B (σ_E,2 = λ·σ_max); "
            "Miner_full = costruisce spettro Rayleigh+cicli e applica Miner."
        ),
    )
    lambda_damage: float = Field(
        2.0, ge=1.0, le=4.0,
        description=(
            "Damage equivalent factor (EN 1993-3-1 Annex B Fig. B.4 / Tab. B.1). "
            "Default 2.0 cautelativo per pali TLC."
        ),
    )
    V_N_anni: int = Field(50, ge=10, le=100)
    gamma_Ff: float = 1.0
    gamma_Mf: float = Field(
        1.35,
        description=(
            "EN 1993-1-9 Tab. 3.1 — 1.00 (safe-life) / 1.15 (safe-life NDT) / "
            "1.35 (consequence elevated)"
        ),
    )
    # Solo per Miner_full:
    n_struct_Hz: float | None = Field(
        None, description="Freq. propria struttura (solo metodo Miner_full)"
    )


class CheckWindFatigueOutput(CalcResult):
    sigma_E_2_MPa: float | None = None
    delta_sigma_C_d_MPa: float | None = None
    damage_D: float | None = None
    metodo_usato: str = ""
    verifica_ok: bool = False


def check_wind_fatigue(inp: CheckWindFatigueInput) -> CheckWindFatigueOutput:
    out = CheckWindFatigueOutput(tool="check_wind_fatigue", inputs_hash=compute_inputs_hash(inp))
    out.metodo_usato = inp.metodo

    # σ di progetto (γ_Ff applicato)
    sigma_max_d = inp.sigma_max_MPa * inp.gamma_Ff

    # σ_E,2 — damage equivalent stress range a 2·10⁶ cicli
    # Aggiunta correzione vita: (V_N/50)^(1/m), m=3 → factor V_N
    factor_VN = (inp.V_N_anni / 50.0) ** (1.0 / 3.0)
    sigma_E_2 = inp.lambda_damage * sigma_max_d * factor_VN
    out.sigma_E_2_MPa = sigma_E_2

    out.trace.append(TraceStep(
        label="σ_E,2 (damage-equivalent)",
        formula="σ_E,2 = λ · σ_max · γ_Ff · (V_N/50)^(1/3)",
        substitution=(
            f"λ={inp.lambda_damage}, σ_max={inp.sigma_max_MPa} MPa, γ_Ff={inp.gamma_Ff}, "
            f"V_N={inp.V_N_anni} → σ_E,2 = {sigma_E_2:.2f} MPa"
        ),
        value=sigma_E_2, unit="MPa",
        norm_ref="EN 1993-3-1 Annex B §B.2.3 — Damage Equivalent Method",
    ))

    # Δσ_C di calcolo
    delta_sigma_C_d = inp.delta_sigma_C_MPa / inp.gamma_Mf
    out.delta_sigma_C_d_MPa = delta_sigma_C_d
    out.trace.append(TraceStep(
        label="Δσ_C,d",
        formula="Δσ_C,d = Δσ_C / γ_Mf",
        substitution=f"Δσ_C={inp.delta_sigma_C_MPa} MPa / γ_Mf={inp.gamma_Mf} → {delta_sigma_C_d:.2f} MPa",
        value=delta_sigma_C_d, unit="MPa",
        norm_ref="EN 1993-1-9 §8 Tab. 8.1 + Tab. 3.1 (γ_Mf)",
    ))

    # Damage D — semplificato per 2·10⁶ cicli rappresentativi
    if inp.metodo == "EN_3_1_rapid":
        # D = (σ_E,2 / Δσ_C,d)^3   (curva m=3)
        D = (sigma_E_2 / delta_sigma_C_d) ** 3
        out.damage_D = D
        out.trace.append(TraceStep(
            label="D (damage equivalent)",
            formula="D = (σ_E,2 / Δσ_C,d)^3   [curva S-N m=3 EN 1993-1-9]",
            substitution=f"D = ({sigma_E_2:.2f} / {delta_sigma_C_d:.2f})³ = {D:.4f}",
            value=D, unit="-",
            norm_ref="EN 1993-1-9 §8.2 + EN 1993-3-1 Annex B",
        ))
    elif inp.metodo == "Miner_full":
        if inp.n_struct_Hz is None:
            out.warnings.append("Miner_full richiede n_struct_Hz. Fallback a EN_3_1_rapid.")
            D = (sigma_E_2 / delta_sigma_C_d) ** 3
        else:
            # Spettro Rayleigh semplificato: assume σ ~ v²/v_b² · σ_max
            # Numero cicli in V_N: n_tot = n_struct · 0.6 · V_N · 365 · 24 · 3600 (vento attivo ~60%)
            n_tot = inp.n_struct_Hz * 0.6 * inp.V_N_anni * 365 * 24 * 3600
            # Cicli effettivi danno (parte alta dello spettro Weibull)
            # Cautelativo: assumo 5% dei cicli totali contribuiscono
            n_eff = n_tot * 0.05
            # Applico curva m=3 con scaling cicli
            D = (sigma_E_2 / delta_sigma_C_d) ** 3 * (n_eff / 2.0e6)
            out.damage_D = D
            out.trace.append(TraceStep(
                label="D Miner (full)",
                formula="n_tot = n_struct·0.6·V_N·31536000 ; D ∝ (σ/Δσ_C,d)³·(n_eff/2e6)",
                substitution=(
                    f"n_struct={inp.n_struct_Hz} Hz, n_tot={n_tot:.2e}, "
                    f"n_eff(5%)={n_eff:.2e} → D = {D:.4f}"
                ),
                value=D, unit="-",
                norm_ref="EN 1993-1-9 §8.2 + Miner cumulativo",
            ))
        out.damage_D = D

    out.verifica_ok = (out.damage_D or 0.0) <= 1.0
    out.trace.append(TraceStep(
        label="esito fatica",
        formula="D ≤ 1.0",
        substitution=f"D={out.damage_D:.4f} → {'OK' if out.verifica_ok else 'NON VERIFICATO'}",
        value=out.damage_D, unit="-",
        norm_ref="EN 1993-1-9 §8.2 eq. 8.2",
    ))

    out.primary_value = out.damage_D
    out.primary_unit = "-"
    return out


# Tabella dettagli costruttivi più frequenti su pali TLC
DETTAGLI_TIPICI_PALI_TLC: dict[str, dict] = {
    "flangia_bullonata_M_perpend": {
        "delta_sigma_C": 71,
        "descrizione": "Bullone in flangia con M_Ed perpendicolare all'asse del bullone",
        "norm_ref": "EN 1993-1-9 Tab. 8.1 Caso 14",
    },
    "saldatura_cordone_dangolo": {
        "delta_sigma_C": 80,
        "descrizione": "Saldatura a cordoni d'angolo continua, perpendicolare allo sforzo",
        "norm_ref": "EN 1993-1-9 Tab. 8.5 Caso 1",
    },
    "saldatura_testa_a_testa_classe_B": {
        "delta_sigma_C": 90,
        "descrizione": "Saldatura testa-testa molata, classe qualità B EN ISO 5817",
        "norm_ref": "EN 1993-1-9 Tab. 8.3 Caso 1 (Cellnex CNP_TS21_002 post-2009)",
    },
    "saldatura_testa_a_testa_lunghezza_max": {
        "delta_sigma_C": 100,
        "descrizione": "Saldatura testa-testa accurata, lunghezza > limite (giunti palo)",
        "norm_ref": "EN 1993-1-9 Tab. 8.3 Caso 2",
    },
    "sezione_liscia_no_intaglio": {
        "delta_sigma_C": 125,
        "descrizione": "Sezione tubolare liscia senza intagli",
        "norm_ref": "EN 1993-1-9 Tab. 8.1 Caso 1",
    },
}
