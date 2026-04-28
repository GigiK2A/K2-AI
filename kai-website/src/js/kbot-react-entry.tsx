import React from 'react'
import { createRoot } from 'react-dom/client'
import { KBot } from '../../components/kbot/KBot'

function mountKBot(): boolean {
  const rootEl = document.getElementById('kbot-react-root')
  if (!rootEl) return false

  try {
    const root = createRoot(rootEl)
    root.render(<KBot />)
    return true
  } catch (error) {
    console.error('K-BOT mount failed:', error)
    rootEl.innerHTML = '<div class="kbot-mount-error">K-BOT non disponibile al momento. Ricarica la pagina.</div>'
    return true
  }
}

if (!mountKBot()) {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { mountKBot() }, { once: true })
  } else {
    window.setTimeout(() => { mountKBot() }, 0)
  }
}

// PostHog — inizializza solo se VITE_POSTHOG_KEY è impostata
const posthogKey = import.meta.env.VITE_POSTHOG_KEY as string | undefined
if (posthogKey) {
  import('posthog-js').then(({ default: posthog }) => {
    posthog.init(posthogKey, {
      api_host: (import.meta.env.VITE_POSTHOG_HOST as string | undefined) || 'https://api.k2-ai.it',
      autocapture: false,
      capture_pageview: true,
      disable_session_recording: true,
      loaded: ph => { if (import.meta.env.DEV) ph.debug() },
    })
    ;(window as any).posthog = posthog
  })
}
