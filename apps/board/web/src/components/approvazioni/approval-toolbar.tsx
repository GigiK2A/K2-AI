"use client";

import { Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ApprovalKind } from "@/types/approval";
import {
  APPROVAL_KIND_LABELS,
  APPROVAL_KIND_ORDER,
} from "@/lib/approvals";

export type TabKey = "pending" | "decisi" | "tutti";
export type SortKey = "newest" | "oldest";

interface Props {
  tab: TabKey;
  onTabChange: (t: TabKey) => void;
  kinds: Set<ApprovalKind>;
  onKindsChange: (s: Set<ApprovalKind>) => void;
  sort: SortKey;
  onSortChange: (s: SortKey) => void;
  pendingCount: number;
  decidedCount: number;
  totalCount: number;
  selectedCount: number;
  showBulk: boolean;
  onBulkApprove: () => void;
  onBulkReject: () => void;
  bulkBusy: boolean;
}

const TABS: { key: TabKey; label: string }[] = [
  { key: "pending", label: "In attesa" },
  { key: "decisi", label: "Decisi" },
  { key: "tutti", label: "Tutti" },
];

export function ApprovalToolbar({
  tab,
  onTabChange,
  kinds,
  onKindsChange,
  sort,
  onSortChange,
  pendingCount,
  decidedCount,
  totalCount,
  selectedCount,
  showBulk,
  onBulkApprove,
  onBulkReject,
  bulkBusy,
}: Props) {
  function toggleKind(k: ApprovalKind) {
    const next = new Set(kinds);
    if (next.has(k)) next.delete(k);
    else next.add(k);
    onKindsChange(next);
  }

  function countFor(t: TabKey): number {
    if (t === "pending") return pendingCount;
    if (t === "decisi") return decidedCount;
    return totalCount;
  }

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] p-3">
      <div className="flex flex-wrap items-center gap-1">
        {TABS.map((t) => {
          const active = tab === t.key;
          return (
            <button
              key={t.key}
              type="button"
              onClick={() => onTabChange(t.key)}
              className={
                "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors " +
                (active
                  ? "bg-[color:var(--color-teal)] text-black"
                  : "text-[color:var(--color-text-soft)] hover:bg-[color:var(--color-bg-elevated)] hover:text-[color:var(--color-text)]")
              }
            >
              {t.label}
              <span
                className={
                  "ml-2 rounded-md px-1.5 py-0.5 text-[11px] " +
                  (active
                    ? "bg-black/15 text-black"
                    : "bg-[color:var(--color-bg-elevated)] text-[color:var(--color-text-muted)]")
                }
              >
                {countFor(t.key)}
              </span>
            </button>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[color:var(--color-text-muted)]">
          Tipo
        </span>
        {APPROVAL_KIND_ORDER.map((k) => {
          const active = kinds.has(k);
          return (
            <button
              key={k}
              type="button"
              onClick={() => toggleKind(k)}
              className={
                "rounded-full border px-3 py-1 text-xs transition-colors " +
                (active
                  ? "border-[color:var(--color-teal)] bg-[color:var(--color-teal)]/15 text-[color:var(--color-teal)]"
                  : "border-[color:var(--color-line-strong)] bg-transparent text-[color:var(--color-text-soft)] hover:bg-[color:var(--color-bg-elevated)]")
              }
            >
              {APPROVAL_KIND_LABELS[k]}
            </button>
          );
        })}

        <div className="ml-auto flex items-center gap-2">
          <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[color:var(--color-text-muted)]">
            Ordina
          </span>
          <select
            value={sort}
            onChange={(e) => onSortChange(e.target.value as SortKey)}
            className="h-8 rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-2 text-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
          >
            <option value="newest">Più recenti</option>
            <option value="oldest">Più vecchi</option>
          </select>
        </div>
      </div>

      {showBulk && (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[color:var(--color-line)] bg-[color:var(--color-bg-elevated)] px-3 py-2">
          <span className="text-xs text-[color:var(--color-text-soft)]">
            {selectedCount > 0
              ? `${selectedCount} selezionate`
              : "Seleziona le card per agire in blocco"}
          </span>
          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              onClick={onBulkApprove}
              disabled={bulkBusy || selectedCount === 0}
            >
              <Check className="h-4 w-4" />
              Approva selezionate
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={onBulkReject}
              disabled={bulkBusy || selectedCount === 0}
            >
              <X className="h-4 w-4" />
              Rifiuta selezionate
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
