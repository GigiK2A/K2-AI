"""mcp_quant — client del MCP server `k2a-quant` di Luca, eseguito DENTRO il backend.

Architettura decisa con Luca: i numeri deterministici vengono dal SUO MCP server
(`k2a-quant`, repo inglucarossi73/k2a-mcp-quant), non da copie vendorizzate né dal
modello. Il backend avvia il server come sottoprocesso **stdio** e lo interroga via
protocollo MCP. Stessa fonte per la pipeline (resolve) e per l'agente A2.

Install (pinnato, non copia): `pip install git+https://github.com/inglucarossi73/k2a-mcp-quant@<tag>`
→ espone l'entrypoint `k2a-quant`. Override comando con env `K2A_QUANT_CMD`.

Una connessione per-chiamata (semplice e corretto). Per più calcoli nello stesso
flusso usa `call_batch` (una sola connessione → niente startup ripetuto).
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import json
import os
import shutil
from typing import Any, Optional

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    _MCP_OK = True
except Exception:  # pragma: no cover - mcp non installato
    _MCP_OK = False


def _cmd() -> Optional[str]:
    return os.environ.get("K2A_QUANT_CMD") or shutil.which("k2a-quant")


def available() -> bool:
    """True se il client MCP e il server k2a-quant sono utilizzabili."""
    return _MCP_OK and bool(_cmd())


async def _session(run):
    cmd = _cmd()
    if not _MCP_OK or not cmd:
        raise RuntimeError("k2a-quant MCP non disponibile (manca il pacchetto mcp o l'entrypoint k2a-quant)")
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


async def acall(tool: str, args: dict) -> dict:
    """Una chiamata al tool MCP. Ritorna l'envelope deterministico (call_id, outputs, trace)."""
    async def run(s):
        return _parse(await s.call_tool(tool, args))
    return await _session(run)


async def acall_batch(calls: list[tuple[str, dict]]) -> list[dict]:
    """Più chiamate su UNA sola connessione (ammortizza lo startup del server)."""
    async def run(s):
        out = []
        for tool, args in calls:
            out.append(_parse(await s.call_tool(tool, args)))
        return out
    return await _session(run)


async def alist_tools() -> list[str]:
    async def run(s):
        return [t.name for t in (await s.list_tools()).tools]
    return await _session(run)


# ---- wrapper sincroni per il codice FastAPI sync (gestiscono il loop già attivo) ----
def _sync(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(lambda: asyncio.run(coro)).result()
    return asyncio.run(coro)


def call(tool: str, args: dict) -> dict:
    return _sync(acall(tool, args))


def call_batch(calls: list[tuple[str, dict]]) -> list[dict]:
    return _sync(acall_batch(calls))


def list_tools() -> list[str]:
    return _sync(alist_tools())
