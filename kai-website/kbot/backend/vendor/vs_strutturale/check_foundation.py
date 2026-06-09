"""Verifica fondazione superficiale a plinto — NTC 2018 §6.4.2.

Verifiche:
  1. Capacità portante (Terzaghi / Vesic) — A2 + M2 (R3) approccio 2 NTC §6.4.2.1
  2. Scorrimento alla base
  3. Ribaltamento (EQU — γ_G,fav e γ_G,sfav distinti)
  4. Eccentricità ammissibile (e ≤ L/6 per non avere parzializzazione)

NB: micropali e pali trivellati — sessione dedicata futura (interfaccia
geotecnica più complessa, modello t-z).
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash
from ._sanity import apply_sanity_rules_to_output, sanity_check_enabled
from ._units import dimensional_check_enabled, verify_output_dimensions

import math

from pydantic import BaseModel, Field

from .schemas import CalcResult, TraceStep


class CheckFoundationInput(BaseModel):
    # Geometria plinto rettangolare
    L_x_m: float = Field(..., gt=0, description="Lato in direzione del momento")
    B_y_m: float = Field(..., gt=0, description="Lato ortogonale")
    H_m: float = Field(..., gt=0, description="Altezza plinto")
    profondita_imposta_m: float = Field(..., ge=0, description="D — profondità piano fondazione")
    # Carichi alla base plinto (SLU fondamentale)
    N_Ed_kN: float = Field(..., description="Forza verticale tot (incluso peso plinto + terreno)")
    H_Ed_kN: float = Field(..., description="Forza orizzontale alla base")
    M_Ed_kNm: float = Field(..., description="Momento alla base, attorno asse y (M in direzione L_x)")
    # Carichi favorevole/sfavorevole per EQU (ribaltamento)
    G_stabilizzante_kN: float = Field(..., description="Peso proprio plinto + terreno sopra, FAVOREVOLE per ribaltamento")
    M_ribaltante_kNm: float = Field(..., description="Componente momento ribaltante")
    # Terreno (parametri geotecnici caratteristici)
    gamma_terreno_kN_m3: float = 18.0
    c_prime_kPa: float = Field(0.0, description="Coesione drenata caratteristica")
    phi_prime_deg: float = Field(..., description="Angolo attrito drenato caratteristico")
    delta_attrito_terreno_deg: float | None = Field(
        None, description="Attrito interfaccia plinto-terreno; default = 2/3 · φ'"
    )
    # Coeff. parziali NTC Tab. 6.2.II (M2) e 6.4.I (R3) — DA verificare per progetto
    gamma_phi: float = 1.25
    gamma_c: float = 1.25
    gamma_R3_capacita: float = 2.3
    gamma_R3_scorrimento: float = 1.1
    # EQU (ribaltamento)
    gamma_G_fav_EQU: float = 0.9
    gamma_G_sfav_EQU: float = 1.1


class CheckFoundationOutput(CalcResult):
    A_eff_m2: float | None = None
    eccentricita_m: float | None = None
    parzializzato: bool = False
    q_Ed_kPa: float | None = None
    q_Rd_kPa: float | None = None
    eta_capacita: float | None = None
    H_Rd_scorrimento_kN: float | None = None
    eta_scorrimento: float | None = None
    M_stab_kNm: float | None = None
    M_rib_d_kNm: float | None = None
    eta_ribaltamento: float | None = None
    verifica_ok: bool = False


def check_foundation(inp: CheckFoundationInput) -> CheckFoundationOutput:
    out = CheckFoundationOutput(tool="check_foundation", inputs_hash=compute_inputs_hash(inp))
    L, B, D = inp.L_x_m, inp.B_y_m, inp.profondita_imposta_m

    # Eccentricità
    if inp.N_Ed_kN <= 0:
        raise ValueError("N_Ed deve essere positivo (compressione) per verifica capacità portante.")
    e = abs(inp.M_Ed_kNm) / inp.N_Ed_kN
    out.eccentricita_m = e
    parz = e > L / 6.0
    out.parzializzato = parz

    out.trace.append(TraceStep(
        label="eccentricità",
        formula="e = |M_Ed|/N_Ed ; parzializzato se e > L/6",
        substitution=f"e={e:.3f}m, L/6={L/6:.3f}m → {'parzializzato' if parz else 'tutto reagente'}",
        value=e, unit="m", norm_ref="Statica fondazioni — distribuzione lineare",
    ))

    # Larghezza efficace Meyerhof: L' = L − 2e
    L_eff = max(L - 2.0 * e, 1e-3)
    A_eff = L_eff * B
    out.A_eff_m2 = A_eff
    out.trace.append(TraceStep(
        label="A_eff (Meyerhof)",
        formula="L' = L − 2e ; A_eff = L'·B",
        substitution=f"L'={L_eff:.3f}m, A_eff={A_eff:.3f} m²",
        value=A_eff, unit="m²", norm_ref="Approccio Meyerhof — NTC §6.4.2.1",
    ))

    # Parametri di progetto (M2)
    phi_k = math.radians(inp.phi_prime_deg)
    phi_d = math.atan(math.tan(phi_k) / inp.gamma_phi)
    c_d = inp.c_prime_kPa / inp.gamma_c
    out.trace.append(TraceStep(
        label="parametri di progetto (M2)",
        formula="φ_d = atan(tan(φ_k)/γ_φ) ; c'_d = c'_k/γ_c",
        substitution=f"φ_k={inp.phi_prime_deg}°, γ_φ={inp.gamma_phi} → φ_d={math.degrees(phi_d):.2f}°; c'_d={c_d:.2f} kPa",
        value=math.degrees(phi_d), unit="°", norm_ref="NTC Tab. 6.2.II",
    ))

    # Fattori di capacità portante (Vesic / Terzaghi)
    Nq = math.exp(math.pi * math.tan(phi_d)) * (math.tan(math.pi/4 + phi_d/2))**2 if phi_d > 0 else 1.0
    Nc = (Nq - 1.0) / math.tan(phi_d) if phi_d > 0 else 5.14
    Ng = 2.0 * (Nq - 1.0) * math.tan(phi_d) if phi_d > 0 else 0.0

    # Capacità portante drenata (formula Brinch Hansen semplificata, senza inclinazione)
    q_lim = c_d * Nc + inp.gamma_terreno_kN_m3 * D * Nq + 0.5 * inp.gamma_terreno_kN_m3 * L_eff * Ng
    q_Rd = q_lim / inp.gamma_R3_capacita
    out.q_Rd_kPa = q_Rd
    out.trace.append(TraceStep(
        label="q_lim e q_Rd",
        formula="q_lim = c·Nc + γ·D·Nq + 0.5·γ·L'·Nγ ; q_Rd = q_lim/γ_R",
        substitution=(
            f"Nc={Nc:.2f}, Nq={Nq:.2f}, Nγ={Ng:.2f} → "
            f"q_lim={q_lim:.1f} kPa, q_Rd={q_Rd:.1f} kPa (γ_R={inp.gamma_R3_capacita})"
        ),
        value=q_Rd, unit="kPa", norm_ref="NTC §6.4.2.1 + Vesic/Brinch-Hansen",
    ))

    q_Ed = inp.N_Ed_kN / A_eff   # kPa
    out.q_Ed_kPa = q_Ed
    eta_q = q_Ed / q_Rd if q_Rd > 0 else float("inf")
    out.eta_capacita = eta_q

    # Scorrimento alla base
    delta_d = (inp.delta_attrito_terreno_deg if inp.delta_attrito_terreno_deg is not None
               else inp.phi_prime_deg * 2.0 / 3.0)
    delta_d_rad = math.atan(math.tan(math.radians(delta_d)) / inp.gamma_phi)
    H_Rd = inp.N_Ed_kN * math.tan(delta_d_rad) / inp.gamma_R3_scorrimento
    out.H_Rd_scorrimento_kN = H_Rd
    eta_H = abs(inp.H_Ed_kN) / H_Rd if H_Rd > 0 else float("inf")
    out.eta_scorrimento = eta_H

    out.trace.append(TraceStep(
        label="scorrimento",
        formula="H_Rd = N_Ed · tan(δ_d)/γ_R ; δ_d default = 2/3 φ_k",
        substitution=f"δ={delta_d:.2f}° → H_Rd={H_Rd:.1f} kN, η={eta_H:.3f}",
        value=eta_H, unit="-", norm_ref="NTC §6.4.2.1 — Tab. 6.4.I (R3)",
    ))

    # Ribaltamento (EQU)
    M_stab = inp.G_stabilizzante_kN * (L / 2.0) * inp.gamma_G_fav_EQU
    M_rib_d = inp.M_ribaltante_kNm * inp.gamma_G_sfav_EQU + abs(inp.H_Ed_kN) * inp.H_m * inp.gamma_G_sfav_EQU
    out.M_stab_kNm = M_stab
    out.M_rib_d_kNm = M_rib_d
    eta_rib = M_rib_d / M_stab if M_stab > 0 else float("inf")
    out.eta_ribaltamento = eta_rib

    out.trace.append(TraceStep(
        label="ribaltamento (EQU)",
        formula="M_stab = γ_G,fav·G·L/2 ; M_rib = γ_G,sfav·(M_rib + H·h)",
        substitution=(
            f"M_stab={M_stab:.1f} kN·m, M_rib_d={M_rib_d:.1f} kN·m → η={eta_rib:.3f}"
        ),
        value=eta_rib, unit="-", norm_ref="NTC §2.6.1 Tab. 2.6.I (EQU)",
    ))

    eta_glob = max(eta_q, eta_H, eta_rib)
    out.verifica_ok = eta_glob <= 1.0
    out.primary_value = eta_glob
    out.primary_unit = "-"

    out.trace.append(TraceStep(
        label="η globale fondazione",
        formula="η = max(η_capacità, η_scorrimento, η_ribaltamento)",
        substitution=f"= {eta_glob:.3f} {'OK' if out.verifica_ok else 'NON VERIFICATO'}",
        value=eta_glob, unit="-", norm_ref="NTC §6.4.2.1",
    ))

    if parz:
        out.warnings.append(
            "Plinto parzializzato (e > L/6): distribuzione triangolare. "
            "Modello Meyerhof applicato; verificare anche con SLE compressione triangolare."
        )

    if dimensional_check_enabled():
        for _w in verify_output_dimensions(out.model_dump(), out.tool):
            out.warnings.append(f"[dim] {_w}")
    if sanity_check_enabled():
        out.warnings.extend(apply_sanity_rules_to_output(out.tool, out.model_dump()))
    return out
