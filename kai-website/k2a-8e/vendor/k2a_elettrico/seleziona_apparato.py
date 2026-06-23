"""Tool MCP `seleziona_apparato` (MT-E2): proposta articoli reali dal requisito.

Dato il requisito tipicamente derivato da `dimensiona_cavo` (In >= corrente di
impiego/protezione, curva, potere di interruzione >= Icc nel punto), propone gli
articoli REALI del DB articoli (MT-E1) che lo soddisfano, ordinati dal piu'
piccolo adeguato. Ogni articolo porta la sua **fonte**. Nessun valore inventato:
cio' che non e' nel DB non viene proposto.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .articoli_db import db_da_seed, query


class SelezionaApparatoInput(BaseModel):
    In_min_A: float = Field(..., description="In minima richiesta (>= corrente impiego/protezione da dimensiona_cavo)")
    potere_min_kA: float = Field(..., description="potere di interruzione minimo Icn (>= Icc nel punto)")
    curva: Optional[str] = Field(None, description="caratteristica richiesta: B/C/D")
    costruttore: Optional[str] = Field(None, description="es. 'ABB'")
    tipo_dispositivo: Optional[str] = Field("interruttore_magnetotermico")
    poli: Optional[int] = Field(None, description="numero poli richiesto")


class SelezionaApparatoOutput(BaseModel):
    requisito: dict
    totale: int
    proposta: list[dict]
    trace: dict
    nota: str


def seleziona_apparato(inp: SelezionaApparatoInput) -> SelezionaApparatoOutput:
    conn = db_da_seed()
    try:
        ris = query(
            conn,
            costruttore=inp.costruttore,
            tipo_dispositivo=inp.tipo_dispositivo,
            In_min=inp.In_min_A,
            curva=inp.curva,
            poli=inp.poli,
            potere_min_kA=inp.potere_min_kA,
        )
    finally:
        conn.close()

    # piu' piccolo adeguato prima (In crescente, poi potere)
    ris.sort(key=lambda a: (a["In_A"], a["potere_int_Icn_kA"]))

    return SelezionaApparatoOutput(
        requisito=inp.model_dump(exclude_none=True),
        totale=len(ris),
        proposta=ris,
        trace={
            "norma": "selezione da DB articoli reali; coordinamento CEI 64-8 (In>=Ib, Icn>=Icc)",
            "metodo": "filtro DB articoli: In>=In_min, curva, Icn>=potere_min; ordinato per In crescente",
            "fonte_dati": "campo 'fonte' di ogni articolo proposto",
        },
        nota=(
            "Proposta di articoli REALI dal DB con fonte. Requisito tipicamente da dimensiona_cavo "
            "(In>=, curva, potere>=Icc). Cio' che non e' nel DB non e' proposto (mai inventato)."
        ),
    )
