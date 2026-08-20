from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Protocol

from aios import billing


def _meter_anthropic(model: str, msg: Any) -> None:
    """Registra i token/costo di una risposta Anthropic sull'attore corrente.
    Best-effort: non deve mai rompere una completion."""
    try:
        usage = getattr(msg, "usage", None)
        if usage is not None:
            billing.record_usage(
                model,
                int(getattr(usage, "input_tokens", 0) or 0),
                int(getattr(usage, "output_tokens", 0) or 0))
    except Exception:
        pass


def _robust_json(text: str) -> dict:
    """Best-effort parse of a JSON object out of model text (raw/fenced/prose)."""
    t = text.strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            t = m.group(1).strip()
    a, b = t.find("{"), t.rfind("}")
    if a >= 0 and b > a:
        return json.loads(t[a:b + 1])
    raise ValueError("nessun oggetto JSON nella risposta")


class LLM(Protocol):
    def complete(self, *, system: str, user: str) -> str: ...
    def complete_json(self, *, system: str, user: str, schema: dict | None = None) -> dict: ...


class FakeLLM:
    """Deterministic LLM for tests. Returns scripted responses; reuses the last
    one when exhausted. Records (system, user) calls."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._i = 0
        self.calls: list[tuple[str, str]] = []

    def complete(self, *, system: str, user: str) -> str:
        self.calls.append((system, user))
        if self._i < len(self._responses):
            out = self._responses[self._i]
            self._i += 1
            return out
        return self._responses[-1]

    def complete_json(self, *, system: str, user: str, schema: dict | None = None) -> dict:
        # consumes a scripted response (records the call) then parses it robustly
        return _robust_json(self.complete(system=system, user=user))


def _anthropic_client(api_key: str):
    import anthropic
    return anthropic.Anthropic(api_key=api_key)


class AnthropicLLM:
    """Real LLM via the Anthropic SDK. Model defaults to Haiku for cost.
    Optional web_search tool for trend-aware responses."""

    def __init__(self, api_key: str | None = None,
                 model: str = "claude-haiku-4-5-20251001",
                 max_tokens: int = 2000, enable_web_search: bool = False) -> None:
        self._client = _anthropic_client(api_key or os.environ["ANTHROPIC_API_KEY"])
        self._model = model
        self._max_tokens = max_tokens
        self._web = enable_web_search

    def complete(self, *, system: str, user: str) -> str:
        kwargs = dict(model=self._model, max_tokens=self._max_tokens, system=system,
                      messages=[{"role": "user", "content": user}])
        if self._web:
            kwargs["tools"] = [{"type": "web_search_20250305",
                                "name": "web_search", "max_uses": 5}]
        msg = self._client.messages.create(**kwargs)
        _meter_anthropic(self._model, msg)
        return "".join(b.text for b in msg.content
                       if getattr(b, "type", None) == "text")

    def complete_json(self, *, system: str, user: str, schema: dict | None = None) -> dict:
        """Guaranteed-valid JSON via a forced tool call (structured output).
        Pass `schema` (a JSON Schema object) to guide what fields the model fills."""
        tool = {"name": "rispondi", "description": "Restituisci la risposta strutturata",
                "input_schema": schema or {"type": "object", "additionalProperties": True}}
        msg = self._client.messages.create(
            model=self._model, max_tokens=self._max_tokens, system=system,
            messages=[{"role": "user", "content": user}],
            tools=[tool], tool_choice={"type": "tool", "name": "rispondi"})
        _meter_anthropic(self._model, msg)
        for b in msg.content:
            if getattr(b, "type", None) == "tool_use":
                return dict(b.input)
        # fallback: parse any text
        text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
        return _robust_json(text)

    def stream_agentic(self, *, system: str, user: str, tools: list[dict],
                       tool_exec, max_iters: int = 6, max_tokens: int | None = None,
                       web_search: bool = False, history: list[dict] | None = None,
                       media: list[dict] | None = None):
        """Loop tool-use REALE con streaming. Generatore di eventi (dict) mappati sui
        veri segnali dello streaming Anthropic, così la UI mostra stati veri:
          {phase:'thinking'}            — turno aperto, il modello sta ragionando
          {phase:'tool', tool}          — il modello ha deciso di usare un tool
          {phase:'writing'}             — inizia a produrre testo
          {phase:'delta', text}         — token di testo (stream live)
          {phase:'tool_run', tool}      — eseguo il tool sui dati reali
          {phase:'done', text}          — fine (nessun altro tool richiesto)
        `tools`: tool def in formato Anthropic. `tool_exec(name, input)->risultato`
        esegue il tool (sensore o azione) e ritorna un valore JSON-serializzabile."""
        mt = max_tokens or self._max_tokens
        all_tools = list(tools)
        if web_search:   # web search NATIVA di Claude (server-tool Anthropic, non OpenAI)
            all_tools.append({"type": "web_search_20250305",
                              "name": "web_search", "max_uses": 4})
        # contenuto utente: testo + eventuali allegati (immagini/PDF come blocchi nativi)
        content: Any = user
        if media:
            content = [{"type": "text", "text": user}] + list(media)
        # history = turni precedenti [{role, content}] → memoria conversazionale
        messages: list[dict] = list(history or []) + [{"role": "user", "content": content}]
        for _ in range(max_iters):
            yield {"phase": "thinking"}
            text_started = False
            with self._client.messages.stream(
                    model=self._model, max_tokens=mt, system=system,
                    messages=messages, tools=all_tools) as stream:
                for ev in stream:
                    et = getattr(ev, "type", "")
                    if et == "content_block_start":
                        cb = getattr(ev, "content_block", None)
                        ct = getattr(cb, "type", "")
                        if ct == "tool_use":
                            yield {"phase": "tool", "tool": getattr(cb, "name", "")}
                        elif ct == "server_tool_use":   # es. web_search: lo esegue Anthropic
                            yield {"phase": "tool", "tool": getattr(cb, "name", "web_search")}
                    elif et == "content_block_delta":
                        d = getattr(ev, "delta", None)
                        if getattr(d, "type", "") == "text_delta":
                            if not text_started:
                                yield {"phase": "writing"}
                                text_started = True
                            yield {"phase": "delta", "text": getattr(d, "text", "")}
                final = stream.get_final_message()
            _meter_anthropic(self._model, final)
            # solo i tool CUSTOM richiedono un risultato da noi; i server-tool (web_search)
            # li ha già eseguiti Anthropic dentro il turno.
            tool_uses = [b for b in final.content if getattr(b, "type", "") == "tool_use"]
            text = "".join(getattr(b, "text", "") for b in final.content
                           if getattr(b, "type", "") == "text")
            if not tool_uses:
                yield {"phase": "done", "text": text}
                return
            # Passo i blocchi originali del turno assistant (testo + tool_use + eventuali
            # server_tool_use/result) così com'è: l'SDK li ri-serializza correttamente.
            messages.append({"role": "assistant", "content": final.content})
            results = []
            for tu in tool_uses:
                yield {"phase": "tool_run", "tool": tu.name}
                try:
                    out = tool_exec(tu.name, dict(tu.input))
                except Exception as exc:
                    out = {"error": str(exc)}
                results.append({"type": "tool_result", "tool_use_id": tu.id,
                                "content": json.dumps(out, ensure_ascii=False,
                                                      default=str)[:6000]})
            messages.append({"role": "user", "content": results})
        yield {"phase": "done", "text": "(troppi passaggi, mi fermo qui)"}


# --- Backend OpenAI ----------------------------------------------------------
# Eccezione al "no OpenAI" ampliata dall'owner (19 ago 2026): oltre alla web search del
# K-BOT e alla generazione immagini, OpenAI è un TIER del board. Motivo pratico: nella
# stessa giornata il modello locale non rispondeva (GB10 via tailnet) e la chiave
# Anthropic era invalida — con un solo fornitore alternativo l'azienda si ferma.
# Nessuna dipendenza nuova: Chat Completions via urllib, come già fa image_gen.py.
_OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
_OPENAI_MODEL = os.environ.get("AIOS_OPENAI_MODEL") or os.environ.get(
    "DEFAULT_OPENAI_MODEL", "gpt-4o")
_OPENAI_MINI = os.environ.get("AIOS_OPENAI_MINI_MODEL") or os.environ.get(
    "DEFAULT_OPENAI_MINI_MODEL", "gpt-4o-mini")
_OPENAI_TIMEOUT = int(os.environ.get("AIOS_OPENAI_TIMEOUT", "120"))


class OpenAIError(RuntimeError):
    """Errore HTTP di OpenAI, con lo `status` esposto perché la riserva lo riconosca."""

    def __init__(self, messaggio: str, status: int | None = None) -> None:
        super().__init__(messaggio)
        self.status_code = status


class OpenAILLM:
    """LLM via Chat Completions di OpenAI: `complete`, `complete_json`,
    `stream_agentic`. Stessa interfaccia degli altri, così è interscambiabile."""

    def __init__(self, model: str | None = None, max_tokens: int = 2000,
                 api_key: str | None = None, mini: bool = False,
                 web_search: bool = False) -> None:
        self._model = model or (_OPENAI_MINI if mini else _OPENAI_MODEL)
        self._max_tokens = int(max_tokens)
        self._key = api_key or os.environ.get("OPENAI_API_KEY", "")
        # Con la ricerca web `complete()` passa dalla Responses API: serve al
        # prospecting, che senza dati veri dal web si INVENTEREBBE le aziende.
        self._web = bool(web_search)

    def _cerca_sul_web(self, system: str, user: str) -> str:
        """`complete()` con ricerca web via Responses API (l'unica che espone il tool
        `web_search`). Ritorna il testo aggregato della risposta."""
        if not self._key:
            raise OpenAIError("OPENAI_API_KEY non configurato", status=401)
        corpo = {"model": self._model, "tools": [{"type": "web_search"}],
                 "max_output_tokens": max(512, self._max_tokens),
                 "input": [{"role": "system", "content": system},
                           {"role": "user", "content": user}]}
        data = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request("https://api.openai.com/v1/responses", data=data,
                                     method="POST", headers={
                                         "Authorization": f"Bearer {self._key}",
                                         "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=max(180, _OPENAI_TIMEOUT)) as r:  # noqa: S310
                d = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                msg = json.loads(exc.read().decode()).get("error", {}).get("message", "")
            except Exception:
                msg = ""
            raise OpenAIError(f"OpenAI HTTP {exc.code}: {msg[:160]}", status=exc.code) from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            raise OpenAIError(f"OpenAI non raggiungibile: {exc}", status=503) from exc
        self._metering({"usage": {
            "prompt_tokens": (d.get("usage") or {}).get("input_tokens", 0),
            "completion_tokens": (d.get("usage") or {}).get("output_tokens", 0)}})
        if d.get("output_text"):
            return str(d["output_text"])
        pezzi = []
        for blocco in d.get("output") or []:
            for c in (blocco or {}).get("content") or []:
                if c.get("type") in ("output_text", "text") and c.get("text"):
                    pezzi.append(c["text"])
        return "\n".join(pezzi)

    # -- trasporto -------------------------------------------------------
    def _post(self, body: dict, *, stream: bool = False, timeout: int | None = None):
        if not self._key:
            raise OpenAIError("OPENAI_API_KEY non configurato", status=401)
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(_OPENAI_ENDPOINT, data=data, method="POST", headers={
            "Authorization": f"Bearer {self._key}", "Content-Type": "application/json"})
        try:
            return urllib.request.urlopen(req, timeout=timeout or _OPENAI_TIMEOUT)  # noqa: S310
        except urllib.error.HTTPError as exc:
            try:
                msg = json.loads(exc.read().decode()).get("error", {}).get("message", "")
            except Exception:
                msg = ""
            raise OpenAIError(f"OpenAI HTTP {exc.code}: {msg[:160]}", status=exc.code) from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            raise OpenAIError(f"OpenAI non raggiungibile: {exc}", status=503) from exc

    def _messaggi(self, system: str, user: str, media: list[dict] | None = None) -> list[dict]:
        contenuto: Any = user
        immagini = []
        for m in media or []:
            src = (m or {}).get("source") or {}
            if (src.get("type") == "base64"
                    and str(src.get("media_type") or "").startswith("image/")):
                immagini.append({"type": "image_url", "image_url": {
                    "url": f"data:{src['media_type']};base64,{src.get('data','')}"}})
        if immagini:
            contenuto = [{"type": "text", "text": user}] + immagini
        return [{"role": "system", "content": system},
                {"role": "user", "content": contenuto}]

    # -- completions -----------------------------------------------------
    def complete(self, *, system: str, user: str) -> str:
        if self._web:
            return self._cerca_sul_web(system, user)
        with self._post({"model": self._model, "max_tokens": self._max_tokens,
                         "messages": self._messaggi(system, user)}) as r:
            d = json.loads(r.read().decode("utf-8"))
        self._metering(d)
        return (d.get("choices") or [{}])[0].get("message", {}).get("content") or ""

    def complete_json(self, *, system: str, user: str, schema: dict | None = None) -> dict:
        """JSON garantito con `response_format: json_object` — più compatibile dello
        json_schema strict, che pretende additionalProperties=false su ogni livello
        (gli schemi del board non lo rispettano)."""
        istruzione = system + "\n\nRispondi SOLO con un oggetto JSON valido."
        if schema:
            istruzione += ("\nSegui questa struttura (JSON Schema):\n"
                           + json.dumps(schema, ensure_ascii=False)[:2000])
        with self._post({"model": self._model, "max_tokens": self._max_tokens,
                         "response_format": {"type": "json_object"},
                         "messages": self._messaggi(istruzione, user)}) as r:
            d = json.loads(r.read().decode("utf-8"))
        self._metering(d)
        testo = (d.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        return _robust_json(testo)

    def _metering(self, d: dict) -> None:
        try:
            u = d.get("usage") or {}
            billing.record_usage(self._model, int(u.get("prompt_tokens", 0) or 0),
                                 int(u.get("completion_tokens", 0) or 0))
        except Exception:
            pass

    # -- streaming tool-use ---------------------------------------------
    @staticmethod
    def _tool_openai(tools: list[dict] | None) -> list[dict]:
        fuori = []
        for t in tools or []:
            nome = (t or {}).get("name")
            if not nome or t.get("type"):     # server-tool Anthropic: non esistono qui
                continue
            fuori.append({"type": "function", "function": {
                "name": nome, "description": str(t.get("description") or "")[:1024],
                "parameters": t.get("input_schema") or {"type": "object", "properties": {}}}})
        return fuori

    def stream_agentic(self, *, system: str, user: str, tools: list[dict],
                       tool_exec, max_iters: int = 4, max_tokens: int | None = None,
                       web_search: bool = False, history: list[dict] | None = None,
                       media: list[dict] | None = None):
        """Loop tool-use in streaming, stessi eventi degli altri backend."""
        messaggi = [{"role": "system", "content": system}]
        messaggi += [m for m in (history or []) if isinstance(m, dict)]
        messaggi += self._messaggi("", user, media)[1:]      # solo il turno utente
        strumenti = self._tool_openai(tools)

        for _ in range(max_iters):
            yield {"phase": "thinking"}
            corpo: dict[str, Any] = {
                "model": self._model, "stream": True,
                "max_tokens": int(max_tokens or self._max_tokens),
                "messages": messaggi}
            if strumenti:
                corpo["tools"] = strumenti
            testo, iniziato = "", False
            # le tool call arrivano a pezzi: si accumulano per indice
            parziali: dict[int, dict] = {}
            with self._post(corpo, stream=True) as r:
                for riga in r:
                    riga = riga.strip()
                    if not riga.startswith(b"data: "):
                        continue
                    grezzo = riga[6:]
                    if grezzo == b"[DONE]":
                        break
                    try:
                        chunk = json.loads(grezzo)
                    except Exception:
                        continue
                    delta = ((chunk.get("choices") or [{}])[0]).get("delta") or {}
                    for tc in delta.get("tool_calls") or []:
                        i = int(tc.get("index") or 0)
                        acc = parziali.setdefault(i, {"name": "", "args": ""})
                        fn = tc.get("function") or {}
                        if fn.get("name"):
                            acc["name"] = fn["name"]
                            yield {"phase": "tool", "tool": fn["name"]}
                        if fn.get("arguments"):
                            acc["args"] += fn["arguments"]
                    pezzo = delta.get("content") or ""
                    if pezzo:
                        if not iniziato:
                            yield {"phase": "writing"}
                            iniziato = True
                        testo += pezzo
                        yield {"phase": "delta", "text": pezzo}
            if not parziali:
                yield {"phase": "done", "text": testo}
                return
            chiamate = []
            for i in sorted(parziali):
                acc = parziali[i]
                try:
                    args = json.loads(acc["args"]) if acc["args"].strip() else {}
                except Exception:
                    args = {}
                chiamate.append({"name": acc["name"], "args": args if isinstance(args, dict) else {}})
            messaggi.append({"role": "assistant", "content": testo or None, "tool_calls": [
                {"id": f"call_{i}", "type": "function",
                 "function": {"name": c["name"], "arguments": json.dumps(c["args"])}}
                for i, c in enumerate(chiamate)]})
            for i, c in enumerate(chiamate):
                yield {"phase": "tool_run", "tool": c["name"]}
                try:
                    out = tool_exec(c["name"], dict(c["args"]))
                except Exception as exc:
                    out = {"error": str(exc)}
                messaggi.append({"role": "tool", "tool_call_id": f"call_{i}",
                                 "content": json.dumps(out, ensure_ascii=False,
                                                       default=str)[:6000]})
        yield {"phase": "done", "text": testo or "(troppi passaggi, mi fermo qui)"}


# --- Backend LOCALE (Ollama) -------------------------------------------------
# Stessa Protocol di AnthropicLLM, ma parla all'API nativa di Ollama (/api/chat).
# Pensato per girare su un Ollama REMOTO (il GB10 sempre acceso, esposto via
# Cloudflare Tunnel) o locale: per l'adapter è solo un URL HTTP.
#   - JSON garantito a schema col parametro `format` di Ollama (structured output).
#   - Nessuna dipendenza nuova: usa urllib della stdlib → niente da installare su Railway.
#   - Reasoning models (gpt-oss): il "think" NON va messo a false (svuota l'output);
#     si tiene a low/medium e si dà budget token largo, o il reasoning affama il JSON.
_OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
_LOCAL_MODEL = os.environ.get("AIOS_LOCAL_MODEL", "gpt-oss:120b")
_LOCAL_THINK = os.environ.get("AIOS_LOCAL_THINK", "medium")      # low|medium|high (mai false su gpt-oss)
_LOCAL_NUM_PREDICT = int(os.environ.get("AIOS_LOCAL_NUM_PREDICT", "8192"))  # budget out largo: headroom per il reasoning
# Pavimento sotto cui non si scende comunque: serve al reasoning di gpt-oss, che consuma
# token prima di scrivere. Ma NON è il default: un chiamante che chiede meno deve
# ottenere meno, altrimenti ogni risposta di chat ha il budget di un report.
_LOCAL_NUM_PREDICT_MIN = int(os.environ.get("AIOS_LOCAL_NUM_PREDICT_MIN", "768"))
# La CHAT è interattiva: chi aspetta guarda lo schermo. Budget e reasoning più corti,
# perché una risposta conversazionale non ha bisogno di 8192 token — e su un 120B remoto
# ogni token si paga in secondi.
_LOCAL_CHAT_NUM_PREDICT = int(os.environ.get("AIOS_LOCAL_CHAT_NUM_PREDICT", "1536"))
_LOCAL_CHAT_THINK = os.environ.get("AIOS_LOCAL_CHAT_THINK", "low")
_LOCAL_CHAT_ITERS = int(os.environ.get("AIOS_LOCAL_CHAT_ITERS", "3"))
# In chat si aspetta poco e non si ritenta. Con i parametri da background (600s × 3
# tentativi) una richiesta a un Ollama che non risponde teneva l'utente 30 MINUTI davanti
# a uno schermo muto: misurato il 19 ago 2026 — 885 secondi, 60 ping e nemmeno il triage.
# Meglio dire in un minuto «il modello non risponde» che tacere per mezz'ora.
_LOCAL_CHAT_TIMEOUT = int(os.environ.get("AIOS_LOCAL_CHAT_TIMEOUT", "75"))
_LOCAL_CHAT_RETRIES = int(os.environ.get("AIOS_LOCAL_CHAT_RETRIES", "0"))
_LOCAL_NUM_CTX = int(os.environ.get("AIOS_LOCAL_NUM_CTX", "16384"))         # ctx ampio: i prompt del board portano dati reali
_LOCAL_TIMEOUT = int(os.environ.get("AIOS_LOCAL_TIMEOUT", "600"))
_LOCAL_RETRIES = int(os.environ.get("AIOS_LOCAL_RETRIES", "2"))  # blip del tunnel → ritenta (opzione A: degrada e ritenta)
# Proxy SOLO per raggiungere Ollama (es. Tailscale userspace su Railway: http://localhost:1055).
# Scoped a LocalLLM: le altre uscite del board (Supabase, Anthropic) restano dirette.
_LOCAL_PROXY = os.environ.get("AIOS_LOCAL_PROXY", "").strip()


def _local_opener() -> urllib.request.OpenerDirector:
    if _LOCAL_PROXY:
        return urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": _LOCAL_PROXY, "https": _LOCAL_PROXY}))
    return urllib.request.build_opener()


def _local_headers() -> dict:
    """Header per /api/chat. Se presenti, aggiunge il service-token Cloudflare Access
    così solo il board può usare l'Ollama esposto dal tunnel."""
    h = {"Content-Type": "application/json"}
    cid = os.environ.get("OLLAMA_CF_ACCESS_CLIENT_ID")
    sec = os.environ.get("OLLAMA_CF_ACCESS_CLIENT_SECRET")
    if cid and sec:
        h["CF-Access-Client-Id"] = cid
        h["CF-Access-Client-Secret"] = sec
    return h


class LocalLLMUnreachable(RuntimeError):
    """Ollama non risponde (tailnet giù, GB10 spento, timeout). Errore di TRASPORTO,
    non di contenuto: è l'unico caso in cui vale la pena passare alla riserva."""


# Provider INUTILIZZABILE: non ci arrivo, non mi lascia entrare, o non ce la fa. Sono i
# casi in cui insistere è inutile e la riserva è la risposta giusta. Riconosciuti dal nome
# della classe per non importare l'SDK qui.
# Storia vera del 19 ago 2026, in mezza giornata: ANTHROPIC_BASE_URL puntava a un tunnel
# Cloudflare morto (APIConnectionError), e sotto c'era anche una ANTHROPIC_API_KEY non
# valida (401 authentication_error). Se la riserva coprisse solo il primo caso, il
# secondo fermerebbe i reparti — ed è esattamente quello che sarebbe successo stasera.
_PROVIDER_INUTILIZZABILE = (
    # trasporto
    "APIConnectionError", "APITimeoutError", "APIConnectionTimeoutError",
    "ConnectionError", "TimeoutError",
    # il provider non ce la fa
    "InternalServerError", "ServiceUnavailableError", "OverloadedError",
    "RateLimitError",
    # non mi lascia entrare / non ha quel modello
    "AuthenticationError", "PermissionDeniedError", "NotFoundError")


def guasto_di_trasporto(exc: BaseException) -> bool:
    """True se il provider è inutilizzabile (non ci arrivo, non mi lascia entrare, non
    ce la fa) e quindi vale la pena passare alla riserva.

    NON copre gli errori di CONTENUTO — prompt troppo lungo, schema non valido, JSON
    malformato: quelli devono emergere, perché sono bug nostri e la riserva li
    mascherebbe."""
    if isinstance(exc, LocalLLMUnreachable):
        return True
    nomi = {c.__name__ for c in type(exc).__mro__}
    if nomi & set(_PROVIDER_INUTILIZZABILE):
        return True
    # Ultima rete: il codice HTTP, con i tre nomi che usano SDK e urllib
    # (`urllib.error.HTTPError` espone `code`, non `status_code`).
    stato = (getattr(exc, "status_code", None) or getattr(exc, "status", None)
             or getattr(exc, "code", None))
    return stato in (401, 403, 404, 429, 500, 502, 503, 529)


class LocalLLM:
    """LLM locale via Ollama. Drop-in di AnthropicLLM per `complete`/`complete_json`."""

    def __init__(self, model: str | None = None, max_tokens: int | None = None,
                 base_url: str | None = None, think: str | None = None) -> None:
        self._model = model or _LOCAL_MODEL
        # Il chiamante decide: se chiede meno token, ne ottiene meno (col solo pavimento
        # tecnico per il reasoning). Prima era `max(richiesta, 8192)`, quindi anche una
        # risposta di chat generava fino a 8192 token — su un 120B remoto sono minuti.
        self._num_predict = (max(int(max_tokens), _LOCAL_NUM_PREDICT_MIN)
                             if max_tokens else _LOCAL_NUM_PREDICT)
        self._base = (base_url or _OLLAMA_BASE).rstrip("/")
        self._think = think if think is not None else _LOCAL_THINK

    def _think_value(self):
        t = str(self._think).lower()
        if t in ("false", "off", "no", "0"):
            return False        # sconsigliato su gpt-oss: svuota l'output
        if t in ("true", "on", "yes", "1"):
            return True
        return t                 # "low" | "medium" | "high" (livelli gpt-oss)

    def _chat(self, *, system: str, user: str, fmt: Any = None) -> str:
        body: dict[str, Any] = {
            "model": self._model, "stream": False, "think": self._think_value(),
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "options": {"num_predict": self._num_predict, "num_ctx": _LOCAL_NUM_CTX},
        }
        if fmt is not None:
            body["format"] = fmt
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        last: Exception | None = None
        for attempt in range(_LOCAL_RETRIES + 1):
            try:
                req = urllib.request.Request(self._base + "/api/chat", data=data,
                                             headers=_local_headers(), method="POST")
                with _local_opener().open(req, timeout=_LOCAL_TIMEOUT) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                try:  # metering: token locali (costo 0, ma visibilità dei consumi)
                    billing.record_usage(self._model,
                                         int(payload.get("prompt_eval_count", 0) or 0),
                                         int(payload.get("eval_count", 0) or 0))
                except Exception:
                    pass
                return payload.get("message", {}).get("content", "")
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
                last = exc
                if attempt < _LOCAL_RETRIES:
                    time.sleep(1.5 * (attempt + 1))
        raise LocalLLMUnreachable(
            f"LocalLLM: Ollama non raggiungibile su {self._base} "
            f"(modello {self._model}): {last}")

    def complete(self, *, system: str, user: str) -> str:
        return self._chat(system=system, user=user)

    def complete_json(self, *, system: str, user: str, schema: dict | None = None) -> dict:
        # `format`=schema → output vincolato allo schema; senza schema, "json" forza JSON valido
        text = self._chat(system=system, user=user, fmt=schema or "json")
        return _robust_json(text)

    # ---- streaming tool-use (chat multi-agente) ------------------------------
    @staticmethod
    def _tool_ollama(tools: list[dict] | None) -> list[dict]:
        """Definizioni tool dal formato Anthropic (`name`/`input_schema`) a quello di
        Ollama (`function`/`parameters`). I server-tool di Anthropic (web_search) non
        hanno equivalente: si scartano invece di far fallire la richiesta."""
        fuori = []
        for t in tools or []:
            nome = (t or {}).get("name")
            if not nome or t.get("type"):        # {"type": "web_search_..."} → non c'è
                continue
            fuori.append({"type": "function", "function": {
                "name": nome, "description": str(t.get("description") or "")[:1024],
                "parameters": t.get("input_schema") or {"type": "object", "properties": {}}}})
        return fuori

    @staticmethod
    def _immagini(media: list[dict] | None) -> list[str]:
        """Immagini base64 dai blocchi Anthropic → campo `images` di Ollama.
        I PDF restano fuori: il modello locale non li legge come blocchi nativi."""
        out = []
        for m in media or []:
            src = (m or {}).get("source") or {}
            if (src.get("type") == "base64"
                    and str(src.get("media_type") or "").startswith("image/")
                    and src.get("data")):
                out.append(src["data"])
        return out

    def _stream_chat(self, messages: list[dict], strumenti: list[dict],
                     max_tokens: int | None, think: Any = None,
                     timeout: int | None = None, retries: int | None = None):
        """Righe NDJSON di /api/chat con stream=true. Solleva LocalLLMUnreachable se
        Ollama non risponde, così la riserva può entrare come per le altre chiamate."""
        body: dict[str, Any] = {
            "model": self._model, "stream": True,
            "think": think if think is not None else self._think_value(),
            "messages": messages,
            "options": {"num_predict": int(max_tokens or self._num_predict),
                        "num_ctx": _LOCAL_NUM_CTX}}
        if strumenti:
            body["tools"] = strumenti
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        attesa = int(timeout if timeout is not None else _LOCAL_TIMEOUT)
        giri = int(retries if retries is not None else _LOCAL_RETRIES)
        last: Exception | None = None
        for tentativo in range(giri + 1):
            try:
                req = urllib.request.Request(self._base + "/api/chat", data=data,
                                             headers=_local_headers(), method="POST")
                with _local_opener().open(req, timeout=attesa) as resp:
                    for riga in resp:
                        riga = riga.strip()
                        if not riga:
                            continue
                        try:
                            yield json.loads(riga.decode("utf-8"))
                        except Exception:
                            continue        # riga parziale: la salta, lo stream continua
                return
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
                last = exc
                if tentativo < giri:
                    time.sleep(1.5 * (tentativo + 1))
        raise LocalLLMUnreachable(
            f"LocalLLM: Ollama non ha risposto entro {attesa}s su {self._base} "
            f"(modello {self._model}): {last}")

    def stream_agentic(self, *, system: str, user: str, tools: list[dict],
                       tool_exec, max_iters: int | None = None, max_tokens: int | None = None,
                       web_search: bool = False, history: list[dict] | None = None,
                       media: list[dict] | None = None):
        """Loop tool-use in streaming sul modello LOCALE, con gli stessi eventi della
        versione Anthropic — così il cockpit non cambia una riga.

        Perché esiste: lo streaming tool-use era solo di Anthropic, quindi con la chiave
        non valida (o senza) la chat multi-agente restava muta pur avendo un gpt-oss:120b
        perfettamente funzionante a due passi di distanza. Ora la chat gira sul locale.

        `web_search` viene ignorato: è un server-tool di Anthropic e qui non esiste — si
        preferisce una risposta senza ricerca web a nessuna risposta."""
        # Parametri da INTERATTIVO: chi aspetta una chat guarda lo schermo. Il chiamante
        # può ancora imporre il suo budget passando max_tokens/max_iters.
        budget = int(max_tokens) if max_tokens else _LOCAL_CHAT_NUM_PREDICT
        giri = int(max_iters) if max_iters else _LOCAL_CHAT_ITERS
        messages: list[dict] = [{"role": "system", "content": system}]
        messages += [m for m in (history or []) if isinstance(m, dict)]
        turno_utente: dict[str, Any] = {"role": "user", "content": user}
        immagini = self._immagini(media)
        if immagini:
            turno_utente["images"] = immagini
        messages.append(turno_utente)
        strumenti = self._tool_ollama(tools)

        for _ in range(giri):
            yield {"phase": "thinking"}
            testo, chiamate, iniziato = "", [], False
            for chunk in self._stream_chat(messages, strumenti, budget,
                                           think=_LOCAL_CHAT_THINK,
                                           timeout=_LOCAL_CHAT_TIMEOUT,
                                           retries=_LOCAL_CHAT_RETRIES):
                msg = chunk.get("message") or {}
                for tc in (msg.get("tool_calls") or []):
                    fn = (tc or {}).get("function") or {}
                    args = fn.get("arguments")
                    if isinstance(args, str):        # certe versioni le mandano come JSON
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {}
                    chiamate.append({"name": str(fn.get("name") or ""),
                                     "args": args if isinstance(args, dict) else {}})
                    yield {"phase": "tool", "tool": str(fn.get("name") or "")}
                pezzo = msg.get("content") or ""
                if pezzo:
                    if not iniziato:
                        yield {"phase": "writing"}
                        iniziato = True
                    testo += pezzo
                    yield {"phase": "delta", "text": pezzo}
                if chunk.get("done"):
                    try:      # metering: token locali (costo 0, ma visibilità dei consumi)
                        billing.record_usage(self._model,
                                             int(chunk.get("prompt_eval_count", 0) or 0),
                                             int(chunk.get("eval_count", 0) or 0))
                    except Exception:
                        pass
            if not chiamate:
                yield {"phase": "done", "text": testo}
                return
            messages.append({"role": "assistant", "content": testo, "tool_calls": [
                {"function": {"name": c["name"], "arguments": c["args"]}} for c in chiamate]})
            for c in chiamate:
                yield {"phase": "tool_run", "tool": c["name"]}
                try:
                    out = tool_exec(c["name"], dict(c["args"]))
                except Exception as exc:
                    out = {"error": str(exc)}
                messages.append({
                    "role": "tool", "tool_name": c["name"],
                    "content": json.dumps(out, ensure_ascii=False, default=str)[:6000]})
        yield {"phase": "done", "text": testo or "(troppi passaggi, mi fermo qui)"}


class FallbackLLM:
    """LLM con riserva: usa il primario, e se è IRRAGGIUNGIBILE passa al secondario.

    Il modello locale sul GB10 arriva via tailnet e va e viene: il 19 ago 2026 alle
    06:24 finance/operations/legal sono andati in timeout, alle 07:15 hanno girato tutti.
    Un reparto che salta il giro perde la giornata e non lo dice a nessuno (l'errore
    finisce solo nei log). Con la riserva l'agente gira comunque.

    Passa alla riserva SOLO su LocalLLMUnreachable, cioè un problema di trasporto: un
    JSON malformato o una risposta vuota restano errori del primario e devono emergere.
    """

    def __init__(self, primario: Any, riserva: Any) -> None:
        self._primario = primario
        self._riserva = riserva          # istanza o callable che la costruisce a richiesta
        self._istanza = None
        self.fallback_usati = 0

    def _backup(self):
        if self._istanza is None:
            self._istanza = self._riserva() if callable(self._riserva) else self._riserva
        return self._istanza

    def complete(self, *, system: str, user: str) -> str:
        try:
            return self._primario.complete(system=system, user=user)
        except Exception as exc:
            if not guasto_di_trasporto(exc):
                raise
            self.fallback_usati += 1
            print(f"[llm] primario giù ({type(exc).__name__}: {exc}) → passo alla riserva")
            return self._backup().complete(system=system, user=user)

    def complete_json(self, *, system: str, user: str, schema: dict | None = None) -> dict:
        try:
            return self._primario.complete_json(system=system, user=user, schema=schema)
        except Exception as exc:
            if not guasto_di_trasporto(exc):
                raise
            self.fallback_usati += 1
            print(f"[llm] primario giù ({type(exc).__name__}: {exc}) → passo alla riserva")
            return self._backup().complete_json(system=system, user=user, schema=schema)

    def stream_agentic(self, **kw):
        """Streaming tool-use con riserva, ma solo se il primario cade PRIMA di parlare.

        Se cade a metà stream la riserva non entra: ripartire da zero duplicherebbe il
        testo già arrivato all'utente. Meglio un troncamento visibile che una risposta
        schizofrenica. Se il primario non ha lo streaming, si usa direttamente la riserva."""
        primario = self._primario
        if not hasattr(primario, "stream_agentic"):
            yield from self._backup().stream_agentic(**kw)
            return
        # "Irreversibile" NON è il primo evento qualunque: `thinking` e `tool` sono
        # dichiarazioni di stato, non output. Contano solo il testo già mostrato
        # all'utente (`delta`) e un tool già ESEGUITO (`tool_run`) — ripartire dopo
        # quelli duplicherebbe testo o azioni.
        # Bug trovato in produzione il 19 ago 2026: la versione Anthropic emette
        # `thinking` PRIMA di aprire lo stream, quindi il 401 arrivava con "già parlato"
        # a true e la riserva non entrava mai.
        irreversibile = False
        try:
            for ev in primario.stream_agentic(**kw):
                if ev.get("phase") in ("delta", "tool_run"):
                    irreversibile = True
                yield ev
            return
        except Exception as exc:
            if irreversibile or not guasto_di_trasporto(exc):
                raise
            self.fallback_usati += 1
            print(f"[llm] stream del primario giù ({type(exc).__name__}) → riserva")
        yield from self._backup().stream_agentic(**kw)
