"""Hashing deterministico degli input dei tool (quick win B2).

Centralizza la logica prima duplicata ~24 volte come `_hash()`/`_hash_inputs()`
nei singoli moduli tool. Avere un'unica implementazione elimina il rischio che
una variante diverga e rompa il determinismo bit-per-bit (Masterplan §5.1).

ATTENZIONE — convenzione di serializzazione invariata di proposito:
    json.dumps(payload, sort_keys=True, default=str)
con i SEPARATORI DI DEFAULT (", " / ": "), NON quelli compatti. Questa è la forma
storicamente usata dai moduli tool: cambiarla (es. separators=(",",":")) altererebbe
ogni inputs_hash e romperebbe la riproducibilità degli audit trail già emessi.
`default=str` è un superset innocuo: per input JSON-nativi (come sono tutti quelli
attuali) produce byte identici alla forma senza `default`.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_inputs_hash(inputs: Any) -> str:
    """SHA256 deterministico degli input, troncato a 16 char hex.

    Accetta sia un modello pydantic (di cui usa `model_dump()`) sia un dict già
    serializzabile, così da sostituire 1:1 le vecchie chiamate `_hash(inp)`.
    """
    payload = inputs.model_dump() if hasattr(inputs, "model_dump") else inputs
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
