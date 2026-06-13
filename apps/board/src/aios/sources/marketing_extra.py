"""Sensori marketing aggiuntivi (readonly) per coprire le sotto-funzioni del
reparto oltre Social/Content/Competitor già esistenti:
- Email/Lifecycle  → newsletter_subscribers + newsletter_issues
- Analytics        → analytics_snapshots (IG + funnel K-BOT)
- Market Research   → kbot_sessions (settore + dati raccolti = voce clienti reale)
Tutto readonly: l'agente PROPONE soltanto.
"""
from __future__ import annotations

from typing import Any

from aios.tools import Tool


def _ro(name: str, table: str, params: dict[str, str], client: Any) -> Tool:
    return Tool(name=name, action_type=None, readonly=True,
                run=lambda **_: client.select(table, params))


def marketing_extra_tools(client: Any) -> list[Tool]:
    return [
        _ro("leggi_iscritti", "newsletter_subscribers",
            {"select": "email,confirmed,is_active,newsletter_ai,source,unsubscribed_at",
             "limit": "500"}, client),
        _ro("leggi_newsletter", "newsletter_issues",
            {"select": "slug,subject,preview_text,published_at",
             "order": "published_at.desc", "limit": "20"}, client),
        _ro("leggi_analytics", "analytics_snapshots",
            {"select": "ts,profile_stats,kbot_funnel,events_processed",
             "order": "ts.desc", "limit": "8"}, client),
        _ro("leggi_voce_clienti", "kbot_sessions",
            {"select": "sector,collected_data,status",
             "order": "created_at.desc", "limit": "25"}, client),
        _ro("leggi_calendario_contenuti", "aios_content_calendar",
            {"select": "canale,titolo,stato,data_programmata,fonte_tipo",
             "order": "created_at.desc", "limit": "50"}, client),
    ]
