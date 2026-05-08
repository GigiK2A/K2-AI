const titleNode = document.getElementById('newsletter-title')
const metaNode = document.getElementById('newsletter-meta')
const htmlNode = document.getElementById('newsletter-html')

function formatDate(value) {
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString('it-IT', { day: '2-digit', month: 'long', year: 'numeric' })
}

async function loadIssue() {
  const params = new URLSearchParams(window.location.search)
  const slug = (params.get('slug') || '').trim()

  if (!slug) {
    titleNode.textContent = 'Newsletter non trovata'
    metaNode.textContent = 'Manca lo slug nella URL.'
    return
  }

  try {
    const resp = await fetch(`/api/newsletter/issue?slug=${encodeURIComponent(slug)}`, { headers: { Accept: 'application/json' } })
    if (!resp.ok) throw new Error('Load failed')
    const data = await resp.json()
    const item = data?.item

    if (!item) throw new Error('Missing item')

    titleNode.textContent = item.subject || 'Newsletter K2-AI'
    metaNode.textContent = formatDate(item.published_at)
    htmlNode.innerHTML = item.html || ''
    document.title = `${item.subject || 'Newsletter'} | K2-AI`
  } catch (err) {
    console.error(err)
    titleNode.textContent = 'Errore nel caricamento'
    metaNode.textContent = 'Riprova tra poco.'
  }
}

loadIssue()
