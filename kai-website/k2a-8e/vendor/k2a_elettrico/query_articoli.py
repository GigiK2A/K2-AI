"""Tool MCP `query_articoli` (MT-E1): interroga il DB articoli per requisito.

Dati SOLO reali con fonte (seed groundato da datasheet/pagine prodotto costruttore).
Nessun valore inventato: cio' che non e' nel seed non viene restituito.
Questo tool NON fa selettivita'/filiazione (MT-E2) ne' calcoli normativi: e' un
lookup di catalogo con tracciabilita' della fonte.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .articoli_db import db_da_seed, query


class QueryArticoliInput(BaseModel):
    costruttore: Optional[str] = Field(None, description="es. 'ABB' (case-insensitive)")
    tipo_dispositivo: Optional[str] = Field(None, description="es. 'interruttore_magnetotermico'")
    In_A: Optional[float] = Field(None, description="corrente nominale ESATTA (A)")
    In_min: Optional[float] = Field(None, description="corrente nominale minima (A)")
    In_max: Optional[float] = Field(None, description="corrente nominale massima (A)")
    curva: Optional[str] = Field(None, description="caratteristica di intervento: B/C/D/K/Z")
    poli: Optional[int] = Field(None, description="numero poli: 1/2/3/4")
    potere_min_kA: Optional[float] = Field(None, description="potere di interruzione minimo Icn (kA, EN 60898-1)")


class QueryArticoliOutput(BaseModel):
    requisito: dict
    totale: int
    articoli: list[dict]
    trace: dict
    nota: str


def query_articoli(inp: QueryArticoliInput) -> QueryArticoliOutput:
    conn = db_da_seed()
    try:
        ris = query(
            conn,
            costruttore=inp.costruttore,
            tipo_dispositivo=inp.tipo_dispositivo,
            In_A=inp.In_A,
            In_min=inp.In_min,
            In_max=inp.In_max,
            curva=inp.curva,
            poli=inp.poli,
            potere_min_kA=inp.potere_min_kA,
        )
    finally:
        conn.close()

    return QueryArticoliOutput(
        requisito=inp.model_dump(exclude_none=True),
        totale=len(ris),
        articoli=ris,
        trace={
            "norma": "dato di catalogo costruttore (datasheet) - nessun calcolo/giudizio normativo",
            "formula": "filtro SQL su DB articoli (SQLite) costruito dal seed groundato",
            "fonte_dati": "campo 'fonte' di ogni articolo (URL pagina prodotto/datasheet)",
        },
        nota=(
            "Dati reali da datasheet con fonte dichiarata per ogni articolo. "
            "Cio' che non e' nel seed non e' restituito (mancante = non caricato, mai inventato)."
        ),
    )
