"use client";

import { useEffect, useState } from "react";
import { useKbotAuth } from "@/app/providers";
import { getCompanyProfile, saveCompanyProfile, type CompanyProfile } from "@/lib/api";

const FIELDS: { key: keyof CompanyProfile; label: string; placeholder: string }[] = [
  { key: "ragione_sociale", label: "Ragione sociale", placeholder: "Es. Rossi Impianti Srl" },
  { key: "partita_iva", label: "Partita IVA", placeholder: "Es. 03655920548" },
  { key: "codice_ateco", label: "Codice ATECO", placeholder: "Es. 43.21.01" },
  { key: "forma_giuridica", label: "Forma giuridica", placeholder: "Es. Srl, SpA, ditta individuale" },
  { key: "settore", label: "Settore", placeholder: "Es. impianti elettrici" },
  { key: "dipendenti", label: "Dipendenti", placeholder: "Es. 12" },
  { key: "fatturato", label: "Fatturato annuo", placeholder: "Es. 1.200.000 €" },
  { key: "citta", label: "Città / sede", placeholder: "Es. Perugia" },
];

type Props = {
  /** compact: layout ridotto per lo step post-signup */
  compact?: boolean;
  onSaved?: (p: CompanyProfile) => void;
  /** testo del bottone secondario (es. "Salta") */
  secondaryLabel?: string;
  onSecondary?: () => void;
};

export default function CompanyProfileForm({ compact, onSaved, secondaryLabel, onSecondary }: Props) {
  const { getToken, isSignedIn } = useKbotAuth();
  const [values, setValues] = useState<CompanyProfile>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<"idle" | "saved" | "error">("idle");

  useEffect(() => {
    if (!isSignedIn) return;          // niente setState sincrono: il render guarda isSignedIn
    let mounted = true;
    (async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const p = await getCompanyProfile(token);
        if (mounted) setValues(p);
      } catch {
        /* fail-open: form vuoto */
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [getToken, isSignedIn]);

  const set = (k: keyof CompanyProfile, v: string) => {
    setValues((prev) => ({ ...prev, [k]: v }));
    setStatus("idle");
  };

  const handleSave = async () => {
    setSaving(true);
    setStatus("idle");
    try {
      const token = await getToken();
      if (!token) throw new Error("no token");
      const saved = await saveCompanyProfile(values, token);
      setValues(saved);
      setStatus("saved");
      onSaved?.(saved);
    } catch {
      setStatus("error");
    } finally {
      setSaving(false);
    }
  };

  if (loading && isSignedIn) {
    return <div className="text-sm text-[#6b7280]">Caricamento dati azienda…</div>;
  }

  return (
    <div>
      {!compact && (
        <p className="mb-4 text-sm text-[#9ca3af]">
          Inseriscili una volta: verranno usati in ogni consulenza, senza doverli
          riscrivere in ogni chat. Puoi lasciarne alcuni vuoti e completarli dopo.
        </p>
      )}
      <div className={`grid gap-3 ${compact ? "grid-cols-1" : "grid-cols-1 sm:grid-cols-2"}`}>
        {FIELDS.map((f) => (
          <label key={f.key} className="flex flex-col gap-1 text-sm">
            <span className="text-[#9ca3af]">{f.label}</span>
            <input
              type="text"
              value={values[f.key] ?? ""}
              placeholder={f.placeholder}
              onChange={(e) => set(f.key, e.target.value)}
              className="rounded-lg border border-[#1f2937] bg-[#0a0a0a] px-3 py-2 text-white outline-none focus:border-[var(--teal)]"
            />
          </label>
        ))}
      </div>

      <div className="mt-5 flex items-center gap-3">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="rounded-lg bg-[var(--teal)] px-4 py-2 text-sm font-semibold text-black disabled:opacity-60"
        >
          {saving ? "Salvataggio…" : "Salva dati azienda"}
        </button>
        {secondaryLabel && (
          <button
            type="button"
            onClick={onSecondary}
            className="rounded-lg border border-[#1f2937] px-4 py-2 text-sm text-[#9ca3af] hover:text-white"
          >
            {secondaryLabel}
          </button>
        )}
        {status === "saved" && <span className="text-sm text-[var(--teal)]">Salvato ✓</span>}
        {status === "error" && (
          <span className="text-sm text-red-400">Errore nel salvataggio, riprova.</span>
        )}
      </div>
    </div>
  );
}
