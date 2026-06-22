"""Direzione KB → Tool (Tappa 2 Fase 2).

Dato un riferimento normativo (norma + paragrafo), suggerisce quali tool MCP del
principale sono applicabili, leggendo lo snapshot `KB_REFERENCES_BY_TOOL`.

Use case: l'utente trova "CEI 64-8 §433.1" nella KB e chiede «quale tool uso?».
Il sistema risponde: verifica_protezione, dimensiona_cavo (coordinamento).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ._kb_mapping import KB_REFERENCES_BY_TOOL


class SuggerisciToolInput(BaseModel):
    norma: str = Field(..., description="es. 'CEI 64-8:2024' (anche parziale, es. 'CEI 64-8')")
    paragrafo: str = Field(..., description="es. '433.1', '525', '5.3.5', 'C.2'")
    match_paragrafo: Literal["esatto", "prefisso", "fuzzy"] = Field(
        "prefisso", description="strategia di match sul paragrafo")


class ToolSuggerito(BaseModel):
    nome_tool: str
    motivazione: str
    contesto_uso: str
    paragrafo_match: str
    norma_match: str


class SuggerisciToolOutput(BaseModel):
    norma: str
    paragrafo: str
    tool_suggeriti: list[ToolSuggerito]
    n_match: int
    note: list[str] = Field(default_factory=list)


def _norma_match(req: str, ref: str) -> bool:
    return req == ref or req in ref or ref in req


def _par_match(req: str, ref: str, mode: str) -> bool:
    if mode == "esatto":
        return req == ref
    if mode == "prefisso":
        return ref.startswith(req) or req.startswith(ref)
    return req in ref or ref in req  # fuzzy


def suggerisci_tool_da_paragrafo(inp: SuggerisciToolInput) -> SuggerisciToolOutput:
    """Cerca quali tool MCP citano (norma, paragrafo) nei loro riferimenti KB."""
    matches: list[ToolSuggerito] = []
    for tool_name, refs in KB_REFERENCES_BY_TOOL.items():
        for ref in refs:
            if not _norma_match(inp.norma, ref["norma"]):
                continue
            if not _par_match(inp.paragrafo, ref["paragrafo"], inp.match_paragrafo):
                continue
            matches.append(ToolSuggerito(
                nome_tool=tool_name,
                motivazione=f"{tool_name} cita {ref['norma']} §{ref['paragrafo']} "
                            f"({ref['titolo']})",
                contesto_uso=ref["contesto_uso"],
                paragrafo_match=ref["paragrafo"],
                norma_match=ref["norma"],
            ))

    note: list[str] = []
    if not matches:
        note.append(
            f"Nessun tool del MCP principale cita {inp.norma} §{inp.paragrafo}. "
            "Potrebbe essere coperto da tool non ancora mappati in KB, o norma non gestita."
        )
    return SuggerisciToolOutput(
        norma=inp.norma, paragrafo=inp.paragrafo,
        tool_suggeriti=matches, n_match=len(matches), note=note,
    )
