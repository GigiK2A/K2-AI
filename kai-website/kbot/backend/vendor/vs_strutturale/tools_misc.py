"""Tool MCP atomici aggiunti in v0.4 — dai gap delle skill VS K2A.

- ice_load           (CNR-DT 207 + iliad LG manicotto 10 mm)
- check_sliding      (scorrimento, NTC §6.4.2 stand-alone)
- check_overturning  (ribaltamento EQU, NTC §2.6.1 stand-alone)
- check_section_class (classificazione EN 1993-1-1 §5.5 stand-alone)
- get_combination_factors (lookup ψ_0/ψ_1/ψ_2 NTC Tab. 2.5.I)
- distribute_anchor_reactions (T per bullone in flangia anulare M+N+V)
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash

import math
from typing import Literal

from pydantic import BaseModel, Field

from .data.profili_chs import lookup_chs_commerciale
from .schemas import CalcResult, TraceStep


# ---------------------------------------------------------------------------
# ice_load — manicotto ghiaccio CNR-DT 207 §3.6 + iliad LG
# ---------------------------------------------------------------------------

class IceLoadInput(BaseModel):
    diametro_elemento_mm: float = Field(..., gt=0)
    lunghezza_elemento_m: float = Field(..., gt=0)
    spessore_ghiaccio_mm: float = Field(
        10.0, ge=0, le=50,
        description="Tipico: iliad LG=10 mm, CNR-DT 207=variabile zona climatica",
    )
    densita_ghiaccio_kg_m3: float = Field(700.0, ge=600, le=900)
    zona_climatica: Literal["I", "II", "III"] = Field(
        "II",
        description=(
            "Zona climatica CNR-DT 207: I (assente), II (rara, t=10mm), "
            "III (frequente, t=25mm). Default II conforme iliad LG"
        ),
    )


class IceLoadOutput(CalcResult):
    diametro_con_ghiaccio_mm: float | None = None
    peso_per_metro_kN_m: float | None = None
    peso_totale_kN: float | None = None
    area_frontale_aumentata_m2: float | None = None


def ice_load(inp: IceLoadInput) -> IceLoadOutput:
    out = IceLoadOutput(tool="ice_load", inputs_hash=compute_inputs_hash(inp))
    D = inp.diametro_elemento_mm
    s = inp.spessore_ghiaccio_mm
    D_iced = D + 2.0 * s
    # Area anello di ghiaccio per unità di lunghezza
    A_ghiaccio_mm2 = math.pi / 4.0 * (D_iced**2 - D**2)
    peso_per_m = A_ghiaccio_mm2 * 1e-6 * inp.densita_ghiaccio_kg_m3 * 9.81 / 1000.0  # kN/m
    peso_tot = peso_per_m * inp.lunghezza_elemento_m
    # Area frontale aumentata (ghiaccio espone più superficie al vento)
    delta_area = (D_iced - D) / 1000.0 * inp.lunghezza_elemento_m  # m²

    out.diametro_con_ghiaccio_mm = D_iced
    out.peso_per_metro_kN_m = peso_per_m
    out.peso_totale_kN = peso_tot
    out.area_frontale_aumentata_m2 = delta_area

    out.trace.append(TraceStep(
        label="manicotto ghiaccio",
        formula="D' = D + 2s ; W = A_anello · ρ · g · L",
        substitution=(
            f"D={D}mm, s={s}mm, ρ={inp.densita_ghiaccio_kg_m3} kg/m³ → "
            f"D'={D_iced}mm, peso={peso_per_m:.3f} kN/m, ΔA_front={delta_area:.3f} m²"
        ),
        value=peso_per_m, unit="kN/m",
        norm_ref=(
            f"CNR-DT 207 §3.6 (zona {inp.zona_climatica}) + iliad LG VS 1.5 "
            "(manicotto 10mm prescritto)"
        ),
    ))
    out.primary_value = peso_per_m
    out.primary_unit = "kN/m"
    return out


# ---------------------------------------------------------------------------
# check_sliding — scorrimento alla base
# ---------------------------------------------------------------------------

class CheckSlidingInput(BaseModel):
    N_Ed_kN: float = Field(..., gt=0, description="Carico verticale (compressione)")
    H_Ed_kN: float = Field(..., description="Forza orizzontale")
    phi_prime_deg: float = Field(..., gt=0, le=45)
    delta_attrito_factor: float = Field(
        2.0 / 3.0, ge=0.5, le=1.0,
        description="δ/φ — interfaccia plinto/terreno (2/3 default NTC)",
    )
    gamma_phi: float = 1.25
    gamma_R3: float = 1.1
    c_a_kPa: float = Field(0.0, ge=0, description="Adesione plinto-terreno, default 0")
    A_base_m2: float = Field(0.0, ge=0, description="Area base, solo se c_a > 0")


class CheckSlidingOutput(CalcResult):
    H_Rd_kN: float | None = None
    eta: float | None = None
    verifica_ok: bool = False


def check_sliding(inp: CheckSlidingInput) -> CheckSlidingOutput:
    out = CheckSlidingOutput(tool="check_sliding", inputs_hash=compute_inputs_hash(inp))
    phi_d = math.atan(math.tan(math.radians(inp.phi_prime_deg)) / inp.gamma_phi)
    delta_d = math.atan(math.tan(phi_d) * inp.delta_attrito_factor)
    H_Rd_attrito = inp.N_Ed_kN * math.tan(delta_d) / inp.gamma_R3
    H_Rd_coesione = inp.c_a_kPa * inp.A_base_m2 / inp.gamma_R3
    H_Rd = H_Rd_attrito + H_Rd_coesione
    eta = abs(inp.H_Ed_kN) / H_Rd if H_Rd > 0 else float("inf")
    out.H_Rd_kN = H_Rd
    out.eta = eta
    out.verifica_ok = eta <= 1.0
    out.trace.append(TraceStep(
        label="scorrimento",
        formula="H_Rd = N_Ed·tan(δ_d)/γ_R3 + c_a·A/γ_R3 ; η=H_Ed/H_Rd",
        substitution=(
            f"φ_d={math.degrees(phi_d):.2f}°, δ_d={math.degrees(delta_d):.2f}°, "
            f"H_Rd={H_Rd:.2f} kN → η={eta:.3f}"
        ),
        value=eta, unit="-",
        norm_ref="NTC 2018 §6.4.2.1 + Tab. 6.4.I (A1+M2+R3)",
    ))
    out.primary_value = eta
    return out


# ---------------------------------------------------------------------------
# check_overturning_equ — ribaltamento equilibrio
# ---------------------------------------------------------------------------

class CheckOverturningInput(BaseModel):
    M_ribaltante_kNm: float = Field(..., description="Caratteristico (no γ)")
    H_Ed_kNm_aggiuntivo: float = Field(
        0.0, description="H · h_braccio extra (se non già in M_rib)"
    )
    G_stabilizzante_kN: float = Field(..., gt=0)
    braccio_stabilizzante_m: float = Field(
        ..., gt=0, description="Distanza linea applicazione G dal punto di ribaltamento (≈ L/2)"
    )
    gamma_G_fav: float = Field(0.9, description="NTC Tab. 2.6.I EQU")
    gamma_G_sfav: float = Field(1.1)


class CheckOverturningOutput(CalcResult):
    M_stab_d_kNm: float | None = None
    M_rib_d_kNm: float | None = None
    eta: float | None = None
    coefficiente_sicurezza: float | None = None
    verifica_ok: bool = False


def check_overturning(inp: CheckOverturningInput) -> CheckOverturningOutput:
    out = CheckOverturningOutput(tool="check_overturning_equ", inputs_hash=compute_inputs_hash(inp))
    M_stab = inp.G_stabilizzante_kN * inp.braccio_stabilizzante_m * inp.gamma_G_fav
    M_rib = (inp.M_ribaltante_kNm + inp.H_Ed_kNm_aggiuntivo) * inp.gamma_G_sfav
    eta = M_rib / M_stab if M_stab > 0 else float("inf")
    SF = 1.0 / eta if eta > 0 else float("inf")
    out.M_stab_d_kNm = M_stab
    out.M_rib_d_kNm = M_rib
    out.eta = eta
    out.coefficiente_sicurezza = SF
    out.verifica_ok = eta <= 1.0
    out.trace.append(TraceStep(
        label="ribaltamento EQU",
        formula="M_stab = γ_G,fav · G · b ; M_rib_d = γ_G,sfav · (M_rib + H·h)",
        substitution=(
            f"M_stab={M_stab:.1f}, M_rib_d={M_rib:.1f} → η={eta:.3f}, SF={SF:.2f}"
        ),
        value=eta, unit="-",
        norm_ref="NTC 2018 §2.6.1 EQU + Tab. 2.6.I",
    ))
    out.primary_value = eta
    return out


# ---------------------------------------------------------------------------
# check_section_class — classificazione sezione stand-alone
# ---------------------------------------------------------------------------

class CheckSectionClassInput(BaseModel):
    tipo: Literal["CHS", "poligonale"] = "CHS"
    designazione_commerciale: str | None = None
    D_ext_mm: float | None = None
    t_mm: float | None = None
    fy_MPa: float = 275.0


class CheckSectionClassOutput(CalcResult):
    classe: int | None = None
    rapporto_d_su_t: float | None = None
    epsilon: float | None = None
    limite_C1: float | None = None
    limite_C2: float | None = None
    limite_C3: float | None = None
    nota: str = ""


def check_section_class(inp: CheckSectionClassInput) -> CheckSectionClassOutput:
    out = CheckSectionClassOutput(tool="check_section_class", inputs_hash=compute_inputs_hash(inp))
    if inp.designazione_commerciale:
        sez = lookup_chs_commerciale(inp.designazione_commerciale)
        D, t = sez.D_ext_mm, sez.t_mm
    elif inp.D_ext_mm and inp.t_mm:
        D, t = inp.D_ext_mm, inp.t_mm
    else:
        raise ValueError("Specificare designazione_commerciale o (D_ext_mm, t_mm)")
    eps = math.sqrt(235.0 / inp.fy_MPa)
    eps2 = eps * eps
    ratio = D / t
    L1, L2, L3 = 50 * eps2, 70 * eps2, 90 * eps2
    if ratio <= L1: classe = 1
    elif ratio <= L2: classe = 2
    elif ratio <= L3: classe = 3
    else: classe = 4

    out.classe = classe
    out.rapporto_d_su_t = ratio
    out.epsilon = eps
    out.limite_C1 = L1
    out.limite_C2 = L2
    out.limite_C3 = L3
    out.nota = {
        1: "Plastica piena, M_pl,Rd disponibile, rotazione fino a collasso",
        2: "Plastica limitata, M_pl,Rd disponibile, rotazione ridotta",
        3: "Elastica, M_el,Rd max",
        4: "Slender shell — A_eff/W_eff con riduzione locale (EN 1993-1-5 / -1-6)",
    }[classe]
    out.trace.append(TraceStep(
        label="classificazione",
        formula="d/t vs 50ε²/70ε²/90ε², ε=√(235/fy)",
        substitution=(
            f"D={D}, t={t}, d/t={ratio:.1f}, ε²={eps2:.3f} → "
            f"limiti C1={L1:.1f} C2={L2:.1f} C3={L3:.1f} → classe {classe}"
        ),
        value=classe, unit="-",
        norm_ref="EN 1993-1-1 §5.5 + Tab. 5.2 (CHS)",
    ))

    # Sanity rules (§12.13) — F12-W4
    if not (235.0 <= inp.fy_MPa <= 460.0):
        out.warnings.append(
            f"fy={inp.fy_MPa} MPa fuori [235,460]: ε=√(235/fy) calibrata su acciai S235-S460, "
            "classificazione fuori perimetro per acciai non standard."
        )
    if ratio < 10.0:
        out.warnings.append(
            f"d/t={ratio:.1f} < 10: sezione molto tozza (classe 1 attesa) — verificare significato fisico."
        )
    if classe == 4:
        out.warnings.append(
            "Classe 4 (snella): richiede area efficace A_eff (EC3 §6.2.2.5) — vedi check_tubular_stability/A_eff."
        )

    out.primary_value = float(classe)
    out.primary_unit = "classe"
    return out


# ---------------------------------------------------------------------------
# get_combination_factors — ψ_0/ψ_1/ψ_2 NTC §2.5
# ---------------------------------------------------------------------------

# NTC 2018 Tab. 2.5.I — coefficienti di combinazione
NTC_PSI: dict[str, dict[str, float]] = {
    "categoria_A_residenziale":  {"psi_0": 0.7, "psi_1": 0.5, "psi_2": 0.3},
    "categoria_B_uffici":        {"psi_0": 0.7, "psi_1": 0.5, "psi_2": 0.3},
    "categoria_C_riunione":      {"psi_0": 0.7, "psi_1": 0.7, "psi_2": 0.6},
    "categoria_D_commerciale":   {"psi_0": 0.7, "psi_1": 0.7, "psi_2": 0.6},
    "categoria_E_magazzino":     {"psi_0": 1.0, "psi_1": 0.9, "psi_2": 0.8},
    "vento":                     {"psi_0": 0.6, "psi_1": 0.2, "psi_2": 0.0},
    "neve_H_le_1000":            {"psi_0": 0.5, "psi_1": 0.2, "psi_2": 0.0},
    "neve_H_gt_1000":            {"psi_0": 0.7, "psi_1": 0.5, "psi_2": 0.2},
    "temperatura":               {"psi_0": 0.6, "psi_1": 0.5, "psi_2": 0.0},
    "ghiaccio_pali_TLC":         {"psi_0": 0.5, "psi_1": 0.2, "psi_2": 0.0},
}

# γ NTC Tab. 2.6.I — coeff. parziali azioni
NTC_GAMMA = {
    "STR_A1": {"G1_sfav": 1.3, "G1_fav": 1.0, "G2_sfav": 1.5, "G2_fav": 0.0,
                "Q_sfav": 1.5,  "Q_fav": 0.0},
    "GEO_A2": {"G1_sfav": 1.0, "G1_fav": 1.0, "G2_sfav": 1.3, "G2_fav": 0.0,
                "Q_sfav": 1.3,  "Q_fav": 0.0},
    "EQU":    {"G1_sfav": 1.1, "G1_fav": 0.9, "G2_sfav": 1.5, "G2_fav": 0.0,
                "Q_sfav": 1.5,  "Q_fav": 0.0},
}


class GetCombinationFactorsInput(BaseModel):
    azione: str = Field(..., description=f"Una di: {list(NTC_PSI)}")
    set_gamma: Literal["STR_A1", "GEO_A2", "EQU"] = "STR_A1"


class GetCombinationFactorsOutput(CalcResult):
    psi_0: float | None = None
    psi_1: float | None = None
    psi_2: float | None = None
    gamma: dict | None = None


def get_combination_factors(inp: GetCombinationFactorsInput) -> GetCombinationFactorsOutput:
    out = GetCombinationFactorsOutput(tool="get_combination_factors", inputs_hash=compute_inputs_hash(inp))
    if inp.azione not in NTC_PSI:
        out.out_of_scope = True
        out.out_of_scope_reason = f"Azione '{inp.azione}' non in tab. NTC §2.5"
        return out
    p = NTC_PSI[inp.azione]
    g = NTC_GAMMA[inp.set_gamma]
    out.psi_0, out.psi_1, out.psi_2 = p["psi_0"], p["psi_1"], p["psi_2"]
    out.gamma = g
    out.trace.append(TraceStep(
        label="coefficienti combinazione",
        formula="ψ_0/ψ_1/ψ_2 + γ_G/γ_Q",
        substitution=(
            f"azione={inp.azione}, set={inp.set_gamma}: "
            f"ψ_0={p['psi_0']}, ψ_1={p['psi_1']}, ψ_2={p['psi_2']}"
        ),
        value=p["psi_0"], unit="-",
        norm_ref="NTC 2018 Tab. 2.5.I + Tab. 2.6.I",
    ))
    return out
