"""Calcoli in corrente continua — FV, BESS, TLC -48V DC, UPS DC."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "portate_cei_unel_35024.json").read_text())


# ------------------ CADUTA DI TENSIONE DC ------------------

class CadutaVDCInput(BaseModel):
    I_A: float = Field(..., gt=0, description="Corrente DC in A")
    L_m: float = Field(..., gt=0, description="Lunghezza linea singolo polo in m (la formula raddoppia per andata+ritorno)")
    sezione_mm2: float = Field(..., gt=0)
    Vn_DC: float = Field(..., gt=0, description="Tensione nominale DC (es. 48 TLC, 600 FV, 750 BESS)")
    materiale: Literal["Cu", "Al"] = "Cu"
    temp_conduttore_C: float = Field(70.0, description="T° conduttore per correzione ρ (default 70°C)")
    delta_V_limite_pc: float = Field(1.0, description="Limite ΔV% (FV: 1%, TLC: 1%, generale BT DC: 4%)")


class CadutaVDCOutput(BaseModel):
    delta_V_volt: float
    delta_V_percento: float
    R_unitario_ohm_per_km: float
    R_loop_ohm: float
    verifica_ok: bool
    formula: str
    trace: dict


def caduta_tensione_dc(inp: CadutaVDCInput) -> CadutaVDCOutput:
    rho20 = _DATA["resistivita_conduttori"][inp.materiale]
    rho = rho20 * (1 + 0.004 * (inp.temp_conduttore_C - 20))
    R_per_km = rho * 1000 / inp.sezione_mm2
    # DC: R_loop = 2·L·R_unitario (andata + ritorno, no X, no cosφ)
    R_loop = 2 * R_per_km * inp.L_m / 1000
    dV = R_loop * inp.I_A
    dVpc = dV / inp.Vn_DC * 100
    return CadutaVDCOutput(
        delta_V_volt=round(dV, 4),
        delta_V_percento=round(dVpc, 4),
        R_unitario_ohm_per_km=round(R_per_km, 5),
        R_loop_ohm=round(R_loop, 5),
        verifica_ok=dVpc <= inp.delta_V_limite_pc,
        formula="ΔV_DC = 2 × L × ρ(T) × I / S",
        trace={
            "norma": "CEI 64-8 sez.712 (FV) / ETSI EN 300 132-2 (TLC -48V DC)",
            "rho_a_T": round(rho, 5),
            "limite_pc_riferimento": {
                "FV_DC": "1-2% (CEI 64-8/712 + Guida CEI 82-25)",
                "TLC_-48V": "1% (ETSI: garantire 40.5-57V al carico)",
                "BT_DC_generale": "4% (analogo a AC)",
            },
        },
    )


# ------------------ CORTO CIRCUITO DC ------------------

class CortoCircuitoDCInput(BaseModel):
    sorgente: Literal["batteria", "raddrizzatore", "FV"] = "batteria"
    Vn_DC: float = Field(..., gt=0, description="Tensione nominale V")
    R_interno_sorgente_ohm: float = Field(..., ge=0, description="R interna sorgente Ω (batteria: 1-10mΩ/cella×Nserie; raddrizzatore: da datasheet)")
    L_linea_m: float = Field(..., ge=0)
    sezione_mm2: float = Field(..., gt=0)
    materiale: Literal["Cu", "Al"] = "Cu"
    # Solo FV
    Isc_modulo_A: float | None = Field(None, description="Solo FV: corrente cc del modulo")
    n_stringhe_parallelo: int | None = Field(None, ge=1, description="Solo FV: stringhe in parallelo")


class CortoCircuitoDCOutput(BaseModel):
    Icc_DC_A: float
    R_linea_loop_ohm: float
    R_totale_ohm: float
    trace: dict


def corto_circuito_dc(inp: CortoCircuitoDCInput) -> CortoCircuitoDCOutput:
    rho = _DATA["resistivita_conduttori"][inp.materiale] * (1 + 0.004 * (80 - 20))
    R_loop = 2 * rho * inp.L_linea_m / inp.sezione_mm2
    R_tot = inp.R_interno_sorgente_ohm + R_loop

    if inp.sorgente == "FV":
        # FV: Icc = 1.25 × Isc × Nstringhe (CEI 64-8 sez. 712.433 fattore sicurezza)
        if inp.Isc_modulo_A is None or inp.n_stringhe_parallelo is None:
            raise ValueError("FV: servono Isc_modulo_A e n_stringhe_parallelo")
        Icc = 1.25 * inp.Isc_modulo_A * inp.n_stringhe_parallelo
        note = "Icc_FV = 1.25 × Isc × Nstr (CEI 64-8/712.433)"
    else:
        # Batteria/raddrizzatore: legge di Ohm V/R
        if R_tot <= 0:
            raise ValueError("R_totale = 0 (sorgente ideale): impossibile calcolare Icc finito")
        Icc = inp.Vn_DC / R_tot
        note = "Icc = Vn / (R_sorgente + R_loop_linea)"

    return CortoCircuitoDCOutput(
        Icc_DC_A=round(Icc, 2),
        R_linea_loop_ohm=round(R_loop, 5),
        R_totale_ohm=round(R_tot, 5),
        trace={
            "norma": "CEI 64-8 sez.712 (FV) / IEC 61660 (DC corto circuito) — semplificato",
            "formula": note,
            "ipotesi": "regime DC stazionario, T_conduttore=80°C (riscaldamento c.c.)",
        },
    )


# ------------------ STRINGA FOTOVOLTAICA ------------------

class StringaFVInput(BaseModel):
    Voc_modulo_STC_V: float = Field(..., gt=0, description="Voc a STC (25°C) da datasheet")
    Vmpp_modulo_STC_V: float = Field(..., gt=0, description="Vmpp a STC da datasheet")
    Isc_modulo_A: float = Field(..., gt=0, description="Isc da datasheet")
    coeff_temp_Voc_pcK: float = Field(-0.30, description="β coeff temperatura Voc, %/K (negativo, tipico -0.27/-0.35)")
    T_min_C: float = Field(-10.0, description="Temperatura minima moduli (sito): -10°C tipico zona NO Italia")
    T_max_C: float = Field(70.0, description="Temperatura massima moduli operativa (sito)")
    V_max_inverter_DC_V: float = Field(1000.0, description="Tensione DC max ammessa inverter (V)")
    V_mppt_min_V: float = Field(200.0, description="Estremo inferiore range MPPT inverter")
    V_mppt_max_V: float = Field(800.0, description="Estremo superiore range MPPT inverter")


class StringaFVOutput(BaseModel):
    N_serie_max_da_Voc: int
    N_serie_min_da_Vmpp_Tmax: int
    N_serie_max_da_Vmpp_Tmin: int
    N_serie_raccomandato_range: list[int]
    Voc_stringa_Tmin_V: float
    Vmpp_stringa_Tmax_V: float
    Vmpp_stringa_Tmin_V: float
    verifica_ok: bool
    trace: dict


def stringa_fv(inp: StringaFVInput) -> StringaFVOutput:
    # Coefficiente di correzione Voc a T_min
    delta_T_min = inp.T_min_C - 25  # negativo
    k_Voc_Tmin = 1 + inp.coeff_temp_Voc_pcK / 100 * delta_T_min  # >1 perché ΔT negativo × β negativo
    Voc_Tmin = inp.Voc_modulo_STC_V * k_Voc_Tmin

    # Voc stringa a T_min ≤ V_max_inverter
    N_max_Voc = int(inp.V_max_inverter_DC_V / Voc_Tmin)

    # Vmpp dipende anch'esso dalla temperatura (uso lo stesso β come approssimazione)
    delta_T_max = inp.T_max_C - 25  # positivo
    k_Vmpp_Tmax = 1 + inp.coeff_temp_Voc_pcK / 100 * delta_T_max  # <1
    Vmpp_Tmax = inp.Vmpp_modulo_STC_V * k_Vmpp_Tmax

    k_Vmpp_Tmin = 1 + inp.coeff_temp_Voc_pcK / 100 * delta_T_min  # >1
    Vmpp_Tmin = inp.Vmpp_modulo_STC_V * k_Vmpp_Tmin

    # N_min: Vmpp stringa a T_max ≥ V_mppt_min  →  N ≥ V_mppt_min / Vmpp_Tmax
    N_min_Vmpp = int(inp.V_mppt_min_V / Vmpp_Tmax) + 1
    # N_max_Vmpp: Vmpp stringa a T_min ≤ V_mppt_max  →  N ≤ V_mppt_max / Vmpp_Tmin
    N_max_Vmpp = int(inp.V_mppt_max_V / Vmpp_Tmin)

    N_range_low = max(N_min_Vmpp, 1)
    N_range_high = min(N_max_Voc, N_max_Vmpp)
    ok = N_range_high >= N_range_low

    return StringaFVOutput(
        N_serie_max_da_Voc=N_max_Voc,
        N_serie_min_da_Vmpp_Tmax=N_min_Vmpp,
        N_serie_max_da_Vmpp_Tmin=N_max_Vmpp,
        N_serie_raccomandato_range=[N_range_low, N_range_high] if ok else [],
        Voc_stringa_Tmin_V=round(Voc_Tmin * N_range_high if ok else 0, 2),
        Vmpp_stringa_Tmax_V=round(Vmpp_Tmax * N_range_low if ok else 0, 2),
        Vmpp_stringa_Tmin_V=round(Vmpp_Tmin * N_range_high if ok else 0, 2),
        verifica_ok=ok,
        trace={
            "norma": "CEI 64-8 sez.712 + Guida CEI 82-25 + IEC 62548",
            "criteri": {
                "Voc_max": "N × Voc(Tmin) ≤ V_max_inverter (sicurezza moduli/inverter)",
                "Vmpp_min": "N × Vmpp(Tmax) ≥ V_mppt_min (efficienza estate)",
                "Vmpp_max": "N × Vmpp(Tmin) ≤ V_mppt_max (range MPPT inverno)",
            },
            "Voc_Tmin_unitario": round(Voc_Tmin, 2),
            "Vmpp_Tmax_unitario": round(Vmpp_Tmax, 2),
            "Vmpp_Tmin_unitario": round(Vmpp_Tmin, 2),
        },
    )


# ------------------ BESS / BATTERIA RUNTIME ------------------

class BessRuntimeInput(BaseModel):
    capacita_kWh: float = Field(..., gt=0, description="Capacità nominale batteria in kWh")
    potenza_carico_kW: float = Field(..., gt=0, description="Potenza assorbita dal carico in kW")
    DoD_percento: float = Field(80.0, gt=0, le=100, description="Profondità di scarica ammessa (LiFePO4 80-90%, AGM 50%, Pb-acido 30%)")
    rendimento_inverter: float = Field(0.95, gt=0, le=1)
    rendimento_batteria_round_trip: float = Field(0.92, gt=0, le=1, description="Round-trip efficiency (LiFePO4 ~92-95%, Pb ~70-80%)")


class BessRuntimeOutput(BaseModel):
    energia_utile_kWh: float
    autonomia_h: float
    autonomia_min: float
    n_cicli_anno_a_1_ciclo_giorno: int
    vita_attesa_anni_a_DoD: float
    trace: dict


def bess_runtime(inp: BessRuntimeInput) -> BessRuntimeOutput:
    E_utile = inp.capacita_kWh * inp.DoD_percento / 100 * inp.rendimento_inverter
    # rendimento round-trip applicato sul ciclo completo, per autonomia in scarica usiamo η_inverter
    autonomia_h = E_utile / inp.potenza_carico_kW

    # Stima vita: 5000 cicli LiFePO4 @ 80% DoD, 2000 cicli AGM @ 50%, 500 cicli Pb @ 30%
    # Approssimazione: cicli_target ∝ 1/DoD
    if inp.DoD_percento >= 75:
        cicli_target = 5000  # LiFePO4-like
    elif inp.DoD_percento >= 50:
        cicli_target = 2500
    else:
        cicli_target = 1000
    vita_anni = cicli_target / 365

    return BessRuntimeOutput(
        energia_utile_kWh=round(E_utile, 3),
        autonomia_h=round(autonomia_h, 3),
        autonomia_min=round(autonomia_h * 60, 1),
        n_cicli_anno_a_1_ciclo_giorno=365,
        vita_attesa_anni_a_DoD=round(vita_anni, 1),
        trace={
            "norma": "IEC 62619 (batterie industriali) / CEI 0-21 (accumulo connesso)",
            "formula": "E_utile = C × DoD × η_inv  →  autonomia = E_utile / P_carico",
            "DoD_riferimenti": {
                "LiFePO4": "80-90%",
                "Litio_NMC": "80-95%",
                "AGM_VRLA": "50-60%",
                "Pb-acido_aperto": "30-50%",
            },
        },
    )


# ------------------ SRB TLC -48V DC ------------------

class SrbTlcInput(BaseModel):
    potenza_carico_W: float = Field(..., gt=0, description="Potenza SRB in W (tipico 300-3000W)")
    Vn_DC: float = Field(48.0, gt=0, description="Tensione nominale (TLC standard -48V)")
    V_min_carico_V: float = Field(40.5, gt=0, description="Tensione minima ammessa al carico (ETSI 40.5V)")
    V_max_carico_V: float = Field(57.0, gt=0, description="Tensione max ammessa al carico (ETSI 57V)")
    L_linea_m: float = Field(..., gt=0)
    materiale: Literal["Cu", "Al"] = "Cu"
    autonomia_richiesta_h: float = Field(4.0, gt=0, description="Autonomia batterie tampone richiesta (h)")
    DoD_batteria_pc: float = Field(80.0, gt=0, le=100)


class SrbTlcOutput(BaseModel):
    corrente_carico_A: float
    sezione_min_cavo_mm2_da_dV: float
    delta_V_pc_su_sezione_min: float
    capacita_batterie_Ah: float
    capacita_batterie_kWh: float
    trace: dict


def srb_tlc(inp: SrbTlcInput) -> SrbTlcOutput:
    I = inp.potenza_carico_W / inp.Vn_DC
    # Margine ΔV ammesso: Vn - Vmin = 48 - 40.5 = 7.5V → ΔV_max = 7.5 / Vn × 100 ≈ 15.6%
    # Ma convenzione TLC: ΔV cavo ≤ 1% (sui 48V = 0.48V) — il resto è margine batterie
    dV_max_V = inp.Vn_DC * 0.01  # 1%
    rho = _DATA["resistivita_conduttori"][inp.materiale] * (1 + 0.004 * (70 - 20))
    # ΔV = 2·L·ρ·I / S  →  S = 2·L·ρ·I / ΔV_max
    S_required = 2 * inp.L_linea_m * rho * I / dV_max_V

    # Trova sezione standard ≥ S_required
    sezioni_std = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
    S_chosen = next((s for s in sezioni_std if s >= S_required), None)
    if S_chosen is None:
        S_chosen = 240
    # Ricalcola ΔV reale con S_chosen
    dV_reale = 2 * inp.L_linea_m * rho * I / S_chosen
    dV_pc_reale = dV_reale / inp.Vn_DC * 100

    # Batterie tampone: Capacità Ah = (I × autonomia_h) / (DoD × η)
    eta_inv = 0.95
    C_Ah = I * inp.autonomia_richiesta_h / (inp.DoD_batteria_pc / 100 * eta_inv)
    C_kWh = C_Ah * inp.Vn_DC / 1000

    return SrbTlcOutput(
        corrente_carico_A=round(I, 2),
        sezione_min_cavo_mm2_da_dV=S_chosen,
        delta_V_pc_su_sezione_min=round(dV_pc_reale, 3),
        capacita_batterie_Ah=round(C_Ah, 1),
        capacita_batterie_kWh=round(C_kWh, 3),
        trace={
            "norma": "ETSI EN 300 132-2 (DC -48V TLC) + IEC 60364-7-712",
            "criteri": "ΔV cavo ≤1% Vn DC (~0.48V su 48V), V_carico ∈ [40.5; 57]V",
            "rho_a_70C": round(rho, 5),
            "S_calcolata_continua": round(S_required, 3),
            "ipotesi_batterie": f"DoD={inp.DoD_batteria_pc}%, η_inv=95%",
        },
    )
