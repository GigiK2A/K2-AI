"use client";

import type { Memo } from "@/types/memo";
import { previewBody } from "@/lib/memos";
import { formatRelativeDay } from "@/lib/format";

interface Props {
  memo: Memo;
  onOpen: (memo: Memo) => void;
}

export function MemoCard({ memo, onOpen }: Props) {
  return (
    <button
      type="button"
      onClick={() => onOpen(memo)}
      className="flex flex-col gap-3 rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] p-4 text-left transition-colors hover:border-[color:var(--color-line-strong)] hover:bg-[color:var(--color-bg-elevated)]"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="line-clamp-2 font-display text-base leading-snug">
          {memo.subject || "(senza titolo)"}
        </h3>
        <span className="shrink-0 text-[11px] text-[color:var(--color-text-muted)]">
          {formatRelativeDay(memo.updated_at)}
        </span>
      </div>

      {memo.body && (
        <p className="whitespace-pre-wrap text-sm text-[color:var(--color-text-soft)]">
          {previewBody(memo.body)}
        </p>
      )}

      {memo.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {memo.tags.map((t) => (
            <span
              key={t}
              className="rounded-full border border-[color:var(--color-line-strong)] px-2 py-0.5 text-[10px] text-[color:var(--color-text-soft)]"
            >
              #{t}
            </span>
          ))}
        </div>
      )}
    </button>
  );
}
