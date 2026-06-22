"""Envelope CalcResult — contratto di provenienza per i tool budget.

Copia verbatim del pattern di k2a-quant (call_id univoco, inputs_hash riproducibilità,
snapshot_as_of staleness visibile, trace passi+formula+valori, warnings).
Su errore: campo `errore` invece di `outputs`, mai eccezioni sullo stdio.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time
from typing import Any, Optional

_TOOL_VERSION = "0.1.0"


def make_call_id(tool: str) -> str:
    return f"b-{time.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"


def inputs_hash(inputs: dict) -> str:
    blob = json.dumps(inputs, sort_keys=True, default=str, ensure_ascii=False)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def calc_result(
    tool: str,
    inputs: dict,
    outputs: Optional[dict] = None,
    *,
    snapshot_as_of: Any = None,
    trace: Optional[list] = None,
    warnings: Optional[list] = None,
    errore: Optional[dict] = None,
    tool_version: str = _TOOL_VERSION,
) -> dict:
    env: dict[str, Any] = {
        "call_id": make_call_id(tool),
        "tool": tool,
        "tool_version": tool_version,
        "inputs_hash": inputs_hash(inputs),
        "snapshot_as_of": snapshot_as_of,
        "trace": trace or [],
        "warnings": warnings or [],
    }
    if errore is not None:
        env["errore"] = errore
    else:
        env["outputs"] = outputs or {}
    return env
