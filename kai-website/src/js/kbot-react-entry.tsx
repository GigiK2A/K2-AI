import React from 'react'
import { createRoot } from 'react-dom/client'
import { KBot } from '../../components/kbot/KBot'

function mountKBot(rootEl: HTMLElement): boolean {
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

async function isKBotApiReachable(): Promise<boolean> {
  try {
    const response = await fetch('/api/kbot/status?id=00000000-0000-0000-0000-000000000000', {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'X-KAI-Request': 'fetch',
      },
      credentials: 'same-origin',
    })

    if (response.status === 401 || response.status === 403 || response.status === 503) {
      return false
    }

    const contentType = response.headers.get('content-type') || ''
    if (!contentType.includes('application/json')) return false

    return response.status === 200 || response.status === 400 || response.status === 404
  } catch {
    return false
  }
}

function renderLegacyFallback(rootEl: HTMLElement) {
  rootEl.innerHTML = `
    <div class="chat-header">
      <div class="chat-header-main">
        <div class="chat-status"></div>
        <div class="chat-header-copy">
          <span class="chat-header-text">K-BOT</span>
          <span class="chat-header-sub">Modalità compatibile</span>
        </div>
      </div>
    </div>
    <div class="chat-messages" id="chat-messages"></div>
    <form class="chat-input-area" id="chat-form">
      <textarea
        id="chat-input"
        placeholder="Descrivi il processo che ti sta costando più tempo..."
        rows="1"
        enterkeyhint="send"
      ></textarea>
      <button id="chat-send" type="button" aria-label="Invia">→</button>
    </form>
  `

  import('./chat.js').catch(err => {
    console.error('K-BOT fallback load failed:', err)
    rootEl.innerHTML = '<div class="kbot-mount-error">K-BOT non disponibile al momento. Riprova più tardi.</div>'
  })
}

async function bootKBot() {
  const rootEl = document.getElementById('kbot-react-root')
  if (!rootEl) return false

  const canUseReactKBot = await isKBotApiReachable()
  if (canUseReactKBot) {
    return mountKBot(rootEl)
  }

  renderLegacyFallback(rootEl)
  return true
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => { void bootKBot() }, { once: true })
} else {
  window.setTimeout(() => { void bootKBot() }, 0)
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
