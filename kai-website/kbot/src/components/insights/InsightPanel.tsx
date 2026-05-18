"use client";

import { Activity, Sparkles } from "lucide-react";
import { SkillSummary } from "@/types/chat";
import { ReportCard } from "@/components/report/ReportCard";
import type { AvailableSkill } from "@/lib/api";

export function InsightPanel({
  usedSkills,
}: {
  mode: "lead" | "report";
  usedSkills: string[];
  /** Legacy props kept for backwards compatibility with existing callsites. */
  forcedSkills?: string[];
  onToggleForcedSkill?: (name: string) => void;
  availableSkills?: SkillSummary[] | AvailableSkill[];
  onLeadSave?: (email: string) => Promise<void>;
}) {
  const hasSkills = usedSkills.length > 0;

  return (
    <aside className="k2-panel hidden w-[320px] border-l p-4 xl:block">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold">Insight Panel</p>
        <Activity size={15} className="text-[var(--teal)]" />
      </div>

      <div className="mt-4 space-y-3">
        <ReportCard title="Modalità" value="Report Premium" />

        <div className="rounded-xl border border-[var(--line)] p-3">
          <div className="mb-2 flex items-center gap-1.5">
            <Sparkles size={12} className="text-[var(--teal)]" />
            <p className="text-xs uppercase tracking-wider text-[var(--text-muted)]">
              Skill attive ora
            </p>
            {hasSkills && (
              <span className="ml-auto rounded-full bg-[var(--teal-soft)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--teal)]">
                {usedSkills.length}
              </span>
            )}
          </div>
          {!hasSkills && (
            <p className="text-xs text-[var(--text-muted)]">
              In attesa del primo turno — l&apos;agente seleziona le skill in base alla richiesta.
            </p>
          )}
          {hasSkills && (
            <ul className="space-y-1.5">
              {usedSkills.map((name) => (
                <li
                  key={name}
                  className="flex items-center gap-2 rounded-md border border-[var(--teal)]/40 bg-[var(--teal-soft)] px-2 py-1.5 text-xs text-[var(--text-main)]"
                >
                  <span className="inline-block h-1.5 w-1.5 shrink-0 animate-pulse rounded-full bg-[var(--teal)]" />
                  <span className="truncate">{name}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </aside>
  );
}
