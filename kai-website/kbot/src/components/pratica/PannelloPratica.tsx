"use client";

import { useState } from "react";
import { Copy, Download, FileText, Globe, X } from "lucide-react";
import type { AnalyzedUrl, UploadedFile } from "@/lib/api";

export type SchedaPratica = "bozza" | "documenti" | "fatti" | "fonti";

const SCHEDE: { id: SchedaPratica; label: string }[] = [
  { id: "bozza", label: "Bozza" },
  { id: "documenti", label: "Documenti" },
  { id: "fatti", label: "Fatti" },
  { id: "fonti", label: "Fonti" },
];

/** Un messaggio del consulente che contiene un documento da consegnare (lettera, diffida, comunicazione). */
const BOZZA_RE = /(^|\n)\s*(oggetto\s*:|spett\.?le|egregio|egregi|gentile|raccomandata|a mezzo pec)/i;
export function eBozza(testo: string): boolean {
  return testo.length > 250 && BOZZA_RE.test(testo);
}

/** Le righe «Fonti: A; B.» che il backend aggiunge in coda alle risposte. */
export function estraiFonti(testi: string[]): string[] {
  const out: string[] = [];
  for (const t of testi) {
    const m = /(?:^|\n)Fonti:\s*(.+?)\s*$/m.exec(t);
    if (!m) continue;
    for (const f of m[1].replace(/\.$/, "").split(";")) {
      const v = f.trim();
      if (v && !out.includes(v)) out.push(v);
    }
  }
  return out;
}

function etichettaFatto(chiave: string): string {
  const t = chiave.replace(/_/g, " ");
  return t.charAt(0).toUpperCase() + t.slice(1);
}

export function PannelloPratica({
  scheda,
  onScheda,
  bozza,
  onScaricaWord,
  fatti,
  fonti,
  competenze,
  documenti,
  siti,
  onClose,
  className = "",
}: {
  scheda: SchedaPratica;
  onScheda: (s: SchedaPratica) => void;
  bozza: string | null;
  onScaricaWord?: () => Promise<void>;
  fatti: Record<string, string>;
  fonti: string[];
  competenze: string[];
  documenti: UploadedFile[];
  siti: AnalyzedUrl[];
  /** Su telefono il pannello è una schermata a sé: la freccia/chiudi riporta alla chat. */
  onClose?: () => void;
  className?: string;
}) {
  const [copiato, setCopiato] = useState(false);
  const [errore, setErrore] = useState<string | null>(null);
  const nFatti = Object.keys(fatti).length;
  const conteggi: Record<SchedaPratica, number> = {
    bozza: bozza ? 1 : 0,
    documenti: documenti.length + siti.length,
    fatti: nFatti,
    fonti: fonti.length,
  };

  async function copia() {
    if (!bozza) return;
    try {
      await navigator.clipboard.writeText(bozza);
      setCopiato(true);
      setTimeout(() => setCopiato(false), 1800);
    } catch {
      setErrore("Non riesco a copiare: seleziona il testo e copialo a mano.");
    }
  }

  return (
    <section aria-label="Pratica" className={"flex min-h-0 flex-col bg-[var(--bg-1)] " + className}>
      <div className="flex items-center border-b border-[var(--line)] px-2">
        {onClose && (
          <button onClick={onClose} className="mr-1 rounded-md p-2 text-[var(--text-soft)] lg:hidden" aria-label="Torna alla chat">
            <X size={16} />
          </button>
        )}
        <div role="tablist" className="flex min-w-0 flex-1 overflow-x-auto">
          {SCHEDE.map((s) => (
            <button
              key={s.id}
              role="tab"
              aria-selected={scheda === s.id}
              onClick={() => onScheda(s.id)}
              className={
                "whitespace-nowrap border-b-2 px-3 py-3 text-sm " +
                (scheda === s.id
                  ? "border-[var(--text-main)] font-medium"
                  : "border-transparent text-[var(--text-soft)] hover:text-[var(--text-main)]")
              }
            >
              {s.label}
              {conteggi[s.id] > 0 && (
                <span className="ml-1.5 rounded-full bg-[var(--bg-2)] px-1.5 py-0.5 text-[11px] text-[var(--text-soft)]">
                  {conteggi[s.id]}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="scroll-premium min-h-0 flex-1 overflow-y-auto p-4 text-sm leading-6">
        {scheda === "bozza" &&
          (bozza ? (
            <>
              <div className="mb-3 flex items-center gap-2">
                <p className="flex-1 font-medium">Documento in preparazione</p>
                <span className="rounded-md bg-[var(--warn-bg)] px-2 py-0.5 text-xs text-[var(--warn-text)]">Da verificare</span>
              </div>
              <article className="whitespace-pre-wrap rounded-lg border border-[var(--line)] bg-[var(--bg-1)] p-4 text-[14px] leading-7">
                {bozza}
              </article>
              <p className="mt-3 text-xs text-[var(--text-muted)]">
                Controlla date, importi e nomi prima di inviare. Per modificarla chiedi in chat.
              </p>
            </>
          ) : (
            <Vuoto icona={<FileText size={18} />} titolo="Nessuna bozza, per ora">
              Quando chiedi una lettera, una diffida o una comunicazione, il testo compare qui.
            </Vuoto>
          ))}

        {scheda === "documenti" &&
          (documenti.length + siti.length === 0 ? (
            <Vuoto icona={<FileText size={18} />} titolo="Nessun documento">
              Allega contratti, fatture o visure con la graffetta: K-BOT li legge e li usa nella pratica.
            </Vuoto>
          ) : (
            <ul className="space-y-2">
              {documenti.map((f) => (
                <li key={f.path} className="rounded-lg border border-[var(--line)] p-3">
                  <p className="flex items-center gap-2 font-medium"><FileText size={14} /> <span className="truncate">{f.name}</span></p>
                  {f.extractedSummary && <p className="mt-1 line-clamp-3 text-xs text-[var(--text-soft)]">{f.extractedSummary}</p>}
                </li>
              ))}
              {siti.map((u) => (
                <li key={u.url} className="rounded-lg border border-[var(--line)] p-3">
                  <p className="flex items-center gap-2 font-medium"><Globe size={14} /> <span className="truncate">{u.title || u.url}</span></p>
                  {u.summary && <p className="mt-1 line-clamp-3 text-xs text-[var(--text-soft)]">{u.summary}</p>}
                </li>
              ))}
            </ul>
          ))}

        {scheda === "fatti" &&
          (nFatti === 0 ? (
            <Vuoto titolo="Ancora nessun fatto">
              Man mano che racconti il caso, qui trovi ciò che K-BOT ha capito: città, dipendenti, importi, date. Se qualcosa è sbagliato, correggilo in chat.
            </Vuoto>
          ) : (
            <>
              <p className="mb-3 text-xs text-[var(--text-muted)]">Quello che hai detto tu, in questa pratica. Vale l&apos;ultima versione.</p>
              <dl className="divide-y divide-[var(--line)] rounded-lg border border-[var(--line)]">
                {Object.entries(fatti).map(([k, v]) => (
                  <div key={k} className="grid grid-cols-[120px_1fr] gap-3 px-3 py-2">
                    <dt className="text-[var(--text-muted)]">{etichettaFatto(k)}</dt>
                    <dd className="min-w-0 break-words">{v}</dd>
                  </div>
                ))}
              </dl>
            </>
          ))}

        {scheda === "fonti" && (
          <>
            {fonti.length === 0 ? (
              <Vuoto titolo="Nessuna fonte citata">
                Le norme che K-BOT cita nelle risposte, lette dal testo vigente, compaiono qui.
              </Vuoto>
            ) : (
              <ul className="space-y-2">
                {fonti.map((f) => (
                  <li key={f} className="flex items-center gap-2 rounded-lg border border-[var(--line)] px-3 py-2">
                    <span className="flex-1">{f}</span>
                    <span className="rounded-md bg-[var(--ok-bg)] px-2 py-0.5 text-xs text-[var(--ok-text)]">Testo vigente</span>
                  </li>
                ))}
              </ul>
            )}
            {competenze.length > 0 && (
              <div className="mt-5">
                <p className="mb-2 text-xs text-[var(--text-muted)]">Competenze usate in questa pratica</p>
                <div className="flex flex-wrap gap-1.5">
                  {competenze.map((c) => (
                    <span key={c} className="rounded-md border border-[var(--line)] px-2 py-1 text-xs text-[var(--text-soft)]">{c}</span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
        {errore && <p className="mt-3 text-xs text-[var(--warn-text)]">{errore}</p>}
      </div>

      {scheda === "bozza" && bozza && (
        <div className="flex gap-2 border-t border-[var(--line)] px-4 py-3">
          {onScaricaWord && (
            <button
              onClick={() => { setErrore(null); onScaricaWord().catch((e: unknown) => setErrore(e instanceof Error ? e.message : "Download non riuscito.")); }}
              className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--teal)] px-3 py-2 text-sm font-medium text-[var(--on-accent)] hover:opacity-90"
            >
              <Download size={14} /> Scarica Word
            </button>
          )}
          <button onClick={copia} className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--line-strong)] px-3 py-2 text-sm hover:border-[var(--teal)]">
            <Copy size={14} /> {copiato ? "Copiato" : "Copia testo"}
          </button>
        </div>
      )}
    </section>
  );
}

function Vuoto({ titolo, children, icona }: { titolo: string; children: React.ReactNode; icona?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-start gap-1 py-6 text-[var(--text-soft)]">
      {icona && <span className="mb-1 text-[var(--text-muted)]">{icona}</span>}
      <p className="font-medium text-[var(--text-main)]">{titolo}</p>
      <p className="max-w-sm">{children}</p>
    </div>
  );
}
