"use client";

import { Fragment } from "react";
import { motion } from "framer-motion";
import { Bot } from "lucide-react";
import { ChatMessage } from "@/types/chat";
import { prettyTime } from "@/lib/utils";

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
        className="mx-0.5 inline-flex items-baseline rounded-md border border-[var(--teal)]/40 bg-[var(--teal)]/10 px-1 py-0 text-[11px] font-medium text-[var(--teal)] align-baseline"
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
}: {
  message: ChatMessage;
  onCheckout?: () => Promise<void>;
  onGeneratePdf?: () => Promise<void>;
  onDownloadXlsx?: () => Promise<void>;
  onFollowUp?: (text: string) => void;
  /** Legacy props kept for backwards compatibility. */
  getAuthToken?: () => Promise<string | null>;
  messageIndex?: number;
}) {
  const isBot = message.role === "assistant";

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className={isBot ? "mr-auto max-w-3xl" : "ml-auto max-w-xl"}
    >
      <div
        className={
          isBot
            ? "k2-panel rounded-2xl p-4"
            : "rounded-2xl border border-[var(--line)] bg-[rgba(255,255,255,0.02)] p-4"
        }
      >
        {isBot && (
          <div className="mb-2 flex items-center gap-2 text-xs text-[var(--text-muted)]">
            <Bot size={14} /> K2-AI
          </div>
        )}

        <p className="whitespace-pre-wrap text-[15px] leading-7 text-[var(--text-main)]">
          {renderWithCitations(message.content)}
        </p>

        {message.attachments && message.attachments.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.attachments.map((f) => {
              const isImage =
                (f.type || "").startsWith("image/") ||
                /\.(jpe?g|png|gif|webp)$/i.test(f.name);
              if (isImage && f.publicUrl) {
                return (
                  // eslint-disable-next-line @next/next/no-img-element
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
              className="inline-flex rounded-lg bg-[var(--teal)] px-3 py-2 text-xs font-semibold text-black"
            >
              Apri il report (PDF)
            </a>
            {onDownloadXlsx && (
              <button
                type="button"
                onClick={() => {
                  void onDownloadXlsx();
                }}
                className="inline-flex rounded-lg border border-[var(--teal)] px-3 py-2 text-xs font-semibold text-[var(--teal)] hover:bg-[var(--teal)]/10"
              >
                Scarica in Excel
              </button>
            )}
          </div>
        )}

        {/* Report-ready CTA conversazionale. In FREE_MODE è nascosta: il documento
            viene generato dal motore 8e tramite il DeliverablePanel (selettore catalogo). */}
        {message.reportReady && !message.reportPdfUrl && !FREE_MODE && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              onClick={message.hasPaid ? onCheckout : onGeneratePdf}
              className="inline-flex rounded-lg bg-[var(--teal)] px-3 py-2 text-xs font-semibold text-black hover:opacity-90"
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

        <p className="mt-2 text-xs text-[var(--text-muted)]">{prettyTime(message.ts)}</p>
      </div>
    </motion.div>
  );
}
