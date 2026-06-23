"""UPS — dimensionamento statico/dinamico, autonomia batterie, ridondanza N+1 (IEC 62040)."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class UpsDimensionaInput(BaseModel):
    P_carico_kW: float = Field(..., gt=0)
    cosfi_carico: float = Field(0.9, gt=0, le=1)
    rendimento_UPS: float = Field(0.94, gt=0, le=1, description="η UPS online: ~94-97% double-conversion, ~98% line-interactive")
    fattore_carico_massimo_UPS_pc: float = Field(80.0, gt=0, le=100, description="Mai >80% UPS per caldo + margine batterie")
    autonomia_richiesta_min: float = Field(15.0, gt=0)
    tensione_batteria_V: float = Field(480.0, gt=0, description="V banco batterie (tipico 360-540V)")
    DoD_batteria_pc: float = Field(80.0, gt=0, le=100)
    rendimento_inverter: float = Field(0.95, gt=0, le=1)
    ridondanza: Literal["N", "N+1", "2N"] = "N"
    spunto_carichi_motore_pc: float = Field(0.0, ge=0, description="% carichi motore (inrush 6×In)")


class UpsDimensionaOutput(BaseModel):
    Sn_UPS_kVA: float
    Sn_UPS_commerciale_kVA: int
    n_UPS_paralleli: int
    margine_residuo_pc: float
    capacita_batterie_Ah: float
    capacita_batterie_kWh: float
    energia_utile_kWh: float
    P_dissipata_calore_kW: float
    note_ridondanza: str
    trace: dict


SERIE_UPS_KVA = [10, 15, 20, 30, 40, 60, 80, 100, 120, 160, 200, 250, 300, 400, 500, 600, 800, 1000]


def dimensiona_ups(inp: UpsDimensionaInput) -> UpsDimensionaOutput:
    # Potenza apparente con margine carichi motore (inrush)
    Sn_base = inp.P_carico_kW / inp.cosfi_carico
    Sn_required = Sn_base / (inp.fattore_carico_massimo_UPS_pc / 100)
    # Inrush spunto motori: aggiungiamo 25% per 6×In del 10% carico motore
    if inp.spunto_carichi_motore_pc > 0:
        Sn_required *= (1 + 0.05 * inp.spunto_carichi_motore_pc / 10)

    if inp.ridondanza == "N":
        n_ups = 1
    elif inp.ridondanza == "N+1":
        n_ups = 2  # almeno 2 UPS, ognuno dimensionato per il 100% carico
    elif inp.ridondanza == "2N":
        n_ups = 2  # ogni UPS al 100%
    else:
        n_ups = 1

    Sn_comm = next((s for s in SERIE_UPS_KVA if s >= Sn_required), SERIE_UPS_KVA[-1])

    # Margine residuo: quanto della taglia commerciale resta libero a pieno carico nominale
    margine_residuo_pc = round((1 - Sn_base / Sn_comm) * 100, 2)

    # Batterie: E = P_carico × autonomia / (η_inv × DoD)
    E_richiesta_kWh = (inp.P_carico_kW * inp.autonomia_richiesta_min / 60) / (inp.rendimento_inverter * inp.DoD_batteria_pc / 100)
    Ah = E_richiesta_kWh * 1000 / inp.tensione_batteria_V

    # Calore dissipato: P × (1 - η_UPS)
    Q = inp.P_carico_kW * (1 - inp.rendimento_UPS)

    note = {
        "N":   "Nessuna ridondanza: SPOF su UPS singolo. Down-time totale in caso di guasto.",
        "N+1": "1 UPS extra in parallelo: tollera 1 guasto. Standard per data center Tier III.",
        "2N":  "Sistema completamente ridondato: 2 percorsi indipendenti. Tier IV.",
    }[inp.ridondanza]

    return UpsDimensionaOutput(
        Sn_UPS_kVA=round(Sn_required, 2),
        Sn_UPS_commerciale_kVA=Sn_comm,
        n_UPS_paralleli=n_ups,
        margine_residuo_pc=margine_residuo_pc,
        capacita_batterie_Ah=round(Ah, 1),
        capacita_batterie_kWh=round(E_richiesta_kWh, 3),
        energia_utile_kWh=round(E_richiesta_kWh * inp.DoD_batteria_pc / 100, 3),
        P_dissipata_calore_kW=round(Q, 3),
        note_ridondanza=note,
        trace={
            "norma": "IEC 62040-1/-2/-3 + Uptime Institute Tier classification",
            "formula_Sn": "Sn = (P/cosφ) / k_max × margine_inrush",
            "formula_Ah": "Ah = (P_carico × t_min/60) × 1000 / (η_inv × DoD × V_batt)",
            "tier_ref": {"N":"Tier I-II", "N+1":"Tier III", "2N":"Tier IV"},
        },
    )
