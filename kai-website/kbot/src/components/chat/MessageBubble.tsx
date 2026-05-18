"use client";

import { Fragment, useState } from "react";
import { motion } from "framer-motion";
import { Bot, Download, FileText, FileCode, FileType2 } from "lucide-react";
import { ChatMessage } from "@/types/chat";
import { prettyTime } from "@/lib/utils";
import {
  downloadMarkdown,
  downloadMessageExport,
  type MessageExportFormat,
} from "@/lib/api";

const EXPORT_THRESHOLD = 1500;

function isExportable(message: ChatMessage): boolean {
  if (message.role !== "assistant") return false;
  if (!message.sessionId) return false;
  // Export gated to post-payment users (hasPaid) or pre-generated PDF on the message.
  if (!message.hasPaid && !message.reportPdfUrl) return false;
  if (message.reportReady) return true;
  return (message.content?.length ?? 0) >= EXPORT_THRESHOLD;
}

const CITATION_RE = /\(pag\.\s*(\d+)\)/gi;

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
  onFollowUp,
  getAuthToken,
  messageIndex,
}: {
  message: ChatMessage;
  onCheckout?: () => Promise<void>;
  onFollowUp?: (text: string) => void;
  getAuthToken?: () => Promise<string | null>;
  messageIndex?: number;
}) {
  const isBot = message.role === "assistant";
  const [menuOpen, setMenuOpen] = useState(false);
  const [busy, setBusy] = useState<MessageExportFormat | "md" | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const canExport = isExportable(message);

  async function handleExport(format: MessageExportFormat | "md") {
    if (!message.sessionId) return;
    setBusy(format);
    setExportError(null);
    try {
      if (format === "md") {
        downloadMarkdown(message.sessionId, message.content);
      } else {
        const token = getAuthToken ? await getAuthToken() : null;
        await downloadMessageExport(message.sessionId, format, {
          messageIndex,
          messageId: message.id,
          authToken: token,
        });
      }
      setMenuOpen(false);
    } catch (e) {
      setExportError(e instanceof Error ? e.message : "Errore export");
    } finally {
      setBusy(null);
    }
  }

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

        {/* Already-generated PDF link (post-payment) */}
        {message.reportPdfUrl && (
          <div className="mt-3">
            <a
              href={message.reportPdfUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex rounded-lg bg-[var(--teal)] px-3 py-2 text-xs font-semibold text-black"
            >
              Apri il report (PDF)
            </a>
          </div>
        )}

        {/* Report-ready CTA: only for paid users (no more 19€ unlock during free phase). */}
        {message.reportReady && !message.reportPdfUrl && message.hasPaid && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              onClick={onCheckout}
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

        {/* Inline export menu for long assistant messages */}
        {canExport && (
          <div className="relative mt-3">
            <button
              type="button"
              onClick={() => setMenuOpen((s) => !s)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--line)] bg-[rgba(255,255,255,0.02)] px-3 py-1.5 text-xs font-medium text-[var(--text-soft)] hover:text-[var(--text-main)]"
              aria-expanded={menuOpen}
            >
              <Download size={14} /> Scarica
            </button>
            {menuOpen && (
              <div className="absolute z-20 mt-1 w-44 rounded-lg border border-[var(--line)] bg-[var(--bg-1)] p-1 text-xs shadow-lg">
                <button
                  type="button"
                  disabled={busy !== null}
                  onClick={() => handleExport("pdf")}
                  className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-[var(--text-soft)] hover:bg-[rgba(255,255,255,0.04)] hover:text-[var(--text-main)] disabled:opacity-50"
                >
                  <FileType2 size={14} />
                  {busy === "pdf" ? "Generazione PDF…" : "Scarica PDF"}
                </button>
                <button
                  type="button"
                  disabled={busy !== null}
                  onClick={() => handleExport("md")}
                  className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-[var(--text-soft)] hover:bg-[rgba(255,255,255,0.04)] hover:text-[var(--text-main)] disabled:opacity-50"
                >
                  <FileCode size={14} />
                  {busy === "md" ? "Salvataggio…" : "Scarica Markdown"}
                </button>
                <button
                  type="button"
                  disabled={busy !== null}
                  onClick={() => handleExport("docx")}
                  className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-[var(--text-soft)] hover:bg-[rgba(255,255,255,0.04)] hover:text-[var(--text-main)] disabled:opacity-50"
                >
                  <FileText size={14} />
                  {busy === "docx" ? "Generazione DOCX…" : "Scarica DOCX"}
                </button>
              </div>
            )}
            {exportError && (
              <p className="mt-1 text-xs text-red-300">{exportError}</p>
            )}
          </div>
        )}

        <p className="mt-2 text-xs text-[var(--text-muted)]">{prettyTime(message.ts)}</p>
      </div>
    </motion.div>
  );
}
