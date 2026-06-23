"""Cabine MT/BT — dimensionamento trafo, Icc lato MT/BT, selettività relè 50/51/51N (CEI 11-27, IEC 60909)."""
from __future__ import annotations
import math
from typing import Literal
from pydantic import BaseModel, Field


class DimensionaTrafoInput(BaseModel):
    Pn_carico_kW: float = Field(..., gt=0, description="Potenza attiva del carico in kW")
    cosfi: float = Field(0.9, gt=0, le=1)
    fattore_contemporaneita: float = Field(0.8, gt=0, le=1)
    fattore_carico_max: float = Field(0.85, gt=0, le=1, description="Carico massimo / Pn trafo (sovradimens. termico)")
    margine_futuro_pc: float = Field(20.0, ge=0, description="% margine espansione futura")


class DimensionaTrafoOutput(BaseModel):
    Sn_carico_kVA: float
    Sn_trafo_min_kVA: float
    Sn_trafo_commerciale_kVA: int
    serie_commerciale: list[int]
    trace: dict


# Serie commerciale trafo MT/BT (CEI EN 60076-1)
_SERIE_TRAFO_KVA = [50, 100, 160, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500]


def dimensiona_trafo(inp: DimensionaTrafoInput) -> DimensionaTrafoOutput:
    Sn_carico = inp.Pn_carico_kW / inp.cosfi
    Sn_richiesta = Sn_carico * inp.fattore_contemporaneita * (1 + inp.margine_futuro_pc / 100) / inp.fattore_carico_max
    Sn_comm = next((s for s in _SERIE_TRAFO_KVA if s >= Sn_richiesta), _SERIE_TRAFO_KVA[-1])
    return DimensionaTrafoOutput(
        Sn_carico_kVA=round(Sn_carico, 2),
        Sn_trafo_min_kVA=round(Sn_richiesta, 2),
        Sn_trafo_commerciale_kVA=Sn_comm,
        serie_commerciale=_SERIE_TRAFO_KVA,
        trace={"norma": "CEI EN 60076 + Guida CEI 99-4",
               "formula": "Sn = (P/cosφ) × kc × (1+margine) / k_max",
               "ipotesi": f"kc={inp.fattore_contemporaneita}, margine={inp.margine_futuro_pc}%, kmax={inp.fattore_carico_max}"},
    )


class IccCabinaMTInput(BaseModel):
    Sn_trafo_kVA: float = Field(..., gt=0)
    Ucc_percento: float = Field(6.0, gt=0)
    Vn_MT: float = Field(20.0, gt=0, description="Tensione MT in kV (15, 20, 23)")
    Vn_BT: float = Field(0.4, gt=0, description="Tensione BT in kV (0.4 = 400V)")
    Pcc_rete_MT_MVA: float = Field(500.0, gt=0, description="Potenza di c.c. rete MT (tipico 250-500 MVA)")


class IccCabinaMTOutput(BaseModel):
    In_primario_A: float
    In_secondario_A: float
    Icc_MT_kA: float
    Icc_BT_kA: float
    Z_rete_MT_ohm_riferita_BT: float
    Z_trafo_ohm_riferita_BT: float
    trace: dict


def calcola_icc_cabina(inp: IccCabinaMTInput) -> IccCabinaMTOutput:
    Vn_MT_V = inp.Vn_MT * 1000
    Vn_BT_V = inp.Vn_BT * 1000
    Sn_VA = inp.Sn_trafo_kVA * 1000

    In_pri = Sn_VA / (math.sqrt(3) * Vn_MT_V)
    In_sec = Sn_VA / (math.sqrt(3) * Vn_BT_V)

    # Icc MT da Pcc rete
    Icc_MT = inp.Pcc_rete_MT_MVA * 1e6 / (math.sqrt(3) * Vn_MT_V)

    # Z_rete riferita a BT
    Z_rete_BT = Vn_BT_V ** 2 / (inp.Pcc_rete_MT_MVA * 1e6)
    # Z_trafo riferita BT
    Z_trafo_BT = inp.Ucc_percento / 100 * Vn_BT_V ** 2 / Sn_VA
    Z_tot_BT = Z_rete_BT + Z_trafo_BT
    Icc_BT = Vn_BT_V / (math.sqrt(3) * Z_tot_BT)

    return IccCabinaMTOutput(
        In_primario_A=round(In_pri, 2),
        In_secondario_A=round(In_sec, 2),
        Icc_MT_kA=round(Icc_MT / 1000, 3),
        Icc_BT_kA=round(Icc_BT / 1000, 3),
        Z_rete_MT_ohm_riferita_BT=round(Z_rete_BT, 6),
        Z_trafo_ohm_riferita_BT=round(Z_trafo_BT, 6),
        trace={"norma": "IEC 60909 + CEI 11-25 + CEI 99-4",
               "formula": "Icc_BT = Vn / (√3·(Z_rete + Z_trafo))"},
    )


class SelettivitaInput(BaseModel):
    """Selettività cronometrica tra protezione monte e valle (CEI 11-27)."""
    In_rele_monte_A: float = Field(..., gt=0)
    In_rele_valle_A: float = Field(..., gt=0)
    t_rele_monte_s: float = Field(..., gt=0, description="Tempo di intervento monte alla Icc di guasto")
    t_rele_valle_s: float = Field(..., gt=0, description="Tempo di intervento valle alla stessa Icc")
    delta_t_minimo_s: float = Field(0.3, gt=0, description="Intervallo selettività richiesto (tipico 0.3-0.4s)")


class SelettivitaOutput(BaseModel):
    selettivita_cronometrica_ok: bool
    delta_t_effettivo_s: float
    selettivita_amperometrica_ok: bool
    rapporto_In_monte_valle: float
    msg: str
    trace: dict


def verifica_selettivita(inp: SelettivitaInput) -> SelettivitaOutput:
    dt = inp.t_rele_monte_s - inp.t_rele_valle_s
    ok_t = dt >= inp.delta_t_minimo_s
    rapp = inp.In_rele_monte_A / inp.In_rele_valle_A
    ok_a = rapp >= 1.6  # criterio empirico CEI 11-27: ratio ≥ 1.5-2
    if ok_t and ok_a:
        msg = f"OK selettività totale: Δt={dt:.2f}s ≥ {inp.delta_t_minimo_s}s, rapp_In={rapp:.2f}≥1.6"
    elif ok_t:
        msg = f"OK selettività cronometrica (Δt={dt:.2f}s) ma rapp_In={rapp:.2f}<1.6 (rischio interventi simultanei)"
    elif ok_a:
        msg = f"OK amperometrica (rapp_In={rapp:.2f}) ma Δt={dt:.2f}s < {inp.delta_t_minimo_s}s"
    else:
        msg = f"KO: né cronometrica (Δt={dt:.2f}s) né amperometrica (rapp_In={rapp:.2f})"
    return SelettivitaOutput(
        selettivita_cronometrica_ok=ok_t,
        delta_t_effettivo_s=round(dt, 3),
        selettivita_amperometrica_ok=ok_a,
        rapporto_In_monte_valle=round(rapp, 3),
        msg=msg,
        trace={"norma": "CEI 11-27 (cabine MT) + IEC 60255 (relè)",
               "criteri": "Δt ≥ 0.3s (tipico) AND In_monte/In_valle ≥ 1.6"},
    )
