"""Trace strutturato per i tool MT (nuovo standard, ADDITIVO e backward-compatible).

`CalcResult` / `TraceStep` / `inputs_hash` danno ancoraggio e ripercorribilità,
necessari per la liability MT. Il dizionario `trace` di output resta però
BACKWARD-COMPATIBLE: include SEMPRE `norma` e `formula` nella forma già consumata
dal gateway (come i tool BT `cavo`/`caduta_v`), così la verifica BT non cambia.

I tool BT NON vengono migrati a questo standard in questa fase: una eventuale
migrazione del trace BT sarà una slice dedicata e testata a sé, mai un effetto
collaterale dei tool MT.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, Field


class TraceStep(BaseModel):
    step: int
    descrizione: str
    formula: str
    valori: dict[str, Any] = Field(default_factory=dict)
    risultato: float
    unita: str


class CalcResult(BaseModel):
    valore: float
    unita: str
    formula: str
    steps: list[TraceStep] = Field(default_factory=list)


def inputs_hash(inputs: dict[str, Any]) -> str:
    payload = json.dumps(inputs, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def build_trace(
    norma: str,
    formula: str,
    steps: list[TraceStep],
    inputs: dict[str, Any],
    gap: list[str] | None = None,
) -> dict[str, Any]:
    """Costruisce il `trace` di output.

    Backward-compatible (le chiavi `norma` e `formula` in chiaro, come i tool BT,
    sono ciò che il gateway legge) + ricco (`steps`/`inputs_hash`/`gap`).
    """
    return {
        # --- consumato dal gateway (identico ai tool BT) ---
        "norma": norma,
        "formula": formula,
        # --- ricco (additivo) ---
        "steps": [s.model_dump() for s in steps],
        "inputs_hash": inputs_hash(inputs),
        "gap": gap or [],
        "schema": "CalcResult/TraceStep/inputs_hash v1",
    }
