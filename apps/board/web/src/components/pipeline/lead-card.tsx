"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Calendar, Building2 } from "lucide-react";
import type { Contact, Lead } from "@/types/lead";
import { formatLeadValue, formatProbability } from "@/lib/leads";
import { formatRelativeDay } from "@/lib/format";

interface Props {
  lead: Lead;
  contact: Contact | null;
  onOpen: (lead: Lead) => void;
  syncing?: boolean;
}

export function LeadCard({ lead, contact, onOpen, syncing }: Props) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: lead.id, data: { status: lead.status } });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const contactLabel = contact?.company || contact?.person_name || null;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={
        "group relative flex gap-2 rounded-xl border border-[color:var(--color-line)] bg-[color:var(--color-bg-elevated)] p-3 text-left transition-shadow hover:border-[color:var(--color-line-strong)] hover:shadow-lg " +
        (isDragging ? "opacity-50" : "")
      }
    >
      <button
        type="button"
        {...attributes}
        {...listeners}
        aria-label="Trascina"
        className="flex cursor-grab items-start pt-1 text-[color:var(--color-text-muted)] opacity-40 transition-opacity group-hover:opacity-100 active:cursor-grabbing"
      >
        <GripVertical className="h-4 w-4" />
      </button>

      <button
        type="button"
        onClick={() => onOpen(lead)}
        className="flex flex-1 flex-col gap-2 text-left"
      >
        <div className="flex items-start justify-between gap-2">
          <h3 className="line-clamp-2 text-sm font-medium leading-snug">
            {lead.title}
          </h3>
          {syncing && (
            <span className="mt-0.5 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-[color:var(--color-teal)]" />
          )}
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="font-medium text-[color:var(--color-text)]">
            {formatLeadValue(lead)}
          </span>
          <span className="rounded-full border border-[color:var(--color-line-strong)] px-2 py-0.5 text-[10px] text-[color:var(--color-text-soft)]">
            {formatProbability(lead.probability)}
          </span>
        </div>

        {contactLabel && (
          <div className="flex items-center gap-1 text-[11px] text-[color:var(--color-text-muted)]">
            <Building2 className="h-3 w-3" />
            <span className="truncate">{contactLabel}</span>
          </div>
        )}

        {lead.next_action_at && (
          <div className="flex items-center gap-1 text-[11px] text-[color:var(--color-text-soft)]">
            <Calendar className="h-3 w-3" />
            <span>{formatRelativeDay(lead.next_action_at)}</span>
          </div>
        )}
      </button>
    </div>
  );
}
