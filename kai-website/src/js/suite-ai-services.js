import { SUITE_AI_SERVICES, CATEGORIES, TARGET_GROUPS, CATEGORY_META } from '../data/suiteAiServices.ts'

let activeCategory = 'all'
let activeTarget = 'all'
let searchQuery = ''

function esc(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

/* ── Filters ─────────────────────────────────── */

function renderCatFilters(el) {
  el.innerHTML = CATEGORIES.map(c => `
    <button class="sas-filter-btn${c.slug === activeCategory ? ' active' : ''}"
      data-cat="${esc(c.slug)}" type="button">${esc(c.label)}</button>
  `).join('') + '<span class="sas-filter-divider"></span>'

  el.querySelectorAll('.sas-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      activeCategory = btn.dataset.cat
      renderCatFilters(el)
      refresh()
    })
  })
}

function renderTargetFilters(el) {
  el.innerHTML = TARGET_GROUPS.map(t => `
    <button class="sas-filter-btn${t.slug === activeTarget ? ' active' : ''}"
      data-tgt="${esc(t.slug)}" type="button">${esc(t.label)}</button>
  `).join('')

  el.querySelectorAll('.sas-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      activeTarget = btn.dataset.tgt
      renderTargetFilters(el)
      refresh()
    })
  })
}

/* ── Grid ────────────────────────────────────── */

function filtered() {
  const q = searchQuery.trim().toLowerCase()
  return SUITE_AI_SERVICES.filter(s => {
    if (activeCategory !== 'all' && s.category !== activeCategory) return false
    if (activeTarget !== 'all' && s.targetGroup !== activeTarget) return false
    if (q) {
      const haystack = [s.name, s.shortDescription, s.target, ...s.tags, ...s.skills]
        .join(' ').toLowerCase()
      if (!haystack.includes(q)) return false
    }
    return true
  })
}

function renderGrid(grid, countEl) {
  const services = filtered()
  if (countEl) countEl.textContent = `${services.length} servizi`

  if (!services.length) {
    grid.innerHTML = '<div class="sas-empty">Nessun servizio corrisponde ai filtri selezionati.</div>'
    return
  }

  grid.innerHTML = services.map((svc, i) => {
    const meta = CATEGORY_META[svc.category]
    const catSlug = esc(svc.category)
    const skills = svc.skills.slice(0, 3).map(s =>
      `<span class="sas-skill">${esc(s)}</span>`
    ).join('')

    const btnScopri = svc.pillarUrl
      ? `<a href="${esc(svc.pillarUrl)}" class="sas-btn-scopri">
           Scopri
           <svg width="11" height="11" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M2 6h8M6 2l4 4-4 4"/></svg>
         </a>`
      : ''

    const kbotUrl = `/k-bot.html?service=${esc(svc.id)}`

    return `
      <div class="sas-card" style="animation-delay:${(i % 6) * 55}ms" data-id="${esc(svc.id)}">
        <div class="sas-card-head">
          <span class="sas-cat-badge sas-cat-${catSlug}">${esc(meta.label)}</span>
          <span class="sas-tier-chip">${esc(svc.recommendedTier)}</span>
        </div>
        <div class="sas-card-name">${esc(svc.name)}</div>
        <p class="sas-card-desc">${esc(svc.shortDescription)}</p>
        <div class="sas-skills">${skills}</div>
        <div class="sas-card-actions">
          <a href="${kbotUrl}" class="sas-btn-kbot">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8zm-1-5h2v2h-2zm0-8h2v6h-2z"/></svg>
            Avvia con K-BOT
          </a>
          ${btnScopri}
        </div>
      </div>
    `
  }).join('')

  /* Stagger with IntersectionObserver */
  const io = new IntersectionObserver((entries, obs) => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('sas-visible'); obs.unobserve(e.target) }
    })
  }, { threshold: 0.04 })
  grid.querySelectorAll('.sas-card').forEach(c => io.observe(c))
}

/* ── Steps reveal ────────────────────────────── */

function initStepsReveal() {
  const io = new IntersectionObserver((entries, obs) => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('sas-visible'); obs.unobserve(e.target) }
    })
  }, { threshold: 0.15 })
  document.querySelectorAll('.sas-step').forEach((el, i) => {
    el.style.transitionDelay = `${i * 90}ms`
    io.observe(el)
  })
}

/* ── Refresh ─────────────────────────────────── */

function refresh() {
  const grid = document.getElementById('sas-grid')
  const countEl = document.getElementById('sas-count')
  if (grid) renderGrid(grid, countEl)
}

/* ── Init ────────────────────────────────────── */

export function initSuiteAiServices() {
  const catFiltersEl = document.getElementById('sas-cat-filters')
  const tgtFiltersEl = document.getElementById('sas-target-filters')
  const gridEl = document.getElementById('sas-grid')
  const searchEl = document.getElementById('sas-search')
  const countEl = document.getElementById('sas-count')

  if (catFiltersEl) renderCatFilters(catFiltersEl)
  if (tgtFiltersEl) renderTargetFilters(tgtFiltersEl)
  if (gridEl) renderGrid(gridEl, countEl)

  if (searchEl) {
    searchEl.addEventListener('input', () => {
      searchQuery = searchEl.value
      refresh()
    })
  }

  initStepsReveal()
}
