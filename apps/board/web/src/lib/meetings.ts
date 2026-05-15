import type { Meeting } from "@/types/meeting";
import { formatTime, formatRelativeDay } from "@/lib/format";

const DATE_KEY_FMT = new Intl.DateTimeFormat("it-IT", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

export function dayKey(iso: string): string {
  return DATE_KEY_FMT.format(new Date(iso));
}

export function dayLabel(iso: string): string {
  return formatRelativeDay(iso);
}

export function timeRange(meeting: Meeting): string {
  return `${formatTime(meeting.starts_at)} – ${formatTime(meeting.ends_at)}`;
}

export function groupByDay(meetings: Meeting[]): Array<{
  key: string;
  iso: string;
  label: string;
  items: Meeting[];
}> {
  const sorted = [...meetings].sort(
    (a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime(),
  );
  const groups = new Map<string, { iso: string; items: Meeting[] }>();
  for (const m of sorted) {
    const k = dayKey(m.starts_at);
    if (!groups.has(k)) groups.set(k, { iso: m.starts_at, items: [] });
    groups.get(k)!.items.push(m);
  }
  return Array.from(groups.entries()).map(([key, { iso, items }]) => ({
    key,
    iso,
    label: dayLabel(iso),
    items,
  }));
}

// Returns array of 7 Date objects (mon-sun) for the current week (relative to ref).
export function currentWeekStart(ref: Date = new Date()): Date {
  const d = new Date(ref.getFullYear(), ref.getMonth(), ref.getDate());
  const day = d.getDay(); // 0=sun..6=sat
  const offset = day === 0 ? -6 : 1 - day; // shift to monday
  d.setDate(d.getDate() + offset);
  return d;
}

export function weekDays(start: Date): Date[] {
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    return d;
  });
}

const DAY_NAME = new Intl.DateTimeFormat("it-IT", { weekday: "short" });
const DAY_NUM = new Intl.DateTimeFormat("it-IT", { day: "2-digit" });

export function shortDayName(d: Date): string {
  return DAY_NAME.format(d);
}

export function shortDayNum(d: Date): string {
  return DAY_NUM.format(d);
}

export function sameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}
