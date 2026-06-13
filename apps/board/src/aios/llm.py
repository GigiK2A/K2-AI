from __future__ import annotations

import json
import os
import re
from typing import Any, Protocol


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
        for b in msg.content:
            if getattr(b, "type", None) == "tool_use":
                return dict(b.input)
        # fallback: parse any text
        text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
        return _robust_json(text)
