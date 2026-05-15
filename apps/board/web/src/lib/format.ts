// Italian-locale formatting helpers.

const NUM_FMT = new Intl.NumberFormat("it-IT");
const EURO_FMT = new Intl.NumberFormat("it-IT", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});
const TIME_FMT = new Intl.DateTimeFormat("it-IT", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});
const WEEKDAY_FMT = new Intl.DateTimeFormat("it-IT", { weekday: "long" });
const DAY_MONTH_FMT = new Intl.DateTimeFormat("it-IT", {
  day: "2-digit",
  month: "2-digit",
});

export function formatNumber(n: number): string {
  return NUM_FMT.format(n);
}

export function formatEuro(cents: number): string {
  return EURO_FMT.format(Math.round(cents) / 100);
}

export function formatTime(iso: string): string {
  return TIME_FMT.format(new Date(iso));
}

function dayDiff(target: Date, ref: Date): number {
  const a = new Date(target.getFullYear(), target.getMonth(), target.getDate());
  const b = new Date(ref.getFullYear(), ref.getMonth(), ref.getDate());
  return Math.round((a.getTime() - b.getTime()) / 86_400_000);
}

export function formatRelativeDay(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diff = dayDiff(d, now);
  if (diff === 0) return "oggi";
  if (diff === 1) return "domani";
  if (diff === -1) return "ieri";
  if (diff > 1 && diff < 7) return WEEKDAY_FMT.format(d);
  return DAY_MONTH_FMT.format(d);
}

export function formatRelativeDayTime(iso: string): string {
  return `${formatRelativeDay(iso)} ${formatTime(iso)}`;
}
