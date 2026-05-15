import { requireUser } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import type { RevenueEvent } from "@/types/revenue";
import { RevenueOverview } from "@/components/revenue/revenue-overview";

export const dynamic = "force-dynamic";

export default async function RevenuePage() {
  await requireUser();

  const events = await apiFetch<RevenueEvent[]>("/api/revenue/?limit=500");

  return (
    <div className="flex flex-col gap-5 p-4 md:p-6 lg:p-8">
      <header className="flex flex-col gap-1">
        <h1 className="font-display text-2xl md:text-3xl">Revenue</h1>
        <p className="text-sm text-[color:var(--color-text-soft)]">
          Quanto entra, da chi, quando. Dati Stripe consolidati.
        </p>
      </header>

      <RevenueOverview events={events} />
    </div>
  );
}
