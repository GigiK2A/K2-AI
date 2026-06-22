"""Verifica gruppo bulloni — distribuzione tensione/taglio EN 1993-1-8.

Modello: bulloni disposti su circonferenza (o pattern arbitrario), sollecitati
da M_Ed (momento), N_Ed (assiale), V_Ed (taglio). Il bullone più carico in
trazione è quello al raggio massimo nel piano di M.

Distribuzione (assunzione asse neutro al centro):
  T_max = N_Ed/n + M_Ed · r_max / Σ r²
  V_per_bullone = V_Ed / n   (taglio uniforme)

Verifiche EN 1993-1-8 Tab. 3.4:
  F_t,Rd  = k_2 · f_ub · A_s / γ_M2   (trazione, k_2=0.9)
  F_v,Rd  = α_v · f_ub · A / γ_M2     (taglio)
  F_b,Rd  = α_b · f_u_p · d · t_p / γ_M2  (rifollamento piastra)
  B_p,Rd  = 0.6 · π · d_m · t_p · f_u / γ_M2  (punzonamento testa bullone)
  Interazione: V/F_v,Rd + T/(1.4·F_t,Rd) ≤ 1
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash

import math

from pydantic import BaseModel, Field

from .data.bulloni import BULLONI_AREE, CLASSI_BULLONI, alpha_v
from .schemas import CalcResult, TraceStep


class CheckBoltGroupInput(BaseModel):
    n_bulloni: int = Field(..., ge=3)
    raggi_bulloni_mm: list[float] | None = Field(
        None,
        description=(
            "Lista raggi di ogni bullone dal centro della flangia. "
            "Se None → disposizione uniforme su circonferenza R = D_cerchio/2."
        ),
    )
    D_cerchio_bulloni_mm: float | None = Field(
        None, description="Per disposizione circolare uniforme"
    )
    designazione_bullone: str = Field(..., description="es. 'M24'")
    classe_bulloni: str = Field(..., description="es. '8.8'")
    # Sollecitazioni
    N_Ed_kN: float = Field(0.0, description="Trazione: + ; compressione: −")
    M_Ed_kNm: float = 0.0
    V_Ed_kN: float = 0.0
    modalita_cautelativa: bool = Field(
        False, description="M × 1.10 imperfezioni"
    )
    fattore_amplificazione_M_vortex: float = Field(1.0, ge=1.0, le=1.5)
    # Geometria piastra (per rifollamento e punzonamento)
    t_piastra_mm: float = Field(20.0, description="Spessore piastra")
    f_u_piastra_MPa: float = 510.0
    diametro_foro_mm: float | None = Field(
        None, description="Diametro nominale foro. Default = d_bullone + 2"
    )
    diametro_medio_testa_mm: float | None = Field(
        None, description="d_m, default = 1.5·d_bullone"
    )
    e1_distanza_bordo_mm: float = Field(40.0, description="Distanza bordo nel verso del taglio")
    p1_passo_mm: float = Field(60.0, description="Interasse bulloni nel verso del taglio")
    gamma_M2: float = 1.25
    taglio_in_filettato: bool = True


class CheckBoltGroupOutput(CalcResult):
    F_t_Rd_kN: float | None = None
    F_v_Rd_kN: float | None = None
    F_b_Rd_kN: float | None = None
    B_p_Rd_kN: float | None = None
    T_max_kN: float | None = None
    V_per_bullone_kN: float | None = None
    eta_trazione: float | None = None
    eta_taglio: float | None = None
    eta_rifollamento: float | None = None
    eta_punzonamento: float | None = None
    eta_combinata: float | None = None
    eta_globale: float | None = None
    verifica_ok: bool = False


def check_bolt_group(inp: CheckBoltGroupInput) -> CheckBoltGroupOutput:
    out = CheckBoltGroupOutput(tool="check_bolt_group", inputs_hash=compute_inputs_hash(inp))

    bd = BULLONI_AREE[inp.designazione_bullone]
    cls = CLASSI_BULLONI[inp.classe_bulloni]
    A_s, A_nom = bd["A_s"], bd["A"]
    d_b = bd["d"]
    f_ub = cls["f_ub"]
    av = alpha_v(inp.classe_bulloni)
    d_0 = inp.diametro_foro_mm or (d_b + 2.0)
    d_m = inp.diametro_medio_testa_mm or (1.5 * d_b)
    A_shear = A_s if inp.taglio_in_filettato else A_nom

    n = inp.n_bulloni
    # Raggi: lista esplicita o uniforme su cerchio
    if inp.raggi_bulloni_mm:
        raggi = inp.raggi_bulloni_mm
        if len(raggi) != n:
            raise ValueError(f"raggi_bulloni_mm length={len(raggi)} != n_bulloni={n}")
    elif inp.D_cerchio_bulloni_mm:
        r = inp.D_cerchio_bulloni_mm / 2.0
        # Bulloni equispaziati: angoli θ_i = 2π·i/n
        # Proiezione sul piano di M (asse x): r·cos(θ)
        raggi = [r * math.cos(2*math.pi * i / n) for i in range(n)]
    else:
        raise ValueError("Specificare raggi_bulloni_mm O D_cerchio_bulloni_mm")

    # Solo i raggi POSITIVI contribuiscono alla trazione (lato teso)
    r_max = max(raggi)
    sum_r2 = sum(r * r for r in raggi if r > 0)  # solo lato teso reagisce in trazione

    # Trazione bullone più carico
    # Modalità cautelativa
    M_Ed_used = inp.M_Ed_kNm * inp.fattore_amplificazione_M_vortex
    if inp.modalita_cautelativa:
        M_Ed_used *= 1.10
    N_per_bull = inp.N_Ed_kN / n   # se N positivo è trazione, negativo compressione (riduce T)
    T_da_M = M_Ed_used * 1e3 * r_max / sum_r2 if sum_r2 > 0 else 0  # kN
    T_max = max(0.0, T_da_M + N_per_bull) if inp.N_Ed_kN >= 0 else max(0.0, T_da_M - abs(N_per_bull))
    out.T_max_kN = T_max

    V_per_bull = abs(inp.V_Ed_kN) / n
    out.V_per_bullone_kN = V_per_bull

    out.trace.append(TraceStep(
        label="distribuzione T",
        formula="T_max = N/n + M·r_max/Σr²  (lato teso)",
        substitution=(
            f"n={n}, r_max={r_max:.0f} mm, Σr²={sum_r2:.0f} mm², "
            f"N_per_bull={N_per_bull:.2f}, T_da_M={T_da_M:.2f} → T_max={T_max:.2f} kN"
        ),
        value=T_max, unit="kN",
        norm_ref="Distribuzione asse neutro centrato (rigid flange)",
    ))

    # Resistenze bullone
    F_t_Rd = 0.9 * f_ub * A_s / inp.gamma_M2 / 1000.0
    F_v_Rd = av * f_ub * A_shear / inp.gamma_M2 / 1000.0
    out.F_t_Rd_kN = F_t_Rd
    out.F_v_Rd_kN = F_v_Rd

    # Rifollamento (EN 1993-1-8 Tab. 3.4 — direzione carico)
    e1, p1 = inp.e1_distanza_bordo_mm, inp.p1_passo_mm
    alpha_d = min(e1 / (3 * d_0), (p1 / (3 * d_0)) - 0.25, f_ub / inp.f_u_piastra_MPa, 1.0)
    k_1 = 2.5  # cautelativo
    F_b_Rd = k_1 * alpha_d * inp.f_u_piastra_MPa * d_b * inp.t_piastra_mm / inp.gamma_M2 / 1000.0
    out.F_b_Rd_kN = F_b_Rd

    # Punzonamento testa bullone (Tab. 3.4)
    B_p_Rd = 0.6 * math.pi * d_m * inp.t_piastra_mm * inp.f_u_piastra_MPa / inp.gamma_M2 / 1000.0
    out.B_p_Rd_kN = B_p_Rd

    out.trace.append(TraceStep(
        label="resistenze bullone",
        formula="F_t,Rd=0.9·f_ub·A_s/γ ; F_v,Rd=α_v·f_ub·A/γ ; F_b,Rd ; B_p,Rd",
        substitution=(
            f"F_t,Rd={F_t_Rd:.1f}  F_v,Rd={F_v_Rd:.1f}  F_b,Rd={F_b_Rd:.1f}  B_p,Rd={B_p_Rd:.1f} kN"
        ),
        value=F_t_Rd, unit="kN",
        norm_ref="EN 1993-1-8 Tab. 3.4",
    ))

    # η per ogni verifica
    out.eta_trazione    = T_max / F_t_Rd if F_t_Rd > 0 else float("inf")
    out.eta_taglio      = V_per_bull / F_v_Rd if F_v_Rd > 0 else float("inf")
    out.eta_rifollamento = V_per_bull / F_b_Rd if F_b_Rd > 0 else float("inf")
    out.eta_punzonamento = T_max / B_p_Rd if B_p_Rd > 0 else float("inf")
    out.eta_combinata   = (V_per_bull / F_v_Rd) + T_max / (1.4 * F_t_Rd)

    eta_glob = max(out.eta_trazione, out.eta_taglio, out.eta_rifollamento,
                   out.eta_punzonamento, out.eta_combinata)
    out.eta_globale = eta_glob
    out.verifica_ok = eta_glob <= 1.0

    out.trace.append(TraceStep(
        label="η globale gruppo bulloni",
        formula="max(η_T, η_V, η_rifoll, η_punz, η_comb)",
        substitution=(
            f"η_T={out.eta_trazione:.3f}, η_V={out.eta_taglio:.3f}, "
            f"η_rifoll={out.eta_rifollamento:.3f}, η_punz={out.eta_punzonamento:.3f}, "
            f"η_comb={out.eta_combinata:.3f} → η={eta_glob:.3f} "
            f"{'OK' if out.verifica_ok else 'NON VERIFICATO'}"
        ),
        value=eta_glob, unit="-",
        norm_ref="EN 1993-1-8 §3 + interaz. Tab. 3.4",
    ))
    # Sanity rules (§12.13) — F12-W4 Stage 5
    if not (300.0 <= inp.f_u_piastra_MPa <= 700.0):
        out.warnings.append(
            f"f_u_piastra={inp.f_u_piastra_MPa} MPa fuori [300,700]: acciaio non standard."
        )
    if alpha_d <= e1 / (3 * d_0) and alpha_d < 1.0:
        out.warnings.append(
            f"α_d={alpha_d:.3f} limitato dalla distanza al bordo e1={e1} mm: "
            "verificare la geometria dei fori (rifollamento ridotto)."
        )
    governing = max(
        (out.eta_trazione, "trazione"), (out.eta_taglio, "taglio"),
        (out.eta_rifollamento, "rifollamento"), (out.eta_punzonamento, "punzonamento"),
        (out.eta_combinata, "combinata"),
    )
    if governing[0] > 1.0:
        out.warnings.append(
            f"Verifica governata da '{governing[1]}' (η={governing[0]:.2f}) > 1: NON verificato."
        )

    out.primary_value = eta_glob
    return out
