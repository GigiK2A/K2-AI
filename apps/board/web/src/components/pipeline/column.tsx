"use client";

import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import type { Contact, Lead, LeadStatus } from "@/types/lead";
import { LEAD_STATUS_COLORS, LEAD_STATUS_LABELS } from "@/lib/leads";
import { LeadCard } from "./lead-card";

interface Props {
  status: LeadStatus;
  leads: Lead[];
  contactsById: Map<string, Contact>;
  onOpenLead: (lead: Lead) => void;
  syncingIds: Set<string>;
}

export function Column({ status, leads, contactsById, onOpenLead, syncingIds }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id: status, data: { status } });

  return (
    <div
      ref={setNodeRef}
      className={
        "flex min-w-[260px] flex-1 flex-col rounded-2xl border bg-[color:var(--color-bg-soft)] transition-colors " +
        (isOver
          ? "border-[color:var(--color-teal)]/60"
          : "border-[color:var(--color-line)]")
      }
    >
      <div className="flex items-center justify-between gap-2 border-b border-[color:var(--color-line)] px-4 py-3">
        <div className="flex items-center gap-2">
          <span className={"h-2 w-2 rounded-full " + LEAD_STATUS_COLORS[status]} />
          <h2 className="text-sm font-semibold">{LEAD_STATUS_LABELS[status]}</h2>
        </div>
        <span className="rounded-full bg-[color:var(--color-bg-elevated)] px-2 py-0.5 text-[11px] font-medium text-[color:var(--color-text-soft)]">
          {leads.length}
        </span>
      </div>

      <SortableContext
        items={leads.map((l) => l.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="flex flex-1 flex-col gap-2 p-3">
          {leads.length === 0 && (
            <div className="rounded-lg border border-dashed border-[color:var(--color-line)] p-4 text-center text-xs text-[color:var(--color-text-muted)]">
              Nessuno
            </div>
          )}
          {leads.map((lead) => (
            <LeadCard
              key={lead.id}
              lead={lead}
              contact={lead.contact_id ? contactsById.get(lead.contact_id) ?? null : null}
              onOpen={onOpenLead}
              syncing={syncingIds.has(lead.id)}
            />
          ))}
        </div>
      </SortableContext>
    </div>
  );
}
