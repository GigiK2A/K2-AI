import { KpiCard } from "@/components/dashboard/kpi-card";
import type { PostHogKbotKpis } from "@/types/posthog";
import { formatNumber } from "@/lib/format";

interface Props {
  kpis: PostHogKbotKpis;
}

export function KbotKpis({ kpis }: Props) {
  const conversion =
    kpis.kbot_report_requested > 0
      ? Math.round(
          (kpis.kbot_report_generated / kpis.kbot_report_requested) * 100,
        )
      : 0;
  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
      <KpiCard
        label="Aperture K-BOT"
        value={formatNumber(kpis.kbot_open)}
        accent="teal"
      />
      <KpiCard
        label="Messaggi inviati"
        value={formatNumber(kpis.kbot_message_sent)}
      />
      <KpiCard
        label="Report richiesti"
        value={formatNumber(kpis.kbot_report_requested)}
      />
      <KpiCard
        label="Report generati"
        value={formatNumber(kpis.kbot_report_generated)}
        sublabel={`Conversione ${conversion}%`}
        accent={conversion >= 50 ? "teal" : "default"}
      />
    </div>
  );
}
