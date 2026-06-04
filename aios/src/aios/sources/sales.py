from __future__ import annotations

from typing import Any

from aios.tools import Tool


def lead_tools(client: Any) -> list[Tool]:
    return [
        Tool(name="leggi_lead", action_type=None, readonly=True,
             run=lambda **_: client.select("pipeline_leads", {
                 "select": "id,name,company,sector,status,score,next_action,"
                           "next_action_date,pain_point,offer_fit,notes",
                 "order": "score.desc"})),
        Tool(name="leggi_memo_vendite", action_type=None, readonly=True,
             run=lambda **_: client.select("board_memos", {
                 "select": "subject,body,tags,created_at",
                 "order": "created_at.desc", "limit": "20"})),
    ]
