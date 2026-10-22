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

import contextvars
import logging
import os
import re
from urllib.parse import urlsplit, urlunsplit
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
    "promesse di ricerche che non fai.\n"
    "- OBBLIGO SU NUMERI DI ARTICOLO: prima di scrivere il numero di un articolo di legge, "
    "di un CCNL o di un decreto (es. 'art. 2096 c.c.', 'art. 34 del CCNL commercio'), "
    "USA `web_search` per verificarlo — MAI scriverlo a memoria. Se non verifichi (o la "
    "ricerca non conferma con certezza), NON scrivere il numero: parla in modo descrittivo "
    "('il codice civile disciplina il periodo di prova', 'il tuo CCNL specifica la durata "
    "del preavviso') senza inventare la numerazione esatta. Un numero di articolo sbagliato "
    "è un danno per l'utente maggiore che non citarlo affatto.\n"
    "- FONTI: per norme, circolari e prassi vale solo una fonte UFFICIALE (Normattiva, Gazzetta Ufficiale, EUR-Lex, "
    "Agenzia delle Entrate, INPS, INAIL, Ministero del Lavoro, Banca d'Italia/ABF, Garante privacy). Siti di aziende, "
    "noleggi, blog e portali commerciali non sono fonti di legge: se la ricerca restituisce solo quelle, dillo "
    "all'utente invece di citarle come base normativa."
)

_MAX_QUERY_CHARS = 600

# FONTI UFFICIALI (22/10/2026, test 10: la ricerca citava un sito di noleggio al posto della normativa). La prima ricerca è
# ristretta a questi domini; se non restituisce nulla si ripiega senza filtro e le fonti restano marcate «non ufficiale».
DOMINI_UFFICIALI = (
    "normattiva.it", "gazzettaufficiale.it", "eur-lex.europa.eu", "europa.eu", "agenziaentrate.gov.it", "finanze.gov.it",
    "mef.gov.it", "inps.it", "inail.it", "lavoro.gov.it", "ispettorato.gov.it", "garanteprivacy.it", "bancaditalia.it",
    "arbitrobancariofinanziario.it", "consob.it", "cortecostituzionale.it", "cortedicassazione.it", "giustizia.it",
    "senato.it", "camera.it", "agid.gov.it", "mimit.gov.it", "governo.it", "gov.it", "esma.europa.eu", "eba.europa.eu",
)
_FILTRO_MAX = 20            # limite del filtro `allowed_domains` dell'API: i primi 20 (i più autorevoli)


def e_ufficiale(url: str) -> bool:
    """True se l'host è (o è un sottodominio di) un dominio istituzionale. `normattiva.it.evil.example` NON lo è."""
    try:
        host = (urlsplit(url).hostname or "").lower()
    except ValueError:
        return False
    return any(host == d or host.endswith("." + d) for d in DOMINI_UFFICIALI)


def _pulisci_url(url: str) -> str:
    """Senza parametri di tracciamento (utm_*, ...): l'utente vede l'indirizzo vero della fonte."""
    try:
        p = urlsplit(url)
        q = "&".join(x for x in p.query.split("&") if x and not re.match(r"(?i)(utm_|fbclid|gclid)", x))
        return urlunsplit((p.scheme, p.netloc, p.path, q, p.fragment))
    except ValueError:
        return url


def ordina_fonti(cites: list) -> list:
    """Fonti ripulite, marcate `ufficiale` e ordinate: prima le istituzionali (a parità, l'ordine originale)."""
    out = [{**c, "url": _pulisci_url(c["url"]), "ufficiale": e_ufficiale(c["url"]),
            "title": _pulisci_url(c["title"]) if str(c.get("title") or "").startswith("http") else c.get("title", "")}
           for c in cites if c.get("url")]
    return sorted(out, key=lambda c: not c["ufficiale"])


def _marca(c: dict) -> str:
    return "[ufficiale]" if c.get("ufficiale") else "[non ufficiale]"


# FONTI REALMENTE CONSULTATE nel turno: ogni ricerca registra qui le URL che ha restituito (la lista è creata dal chiamante e
# condivisa con i thread, che ne ricevono una copia del contesto ma lo stesso oggetto lista). A fine turno il codice — non il
# modello — le riporta in coda alla risposta: «cita le fonti» affidato al modello non è una garanzia.
_FONTI_TURNO: contextvars.ContextVar = contextvars.ContextVar("kbot_fonti_web", default=None)


def inizia_turno() -> None:
    _FONTI_TURNO.set([])


def _registra(cites: list) -> None:
    lista = _FONTI_TURNO.get()
    if lista is None:
        return
    for c in ordina_fonti(cites):
        if all(c["url"] != x["url"] for x in lista):
            lista.append(c)
    lista.sort(key=lambda c: not c.get("ufficiale", e_ufficiale(c["url"])))


def fonti_turno() -> list:
    return list(_FONTI_TURNO.get() or [])


def aggiungi_fonti_web(testo: str, massimo: int = 6) -> str:
    """In coda alla risposta, le fonti web che le ricerche del turno hanno davvero restituito."""
    fonti = fonti_turno()
    if not fonti or not testo or "Fonti web consultate" in testo:
        return testo
    fonti = ordina_fonti(fonti)
    righe = "\n".join(f"- {_marca(f)} {(f.get('title') or f['url'])[:90]}: {f['url']}" for f in fonti[:massimo])
    return testo.rstrip() + "\n\nFonti web consultate:\n" + righe


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

        # Timeout esplicito: il default SDK è 600s → una singola ricerca appesa
        # bloccherebbe la chat e la generazione. Cap a 30s + 1 solo retry.
        client = OpenAI(api_key=OPENAI_API_KEY, timeout=30.0, max_retries=1)

        def _cerca(domini):
            tool = {"type": "web_search"}
            if domini:
                tool["filters"] = {"allowed_domains": list(domini)[:_FILTRO_MAX]}
            return client.responses.create(model=OPENAI_SEARCH_MODEL, tools=[tool], input=query, timeout=30.0)

        resp, cites = None, []
        if _flag("KBOT_WEB_SEARCH_UFFICIALI", "1"):
            try:
                resp = _cerca(DOMINI_UFFICIALI)
                cites = _extract_citations(resp)
            except Exception as exc:                      # filtro non supportato/errore: si ripiega senza filtro
                log.warning("ricerca web ristretta ai domini ufficiali non riuscita (%s): ripiego senza filtro", exc)
                resp = None
        if resp is None or not cites:
            resp = _cerca(None)
            cites = _extract_citations(resp)
        text = (getattr(resp, "output_text", "") or "").strip()
        cites = ordina_fonti(cites)
        _registra(cites)
        if cites:
            fonti = "\n".join(f"- {_marca(c)} {c['title'] or c['url']}: {c['url']}" for c in cites)
            nota = ("" if any(c["ufficiale"] for c in cites) else
                    "\nATTENZIONE: nessuna fonte ufficiale trovata; per norme e prassi non fidarti di queste fonti come testo di legge: dillo all'utente.")
            text = f"{text}\n\nFonti:\n{fonti}{nota}" if text else f"Fonti:\n{fonti}{nota}"
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
