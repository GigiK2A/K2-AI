"""Ricerca web REALE — OpenAI fa la ricerca, Claude resta il cervello.

Decisione owner (giu 2026): override cosciente della regola "no OpenAI" in CLAUDE.md
SOLO per il motore di ricerca. Architettura:

- `web_search` è un **client-tool** dichiarato sulla chiamata Claude. Quando Claude decide
  di cercare, emette un `tool_use`; il nostro handler chiama l'**API OpenAI** (Responses +
  tool `web_search`) e ripassa testo + fonti a Claude come `tool_result`. Claude continua.
- Tutto il resto (chat, ragionamento, structuring) resta su Claude/Anthropic. OpenAI è
  usato ESCLUSIVAMENTE per la ricerca web.

Degrada in sicurezza: senza `OPENAI_API_KEY` (o con `KBOT_WEB_SEARCH=0`) il tool non viene
nemmeno dichiarato → chat/generazione funzionano come prima, senza ricerca.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

from ..settings import OPENAI_API_KEY, OPENAI_SEARCH_MODEL

log = logging.getLogger(__name__)


def _flag(name: str, default: str = "1") -> bool:
    return (os.environ.get(name, default) or default).strip().lower() not in ("0", "false", "no", "off")


def enabled() -> bool:
    """ON quando la ricerca è usabile: flag attivo E chiave OpenAI presente.
    `KBOT_WEB_SEARCH=0` la spegne."""
    return bool(OPENAI_API_KEY) and _flag("KBOT_WEB_SEARCH", "1")


# Client-tool esposto a Claude (NON un server-tool: l'esecuzione è nostra → OpenAI).
def web_search_tool() -> dict:
    return {
        "name": "web_search",
        "description": (
            "Cerca informazioni aggiornate sul web (competitor, dati di mercato, prezzi, "
            "normative, notizie, fatti su aziende/settori). Restituisce un riassunto con le "
            "fonti (URL). Usalo ogni volta che ti servono dati che non possiedi."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "La query di ricerca, specifica e mirata."},
            },
            "required": ["query"],
        },
    }


SYSTEM_HINT = (
    "\n\nRICERCA WEB — hai accesso a una ricerca web REALE tramite il tool `web_search`.\n"
    "- Quando l'utente ti chiede di cercare, trovare o verificare informazioni che non "
    "possiedi (competitor, dati di mercato, prezzi, normative, notizie recenti, fatti su "
    "un'azienda o un settore), USA davvero `web_search` e cita le fonti nel testo.\n"
    "- NON dire MAI 'cercherò' / 'sto cercando' / 'lo farò' senza eseguire la ricerca: o "
    "cerchi subito con il tool, oppure dici onestamente che quel dato non ce l'hai. Niente "
    "promesse di ricerche che non fai."
)

_MAX_QUERY_CHARS = 600


def _extract_citations(resp: Any) -> list[dict]:
    """URL citate dalla risposta OpenAI Responses: output[].content[].annotations[]
    con type=='url_citation'. Robusto a oggetti SDK o dict."""
    out: list[dict] = []
    seen: set[str] = set()

    def _g(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    for item in (_g(resp, "output", []) or []):
        for block in (_g(item, "content", []) or []):
            for ann in (_g(block, "annotations", []) or []):
                if _g(ann, "type") != "url_citation":
                    continue
                url = str(_g(ann, "url", "") or "").strip()
                if url and url not in seen:
                    seen.add(url)
                    out.append({"url": url, "title": str(_g(ann, "title", "") or "").strip()})
    return out


def run_openai_search(query: str) -> str:
    """Esegue UNA ricerca web via OpenAI (Responses API + tool `web_search`) e ritorna
    testo + elenco fonti. Best-effort: ritorna una nota d'errore (mai solleva) così
    l'handler del tool può sempre rispondere a Claude."""
    query = (query or "").strip()[:_MAX_QUERY_CHARS]
    if not query:
        return "[ricerca web: query mancante]"
    if not OPENAI_API_KEY:
        return "[ricerca web non configurata: manca OPENAI_API_KEY]"
    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.responses.create(
            model=OPENAI_SEARCH_MODEL,
            tools=[{"type": "web_search"}],
            input=query,
        )
        text = (getattr(resp, "output_text", "") or "").strip()
        cites = _extract_citations(resp)
        if cites:
            fonti = "\n".join(f"- {c['title'] or c['url']}: {c['url']}" for c in cites)
            text = f"{text}\n\nFonti:\n{fonti}" if text else f"Fonti:\n{fonti}"
        return text or "[ricerca web: nessun risultato]"
    except Exception as exc:  # rete/credito/modello: Claude prosegue con la nota
        log.warning("OpenAI web search fallita: %s", exc)
        return f"[ricerca web non riuscita: {str(exc)[:160]}]"


def execute_tool_uses(content: Any) -> list[dict]:
    """Per ogni blocco `tool_use` di nome `web_search` nella risposta Claude, esegue la
    ricerca OpenAI e costruisce il `tool_result` corrispondente."""
    results: list[dict] = []
    for block in (content or []):
        if getattr(block, "type", "") != "tool_use" or getattr(block, "name", "") != "web_search":
            continue
        inp = getattr(block, "input", None) or {}
        query = str((inp.get("query") if isinstance(inp, dict) else "") or "").strip()
        results.append({
            "type": "tool_result",
            "tool_use_id": getattr(block, "id", None),
            "content": run_openai_search(query),
        })
    return results


def create_with_web_search(client: Any, *, max_rounds: int = 4, **create_kwargs: Any) -> Any:
    """`messages.create` (NON streaming) con il client-tool `web_search` agganciato a OpenAI.

    Loop agentico: Claude può chiamare `web_search` più volte; ogni chiamata la eseguiamo
    via OpenAI e ripassiamo i risultati, finché Claude smette (o si raggiunge `max_rounds`).
    Ritorna il Message finale. Se la ricerca è spenta, è un semplice `messages.create`."""
    if not enabled():
        return client.messages.create(**create_kwargs)

    tools = [*(create_kwargs.get("tools") or []), web_search_tool()]
    messages = list(create_kwargs.get("messages") or [])
    kwargs = {**create_kwargs, "tools": tools, "messages": messages}

    resp = client.messages.create(**kwargs)
    rounds = 0
    while getattr(resp, "stop_reason", None) == "tool_use" and rounds < max_rounds:
        tool_results = execute_tool_uses(resp.content)
        if not tool_results:
            break
        messages = [
            *messages,
            {"role": "assistant", "content": resp.content},
            {"role": "user", "content": tool_results},
        ]
        resp = client.messages.create(**{**kwargs, "messages": messages})
        rounds += 1
    return resp
