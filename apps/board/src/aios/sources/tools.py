from __future__ import annotations

from typing import Any

from aios.tools import Tool
from aios.sources.content import read_servizi, read_topics


def content_tools(conn: Any) -> list[Tool]:
    return [
        Tool(name="leggi_servizi", action_type=None, readonly=True,
             run=lambda **_: read_servizi(conn)),
        Tool(name="leggi_topics", action_type=None, readonly=True,
             run=lambda **_: read_topics(conn)),
    ]


def instagram_tools(client: Any) -> list[Tool]:
    return [
        Tool(name="leggi_profilo_ig", action_type=None, readonly=True,
             run=lambda **_: client.account()),
        Tool(name="leggi_post_ig", action_type=None, readonly=True,
             run=lambda limit=10, **_: client.recent_media(limit=limit)),
        # Testo effettivo dei commenti (non solo il conteggio). Senza media_id scorre i
        # post recenti con commenti; con media_id legge quel post specifico.
        Tool(name="leggi_commenti_ig", action_type=None, readonly=True,
             run=lambda media_id=None, limit=25, **_: (
                 client.comments(str(media_id), limit=limit) if media_id
                 else client.latest_comments(per_post=limit))),
    ]


def content_tools_rest(client: Any) -> list[Tool]:
    return [
        Tool(name="leggi_servizi", action_type=None, readonly=True,
             run=lambda **_: client.select("servizi", {"select": "*", "order": "id.asc"})),
        Tool(name="leggi_topics", action_type=None, readonly=True,
             run=lambda **_: client.select("topics", {"select": "*", "order": "id.asc"})),
    ]


def competitor_tools(ig_client: Any, usernames: list[str]) -> list[Tool]:
    def _run(**_):
        out = {}
        for u in usernames:
            try:
                out[u] = ig_client.business_discovery(u)
            except Exception as exc:
                out[u] = {"error": str(exc)}
        return out
    return [Tool(name="leggi_competitor_ig", action_type=None, readonly=True, run=_run)]


def insights_tools(ig_client: Any) -> list[Tool]:
    return [Tool(name="leggi_insight_ig", action_type=None, readonly=True,
                 run=lambda **_: ig_client.account_insights())]


def competitor_lookup_tool(ig_client: Any) -> Tool:
    def _run(usernames=None, **_):
        out = {}
        for u in (usernames or []):
            try:
                out[u] = ig_client.business_discovery(u)
            except Exception as exc:
                out[u] = {"error": str(exc)}
        return out
    return Tool(name="analizza_competitor", action_type=None, readonly=True, run=_run)
