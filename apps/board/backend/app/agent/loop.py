"""Giuseppina agent loop — Anthropic tool-use with streaming SSE events.

Model: claude-haiku-4-5 (fast + cheap for tool-use). Reasoning quality on the
tool-use loop is good enough; if Giuseppina starts looping or skipping tools
we can swap to claude-sonnet-4-5 by changing AGENT_MODEL.
"""
from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from anthropic import AsyncAnthropic

from app.agent.executor import execute_tool
from app.agent.prompt import build_system_prompt
from app.agent.tools import TOOLS
from app.db.client import get_supabase
from app.settings import get_settings

log = logging.getLogger(__name__)


AGENT_MODEL = "claude-haiku-4-5"
MAX_ITERATIONS = 10
MAX_TOKENS = 2048


def _client() -> AsyncAnthropic:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")
    return AsyncAnthropic(api_key=settings.anthropic_api_key)


def _sse(event_type: str, data: Dict[str, Any]) -> str:
    """Render a single SSE event."""
    payload = {"type": event_type, **data}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def run_agent(
    history: List[Dict[str, Any]],
    user_message: str,
) -> AsyncGenerator[str, None]:
    """Run Giuseppina against a user turn, streaming SSE-formatted events.

    `history` is the prior conversation in Anthropic message format
    (`[{role, content}]`). The current user_message is appended.

    Yields SSE event strings:
      data: {"type":"text","content":"..."}
      data: {"type":"tool_call","id":"...","name":"...","args":{...}}
      data: {"type":"tool_result","id":"...","name":"...","result":{...}}
      data: {"type":"final","content":"..."}  — full assistant text at end
      data: {"type":"done","messages":[...]}  — final message list to persist
      data: {"type":"error","message":"..."}
    """
    client = _client()
    sb = get_supabase()
    system_prompt = build_system_prompt()

    messages: List[Dict[str, Any]] = list(history) + [
        {"role": "user", "content": user_message}
    ]

    full_assistant_text = ""

    for iteration in range(MAX_ITERATIONS):
        try:
            response = await client.messages.create(
                model=AGENT_MODEL,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                tools=TOOLS,
                messages=messages,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("agent.api_error")
            yield _sse("error", {"message": f"Errore chiamata Claude: {exc}"})
            return

        # Collect assistant content blocks
        assistant_blocks: List[Dict[str, Any]] = []
        tool_uses: List[Dict[str, Any]] = []
        iteration_text = ""

        for block in response.content:
            btype = getattr(block, "type", None)
            if btype == "text":
                text = block.text or ""
                iteration_text += text
                assistant_blocks.append({"type": "text", "text": text})
                if text:
                    yield _sse("text", {"content": text})
            elif btype == "tool_use":
                tu = {
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input or {},
                }
                assistant_blocks.append(tu)
                tool_uses.append(tu)
                yield _sse(
                    "tool_call",
                    {"id": block.id, "name": block.name, "args": block.input or {}},
                )

        full_assistant_text += iteration_text

        # Append the assistant turn (must include tool_use blocks so the
        # tool_result blocks we send next reference valid ids).
        messages.append({"role": "assistant", "content": assistant_blocks})

        # If no tool calls or model signalled end of turn, finish.
        if not tool_uses or response.stop_reason == "end_turn":
            yield _sse("final", {"content": full_assistant_text})
            yield _sse("done", {"messages": messages})
            return

        # Execute tools, build a single user turn carrying tool_result blocks.
        tool_result_blocks: List[Dict[str, Any]] = []
        for tu in tool_uses:
            result = await execute_tool(tu["name"], tu["input"], sb)
            yield _sse(
                "tool_result",
                {"id": tu["id"], "name": tu["name"], "result": result},
            )
            tool_result_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu["id"],
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                }
            )

        messages.append({"role": "user", "content": tool_result_blocks})

    # Iteration cap hit
    yield _sse(
        "error",
        {"message": f"Limite iterazioni ({MAX_ITERATIONS}) raggiunto."},
    )
    yield _sse("done", {"messages": messages})
