"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check, X, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Approval } from "@/types/approval";
import type { Lead } from "@/types/lead";
import {
  APPROVAL_KIND_COLORS,
  APPROVAL_KIND_LABELS,
  APPROVAL_STATUS_LABELS,
  formatRelativeTime,
} from "@/lib/approvals";

interface Props {
  approval: Approval;
  lead: Lead | null;
  selectable: boolean;
  selected: boolean;
  onToggleSelect: (id: string) => void;
  onOpen: (a: Approval) => void;
  onApprove: (a: Approval) => void;
  onReject: (a: Approval) => void;
  busy: boolean;
}

function truncateBody(body: string, lines = 5): string {
  const arr = body.split("\n").filter((l) => l.trim() !== "");
  return arr.slice(0, lines).join("\n");
}

export function ApprovalCard({
  approval,
  lead,
  selectable,
  selected,
  onToggleSelect,
  onOpen,
  onApprove,
  onReject,
  busy,
}: Props) {
  const preview = truncateBody(approval.body, 5);
  const isPending = approval.status === "pending";

  return (
    <article
      className={
        "flex flex-col gap-3 rounded-xl border bg-[color:var(--color-bg-soft)] p-4 transition-colors " +
        (selected
          ? "border-[color:var(--color-teal)]"
          : "border-[color:var(--color-line)] hover:border-[color:var(--color-line-strong)]")
      }
    >
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex flex-1 items-start gap-2">
          {selectable && isPending && (
            <input
              type="checkbox"
              checked={selected}
              onChange={() => onToggleSelect(approval.id)}
              aria-label="Seleziona"
              className="mt-1.5 h-4 w-4 cursor-pointer accent-[color:var(--color-teal)]"
            />
          )}
          <div className="flex flex-1 flex-col gap-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={
                  "rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider " +
                  APPROVAL_KIND_COLORS[approval.kind]
                }
              >
                {APPROVAL_KIND_LABELS[approval.kind]}
              </span>
              {!isPending && (
                <span className="rounded-md border border-[color:var(--color-line-strong)] px-2 py-0.5 text-[11px] text-[color:var(--color-text-soft)]">
                  {APPROVAL_STATUS_LABELS[approval.status]}
                </span>
              )}
              <span className="text-[11px] text-[color:var(--color-text-muted)]">
                {formatRelativeTime(approval.created_at)}
              </span>
            </div>
            <h3 className="font-display text-lg leading-snug">{approval.title}</h3>
            {lead && (
              <p className="text-xs text-[color:var(--color-text-soft)]">
                Lead: <span className="text-[color:var(--color-text)]">{lead.title}</span>
              </p>
            )}
          </div>
        </div>
      </header>

      <button
        type="button"
        onClick={() => onOpen(approval)}
        className="cursor-pointer rounded-lg border border-transparent bg-[color:var(--color-bg)]/40 p-3 text-left text-sm text-[color:var(--color-text-soft)] hover:border-[color:var(--color-line)] hover:text-[color:var(--color-text)]"
        aria-label="Apri bozza"
      >
        <div className="prose-approval line-clamp-5 whitespace-pre-wrap text-sm">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {preview || "_(corpo vuoto)_"}
          </ReactMarkdown>
        </div>
        {approval.body.split("\n").filter((l) => l.trim()).length > 5 && (
          <span className="mt-2 inline-block text-[11px] text-[color:var(--color-teal)]">
            Apri per leggere tutto →
          </span>
        )}
      </button>

      {approval.rationale && (
        <p className="rounded-lg border border-[color:var(--color-line)] bg-[color:var(--color-bg)]/40 px-3 py-2 text-xs italic text-[color:var(--color-text-muted)]">
          AI dice: {approval.rationale}
        </p>
      )}

      {isPending && (
        <footer className="flex flex-wrap items-center justify-end gap-2">
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => onOpen(approval)}
            disabled={busy}
          >
            <Pencil className="h-4 w-4" />
            Modifica
          </Button>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={() => onReject(approval)}
            disabled={busy}
          >
            <X className="h-4 w-4" />
            Rifiuta
          </Button>
          <Button
            type="button"
            size="sm"
            onClick={() => onApprove(approval)}
            disabled={busy}
          >
            <Check className="h-4 w-4" />
            Approva
          </Button>
        </footer>
      )}

      {!isPending && approval.decision_note && (
        <p className="text-xs text-[color:var(--color-text-muted)]">
          Nota: {approval.decision_note}
        </p>
      )}
    </article>
  );
}
