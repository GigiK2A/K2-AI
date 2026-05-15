import { requireUser } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import type { Memo } from "@/types/memo";
import type { Contact, Lead } from "@/types/lead";
import { MemosGrid } from "@/components/memos/memos-grid";

export const dynamic = "force-dynamic";

export default async function MemosPage() {
  await requireUser();

  const [memos, leads, contacts] = await Promise.all([
    apiFetch<Memo[]>("/api/memos/?limit=500"),
    apiFetch<Lead[]>("/api/leads/?limit=500"),
    apiFetch<Contact[]>("/api/contacts/?limit=500"),
  ]);

  return (
    <div className="flex flex-col gap-5 p-4 md:p-6 lg:p-8">
      <header className="flex flex-col gap-1">
        <h1 className="font-display text-2xl md:text-3xl">Memos</h1>
        <p className="text-sm text-[color:var(--color-text-soft)]">
          Appunti, contesto e pensieri. Cerca per parola o filtra per tag.
        </p>
      </header>

      <MemosGrid initialMemos={memos} leads={leads} contacts={contacts} />
    </div>
  );
}
