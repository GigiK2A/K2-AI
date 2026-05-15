"use client";

import { useMemo, useState } from "react";
import type { RevenueEvent } from "@/types/revenue";
import {
  lastNMonthsBuckets,
  mtdTotal,
  operationsThisMonth,
  startForRange,
  ytdTotal,
  type RevenueRangeKey,
} from "@/lib/revenue";
import { RevenueKpis } from "./revenue-kpis";
import { RevenueChart } from "./revenue-chart";
import { RevenueTable } from "./revenue-table";
import { RevenueToolbar } from "./revenue-toolbar";

interface Props {
  events: RevenueEvent[];
}

export function RevenueOverview({ events }: Props) {
  const [range, setRange] = useState<RevenueRangeKey>("30d");
  const [statuses, setStatuses] = useState<Set<string>>(new Set());
  const [syncNotice, setSyncNotice] = useState(false);

  const mtd = useMemo(() => mtdTotal(events), [events]);
  const ytd = useMemo(() => ytdTotal(events), [events]);
  const ops = useMemo(() => operationsThisMonth(events), [events]);
  const buckets = useMemo(() => lastNMonthsBuckets(events), [events]);

  const filtered = useMemo(() => {
    const start = startForRange(range);
    return events
      .filter((e) => {
        if (start && new Date(e.occurred_at) < start) return false;
        if (statuses.size > 0 && !statuses.has(e.status)) return false;
        return true;
      })
      .sort(
        (a, b) =>
          new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime(),
      );
  }, [events, range, statuses]);

  function toggleStatus(s: string) {
    setStatuses((prev) => {
      const next = new Set(prev);
      if (next.has(s)) next.delete(s);
      else next.add(s);
      return next;
    });
  }

  return (
    <div className="flex flex-col gap-4">
      <RevenueKpis mtdCents={mtd} ytdCents={ytd} operationsMonth={ops} />
      <RevenueChart buckets={buckets} />
      <RevenueToolbar
        range={range}
        onRangeChange={setRange}
        statuses={statuses}
        onToggleStatus={toggleStatus}
        onSync={() => setSyncNotice(true)}
      />
      {syncNotice && (
        <div className="flex items-center justify-between rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-elevated)] px-3 py-2 text-xs text-[color:var(--color-text-soft)]">
          <span>La sincronizzazione Stripe arriva con lo Sprint 7.</span>
          <button onClick={() => setSyncNotice(false)} className="underline">
            Ok
          </button>
        </div>
      )}
      <RevenueTable events={filtered} />
    </div>
  );
}
