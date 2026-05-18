"use client";

import { Activity, Check, Plus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { SkillSummary } from "@/types/chat";
import { ReportCard } from "@/components/report/ReportCard";
import { listSkills, type AvailableSkill } from "@/lib/api";

export function InsightPanel({
  usedSkills,
  forcedSkills = [],
  onToggleForcedSkill,
}: {
  mode: "lead" | "report";
  usedSkills: string[];
  /** Skills the user has manually pinned for this session. */
  forcedSkills?: string[];
  onToggleForcedSkill?: (name: string) => void;
  /** Legacy props kept for backwards compatibility with existing callsites. */
  availableSkills?: SkillSummary[];
  onLeadSave?: (email: string) => Promise<void>;
}) {
  const [skills, setSkills] = useState<AvailableSkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

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

  const usedSet = useMemo(() => new Set(usedSkills), [usedSkills]);
  const forcedSet = useMemo(() => new Set(forcedSkills), [forcedSkills]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const base = skills.filter((s) => !usedSet.has(s.name));
    if (!q) return base.slice(0, 30);
    return base
      .filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          (s.description || "").toLowerCase().includes(q),
      )
      .slice(0, 30);
  }, [skills, usedSet, query]);

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
            Skill disponibili
          </p>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Cerca skill…"
            className="mb-2 w-full rounded-md border border-[var(--line)] bg-[var(--bg-1)] px-2 py-1 text-xs outline-none focus:border-[var(--teal)]"
          />
          <div className="scroll-premium max-h-[260px] space-y-1 overflow-y-auto pr-1">
            {loading && (
              <p className="text-xs text-[var(--text-muted)]">Caricamento…</p>
            )}
            {!loading && filtered.length === 0 && (
              <p className="text-xs text-[var(--text-muted)]">Nessuna skill.</p>
            )}
            {filtered.map((s) => {
              const isForced = forcedSet.has(s.name);
              return (
                <button
                  key={s.name}
                  type="button"
                  onClick={() => onToggleForcedSkill?.(s.name)}
                  title={s.description || s.name}
                  className={`flex w-full items-center justify-between gap-2 rounded-md border px-2 py-1 text-left text-xs transition ${
                    isForced
                      ? "border-[var(--teal)] bg-[var(--teal-soft)] text-[var(--text-main)]"
                      : "border-[var(--line)] text-[var(--text-soft)] hover:border-[var(--line-strong)]"
                  }`}
                >
                  <span className="truncate">+ {s.name}</span>
                  {isForced ? (
                    <Check size={12} className="shrink-0 text-[var(--teal)]" />
                  ) : (
                    <Plus size={12} className="shrink-0 opacity-60" />
                  )}
                </button>
              );
            })}
          </div>
          {forcedSkills.length > 0 && (
            <p className="mt-2 text-[10px] text-[var(--text-muted)]">
              {forcedSkills.length} skill forzate per la sessione
            </p>
          )}
        </div>
      </div>
    </aside>
  );
}
