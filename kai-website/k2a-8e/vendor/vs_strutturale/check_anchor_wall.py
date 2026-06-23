"""Verifica ancoraggi chimici/meccanici su MURATURA — ETAG 029 + EN 1996.

Pensato per pali RT con attacco a parete su muratura piena, semipiena, forata o
pietra. Diverso da `check_anchor.py` (EN 1992-4) che vale solo su calcestruzzo.

Modello semplificato in 3 modalità di rottura:

TRAZIONE:
  1. N_Rk,s = A_s · f_uk          (rottura acciaio bullone)
  2. N_Rk,p (pull-out)            (estrazione, da ETA prodotto su muratura)
  3. N_Rk,b = α_b · f_b,k · h_ef² (rottura conoide su muratura — semplificato)
     α_b = 0,5  per muratura piena di mattoni
     α_b = 0,3  per muratura semipiena / cls cellulare
     α_b = 0,2  per muratura forata (foratura ≥ 45%)
     α_b = 0,7  per blocchi cls pieno / pietra naturale densa

TAGLIO:
  1. V_Rk,s = k_8 · A_s · f_uk  (rottura acciaio)
  2. V_Rk,c = β_b · f_b,k · h_ef · d  (taglio bordo / pry-out semplificato)
     β_b = 0,7·α_b

INTERAZIONE: (N_Ed/N_Rd)^1.5 + (V_Ed/V_Rd)^1.5 ≤ 1

Riferimenti:
- ETAG 029 — Metal injection anchors for use in masonry
- EN 1996-1-1 §3.6 (resistenza a compressione muratura)
- HILTI / FISCHER / WÜRTH ETA su muratura per valori puntuali

NB: questo modulo NON sostituisce l'uso di catalogo ETA dell'ancorante
specifico — fornisce un primo screening con ordini di grandezza. Per
verifiche di consegna usare ETA prodotto.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .data.bulloni import BULLONI_AREE, CLASSI_BULLONI
from .schemas import CalcResult, TraceStep

# Coefficienti α_b per tipologia di muratura (cono di rottura)
ALPHA_B_MURATURA = {
    "mattoni_pieni": 0.50,         # mattoni pieni laterizio
    "mattoni_semipieni": 0.35,     # foratura < 45%
    "mattoni_forati": 0.20,        # foratura ≥ 45% (blocchi cavi)
    "cls_cellulare": 0.30,         # AAC / Gasbeton
    "blocchi_cls_pieni": 0.70,     # cls pieno o pietra densa
    "pietra_naturale_densa": 0.70, # tufo compatto, calcare denso
    "tufo_tenero": 0.25,           # tufo poroso (es. Roma)
}

# k_8 acciaio bullone in taglio (EN 1993-1-8 Tab. 3.4 — semplificato)
K_8_TAGLIO = 0.60


class CheckAnchorWallInput(BaseModel):
    designazione_bullone: str = Field(..., description="es. 'M12', 'M16'")
    classe_bulloni: str = Field("8.8", description="es. '8.8', 'A4-70'")
    h_ef_mm: float = Field(..., gt=0, description="Profondità effettiva ancoraggio nella muratura")
    tipo_muratura: str = Field(
        ...,
        description=(
            "Una di: mattoni_pieni, mattoni_semipieni, mattoni_forati, "
            "cls_cellulare, blocchi_cls_pieni, pietra_naturale_densa, tufo_tenero"
        ),
    )
    f_b_k_MPa: float = Field(
        ...,
        gt=0,
        description=(
            "Resistenza caratteristica a compressione del blocco singolo (EN 1996). "
            "Mattoni pieni tipici: 10-30 MPa. Forati: 5-15 MPa. Tufo: 2-5 MPa."
        ),
    )
    spessore_muratura_mm: float = Field(
        ..., gt=0,
        description="Spessore parete (deve essere ≥ h_ef + copriferro ~50mm)",
    )
    distanza_bordo_min_mm: float = Field(
        100.0,
        gt=0,
        description="c_1 distanza bordo critico — minimo 5·d per muratura",
    )
    n_ancoraggi: int = Field(1, ge=1)
    # Sollecitazioni per ancoraggio
    N_Ed_kN: float = Field(0.0, ge=0, description="Trazione di progetto per singolo ancoraggio")
    V_Ed_kN: float = Field(0.0, ge=0, description="Taglio di progetto per singolo ancoraggio")
    # Pull-out da ETA prodotto (opzionale)
    N_Rk_pullout_kN: float | None = Field(
        None, description="Resistenza pull-out caratteristica da ETA dell'ancorante (es. HILTI HIT-HY 270)"
    )
    # γ
    gamma_Ms: float = Field(1.40, description="Acciaio EN 1992-4")
    gamma_Mw: float = Field(2.00, description="Muratura (più cautelativo di cls)")
    # Spina di rottura
    fattore_riduzione_qualita: float = Field(
        1.0,
        ge=0.5,
        le=1.0,
        description=(
            "Riduzione globale per qualità muratura (1.0 = ben fatta, "
            "0.7 = muratura storica con malta scadente, 0.5 = condizioni dubbie)"
        ),
    )


class CheckAnchorWallOutput(CalcResult):
    N_Rd_steel_kN: float | None = None
    N_Rd_cono_muratura_kN: float | None = None
    N_Rd_pullout_kN: float | None = None
    V_Rd_steel_kN: float | None = None
    V_Rd_muratura_kN: float | None = None
    eta_trazione: float | None = None
    eta_taglio: float | None = None
    eta_interazione: float | None = None
    modalita_critica: str = ""
    verifica_ok: bool = False
    avvertenze_ETA: str = ""


def check_anchor_wall(inp: CheckAnchorWallInput) -> CheckAnchorWallOutput:
    out = CheckAnchorWallOutput(tool="check_anchor_wall", inputs_hash=compute_inputs_hash(inp))

    if inp.tipo_muratura not in ALPHA_B_MURATURA:
        out.out_of_scope = True
        out.out_of_scope_reason = (
            f"tipo_muratura '{inp.tipo_muratura}' non riconosciuto. "
            f"Valori ammessi: {list(ALPHA_B_MURATURA.keys())}"
        )
        return out

    if inp.h_ef_mm + 30 > inp.spessore_muratura_mm:
        out.warnings.append(
            f"h_ef={inp.h_ef_mm}mm + copriferro 30mm > spessore parete {inp.spessore_muratura_mm}mm. "
            "Ancoraggio non realizzabile o richiede tassello passante."
        )

    bd = BULLONI_AREE[inp.designazione_bullone]
    cls = CLASSI_BULLONI[inp.classe_bulloni]
    A_s = bd["A_s"]
    d = bd["d"]
    f_uk = cls["f_ub"]

    alpha_b = ALPHA_B_MURATURA[inp.tipo_muratura]
    rq = inp.fattore_riduzione_qualita

    # 1) Acciaio — TRAZIONE
    N_Rk_s = A_s * f_uk / 1000.0
    N_Rd_s = N_Rk_s / inp.gamma_Ms
    out.N_Rd_steel_kN = N_Rd_s
    out.trace.append(TraceStep(
        label="acciaio trazione",
        formula="N_Rk,s = A_s·f_uk ; N_Rd,s = N_Rk,s/γ_Ms",
        substitution=(
            f"A_s={A_s:.1f} mm², f_uk={f_uk} MPa → "
            f"N_Rk,s={N_Rk_s:.2f} kN ; N_Rd,s={N_Rd_s:.2f} kN"
        ),
        value=N_Rd_s, unit="kN",
        norm_ref="EN 1992-4 §7.2.1.3 (applicabile anche a muratura)",
    ))

    # 2) Cono di rottura su muratura
    N_Rk_b = alpha_b * inp.f_b_k_MPa * inp.h_ef_mm ** 2 / 1000.0 * rq
    # Penalizzazione bordo (se c < 1.5·h_ef, lineare)
    c_cr = 1.5 * inp.h_ef_mm
    if inp.distanza_bordo_min_mm < c_cr:
        psi_edge = 0.5 + 0.5 * (inp.distanza_bordo_min_mm / c_cr)
        N_Rk_b *= psi_edge
    else:
        psi_edge = 1.0
    N_Rd_b = N_Rk_b / inp.gamma_Mw * inp.n_ancoraggi
    out.N_Rd_cono_muratura_kN = N_Rd_b
    out.trace.append(TraceStep(
        label="cono muratura",
        formula="N_Rk,b = α_b·f_b,k·h_ef²·ψ_edge·r_q ; N_Rd,b = N_Rk,b/γ_Mw·n",
        substitution=(
            f"α_b={alpha_b} ({inp.tipo_muratura}), f_b,k={inp.f_b_k_MPa} MPa, "
            f"h_ef={inp.h_ef_mm} mm, ψ_edge={psi_edge:.2f}, r_q={rq} → "
            f"N_Rk,b={N_Rk_b:.2f} kN ; N_Rd,b={N_Rd_b:.2f} kN ({inp.n_ancoraggi} anc.)"
        ),
        value=N_Rd_b, unit="kN",
        norm_ref="ETAG 029 + EN 1996-1-1 §3.6 (modello semplificato)",
    ))

    # 3) Pull-out da ETA
    N_Rd_p = None
    if inp.N_Rk_pullout_kN:
        N_Rd_p = inp.N_Rk_pullout_kN / inp.gamma_Mw * inp.n_ancoraggi
        out.N_Rd_pullout_kN = N_Rd_p
        out.trace.append(TraceStep(
            label="pull-out (ETA)",
            formula="N_Rd,p = N_Rk,p / γ_Mw · n",
            substitution=f"N_Rk,p={inp.N_Rk_pullout_kN} (ETA) → N_Rd,p={N_Rd_p:.2f} kN",
            value=N_Rd_p, unit="kN",
            norm_ref="ETA prodotto (catalogo ancorante)",
        ))
    else:
        out.avvertenze_ETA = (
            "N_Rk_pullout_kN non fornito. Verifica pull-out limitata al cono muratura. "
            "Per la consegna inserire valore da ETA prodotto (HILTI/FISCHER/WÜRTH)."
        )

    N_Rd_min = min(filter(None, [N_Rd_s, N_Rd_b, N_Rd_p]))
    modalita = "acciaio" if N_Rd_min == N_Rd_s else (
        "cono_muratura" if N_Rd_min == N_Rd_b else "pull-out"
    )

    # 4) Acciaio — TAGLIO
    V_Rk_s = K_8_TAGLIO * A_s * f_uk / 1000.0
    V_Rd_s = V_Rk_s / inp.gamma_Ms
    out.V_Rd_steel_kN = V_Rd_s

    # 5) Taglio muratura (semplificato)
    beta_b = 0.7 * alpha_b
    V_Rk_b = beta_b * inp.f_b_k_MPa * inp.h_ef_mm * d / 1000.0 * rq
    if inp.distanza_bordo_min_mm < c_cr:
        V_Rk_b *= psi_edge
    V_Rd_b = V_Rk_b / inp.gamma_Mw * inp.n_ancoraggi
    out.V_Rd_muratura_kN = V_Rd_b
    out.trace.append(TraceStep(
        label="taglio muratura",
        formula="V_Rk,b = β_b·f_b,k·h_ef·d·ψ_edge·r_q ; β_b=0.7·α_b",
        substitution=(
            f"β_b={beta_b:.2f}, d={d}mm → V_Rk,b={V_Rk_b:.2f} kN ; V_Rd,b={V_Rd_b:.2f} kN"
        ),
        value=V_Rd_b, unit="kN",
        norm_ref="ETAG 029 + correlazione cono (modello semplificato)",
    ))

    V_Rd_min = min(V_Rd_s, V_Rd_b)
    if V_Rd_min == V_Rd_b and modalita == "acciaio":
        modalita = "muratura_(critico_taglio)"

    # 6) Sollecitazioni e η
    eta_N = inp.N_Ed_kN / N_Rd_min if N_Rd_min > 0 else math.inf
    eta_V = inp.V_Ed_kN / V_Rd_min if V_Rd_min > 0 else math.inf
    out.eta_trazione = eta_N
    out.eta_taglio = eta_V

    # 7) Interazione (k=1.5 cautelativa per muratura)
    eta_int = (eta_N ** 1.5 + eta_V ** 1.5) if (eta_N >= 0 and eta_V >= 0) else math.inf
    out.eta_interazione = eta_int
    out.modalita_critica = modalita
    out.verifica_ok = eta_int <= 1.0

    out.trace.append(TraceStep(
        label="interazione N+V",
        formula="(N_Ed/N_Rd)^1.5 + (V_Ed/V_Rd)^1.5 ≤ 1",
        substitution=(
            f"η_N={eta_N:.3f}, η_V={eta_V:.3f} → η_int={eta_int:.3f} "
            f"{'OK' if eta_int <= 1 else 'NON VERIFICATO'}; "
            f"modalità critica: {modalita}"
        ),
        value=eta_int, unit="-",
        norm_ref="ETAG 029 §5.2.5",
    ))

    out.primary_value = eta_int
    out.primary_unit = "-"
    return out
