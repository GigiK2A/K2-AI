import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { requireUser } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import type { OverviewResponse } from "@/types/overview";
import { Card } from "@/components/ui/card";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { AlertsStrip } from "@/components/dashboard/alerts-strip";
import { PipelineFunnel } from "@/components/dashboard/pipeline-funnel";
import { HighValueLeads } from "@/components/dashboard/high-value-leads";
import { NextMeetingCard } from "@/components/dashboard/next-meeting-card";
import { EmptyState } from "@/components/dashboard/empty-state";
import { formatEuro, formatNumber } from "@/lib/format";

const QUICK_LINKS = [
  { href: "/pipeline", label: "Pipeline" },
  { href: "/approvazioni", label: "Approvazioni" },
  { href: "/tasks", label: "Task" },
  { href: "/memos", label: "Memo" },
];

export default async function DashboardPage() {
  const user = await requireUser();
  const data = await apiFetch<OverviewResponse>("/api/overview/");

  const { leads, tasks, approvals_pending, revenue_mtd_cents, next_meeting, alerts } = data;
  const pipelineTotal =
    (leads.by_status.nuovo ?? 0) +
    (leads.by_status.contatto ?? 0) +
    (leads.by_status.proposta ?? 0);
  const urgentTasks = tasks.overdue + tasks.today;

  const isEmpty =
    leads.active === 0 &&
    pipelineTotal === 0 &&
    approvals_pending === 0 &&
    revenue_mtd_cents === 0 &&
    urgentTasks === 0 &&
    alerts.length === 0 &&
    !next_meeting;

  return (
    <div className="flex flex-col gap-6 p-4 md:p-6 lg:p-8">
      <header className="flex flex-col gap-1">
        <h1 className="font-display text-2xl md:text-3xl">Dashboard</h1>
        <p className="text-sm text-[color:var(--color-text-soft)]">
          Sintesi operativa della giornata.
        </p>
      </header>

      {isEmpty ? (
        <EmptyState username={user.username} />
      ) : (
        <>
          {alerts.length > 0 && <AlertsStrip alerts={alerts} />}

          <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <KpiCard
              label="Lead attivi"
              value={formatNumber(leads.active)}
              sublabel={`Pipeline: ${formatNumber(pipelineTotal)}`}
              accent="teal"
            />
            <KpiCard
              label="Approvazioni"
              value={formatNumber(approvals_pending)}
              sublabel="Da decidere"
              accent={approvals_pending > 0 ? "warning" : "default"}
            />
            <KpiCard
              label="Revenue MTD"
              value={formatEuro(revenue_mtd_cents)}
              sublabel="Mese in corso"
            />
            <KpiCard
              label="Task urgenti"
              value={formatNumber(urgentTasks)}
              sublabel="Oggi + scaduti"
              accent={urgentTasks > 0 ? "danger" : "default"}
            />
          </section>

          <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <Card className="flex flex-col gap-5 md:col-span-2">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
                  Pipeline veloce
                </h2>
                <Link
                  href="/pipeline"
                  className="inline-flex items-center gap-1 text-xs text-[color:var(--color-teal)] hover:underline"
                >
                  Apri pipeline <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
              <PipelineFunnel byStatus={leads.by_status} />
              <div className="border-t border-[color:var(--color-line)] pt-4">
                <h3 className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
                  Top lead aperti
                </h3>
                <HighValueLeads leads={leads.high_value} />
              </div>
            </Card>

            <div className="flex flex-col gap-4">
              {next_meeting && <NextMeetingCard meeting={next_meeting} />}

              <Card className="flex flex-col gap-3">
                <h2 className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
                  Task
                </h2>
                <div className="grid grid-cols-2 gap-3">
                  <Link
                    href="/tasks?range=today"
                    className="rounded-lg bg-[color:var(--color-bg-elevated)] p-3 transition-colors hover:bg-[color:var(--color-bg)]"
                  >
                    <div className="font-display text-2xl leading-none">
                      {formatNumber(tasks.today)}
                    </div>
                    <div className="mt-1 text-xs text-[color:var(--color-text-soft)]">
                      Oggi
                    </div>
                  </Link>
                  <Link
                    href="/tasks?range=week"
                    className="rounded-lg bg-[color:var(--color-bg-elevated)] p-3 transition-colors hover:bg-[color:var(--color-bg)]"
                  >
                    <div className="font-display text-2xl leading-none">
                      {formatNumber(tasks.this_week)}
                    </div>
                    <div className="mt-1 text-xs text-[color:var(--color-text-soft)]">
                      Questa settimana
                    </div>
                  </Link>
                </div>
              </Card>

              <Card className="flex flex-col gap-2">
                <h2 className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
                  Vai a
                </h2>
                <ul className="flex flex-col">
                  {QUICK_LINKS.map((q) => (
                    <li key={q.href}>
                      <Link
                        href={q.href}
                        className="group flex items-center justify-between rounded-md px-2 py-2 text-sm transition-colors hover:bg-[color:var(--color-bg-elevated)]"
                      >
                        <span>{q.label}</span>
                        <ArrowRight className="h-4 w-4 text-[color:var(--color-text-muted)] group-hover:text-[color:var(--color-teal)]" />
                      </Link>
                    </li>
                  ))}
                </ul>
              </Card>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
