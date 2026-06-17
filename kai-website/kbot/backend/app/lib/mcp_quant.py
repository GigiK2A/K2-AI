"""mcp_quant — wrapper del MCP server `k2a-quant` di Luca (server "quant").

Delega a `mcp_client` (client generico per TUTTI i suoi MCP nel backend). API
mantenuta per i consumatori esistenti (boost_agent, compute.py): i numeri di
valutazione/finanza escono dal SUO MCP, eseguito come sottoprocesso stdio nel
backend. Override comando con env `K2A_QUANT_CMD` o `K2A_MCP_QUANT_CMD`.
"""
from __future__ import annotations

import os

from . import mcp_client

_SERVER = "quant"

# retro-compat: K2A_QUANT_CMD storico → K2A_MCP_QUANT_CMD del client generico
if os.environ.get("K2A_QUANT_CMD") and not os.environ.get("K2A_MCP_QUANT_CMD"):
    os.environ["K2A_MCP_QUANT_CMD"] = os.environ["K2A_QUANT_CMD"]


def available() -> bool:
    return mcp_client.available(_SERVER)


def call(tool: str, args: dict) -> dict:
    return mcp_client.call(_SERVER, tool, args)


def call_batch(calls: list[tuple[str, dict]]) -> list[dict]:
    return mcp_client.call_batch(_SERVER, calls)


def list_tools() -> list[str]:
    return mcp_client.list_tools(_SERVER)


def tool_defs() -> list[dict]:
    return mcp_client.tool_defs(_SERVER)


async def acall(tool: str, args: dict) -> dict:
    return await mcp_client.acall(_SERVER, tool, args)
