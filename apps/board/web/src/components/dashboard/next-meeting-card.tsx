import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CalendarClock, Video } from "lucide-react";
import type { NextMeeting } from "@/types/overview";
import { formatRelativeDay, formatTime } from "@/lib/format";

export function NextMeetingCard({ meeting }: { meeting: NextMeeting }) {
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
        <CalendarClock className="h-3.5 w-3.5" />
        Prossimo meeting
      </div>
      <div>
        <h3 className="text-base font-semibold text-[color:var(--color-text)]">
          {meeting.title}
        </h3>
        <p className="mt-1 text-sm text-[color:var(--color-text-soft)]">
          {formatRelativeDay(meeting.starts_at)} ·{" "}
          <span className="tabular-nums">{formatTime(meeting.starts_at)}</span>
        </p>
      </div>
      {meeting.meet_link && (
        <Button asChild size="sm" variant="outline" className="w-fit">
          <a href={meeting.meet_link} target="_blank" rel="noreferrer">
            <Video className="h-4 w-4" />
            Apri Meet
          </a>
        </Button>
      )}
    </Card>
  );
}
