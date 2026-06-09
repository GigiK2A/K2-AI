"""Combinazioni di carico NTC 2018 §2.5.3.

Implementa SLU fondamentale, SLU sismica, SLE rara/frequente/quasi permanente.
Carichi forniti come dizionario { 'G1': val, 'G2': val, 'Q_k': [...], 'W_k': val, 'E': val, 'A_d': val }.
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash

from typing import Literal

from pydantic import BaseModel, Field

from .schemas import CalcResult, TraceStep

TipoCombinazione = Literal[
    "SLU_fondamentale", "SLU_sismica", "SLU_eccezionale",
    "SLE_rara", "SLE_frequente", "SLE_quasi_permanente",
]


class CombineLoadsInput(BaseModel):
    tipo: TipoCombinazione
    G1: float = Field(0.0, description="Peso proprio strutturali")
    G2: float = Field(0.0, description="Permanenti non strutturali")
    P: float = Field(0.0, description="Pretensione")
    Q_variabili: dict[str, float] = Field(
        default_factory=dict,
        description="Azioni variabili indipendenti: es. {'vento': 100, 'neve': 30}",
    )
    azione_dominante: str | None = Field(None, description="Chiave Q_variabili dominante; se None, max")
    psi_0: dict[str, float] = Field(default_factory=dict, description="ψ_0 raro per ciascuna var")
    psi_1: dict[str, float] = Field(default_factory=dict, description="ψ_1 frequente")
    psi_2: dict[str, float] = Field(default_factory=dict, description="ψ_2 quasi-permanente")
    E_sisma: float = Field(0.0, description="Azione sismica (per SLU sismica)")
    A_d: float = Field(0.0, description="Azione eccezionale")
    gamma_G1: float = 1.30   # NTC Tab. 2.6.I — favorevole 1.0, sfavorevole 1.30
    gamma_G2: float = 1.50
    gamma_Q: float = 1.50
    favorevole: bool = False  # se True usa γ favorevoli (1.0/0.8/0.0)


class CombineLoadsOutput(CalcResult):
    valore_combinazione: float | None = None
    contributo_per_azione: dict[str, float] = Field(default_factory=dict)


def _default_gammas(inp: CombineLoadsInput) -> tuple[float, float, float]:
    if inp.favorevole:
        return (1.0, 0.8, 0.0)
    return (inp.gamma_G1, inp.gamma_G2, inp.gamma_Q)


def compute_combine_loads(inp: CombineLoadsInput) -> CombineLoadsOutput:
    out = CombineLoadsOutput(tool="combine_loads", inputs_hash=compute_inputs_hash(inp))
    g1, g2, gq = _default_gammas(inp)
    contributi: dict[str, float] = {}
    total = 0.0

    # Determina dominante
    Qs = inp.Q_variabili
    if not inp.azione_dominante and Qs:
        dominante = max(Qs, key=lambda k: Qs[k])
    else:
        dominante = inp.azione_dominante

    if inp.tipo == "SLU_fondamentale":
        # γ_G1·G1 + γ_G2·G2 + γ_P·P + γ_Q·Q_dom + Σ γ_Q·ψ_0i·Q_ki
        contributi["G1"] = g1 * inp.G1
        contributi["G2"] = g2 * inp.G2
        contributi["P"]  = 1.0 * inp.P
        if dominante and dominante in Qs:
            contributi[f"Q_{dominante}_dom"] = gq * Qs[dominante]
        for k, v in Qs.items():
            if k == dominante:
                continue
            psi0 = inp.psi_0.get(k, 0.6)
            contributi[f"Q_{k}_psi0"] = gq * psi0 * v
        total = sum(contributi.values())
        out.trace.append(TraceStep(
            label="SLU fond.",
            formula="γ_G1·G1 + γ_G2·G2 + γ_P·P + γ_Q·Q_dom + Σ γ_Q·ψ_0i·Q_ki",
            substitution=f"γ_G1={g1}, γ_G2={g2}, γ_Q={gq}, dominante={dominante}",
            value=total, unit="(coerente con input)",
            norm_ref="NTC 2018 §2.5.3 — eq. 2.5.1, Tab. 2.6.I",
        ))

    elif inp.tipo == "SLU_sismica":
        # E + G1 + G2 + P + Σ ψ_2i·Q_ki
        contributi["E"] = inp.E_sisma
        contributi["G1"] = inp.G1
        contributi["G2"] = inp.G2
        contributi["P"]  = inp.P
        for k, v in Qs.items():
            psi2 = inp.psi_2.get(k, 0.0)
            contributi[f"Q_{k}_psi2"] = psi2 * v
        total = sum(contributi.values())
        out.trace.append(TraceStep(
            label="SLU sismica",
            formula="E + G1 + G2 + P + Σ ψ_2i·Q_ki",
            substitution=f"E={inp.E_sisma}, ψ_2 applicati a {list(Qs)}",
            value=total, unit="(coerente)",
            norm_ref="NTC 2018 §2.5.3 — eq. 2.5.5",
        ))

    elif inp.tipo == "SLE_rara":
        contributi["G1"] = inp.G1; contributi["G2"] = inp.G2; contributi["P"] = inp.P
        if dominante and dominante in Qs:
            contributi[f"Q_{dominante}_dom"] = Qs[dominante]
        for k, v in Qs.items():
            if k == dominante: continue
            contributi[f"Q_{k}_psi0"] = inp.psi_0.get(k, 0.6) * v
        total = sum(contributi.values())
        out.trace.append(TraceStep(
            label="SLE rara", formula="G1+G2+P+Q_dom+Σψ_0·Q",
            substitution=f"dominante={dominante}", value=total, unit="-",
            norm_ref="NTC 2018 §2.5.3 — eq. 2.5.2",
        ))

    elif inp.tipo == "SLE_frequente":
        contributi["G1"] = inp.G1; contributi["G2"] = inp.G2; contributi["P"] = inp.P
        if dominante and dominante in Qs:
            contributi[f"Q_{dominante}_psi1"] = inp.psi_1.get(dominante, 0.5) * Qs[dominante]
        for k, v in Qs.items():
            if k == dominante: continue
            contributi[f"Q_{k}_psi2"] = inp.psi_2.get(k, 0.0) * v
        total = sum(contributi.values())
        out.trace.append(TraceStep(
            label="SLE freq.", formula="G1+G2+P+ψ_1·Q_dom+Σψ_2·Q",
            substitution=f"dominante={dominante}", value=total, unit="-",
            norm_ref="NTC 2018 §2.5.3 — eq. 2.5.3",
        ))

    elif inp.tipo == "SLE_quasi_permanente":
        contributi["G1"] = inp.G1; contributi["G2"] = inp.G2; contributi["P"] = inp.P
        for k, v in Qs.items():
            contributi[f"Q_{k}_psi2"] = inp.psi_2.get(k, 0.0) * v
        total = sum(contributi.values())
        out.trace.append(TraceStep(
            label="SLE q.perm.", formula="G1+G2+P+Σψ_2·Q",
            substitution="", value=total, unit="-",
            norm_ref="NTC 2018 §2.5.3 — eq. 2.5.4",
        ))

    elif inp.tipo == "SLU_eccezionale":
        contributi["G1"] = inp.G1; contributi["G2"] = inp.G2; contributi["P"] = inp.P
        contributi["A_d"] = inp.A_d
        for k, v in Qs.items():
            psi2 = inp.psi_2.get(k, 0.0)
            contributi[f"Q_{k}_psi2"] = psi2 * v
        total = sum(contributi.values())
        out.trace.append(TraceStep(
            label="SLU eccez.", formula="G1+G2+P+A_d+Σψ_2·Q",
            substitution=f"A_d={inp.A_d}", value=total, unit="-",
            norm_ref="NTC 2018 §2.5.3",
        ))

    out.contributo_per_azione = contributi
    out.valore_combinazione = total
    out.primary_value = total
    out.primary_unit = "(coerente con input)"
    return out
