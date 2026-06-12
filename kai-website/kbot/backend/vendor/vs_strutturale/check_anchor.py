"""Verifica ancoraggi chimici/meccanici nel cls — EN 1992-4 §6+§7 (semplificata).

Verifiche per singolo ancoraggio (1 tirante) sotto N_Ed trazione + V_Ed taglio:

TRAZIONE (EN 1992-4 §7.2):
  1. N_Rk,s = A_s · f_uk   (rottura acciaio)
  2. N_Rk,p pull-out      (estrazione, da ETA prodotto)
  3. N_Rk,c = N_Rk,c0 · (A_c/A_c,0) · ψ_s,N · ψ_re,N · ψ_ec,N · ψ_M,N
     N_Rk,c0 = k_1 · √f_ck · h_ef^1.5   (cono cls)
  4. N_Rk,sp = splitting  (da ETA)

TAGLIO (EN 1992-4 §7.3):
  1. V_Rk,s = k_8 · A_s · f_uk    (rottura acciaio)
  2. V_Rk,cp = k_9 · N_Rk,c       (pry-out)
  3. V_Rk,c,edge cono di bordo

INTERAZIONE (§7.4):
  (N_Ed/N_Rd)^k + (V_Ed/V_Rd)^k ≤ 1
  k = 1.5 default (esponenziale)

Versione MCP v0.4: implemento le verifiche acciaio + cono cls + interazione.
Pull-out e splitting → input diretto da ETA prodotto (cataloghi HILTI/FISCHER/WÜRTH).
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash

import math

from pydantic import BaseModel, Field

from .data.bulloni import BULLONI_AREE, CLASSI_BULLONI
from .schemas import CalcResult, TraceStep

# k_1 EN 1992-4 §7.2.1.4 (cls non fessurato / fessurato)
K1_CLS_NON_FESSURATO = 11.9
K1_CLS_FESSURATO = 8.9


class CheckAnchorInput(BaseModel):
    designazione_bullone: str = Field(..., description="es. 'M16'")
    classe_bulloni: str = Field("8.8", description="es. '8.8' (acciaio), o classe specifica ETA")
    h_ef_mm: float = Field(..., gt=0, description="Profondità effettiva di ancoraggio")
    # Geometria — ancoraggio singolo o gruppo
    distanza_bordo_min_mm: float = Field(..., gt=0, description="c_1 distanza bordo critico")
    spaziatura_min_mm: float | None = Field(
        None, description="s_1 in gruppo, None = singolo"
    )
    n_ancoraggi: int = Field(1, ge=1)
    # Cls
    fck_MPa: float = Field(20.0, description="Resistenza cls C20/25 → 20 MPa")
    cls_fessurato: bool = Field(False, description="True per zone tese o coperture esposte")
    # Sollecitazioni
    N_Ed_kN: float = Field(0.0, ge=0, description="Trazione di progetto (per ancoraggio)")
    V_Ed_kN: float = Field(0.0, ge=0, description="Taglio di progetto (per ancoraggio)")
    # Resistenze pull-out e splitting da ETA prodotto (non in DB MCP — input)
    N_Rk_pullout_kN: float | None = Field(
        None, description="Resistenza pull-out caratteristica da ETA (se non noto, skip)"
    )
    N_Rk_splitting_kN: float | None = Field(None, description="Da ETA")
    # γ
    gamma_Ms: float = Field(1.40, description="EN 1992-4 §4.4.3 acciaio")
    gamma_Mc: float = Field(1.50, description="cls")


class CheckAnchorOutput(CalcResult):
    N_Rd_steel_kN: float | None = None
    N_Rd_cono_cls_kN: float | None = None
    N_Rd_pullout_kN: float | None = None
    V_Rd_steel_kN: float | None = None
    V_Rd_pryout_kN: float | None = None
    V_Rd_edge_kN: float | None = None
    eta_trazione: float | None = None
    eta_taglio: float | None = None
    eta_interazione: float | None = None
    modalita_critica: str = ""
    verifica_ok: bool = False


def check_anchor_en1992_4(inp: CheckAnchorInput) -> CheckAnchorOutput:
    out = CheckAnchorOutput(tool="check_anchor_en1992_4", inputs_hash=compute_inputs_hash(inp))

    bd = BULLONI_AREE[inp.designazione_bullone]
    cls = CLASSI_BULLONI[inp.classe_bulloni]
    A_s = bd["A_s"]
    f_uk = cls["f_ub"]

    # 1) Acciaio TRAZIONE — N_Rk,s = A_s · f_uk
    N_Rk_s = A_s * f_uk / 1000.0
    N_Rd_s = N_Rk_s / inp.gamma_Ms
    out.N_Rd_steel_kN = N_Rd_s

    # 2) Cono cls TRAZIONE — N_Rk,c0 = k_1 · √f_ck · h_ef^1.5 (singolo ancoraggio)
    k_1 = K1_CLS_FESSURATO if inp.cls_fessurato else K1_CLS_NON_FESSURATO
    N_Rk_c0 = k_1 * math.sqrt(inp.fck_MPa) * inp.h_ef_mm ** 1.5 / 1000.0  # kN

    # Fattore distanza bordo ψ_s,N (EN 1992-4 §7.2.1.5)
    # A_c0 = (s_cr)^2, s_cr = 3·h_ef
    s_cr = 3.0 * inp.h_ef_mm
    c_cr = 1.5 * inp.h_ef_mm
    psi_s = 0.7 + 0.3 * min(inp.distanza_bordo_min_mm / c_cr, 1.0)
    # A_c effettiva (semplificato, ancoraggio singolo)
    A_c0 = s_cr * s_cr
    if inp.distanza_bordo_min_mm < c_cr:
        # area ridotta dal bordo
        A_c = (inp.distanza_bordo_min_mm + 0.5 * s_cr) * s_cr
    else:
        A_c = A_c0
    psi_re = 1.0  # rinforzo non considerato (cautelativo)
    psi_ec = 1.0  # senza eccentricità (singolo ancoraggio)
    psi_M = 1.0   # modificatore qualità

    N_Rk_c = N_Rk_c0 * (A_c / A_c0) * psi_s * psi_re * psi_ec * psi_M
    N_Rd_c = N_Rk_c / inp.gamma_Mc * inp.n_ancoraggi
    out.N_Rd_cono_cls_kN = N_Rd_c

    out.trace.append(TraceStep(
        label="cono cls",
        formula="N_Rk,c0 = k_1·√f_ck·h_ef^1.5 ; N_Rk,c = N_Rk,c0·(A_c/A_c0)·ψ_s,N·ψ_re·ψ_ec·ψ_M",
        substitution=(
            f"k_1={k_1} ({'fess.' if inp.cls_fessurato else 'non fess.'}), "
            f"h_ef={inp.h_ef_mm}mm → N_Rk,c0={N_Rk_c0:.1f} kN; ψ_s={psi_s:.3f}, "
            f"A_c/A_c0={A_c/A_c0:.3f} → N_Rd,c={N_Rd_c:.1f} kN"
        ),
        value=N_Rd_c, unit="kN",
        norm_ref="EN 1992-4 §7.2.1.4-5",
    ))

    # 3) Pull-out — da ETA, se fornito
    N_Rd_p = None
    if inp.N_Rk_pullout_kN:
        N_Rd_p = inp.N_Rk_pullout_kN / inp.gamma_Mc
        out.N_Rd_pullout_kN = N_Rd_p

    # 4) Acciaio TAGLIO — V_Rk,s = k_8·A_s·f_uk (k_8 = 0.6 default per ancoraggio standard)
    V_Rk_s = 0.6 * A_s * f_uk / 1000.0
    V_Rd_s = V_Rk_s / inp.gamma_Ms
    out.V_Rd_steel_kN = V_Rd_s

    # 5) Pry-out — V_Rk,cp = k_9 · N_Rk,c (k_9 = 2.0 per h_ef ≥ 60mm, altrimenti 1.0)
    k_9 = 2.0 if inp.h_ef_mm >= 60 else 1.0
    V_Rk_cp = k_9 * N_Rk_c
    V_Rd_cp = V_Rk_cp / inp.gamma_Mc
    out.V_Rd_pryout_kN = V_Rd_cp

    # 6) Cono di bordo (semplificato) — V_Rk,c,edge ≈ 1.6·√f_ck·c_1^1.5
    # Forma cautelativa, EN 1992-4 §7.3.2 è più dettagliata
    V_Rk_edge = 1.6 * math.sqrt(inp.fck_MPa) * inp.distanza_bordo_min_mm ** 1.5 / 1000.0
    V_Rd_edge = V_Rk_edge / inp.gamma_Mc
    out.V_Rd_edge_kN = V_Rd_edge

    out.trace.append(TraceStep(
        label="taglio acciaio + pry-out + cono bordo",
        formula="V_Rk,s=k_8·A·f_uk ; V_Rk,cp=k_9·N_Rk,c ; V_Rk,edge",
        substitution=f"V_Rd,s={V_Rd_s:.1f}, V_Rd,cp={V_Rd_cp:.1f}, V_Rd,edge={V_Rd_edge:.1f} kN",
        value=V_Rd_s, unit="kN",
        norm_ref="EN 1992-4 §7.3.2-4",
    ))

    # η
    candidates_N = [v for v in [N_Rd_s, N_Rd_c, N_Rd_p] if v is not None]
    N_Rd_critico = min(candidates_N)
    eta_N = inp.N_Ed_kN / N_Rd_critico if N_Rd_critico > 0 else float("inf")

    V_Rd_critico = min(V_Rd_s, V_Rd_cp, V_Rd_edge)
    eta_V = inp.V_Ed_kN / V_Rd_critico if V_Rd_critico > 0 else float("inf")

    # Interazione esponenziale §7.4
    k_int = 1.5
    eta_int = (eta_N ** k_int) + (eta_V ** k_int)

    out.eta_trazione = eta_N
    out.eta_taglio = eta_V
    out.eta_interazione = eta_int

    # Critical mode
    if N_Rd_critico == N_Rd_s:
        out.modalita_critica = "acciaio (trazione)"
    elif N_Rd_critico == N_Rd_c:
        out.modalita_critica = "cono cls"
    else:
        out.modalita_critica = "pull-out"

    out.verifica_ok = eta_int <= 1.0 and eta_N <= 1.0 and eta_V <= 1.0
    out.trace.append(TraceStep(
        label="η interazione",
        formula="(N_Ed/N_Rd)^1.5 + (V_Ed/V_Rd)^1.5 ≤ 1",
        substitution=(
            f"η_N={eta_N:.3f}, η_V={eta_V:.3f} → η_int={eta_int:.3f} "
            f"{'OK' if out.verifica_ok else 'NON VERIFICATO'} (critico: {out.modalita_critica})"
        ),
        value=eta_int, unit="-",
        norm_ref="EN 1992-4 §7.4 — interazione esponenziale",
    ))
    # Sanity rules (§12.13) — F12-W4 Stage 6
    if not (12.0 <= inp.fck_MPa <= 90.0):
        out.warnings.append(
            f"fck={inp.fck_MPa} MPa fuori [12,90]: classe cls non standard EN 1992-4."
        )
    if inp.distanza_bordo_min_mm < c_cr:
        out.warnings.append(
            f"c={inp.distanza_bordo_min_mm} mm < c_cr={c_cr:.0f} mm: area cono ridotta dal bordo "
            f"(ψ_s={psi_s:.2f}); verificare disposizione vicino al bordo."
        )
    if out.modalita_critica == "cono cls" and eta_N > 1.0:
        out.warnings.append(
            "Rottura per cono di calcestruzzo governa e η>1: rottura fragile lato cls — "
            "aumentare h_ef o prevedere armatura di sospensione (EN 1992-4 §7.2.1.9)."
        )
    if inp.N_Rk_pullout_kN is None and inp.N_Ed_kN > 0:
        out.warnings.append(
            "Pull-out non fornito (manca ETA prodotto): verifica trazione basata solo su "
            "acciaio + cono cls. Inserire N_Rk_pullout_kN da ETA per completezza."
        )

    out.primary_value = eta_int
    return out
