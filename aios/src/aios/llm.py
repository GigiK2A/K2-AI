from __future__ import annotations

import os
from typing import Protocol


class LLM(Protocol):
    def complete(self, *, system: str, user: str) -> str: ...


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
