"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Copy, Download, FileText, Globe, Loader2, RotateCcw, X } from "lucide-react";
import type { AnalyzedUrl, UploadedFile } from "@/lib/api";
import type { StatoDocumento } from "@/lib/documento";

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

export type DocumentoPannello = {
  titolo: string;
  testo: string;
  stato: StatoDocumento;
  /** Versione mostrata (1-based) e numero di versioni dello stesso documento. */
  versione: number;
  versioni: number;
  /** Testo dell'ultimo tentativo interrotto, mostrato finché il nuovo non produce un documento. */
  errore?: string;
  /** Il documento viene dalla vecchia euristica (messaggi senza marcatori). */
  legacy?: boolean;
};

const ETICHETTA_STATO: Record<StatoDocumento, string> = {
  preparazione: "Preparo il documento…",
  scrittura: "In scrittura…",
  verifica: "Controllo il testo…",
  pronto: "Bozza pronta · da verificare",
  errore: "Interrotto",
};

export function PannelloPratica({
  scheda,
  onScheda,
  documento,
  onVersione,
  onRiprova,
  onScarica,
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
  documento: DocumentoPannello | null;
  /** -1 = versione precedente, +1 = successiva. */
  onVersione?: (delta: number) => void;
  onRiprova?: () => void;
  /** Scarica il documento mostrato nel formato scelto. L'esportazione è un passo a parte: il testo è già leggibile. */
  onScarica?: (formato: "docx" | "pdf") => Promise<void>;
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
  const [esportando, setEsportando] = useState<"docx" | "pdf" | null>(null);
  const finePagina = useRef<HTMLDivElement>(null);
  const nFatti = Object.keys(fatti).length;
  const conteggi: Record<SchedaPratica, number> = {
    bozza: documento ? 1 : 0,
    documenti: documenti.length + siti.length,
    fatti: nFatti,
    fonti: fonti.length,
  };

  // Mentre il documento si scrive il testo resta in vista: si scorre in fondo a ogni aggiornamento.
  useEffect(() => {
    if (documento?.stato === "scrittura") finePagina.current?.scrollIntoView({ block: "end" });
  }, [documento?.testo, documento?.stato]);

  async function esporta(formato: "docx" | "pdf") {
    if (!onScarica || esportando) return;
    setErrore(null);
    setEsportando(formato);
    try {
      await onScarica(formato);
    } catch (e) {
      setErrore(e instanceof Error ? e.message : "Esportazione non riuscita. Il testo resta qui: riprova.");
    } finally {
      setEsportando(null);
    }
  }

  async function copia() {
    if (!documento?.testo) return;
    try {
      await navigator.clipboard.writeText(documento.testo);
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
          (documento ? (
            <>
              <div className="mb-3 flex items-start gap-2">
                <p className="font-doc flex-1 text-base font-semibold">{documento.titolo}</p>
                <span
                  className={
                    "inline-flex items-center gap-1.5 border px-2 py-0.5 text-[11px] font-medium uppercase tracking-[0.1em] " +
                    (documento.stato === "pronto"
                      ? "border-[var(--warn-text)] text-[var(--warn-text)]"
                      : documento.stato === "errore"
                        ? "border-red-600 text-red-700"
                        : "border-[var(--line-strong)] text-[var(--text-soft)]")
                  }
                  role="status"
                  aria-live="polite"
                >
                  {(documento.stato === "preparazione" || documento.stato === "verifica") && <Loader2 size={11} className="animate-spin" />}
                  {documento.stato === "scrittura" && <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--teal)]" />}
                  {esportando ? "Preparo il file…" : ETICHETTA_STATO[documento.stato]}
                </span>
              </div>
              {documento.versioni > 1 && (
                <div className="mb-3 flex items-center gap-2 text-xs text-[var(--text-soft)]">
                  <button onClick={() => onVersione?.(-1)} disabled={documento.versione <= 1} className="rounded p-1 hover:bg-[var(--bg-2)] disabled:opacity-30" aria-label="Versione precedente">
                    <ChevronLeft size={14} />
                  </button>
                  <span>Versione {documento.versione} di {documento.versioni}</span>
                  <button onClick={() => onVersione?.(1)} disabled={documento.versione >= documento.versioni} className="rounded p-1 hover:bg-[var(--bg-2)] disabled:opacity-30" aria-label="Versione successiva">
                    <ChevronRight size={14} />
                  </button>
                </div>
              )}
              {documento.stato === "errore" && (
                <div className="mb-3 border border-red-300 bg-red-50 p-3 text-xs text-red-800">
                  <p>{documento.errore || "La generazione si è interrotta."} Il testo già scritto è qui sotto: non è andato perso.</p>
                  {onRiprova && (
                    <button onClick={onRiprova} className="mt-2 inline-flex items-center gap-1.5 rounded-md border border-red-400 bg-white px-2.5 py-1 font-medium hover:bg-red-100">
                      <RotateCcw size={12} /> Riprova
                    </button>
                  )}
                </div>
              )}
              {documento.testo ? (
                <article className="font-doc whitespace-pre-wrap border border-[var(--line)] bg-white p-6 text-[15px] leading-8 text-[#1d2128] shadow-[2px_2px_0_var(--line)]">
                  {documento.testo}
                  {documento.stato === "scrittura" && <span className="ml-0.5 inline-block w-[2px] animate-pulse bg-[#1d2128]" style={{ height: "1.1em", verticalAlign: "text-bottom" }} aria-hidden />}
                </article>
              ) : (
                <div className="flex items-center gap-2 border border-dashed border-[var(--line-strong)] p-6 text-sm text-[var(--text-soft)]">
                  <Loader2 size={14} className="animate-spin" /> Il testo comparirà qui mentre viene scritto.
                </div>
              )}
              <div ref={finePagina} />
              {documento.stato === "pronto" && (
                <p className="mt-3 text-xs text-[var(--text-muted)]">
                  È una bozza: controlla date, importi e nomi prima di inviare e, se la posta in gioco è alta, falla rivedere dal tuo professionista. Per modificarla chiedilo in chat.
                </p>
              )}
            </>
          ) : (
            <Vuoto icona={<FileText size={18} />} titolo="Nessuna bozza, per ora">
              Quando chiedi una lettera, una PEC, un registro o un verbale, il testo compare qui mentre viene scritto.
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
      </div>

      {scheda === "bozza" && documento && documento.testo && (documento.stato === "pronto" || documento.stato === "errore") && (
        <div className="flex flex-wrap gap-2 border-t border-[var(--line)] px-4 py-3">
          {onScarica && (
            <>
              <button
                onClick={() => void esporta("docx")}
                disabled={Boolean(esportando) || documento.stato === "errore"}
                className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--teal)] px-3 py-2 text-sm font-medium text-[var(--on-accent)] hover:opacity-90 disabled:opacity-50"
              >
                {esportando === "docx" ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />} Scarica Word
              </button>
              <button
                onClick={() => void esporta("pdf")}
                disabled={Boolean(esportando) || documento.stato === "errore"}
                className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--line-strong)] px-3 py-2 text-sm hover:border-[var(--teal)] disabled:opacity-50"
              >
                {esportando === "pdf" ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />} Scarica PDF
              </button>
            </>
          )}
          <button onClick={copia} className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--line-strong)] px-3 py-2 text-sm hover:border-[var(--teal)]">
            <Copy size={14} /> {copiato ? "Copiato" : "Copia testo"}
          </button>
        </div>
      )}
      {errore && scheda === "bozza" && <p className="px-4 pb-3 text-xs text-[var(--warn-text)]">{errore}</p>}
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
