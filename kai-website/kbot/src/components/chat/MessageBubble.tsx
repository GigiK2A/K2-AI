"use client";

import { motion } from "framer-motion";
import { Bot } from "lucide-react";
import { ChatMessage } from "@/types/chat";
import { prettyTime } from "@/lib/utils";

export function MessageBubble({
  message,
  onCheckout,
}: {
  message: ChatMessage;
  onCheckout?: () => Promise<void>;
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
          {message.content}
        </p>

        {message.attachments && message.attachments.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.attachments.map((f) => (
              <span
                key={f.path}
                className="rounded-full border border-[var(--line)] px-2 py-1 text-xs text-[var(--text-soft)]"
              >
                Allegato: {f.name}
              </span>
            ))}
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

        {/* Report-ready CTA: shown when the V2 summary has been emitted but no PDF yet */}
        {message.reportReady && !message.reportPdfUrl && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              onClick={onCheckout}
              className="inline-flex rounded-lg bg-[var(--teal)] px-3 py-2 text-xs font-semibold text-black hover:opacity-90"
            >
              {message.hasPaid ? "Genera il report PDF" : "Sblocca il report PDF · 19€"}
            </button>
            <span className="text-xs text-[var(--text-muted)]">
              Documento di ~9 pagine con KPI, piano d&apos;azione e roadmap.
            </span>
          </div>
        )}

        <p className="mt-2 text-xs text-[var(--text-muted)]">{prettyTime(message.ts)}</p>
      </div>
    </motion.div>
  );
}
