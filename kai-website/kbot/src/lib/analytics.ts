// K-BOT (Next.js) analytics — PostHog Cloud EU, anonymous mode.
// Same architectural choices as the marketing site:
//   - persistence: 'memory' (no cookies, no localStorage)
//   - no autocapture, no session recording
//   - never throws, never blocks UI
//
// Loaded dynamically so SSR/edge code paths are unaffected.

"use client";

type AnyProps = Record<string, unknown>;

let initialized = false;
let initPromise: Promise<void> | null = null;

const KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY || "";
const HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://eu.i.posthog.com";

export function initAnalytics(): Promise<void> {
  if (initPromise) return initPromise;
  if (typeof window === "undefined" || !KEY) {
    initPromise = Promise.resolve();
    return initPromise;
  }
  initPromise = import("posthog-js")
    .then(({ default: posthog }) => {
      try {
        posthog.init(KEY, {
          api_host: HOST,
          persistence: "memory",
          capture_pageview: true,
          capture_pageleave: true,
          disable_session_recording: true,
          respect_dnt: true,
          opt_out_capturing_by_default: false,
          autocapture: false,
        });
        initialized = true;
        // Make available for ad-hoc calls.
        (window as unknown as { posthog?: unknown }).posthog = posthog;
      } catch {
        /* swallow */
      }
    })
    .catch(() => {
      /* posthog-js failed to load — no-op */
    });
  return initPromise;
}

export function track(event: string, props: AnyProps = {}): void {
  if (typeof window === "undefined" || !KEY) return;
  if (!initialized) {
    // Best-effort: queue a track after init completes.
    void initAnalytics().then(() => {
      const ph = (window as unknown as { posthog?: { capture?: (e: string, p: AnyProps) => void } }).posthog;
      try { ph?.capture?.(event, props); } catch { /* ignore */ }
    });
    return;
  }
  try {
    const ph = (window as unknown as { posthog?: { capture?: (e: string, p: AnyProps) => void } }).posthog;
    ph?.capture?.(event, props);
  } catch {
    /* ignore */
  }
}
