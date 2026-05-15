"use client";

import type { PostHogProfileClick } from "@/types/posthog";
import { formatNumber } from "@/lib/format";

interface Props {
  clicks: PostHogProfileClick[];
}

export function ProfileClicksChart({ clicks }: Props) {
  if (clicks.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] p-6 text-center text-sm text-[color:var(--color-text-muted)]">
        Nessun click profilo registrato negli ultimi 30 giorni.
      </div>
    );
  }
  const max = Math.max(1, ...clicks.map((c) => c.count));
  return (
    <div className="rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] p-5">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="font-display text-base">Click per profilo</h2>
        <span className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--color-text-muted)]">
          Top 10 — ultimi 30 giorni
        </span>
      </div>
      <ul className="flex flex-col gap-2">
        {clicks.map((c) => {
          const pct = (c.count / max) * 100;
          return (
            <li key={c.profile_id} className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-xs">
                <span className="truncate font-mono text-[color:var(--color-text)]">
                  {c.profile_id}
                </span>
                <span className="text-[color:var(--color-text-soft)]">
                  {formatNumber(c.count)}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-[color:var(--color-bg-elevated)]">
                <div
                  className="h-full rounded-full bg-[color:var(--color-teal)]"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
