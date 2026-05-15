import type { KbotAnalytics } from "@/types/posthog";
import { KbotKpis } from "./kbot-kpis";
import { ProfileClicksChart } from "./profile-clicks-chart";
import { EventsTable } from "./events-table";

interface Props {
  data: KbotAnalytics;
}

export function KbotAnalyticsView({ data }: Props) {
  if (!data.configured) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-xl border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] px-6 py-10 text-center">
        <p className="font-display text-lg">Analytics non configurati.</p>
        <p className="max-w-md text-sm text-[color:var(--color-text-soft)]">
          Configura <code className="font-mono text-[color:var(--color-teal)]">POSTHOG_PERSONAL_API_KEY</code>{" "}
          nelle env del frontend per vedere analytics K-BOT.
        </p>
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-4">
      {data.error && (
        <div className="rounded-lg border border-[color:var(--color-danger)]/50 bg-[color:var(--color-danger)]/10 px-3 py-2 text-xs text-[color:var(--color-danger)]">
          {data.error}
        </div>
      )}
      <KbotKpis kpis={data.kpis} />
      <ProfileClicksChart clicks={data.profile_clicks} />
      <div className="flex flex-col gap-2">
        <h2 className="font-display text-base">Eventi recenti</h2>
        <EventsTable events={data.recent_events} />
      </div>
    </div>
  );
}
