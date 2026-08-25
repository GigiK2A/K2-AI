"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";

interface LoadingStateProps {
  text?: string;
  /** Quando passato (SSE reale), mostra la progress della generazione report.
   *  Se null, mostriamo lo stato onesto "sta ragionando" col tempo trascorso. */
  reportProgress?: { stage: string; progress: number } | null;
}

export function LoadingState({ text = "K2-AI sta ragionando...", reportProgress = null }: LoadingStateProps) {
  const live = !!reportProgress;
  const [elapsed, setElapsed] = useState(0);

  // Timer in tempo reale mentre il modello pensa. Niente più euristica "dopo 8s
  // assumo un report": un turno lento (es. modello con reasoning) NON è un report.
  // La UI di generazione report compare solo con progress reale via SSE (`live`).
  useEffect(() => {
    if (live) return;
    const start = Date.now();
    const t = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 1000);
    return () => clearInterval(t);
  }, [live]);

  return (
    <AnimatePresence mode="wait">
      {!live ? (
        <motion.div
          key="thinking"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="k2-panel max-w-2xl rounded-2xl p-4"
        >
          <div className="flex items-center gap-3">
            <p className="text-sm text-[var(--text-soft)]">{text}</p>
            {elapsed >= 3 && (
              <span className="text-xs tabular-nums text-[var(--text-soft)] opacity-70">{elapsed}s</span>
            )}
          </div>
          <div className="mt-3 flex gap-2">
            {[0, 1, 2].map((i) => (
              <motion.span
                key={i}
                animate={{ opacity: [0.25, 1, 0.25] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.15 }}
                className="h-2 w-2 rounded-full bg-[var(--teal)]"
              />
            ))}
          </div>
        </motion.div>
      ) : (
        <motion.div
          key="report"
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="k2-panel max-w-2xl rounded-2xl p-5"
        >
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-semibold text-[var(--text-main)]">Generazione report in corso</p>
            <span className="text-sm font-bold tabular-nums text-[var(--teal)]">
              {Math.floor(reportProgress!.progress)}%
            </span>
          </div>

          <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--bg-1,#1e2a38)]">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-[var(--teal)] to-[var(--accent,#E8A020)]"
              animate={{ width: `${reportProgress!.progress}%` }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            />
          </div>

          {reportProgress!.stage && (
            <motion.p
              key={reportProgress!.stage}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="mt-3 text-xs text-[var(--text-soft)]"
            >
              {reportProgress!.stage}
            </motion.p>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
