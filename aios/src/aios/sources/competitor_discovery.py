from __future__ import annotations

import json
import re

from aios.founder import FounderModel
from aios.llm import LLM

_SYSTEM = (
    "Sei un analista di mercato. Dato il profilo dell'azienda, individua i "
    "competitor/riferimenti italiani che pubblicano su Instagram nello stesso "
    "spazio (AI operativa per PMI, automazione, studi/agenzie AI). "
    "Usa la ricerca web se disponibile. "
    'Rispondi SOLO con JSON: {"handles": ["handle1", "handle2", ...]} '
    "(handle Instagram senza @, niente altro testo)."
)


def discover_competitor_handles(llm: LLM, founder: FounderModel,
                                max_handles: int = 5) -> list[str]:
    user = (founder.to_prompt()
            + f"\n\nElenca fino a {max_handles} handle Instagram di competitor/"
              "riferimenti italiani pertinenti. Solo JSON.")
    raw = llm.complete(system=_SYSTEM, user=user)
    try:
        t = raw.strip()
        m = re.search(r"\{.*\}", t, re.DOTALL)
        data = json.loads(m.group(0) if m else t)
    except (json.JSONDecodeError, AttributeError, ValueError):
        return []
    handles = [str(h).lstrip("@").strip() for h in data.get("handles", [])]
    return [h for h in handles if h][:max_handles]
