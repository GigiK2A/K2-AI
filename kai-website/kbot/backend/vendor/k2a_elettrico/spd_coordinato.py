"""Verifica SPD coordinato — CEI EN 61643-12 + CEI 81-30 (distanza max protezione)."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class SpdCoordinatoInput(BaseModel):
    LPL: Literal["I", "II", "III", "IV"] = "II"
    tipo_struttura: Literal["LPS_esterno", "rete_aerea", "rete_interrata"] = "LPS_esterno"
    Up_spd_tipo1_kV: float = Field(1.5, gt=0, description="Tensione protezione SPD tipo 1 (kV) — tipico 1.5-2.5")
    Up_spd_tipo2_kV: float = Field(1.5, gt=0, description="Up SPD tipo 2 (kV) — tipico 1.5-2.0")
    Up_spd_tipo3_kV: float = Field(1.5, gt=0, description="Up SPD tipo 3 (kV) — finissimo presso utenze")
    tensione_tenuta_apparato_Uw_kV: float = Field(2.5, gt=0, description="Tensione impulsiva Uw apparato protetto (categoria sovratensione: I=1.5, II=2.5, III=4, IV=6)")
    L_cavi_da_SPD2_apparato_m: float = Field(..., gt=0, description="Lunghezza cavi tra SPD ultimo e apparato")


class SpdCoordinatoOutput(BaseModel):
    Iimp_SPD1_richiesto_kA: float
    In_SPD2_minimo_kA: float
    distanza_max_protezione_m: float
    SPD3_richiesto: bool
    coordinamento_Up_apparato_ok: bool
    msg: str
    note_normative: list[str]
    trace: dict


def verifica_spd_coordinato(inp: SpdCoordinatoInput) -> SpdCoordinatoOutput:
    # Iimp tipo 1 in funzione LPL (CEI EN 62305-4 Tab. E.2)
    iimp_per_lpl = {"I": 25, "II": 18.75, "III": 12.5, "IV": 12.5}  # kA per polo
    Iimp_T1 = iimp_per_lpl[inp.LPL]

    # In tipo 2 minimo: per ambiente residenziale 5 kA, terziario 10 kA, industriale 15-20 kA
    In_T2_min = 5 if inp.tipo_struttura == "rete_interrata" else 10

    # Distanza max protezione: oltre questa lunghezza Up effettivo > Up SPD a causa onda riflessa
    # Regola pratica CEI 81-30: 10m / kV di Up → es. Up=1.5kV → 15m max
    d_max = inp.Up_spd_tipo2_kV * 10

    # SPD3 richiesto se distanza tra SPD2 e apparato > d_max
    spd3 = inp.L_cavi_da_SPD2_apparato_m > d_max

    # Verifica Up vs Uw: Up_effettivo ≤ Uw / 1.2 (margine sicurezza 20%)
    Up_eff = inp.Up_spd_tipo3_kV if spd3 else inp.Up_spd_tipo2_kV
    Up_eff_con_distanza = Up_eff + 0.001 * inp.L_cavi_da_SPD2_apparato_m  # +1V/m approssimazione induttanza cavi
    coord_ok = Up_eff_con_distanza * 1.2 <= inp.tensione_tenuta_apparato_Uw_kV

    if coord_ok and not spd3:
        msg = f"OK: SPD tipo 1+2 sufficienti. Up={Up_eff_con_distanza:.2f}kV × 1.2 = {Up_eff_con_distanza*1.2:.2f}kV ≤ Uw={inp.tensione_tenuta_apparato_Uw_kV}kV."
    elif coord_ok and spd3:
        msg = f"OK con SPD3: distanza {inp.L_cavi_da_SPD2_apparato_m}m > d_max={d_max}m → richiesto SPD tipo 3 vicino all'apparato."
    else:
        msg = f"KO: Up_eff×1.2 = {Up_eff_con_distanza*1.2:.2f}kV > Uw = {inp.tensione_tenuta_apparato_Uw_kV}kV. Scegliere SPD con Up minore o aggiungere SPD3."

    note = [
        "CEI EN 61643-11/-12: scelta e installazione SPD BT",
        "CEI 81-30: coordinamento e distanza max",
        f"LPL {inp.LPL} → Iimp SPD tipo 1 ≥ {Iimp_T1} kA per polo (10/350μs)",
        f"In SPD tipo 2 ≥ {In_T2_min} kA (8/20μs)",
        "Lunghezza cavi tra SPD1 e SPD2: ≤ 10m altrimenti aggiungere SPD intermedio",
        "Cavo collegamento a terra SPD: max 50cm, sezione min 16mm² rame",
    ]

    return SpdCoordinatoOutput(
        Iimp_SPD1_richiesto_kA=Iimp_T1,
        In_SPD2_minimo_kA=In_T2_min,
        distanza_max_protezione_m=round(d_max, 1),
        SPD3_richiesto=spd3,
        coordinamento_Up_apparato_ok=coord_ok,
        msg=msg,
        note_normative=note,
        trace={
            "norma": "CEI EN 61643-12 + CEI 81-30 + CEI 64-8 sez.443/534",
            "regola_distanza": "d_max ≈ 10m × Up [kV]",
            "criterio_Uw": "Up_eff × 1.2 ≤ Uw apparato",
            "categorie_Uw": {"I": "1.5kV (apparati sensibili)", "II": "2.5kV (apparati domestici)",
                             "III": "4kV (distribuzione)", "IV": "6kV (ingresso impianto)"},
        },
    )
