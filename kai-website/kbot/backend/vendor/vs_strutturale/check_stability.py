"""Verifica stabilità asta compressa+inflessa — EN 1993-1-1 §6.3.

Per pali TLC tubolari cavi (CHS):
  §6.3.1 — instabilità per flessione (compressione pura): N_b,Rd = χ · A · fy / γ_M1
  §6.3.3 — interazione N + M (versione semplificata, no LTB per CHS)

Lunghezza libera di inflessione palo a mensola: L_cr = 2·H (β=2).
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash
from ._sanity import apply_sanity_rules_to_output, sanity_check_enabled
from ._units import dimensional_check_enabled, verify_output_dimensions

import math
from typing import Literal

from pydantic import BaseModel, Field

from .data.profili_chs import chs_proprieta, lookup_chs_commerciale
from .schemas import CalcResult, TraceStep
from .shell_buckling import chi_shell_circular

# Imperfezioni EN 1993-1-1 Tab. 6.2
ALPHA_CURVA = {"a0": 0.13, "a": 0.21, "b": 0.34, "c": 0.49, "d": 0.76}

# Modulo elastico acciaio
E_ACCIAIO_MPa = 210000.0


class CheckStabilityInput(BaseModel):
    # Geometria
    designazione_commerciale: str | None = None
    D_ext_mm: float | None = None
    t_mm: float | None = None
    # Sistema
    L_cr_mm: float = Field(..., description="Lunghezza libera di inflessione")
    curva_instabilita: Literal["a0", "a", "b", "c", "d"] = Field(
        "a",
        description="EN 1993-1-1 Tab. 6.2 — CHS hot-finished: 'a' (S275/S355), 'a0' (S460+), saldati: 'c'",
    )
    # Materiale
    fy_MPa: float = 275.0
    gamma_M1: float = 1.05
    # Sollecitazioni di progetto
    N_Ed_kN: float = Field(0.0, description="Compressione di progetto")
    M_y_Ed_kNm: float = Field(0.0, description="Momento flettente max sull'asta")
    # Coefficienti di interazione (semplificato; default conservativo)
    C_my: float = Field(0.9, description="Coeff. momento equivalente — default 0.9 (cautelativo)")
    quality_class: str = Field(
        "B",
        description="Qualità fabbricazione EN 1993-1-6 Tab. D.2 — rilevante per cl 4",
    )
    is_poligonale: bool = Field(
        False,
        description="True per palo poligonale (α × 0.85, EN 1993-3-1 Annex A)",
    )
    modalita_cautelativa: bool = Field(
        False,
        description="Se True: quality_class='C' forzato + M × 1.10. VS asseverata K2A.",
    )
    fattore_amplificazione_M_vortex: float = Field(1.0, ge=1.0, le=1.5)


class CheckStabilityOutput(CalcResult):
    classe_sezione: int | None = None
    N_cr_kN: float | None = None
    lambda_bar: float | None = None
    chi: float | None = None
    chi_shell: float | None = None
    N_b_Rd_kN: float | None = None
    k_yy: float | None = None
    eta_compressione: float | None = None
    eta_interazione: float | None = None
    verifica_ok: bool = False


def _get_sezione(inp: CheckStabilityInput):
    if inp.designazione_commerciale:
        return lookup_chs_commerciale(inp.designazione_commerciale)
    if inp.D_ext_mm and inp.t_mm:
        return chs_proprieta(inp.D_ext_mm, inp.t_mm)
    raise ValueError("Specificare designazione_commerciale O (D_ext_mm, t_mm)")


def check_tubular_stability(inp: CheckStabilityInput) -> CheckStabilityOutput:
    out = CheckStabilityOutput(tool="check_tubular_stability", inputs_hash=compute_inputs_hash(inp))
    sez = _get_sezione(inp)
    fy = inp.fy_MPa
    gM1 = inp.gamma_M1

    classe = sez.classe_sezione(fy)
    out.classe_sezione = classe
    if classe == 4:
        out.warnings.append("Sezione classe 4: verifica con A_eff non implementata in v1.")

    # MODALITÀ CAUTELATIVA
    quality_used = inp.quality_class
    M_y_Ed_used = inp.M_y_Ed_kNm * inp.fattore_amplificazione_M_vortex
    if inp.modalita_cautelativa:
        quality_used = "C"
        M_y_Ed_used *= 1.10
        out.trace.append(TraceStep(
            label="modalità cautelativa",
            formula="quality_class='C' + M_y × 1.10 (+ vortex)",
            substitution=f"M_y_eff = {M_y_Ed_used:.1f} kN·m",
            value=M_y_Ed_used, unit="kN·m",
            norm_ref="EN 1993-1-1 §5.3.2",
        ))

    # Shell buckling EN 1993-1-6 per classe 4 — applico χ_shell a N_pl,Rk e M_y,Rk
    chi_shell = 1.0
    if classe == 4:
        sh = chi_shell_circular(D_mm=sez.D_ext_mm, t_mm=sez.t_mm, fy_MPa=fy,
                                quality=quality_used, is_poligonale=inp.is_poligonale)
        chi_shell = sh["chi"]
        out.chi_shell = chi_shell
        out.trace.append(TraceStep(
            label="χ_shell (EN 1993-1-6)",
            formula="χ_x per classe 4 — riduce N_pl,Rk e M_y,Rk",
            substitution=f"χ_shell = {chi_shell:.4f} ({sh['regime']})",
            value=chi_shell, unit="-",
            norm_ref=f"EN 1993-1-6 §8.5 + Tab. D.2 (qualità {quality_used})",
        ))

    # N_pl,Rk = A · fy (caratteristico, senza γ) — ridotto se cl 4
    N_pl_Rk = sez.A_mm2 * fy / 1000.0 * chi_shell  # kN

    # Carico critico euleriano
    N_cr = (math.pi ** 2) * E_ACCIAIO_MPa * sez.I_mm4 / (inp.L_cr_mm ** 2) / 1000.0  # kN
    out.N_cr_kN = N_cr
    out.trace.append(TraceStep(
        label="N_cr",
        formula="N_cr = π²·E·I / L_cr²",
        substitution=f"= π²·{E_ACCIAIO_MPa}·{sez.I_mm4:.2e}/{inp.L_cr_mm}² = {N_cr:.1f} kN",
        value=N_cr, unit="kN", norm_ref="EN 1993-1-1 §6.3.1 (Eulero)",
    ))

    # Snellezza adimensionalizzata
    lam_bar = math.sqrt(N_pl_Rk / N_cr) if N_cr > 0 else float("inf")
    out.lambda_bar = lam_bar
    out.trace.append(TraceStep(
        label="λ̄",
        formula="λ̄ = √(A·fy / N_cr) = √(N_pl,Rk / N_cr)",
        substitution=f"= √({N_pl_Rk:.1f}/{N_cr:.1f}) = {lam_bar:.4f}",
        value=lam_bar, unit="-", norm_ref="EN 1993-1-1 §6.3.1.2 eq. 6.50",
    ))

    # Fattore di riduzione χ
    alpha = ALPHA_CURVA[inp.curva_instabilita]
    if lam_bar <= 0.2:
        chi = 1.0
    else:
        phi = 0.5 * (1.0 + alpha * (lam_bar - 0.2) + lam_bar ** 2)
        chi = 1.0 / (phi + math.sqrt(phi ** 2 - lam_bar ** 2))
        chi = min(chi, 1.0)
    out.chi = chi
    out.trace.append(TraceStep(
        label="χ",
        formula=f"φ = 0.5·[1 + α(λ̄−0.2) + λ̄²] ; χ = 1/(φ+√(φ²−λ̄²))  (curva {inp.curva_instabilita}, α={alpha})",
        substitution=f"λ̄={lam_bar:.4f} → χ={chi:.4f}",
        value=chi, unit="-", norm_ref="EN 1993-1-1 §6.3.1.2 eq. 6.49 + Tab. 6.1",
    ))

    # Resistenza all'instabilità per compressione
    N_b_Rd = chi * sez.A_mm2 * fy / gM1 / 1000.0  # kN
    out.N_b_Rd_kN = N_b_Rd
    out.trace.append(TraceStep(
        label="N_b,Rd",
        formula="N_b,Rd = χ·A·fy/γ_M1",
        substitution=f"= {chi:.4f}·{sez.A_mm2:.1f}·{fy}/{gM1}/1000 = {N_b_Rd:.2f} kN",
        value=N_b_Rd, unit="kN", norm_ref="EN 1993-1-1 §6.3.1.1 eq. 6.47",
    ))

    eta_c = abs(inp.N_Ed_kN) / N_b_Rd if N_b_Rd > 0 else float("inf")
    out.eta_compressione = eta_c

    # Interazione N+M EN 1993-1-1 §6.3.3 (semplificato — Annex B Tab. B.1)
    # k_yy = C_my · [1 + (λ̄ − 0.2)·N_Ed/(χ·N_Rk/γ_M1)], limitato sup a C_my·[1+0.8·n_ed]
    n_ed = abs(inp.N_Ed_kN) / (chi * N_pl_Rk / gM1)
    k_yy_a = inp.C_my * (1.0 + (lam_bar - 0.2) * n_ed)
    k_yy_b = inp.C_my * (1.0 + 0.8 * n_ed)
    k_yy = min(k_yy_a, k_yy_b)
    out.k_yy = k_yy
    out.trace.append(TraceStep(
        label="k_yy",
        formula="k_yy = C_my·[1 + (λ̄−0.2)·n_Ed] ≤ C_my·[1 + 0.8·n_Ed]",
        substitution=f"n_Ed={n_ed:.3f}, k_yy={k_yy:.4f}",
        value=k_yy, unit="-", norm_ref="EN 1993-1-1 Annex B Tab. B.1",
    ))

    # M_y,Rk — applico χ_shell anche al modulo se cl 4
    if classe <= 2:
        M_y_Rk = sez.W_pl_mm3 * fy / 1.0e6
    else:
        M_y_Rk = sez.W_el_mm3 * fy / 1.0e6
    M_y_Rk = M_y_Rk * chi_shell   # cl 4 → riduzione shell anche su M

    # Verifica interazione N+M
    # Cl 1-3: equazione 6.61 EN 1993-1-1 lineare (membrature ordinarie)
    # Cl 4: equazione 8.40 EN 1993-1-6 esponenziale (shell — non sommatoria lineare)
    term_N = abs(inp.N_Ed_kN) / (chi * N_pl_Rk / gM1)
    term_M = k_yy * abs(M_y_Ed_used) / (M_y_Rk / gM1)

    if classe == 4:
        # EN 1993-1-6 §8.7 eq. 8.40 con esponente k_x=1.25 (tipico per long shells)
        # Riconosce che la distribuzione di tensione da M non è uniforme sulla
        # circonferenza → meno critico della sola compressione. k_xi consigliato 1.25.
        k_xi = 1.25
        eta_int = term_N ** k_xi + term_M ** k_xi
        norm = "EN 1993-1-6 §8.7 eq. 8.40 — interazione esponenziale shell"
        formula = f"(N_Ed/N_Rd)^{k_xi} + (M_Ed/M_Rd)^{k_xi} ≤ 1  [cl 4 shell]"
    else:
        eta_int = term_N + term_M
        norm = "EN 1993-1-1 §6.3.3 eq. 6.61 — interazione lineare"
        formula = "N_Ed/(χ·N_Rk/γ_M1) + k_yy·M_y_Ed/(M_y_Rk/γ_M1) ≤ 1"

    out.eta_interazione = eta_int
    out.verifica_ok = eta_int <= 1.0 and eta_c <= 1.0

    out.trace.append(TraceStep(
        label="η interazione",
        formula=formula,
        substitution=(
            f"term_N={term_N:.3f}, term_M={term_M:.3f} → η={eta_int:.3f} "
            f"{'OK' if out.verifica_ok else 'NON VERIFICATO'}"
        ),
        value=eta_int, unit="-", norm_ref=norm,
    ))

    out.primary_value = eta_int
    out.primary_unit = "-"
    if dimensional_check_enabled():
        for _w in verify_output_dimensions(out.model_dump(), out.tool):
            out.warnings.append(f"[dim] {_w}")
    if sanity_check_enabled():
        out.warnings.extend(apply_sanity_rules_to_output(out.tool, out.model_dump()))
    return out
