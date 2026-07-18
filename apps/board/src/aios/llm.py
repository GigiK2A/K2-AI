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


class LocalLLM:
    """LLM locale via Ollama. Drop-in di AnthropicLLM per `complete`/`complete_json`."""

    def __init__(self, model: str | None = None, max_tokens: int | None = None,
                 base_url: str | None = None, think: str | None = None) -> None:
        self._model = model or _LOCAL_MODEL
        # num_predict = il più largo tra quanto chiede il chiamante e il default generoso
        self._num_predict = max(int(max_tokens or 0), _LOCAL_NUM_PREDICT)
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
        raise RuntimeError(
            f"LocalLLM: Ollama non raggiungibile su {self._base} "
            f"(modello {self._model}): {last}")

    def complete(self, *, system: str, user: str) -> str:
        return self._chat(system=system, user=user)

    def complete_json(self, *, system: str, user: str, schema: dict | None = None) -> dict:
        # `format`=schema → output vincolato allo schema; senza schema, "json" forza JSON valido
        text = self._chat(system=system, user=user, fmt=schema or "json")
        return _robust_json(text)
