import type { PostHogRecentEvent } from "@/types/posthog";
import { formatRelativeDayTime } from "@/lib/format";

interface Props {
  events: PostHogRecentEvent[];
}

const EVENT_LABELS: Record<string, string> = {
  kbot_open: "Apertura K-BOT",
  kbot_message_sent: "Messaggio inviato",
  kbot_report_requested: "Report richiesto",
  kbot_report_generated: "Report generato",
  profile_click: "Click profilo",
};

function eventLabel(name: string): string {
  return EVENT_LABELS[name] || name;
}

export function EventsTable({ events }: Props) {
  if (events.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] p-6 text-center text-sm text-[color:var(--color-text-muted)]">
        Nessun evento recente.
      </div>
    );
  }
  return (
    <div className="overflow-hidden rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)]">
      <div className="hidden grid-cols-[1.2fr_1.5fr_2fr] gap-3 border-b border-[color:var(--color-line)] px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-[color:var(--color-text-muted)] md:grid">
        <span>Timestamp</span>
        <span>Evento</span>
        <span>Distinct ID</span>
      </div>
      <ul className="divide-y divide-[color:var(--color-line)]">
        {events.map((e, i) => (
          <li
            key={`${e.timestamp}-${i}`}
            className="grid grid-cols-1 gap-1 px-4 py-3 text-sm md:grid-cols-[1.2fr_1.5fr_2fr] md:gap-3"
          >
            <span className="text-[color:var(--color-text-soft)]">
              {formatRelativeDayTime(e.timestamp)}
            </span>
            <span className="text-[color:var(--color-text)]">{eventLabel(e.event)}</span>
            <span className="truncate font-mono text-[11px] text-[color:var(--color-text-muted)]">
              {e.distinct_id}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
