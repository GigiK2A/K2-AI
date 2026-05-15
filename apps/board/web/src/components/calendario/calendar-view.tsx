"use client";

import { useState } from "react";
import type { Meeting } from "@/types/meeting";
import type { Contact, Lead } from "@/types/lead";
import { CalendarList } from "./calendar-list";
import { CalendarWeek } from "./calendar-week";
import { MeetingDrawer } from "./meeting-drawer";

interface Props {
  initialMeetings: Meeting[];
  leads: Lead[];
  contacts: Contact[];
}

type DrawerState =
  | { mode: "edit"; meeting: Meeting }
  | { mode: "create" }
  | null;

type ViewKey = "lista" | "settimana";

export function CalendarView({ initialMeetings, leads, contacts }: Props) {
  const [meetings, setMeetings] = useState<Meeting[]>(initialMeetings);
  const [view, setView] = useState<ViewKey>("lista");
  const [drawer, setDrawer] = useState<DrawerState>(null);
  const [syncNotice, setSyncNotice] = useState(false);

  function handleSaved(m: Meeting) {
    setMeetings((curr) => {
      const idx = curr.findIndex((x) => x.id === m.id);
      if (idx === -1) return [m, ...curr];
      const next = [...curr];
      next[idx] = m;
      return next;
    });
  }

  function handleDeleted(id: string) {
    setMeetings((curr) => curr.filter((m) => m.id !== id));
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="inline-flex rounded-lg border border-[color:var(--color-line-strong)] p-0.5">
          {(["lista", "settimana"] as ViewKey[]).map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => setView(v)}
              className={
                "rounded-md px-3 py-1.5 text-xs font-medium transition-colors " +
                (view === v
                  ? "bg-[color:var(--color-teal)] text-black"
                  : "text-[color:var(--color-text-soft)] hover:text-[color:var(--color-text)]")
              }
            >
              {v === "lista" ? "Lista" : "Settimana"}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setSyncNotice(true)}
            disabled
            title="Coming Sprint 7"
            className="inline-flex h-9 items-center gap-1 rounded-lg border border-[color:var(--color-line-strong)] px-3 text-xs font-medium text-[color:var(--color-text-soft)] opacity-60"
          >
            ↻ Sincronizza Google Calendar
          </button>
          <button
            type="button"
            onClick={() => setDrawer({ mode: "create" })}
            className="inline-flex h-9 items-center gap-1 rounded-lg bg-[color:var(--color-teal)] px-3 text-sm font-medium text-black transition-colors hover:bg-[color:var(--color-teal-soft)]"
          >
            + Nuovo meeting
          </button>
        </div>
      </div>

      {syncNotice && (
        <div className="flex items-center justify-between rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-elevated)] px-3 py-2 text-xs text-[color:var(--color-text-soft)]">
          <span>La sincronizzazione Google Calendar arriva con lo Sprint 7.</span>
          <button onClick={() => setSyncNotice(false)} className="underline">
            Ok
          </button>
        </div>
      )}

      {view === "lista" ? (
        <CalendarList
          meetings={meetings}
          onOpen={(m) => setDrawer({ mode: "edit", meeting: m })}
        />
      ) : (
        <CalendarWeek
          meetings={meetings}
          onOpen={(m) => setDrawer({ mode: "edit", meeting: m })}
        />
      )}

      {drawer?.mode === "edit" && (
        <MeetingDrawer
          mode="edit"
          open
          meeting={drawer.meeting}
          leads={leads}
          contacts={contacts}
          onClose={() => setDrawer(null)}
          onSaved={handleSaved}
          onDeleted={handleDeleted}
        />
      )}
      {drawer?.mode === "create" && (
        <MeetingDrawer
          mode="create"
          open
          leads={leads}
          contacts={contacts}
          onClose={() => setDrawer(null)}
          onSaved={handleSaved}
        />
      )}
    </div>
  );
}
