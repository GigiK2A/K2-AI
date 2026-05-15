import Link from "next/link";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";
import type { OverviewAlert, AlertSeverity } from "@/types/overview";

const severityStyle: Record<AlertSeverity, { box: string; icon: string }> = {
  high: {
    box: "border-[color:var(--color-danger)]/40 bg-[color:var(--color-danger)]/10 text-[color:var(--color-danger)]",
    icon: "text-[color:var(--color-danger)]",
  },
  medium: {
    box: "border-[color:var(--color-warning)]/40 bg-[color:var(--color-warning)]/10 text-[color:var(--color-warning)]",
    icon: "text-[color:var(--color-warning)]",
  },
  low: {
    box: "border-[color:var(--color-teal)]/40 bg-[color:var(--color-teal)]/10 text-[color:var(--color-teal)]",
    icon: "text-[color:var(--color-teal)]",
  },
};

function alertHref(a: OverviewAlert): string {
  switch (a.kind) {
    case "overdue_task":
      return a.ref_id ? `/tasks?focus=${a.ref_id}` : "/tasks";
    case "stale_lead":
      return "/pipeline";
    case "pending_approval":
      return "/approvazioni";
    default:
      return "/dashboard";
  }
}

function Icon({ severity }: { severity: AlertSeverity }) {
  if (severity === "high") return <AlertTriangle className="h-4 w-4 shrink-0" />;
  if (severity === "medium") return <AlertCircle className="h-4 w-4 shrink-0" />;
  return <Info className="h-4 w-4 shrink-0" />;
}

export function AlertsStrip({ alerts }: { alerts: OverviewAlert[] }) {
  if (alerts.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {alerts.map((a, i) => {
        const s = severityStyle[a.severity];
        return (
          <Link
            key={`${a.kind}-${a.ref_id ?? i}`}
            href={alertHref(a)}
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-opacity hover:opacity-80 ${s.box}`}
          >
            <span className={s.icon}>
              <Icon severity={a.severity} />
            </span>
            <span className="text-[color:var(--color-text)]">{a.title}</span>
          </Link>
        );
      })}
    </div>
  );
}
