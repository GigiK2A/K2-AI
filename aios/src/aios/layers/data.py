from __future__ import annotations

from typing import Any

from aios.kernel import Kernel

_SENSORS = {
    "servizi": ("leggi_servizi", {}),
    "topics": ("leggi_topics", {}),
    "profilo_ig": ("leggi_profilo_ig", {}),
    "post_ig": ("leggi_post_ig", {"limit": 10}),
    "insight_ig": ("leggi_insight_ig", {}),
    "calendario": ("leggi_calendario", {}),
}


class DataLayer:
    """Strato (2) Dati: vista unica sui sensori registrati nel kernel."""

    def __init__(self, kernel: Kernel) -> None:
        self.k = kernel

    def vista_unica(self) -> dict[str, Any]:
        names = set(self.k.tools.names())
        out: dict[str, Any] = {}
        for key, (tool, args) in _SENSORS.items():
            if tool in names:
                try:
                    out[key] = self.k.execute(tool, actor="data_layer", args=args).result
                except Exception as exc:
                    out[key] = {"error": str(exc)}
        return out
