"""Verdetto combinato sezione c.a. — aggrega flessione + taglio + fessurazione + interazione.

Aggrega gli η dei check c.a. (flessione SLU, taglio SLU, fessurazione SLE, confinamento) in un
**verdetto cls unico** OK/NV per il fascicolo, con check governante. Per pressoflessione deviata
o interazione N+M+V usa un'interazione semplificata sul dominio (somma quadratica opzionale).

Orchestratore: alimentato da check_rc_flexure, check_rc_shear, check_rc_cracking,
check_rc_confinement. Anchor K2A foglio 13 (parte cls). Pattern analogo a
check_serviceability_combined (W6).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep


class CheckRC(BaseModel):
    nome: str = Field(..., description="es. 'flessione SLU', 'taglio SLU', 'fessurazione SLE'")
    eta: float = Field(..., ge=0, description="Coefficiente di sfruttamento η = E/R")
    tipo: Literal["SLU", "SLE"] = "SLU"
    applicabile: bool = True


class CheckCapacityCombinedRcInput(BaseModel):
    checks: list[CheckRC] = Field(..., min_length=1)
    interazione_quadratica: bool = Field(
        False, description="Se True somma quadratica degli η SLU correlati (N+M+V) invece del max"
    )


class DettaglioRC(BaseModel):
    nome: str
    eta: float
    tipo: str
    verdetto: str  # OK | NV | NA


class CheckCapacityCombinedRcOutput(CalcResult):
    dettaglio: list[DettaglioRC] = Field(default_factory=list)
    eta_SLU_max: float | None = None
    eta_SLE_max: float | None = None
    eta_interazione: float | None = None
    verdetto_rc: str = ""  # OK | NV | INCONCLUSIVO
    check_governante: str | None = None
    verifica_ok: bool = False


def check_capacity_combined_rc(
    inp: CheckCapacityCombinedRcInput,
) -> CheckCapacityCombinedRcOutput:
    out = CheckCapacityCombinedRcOutput(
        tool="check_capacity_combined_rc", inputs_hash=compute_inputs_hash(inp))

    dettaglio: list[DettaglioRC] = []
    eta_slu, eta_sle = [], []
    gov = None
    eta_max_global = -1.0
    n_appl = 0

    for c in inp.checks:
        if not c.applicabile:
            dettaglio.append(DettaglioRC(nome=c.nome, eta=c.eta, tipo=c.tipo, verdetto="NA"))
            continue
        n_appl += 1
        verdetto = "OK" if c.eta <= 1.0 else "NV"
        dettaglio.append(DettaglioRC(nome=c.nome, eta=c.eta, tipo=c.tipo, verdetto=verdetto))
        if c.tipo == "SLU":
            eta_slu.append((c.eta, c.nome))
        else:
            eta_sle.append((c.eta, c.nome))
        if c.eta > eta_max_global:
            eta_max_global = c.eta
            gov = c.nome

    out.dettaglio = dettaglio
    out.eta_SLU_max = max((e for e, _ in eta_slu), default=None)
    out.eta_SLE_max = max((e for e, _ in eta_sle), default=None)

    # interazione quadratica opzionale sugli SLU correlati (es. N+M+V)
    if inp.interazione_quadratica and eta_slu:
        eta_int = sum(e * e for e, _ in eta_slu) ** 0.5
        out.eta_interazione = eta_int
        if eta_int > eta_max_global:
            eta_max_global = eta_int
            gov = "interazione SLU (somma quadratica)"

    if n_appl == 0:
        out.verdetto_rc = "INCONCLUSIVO"
        out.warnings.append("Tutti i check non applicabili (NA): verdetto c.a. inconcludente.")
    else:
        out.verdetto_rc = "OK" if eta_max_global <= 1.0 else "NV"
        out.verifica_ok = eta_max_global <= 1.0
        out.check_governante = gov

    out.trace.append(TraceStep(
        label="verdetto c.a. combinato",
        formula="verdetto = NV se ∃ η>1 ; governante = max(η) ; [interazione quadratica opz.]",
        substitution="; ".join(f"{d.nome}={d.eta:.3f}({d.verdetto})" for d in dettaglio),
        value=eta_max_global if eta_max_global >= 0 else 0.0, unit="-",
        norm_ref="EC2 §6.1/§6.2/§7.3 + NTC §4.1.2 — verdetto di fascicolo",
    ))

    # Sanity rules (§12.13)
    if n_appl > 0 and eta_max_global > 5.0:
        out.warnings.append(
            f"η massimo {eta_max_global:.1f} ≫ 1 su '{gov}': sezione fortemente insufficiente."
        )
    nv = [d.nome for d in dettaglio if d.verdetto == "NV"]
    if len(nv) > 1:
        out.warnings.append(f"Più check c.a. NV ({', '.join(nv)}): revisione della sezione necessaria.")

    out.primary_value = eta_max_global if eta_max_global >= 0 else 0.0
    out.primary_unit = "-"
    return out
