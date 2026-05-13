import { Activity } from "lucide-react";
import { SkillSummary } from "@/types/chat";
import { ReportCard } from "@/components/report/ReportCard";

export function InsightPanel({
  usedSkills,
  availableSkills,
}: {
  mode: "lead" | "report";
  usedSkills: string[];
  availableSkills: SkillSummary[];
  onLeadSave: (email: string) => Promise<void>;
}) {
  return (
    <aside className="k2-panel hidden w-[320px] border-l p-4 xl:block">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold">Insight Panel</p>
        <Activity size={15} className="text-[var(--teal)]" />
      </div>

      <div className="mt-4 space-y-3">
        <ReportCard title="Modalità" value="Report Premium" />
        <ReportCard
          title="Skill usate"
          value={usedSkills.length ? usedSkills.join(" • ") : "In attesa di elaborazione"}
        />
        <ReportCard
          title="Skill disponibili"
          value={availableSkills.slice(0, 5).map((s) => s.name).join(" • ") || "—"}
        />
      </div>
    </aside>
  );
}
