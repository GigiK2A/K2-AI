import { requireUser } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import type { Contact, Lead } from "@/types/lead";
import type { Approval } from "@/types/approval";
import { ApprovalsList } from "@/components/approvazioni/approvals-list";

export const dynamic = "force-dynamic";

export default async function ApprovazioniPage() {
  await requireUser();

  const [approvals, leads, contacts] = await Promise.all([
    apiFetch<Approval[]>("/api/approvals/?limit=500"),
    apiFetch<Lead[]>("/api/leads/?limit=500"),
    apiFetch<Contact[]>("/api/contacts/?limit=500"),
  ]);

  return (
    <div className="flex flex-col gap-5 p-4 md:p-6 lg:p-8">
      <header className="flex flex-col gap-1">
        <h1 className="font-display text-2xl md:text-3xl">Approvazioni</h1>
        <p className="text-sm text-[color:var(--color-text-soft)]">
          Le bozze preparate da Giuseppina. Approva, modifica o rifiuta.
        </p>
      </header>

      <ApprovalsList
        initialApprovals={approvals}
        leads={leads}
        contacts={contacts}
      />
    </div>
  );
}
