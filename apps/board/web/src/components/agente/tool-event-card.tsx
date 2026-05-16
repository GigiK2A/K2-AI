"use client";

import { useState } from "react";
import { ChevronRight, Loader2, CheckCircle2, AlertTriangle, ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface ToolEventCardProps {
  name: string;
  args: Record<string, unknown>;
  result?: Record<string, unknown>;
  status: "running" | "done" | "error";
}

const TOOL_LABELS: Record<string, string> = {
  list_leads: "Elenco lead",
  get_lead: "Dettaglio lead",
  search_contacts: "Ricerca contatti",
  list_tasks: "Elenco task",
  list_pending_approvals: "Approvazioni pending",
  search_memos: "Ricerca memos",
  get_revenue_summary: "Revenue summary",
  list_meetings: "Elenco meeting",
  fetch_url: "Fetch URL",
  overview_snapshot: "Snapshot board",
  propose_new_lead: "Proposta: nuovo lead",
  propose_lead_update: "Proposta: modifica lead",
  propose_email_draft: "Proposta: draft email",
  propose_proposta_commerciale: "Proposta: commerciale",
  propose_task: "Proposta: nuovo task",
  add_memo: "Memo aggiunto",
};

export function ToolEventCard({ name, args, result, status }: ToolEventCardProps) {
  const [open, setOpen] = useState(false);
  const label = TOOL_LABELS[name] ?? name;
  const approvalId = typeof result?.approval_id === "string" ? result.approval_id : null;
  const isError = status === "error" || (result && typeof result.error === "string");

  return (
    <div
      className={cn(
        "rounded-lg border bg-[color:var(--color-bg-elevated)] text-xs",
        isError
          ? "border-[color:var(--color-danger)]/40"
          : "border-[color:var(--color-line)]"
      )}
    >
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
      >
        <ChevronRight
          size={14}
          className={cn(
            "shrink-0 transition-transform text-[color:var(--color-text-muted)]",
            open && "rotate-90"
          )}
        />
        {status === "running" && (
          <Loader2 size={14} className="shrink-0 animate-spin text-[color:var(--color-teal)]" />
        )}
        {status === "done" && !isError && (
          <CheckCircle2 size={14} className="shrink-0 text-[color:var(--color-teal)]" />
        )}
        {isError && <AlertTriangle size={14} className="shrink-0 text-[color:var(--color-danger)]" />}
        <span className="font-medium text-[color:var(--color-text)]">{label}</span>
        <span className="ml-auto text-[10px] uppercase tracking-wide text-[color:var(--color-text-muted)]">
          {status === "running" ? "in corso" : isError ? "errore" : "ok"}
        </span>
      </button>

      {open && (
        <div className="border-t border-[color:var(--color-line)] px-3 py-2 space-y-2">
          <div>
            <div className="mb-1 text-[10px] uppercase tracking-wide text-[color:var(--color-text-muted)]">
              Argomenti
            </div>
            <pre className="overflow-x-auto whitespace-pre-wrap break-words rounded bg-[color:var(--color-bg)] p-2 text-[11px] leading-snug text-[color:var(--color-text-soft)]">
              {JSON.stringify(args, null, 2)}
            </pre>
          </div>
          {result !== undefined && (
            <div>
              <div className="mb-1 text-[10px] uppercase tracking-wide text-[color:var(--color-text-muted)]">
                Risultato
              </div>
              <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-words rounded bg-[color:var(--color-bg)] p-2 text-[11px] leading-snug text-[color:var(--color-text-soft)]">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {approvalId && (
        <div className="border-t border-[color:var(--color-line)] px-3 py-2">
          <Link
            href="/approvazioni"
            className="inline-flex items-center gap-1 text-[color:var(--color-teal)] hover:underline"
          >
            Apri approvazione <ArrowUpRight size={12} />
          </Link>
        </div>
      )}
    </div>
  );
}
