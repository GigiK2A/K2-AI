import { SUITE_AI_SERVICES, CATEGORIES } from '../data/suiteAiServices.ts'

let activeCategory = 'all'

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function renderFilters(container) {
  container.innerHTML = CATEGORIES.map(cat => `
    <button
      class="sas-filter-btn${cat.slug === activeCategory ? ' active' : ''}"
      data-cat="${escHtml(cat.slug)}"
      type="button"
    >${escHtml(cat.label)}</button>
  `).join('')

  container.querySelectorAll('.sas-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      activeCategory = btn.dataset.cat
      renderFilters(container)
      renderGrid(document.getElementById('sas-grid'))
    })
  })
}

function renderGrid(grid) {
  const filtered = activeCategory === 'all'
    ? SUITE_AI_SERVICES
    : SUITE_AI_SERVICES.filter(s => s.category === activeCategory)

  if (!filtered.length) {
    grid.innerHTML = '<div class="sas-empty">Nessun servizio in questa categoria.</div>'
    return
  }

  grid.innerHTML = filtered.map((svc, i) => {
    const tags = svc.tags.slice(0, 4).map(t => `<span class="sas-tag">${escHtml(t)}</span>`).join('')
    const link = svc.pillarUrl
      ? `<a href="${escHtml(svc.pillarUrl)}" class="sas-card-link">Scopri di più <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M2 6h8M6 2l4 4-4 4"/></svg></a>`
      : `<span class="sas-card-nopillar">Scheda in arrivo</span>`

    const delay = (i % 6) * 60

    return `
      <div
        class="sas-card"
        style="animation-delay:${delay}ms"
        data-id="${escHtml(svc.id)}"
      >
        <div class="sas-card-top">
          <span class="sas-card-id">${escHtml(svc.id)}</span>
          <span class="sas-tier-badge sas-tier-${escHtml(svc.recommendedTier)}">${escHtml(svc.recommendedTier)}</span>
        </div>
        <div class="sas-card-name">${escHtml(svc.name)}</div>
        <p class="sas-card-desc">${escHtml(svc.shortDescription)}</p>
        <div class="sas-card-tags">${tags}</div>
        ${link}
      </div>
    `
  }).join('')

  // Trigger blur-fade-in via IntersectionObserver
  const io = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('sas-visible')
        obs.unobserve(entry.target)
      }
    })
  }, { threshold: 0.05 })

  grid.querySelectorAll('.sas-card').forEach(card => io.observe(card))
}

export function initSuiteAiServices() {
  const filtersEl = document.getElementById('sas-filters')
  const gridEl = document.getElementById('sas-grid')
  if (!filtersEl || !gridEl) return

  renderFilters(filtersEl)
  renderGrid(gridEl)
}
