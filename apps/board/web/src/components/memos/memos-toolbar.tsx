"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";

export type MemoSortKey = "recent" | "subject";

const SORT_LABELS: Record<MemoSortKey, string> = {
  recent: "Più recenti",
  subject: "Titolo A-Z",
};

interface Props {
  search: string;
  onSearch: (s: string) => void;
  allTags: string[];
  selectedTags: Set<string>;
  onToggleTag: (t: string) => void;
  sort: MemoSortKey;
  onSort: (s: MemoSortKey) => void;
  onNewMemo: () => void;
}

export function MemosToolbar({
  search,
  onSearch,
  allTags,
  selectedTags,
  onToggleTag,
  sort,
  onSort,
  onNewMemo,
}: Props) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="relative w-full lg:max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--color-text-muted)]" />
          <Input
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            placeholder="Cerca in titolo, corpo o tag"
            className="pl-9"
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
            Ordina
          </label>
          <select
            value={sort}
            onChange={(e) => onSort(e.target.value as MemoSortKey)}
            className="h-9 rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-2 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
          >
            {(Object.keys(SORT_LABELS) as MemoSortKey[]).map((k) => (
              <option key={k} value={k}>
                {SORT_LABELS[k]}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={onNewMemo}
            className="inline-flex h-9 items-center gap-1 rounded-lg bg-[color:var(--color-teal)] px-3 text-sm font-medium text-black transition-colors hover:bg-[color:var(--color-teal-soft)]"
          >
            + Nuovo memo
          </button>
        </div>
      </div>

      {allTags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {allTags.map((tag) => {
            const active = selectedTags.has(tag);
            return (
              <button
                key={tag}
                type="button"
                onClick={() => onToggleTag(tag)}
                className={
                  "rounded-full border px-3 py-1 text-xs font-medium transition-colors " +
                  (active
                    ? "border-[color:var(--color-teal)] bg-[color:var(--color-teal)]/10 text-[color:var(--color-teal)]"
                    : "border-[color:var(--color-line-strong)] text-[color:var(--color-text-soft)] hover:text-[color:var(--color-text)]")
                }
              >
                #{tag}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
