"use client";

import { useCallback, useRef, useState } from "react";
import { streamChat } from "@/lib/agent";
import type { AgentSSEEvent, ChatItem } from "@/types/agent";
import { MessageList } from "./message-list";
import { Composer } from "./composer";

interface ChatShellProps {
  initialConversationId?: string;
  initialItems?: ChatItem[];
}

let itemCounter = 0;
const nextId = (prefix: string) => `${prefix}-${Date.now()}-${++itemCounter}`;

export function ChatShell({ initialConversationId, initialItems = [] }: ChatShellProps) {
  const [items, setItems] = useState<ChatItem[]>(initialItems);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const conversationIdRef = useRef<string | undefined>(initialConversationId);
  const assistantItemIdRef = useRef<string | null>(null);

  const ensureAssistantItem = useCallback(() => {
    if (assistantItemIdRef.current) return assistantItemIdRef.current;
    const id = nextId("a");
    assistantItemIdRef.current = id;
    setItems(prev => [...prev, { kind: "assistant", id, text: "", streaming: true }]);
    return id;
  }, []);

  const handleEvent = useCallback((evt: AgentSSEEvent) => {
    if (evt.type === "conversation") {
      conversationIdRef.current = evt.id;
      return;
    }
    if (evt.type === "text") {
      const id = ensureAssistantItem();
      setItems(prev =>
        prev.map(it =>
          it.kind === "assistant" && it.id === id
            ? { ...it, text: it.text + evt.content }
            : it
        )
      );
      return;
    }
    if (evt.type === "tool_call") {
      // Close current assistant block; a new one may follow after tool results.
      assistantItemIdRef.current = null;
      setItems(prev => [
        ...prev.map(it =>
          it.kind === "assistant" && it.streaming ? { ...it, streaming: false } : it
        ),
        {
          kind: "tool",
          id: evt.id,
          name: evt.name,
          args: evt.args,
          status: "running",
        },
      ]);
      return;
    }
    if (evt.type === "tool_result") {
      const isError = typeof (evt.result as { error?: unknown })?.error === "string";
      setItems(prev =>
        prev.map(it =>
          it.kind === "tool" && it.id === evt.id
            ? { ...it, result: evt.result, status: isError ? "error" : "done" }
            : it
        )
      );
      return;
    }
    if (evt.type === "final") {
      setItems(prev =>
        prev.map(it =>
          it.kind === "assistant" && it.streaming ? { ...it, streaming: false } : it
        )
      );
      return;
    }
    if (evt.type === "error") {
      setError(evt.message);
      return;
    }
  }, [ensureAssistantItem]);

  const send = useCallback(async (text: string) => {
    setError(null);
    setItems(prev => [...prev, { kind: "user", id: nextId("u"), text }]);
    assistantItemIdRef.current = null;
    setBusy(true);
    try {
      await streamChat({
        message: text,
        conversationId: conversationIdRef.current,
        onEvent: handleEvent,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
      setItems(prev =>
        prev.map(it =>
          it.kind === "assistant" && it.streaming ? { ...it, streaming: false } : it
        )
      );
      assistantItemIdRef.current = null;
    }
  }, [handleEvent]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-1 py-2">
        <MessageList items={items} />
      </div>
      {error && (
        <div className="mb-2 rounded-lg border border-[color:var(--color-danger)]/40 bg-[color:var(--color-danger)]/10 px-3 py-2 text-xs text-[color:var(--color-danger)]">
          {error}
        </div>
      )}
      <Composer onSend={send} busy={busy} />
    </div>
  );
}
