"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";

interface LoadingStateProps {
  text?: string;
  /** Quando passato, sostituisce l'animazione fake con i valori reali ricevuti via SSE. */
  reportProgress?: { stage: string; progress: number } | null;
}

const REPORT_STEPS = [
  "Analisi del contesto...",
  "Raccolta benchmark di mercato...",
  "Strutturazione del report...",
  "Generazione sezioni...",
  "Applicazione design system...",
  "Calcolo KPI e proiezioni...",
  "Generazione grafici...",
  "Conversione PDF...",
  "Finalizzazione documento...",
];

// After REPORT_THRESHOLD ms with no response, assume a report is being generated
const REPORT_THRESHOLD = 8000;

export function LoadingState({ text = "K2-AI sta elaborando...", reportProgress = null }: LoadingStateProps) {
  const [isReport, setIsReport] = useState(!!reportProgress);
  const [progress, setProgress] = useState(reportProgress?.progress ?? 0);
  const [stepIndex, setStepIndex] = useState(0);
  const live = !!reportProgress;

  // Real progress: aggiorna stato dai dati SSE
  useEffect(() => {
    if (reportProgress) {
      setIsReport(true);
      setProgress(reportProgress.progress);
    }
  }, [reportProgress]);

  // Switch to report mode after 8 seconds of waiting (solo se non guidato da SSE)
  useEffect(() => {
    if (live) return;
    const timer = setTimeout(() => setIsReport(true), REPORT_THRESHOLD);
    return () => clearTimeout(timer);
  }, [live]);

  // Progress bar animation fake — solo se non c'è SSE attivo
  useEffect(() => {
    if (!isReport || live) return;
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 92) return prev;
        const increment = prev < 40 ? 2.5 : prev < 70 ? 1.2 : 0.5;
        return Math.min(prev + increment, 92);
      });
    }, 600);
    const stepInterval = setInterval(() => {
      setStepIndex((prev) => (prev + 1) % REPORT_STEPS.length);
    }, 8000);
    return () => {
      clearInterval(interval);
      clearInterval(stepInterval);
    };
  }, [isReport, live]);

  const liveStageLabel = reportProgress?.stage;

  return (
    <AnimatePresence mode="wait">
      {!isReport ? (
        <motion.div
          key="dots"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="k2-panel max-w-2xl rounded-2xl p-4"
        >
          <p className="text-sm text-[var(--text-soft)]">{text}</p>
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
            <motion.span
              key={Math.floor(progress)}
              initial={{ opacity: 0.6, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-sm font-bold tabular-nums text-[var(--teal)]"
            >
              {Math.floor(progress)}%
            </motion.span>
          </div>

          <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--bg-1,#1e2a38)]">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-[var(--teal)] to-[var(--accent,#E8A020)]"
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            />
          </div>

          <motion.p
            key={liveStageLabel ?? stepIndex}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="mt-3 text-xs text-[var(--text-soft)]"
          >
            {liveStageLabel ?? REPORT_STEPS[stepIndex]}
          </motion.p>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
