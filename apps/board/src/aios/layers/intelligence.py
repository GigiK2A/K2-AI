from __future__ import annotations

import json
from typing import Any

from aios.llm import LLM

_SYSTEM = ("Sei l'analista dell'AIOS K2. Dato il contesto e i dati reali, estrai "
           "gli insight che contano (cosa funziona, cosa no, perché) con evidenza e "
           "azione consigliata. Rispondi SOLO JSON: "
           '{"insights":[{"titolo":"...","evidenza":"...","azione":"..."}]}')


class IntelligenceLayer:
    """Strato (3) Intelligence: trasforma dati+contesto in insight con evidenza."""

    def __init__(self, llm: LLM) -> None:
        self.llm = llm

    def insights(self, *, context: str, data: dict[str, Any]) -> list[dict]:
        user = (context + "\n\n# DATI\n" + json.dumps(data, ensure_ascii=False)[:6000]
                + "\n\nEstrai 3-6 insight con evidenza dai numeri e azione.")
        try:
            parsed = self.llm.complete_json(system=_SYSTEM, user=user)
        except Exception:
            return []
        out = parsed.get("insights", [])
        return [i for i in out if isinstance(i, dict)] if isinstance(out, list) else []
