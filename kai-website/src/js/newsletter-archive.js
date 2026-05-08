const grid = document.querySelector('[data-newsletter-grid]')
const statusNode = document.querySelector('[data-newsletter-status]')

function formatDate(value) {
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' })
}

function renderItem(item, index) {
  const article = document.createElement('article')
  article.className = `case-card reveal${index % 2 ? ' reveal-delay-1' : ''}`

  article.innerHTML = `
    <div class="case-card-header">
      <div class="case-card-sector">K2-AI Gazette · ${formatDate(item.published_at)}</div>
      <h3 class="case-card-title">${item.subject || 'Newsletter K2-AI'}</h3>
      <p class="case-card-desc">${item.preview_text || 'Apri la versione completa della newsletter in HTML.'}</p>
      <a href="/newsletter-entry?slug=${encodeURIComponent(item.slug)}" class="case-card-cta">Apri versione HTML →</a>
    </div>
    <div class="case-card-metrics">
      <div class="case-metric">
        <div class="case-metric-value">#${String(index + 1).padStart(3, '0')}</div>
        <div class="case-metric-label">Edizione archiviata</div>
      </div>
      <div class="case-metric">
        <div class="case-metric-value">HTML</div>
        <div class="case-metric-label">Versione leggibile dal sito</div>
      </div>
    </div>
  `

  return article
}

async function loadArchive() {
  if (!grid) return

  try {
    const resp = await fetch('/api/newsletter/issues?limit=200', { headers: { Accept: 'application/json' } })
    if (!resp.ok) throw new Error('Load failed')

    const data = await resp.json()
    const items = Array.isArray(data?.items) ? data.items : []

    if (!items.length) {
      if (statusNode) statusNode.textContent = 'Nessuna newsletter pubblicata al momento.'
      return
    }

    grid.innerHTML = ''
    items.forEach((item, index) => grid.appendChild(renderItem(item, index)))
    if (statusNode) statusNode.textContent = `${items.length} newsletter in archivio.`
  } catch (err) {
    console.error(err)
    if (statusNode) statusNode.textContent = 'Errore nel caricamento archivio. Riprova tra poco.'
  }
}

loadArchive()
