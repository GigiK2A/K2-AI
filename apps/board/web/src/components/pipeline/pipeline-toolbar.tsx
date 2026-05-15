"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import type { LeadSource } from "@/types/lead";
import { SOURCE_LABELS } from "@/lib/leads";

export type SortKey = "recent" | "value" | "next_action";

const SORT_LABELS: Record<SortKey, string> = {
  recent: "Più recenti",
  value: "Valore più alto",
  next_action: "Prossima azione",
};

const SOURCE_FILTERS: LeadSource[] = [
  "k_bot",
  "contact_form",
  "newsletter",
  "outbound",
  "other",
];

interface Props {
  search: string;
  onSearch: (s: string) => void;
  sources: Set<LeadSource>;
  onToggleSource: (src: LeadSource) => void;
  sort: SortKey;
  onSort: (s: SortKey) => void;
  onNewLead: () => void;
}

export function PipelineToolbar({
  search,
  onSearch,
  sources,
  onToggleSource,
  sort,
  onSort,
  onNewLead,
}: Props) {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-1 flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative w-full lg:max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--color-text-muted)]" />
          <Input
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            placeholder="Cerca lead, azienda o persona"
            className="pl-9"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {SOURCE_FILTERS.map((src) => {
            const active = sources.has(src);
            return (
              <button
                key={src}
                type="button"
                onClick={() => onToggleSource(src)}
                className={
                  "rounded-full border px-3 py-1 text-xs font-medium transition-colors " +
                  (active
                    ? "border-[color:var(--color-teal)] bg-[color:var(--color-teal)]/10 text-[color:var(--color-teal)]"
                    : "border-[color:var(--color-line-strong)] text-[color:var(--color-text-soft)] hover:text-[color:var(--color-text)]")
                }
              >
                {SOURCE_LABELS[src]}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <label className="text-xs uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
          Ordina
        </label>
        <select
          value={sort}
          onChange={(e) => onSort(e.target.value as SortKey)}
          className="h-9 rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-2 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
        >
          {(Object.keys(SORT_LABELS) as SortKey[]).map((k) => (
            <option key={k} value={k}>
              {SORT_LABELS[k]}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={onNewLead}
          className="inline-flex h-9 items-center gap-1 rounded-lg bg-[color:var(--color-teal)] px-3 text-sm font-medium text-black transition-colors hover:bg-[color:var(--color-teal-soft)]"
        >
          + Nuovo lead
        </button>
      </div>
    </div>
  );
}
