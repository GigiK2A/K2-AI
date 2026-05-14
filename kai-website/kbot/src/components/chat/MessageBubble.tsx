"use client";

import { motion } from "framer-motion";
import { Bot } from "lucide-react";
import { ChatMessage } from "@/types/chat";
import { prettyTime } from "@/lib/utils";
import { FeedbackWidget } from "@/components/report/FeedbackWidget";
import { API_BASE } from "@/lib/api";

export function MessageBubble({
  message,
  onCheckout,
  onFeedback,
}: {
  message: ChatMessage;
  onCheckout?: () => Promise<void>;
  onFeedback?: (reportId: string, rating: number, comment: string) => Promise<void>;
}) {
  const isBot = message.role === "assistant";

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className={isBot ? "mr-auto max-w-3xl" : "ml-auto max-w-xl"}>
      <div className={isBot ? "k2-panel rounded-2xl p-4" : "rounded-2xl border border-[var(--line)] bg-[rgba(255,255,255,0.02)] p-4"}>
        {isBot && (
          <div className="mb-2 flex items-center gap-2 text-xs text-[var(--text-muted)]">
            <Bot size={14} /> K2-AI
          </div>
        )}
        <p className="whitespace-pre-wrap text-[15px] leading-7 text-[var(--text-main)]">{message.content}</p>
        {message.attachments && message.attachments.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.attachments.map((f) => (
              <span key={f.fileId} className="rounded-full border border-[var(--line)] px-2 py-1 text-xs text-[var(--text-soft)]">
                Allegato: {f.name}
              </span>
            ))}
          </div>
        )}
        {(message.reportPdfDownloadUrl || message.reportHtmlUrl) && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.reportHtmlUrl && (
              <a
                href={`${API_BASE}${message.reportHtmlUrl}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex rounded-lg bg-[var(--teal)] px-3 py-2 text-xs font-semibold text-black"
              >
                Apri report
              </a>
            )}
            {message.reportHtmlDownloadUrl && (
              message.hasPaid ? (
                <a
                  href={`${API_BASE}${message.reportHtmlDownloadUrl}`}
                  download
                  className="inline-flex rounded-lg border border-[var(--teal)] px-3 py-2 text-xs font-semibold text-[var(--teal)]"
                >
                  Scarica HTML
                </a>
              ) : (
                <button
                  onClick={onCheckout}
                  className="inline-flex rounded-lg border border-[var(--teal)] px-3 py-2 text-xs font-semibold text-[var(--teal)]"
                >
                  Paga per scaricare HTML
                </button>
              )
            )}
            {message.reportPdfDownloadUrl && (
              message.hasPaid ? (
                <a
                  href={`${API_BASE}${message.reportPdfDownloadUrl}`}
                  target="_blank"
                  rel="noreferrer"
                  download={message.reportPdfFilename ?? undefined}
                  className="inline-flex rounded-lg border border-[var(--line)] px-3 py-2 text-xs font-semibold text-[var(--text-soft)]"
                >
                  Scarica PDF
                </a>
              ) : (
                <button
                  onClick={onCheckout}
                  className="inline-flex rounded-lg border border-[var(--line)] px-3 py-2 text-xs font-semibold text-[var(--text-soft)]"
                >
                  Paga per scaricare PDF
                </button>
              )
            )}
          </div>
        )}
        {message.reportPdfUrl && onFeedback && (
          <FeedbackWidget
            reportId={message.reportPdfUrl.split("/").pop() ?? ""}
            onSubmit={(rating, comment) =>
              onFeedback(message.reportPdfUrl!.split("/").pop() ?? "", rating, comment)
            }
          />
        )}
        <p className="mt-2 text-xs text-[var(--text-muted)]">{prettyTime(message.ts)}</p>
      </div>
    </motion.div>
  );
}
