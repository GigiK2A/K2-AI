"use client";

import { useMemo, useState } from "react";
import {
  DndContext,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import type { Contact, Lead, LeadSource, LeadStatus } from "@/types/lead";
import { LEAD_STATUS_ORDER, isLeadStatus } from "@/lib/leads";
import { apiClient } from "@/lib/api-client";
import { Column } from "./column";
import { PipelineToolbar, type SortKey } from "./pipeline-toolbar";
import { LeadDrawer } from "./lead-drawer";

interface Props {
  initialLeads: Lead[];
  contacts: Contact[];
}

type DrawerState =
  | { mode: "edit"; lead: Lead }
  | { mode: "create" }
  | null;

export function PipelineBoard({ initialLeads, contacts: initialContacts }: Props) {
  const [leads, setLeads] = useState<Lead[]>(initialLeads);
  const [contacts, setContacts] = useState<Contact[]>(initialContacts);
  const [drawer, setDrawer] = useState<DrawerState>(null);
  const [search, setSearch] = useState("");
  const [sources, setSources] = useState<Set<LeadSource>>(new Set());
  const [sort, setSort] = useState<SortKey>("recent");
  const [syncingIds, setSyncingIds] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  const contactsById = useMemo(() => {
    const m = new Map<string, Contact>();
    for (const c of contacts) m.set(c.id, c);
    return m;
  }, [contacts]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return leads.filter((l) => {
      if (sources.size > 0 && !sources.has(l.source)) return false;
      if (q) {
        const contact = l.contact_id ? contactsById.get(l.contact_id) : null;
        const hay = [
          l.title,
          contact?.company ?? "",
          contact?.person_name ?? "",
        ]
          .join(" ")
          .toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [leads, search, sources, contactsById]);

  const grouped = useMemo(() => {
    const groups: Record<LeadStatus, Lead[]> = {
      nuovo: [],
      contatto: [],
      proposta: [],
      chiuso_vinto: [],
      chiuso_perso: [],
    };
    for (const l of filtered) groups[l.status].push(l);
    const sortFn = (a: Lead, b: Lead) => {
      if (sort === "value") return (b.value_eur ?? 0) - (a.value_eur ?? 0);
      if (sort === "next_action") {
        const av = a.next_action_at ? new Date(a.next_action_at).getTime() : Infinity;
        const bv = b.next_action_at ? new Date(b.next_action_at).getTime() : Infinity;
        return av - bv;
      }
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    };
    for (const status of LEAD_STATUS_ORDER) groups[status].sort(sortFn);
    return groups;
  }, [filtered, sort]);

  function toggleSource(src: LeadSource) {
    setSources((prev) => {
      const next = new Set(prev);
      if (next.has(src)) next.delete(src);
      else next.add(src);
      return next;
    });
  }

  async function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over) return;
    const leadId = String(active.id);
    const overData = over.data.current as { status?: LeadStatus } | undefined;
    const activeData = active.data.current as { status?: LeadStatus } | undefined;
    // overId can be a column id (status) or another lead id; resolve target status
    let targetStatus: LeadStatus | null = null;
    if (overData?.status) targetStatus = overData.status;
    else if (typeof over.id === "string" && isLeadStatus(over.id)) {
      targetStatus = over.id;
    } else {
      const overLead = leads.find((l) => l.id === over.id);
      targetStatus = overLead?.status ?? null;
    }
    if (!targetStatus) return;
    const fromStatus = activeData?.status;
    if (fromStatus === targetStatus) return; // same-column reorder is purely visual

    const prevLeads = leads;
    setLeads((curr) =>
      curr.map((l) => (l.id === leadId ? { ...l, status: targetStatus! } : l))
    );
    setSyncingIds((s) => new Set(s).add(leadId));
    try {
      const updated = await apiClient<Lead>(`/api/leads/${leadId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: targetStatus }),
      });
      setLeads((curr) => curr.map((l) => (l.id === leadId ? updated : l)));
    } catch (err) {
      setLeads(prevLeads);
      setError(err instanceof Error ? err.message : "Errore aggiornamento stato");
    } finally {
      setSyncingIds((s) => {
        const next = new Set(s);
        next.delete(leadId);
        return next;
      });
    }
  }

  function handleSaved(lead: Lead) {
    setLeads((curr) => {
      const idx = curr.findIndex((l) => l.id === lead.id);
      if (idx === -1) return [lead, ...curr];
      const next = [...curr];
      next[idx] = lead;
      return next;
    });
  }

  function handleDeleted(id: string) {
    setLeads((curr) => curr.filter((l) => l.id !== id));
  }

  function handleContactCreated(c: Contact) {
    setContacts((curr) => [c, ...curr]);
  }

  return (
    <div className="flex flex-col gap-4">
      <PipelineToolbar
        search={search}
        onSearch={setSearch}
        sources={sources}
        onToggleSource={toggleSource}
        sort={sort}
        onSort={setSort}
        onNewLead={() => setDrawer({ mode: "create" })}
      />

      {error && (
        <div className="flex items-center justify-between rounded-lg border border-[color:var(--color-danger)]/50 bg-[color:var(--color-danger)]/10 px-3 py-2 text-xs text-[color:var(--color-danger)]">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="underline">
            Chiudi
          </button>
        </div>
      )}

      <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
        <div className="flex snap-x snap-mandatory gap-3 overflow-x-auto pb-4 lg:snap-none lg:overflow-visible">
          {LEAD_STATUS_ORDER.map((status) => (
            <div key={status} className="flex w-[80vw] snap-start lg:w-auto lg:flex-1">
              <Column
                status={status}
                leads={grouped[status]}
                contactsById={contactsById}
                onOpenLead={(lead) => setDrawer({ mode: "edit", lead })}
                syncingIds={syncingIds}
              />
            </div>
          ))}
        </div>
      </DndContext>

      {drawer?.mode === "edit" && (
        <LeadDrawer
          mode="edit"
          open
          lead={drawer.lead}
          contacts={contacts}
          onClose={() => setDrawer(null)}
          onSaved={handleSaved}
          onDeleted={handleDeleted}
          onContactCreated={handleContactCreated}
        />
      )}
      {drawer?.mode === "create" && (
        <LeadDrawer
          mode="create"
          open
          contacts={contacts}
          onClose={() => setDrawer(null)}
          onSaved={handleSaved}
          onContactCreated={handleContactCreated}
        />
      )}
    </div>
  );
}
