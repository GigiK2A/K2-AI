import { requireUser } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import type { Contact, Lead } from "@/types/lead";
import { PipelineBoard } from "@/components/pipeline/pipeline-board";

export const dynamic = "force-dynamic";

export default async function PipelinePage() {
  await requireUser();

  const [leads, contacts] = await Promise.all([
    apiFetch<Lead[]>("/api/leads/?limit=500"),
    apiFetch<Contact[]>("/api/contacts/?limit=500"),
  ]);

  return (
    <div className="flex flex-col gap-5 p-4 md:p-6 lg:p-8">
      <header className="flex flex-col gap-1">
        <h1 className="font-display text-2xl md:text-3xl">Pipeline</h1>
        <p className="text-sm text-[color:var(--color-text-soft)]">
          Trascina le card per cambiare stato. Tocca una card per modificarla.
        </p>
      </header>

      <PipelineBoard initialLeads={leads} contacts={contacts} />
    </div>
  );
}
