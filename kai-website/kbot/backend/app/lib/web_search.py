"""Ricerca web REALE — OpenAI fa la ricerca, Claude resta il cervello.

Decisione owner (giu 2026): override cosciente della regola "no OpenAI" in CLAUDE.md
SOLO per il motore di ricerca. Architettura:

- `web_search` è un **client-tool** dichiarato sulla chiamata Claude. Quando Claude decide
  di cercare, emette un `tool_use`; il nostro handler chiama l'**API OpenAI** (Responses +
  tool `web_search`) e ripassa testo + fonti a Claude come `tool_result`. Claude continua.
- Tutto il resto (chat, ragionamento, structuring) resta su Claude/Anthropic. OpenAI è
  usato ESCLUSIVAMENTE per la ricerca web.

Degrada in sicurezza: con `KBOT_WEB_SEARCH=0`, o senza NESSUN motore disponibile, il tool
non viene nemmeno dichiarato → chat/generazione funzionano come prima, senza ricerca.

Fallback gratuito (set 2026): se OpenAI non è utilizzabile (chiave assente o crediti
esauriti → 429 insufficient_quota) la ricerca passa alla lib `ddgs` (DuckDuckGo & co.,
nessuna chiave, nessun costo). OpenAI resta il motore primario quando c'è credito perché
riassume e cita; DDG restituisce risultati grezzi che il modello digerisce da solo.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

from ..settings import OPENAI_API_KEY, OPENAI_SEARCH_MODEL

log = logging.getLogger(__name__)


def _flag(name: str, default: str = "1") -> bool:
    return (os.environ.get(name, default) or default).strip().lower() not in ("0", "false", "no", "off")


def _ddgs_available() -> bool:
    try:
        import importlib.util
        return importlib.util.find_spec("ddgs") is not None
    except Exception:
        return False


def enabled() -> bool:
    """ON quando la ricerca è usabile: flag attivo E almeno un motore disponibile
    (OpenAI con chiave, oppure il fallback gratuito `ddgs`). `KBOT_WEB_SEARCH=0` la spegne."""
    return _flag("KBOT_WEB_SEARCH", "1") and (bool(OPENAI_API_KEY) or _ddgs_available())


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
    "promesse di ricerche che non fai.\n"
    "- NON FIDARTI DELLA MEMORIA su entità recenti: se la domanda riguarda un prodotto, un "
    "annuncio, un'azienda, un prezzo o un evento che potrebbe essere successivo al tuo "
    "training (o che non conosci con certezza), USA `web_search` PRIMA di rispondere — "
    "rispondere a memoria su queste cose produce invenzioni plausibili ma false. Se la "
    "ricerca fallisce o non è disponibile, dichiara che non puoi verificare e NON inventare "
    "i dettagli.\n"
    "- OBBLIGO SU NUMERI DI ARTICOLO: prima di scrivere il numero di un articolo di legge, "
    "di un CCNL o di un decreto (es. 'art. 2096 c.c.', 'art. 34 del CCNL commercio'), "
    "USA `web_search` per verificarlo — MAI scriverlo a memoria. Se non verifichi (o la "
    "ricerca non conferma con certezza), NON scrivere il numero: parla in modo descrittivo "
    "('il codice civile disciplina il periodo di prova', 'il tuo CCNL specifica la durata "
    "del preavviso') senza inventare la numerazione esatta. Un numero di articolo sbagliato "
    "è un danno per l'utente maggiore che non citarlo affatto."
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


def _openai_search(query: str) -> Optional[str]:
    """UNA ricerca via OpenAI (Responses API + tool `web_search`): testo riassunto +
    elenco fonti. None se non utilizzabile (chiave assente, crediti esauriti, rete):
    il chiamante passa al fallback."""
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI

        # Timeout esplicito: il default SDK è 600s → una singola ricerca appesa
        # bloccherebbe la chat e la generazione. Cap a 30s + 1 solo retry.
        client = OpenAI(api_key=OPENAI_API_KEY, timeout=30.0, max_retries=1)
        resp = client.responses.create(
            model=OPENAI_SEARCH_MODEL,
            tools=[{"type": "web_search"}],
            input=query,
            timeout=30.0,
        )
        text = (getattr(resp, "output_text", "") or "").strip()
        cites = _extract_citations(resp)
        if cites:
            fonti = "\n".join(f"- {c['title'] or c['url']}: {c['url']}" for c in cites)
            text = f"{text}\n\nFonti:\n{fonti}" if text else f"Fonti:\n{fonti}"
        return text or None
    except Exception as exc:  # rete/credito/modello → fallback DDG
        log.warning("OpenAI web search fallita (passo al fallback DDG): %s", exc)
        return None


def _ddg_search(query: str) -> Optional[str]:
    """Fallback gratuito senza chiave (lib `ddgs`): risultati grezzi titolo+snippet+URL,
    è il modello a digerirli e citarli. None se lib assente, blocco rete o zero risultati."""
    try:
        from ddgs import DDGS

        rows = DDGS().text(query, max_results=6, region="it-it") or []
    except Exception as exc:
        log.warning("DDG web search fallita: %s", exc)
        return None
    rows = [r for r in rows if r.get("href")]
    if not rows:
        return None
    parts = [
        f"{i}. {(r.get('title') or '').strip()}\n"
        f"   {(r.get('body') or '').strip()}\n"
        f"   URL: {r['href']}"
        for i, r in enumerate(rows, 1)
    ]
    return (
        "Risultati di ricerca web (grezzi: valuta la pertinenza e cita gli URL come fonti):\n\n"
        + "\n\n".join(parts)
    )


def run_search(query: str) -> str:
    """Esegue UNA ricerca web e ritorna sempre una stringa (mai solleva), così l'handler
    del tool può sempre rispondere a Claude. Motori in cascata: OpenAI (riassume e cita,
    quando c'è credito) → ddgs (gratuito, senza chiave)."""
    query = (query or "").strip()[:_MAX_QUERY_CHARS]
    if not query:
        return "[ricerca web: query mancante]"
    return (
        _openai_search(query)
        or _ddg_search(query)
        or "[ricerca web non riuscita: nessun motore disponibile o nessun risultato]"
    )


# Alias storico: fact_grounding, boost_agent e i test chiamano/patchano questo nome.
# Oggi la ricerca è a cascata OpenAI→DDG, non solo OpenAI: stesso contratto (mai solleva).
run_openai_search = run_search


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
            # Via il nome-alias (lookup a runtime): i test lo monkeypatchano.
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
