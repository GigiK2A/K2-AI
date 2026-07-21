"""Macchina a stati del deliverable + chiave d'idempotenza (review flusso deliverable).

Lo stato NON si deduce dal testo del modello: è PERSISTENTE sul record consulenza
(`collected_data`), quindi sopravvive a refresh, timeout e riapertura sessione. Modulo PURO.

Flusso nominale:  CONSULTING → DIAGNOSIS_COMPLETE → READY_FOR_GENERATION → GENERATING → COMPLETED
Stati d'errore:   GENERATION_FAILED · INVALID_SUMMARY · MISSING_REQUIRED_DATA
"""
from __future__ import annotations

from typing import Optional

CONSULTING = "CONSULTING"
DIAGNOSIS_COMPLETE = "DIAGNOSIS_COMPLETE"
READY_FOR_GENERATION = "READY_FOR_GENERATION"
GENERATING = "GENERATING"
COMPLETED = "COMPLETED"
# errori
GENERATION_FAILED = "GENERATION_FAILED"
INVALID_SUMMARY = "INVALID_SUMMARY"
MISSING_REQUIRED_DATA = "MISSING_REQUIRED_DATA"

_ALL = {CONSULTING, DIAGNOSIS_COMPLETE, READY_FOR_GENERATION, GENERATING, COMPLETED,
        GENERATION_FAILED, INVALID_SUMMARY, MISSING_REQUIRED_DATA}

_STATE_KEY = "deliverable_state"
_IDEMP_KEY = "deliverable_idempotency_key"
_OUTPUTS_KEY = "deliverable_outputs"


def get_state(collected: Optional[dict]) -> str:
    st = (collected or {}).get(_STATE_KEY)
    return st if st in _ALL else CONSULTING


def set_state(collected: dict, state: str) -> None:
    """Muta collected in-place col nuovo stato (validato)."""
    if state in _ALL:
        collected[_STATE_KEY] = state


def idempotency_key(consultation_id: Optional[str], summary_ver: Optional[str],
                    outputs: Optional[list[str]]) -> str:
    """consultationId + summaryVersion + outputType → chiave per non duplicare i job.
    Stesso caso (stessa conversazione, stesso summary, stessi output) = stessa chiave."""
    outs = "+".join(sorted({str(o).strip().lower() for o in (outputs or []) if str(o).strip()}))
    return f"{consultation_id or '-'}:{summary_ver or '-'}:{outs or 'pdf+xlsx'}"


def existing_job_for(collected: Optional[dict], key: str) -> Optional[str]:
    """job_id già presente per QUESTA chiave d'idempotenza se lo stato è ancora
    'in volo' o 'completato' → il chiamante lo riusa invece di crearne uno nuovo.
    None se non c'è un job riusabile (nuovo caso, o stato d'errore da cui si ri-genera)."""
    collected = collected or {}
    if collected.get(_IDEMP_KEY) != key:
        return None
    if get_state(collected) not in (GENERATING, COMPLETED):
        return None
    return collected.get("deliverable_job_id") or None


def mark_generating(collected: dict, key: str, outputs: list[str]) -> None:
    """Registra l'avvio: stato GENERATING, chiave d'idempotenza, output attesi 'pending'."""
    set_state(collected, GENERATING)
    collected[_IDEMP_KEY] = key
    collected[_OUTPUTS_KEY] = {o: "pending" for o in (outputs or ["pdf", "xlsx"])}


def set_output_status(collected: dict, output: str, status: str) -> None:
    """Stato per singolo output (pdf/xlsx): pending|rendered|failed. Serve al ripiego
    'PDF ok, Excel fallito' → si riprova solo quello fallito."""
    outs = dict(collected.get(_OUTPUTS_KEY) or {})
    outs[str(output).lower()] = status
    collected[_OUTPUTS_KEY] = outs


def outputs_status(collected: Optional[dict]) -> dict:
    return dict((collected or {}).get(_OUTPUTS_KEY) or {})


def reconcile_state(collected: dict) -> str:
    """Aggiorna lo stato aggregato dagli stati dei singoli output. COMPLETED solo quando
    TUTTI gli output obbligatori sono 'rendered'; GENERATION_FAILED se almeno uno è 'failed'
    e nessuno è più 'pending'; altrimenti resta GENERATING."""
    outs = outputs_status(collected)
    if not outs:
        return get_state(collected)
    vals = set(outs.values())
    if vals == {"rendered"}:
        new = COMPLETED
    elif "pending" in vals:
        new = GENERATING
    elif "failed" in vals:
        new = GENERATION_FAILED
    else:
        new = GENERATING
    set_state(collected, new)
    return new
