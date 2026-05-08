const grid = document.querySelector('[data-newsletter-grid]')
const statusNode = document.querySelector('[data-newsletter-status]')

function formatDate(value) {
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' })
}

function renderItem(item, index) {
  const article = document.createElement('article')
  article.className = 'card'
  article.style.padding = '24px'
  article.style.border = '1px solid var(--border-soft)'

  article.innerHTML = `
    <p class="mono" style="margin-bottom:8px">Newsletter #${String(index + 1).padStart(3, '0')} · ${formatDate(item.published_at)}</p>
    <h2 style="font-size:24px;line-height:1.2;margin-bottom:12px">${item.subject || 'Newsletter K2-AI'}</h2>
    <p style="color:var(--text-secondary);margin-bottom:16px">${item.preview_text || 'Apri la versione completa della newsletter in HTML.'}</p>
    <a href="/newsletter-entry?slug=${encodeURIComponent(item.slug)}" class="btn">Apri versione HTML →</a>
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
