"use client";

import { useCallback, useState } from "react";
import {
  createDeliverable,
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
  authToken?: string | null;
}

/**
 * Pannello che richiede un deliverable Boost al motore 8e e ne polla lo stato,
 * mostrando l'avanzamento e, a fine, il link al PDF. Le citazioni del report
 * portano fonte+vigenza (grounding deterministico).
 */
export function DeliverablePanel({
  sessionId,
  servizioId,
  servizioLabel,
  inputs = {},
  authToken,
}: Props) {
  const [job, setJob] = useState<DeliverableJob | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const start = useCallback(async () => {
    setBusy(true);
    setErr(null);
    setJob(null);
    try {
      const { job_id } = await createDeliverable(sessionId, servizioId, inputs, authToken);
      const final = await pollDeliverable(job_id, (j) => setJob(j));
      setJob(final);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Errore");
    } finally {
      setBusy(false);
    }
  }, [sessionId, servizioId, inputs, authToken]);

  const status = job?.status;
  const pdf = job?.outputs?.pdf_url;

  return (
    <div className="mt-6 rounded-xl border border-neutral-200 bg-white p-5 shadow-sm dark:border-neutral-700 dark:bg-neutral-900">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold">{servizioLabel ?? "Deliverable"}</h3>
          <p className="text-sm text-neutral-500">Report professionale fondato su fonti verificate.</p>
        </div>
        {!busy && status !== "rendered" && (
          <button
            onClick={start}
            className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-700"
          >
            Genera
          </button>
        )}
      </div>

      {(busy || status) && status !== "rendered" && status !== "refused" && status !== "error" && (
        <div className="mt-4 flex items-center gap-3 text-sm text-neutral-600 dark:text-neutral-300">
          <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500" />
          {STATUS_LABEL[status ?? "routed"]}
        </div>
      )}

      {status === "rendered" && (
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
