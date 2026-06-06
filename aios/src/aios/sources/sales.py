from __future__ import annotations

from typing import Any

from aios.tools import Tool


def lead_tools(client: Any) -> list[Tool]:
    return [
        Tool(name="leggi_lead", action_type=None, readonly=True,
             run=lambda **_: client.select("pipeline_leads", {
                 "select": "id,name,company,sector,status,score,next_action,"
                           "next_action_date,pain_point,offer_fit,notes,"
                           "email,value_eur,expected_close_date,last_contact_at",
                 "order": "score.desc"})),
        Tool(name="leggi_memo_vendite", action_type=None, readonly=True,
             run=lambda **_: client.select("board_memos", {
                 "select": "subject,body,tags,created_at",
                 "order": "created_at.desc", "limit": "20"})),
        # clienti paganti (account mgmt / customer success / upsell)
        Tool(name="leggi_clienti", action_type=None, readonly=True,
             run=lambda **_: client.select("kbot_conversions", {
                 "select": "type,amount_eur,email,created_at",
                 "order": "created_at.desc", "limit": "100"})),
        # ricavi chiusi (contract/order + forecast vs actual)
        Tool(name="leggi_ricavi_chiusi", action_type=None, readonly=True,
             run=lambda **_: client.select("board_revenue_events", {
                 "select": "amount_cents,currency,status,description,occurred_at",
                 "order": "occurred_at.desc", "limit": "100"})),
    ]
