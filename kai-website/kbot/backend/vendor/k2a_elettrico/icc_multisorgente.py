"""Icc trifase BT multi-sorgente — IEC 60909-0:2016.

Calcolo Icc max/min su sbarra BT alimentata da rete DSO MT + N trafi
MT/BT in parallelo. Considera:
  - c_max = 1.10 (LV) per Icc max, c_min = 0.95 per Icc min
  - vcc tolleranza ±x% → vcc_min per Icc max, vcc_max per Icc min
  - X/R reale per κ (fattore di picco IEC 60909-0 eq.55)
  - Combinazione complessa Z = R + jX (ammettenze parallele per trafi)
"""
from __future__ import annotations
import math
from typing import Literal
from pydantic import BaseModel, Field


class TrafoSpec(BaseModel):
    Sn_kVA: float = Field(..., gt=0)
    vcc_pct: float = Field(..., gt=0, le=100)
    vcc_tolleranza_pct: float = Field(0.0, ge=0,
        description="Tolleranza simmetrica ±x% sul vcc nominale (IEC 60076)")
    X_R_trafo: float = Field(10.0, gt=0,
        description="X/R trafo; tipico 5-10 per MT/BT distribuzione")


class IccMultisorgenteInput(BaseModel):
    Vn_BT: float = Field(400.0, gt=0, description="V tensione BT")
    Vn_MT: float = Field(20000.0, gt=0, description="V tensione MT")
    Icc_MT_kA: float = Field(..., gt=0, description="Icc trifase rete DSO lato MT")
    X_R_rete: float = Field(10.0, gt=0)
    trafi: list[TrafoSpec] = Field(..., min_length=1)
    modalita: Literal["max", "min", "entrambi"] = "entrambi"
    contributo_motori_kW: float = Field(0.0, ge=0,
        description="Riservato v0.4: contributo motori asincroni IEC 60909 §3.8")
    R_a_caldo_factor: float = Field(
        1.236,
        gt=0,
        description=(
            "Fattore correttivo R trafi a temperatura di fine guasto (IEC 60909 §6.3.1.2). "
            "Default 1.236 = R(80°C)/R(20°C) per Cu. "
            "Applicato solo alla R dei trafi (non alla rete MT), solo per Ik3min."
        ),
    )
    c_factor_override: float | None = Field(
        default=None, gt=0, le=1.2,
        description="Override del fattore di tensione c (IEC 60909-0 Tab.1). "
                    "Se None, usa c_max=1.10 (per Ik3max) e c_min=0.95 (per Ik3min). "
                    "Se specificato, applica lo stesso valore in entrambi i casi. "
                    "Utile per riprodurre calcoli con metodologia non-IEC stretta "
                    "(es. PE che usa c=1.0 nominale).")
    validate_runtime: bool = Field(
        False,
        description="Modalità C runtime (ADR-009): se True, cross-validation inline "
                    "col validator gemello; esito in cross_validation_*. Default False.")
    with_kb_references: bool = Field(
        False,
        description="Tappa 2: se True, include i riferimenti normativi KB applicabili "
                    "in riferimenti_kb. Default False.")
    dynamic_kb: bool = Field(False, description="Tappa 2 Fase 2: con with_kb_references, recupera i verbatim live dalla KB invece dello snapshot statico. Default False.")
    validate_kb_values: bool = Field(False, description="Tappa 2 Fase 2: con with_kb_references, valida i valori normativi del tool contro i verbatim KB (campo kb_validation). Default False.")


class IccMultisorgenteOutput(BaseModel):
    Ik3max_kA: float | None
    Ik3min_kA: float | None
    Ipk_kA: float | None
    kappa: float | None
    contributi: dict
    ipotesi_metodologiche: list[str]
    norma_riferimento_internazionale: str
    norma_riferimento_locale: dict
    trace: dict
    # Modalità C runtime (ADR-009)
    cross_validation_eseguita: bool = False
    cross_validation_esito: str = "NON_ESEGUITA"
    cross_validation_delta_pct: dict = Field(default_factory=dict)
    cross_validation_note: list[str] = Field(default_factory=list)
    # Tappa 2: riferimenti normativi KB
    riferimenti_kb: list[dict] = Field(default_factory=list)
    kb_validation: list[dict] = Field(default_factory=list)


def _impedenze_caso(inp: IccMultisorgenteInput, c: float, vcc_sign: int,
                    r_factor: float = 1.0) -> dict:
    """Calcola R_tot, X_tot, |Z_tot| per un caso (max o min).
    vcc_sign = -1 per Icc max (vcc minimo), +1 per Icc min (vcc massimo).
    r_factor: fattore correttivo R trafi a caldo (IEC 60909 §6.3.1.2);
              1.0 per Icc max, inp.R_a_caldo_factor per Icc min.
              Applicato solo alla R dei trafi (non alla rete MT).
    """
    # Z rete riferita BT (IEC 60909-0 §4.3.1.1 eq.13 + trasporto a BT)
    Z_rete_MT = c * inp.Vn_MT / (math.sqrt(3) * inp.Icc_MT_kA * 1000)
    Z_rete_BT = Z_rete_MT * (inp.Vn_BT / inp.Vn_MT) ** 2
    R_rete = Z_rete_BT / math.sqrt(1 + inp.X_R_rete ** 2)
    X_rete = R_rete * inp.X_R_rete

    # Trafi in parallelo via ammettenze complesse
    Y_sum = complex(0, 0)
    for t in inp.trafi:
        # Tolleranza IEC 60076 §10.4: percentuale RELATIVA del vcc nominale
        # (es. vcc 6% ±10% → 5,4%÷6,6%), NON differenza in punti percentuali.
        # vcc_sign=-1 per Ik3max (Z min), +1 per Ik3min (Z max).
        vcc_eff = t.vcc_pct * (1 + vcc_sign * t.vcc_tolleranza_pct / 100) / 100
        Z_T = vcc_eff * inp.Vn_BT ** 2 / (t.Sn_kVA * 1000)
        R_T = Z_T / math.sqrt(1 + t.X_R_trafo ** 2) * r_factor
        X_T = (Z_T / math.sqrt(1 + t.X_R_trafo ** 2)) * t.X_R_trafo
        Y_sum += 1 / complex(R_T, X_T)
    Z_trafi_par = 1 / Y_sum
    R_trafi_par = Z_trafi_par.real
    X_trafi_par = Z_trafi_par.imag

    R_tot = R_rete + R_trafi_par
    X_tot = X_rete + X_trafi_par
    Z_tot = math.sqrt(R_tot ** 2 + X_tot ** 2)

    return {
        "Z_rete_BT_mOhm": Z_rete_BT * 1000,
        "Z_trafi_par_mOhm": abs(Z_trafi_par) * 1000,
        "R_tot_mOhm": R_tot * 1000,
        "X_tot_mOhm": X_tot * 1000,
        "Z_tot_mOhm": Z_tot * 1000,
        "X_R_finale": X_tot / R_tot if R_tot > 0 else float("inf"),
    }


def icc_bt_multisorgente(inp: IccMultisorgenteInput) -> IccMultisorgenteOutput:
    contributi: dict = {}
    Ik3max = Ipk = kappa = None
    Ik3min = None

    c_max_used = inp.c_factor_override if inp.c_factor_override else 1.10
    c_min_used = inp.c_factor_override if inp.c_factor_override else 0.95
    c_source = "override utente" if inp.c_factor_override else "IEC default LV"

    if inp.modalita in ("max", "entrambi"):
        d = _impedenze_caso(inp, c=c_max_used, vcc_sign=-1)
        Ik3max = c_max_used * inp.Vn_BT / (math.sqrt(3) * d["Z_tot_mOhm"] / 1000) / 1000
        # IEC 60909-0 eq.55: κ = 1.02 + 0.98 × exp(-3·R/X)
        # Edge case: sistema puramente induttivo (R_tot=0, X/R=∞) → R/X=0 → κ=2.0
        R_su_X = 1 / d["X_R_finale"] if d["X_R_finale"] != float("inf") else 0.0
        kappa = 1.02 + 0.98 * math.exp(-3 * R_su_X)
        Ipk = kappa * math.sqrt(2) * Ik3max
        contributi["max"] = {**d, "c_factor": c_max_used, "c_source": c_source,
                             "vcc_caso": "nominale − tolleranza (Z min)"}

    if inp.modalita in ("min", "entrambi"):
        d = _impedenze_caso(inp, c=c_min_used, vcc_sign=+1,
                            r_factor=inp.R_a_caldo_factor)
        Ik3min = c_min_used * inp.Vn_BT / (math.sqrt(3) * d["Z_tot_mOhm"] / 1000) / 1000
        contributi["min"] = {**d, "c_factor": c_min_used, "c_source": c_source,
                             "vcc_caso": "nominale + tolleranza (Z max)"}

    ipotesi = [
        "IEC 60909-0:2016 §4.3 — calcolo Icc via metodo della tensione equivalente",
        f"c_max = {c_max_used:.2f} ({c_source}) per U ≤ 1000 V (Tab.1)",
        f"c_min = {c_min_used:.2f} ({c_source})",
        "Trafi paralleli: combinazione tramite ammettenze complesse Y = 1/Z",
        "Z_rete riportata BT: Z_BT = Z_MT × (Vn_BT/Vn_MT)²",
        "κ secondo eq.55: κ = 1.02 + 0.98·exp(−3·R/X) con R/X reale di Z_tot",
        f"Ik3min: R trafi a caldo ×{inp.R_a_caldo_factor} (IEC 60909-0 §6.3.1.2, "
        "fine guasto ~80°C); applicata solo alla R dei trafi, non alla rete MT",
        "Contributo motori asincroni (IEC 60909-0 §3.8): TRASCURATO (v0.4)",
    ]
    if inp.contributo_motori_kW > 0:
        ipotesi.append(f"⚠ contributo_motori_kW={inp.contributo_motori_kW} dichiarato ma non implementato (v0.4)")

    out = IccMultisorgenteOutput(
        Ik3max_kA=round(Ik3max, 3) if Ik3max is not None else None,
        Ik3min_kA=round(Ik3min, 3) if Ik3min is not None else None,
        Ipk_kA=round(Ipk, 3) if Ipk is not None else None,
        kappa=round(kappa, 4) if kappa is not None else None,
        contributi={k: {kk: round(vv, 4) if isinstance(vv, float) else vv
                        for kk, vv in v.items()} for k, v in contributi.items()},
        ipotesi_metodologiche=ipotesi,
        norma_riferimento_internazionale="IEC 60909-0:2016",
        norma_riferimento_locale={
            "IT": "CEI EN 60909-0:2017",
            "DE": "DIN EN 60909-0:2016",
            "FR": "NF EN 60909-0:2016",
            "ES": "UNE-EN 60909-0:2017",
            "UK": "BS EN 60909-0:2016",
        },
        trace={
            "metodo": "tensione equivalente Eq = c·Vn/√3 in serie a Z_k",
            "n_trafi": len(inp.trafi),
            "rete_DSO_lato": "MT",
        },
    )
    from ._cross_validation import finalize
    return finalize(inp, out, "icc_bt_multisorgente", {})
