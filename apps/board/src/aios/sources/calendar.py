from __future__ import annotations

from typing import Any

from aios.autonomy import ActionType
from aios.tools import Tool

CALENDAR_ACTION = ActionType("marketing", "calendario.voce")


def calendar_tools(client: Any) -> list[Tool]:
    def _schedule(canale: str, titolo: str, bozza: str = "",
                  data_programmata: str | None = None,
                  fonte_tipo: str | None = None, fonte_id: int | None = None,
                  note: str | None = None, **_) -> Any:
        row = {"canale": canale, "titolo": titolo, "bozza": bozza, "stato": "approvato"}
        if data_programmata:
            row["data_programmata"] = data_programmata
        if fonte_tipo:
            row["fonte_tipo"] = fonte_tipo
        if fonte_id is not None:
            row["fonte_id"] = fonte_id
        if note:
            row["note"] = note
        return client.insert("aios_content_calendar", row)

    return [
        Tool(name="leggi_calendario", action_type=None, readonly=True,
             run=lambda **_: client.select(
                 "aios_content_calendar",
                 {"select": "*", "order": "data_programmata.asc"})),
        Tool(name="programma_contenuto", action_type=CALENDAR_ACTION, run=_schedule),
    ]
