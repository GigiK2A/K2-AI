"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import type { ChatItem } from "@/types/agent";
import { ToolEventCard } from "./tool-event-card";

interface MessageListProps {
  items: ChatItem[];
}

export function MessageList({ items }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [items]);

  if (!items.length) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 px-4 py-16 text-center">
        <div className="text-3xl">G.</div>
        <p className="text-sm text-[color:var(--color-text-soft)]">
          Sono Giuseppina. Posso leggere lead, task, approvazioni, memos, meeting e revenue.
          <br />
          Le azioni di scrittura passano da te in <span className="text-[color:var(--color-teal)]">/approvazioni</span>.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {items.map(item => {
        if (item.kind === "user") {
          return (
            <div key={item.id} className="flex justify-end">
              <div className="max-w-[85%] rounded-2xl bg-[color:var(--color-teal)] px-4 py-2 text-sm text-black whitespace-pre-wrap break-words">
                {item.text}
              </div>
            </div>
          );
        }
        if (item.kind === "assistant") {
          return (
            <div key={item.id} className="flex justify-start">
              <div
                className={cn(
                  "max-w-[85%] rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] px-4 py-2 text-sm whitespace-pre-wrap break-words",
                  item.streaming && "opacity-95"
                )}
              >
                {item.text || (item.streaming ? "…" : "")}
              </div>
            </div>
          );
        }
        return (
          <div key={item.id} className="ml-1 mr-12">
            <ToolEventCard
              name={item.name}
              args={item.args}
              result={item.result}
              status={item.status}
            />
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
