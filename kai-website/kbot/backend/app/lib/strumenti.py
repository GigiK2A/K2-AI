"""Strumenti che il modello può chiamare nella chat: ricerca web (OpenAI) e ricerca nel database normativo (`cerca_norma`).

Un solo punto per definirli ed eseguirli, così i percorsi sync e streaming di `api/message.py` restano uguali. I test che sostituiscono
`web_search.enabled/web_search_tool/execute_tool_uses` continuano a valere: qui si chiamano per attributo del modulo.
"""
from __future__ import annotations

from typing import Any

from . import fascicoli, ricerca_norme, web_search


def definizioni() -> list[dict]:
    out: list[dict] = []
    if web_search.enabled():
        out.append(web_search.web_search_tool())
    if ricerca_norme.disponibile():
        out.append(ricerca_norme.definizione())
    if fascicoli.disponibile():
        out.extend(fascicoli.definizioni())
    return out


def hint() -> str:
    return (web_search.SYSTEM_HINT if web_search.enabled() else "") + (ricerca_norme.SYSTEM_HINT if ricerca_norme.disponibile() else "") \
        + (fascicoli.SYSTEM_HINT if fascicoli.disponibile() else "")


def esegui(content: Any) -> list[dict]:
    """tool_result per ogni `tool_use` della risposta (web_search o cerca_norma)."""
    risultati = list(web_search.execute_tool_uses(content))
    for block in (content or []):
        if getattr(block, "type", "") == "tool_use" and getattr(block, "name", "") == ricerca_norme.NOME_STRUMENTO:
            risultati.append({"type": "tool_result", "tool_use_id": getattr(block, "id", None),
                              "content": ricerca_norme.esegui(getattr(block, "input", None) or {})})
        elif getattr(block, "type", "") == "tool_use" and getattr(block, "name", "") in fascicoli.NOMI:
            risultati.append({"type": "tool_result", "tool_use_id": getattr(block, "id", None),
                              "content": fascicoli.esegui(getattr(block, "name", ""), getattr(block, "input", None) or {})})
    return risultati


def create_con_strumenti(client: Any, *, max_rounds: int = 4, **create_kwargs: Any) -> Any:
    """`messages.create` (non streaming) con gli strumenti abilitati; loop finché il modello li chiama (max_rounds)."""
    tools = definizioni()
    if not tools:
        return client.messages.create(**create_kwargs)
    messages = list(create_kwargs.get("messages") or [])
    kwargs = {**create_kwargs, "tools": [*(create_kwargs.get("tools") or []), *tools], "messages": messages}
    resp = client.messages.create(**kwargs)
    rounds = 0
    while getattr(resp, "stop_reason", None) == "tool_use" and rounds < max_rounds:
        risultati = esegui(resp.content)
        if not risultati:
            break
        messages = [*messages, {"role": "assistant", "content": resp.content}, {"role": "user", "content": risultati}]
        rounds += 1
        # all'ultimo giro non si offrono più gli strumenti: la risposta deve chiudersi
        kw = {**kwargs, "messages": messages}
        if rounds >= max_rounds:
            kw.pop("tools", None)
        resp = client.messages.create(**kw)
    return resp
