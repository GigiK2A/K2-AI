import { requireUser } from "@/lib/auth";
import { fetchKbotAnalytics } from "@/lib/posthog";
import { KbotAnalyticsView } from "@/components/kbot/kbot-analytics";

export const dynamic = "force-dynamic";

export default async function KBOTPage() {
  await requireUser();

  const data = await fetchKbotAnalytics();

  return (
    <div className="flex flex-col gap-5 p-4 md:p-6 lg:p-8">
      <header className="flex flex-col gap-1">
        <h1 className="font-display text-2xl md:text-3xl">K-BOT analytics</h1>
        <p className="text-sm text-[color:var(--color-text-soft)]">
          Aperture, conversazioni e conversioni K-BOT — ultimi 30 giorni.
        </p>
      </header>

      <KbotAnalyticsView data={data} />
    </div>
  );
}
