// K2-AI — consenso ai cookie di marketing e caricamento del pixel di OpenAI Ads.
//
// Regole (vedi /cookie):
// - Il pixel NON viene caricato finché l'utente non preme "Accetta".
// - "Rifiuta" ha lo stesso peso di "Accetta" e non carica nulla.
// - La scelta è salvata in localStorage (solo la scelta, nessun dato personale).
// - Se il browser invia Do Not Track, il pixel non viene mai caricato e il
//   banner non viene mostrato (stessa regola già applicata a PostHog).
// - La scelta si può cambiare da /cookie (pulsante con [data-cookie-prefs]).
// - Qualsiasi errore è silenzioso: il consenso non deve mai rompere il sito.

const STORAGE_KEY = 'k2ai_consent_marketing'
const PIXEL_ID = 'EJH5RT4DEn8YjxNKCWN9so' // ID pubblico, non è un segreto
const PIXEL_SRC = 'https://bzrcdn.openai.com/sdk/oaiq.min.js'

function readChoice() {
  try {
    const v = window.localStorage.getItem(STORAGE_KEY)
    return v === 'granted' || v === 'denied' ? v : null
  } catch {
    return null
  }
}

function writeChoice(value) {
  try {
    window.localStorage.setItem(STORAGE_KEY, value)
  } catch {
    /* storage bloccato: la scelta vale solo per questa pagina */
  }
}

function doNotTrack() {
  return navigator.doNotTrack === '1' || window.doNotTrack === '1'
}

let pixelLoaded = false

function loadPixel() {
  if (pixelLoaded || window.oaiq) return
  pixelLoaded = true
  try {
    // Stesso comportamento dello snippet fornito da OpenAI, senza script inline.
    const q = function () {
      q.q.push(arguments)
    }
    q.q = []
    window.oaiq = q
    const s = document.createElement('script')
    s.async = true
    s.src = PIXEL_SRC
    const first = document.getElementsByTagName('script')[0]
    if (first && first.parentNode) first.parentNode.insertBefore(s, first)
    else document.head.appendChild(s)
    window.oaiq('init', { pixelId: PIXEL_ID, debug: false })
  } catch {
    /* mai bloccare la pagina */
  }
}

const BANNER_ID = 'k2ai-consent-banner'

function injectStyles() {
  if (document.getElementById('k2ai-consent-style')) return
  const st = document.createElement('style')
  st.id = 'k2ai-consent-style'
  st.textContent = `
#${BANNER_ID}{position:fixed;left:16px;right:16px;bottom:16px;z-index:2147483000;max-width:560px;margin:0 auto;
background:#0d0d10;color:#f3f3f5;border:1px solid rgba(255,255,255,.18);border-radius:14px;padding:16px 18px;
box-shadow:0 12px 40px rgba(0,0,0,.45);font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
#${BANNER_ID} p{margin:0 0 12px}
#${BANNER_ID} a{color:#fff;text-decoration:underline}
#${BANNER_ID} .k2ai-consent-actions{display:flex;gap:10px;flex-wrap:wrap}
#${BANNER_ID} button{flex:1 1 140px;min-height:44px;padding:10px 16px;border-radius:999px;cursor:pointer;
font:600 14px/1 system-ui,-apple-system,"Segoe UI",sans-serif;border:1px solid #fff;background:#fff;color:#0d0d10}
#${BANNER_ID} button:focus-visible{outline:2px solid #fff;outline-offset:2px}
@media (prefers-reduced-motion:no-preference){#${BANNER_ID}{animation:k2aiConsentIn .25s ease-out}}
@keyframes k2aiConsentIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}`
  document.head.appendChild(st)
}

function removeBanner() {
  const el = document.getElementById(BANNER_ID)
  if (el && el.parentNode) el.parentNode.removeChild(el)
}

function decide(value) {
  const previous = readChoice()
  writeChoice(value)
  removeBanner()
  if (value === 'granted') {
    loadPixel()
  } else if (previous === 'granted') {
    // Il pixel è già in pagina: per fermarlo davvero si ricarica la pagina.
    window.location.reload()
  }
}

function showBanner() {
  if (document.getElementById(BANNER_ID) || !document.body) return
  injectStyles()
  const box = document.createElement('div')
  box.id = BANNER_ID
  box.setAttribute('role', 'dialog')
  box.setAttribute('aria-label', 'Preferenze cookie')

  const p = document.createElement('p')
  p.append(
    'Usiamo uno strumento di terze parti (pixel di OpenAI Ads) per misurare i risultati delle nostre campagne pubblicitarie. ' +
      'Si attiva solo se accetti. Puoi cambiare idea in qualsiasi momento dalla '
  )
  const link = document.createElement('a')
  link.href = '/cookie'
  link.textContent = 'pagina Cookie'
  p.append(link, '.')

  const actions = document.createElement('div')
  actions.className = 'k2ai-consent-actions'
  const reject = document.createElement('button')
  reject.type = 'button'
  reject.textContent = 'Rifiuta'
  reject.addEventListener('click', () => decide('denied'))
  const accept = document.createElement('button')
  accept.type = 'button'
  accept.textContent = 'Accetta'
  accept.addEventListener('click', () => decide('granted'))
  actions.append(reject, accept)

  box.append(p, actions)
  document.body.appendChild(box)
}

function bindPreferencesLink() {
  document.addEventListener('click', (e) => {
    const t = e.target instanceof Element ? e.target.closest('[data-cookie-prefs]') : null
    if (!t) return
    e.preventDefault()
    showBanner()
  })
}

function boot() {
  try {
    bindPreferencesLink()
    if (doNotTrack()) return
    const choice = readChoice()
    if (choice === 'granted') loadPixel()
    else if (choice === null) showBanner()
  } catch {
    /* mai bloccare la pagina */
  }
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true })
  else boot()
}
