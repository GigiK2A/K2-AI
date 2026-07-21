"""Contratto tipizzato del payload di handoff CONSULENZA_SUMMARY (review flusso deliverable).

Il summary NON è un messaggio da mostrare: è il PAYLOAD strutturato che attiva la
generazione. Qui: uno schema Pydantic tollerante che (a) valida il JSON estratto dal blocco,
(b) porta un oggetto `generation` (requested / confirmedByUser / requiredOutputs) che rende
il TRIGGER strutturato e indipendente dal testo naturale del modello, (c) espone una
`summary_version` deterministica per l'idempotenza dei job.

Tollerante di proposito: i campi di analisi sono opzionali (una consulenza può produrre un
summary parziale valido). Un input non-dict o non parsabile → INVALID_SUMMARY, mai un crash.
"""
from __future__ import annotations

import hashlib
import json
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

_VALID_OUTPUTS = ("pdf", "xlsx", "docx")


class GenerationSpec(BaseModel):
    """Trigger STRUTTURATO della generazione (non 'scarica il deliverable' nel testo)."""
    model_config = ConfigDict(extra="ignore")
    requested: bool = True
    confirmedByUser: bool = False
    requiredOutputs: list[str] = Field(default_factory=lambda: ["pdf", "xlsx"])

    @field_validator("requiredOutputs", mode="before")
    @classmethod
    def _norm_outputs(cls, v):
        if not v:
            return ["pdf", "xlsx"]
        if isinstance(v, str):
            v = [v]
        outs = [str(o).strip().lower() for o in v if str(o).strip()]
        outs = [o for o in outs if o in _VALID_OUTPUTS]
        # dedup preservando l'ordine
        seen, ordered = set(), []
        for o in outs:
            if o not in seen:
                seen.add(o); ordered.append(o)
        return ordered or ["pdf", "xlsx"]


class ConsulenzaSummary(BaseModel):
    """Payload di handoff consulenza→generazione. Campi di analisi opzionali."""
    model_config = ConfigDict(extra="allow")
    reportType: Optional[str] = None
    businessType: Optional[str] = None
    objective: Optional[str] = None
    scope: Optional[str] = None
    dataAvailable: Optional[str] = None
    deadline: Optional[str] = None
    notes: Optional[str] = None
    summary: Optional[str] = None
    nextStep: Optional[str] = None
    generation: GenerationSpec = Field(default_factory=GenerationSpec)


def validate_summary(raw: object) -> tuple[Optional[ConsulenzaSummary], Optional[str]]:
    """(modello, None) se valido; (None, errore leggibile) altrimenti — MAI solleva.
    L'errore alimenta lo stato INVALID_SUMMARY, il summary grezzo va loggato dal chiamante."""
    if raw is None:
        return None, "summary assente"
    if not isinstance(raw, dict):
        return None, f"summary non è un oggetto JSON (tipo {type(raw).__name__})"
    try:
        return ConsulenzaSummary.model_validate(raw), None
    except ValidationError as e:
        return None, "; ".join(f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}"
                               for err in e.errors()[:6]) or "summary non valido"


def summary_version(raw: object) -> str:
    """Hash STABILE dei campi di analisi del summary → chiave d'idempotenza. Ignora la
    sezione `generation` (che non cambia il deliverable) e i campi non deterministici."""
    if not isinstance(raw, dict):
        return "invalid"
    stable = {k: raw.get(k) for k in
              ("reportType", "businessType", "objective", "scope", "dataAvailable", "notes")}
    blob = json.dumps(stable, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]


def required_outputs(raw: object) -> list[str]:
    """Output richiesti dal summary (default pdf+xlsx). Robusto a summary invalidi."""
    model, err = validate_summary(raw)
    if model is None:
        return ["pdf", "xlsx"]
    return list(model.generation.requiredOutputs)


def generation_allowed(raw: object) -> bool:
    """True se la generazione è richiesta dal payload strutturato (`generation.requested`).
    Indipendente dal testo naturale: «scarica il deliverable» non conta, `requested` sì."""
    model, err = validate_summary(raw)
    if model is None:
        return False
    return bool(model.generation.requested)
