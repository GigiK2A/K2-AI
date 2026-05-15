import type { RevenueEvent } from "@/types/revenue";

export const REVENUE_STATUS_LABELS: Record<string, string> = {
  succeeded: "Riuscito",
  refunded: "Rimborsato",
  failed: "Fallito",
  pending: "In sospeso",
};

export const REVENUE_STATUS_TONE: Record<string, string> = {
  succeeded:
    "border-[color:var(--color-success)]/40 bg-[color:var(--color-success)]/10 text-[color:var(--color-success)]",
  refunded:
    "border-[color:var(--color-warning)]/40 bg-[color:var(--color-warning)]/10 text-[color:var(--color-warning)]",
  failed:
    "border-[color:var(--color-danger)]/40 bg-[color:var(--color-danger)]/10 text-[color:var(--color-danger)]",
  pending:
    "border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-elevated)] text-[color:var(--color-text-soft)]",
};

export function statusTone(status: string): string {
  return (
    REVENUE_STATUS_TONE[status] ||
    "border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-elevated)] text-[color:var(--color-text-soft)]"
  );
}

export function statusLabel(status: string): string {
  return REVENUE_STATUS_LABELS[status] || status;
}

export type RevenueRangeKey = "30d" | "90d" | "ytd" | "all";

export function startForRange(range: RevenueRangeKey, now: Date = new Date()): Date | null {
  if (range === "all") return null;
  if (range === "30d") return new Date(now.getTime() - 30 * 86_400_000);
  if (range === "90d") return new Date(now.getTime() - 90 * 86_400_000);
  return new Date(now.getFullYear(), 0, 1);
}

export interface MonthBucket {
  year: number;
  month: number; // 0-11
  label: string; // it short
  total_cents: number;
}

const MONTH_SHORT = new Intl.DateTimeFormat("it-IT", { month: "short" });

export function lastNMonthsBuckets(events: RevenueEvent[], n = 6, now: Date = new Date()): MonthBucket[] {
  const buckets: MonthBucket[] = [];
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    buckets.push({
      year: d.getFullYear(),
      month: d.getMonth(),
      label: MONTH_SHORT.format(d),
      total_cents: 0,
    });
  }
  for (const e of events) {
    if (e.status !== "succeeded") continue;
    const d = new Date(e.occurred_at);
    const b = buckets.find((x) => x.year === d.getFullYear() && x.month === d.getMonth());
    if (b) b.total_cents += e.amount_cents;
  }
  return buckets;
}

export function mtdTotal(events: RevenueEvent[], now: Date = new Date()): number {
  return events
    .filter(
      (e) =>
        e.status === "succeeded" &&
        new Date(e.occurred_at).getFullYear() === now.getFullYear() &&
        new Date(e.occurred_at).getMonth() === now.getMonth(),
    )
    .reduce((acc, e) => acc + e.amount_cents, 0);
}

export function ytdTotal(events: RevenueEvent[], now: Date = new Date()): number {
  return events
    .filter(
      (e) =>
        e.status === "succeeded" &&
        new Date(e.occurred_at).getFullYear() === now.getFullYear(),
    )
    .reduce((acc, e) => acc + e.amount_cents, 0);
}

export function operationsThisMonth(events: RevenueEvent[], now: Date = new Date()): number {
  return events.filter(
    (e) =>
      new Date(e.occurred_at).getFullYear() === now.getFullYear() &&
      new Date(e.occurred_at).getMonth() === now.getMonth(),
  ).length;
}
