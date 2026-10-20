"use client";

import { Fragment } from "react";
import { motion } from "framer-motion";
import { FileText, RotateCcw } from "lucide-react";
import { ChatMessage } from "@/types/chat";
import { prettyTime } from "@/lib/utils";
import { fuoriDalDocumento } from "@/lib/documento";

const CITATION_RE = /\(pag\.\s*(\d+)\)/gi;

/**
 * FREE MODE (K-BOT ufficiale senza paywall): quando NEXT_PUBLIC_KBOT_FREE_MODE
 * === "1" il documento è prodotto dal motore 8e (DeliverablePanel) e la CTA del
 * report conversazionale viene nascosta, così c'è un solo percorso di generazione.
 * NB: NEXT_PUBLIC_* è inlinato a build-time → richiede rebuild del frontend.
 */
const FREE_MODE = process.env.NEXT_PUBLIC_KBOT_FREE_MODE === "1";

/** Riconosce "(pag. N)" e li mostra come chip cliccabili (styling only per ora). */
function renderWithCitations(text: string) {
  if (!text) return text;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  CITATION_RE.lastIndex = 0;
  while ((match = CITATION_RE.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    parts.push(
      <span
        key={`cite-${match.index}`}
        title={`Riferimento pagina ${match[1]}`}
        className="mx-0.5 inline-flex items-baseline rounded-md border border-[var(--teal)]/40 bg-[var(--teal-soft)] px-1 py-0 text-[11px] font-medium text-[var(--teal)] align-baseline"
      >
        pag.&nbsp;{match[1]}
      </span>,
    );
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts.length > 1 ? parts.map((p, i) => <Fragment key={i}>{p}</Fragment>) : text;
}

export function MessageBubble({
  message,
  onCheckout,
  onGeneratePdf,
  onDownloadXlsx,
  onFollowUp,
  onOpenDraft,
  docInfo,
  onRetry,
}: {
  message: ChatMessage;
  /** Se presente, sotto la risposta compare «Apri la bozza» (il messaggio contiene un documento). */
  onOpenDraft?: () => void;
  /** Il documento contenuto nel messaggio: la chat mostra solo la conversazione, il documento sta nel pannello. */
  docInfo?: { titolo: string; stato: "scrittura" | "pronto" | "interrotto"; legacy: boolean };
  /** Riprende un turno interrotto senza perdere il testo già scritto. */
  onRetry?: () => void;
  onCheckout?: () => Promise<void>;
  onGeneratePdf?: () => Promise<void>;
  onDownloadXlsx?: () => Promise<void>;
  onFollowUp?: (text: string) => void;
  /** Legacy props kept for backwards compatibility. */
  getAuthToken?: () => Promise<string | null>;
  messageIndex?: number;
}) {
  const isBot = message.role === "assistant";
  // La chat mostra la CONVERSAZIONE; il documento (blocco <<<DOCUMENTO…>>>) sta nel pannello e qui resta solo un rimando.
  const testo = isBot ? fuoriDalDocumento(message.content) : message.content;
  // Risposta ancora vuota (lo stato di attesa lo mostra la riga «sto scrivendo…»): niente riquadro vuoto con l'etichetta sola.
  if (isBot && !testo && !docInfo && !message.errore && !(message.attachments && message.attachments.length)) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-3xl"
    >
      <div className={isBot ? "py-1" : "border-l-2 border-[var(--text-main)] pl-4"}>
        <p className="mb-1 text-[11px] font-medium uppercase tracking-[0.12em] text-[var(--text-muted)]">
          {isBot ? "Risposta di K-BOT" : "La tua richiesta"}
        </p>

        {testo && (
          <p className={"whitespace-pre-wrap text-[15px] leading-7 text-[var(--text-main)]" + (isBot && onOpenDraft && docInfo?.legacy ? " line-clamp-5" : "")}>
            {renderWithCitations(testo)}
          </p>
        )}

        {message.attachments && message.attachments.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.attachments.map((f) => {
              const isImage =
                (f.type || "").startsWith("image/") ||
                /\.(jpe?g|png|gif|webp)$/i.test(f.name);
              if (isImage && f.publicUrl) {
                return (
                  <a
                    key={f.path}
                    href={f.publicUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="block overflow-hidden rounded-lg border border-[var(--line)]"
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={f.publicUrl}
                      alt={f.name}
                      className="h-24 w-24 object-cover"
                    />
                  </a>
                );
              }
              return (
                <span
                  key={f.path}
                  className="rounded-full border border-[var(--line)] px-2 py-1 text-xs text-[var(--text-soft)]"
                >
                  Allegato: {f.name}
                </span>
              );
            })}
          </div>
        )}

        {/* Already-generated deliverable (post-payment): PDF + Excel */}
        {message.reportPdfUrl && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <a
              href={message.reportPdfUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex rounded-lg bg-[var(--teal)] px-3 py-2 text-xs font-semibold text-[var(--on-accent)]"
            >
              Apri il report (PDF)
            </a>
            {onDownloadXlsx && (
              <button
                type="button"
                onClick={() => {
                  void onDownloadXlsx();
                }}
                className="inline-flex rounded-lg border border-[var(--teal)] px-3 py-2 text-xs font-semibold text-[var(--teal)] hover:bg-[var(--teal-soft)]"
              >
                Scarica in Excel
              </button>
            )}
          </div>
        )}

        {/* CTA conversazionale LEGACY (report 19€ via pdf_renderer): superata dal
            flusso ufficiale 8e (ReportGenerator, un bottone, paywall sul boost).
            Tenuta nascosta per non avere due CTA in conflitto. Il path resta vivo
            lato backend se servisse riattivarlo (rimuovi `&& false`). */}
        {false && message.reportReady && !message.reportPdfUrl && !FREE_MODE && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              onClick={message.hasPaid ? onCheckout : onGeneratePdf}
              className="inline-flex rounded-lg bg-[var(--teal)] px-3 py-2 text-xs font-semibold text-[var(--on-accent)] hover:opacity-90"
            >
              Genera il report PDF
            </button>
            <span className="text-xs text-[var(--text-muted)]">
              Documento di ~9 pagine con KPI, piano d&apos;azione e roadmap.
            </span>
          </div>
        )}

        {isBot && message.followUps && message.followUps.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.followUps.slice(0, 3).map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => onFollowUp?.(q)}
                className="rounded-full border border-[var(--line)] px-3 py-1 text-xs text-[var(--text-soft)] hover:border-[var(--teal)] hover:text-[var(--text-main)]"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {isBot && onOpenDraft && (
          <button
            type="button"
            onClick={onOpenDraft}
            className="mt-3 flex w-full max-w-md items-center gap-3 rounded-lg border border-[var(--line-strong)] bg-[var(--bg-1)] px-3 py-2.5 text-left hover:border-[var(--teal)]"
          >
            <FileText size={18} className="shrink-0 text-[var(--text-soft)]" />
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium">{docInfo?.titolo ?? "Bozza"}</span>
              <span className="block text-xs text-[var(--text-muted)]">
                {docInfo?.stato === "scrittura" ? "In scrittura… si apre nel pannello"
                  : docInfo?.stato === "interrotto" ? "Interrotto · apri per vedere il testo scritto"
                  : "Bozza pronta · da verificare"}
              </span>
            </span>
            {docInfo?.stato === "scrittura" && <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-[var(--teal)]" />}
          </button>
        )}

        {isBot && message.errore && (
          <div className="mt-3 border border-red-300 bg-red-50 p-3 text-sm text-red-800">
            <p>{message.errore} {testo || docInfo ? "Quello che era già stato scritto è qui sopra, non è andato perso." : ""}</p>
            {onRetry && (
              <button type="button" onClick={onRetry} className="mt-2 inline-flex items-center gap-1.5 rounded-md border border-red-400 bg-white px-2.5 py-1 text-xs font-medium hover:bg-red-100">
                <RotateCcw size={12} /> Riprova
              </button>
            )}
          </div>
        )}

        {message.ts > 0 && <p className="mt-2 text-xs text-[var(--text-muted)]">{prettyTime(message.ts)}</p>}
      </div>
    </motion.div>
  );
}
