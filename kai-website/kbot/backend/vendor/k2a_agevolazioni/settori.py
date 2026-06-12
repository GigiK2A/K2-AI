"""Settori industriali delle PMI — tassonomia condivisa.

I servizi K2-AI si dividono in due ambiti:
  - TRASVERSALI: marketing, SEO, finanza, agevolazioni — validi per tutti i settori;
  - SETTORIALI: servizi calati sullo specifico comparto industriale della PMI.

Questo modulo espone la tassonomia dei settori PMI e una helper per risolvere
l'etichetta di un settore, usata per contestualizzare i documenti.
"""
from __future__ import annotations
import json
from pathlib import Path
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "settori_pmi.json").read_text())
_SETTORI = _DATA["settori"]


def settore_label(settore_id: str | None) -> str:
    """Etichetta leggibile di un settore; stringa vuota se assente, raw se non in registro."""
    if not settore_id:
        return ""
    node = _SETTORI.get(settore_id)
    return node["label"] if node else settore_id


def settore_valido(settore_id: str | None) -> bool:
    return bool(settore_id) and settore_id in _SETTORI


class ListaSettoriInput(BaseModel):
    pass


class SettoreOut(BaseModel):
    id: str
    label: str
    ateco: str
    descrizione: str


class ListaSettoriOutput(BaseModel):
    settori: list[SettoreOut]
    n: int
    nota: str
    trace: dict


def lista_settori_pmi(inp: ListaSettoriInput | None = None) -> ListaSettoriOutput:
    settori = [
        SettoreOut(id=k, label=v["label"], ateco=v["ateco"], descrizione=v["descrizione"])
        for k, v in _SETTORI.items()
    ]
    return ListaSettoriOutput(
        settori=settori, n=len(settori), nota=_DATA["_nota"],
        trace={"fonte_dati": _DATA["_fonte"], "data_validita_dati": _DATA["_data_validita"]},
    )
