"""Spettro di risposta NTC 2018 §3.2.

Calcolo S_e(T) elastico e S_d(T) di progetto dato:
- ag, F0, Tc* del sito (input — da reticolo INGV in v1.1)
- categoria sottosuolo (A-E)
- categoria topografica (T1-T4)
- smorzamento ξ (default 5%)
- fattore di comportamento q (default 1.0 per elastico)
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash
from ._sanity import apply_sanity_rules_to_output, sanity_check_enabled
from ._units import dimensional_check_enabled, verify_output_dimensions

import math

from pydantic import BaseModel, Field

from .data.ntc_sismica import (
    NTC_PARAMETRI_SOTTOSUOLO,
    NTC_SS_FORMULA,
    NTC_TOPOGRAFICO,
)
from .schemas import CalcResult, TraceStep


class SeismicSpectrumInput(BaseModel):
    """Input spettro NTC 2018 §3.2."""
    ag_g: float = Field(..., ge=0, le=1.0, description="ag/g — accelerazione orizzontale max [-]")
    F0: float = Field(..., ge=2.0, le=3.5, description="F0 — fattore amplificazione spettrale max")
    Tc_star_s: float = Field(..., gt=0, le=1.0, description="Tc* — periodo inizio tratto a vel costante [s]")
    categoria_sottosuolo: str = Field(..., description="A|B|C|D|E (NTC Tab. 3.2.II)")
    categoria_topografica: str = Field("T1", description="T1|T2|T3|T4 (NTC Tab. 3.2.IV)")
    smorzamento_pct: float = Field(5.0, gt=0, le=28.0, description="ξ% — default 5%")
    fattore_comportamento_q: float = Field(1.0, ge=1.0, le=6.0, description="q per spettro progetto")
    periodi_T_s: list[float] = Field(
        default_factory=lambda: [0.0, 0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 4.0],
        description="Periodi T [s] in cui valutare lo spettro",
    )


class SpectrumPoint(BaseModel):
    T_s: float
    S_e_g: float
    S_d_g: float


class SeismicSpectrumOutput(CalcResult):
    S_S: float | None = None
    C_C: float | None = None
    S_T: float | None = None
    S: float | None = None
    T_B_s: float | None = None
    T_C_s: float | None = None
    T_D_s: float | None = None
    eta_smorzamento: float | None = None
    spectrum: list[SpectrumPoint] = Field(default_factory=list)


def compute_seismic_spectrum(inp: SeismicSpectrumInput) -> SeismicSpectrumOutput:
    out = SeismicSpectrumOutput(tool="seismic_spectrum", inputs_hash=compute_inputs_hash(inp))

    if inp.ag_g > 0.30:
        out.warnings.append(
            f"ag/g={inp.ag_g} oltre validation set v1 (≤0.30g). Calcolo eseguibile."
        )

    # S_S — amplificazione stratigrafica (NTC eq. 3.2.5)
    cat = inp.categoria_sottosuolo
    a_ss, b_ss = NTC_SS_FORMULA[cat]
    p = NTC_PARAMETRI_SOTTOSUOLO[cat]
    S_S_raw = a_ss - b_ss * inp.F0 * inp.ag_g
    S_S = max(p["Ss_min"], min(p["Ss_max"], S_S_raw))
    out.S_S = S_S
    out.trace.append(TraceStep(
        label="S_S", formula=f"S_S = {a_ss} − {b_ss}·F0·ag/g, vincolato a [{p['Ss_min']}, {p['Ss_max']}]",
        substitution=f"S_S = {a_ss} − {b_ss}·{inp.F0}·{inp.ag_g} = {S_S_raw:.3f} → clamp = {S_S:.3f}",
        value=S_S, unit="-", norm_ref="NTC 2018 §3.2.3.2.1 — eq. 3.2.5, Tab. 3.2.IV",
    ))

    # C_C — periodo NTC eq. 3.2.6
    a_cc, b_cc = p["Cc_coeff"]
    C_C = a_cc * (inp.Tc_star_s ** b_cc)
    out.C_C = C_C
    out.trace.append(TraceStep(
        label="C_C", formula=f"C_C = {a_cc}·(Tc*)^{b_cc}",
        substitution=f"C_C = {a_cc}·({inp.Tc_star_s})^{b_cc} = {C_C:.4f}",
        value=C_C, unit="-", norm_ref="NTC 2018 §3.2.3.2.1 — eq. 3.2.6, Tab. 3.2.IV",
    ))

    # S_T — topografico
    S_T = NTC_TOPOGRAFICO[inp.categoria_topografica]
    out.S_T = S_T
    out.trace.append(TraceStep(
        label="S_T", formula="S_T = lookup(cat_topografica)",
        substitution=f"cat={inp.categoria_topografica} → S_T = {S_T}",
        value=S_T, unit="-", norm_ref="NTC 2018 §3.2.3.2.1 — Tab. 3.2.V",
    ))

    # S complessivo
    S = S_S * S_T
    out.S = S
    out.trace.append(TraceStep(
        label="S", formula="S = S_S · S_T",
        substitution=f"S = {S_S:.3f} · {S_T} = {S:.3f}",
        value=S, unit="-", norm_ref="NTC 2018 §3.2.3.2.1",
    ))

    # Periodi caratteristici
    T_C = C_C * inp.Tc_star_s
    T_B = T_C / 3.0
    T_D = 4.0 * inp.ag_g + 1.6
    out.T_B_s, out.T_C_s, out.T_D_s = T_B, T_C, T_D
    out.trace.append(TraceStep(
        label="T_B/T_C/T_D",
        formula="T_C = C_C·Tc*, T_B = T_C/3, T_D = 4·ag/g + 1.6",
        substitution=f"T_C={T_C:.3f}s, T_B={T_B:.3f}s, T_D={T_D:.3f}s",
        value=T_C, unit="s", norm_ref="NTC 2018 §3.2.3.2.1 — eq. 3.2.7-9",
    ))

    # eta — fattore smorzamento (eq. 3.2.4)
    eta = math.sqrt(10.0 / (5.0 + inp.smorzamento_pct))
    eta = max(eta, 0.55)
    out.eta_smorzamento = eta
    out.trace.append(TraceStep(
        label="η", formula="η = √(10/(5+ξ%)) ≥ 0.55",
        substitution=f"ξ={inp.smorzamento_pct}% → η = {eta:.4f}",
        value=eta, unit="-", norm_ref="NTC 2018 §3.2.3.2.1 — eq. 3.2.4",
    ))

    # Spettro elastico S_e(T) — NTC eq. 3.2.10
    def S_e(T: float) -> float:
        ag = inp.ag_g  # g
        if T < T_B:
            return ag * S * eta * inp.F0 * (T / T_B + 1.0 / (eta * inp.F0) * (1.0 - T / T_B))
        if T < T_C:
            return ag * S * eta * inp.F0
        if T < T_D:
            return ag * S * eta * inp.F0 * (T_C / T)
        return ag * S * eta * inp.F0 * (T_C * T_D / (T * T))

    # Spettro di progetto S_d(T) = S_e(T) / q, con limite inferiore 0.2·ag
    spectrum: list[SpectrumPoint] = []
    for T in inp.periodi_T_s:
        se = S_e(T)
        sd = max(se / inp.fattore_comportamento_q, 0.2 * inp.ag_g)
        spectrum.append(SpectrumPoint(T_s=T, S_e_g=se, S_d_g=sd))
    out.spectrum = spectrum

    out.trace.append(TraceStep(
        label="S_e(T), S_d(T)",
        formula="ramo costante: S_e = ag·S·η·F0 ; S_d = max(S_e/q, 0.2·ag)",
        substitution=f"valutato in {len(inp.periodi_T_s)} punti, picco plateau = {inp.ag_g*S*eta*inp.F0:.4f}g",
        value=inp.ag_g * S * eta * inp.F0, unit="g",
        norm_ref="NTC 2018 §3.2.3.2.1 — eq. 3.2.10 / §3.2.3.5",
    ))

    out.primary_value = inp.ag_g * S * eta * inp.F0
    out.primary_unit = "g"
    if dimensional_check_enabled():
        for _w in verify_output_dimensions(out.model_dump(), out.tool):
            out.warnings.append(f"[dim] {_w}")
    if sanity_check_enabled():
        out.warnings.extend(apply_sanity_rules_to_output(out.tool, out.model_dump()))
    return out
