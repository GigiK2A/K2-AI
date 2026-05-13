import { Lock, Sparkles } from "lucide-react";

export function PremiumLock({ paymentLink }: { paymentLink: string | null }) {
  return (
    <div className="k2-panel rounded-2xl border-[var(--line-strong)] p-6">
      <div className="mb-5 inline-flex rounded-full border border-[var(--line)] p-3 text-[var(--teal)]">
        <Lock size={18} />
      </div>
      <h3 className="text-xl font-semibold">Report Premium bloccato</h3>
      <p className="mt-2 text-sm text-[var(--text-soft)]">Sblocca analisi strategiche, KPI, timeline operativa e insight verticali.</p>
      <ul className="mt-4 space-y-2 text-sm text-[var(--text-soft)]">
        <li className="flex items-center gap-2"><Sparkles size={14} /> Executive summary professionale</li>
        <li className="flex items-center gap-2"><Sparkles size={14} /> Roadmap e priorita operative</li>
        <li className="flex items-center gap-2"><Sparkles size={14} /> KPI e modello di monitoraggio</li>
      </ul>
      {paymentLink && (
        <a className="mt-6 inline-flex rounded-xl bg-[var(--teal)] px-4 py-2 text-sm font-semibold text-black" href={paymentLink} target="_blank" rel="noreferrer">
          Accedi e paga
        </a>
      )}
    </div>
  );
}
