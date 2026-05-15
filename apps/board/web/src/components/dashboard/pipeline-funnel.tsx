import type { LeadStatus } from "@/types/overview";
import { formatNumber } from "@/lib/format";

const ORDER: { key: LeadStatus; label: string }[] = [
  { key: "nuovo", label: "Nuovo" },
  { key: "contatto", label: "Contatto" },
  { key: "proposta", label: "Proposta" },
  { key: "chiuso_vinto", label: "Vinto" },
  { key: "chiuso_perso", label: "Perso" },
];

const accent: Record<LeadStatus, string> = {
  nuovo: "bg-[color:var(--color-text-soft)]/40",
  contatto: "bg-[color:var(--color-teal)]/60",
  proposta: "bg-[color:var(--color-teal)]",
  chiuso_vinto: "bg-[color:var(--color-success)]",
  chiuso_perso: "bg-[color:var(--color-danger)]/60",
};

export function PipelineFunnel({
  byStatus,
}: {
  byStatus: Partial<Record<LeadStatus, number>>;
}) {
  const max = Math.max(1, ...ORDER.map((s) => byStatus[s.key] ?? 0));
  return (
    <div className="grid grid-cols-5 gap-2">
      {ORDER.map(({ key, label }) => {
        const count = byStatus[key] ?? 0;
        const height = Math.max(8, Math.round((count / max) * 100));
        return (
          <div key={key} className="flex flex-col items-center gap-2">
            <div className="flex h-24 w-full items-end">
              <div
                className={`w-full rounded-md ${accent[key]} transition-all`}
                style={{ height: `${height}%` }}
              />
            </div>
            <div className="text-center">
              <div className="font-display text-lg leading-none">
                {formatNumber(count)}
              </div>
              <div className="mt-1 text-[10px] uppercase tracking-wider text-[color:var(--color-text-muted)]">
                {label}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
