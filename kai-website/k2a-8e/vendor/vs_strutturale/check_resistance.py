"""Verifica resistenza sezione tubolare cava — NTC 2018 §4.2.4.1.2 / EN 1993-1-1 §6.2.

Implementa:
- N_pl,Rd (resistenza plastica trazione/compressione)
- M_el,Rd, M_pl,Rd (momento elastico e plastico)
- V_pl,Rd (taglio plastico)
- Interazione N+M (EN 1993-1-1 eq. 6.31 per sezioni tubolari cave)
- Riduzione fy in presenza di taglio significativo

Convenzioni segni: N positivo se compressione, M momento flettente kN·m, V kN.
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash
from ._sanity import apply_sanity_rules_to_output, sanity_check_enabled
from ._units import dimensional_check_enabled, verify_output_dimensions

import math

from pydantic import BaseModel, Field

from .data.profili_chs import chs_proprieta, lookup_chs_commerciale
from .schemas import CalcResult, TraceStep
from .shell_buckling import chi_shell_circular


class CheckResistanceInput(BaseModel):
    # Geometria — tre alternative
    designazione_commerciale: str | None = None
    D_ext_mm: float | None = None
    t_mm: float | None = None
    # Materiale
    fy_MPa: float = 275.0
    gamma_M0: float = 1.05
    FC: float = Field(
        1.0,
        ge=1.0, le=1.35,
        description=(
            "Fattore di confidenza per strutture esistenti (Circ. NTC §C8). "
            "LC1=1.35, LC2=1.20, LC3=1.00. Riduce fy → fy/FC. Default 1.0 (nuovo)."
        ),
    )
    quality_class: str = Field(
        "B",
        description=(
            "Qualità fabbricazione EN 1993-1-6 Tab. D.2 (rilevante per cl 4): "
            "'A'=excellent (α=0.83), 'B'=high (α=0.62), 'C'=normal (α=0.42, **default cautelativo "
            "per pali poligonali saldati**). Sovrascritta a 'C' automaticamente se modalita_cautelativa=True."
        ),
    )
    is_poligonale: bool = Field(
        False,
        description=(
            "True per pali a sezione poligonale (saldature longitudinali → α × 0.85). "
            "EN 1993-3-1 Annex A — riduzione imperfezioni rispetto a CHS perfetto."
        ),
    )
    modalita_cautelativa: bool = Field(
        False,
        description=(
            "Se True: forza quality_class='C', amplifica M_Ed per imperfezioni (×1.10), "
            "applica ghiaccio anche se non obbligatorio LG. Da usare per VS asseverata "
            "K2A dove si vuole MASSIMA cautela. η risultante più ALTO."
        ),
    )
    fattore_amplificazione_M_vortex: float = Field(
        1.0, ge=1.0, le=1.5,
        description=(
            "Moltiplicatore M_Ed per amplificazione da vortex shedding. Se "
            "check_vortex_shedding segnala risonanza, il chiamante passa qui il fattore "
            "(tipico 1.10-1.30)."
        ),
    )
    # Sollecitazioni di progetto (SLU)
    N_Ed_kN: float = Field(0.0, description="Forza assiale, + compressione")
    M_Ed_kNm: float = Field(0.0, description="Momento flettente")
    V_Ed_kN: float = Field(0.0, description="Taglio")


class CheckResistanceOutput(CalcResult):
    classe_sezione: int | None = None
    N_pl_Rd_kN: float | None = None
    M_el_Rd_kNm: float | None = None
    M_pl_Rd_kNm: float | None = None
    M_N_Rd_kNm: float | None = None     # M ridotto per presenza N
    M_V_Rd_kNm: float | None = None     # M ridotto per presenza V (Issue #001, eq.6.29)
    rho_taglio: float = 0.0             # ρ riduzione per taglio (0 se η_V ≤ 0.5)
    V_pl_Rd_kN: float | None = None
    eta_N: float | None = None          # N_Ed / N_pl_Rd
    eta_V: float | None = None
    eta_M_N: float | None = None        # interazione N+M
    eta_globale: float | None = None
    verifica_ok: bool = False
    # Shell buckling EN 1993-1-6 (solo cl 4)
    chi_shell: float | None = None
    lambda_bar_shell: float | None = None
    shell_regime: str = ""


def _get_sezione(inp: CheckResistanceInput):
    if inp.designazione_commerciale:
        return lookup_chs_commerciale(inp.designazione_commerciale)
    if inp.D_ext_mm and inp.t_mm:
        return chs_proprieta(inp.D_ext_mm, inp.t_mm)
    raise ValueError("Specificare designazione_commerciale O (D_ext_mm, t_mm)")


def check_tubular_resistance(inp: CheckResistanceInput) -> CheckResistanceOutput:
    out = CheckResistanceOutput(tool="check_tubular_resistance", inputs_hash=compute_inputs_hash(inp))
    sez = _get_sezione(inp)
    fy_k = inp.fy_MPa
    fy = fy_k / inp.FC   # FC applicato per strutture esistenti
    gM0 = inp.gamma_M0

    # MODALITÀ CAUTELATIVA — override parametri verso il sicuro
    quality_used = inp.quality_class
    M_Ed_used = inp.M_Ed_kNm * inp.fattore_amplificazione_M_vortex
    if inp.modalita_cautelativa:
        quality_used = "C"  # forza imperfezioni alte
        M_Ed_used *= 1.10   # +10% per incertezza imperfezioni
        out.trace.append(TraceStep(
            label="modalità cautelativa",
            formula="quality_class='C' + M_Ed × 1.10 (+ vortex)",
            substitution=f"M_Ed_eff = {inp.M_Ed_kNm} × {inp.fattore_amplificazione_M_vortex} × 1.10 = {M_Ed_used:.1f} kN·m",
            value=M_Ed_used, unit="kN·m",
            norm_ref="EN 1993-1-1 §5.3.2 + EN 1993-1-6 imperfezioni esplicite",
        ))
    elif inp.fattore_amplificazione_M_vortex > 1.0:
        out.trace.append(TraceStep(
            label="amplificazione vortex shedding",
            formula="M_Ed_eff = M_Ed × k_vortex",
            substitution=f"M_Ed_eff = {inp.M_Ed_kNm} × {inp.fattore_amplificazione_M_vortex} = {M_Ed_used:.1f} kN·m",
            value=M_Ed_used, unit="kN·m",
            norm_ref="CNR-DT 207 §3.3 + EN 1993-3-1 Annex B amplificazione vortex",
        ))
    if inp.FC > 1.0:
        out.trace.append(TraceStep(
            label="FC (struttura esistente)",
            formula="fy_d = fy_k / FC",
            substitution=f"fy_k={fy_k}, FC={inp.FC} → fy_d={fy:.2f} MPa",
            value=fy, unit="MPa", norm_ref="Circ. NTC 2018 §C8.5",
        ))

    # Classificazione
    classe = sez.classe_sezione(fy)
    out.classe_sezione = classe
    out.trace.append(TraceStep(
        label="classe sezione",
        formula="d/t vs 50ε² / 70ε² / 90ε², ε=√(235/fy)",
        substitution=f"d/t={sez.D_ext_mm/sez.t_mm:.1f}, fy={fy} → classe {classe}",
        value=classe, unit="-", norm_ref="EN 1993-1-1 §5.5 Tab. 5.2",
    ))

    # N_pl,Rd  (sezione cl 1-2-3: A piena; cl 4: applico χ_shell EN 1993-1-6)
    N_pl_full = sez.A_mm2 * fy / gM0 / 1000.0  # kN — capacità senza riduzione shell

    chi_shell = 1.0
    if classe == 4:
        shell = chi_shell_circular(
            D_mm=sez.D_ext_mm, t_mm=sez.t_mm, fy_MPa=fy, quality=quality_used,
            is_poligonale=inp.is_poligonale,
        )
        chi_shell = shell["chi"]
        out.chi_shell = chi_shell
        out.lambda_bar_shell = shell["lambda_bar_x"]
        out.shell_regime = shell["regime"]
        out.trace.append(TraceStep(
            label="shell buckling χ_x (EN 1993-1-6)",
            formula=(
                "σ_x,Rcr = 0.605·E·t/r ; λ̄_x = √(fy/σ_x,Rcr) ; "
                "χ_x curva imperfezione (α={α}, β=0.6, η=1)"
            ).replace("{α}", f"{shell['alpha_x']}"),
            substitution=(
                f"σ_x,Rcr={shell['sigma_x_Rcr_MPa']:.1f} MPa, λ̄={shell['lambda_bar_x']:.3f}, "
                f"λ̄_p={shell['lambda_bar_p']:.3f} → χ={chi_shell:.4f} ({shell['regime']})"
            ),
            value=chi_shell, unit="-",
            norm_ref="EN 1993-1-6 §8.5 + Annex D, Tab. D.1 + D.2 (qualità {q})".replace(
                "{q}", inp.quality_class
            ),
        ))

    N_pl = N_pl_full * chi_shell   # ridotta per classe 4
    out.N_pl_Rd_kN = N_pl
    out.trace.append(TraceStep(
        label="N_pl,Rd", formula="N_pl,Rd = A·fy/γ_M0",
        substitution=f"= {sez.A_mm2:.1f}·{fy}/{gM0} = {N_pl:.2f} kN",
        value=N_pl, unit="kN", norm_ref="EN 1993-1-1 §6.2.4 eq. 6.10",
    ))

    # M_el,Rd e M_pl,Rd — applico χ_shell se classe 4
    M_el_full = sez.W_el_mm3 * fy / gM0 / 1.0e6
    M_pl_full = sez.W_pl_mm3 * fy / gM0 / 1.0e6
    M_el = M_el_full * chi_shell
    M_pl = M_pl_full * chi_shell    # cautelativo: stessa χ_x per N e M
    out.M_el_Rd_kNm = M_el
    out.M_pl_Rd_kNm = M_pl
    out.trace.append(TraceStep(
        label="M_pl,Rd / M_el,Rd",
        formula="M_pl,Rd = W_pl·fy/γ_M0 ; M_el,Rd = W_el·fy/γ_M0",
        substitution=f"M_pl,Rd={M_pl:.2f} kN·m, M_el,Rd={M_el:.2f} kN·m",
        value=M_pl, unit="kN·m", norm_ref="EN 1993-1-1 §6.2.5 eq. 6.13",
    ))

    # V_pl,Rd per sezione tubolare cava: A_v = 2A/π
    A_v = 2.0 * sez.A_mm2 / math.pi
    V_pl = A_v * fy / (math.sqrt(3.0) * gM0) / 1000.0  # kN
    out.V_pl_Rd_kN = V_pl
    out.trace.append(TraceStep(
        label="V_pl,Rd", formula="V_pl,Rd = A_v·fy/(√3·γ_M0), A_v=2A/π per CHS",
        substitution=f"A_v={A_v:.1f} mm², V_pl,Rd={V_pl:.2f} kN",
        value=V_pl, unit="kN", norm_ref="EN 1993-1-1 §6.2.6 eq. 6.18",
    ))

    # Verifica taglio (eq. 6.17)
    eta_V = abs(inp.V_Ed_kN) / V_pl
    out.eta_V = eta_V

    # Riduzione resistenza flessionale per V > 0.5·V_pl,Rd (Issue #001, eq. 6.29)
    # ISSUE #001 FIX: ρ era calcolato ma NON applicato a M (errore non-cautelativo).
    # Ora M_pl/M_el sono ridotti di (1−ρ) PRIMA dell'interazione N-M, così la
    # riduzione per taglio compone correttamente anche con lo sforzo assiale.
    rho = 0.0
    if eta_V > 0.5:
        rho = (2.0 * eta_V - 1.0) ** 2
        out.trace.append(TraceStep(
            label="ρ (riduzione per V)", formula="ρ = (2·V_Ed/V_pl,Rd − 1)²",
            substitution=f"V_Ed/V_pl,Rd={eta_V:.3f} → ρ={rho:.4f}",
            value=rho, unit="-", norm_ref="EN 1993-1-1 §6.2.10 eq. 6.29",
        ))
    out.rho_taglio = rho

    # Resistenze flessionali ridotte per taglio (M_V,Rd = (1−ρ)·M_Rd)
    M_pl_V = (1.0 - rho) * M_pl
    M_el_V = (1.0 - rho) * M_el

    # Per cl 1-2: M_pl resistenza; per cl 3: M_el; per cl 4: M_eff (cautelativo M_el)
    M_V_Rd = M_pl_V if classe <= 2 else M_el_V
    out.M_V_Rd_kNm = M_V_Rd
    if rho > 0.0:
        out.trace.append(TraceStep(
            label="M_V,Rd (riduzione taglio)",
            formula="M_V,Rd = (1 − ρ)·M_Rd",
            substitution=f"(1−{rho:.4f})·{(M_pl if classe <= 2 else M_el):.2f} = {M_V_Rd:.2f} kN·m",
            value=M_V_Rd, unit="kN·m", norm_ref="EN 1993-1-1 §6.2.10 eq. 6.29",
        ))

    # Interazione N+M per sezioni tubolari cl 1-2 (EN 1993-1-1 eq. 6.31)
    # M_N,Rd = M_V,Rd · (1 − n^1.7), n = N_Ed/N_pl,Rd  (M_V,Rd già ridotto per taglio)
    n = abs(inp.N_Ed_kN) / N_pl
    out.eta_N = n
    if classe <= 2:
        if n >= 1.0:
            M_N_Rd = 0.0
        else:
            M_N_Rd = M_pl_V * (1.0 - n ** 1.7)
        formula_int = "M_N,Rd = M_V,Rd · (1 − n^1.7), n=N_Ed/N_pl,Rd  [CHS, cl 1-2]"
    else:
        # Per cl 3-4 verifica elastica lineare
        M_N_Rd = M_el_V * max(0.0, 1.0 - n)
        formula_int = "M_N,Rd = M_V,Rd · (1 − n) [cl 3-4, lineare cautelativa]"

    out.M_N_Rd_kNm = M_N_Rd

    out.trace.append(TraceStep(
        label="M_N,Rd", formula=formula_int,
        substitution=f"n={n:.3f}, M_N,Rd={M_N_Rd:.2f} kN·m",
        value=M_N_Rd, unit="kN·m", norm_ref="EN 1993-1-1 §6.2.9 eq. 6.31",
    ))

    # Coefficiente di sfruttamento η_M_N
    eta_M_N = abs(M_Ed_used) / M_N_Rd if M_N_Rd > 0 else float("inf")
    out.eta_M_N = eta_M_N

    # η globale (max di N, V, M+N)
    eta_glob = max(n, eta_V, eta_M_N)
    out.eta_globale = eta_glob
    out.verifica_ok = eta_glob <= 1.0

    out.trace.append(TraceStep(
        label="η globale",
        formula="η = max(N_Ed/N_pl,Rd, V_Ed/V_pl,Rd, M_Ed/M_N,Rd)",
        substitution=(
            f"η_N={n:.3f}, η_V={eta_V:.3f}, η_M_N={eta_M_N:.3f} → η={eta_glob:.3f} "
            f"{'OK' if out.verifica_ok else 'NON VERIFICATO'}"
        ),
        value=eta_glob, unit="-",
        norm_ref="NTC 2018 §4.2.4.1.2 + EN 1993-1-1 §6.2",
    ))

    out.primary_value = eta_glob
    out.primary_unit = "-"

    if dimensional_check_enabled():
        for _w in verify_output_dimensions(out.model_dump(), out.tool):
            out.warnings.append(f"[dim] {_w}")
    if sanity_check_enabled():
        out.warnings.extend(apply_sanity_rules_to_output(out.tool, out.model_dump()))
    return out
