"use client";

import type { Meeting } from "@/types/meeting";
import { groupByDay, timeRange } from "@/lib/meetings";
import { ExternalLink, Users } from "lucide-react";

interface Props {
  meetings: Meeting[];
  onOpen: (m: Meeting) => void;
}

export function CalendarList({ meetings, onOpen }: Props) {
  if (meetings.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] p-8 text-center text-sm text-[color:var(--color-text-muted)]">
        Nessun meeting in programma.
      </div>
    );
  }
  const groups = groupByDay(meetings);
  return (
    <div className="flex flex-col gap-5">
      {groups.map((g) => (
        <section key={g.key} className="flex flex-col gap-2">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
            {g.label}
          </h3>
          <ul className="flex flex-col gap-2">
            {g.items.map((m) => (
              <li
                key={m.id}
                className="flex items-center gap-3 rounded-xl border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] p-3"
              >
                <span className="shrink-0 rounded-lg bg-[color:var(--color-bg-elevated)] px-3 py-1.5 font-mono text-xs text-[color:var(--color-teal)]">
                  {timeRange(m)}
                </span>
                <button
                  type="button"
                  onClick={() => onOpen(m)}
                  className="flex-1 truncate text-left text-sm font-medium hover:text-[color:var(--color-teal)]"
                >
                  {m.title}
                </button>
                {m.attendees.length > 0 && (
                  <span className="hidden items-center gap-1 text-[11px] text-[color:var(--color-text-muted)] md:inline-flex">
                    <Users className="h-3 w-3" />
                    {m.attendees.length}
                  </span>
                )}
                {m.meet_link && (
                  <a
                    href={m.meet_link}
                    target="_blank"
                    rel="noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="inline-flex items-center gap-1 rounded-md border border-[color:var(--color-line-strong)] px-2 py-1 text-[11px] text-[color:var(--color-text-soft)] hover:text-[color:var(--color-text)]"
                  >
                    <ExternalLink className="h-3 w-3" />
                    Apri
                  </a>
                )}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
