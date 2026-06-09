"""Verdetto SLE combinato — aggrega i check di esercizio in un esito unico per fascicolo.

Combina più verifiche SLE (deflessione testa, rotazione testa, frequenza propria/comfort,
cedimenti, ...) in un verdetto complessivo OK/NV con tabella di dettaglio e check governante.

Ogni check ha un verso:
  - "max": OK se valore ≤ limite (deflessione, rotazione: il valore non deve superare il limite)
  - "min": OK se valore ≥ limite (frequenza comfort: deve stare sopra una soglia minima)

ratio = valore/limite ("max") | limite/valore ("min"). verdetto = OK se ratio ≤ 1.
Aggregato: NV se almeno un check applicabile è NV; governante = check con ratio massimo.

Orchestratore: tipicamente alimentato da check_sls_deflection (W1), check_modal_complete (W6),
check_settlement (W5). Anchor K2A: foglio 23 (azioni SLE vento 100 km/h) + foglio 22 (limiti).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep


class CheckSLE(BaseModel):
    nome: str = Field(..., description="es. 'deflessione testa', 'rotazione MW', 'frequenza comfort'")
    valore: float = Field(..., description="Valore di progetto della grandezza SLE")
    limite: float = Field(..., gt=0, description="Limite SLE (sempre > 0)")
    unita: str = Field("", description="es. 'mm', '°', 'Hz'")
    verso: Literal["max", "min"] = Field("max", description="max: val≤lim ; min: val≥lim")
    applicabile: bool = Field(True, description="False se il check non è pertinente per questo caso")


class CheckServiceabilityCombinedInput(BaseModel):
    checks: list[CheckSLE] = Field(..., min_length=1)


class DettaglioSLE(BaseModel):
    nome: str
    valore: float
    limite: float
    unita: str
    ratio: float
    verdetto: str  # OK | NV | NA


class CheckServiceabilityCombinedOutput(CalcResult):
    dettaglio: list[DettaglioSLE] = Field(default_factory=list)
    verdetto_sle_complessivo: str = ""  # OK | NV | INCONCLUSIVO
    check_governante: str | None = None
    ratio_massimo: float | None = None
    n_check_nv: int = 0


def check_serviceability_combined(
    inp: CheckServiceabilityCombinedInput,
) -> CheckServiceabilityCombinedOutput:
    out = CheckServiceabilityCombinedOutput(
        tool="check_serviceability_combined", inputs_hash=compute_inputs_hash(inp))

    if not inp.checks:
        raise ValueError("Lista checks vuota.")

    dettaglio: list[DettaglioSLE] = []
    ratio_max = -1.0
    gov = None
    n_nv = 0
    n_applicabili = 0

    for c in inp.checks:
        if not c.applicabile:
            dettaglio.append(DettaglioSLE(nome=c.nome, valore=c.valore, limite=c.limite,
                                          unita=c.unita, ratio=0.0, verdetto="NA"))
            continue
        n_applicabili += 1
        if c.verso == "max":
            ratio = abs(c.valore) / c.limite
        else:  # min
            ratio = c.limite / abs(c.valore) if c.valore != 0 else float("inf")
        verdetto = "OK" if ratio <= 1.0 else "NV"
        if verdetto == "NV":
            n_nv += 1
        if ratio > ratio_max:
            ratio_max = ratio
            gov = c.nome
        dettaglio.append(DettaglioSLE(nome=c.nome, valore=c.valore, limite=c.limite,
                                      unita=c.unita, ratio=ratio, verdetto=verdetto))

    out.dettaglio = dettaglio
    out.n_check_nv = n_nv

    if n_applicabili == 0:
        out.verdetto_sle_complessivo = "INCONCLUSIVO"
        out.warnings.append("Tutti i check non applicabili (NA): verdetto SLE inconcludente.")
    else:
        out.verdetto_sle_complessivo = "NV" if n_nv > 0 else "OK"
        out.check_governante = gov
        out.ratio_massimo = ratio_max

    out.trace.append(TraceStep(
        label="verdetto SLE combinato",
        formula="verdetto = NV se ∃ check NV ; governante = max(ratio)",
        substitution="; ".join(f"{d.nome}={d.ratio:.3f}({d.verdetto})" for d in dettaglio),
        value=ratio_max if ratio_max >= 0 else 0.0, unit="-",
        norm_ref="NTC 2018 §3.3 + §7.3.6 (SLE) — verdetto di fascicolo",
    ))

    # Sanity rules (§12.13)
    if n_applicabili > 0 and ratio_max > 5.0:
        out.warnings.append(
            f"ratio massimo {ratio_max:.1f} > 5 su '{gov}': SLE fortemente non soddisfatto, "
            "ridimensionamento necessario."
        )
    if n_nv > 0 and n_nv == n_applicabili:
        out.warnings.append("Tutti i check SLE applicabili sono NV: revisione globale del progetto.")

    out.primary_value = ratio_max if ratio_max >= 0 else 0.0
    out.primary_unit = "-"
    return out
