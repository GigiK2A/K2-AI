import { requireUser } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import type { Meeting } from "@/types/meeting";
import type { Contact, Lead } from "@/types/lead";
import { CalendarView } from "@/components/calendario/calendar-view";

export const dynamic = "force-dynamic";

export default async function CalendarioPage() {
  await requireUser();

  const [meetings, leads, contacts] = await Promise.all([
    apiFetch<Meeting[]>("/api/meetings/?limit=500"),
    apiFetch<Lead[]>("/api/leads/?limit=500"),
    apiFetch<Contact[]>("/api/contacts/?limit=500"),
  ]);

  return (
    <div className="flex flex-col gap-5 p-4 md:p-6 lg:p-8">
      <header className="flex flex-col gap-1">
        <h1 className="font-display text-2xl md:text-3xl">Calendario</h1>
        <p className="text-sm text-[color:var(--color-text-soft)]">
          Meeting in agenda. Vista lista o settimana.
        </p>
      </header>

      <CalendarView
        initialMeetings={meetings}
        leads={leads}
        contacts={contacts}
      />
    </div>
  );
}
