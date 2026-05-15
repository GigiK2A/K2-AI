const titleNode = document.getElementById('newsletter-title')
const metaNode = document.getElementById('newsletter-meta')
const htmlNode = document.getElementById('newsletter-html')

function formatDate(value) {
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString('it-IT', { day: '2-digit', month: 'long', year: 'numeric' })
}

// Client-side belt-and-suspenders sanitization. Server-side sanitization
// (isomorphic-dompurify in server.js / api/newsletter/publish.ts) is the
// primary defense; this strips obvious script/event-handler patterns if
// older issues were stored before sanitization landed.
function clientSanitize(html) {
  const tmpl = document.createElement('template')
  tmpl.innerHTML = String(html || '')
  const root = tmpl.content
  const FORBIDDEN_TAGS = new Set(['SCRIPT', 'IFRAME', 'OBJECT', 'EMBED', 'STYLE', 'LINK', 'META', 'BASE', 'FORM', 'INPUT', 'BUTTON'])
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT)
  const toRemove = []
  let node = walker.nextNode()
  while (node) {
    if (FORBIDDEN_TAGS.has(node.tagName)) {
      toRemove.push(node)
    } else {
      // Strip event handler attributes and javascript: URIs.
      for (const attr of Array.from(node.attributes)) {
        const n = attr.name.toLowerCase()
        const v = String(attr.value || '')
        if (n.startsWith('on') || (n === 'href' && /^\s*javascript:/i.test(v)) || (n === 'src' && /^\s*javascript:/i.test(v))) {
          node.removeAttribute(attr.name)
        }
      }
    }
    node = walker.nextNode()
  }
  toRemove.forEach(n => n.remove())
  return root
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
    // Render sanitized DOM rather than raw innerHTML to defend against any
    // pre-sanitization rows that may exist in the issues table.
    htmlNode.replaceChildren(clientSanitize(item.html || ''))
    document.title = `${item.subject || 'Newsletter'} | K2-AI`
  } catch (err) {
    console.error(err)
    titleNode.textContent = 'Errore nel caricamento'
    metaNode.textContent = 'Riprova tra poco.'
  }
}

loadIssue()
