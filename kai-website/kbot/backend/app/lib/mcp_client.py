"""mcp_client — client generico per i MCP server di Luca eseguiti NEL backend (stdio).

Generalizza il pattern del quant a TUTTI i suoi MCP (repo inglucarossi73/k2a-mcp-*):
finanza/valutazione, agevolazioni, elettrico (CEI 64-8), norme tecniche, strutturale
(NTC 2018). Ognuno è installato come dipendenza pinnata e girato come sottoprocesso
stdio; i numeri escono dai SUOI tool, mai dal modello.

Architettura decisa con Luca: "la sua roba", non copie vendorizzate. Override del
comando per server con env `K2A_MCP_<NAME>_CMD` (es. K2A_MCP_QUANT_CMD).
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import json
import os
import shutil
import sys
from typing import Any, Optional

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    _MCP_OK = True
except Exception:  # pragma: no cover
    _MCP_OK = False

# Registro dei MCP server di Luca: nome logico → entrypoint installato + repo sorgente.
REGISTRY: dict[str, dict] = {
    "quant":        {"cmd": "k2a-quant",         "repo": "k2a-mcp-quant",        "domini": ["finanza", "valutazione"]},
    "agevolazioni": {"cmd": "k2a-catalogo",      "repo": "k2a-mcp-agevolazioni", "domini": ["agevolazioni", "finanza", "settoriali", "legale"]},
    "elettrico":    {"cmd": "k2a-elettrico",     "repo": "k2a-mcp-elettrico",    "domini": ["elettrico"]},
    "norme":        {"cmd": "k2a-norme-tecniche","repo": "k2a-mcp-norme-tecniche","domini": ["norme-tecniche"]},
    "strutturale":  {"cmd": "vs-strutturale",    "repo": "k2a-mcp-strutturale",  "domini": ["strutturale"]},
}


def _cmd(server: str) -> Optional[str]:
    spec = REGISTRY.get(server)
    if not spec:
        return None
    env = os.environ.get(f"K2A_MCP_{server.upper()}_CMD")
    if env:
        return env
    name = spec["cmd"]
    # entrypoint accanto al python corrente (venv bin) — robusto senza PATH (container)
    cand = os.path.join(os.path.dirname(sys.executable), name)
    if os.path.exists(cand):
        return cand
    return shutil.which(name)


def available(server: str) -> bool:
    return _MCP_OK and bool(_cmd(server))


async def _session(server: str, run):
    cmd = _cmd(server)
    if not _MCP_OK or not cmd:
        raise RuntimeError(f"MCP '{server}' non disponibile (manca mcp o l'entrypoint {REGISTRY.get(server, {}).get('cmd')})")
    params = StdioServerParameters(command=cmd, args=[])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            return await run(s)


def _parse(res: Any) -> dict:
    txt = res.content[0].text if getattr(res, "content", None) else "{}"
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"raw": txt}


async def acall(server: str, tool: str, args: dict) -> dict:
    async def run(s):
        return _parse(await s.call_tool(tool, args))
    return await _session(server, run)


async def acall_batch(server: str, calls: list[tuple[str, dict]]) -> list[dict]:
    async def run(s):
        return [_parse(await s.call_tool(t, a)) for t, a in calls]
    return await _session(server, run)


async def alist_tools(server: str) -> list[str]:
    async def run(s):
        return [t.name for t in (await s.list_tools()).tools]
    return await _session(server, run)


async def alist_tool_defs(server: str) -> list[dict]:
    async def run(s):
        return [{"name": t.name, "description": (t.description or "")[:1000],
                 "input_schema": t.inputSchema or {"type": "object", "properties": {}}}
                for t in (await s.list_tools()).tools]
    return await _session(server, run)


def _sync(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(lambda: asyncio.run(coro)).result()
    return asyncio.run(coro)


def call(server: str, tool: str, args: dict) -> dict:
    return _sync(acall(server, tool, args))


def call_batch(server: str, calls: list[tuple[str, dict]]) -> list[dict]:
    return _sync(acall_batch(server, calls))


def list_tools(server: str) -> list[str]:
    return _sync(alist_tools(server))


def tool_defs(server: str) -> list[dict]:
    return _sync(alist_tool_defs(server))


def status() -> dict:
    """Stato di TUTTI i MCP di Luca nel backend (per /api/kbot/mcp/health)."""
    out = {}
    for name, spec in REGISTRY.items():
        info: dict[str, Any] = {"repo": spec["repo"], "domini": spec["domini"], "available": available(name)}
        if info["available"]:
            try:
                info["n_tools"] = len(list_tools(name))
            except Exception as exc:  # pragma: no cover
                info["available"] = False
                info["error"] = str(exc)[:200]
        out[name] = info
    return out
