"""Tool `get_committenza_spec` — parametri prescrittivi LG iliad / INWIT / Cellnex.

I dati provengono dai JSON in `data_committenze/` estratti dalle LG originali
(commitenza). Quando una skill VS dichiara `committente=iliad/INWIT/Cellnex`,
chiama questo tool per ottenere i default-override da applicare ai calcoli MCP.

Architettura del precedente: i parametri LG sovrascrivono i default NTC base solo
DOVE DICHIARATI. Se la LG non specifica → resta default NTC.
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .schemas import CalcResult, TraceStep

COMMITTENZE_DIR = Path(__file__).parent.parent.parent / "data_committenze"


class GetCommittenzaSpecInput(BaseModel):
    committente: Literal["iliad", "inwit", "cellnex"]
    sezione: str | None = Field(
        None,
        description=(
            "Sezione specifica da estrarre: 'classificazione' | 'vento' | "
            "'sismica' | 'resistenza' | 'sle' | 'dettagli'. Default = tutto."
        ),
    )


class GetCommittenzaSpecOutput(CalcResult):
    committente: str = ""
    versione_LG: str = ""
    data_estrazione: str = ""
    source_documents: list[str] = Field(default_factory=list)
    spec: dict = Field(default_factory=dict)
    parametri_mancanti: list[str] = Field(default_factory=list)


def _find_null_recursive(d, path="") -> list[str]:
    out = []
    if isinstance(d, dict):
        for k, v in d.items():
            p = f"{path}.{k}" if path else k
            if v is None:
                out.append(p)
            elif isinstance(v, (dict, list)):
                out.extend(_find_null_recursive(v, p))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.extend(_find_null_recursive(v, f"{path}[{i}]"))
    return out


def get_committenza_spec(inp: GetCommittenzaSpecInput) -> GetCommittenzaSpecOutput:
    out = GetCommittenzaSpecOutput(tool="get_committenza_spec", inputs_hash=compute_inputs_hash(inp))
    fp = COMMITTENZE_DIR / f"{inp.committente}.json"

    if not fp.exists():
        out.out_of_scope = True
        out.out_of_scope_reason = (
            f"Spec per committente '{inp.committente}' non disponibile in "
            f"{COMMITTENZE_DIR}. Esegui estrazione LG."
        )
        return out

    data = json.loads(fp.read_text())
    out.committente = data.get("committente", inp.committente)
    out.versione_LG = data.get("versione_LG", "?")
    out.data_estrazione = data.get("data_estrazione", "?")
    out.source_documents = data.get("source_documents", [])

    if inp.sezione:
        out.spec = {inp.sezione: data.get(inp.sezione)}
    else:
        # rimuovo metadata, mantengo solo le sezioni parametriche
        meta_keys = {"committente", "versione_LG", "data_estrazione", "source_documents", "note"}
        out.spec = {k: v for k, v in data.items() if k not in meta_keys}

    out.parametri_mancanti = _find_null_recursive(out.spec)

    out.trace.append(TraceStep(
        label="LG committenza",
        formula="lookup specifica prescrittiva committente",
        substitution=(
            f"committente={inp.committente}, versione={out.versione_LG}, "
            f"sezione={inp.sezione or 'TUTTA'}, "
            f"parametri null = {len(out.parametri_mancanti)}"
        ),
        value=len(out.parametri_mancanti), unit="parametri_mancanti",
        norm_ref=(
            f"LG {inp.committente.upper()} v.{out.versione_LG} "
            f"({', '.join(out.source_documents[:1])})"
        ),
    ))
    out.primary_value = len(out.parametri_mancanti)
    out.primary_unit = "parametri_mancanti"
    return out
