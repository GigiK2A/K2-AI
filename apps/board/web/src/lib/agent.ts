// Sprint 9A — Giuseppina client. Streams SSE from POST /api/agent/chat.

import type { AgentSSEEvent } from "@/types/agent";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export interface StreamChatArgs {
  message: string;
  conversationId?: string;
  signal?: AbortSignal;
  onEvent: (event: AgentSSEEvent) => void;
}

/**
 * POST a chat message and consume the SSE stream.
 * Parses `data: {json}\n\n` frames; ignores comments and blank lines.
 */
export async function streamChat({
  message,
  conversationId,
  signal,
  onEvent,
}: StreamChatArgs): Promise<void> {
  const res = await fetch(`${API_BASE}/api/agent/chat`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, conversation_id: conversationId ?? null }),
    signal,
  });

  if (!res.ok || !res.body) {
    const text = await res.text().catch(() => "");
    throw new Error(`agent chat failed: ${res.status} ${text}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames separated by blank line.
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const dataLines = frame
        .split("\n")
        .filter(l => l.startsWith("data: "))
        .map(l => l.slice(6));
      if (!dataLines.length) continue;
      const payload = dataLines.join("\n");
      try {
        const evt = JSON.parse(payload) as AgentSSEEvent;
        onEvent(evt);
      } catch {
        // ignore malformed frame
      }
    }
  }
}
