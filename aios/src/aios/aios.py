from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aios.kernel import Kernel
from aios.layers.context import ContextLayer
from aios.layers.data import DataLayer
from aios.layers.intelligence import IntelligenceLayer


@dataclass
class AIOS:
    """K2-OS: orchestratore (Kernel) + i 5 strati."""
    kernel: Kernel
    context: ContextLayer
    data: DataLayer
    intelligence: IntelligenceLayer
    automation: Any = None
    development: Any = None

    def situazione(self) -> dict[str, Any]:
        d = self.data.vista_unica()
        ins = self.intelligence.insights(context=self.context.assemble(), data=d)
        return {"dati": d, "insight": ins}
