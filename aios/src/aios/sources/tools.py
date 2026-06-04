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
    ]
