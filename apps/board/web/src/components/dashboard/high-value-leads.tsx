import Link from "next/link";
import type { HighValueLead } from "@/types/overview";
import { formatEuro } from "@/lib/format";

export function HighValueLeads({ leads }: { leads: HighValueLead[] }) {
  const top = leads.slice(0, 3);
  if (top.length === 0) {
    return (
      <p className="text-sm text-[color:var(--color-text-muted)]">
        Nessun lead di alto valore aperto.
      </p>
    );
  }
  return (
    <ul className="flex flex-col divide-y divide-[color:var(--color-line)]">
      {top.map((l) => (
        <li key={l.id} className="py-3 first:pt-0 last:pb-0">
          <Link
            href={`/pipeline?lead=${l.id}`}
            className="group flex items-center justify-between gap-3"
          >
            <span className="min-w-0 truncate text-sm text-[color:var(--color-text)] group-hover:text-[color:var(--color-teal)]">
              {l.title}
            </span>
            <span className="flex shrink-0 items-center gap-2">
              <span className="font-display text-sm tabular-nums text-[color:var(--color-text)]">
                {formatEuro(l.value_eur * 100)}
              </span>
              <span className="rounded-full border border-[color:var(--color-line-strong)] px-2 py-0.5 text-[10px] tabular-nums text-[color:var(--color-text-soft)]">
                {l.probability}%
              </span>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
