"""Verifica trasformatore MT/BT (MT-A) — correnti nominali + Icc presunta lato BT.

Formule deterministiche di elettrotecnica (NESSUN parametro tabellare normativo
da groundare):
    In = S / (√3 · Un)                       [trifase]   (monofase: In = S/Un)
    Icc_BT (rete a monte infinita) = In_BT / (ucc/100)

Ancoraggio: CEI EN 60076-1 (tensione di cortocircuito ucc) · IEC 60909-0 (Icc
presunta). Il fattore di tensione c e l'impedenza della rete a monte (Scc_MT)
NON sono qui groundati: l'Icc è in ipotesi di RETE A MONTE INFINITA, dichiarata
esplicitamente come gap (DN-MT-5: parametro non groundato = gap dichiarato, non
inventato).
"""
from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, Field

from .trace import CalcResult, TraceStep, build_trace


class VerificaTrafoInput(BaseModel):
    potenza_kVA: float = Field(..., gt=0)
    V_MT_kV: float = Field(..., gt=0)
    V_BT_V: float = Field(..., gt=0)
    vcc_percento: float = Field(..., gt=0, description="tensione di cortocircuito ucc%")
    sistema: Literal["trifase", "monofase"] = "trifase"


class VerificaTrafoOutput(BaseModel):
    In_MT_A: float
    In_BT_A: float
    Icc_BT_A: float
    Icc_BT_kA: float
    rete_monte_infinita: bool
    note: list[str]
    calc_Icc_BT: dict[str, Any]
    trace: dict[str, Any]


def verifica_trasformatore_mtbt(inp: VerificaTrafoInput) -> VerificaTrafoOutput:
    S = inp.potenza_kVA * 1000.0  # VA
    V_MT = inp.V_MT_kV * 1000.0  # V
    V_BT = inp.V_BT_V  # V
    ucc = inp.vcc_percento / 100.0
    k = math.sqrt(3) if inp.sistema == "trifase" else 1.0
    fattore = "√3" if inp.sistema == "trifase" else "1"

    In_MT = S / (k * V_MT)
    In_BT = S / (k * V_BT)
    Icc_BT = In_BT / ucc  # ipotesi rete a monte infinita

    steps = [
        TraceStep(
            step=1,
            descrizione="Corrente nominale lato MT",
            formula=f"In_MT = S/({fattore}·V_MT)",
            valori={"S_VA": S, "V_MT_V": V_MT},
            risultato=round(In_MT, 3),
            unita="A",
        ),
        TraceStep(
            step=2,
            descrizione="Corrente nominale lato BT",
            formula=f"In_BT = S/({fattore}·V_BT)",
            valori={"S_VA": S, "V_BT_V": V_BT},
            risultato=round(In_BT, 3),
            unita="A",
        ),
        TraceStep(
            step=3,
            descrizione="Icc presunta lato BT (rete a monte infinita)",
            formula="Icc_BT = In_BT/(ucc/100)",
            valori={"In_BT_A": round(In_BT, 3), "ucc": ucc},
            risultato=round(Icc_BT, 1),
            unita="A",
        ),
    ]

    note = [
        "Icc lato BT in ipotesi di RETE A MONTE INFINITA (impedenza della rete trascurata).",
        "Affinamento con Scc_MT (potenza di cortocircuito della rete a monte) e fattore di "
        "tensione c (IEC 60909-0) NON eseguito: richiede parametri groundati non forniti -> "
        "GAP dichiarato, non calcolato.",
    ]
    norma = (
        "CEI EN 60076-1 (tensione di cortocircuito ucc) · "
        "IEC 60909-0 (Icc presunta, ipotesi rete a monte infinita)"
    )
    formula = f"In = S/({fattore}·Un); Icc_BT = In_BT/(ucc/100)"

    trace = build_trace(norma=norma, formula=formula, steps=steps, inputs=inp.model_dump(), gap=note)
    calc = CalcResult(
        valore=round(Icc_BT, 1), unita="A", formula="Icc_BT = In_BT/(ucc/100)", steps=steps
    ).model_dump()

    return VerificaTrafoOutput(
        In_MT_A=round(In_MT, 3),
        In_BT_A=round(In_BT, 3),
        Icc_BT_A=round(Icc_BT, 1),
        Icc_BT_kA=round(Icc_BT / 1000.0, 3),
        rete_monte_infinita=True,
        note=note,
        calc_Icc_BT=calc,
        trace=trace,
    )
