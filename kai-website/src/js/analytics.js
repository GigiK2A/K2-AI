// K2-AI site analytics — PostHog Cloud EU, anonymous mode (no cookies, no
// localStorage, no person identify). Loaded as an ES module from every page
// that needs tracking. If VITE_POSTHOG_KEY is missing, every function is a
// silent no-op — analytics must NEVER break the site.
//
// Architecture decisions (see docs/tracking/ANALYTICS-ARCHITECTURE.md):
// - persistence: 'memory' → events are tied to an in-memory distinct_id that
//   resets on every page load. No cookie banner required.
// - autocapture: false → we send events explicitly, avoids tracking sensitive
//   form values and chat content.
// - disable_session_recording: true → no replay, no PII.
// - respect_dnt: true → honor the user's "Do Not Track" preference.

import posthog from 'posthog-js'

const POSTHOG_KEY = import.meta.env.VITE_POSTHOG_KEY || ''
const POSTHOG_HOST = import.meta.env.VITE_POSTHOG_HOST || 'https://eu.i.posthog.com'

let initialized = false

export function initAnalytics() {
  if (initialized) return
  if (!POSTHOG_KEY) return // no-op when not configured (dev or missing env)
  try {
    posthog.init(POSTHOG_KEY, {
      api_host: POSTHOG_HOST,
      persistence: 'memory', // no cookies, no localStorage
      capture_pageview: true,
      capture_pageleave: true,
      disable_session_recording: true,
      respect_dnt: true,
      opt_out_capturing_by_default: false,
      autocapture: false,
      loaded: (ph) => {
        if (import.meta.env.DEV) ph.debug()
      },
    })
    initialized = true
    // Expose on window for legacy callers (per-te.js already references it).
    try { window.posthog = posthog } catch { /* ignore */ }
  } catch {
    // never let analytics throw into page boot
  }
}

export function track(event, props = {}) {
  if (!initialized || !POSTHOG_KEY) return
  try {
    posthog.capture(event, props)
  } catch {
    /* swallow */
  }
}

// Auto-wire data-attribute based click tracking. Pages that import this
// module get pillar-link tracking for free — just add data-track-profile="P01"
// (or data-track-cta="label") to any anchor.
function bindClickDelegation() {
  if (typeof document === 'undefined') return
  document.addEventListener(
    'click',
    (e) => {
      const target = e.target instanceof Element ? e.target : null
      if (!target) return

      const profileEl = target.closest('[data-track-profile]')
      if (profileEl instanceof HTMLElement) {
        track('profile_click', {
          profile_id: profileEl.dataset.trackProfile,
          href: profileEl.getAttribute('href') || '',
        })
      }

      const ctaEl = target.closest('[data-track-cta]')
      if (ctaEl instanceof HTMLElement) {
        track('cta_click', {
          label: ctaEl.dataset.trackCta,
          href: ctaEl.getAttribute('href') || '',
        })
      }
    },
    { capture: true, passive: true }
  )
}

// Boot on import.
initAnalytics()
bindClickDelegation()
