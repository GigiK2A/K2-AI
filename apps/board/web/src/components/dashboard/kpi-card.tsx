import { Card } from "@/components/ui/card";

interface KpiCardProps {
  label: string;
  value: string;
  sublabel?: string;
  accent?: "default" | "teal" | "warning" | "danger";
}

const accentClass: Record<NonNullable<KpiCardProps["accent"]>, string> = {
  default: "text-[color:var(--color-text)]",
  teal: "text-[color:var(--color-teal)]",
  warning: "text-[color:var(--color-warning)]",
  danger: "text-[color:var(--color-danger)]",
};

export function KpiCard({ label, value, sublabel, accent = "default" }: KpiCardProps) {
  return (
    <Card className="flex flex-col gap-2">
      <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
        {label}
      </span>
      <span
        className={`font-display text-[2.5rem] leading-none ${accentClass[accent]}`}
      >
        {value}
      </span>
      {sublabel && (
        <span className="text-xs text-[color:var(--color-text-soft)]">
          {sublabel}
        </span>
      )}
    </Card>
  );
}
