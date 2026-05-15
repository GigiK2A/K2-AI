// Per-te page interactivity, extracted from inline <script> blocks to allow
// a strict CSP without 'unsafe-inline' for script-src. The HTML uses
// data-pt-action="select|reset" + data-profile rather than inline onclick.

let ptCurrentProfile = null

function ptSelectProfile(profile, button) {
  document.querySelectorAll('.pt-panel').forEach(p => p.classList.remove('active'))
  const emptyState = document.getElementById('pt-empty-state')
  if (emptyState) emptyState.style.display = 'none'
  document.querySelectorAll('.pt-profile-card').forEach(c => c.classList.remove('active'))
  if (button) button.classList.add('active')
  const panel = document.getElementById('pt-panel-' + profile)
  if (panel) {
    panel.classList.add('active')
    ptCurrentProfile = profile
    setTimeout(() => {
      panel.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 100)
  }
  /* PostHog tracking */
  if (typeof window.posthog !== 'undefined') {
    window.posthog.capture('profile_selected', {
      profile_type: profile,
      page_source: document.referrer || 'direct',
    })
  }
}

function ptReset() {
  document.querySelectorAll('.pt-panel').forEach(p => p.classList.remove('active'))
  document.querySelectorAll('.pt-profile-card').forEach(c => c.classList.remove('active'))
  const emptyState = document.getElementById('pt-empty-state')
  if (emptyState) emptyState.style.display = 'block'
  ptCurrentProfile = null
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Wire buttons declaratively (replacing the inline onclick attributes).
document.addEventListener('click', (ev) => {
  const target = ev.target instanceof Element ? ev.target.closest('[data-pt-action]') : null
  if (!target) return
  const action = target.getAttribute('data-pt-action')
  if (action === 'select') {
    const profile = target.getAttribute('data-profile')
    if (profile) ptSelectProfile(profile, target)
  } else if (action === 'reset') {
    ptReset()
  }
})

// Deep-link via query string.
window.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search)
  const preselect = params.get('profilo')
  if (preselect) {
    const validProfiles = ['hospitality', 'commercialista', 'avvocato', 'ingegnere', 'artigiano', 'pmi']
    if (validProfiles.includes(preselect)) {
      const btn = document.querySelector(`[data-profile="${preselect}"]`)
      if (btn) btn.click()
    }
  }
})

// /contatti pre-fill: rewrite every <a href="/contatti"> inside a profile
// panel to carry settore + messaggio query params so the contact form opens
// already compiled with the user's context.
;(function () {
  const PROFILE_TO_SECTOR = {
    hospitality: 'ops',
    commercialista: 'finance',
    avvocato: 'legale',
    ingegnere: 'tech',
    artigiano: 'ops',
    pmi: 'altro',
  }
  const PROFILE_LABEL = {
    hospitality: 'hospitality (hotel / agriturismo / B&B / affitti brevi)',
    commercialista: 'studio commercialista',
    avvocato: 'studio legale',
    ingegnere: 'studio di ingegneria / architettura',
    artigiano: 'artigiano / piccola impresa',
    pmi: 'PMI manifatturiera',
  }

  function wireContactPrefill() {
    document.querySelectorAll('.pt-panel').forEach(function (panel) {
      const profile = (panel.id || '').replace(/^pt-panel-/, '')
      if (!profile) return
      const sector = PROFILE_TO_SECTOR[profile] || 'altro'
      const profileLabel = PROFILE_LABEL[profile] || profile

      panel.querySelectorAll('a[href="/contatti"], a[href="/contatti/"]').forEach(function (a) {
        const rung = a.closest('.pt-rung')
        const rungName = rung ? (rung.querySelector('.pt-rung-name')?.textContent || '').trim() : ''
        const ctaLabel = (a.textContent || '').trim()

        const lines = [
          `Buongiorno, scrivo dalla pagina "Per te" — profilo ${profileLabel}.`,
          '',
          rungName
            ? `Mi interessa il livello "${rungName}" (CTA cliccato: "${ctaLabel}").`
            : `Vorrei capire come K2-AI può aiutare la mia attività (CTA cliccato: "${ctaLabel}").`,
          '',
          'La mia situazione attuale (descrivi in 2-3 righe):',
          '• cosa fai oggi:',
          '• dove perdi tempo:',
          '• strumenti già in uso (Excel, CRM, gestionale, ecc.):',
          '',
          'Quando posso parlare con qualcuno?',
        ]
        const messaggio = lines.join('\n')

        const params = new URLSearchParams({
          settore: sector,
          messaggio: messaggio,
          source: 'per-te_' + profile + (rungName ? '_' + rungName.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 32) : ''),
        })
        a.setAttribute('href', '/contatti?' + params.toString())
      })
    })
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wireContactPrefill)
  } else {
    wireContactPrefill()
  }

  // Cross-bot bridge: rewrite /app links to carry the site-widget session.
  try {
    const sid = sessionStorage.getItem('kbot.site_session_id')
    if (sid && sid.length >= 8) {
      const carry = '?continue=' + encodeURIComponent(sid)
      document.querySelectorAll('a[href="/app"], a[href="/app/"]').forEach(function (a) {
        a.setAttribute('href', '/app/' + carry)
      })
    }
  } catch (_) { /* ignore */ }
})()
