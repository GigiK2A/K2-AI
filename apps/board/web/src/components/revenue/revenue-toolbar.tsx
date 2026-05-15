"use client";

import type { RevenueRangeKey } from "@/lib/revenue";

const RANGE_LABELS: Record<RevenueRangeKey, string> = {
  "30d": "30 giorni",
  "90d": "90 giorni",
  ytd: "Da inizio anno",
  all: "Tutto",
};

const STATUS_FILTERS = ["succeeded", "refunded", "failed"] as const;
const STATUS_LABELS: Record<(typeof STATUS_FILTERS)[number], string> = {
  succeeded: "Riusciti",
  refunded: "Rimborsati",
  failed: "Falliti",
};

interface Props {
  range: RevenueRangeKey;
  onRangeChange: (r: RevenueRangeKey) => void;
  statuses: Set<string>;
  onToggleStatus: (s: string) => void;
  onSync: () => void;
}

export function RevenueToolbar({
  range,
  onRangeChange,
  statuses,
  onToggleStatus,
  onSync,
}: Props) {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
          Periodo
        </span>
        {(Object.keys(RANGE_LABELS) as RevenueRangeKey[]).map((k) => (
          <button
            key={k}
            type="button"
            onClick={() => onRangeChange(k)}
            className={
              "rounded-full border px-3 py-1 text-xs font-medium transition-colors " +
              (range === k
                ? "border-[color:var(--color-teal)] bg-[color:var(--color-teal)]/10 text-[color:var(--color-teal)]"
                : "border-[color:var(--color-line-strong)] text-[color:var(--color-text-soft)] hover:text-[color:var(--color-text)]")
            }
          >
            {RANGE_LABELS[k]}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {STATUS_FILTERS.map((s) => {
          const active = statuses.has(s);
          return (
            <button
              key={s}
              type="button"
              onClick={() => onToggleStatus(s)}
              className={
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors " +
                (active
                  ? "border-[color:var(--color-teal)] bg-[color:var(--color-teal)]/10 text-[color:var(--color-teal)]"
                  : "border-[color:var(--color-line-strong)] text-[color:var(--color-text-soft)] hover:text-[color:var(--color-text)]")
              }
            >
              {STATUS_LABELS[s]}
            </button>
          );
        })}
        <button
          type="button"
          onClick={onSync}
          disabled
          title="Coming Sprint 7"
          className="inline-flex h-9 items-center gap-1 rounded-lg border border-[color:var(--color-line-strong)] px-3 text-xs font-medium text-[color:var(--color-text-soft)] opacity-60"
        >
          ↻ Sincronizza Stripe
        </button>
      </div>
    </div>
  );
}
