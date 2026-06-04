from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from aios.autonomy import ActionType


@dataclass
class Tool:
    name: str
    action_type: ActionType | None
    run: Callable[..., Any]
    readonly: bool = False


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(name)
        return self._tools[name]

    def names(self) -> list[str]:
        return list(self._tools)
