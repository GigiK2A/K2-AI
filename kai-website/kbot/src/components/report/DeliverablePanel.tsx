"use client";

import { useCallback, useState } from "react";
import {
  createDeliverable,
  createPreview,
  pollDeliverable,
  type DeliverableJob,
  type DeliverableStatus,
} from "@/lib/api";

const STATUS_LABEL: Record<DeliverableStatus, string> = {
  routed: "In coda…",
  running: "Generazione in corso…",
  validating: "Controllo qualità (fonti, conformità)…",
  rendered: "Pronto",
  refused: "Non generabile",
  error: "Errore",
};

interface Props {
  sessionId: string;
  servizioId: string;
  servizioLabel?: string;
  inputs?: Record<string, unknown>;
  /** Gate W8: pagato → documento completo; non pagato → anteprima gratuita. */
  hasPaid?: boolean;
  /** CTA per sbloccare il documento completo (checkout). */
  onUnlock?: () => void;
  getAuthToken?: () => Promise<string | null>;
}

/**
 * Pannello deliverable a due livelli (gate erogazione W8):
 * - non pagato → ANTEPRIMA gratuita (score + criticità #1 + aree bloccate + CTA)
 * - pagato → DOCUMENTO completo via 8e, polling, PDF.
 */
export function DeliverablePanel({
  sessionId,
  servizioId,
  servizioLabel,
  inputs = {},
  hasPaid = false,
  onUnlock,
  getAuthToken,
}: Props) {
  const [job, setJob] = useState<DeliverableJob | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = useCallback(
    async (level: "preview" | "full") => {
      setBusy(true);
      setErr(null);
      setJob(null);
      try {
        const token = getAuthToken ? await getAuthToken() : null;
        const { job_id } =
          level === "preview"
            ? await createPreview(sessionId, servizioId, inputs, token)
            : await createDeliverable(sessionId, servizioId, inputs, token);
        const final = await pollDeliverable(job_id, (j) => setJob(j));
        setJob(final);
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Errore");
      } finally {
        setBusy(false);
      }
    },
    [sessionId, servizioId, inputs, getAuthToken],
  );

  const status = job?.status;
  const preview = job?.outputs?.preview;
  const pdf = job?.outputs?.pdf_url;
  const inProgress = busy && status !== "rendered" && status !== "refused" && status !== "error";

  return (
    <div className="mt-6 rounded-xl border border-neutral-200 bg-white p-5 shadow-sm dark:border-neutral-700 dark:bg-neutral-900">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold">{servizioLabel ?? "Deliverable"}</h3>
          <p className="text-sm text-neutral-500">
            {hasPaid
              ? "Report professionale fondato su fonti verificate."
              : "Anteprima gratuita: punteggio e criticità prioritaria."}
          </p>
        </div>
        {!busy && status !== "rendered" && (
          <button
            onClick={() => run(hasPaid ? "full" : "preview")}
            className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-700"
          >
            {hasPaid ? "Genera documento" : "Anteprima gratuita"}
          </button>
        )}
      </div>

      {inProgress && (
        <div className="mt-4 flex items-center gap-3 text-sm text-neutral-600 dark:text-neutral-300">
          <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500" />
          {STATUS_LABEL[status ?? "routed"]}
        </div>
      )}

      {/* PREVIEW rendered */}
      {status === "rendered" && preview && (
        <div className="mt-4 space-y-3">
          {typeof preview.score === "number" && (
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold">{preview.score}</span>
              <span className="text-sm text-neutral-500">/100 · punteggio di sintesi</span>
            </div>
          )}
          {preview.criticita_1 && (
            <div className="rounded-lg bg-amber-50 p-3 dark:bg-amber-950/30">
              <p className="text-xs font-semibold uppercase text-amber-700">
                Criticità #1 · {preview.criticita_1.area}
              </p>
              <p className="mt-1 text-sm">{preview.criticita_1.descrizione}</p>
            </div>
          )}
          {preview.altre_aree?.length ? (
            <div>
              <p className="text-xs text-neutral-500">Altre aree analizzate (nel documento completo):</p>
              <ul className="mt-1 space-y-1">
                {preview.altre_aree.map((a) => (
                  <li key={a} className="flex items-center gap-2 text-sm text-neutral-400">
                    <span>🔒</span> {a}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          <button
            onClick={onUnlock}
            className="mt-2 inline-block rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
          >
            {preview.cta ?? "Sblocca il documento completo"} →
          </button>
        </div>
      )}

      {/* FULL rendered */}
      {status === "rendered" && !preview && (
        <div className="mt-4">
          <a
            href={pdf || "#"}
            target="_blank"
            rel="noopener"
            className="inline-block rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
          >
            Scarica il report PDF →
          </a>
          {job?.citazioni?.length ? (
            <p className="mt-3 text-xs text-neutral-500">
              {job.citazioni.length} fonti citate con vigenza verificata.
            </p>
          ) : null}
        </div>
      )}

      {status === "refused" && (
        <p className="mt-4 text-sm text-amber-700">
          Non possiamo generare questo report automaticamente
          {job?.refusal_reason ? ` (${job.refusal_reason})` : ""}. Ti ricontattiamo per via diretta.
        </p>
      )}

      {(status === "error" || err) && (
        <p className="mt-4 text-sm text-red-600">
          {err || job?.error || "Si è verificato un errore. Nessun addebito: riprova."}
        </p>
      )}
    </div>
  );
}
