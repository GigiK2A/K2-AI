"use client";

import { useMemo, useState } from "react";
import type { Meeting } from "@/types/meeting";
import {
  currentWeekStart,
  sameDay,
  shortDayName,
  shortDayNum,
  weekDays,
} from "@/lib/meetings";
import { formatTime } from "@/lib/format";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface Props {
  meetings: Meeting[];
  onOpen: (m: Meeting) => void;
}

export function CalendarWeek({ meetings, onOpen }: Props) {
  const [weekStart, setWeekStart] = useState<Date>(() => currentWeekStart());

  const days = useMemo(() => weekDays(weekStart), [weekStart]);
  const today = new Date();

  function shift(deltaDays: number) {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + deltaDays);
    setWeekStart(d);
  }

  function resetThisWeek() {
    setWeekStart(currentWeekStart());
  }

  const meetingsByDay = useMemo(() => {
    const map = new Map<string, Meeting[]>();
    for (const d of days) {
      map.set(d.toDateString(), []);
    }
    for (const m of meetings) {
      const date = new Date(m.starts_at);
      const key = date.toDateString();
      if (map.has(key)) map.get(key)!.push(m);
    }
    for (const list of map.values()) {
      list.sort(
        (a, b) =>
          new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime(),
      );
    }
    return map;
  }, [meetings, days]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => shift(-7)}
            className="rounded-md border border-[color:var(--color-line-strong)] p-1.5 text-[color:var(--color-text-soft)] hover:bg-[color:var(--color-bg-elevated)]"
            aria-label="Settimana precedente"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => shift(7)}
            className="rounded-md border border-[color:var(--color-line-strong)] p-1.5 text-[color:var(--color-text-soft)] hover:bg-[color:var(--color-bg-elevated)]"
            aria-label="Settimana successiva"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={resetThisWeek}
            className="ml-2 rounded-md border border-[color:var(--color-line-strong)] px-2 py-1 text-xs text-[color:var(--color-text-soft)] hover:text-[color:var(--color-text)]"
          >
            Questa settimana
          </button>
        </div>
        <span className="text-xs text-[color:var(--color-text-muted)]">
          {shortDayNum(days[0])} – {shortDayNum(days[6])}
        </span>
      </div>

      <div className="grid grid-cols-7 gap-2">
        {days.map((d) => {
          const isToday = sameDay(d, today);
          const items = meetingsByDay.get(d.toDateString()) ?? [];
          return (
            <div
              key={d.toISOString()}
              className={
                "flex min-h-[180px] flex-col gap-1 rounded-xl border p-2 " +
                (isToday
                  ? "border-[color:var(--color-teal)]/50 bg-[color:var(--color-teal)]/5"
                  : "border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)]")
              }
            >
              <div className="flex items-baseline justify-between">
                <span className="text-[10px] uppercase tracking-[0.16em] text-[color:var(--color-text-muted)]">
                  {shortDayName(d)}
                </span>
                <span
                  className={
                    "text-sm font-semibold " +
                    (isToday
                      ? "text-[color:var(--color-teal)]"
                      : "text-[color:var(--color-text)]")
                  }
                >
                  {shortDayNum(d)}
                </span>
              </div>
              <div className="flex flex-1 flex-col gap-1">
                {items.length === 0 && (
                  <span className="text-[10px] text-[color:var(--color-text-muted)]">
                    —
                  </span>
                )}
                {items.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => onOpen(m)}
                    className="flex flex-col gap-0.5 rounded-md border border-[color:var(--color-teal)]/30 bg-[color:var(--color-teal)]/10 px-1.5 py-1 text-left transition-colors hover:bg-[color:var(--color-teal)]/20"
                  >
                    <span className="font-mono text-[10px] text-[color:var(--color-teal)]">
                      {formatTime(m.starts_at)}
                    </span>
                    <span className="line-clamp-2 text-[11px] leading-tight">
                      {m.title}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
