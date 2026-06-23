"""Tool `lookup_formula` — catalogo formule strutturali indicizzate.

Sostituisce la skill vs-catalogo-formule. 50+ formule da NTC 2018, EC3, EC2,
EC1, CNR-DT 207 indicizzate per categoria + simbolo + parole chiave.
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .schemas import CalcResult, TraceStep

FORMULE_PATH = Path(__file__).parent.parent.parent / "data" / "formule_catalog.json"


class LookupFormulaInput(BaseModel):
    query: str | None = Field(
        None,
        description="Parole chiave (es. 'punzonamento', 'vortex', 'Miner')",
    )
    categoria: Literal[
        "vento", "sismica", "combinazioni", "geometria", "resistenza",
        "stabilita", "bulloni", "ancoraggi", "sle", "fatica", "fondazione",
        "tutte",
    ] = "tutte"
    simbolo: str | None = Field(None, description="Filtro per simbolo esatto (es. 'M_pl,Rd')")
    id_formula: str | None = Field(None, description="ID univoco se noto")


class LookupFormulaOutput(CalcResult):
    n_risultati: int = 0
    formule: list[dict] = Field(default_factory=list)


_CACHE: list[dict] | None = None


def _load_catalog() -> list[dict]:
    global _CACHE
    if _CACHE is None:
        _CACHE = json.loads(FORMULE_PATH.read_text())
    return _CACHE


def lookup_formula(inp: LookupFormulaInput) -> LookupFormulaOutput:
    out = LookupFormulaOutput(tool="lookup_formula", inputs_hash=compute_inputs_hash(inp))
    if not FORMULE_PATH.exists():
        out.out_of_scope = True
        out.out_of_scope_reason = f"Catalogo non trovato: {FORMULE_PATH}"
        return out

    catalog = _load_catalog()

    if inp.id_formula:
        out.formule = [f for f in catalog if f["id"] == inp.id_formula]
    else:
        out.formule = catalog
        if inp.categoria != "tutte":
            out.formule = [f for f in out.formule if f["categoria"] == inp.categoria]
        if inp.simbolo:
            sym = inp.simbolo.strip().lower().replace(" ", "")
            out.formule = [
                f for f in out.formule
                if f["simbolo"].lower().replace(" ", "") == sym
            ]
        if inp.query:
            q = inp.query.lower()
            out.formule = [
                f for f in out.formule
                if q in f["nome"].lower() or q in f["formula"].lower()
                or q in f.get("norm_ref", "").lower() or q in f["simbolo"].lower()
            ]

    out.n_risultati = len(out.formule)
    out.trace.append(TraceStep(
        label="lookup formula",
        formula="catalog filter (id ∪ categoria ∪ simbolo ∪ query)",
        substitution=(
            f"cat={inp.categoria}, sim={inp.simbolo}, q='{inp.query}', "
            f"id={inp.id_formula} → {out.n_risultati} risultati"
        ),
        value=float(out.n_risultati), unit="formule",
        norm_ref="Catalogo K2A — NTC 2018 + EC + CNR-DT 207",
    ))
    out.primary_value = float(out.n_risultati)
    return out
