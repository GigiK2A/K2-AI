from __future__ import annotations

from typing import Any

from aios.tools import Tool


def lead_tools(client: Any) -> list[Tool]:
    return [
        Tool(name="leggi_lead", action_type=None, readonly=True,
             run=lambda **_: client.select("pipeline_leads", {
                 "select": "id,name,company,sector,status,score,next_action,pain_point,notes",
                 "order": "score.desc"})),
    ]
