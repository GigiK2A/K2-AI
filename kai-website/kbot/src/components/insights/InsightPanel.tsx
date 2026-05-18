"use client";

import { Activity, Check } from "lucide-react";
import { useEffect, useState } from "react";
import { SkillSummary } from "@/types/chat";
import { ReportCard } from "@/components/report/ReportCard";
import { listSkills, type AvailableSkill } from "@/lib/api";

export function InsightPanel({
  usedSkills,
}: {
  mode: "lead" | "report";
  usedSkills: string[];
  /** Legacy props kept for backwards compatibility with existing callsites. */
  forcedSkills?: string[];
  onToggleForcedSkill?: (name: string) => void;
  availableSkills?: SkillSummary[];
  onLeadSave?: (email: string) => Promise<void>;
}) {
  const [skills, setSkills] = useState<AvailableSkill[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await listSkills();
        if (!cancelled) setSkills(list);
      } catch {
        /* silent — non-critical */
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const usedSet = new Set(usedSkills);

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

        <div className="rounded-xl border border-[var(--line)] p-3">
          <p className="mb-2 text-xs uppercase tracking-wider text-[var(--text-muted)]">
            Skill registry ({skills.length})
          </p>
          <p className="mb-2 text-[11px] text-[var(--text-muted)]">
            L&apos;agente sceglie autonomamente quali attivare in base alla richiesta.
          </p>
          <div className="scroll-premium max-h-[260px] space-y-1 overflow-y-auto pr-1">
            {loading && (
              <p className="text-xs text-[var(--text-muted)]">Caricamento…</p>
            )}
            {!loading && skills.length === 0 && (
              <p className="text-xs text-[var(--text-muted)]">Nessuna skill.</p>
            )}
            {skills.map((s) => {
              const isUsed = usedSet.has(s.name);
              return (
                <div
                  key={s.name}
                  title={s.description || s.name}
                  className={`flex w-full items-center justify-between gap-2 rounded-md border px-2 py-1 text-left text-xs ${
                    isUsed
                      ? "border-[var(--teal)] bg-[var(--teal-soft)] text-[var(--text-main)]"
                      : "border-[var(--line)] text-[var(--text-soft)]"
                  }`}
                >
                  <span className="truncate">{s.name}</span>
                  {isUsed && <Check size={12} className="shrink-0 text-[var(--teal)]" />}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </aside>
  );
}
