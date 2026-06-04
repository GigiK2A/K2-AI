from __future__ import annotations

from typing import Any

from aios.tools import Tool
from aios.agents.marketing import PROPOSE_ACTION


def output_tool(client: Any) -> Tool:
    """proponi_marketing whose ACTION (run on approval) saves the approved
    proposal as a deliverable in aios_marketing_outputs."""
    def _run(**payload):
        row = {"tipo": payload.get("tipo"), "titolo": payload.get("titolo"),
               "contenuto": payload.get("contenuto"), "motivo": payload.get("motivo"),
               "stato": "approvato"}
        client.insert("aios_marketing_outputs", row)
        return {"saved": True, **payload}
    return Tool(name="proponi_marketing", action_type=PROPOSE_ACTION, run=_run)
