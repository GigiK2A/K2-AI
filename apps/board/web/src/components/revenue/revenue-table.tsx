"use client";

import type { RevenueEvent } from "@/types/revenue";
import { formatEuro, formatRelativeDayTime } from "@/lib/format";
import { statusLabel, statusTone } from "@/lib/revenue";

interface Props {
  events: RevenueEvent[];
}

export function RevenueTable({ events }: Props) {
  if (events.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] p-8 text-center text-sm text-[color:var(--color-text-muted)]">
        Nessun evento nel periodo selezionato.
      </div>
    );
  }
  return (
    <div className="overflow-hidden rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)]">
      <div className="hidden grid-cols-[1.2fr_2fr_2fr_1fr_1fr] gap-3 border-b border-[color:var(--color-line)] px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-[color:var(--color-text-muted)] md:grid">
        <span>Data</span>
        <span>Descrizione</span>
        <span>Cliente</span>
        <span className="text-right">Importo</span>
        <span>Stato</span>
      </div>
      <ul className="divide-y divide-[color:var(--color-line)]">
        {events.map((e) => (
          <li
            key={e.id}
            className="grid grid-cols-2 gap-2 px-4 py-3 text-sm md:grid-cols-[1.2fr_2fr_2fr_1fr_1fr] md:gap-3"
          >
            <span className="text-[color:var(--color-text-soft)]">
              {formatRelativeDayTime(e.occurred_at)}
            </span>
            <span className="truncate md:col-span-1" title={e.description ?? e.external_id}>
              {e.description || e.external_id}
            </span>
            <span className="truncate text-[color:var(--color-text-soft)]">
              {e.customer_email || "—"}
            </span>
            <span className="text-right font-medium md:col-span-1">
              {formatEuro(e.amount_cents)}
            </span>
            <span>
              <span
                className={
                  "inline-block rounded-full border px-2 py-0.5 text-[10px] font-medium " +
                  statusTone(e.status)
                }
              >
                {statusLabel(e.status)}
              </span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
