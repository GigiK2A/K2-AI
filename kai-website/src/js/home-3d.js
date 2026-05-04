// home-3d.js — Interactive effects layered over the Three.js background
// Card 3D tilt, stat counters, magnetic cursor dot, stagger reveals

import { hasFinePointer, prefersReducedMotion, supportsIntersectionObserver } from './runtime-guards.js'

const REDUCED_MOTION = prefersReducedMotion()
const HAS_FINE_POINTER = hasFinePointer()
const IS_SMALL_VIEWPORT = window.innerWidth < 768
const ALLOW_DESKTOP_TIMELINE_MOTION = !IS_SMALL_VIEWPORT
const ALLOW_INTERACTIVE_POINTER_MOTION = !REDUCED_MOTION && !IS_SMALL_VIEWPORT && HAS_FINE_POINTER
const CHAPTER_LABELS = {
  hero: '00 / ingresso nel sistema',
  evidence: '01 / proof operativo',
  context: '02 / da tool a sistema',
  method: '03 / architettura di lavoro',
  principles: '04 / principi operativi',
  diagnostic: '05 / camera diagnostica',
  faq: '06 / obiezioni',
  cta: '07 / azione',
}
const STAGE_COPY = {
  hero: ['state / 00', 'neural field'],
  evidence: ['state / 01', 'proof wall'],
  context: ['state / 02', 'context shift'],
  method: ['state / 03', 'operating method'],
  principles: ['state / 04', 'human control'],
  diagnostic: ['state / 05', 'diagnostic core'],
  faq: ['state / 06', 'objection layer'],
  cta: ['state / 07', 'activation'],
}

// ── Magnetic cursor dot ───────────────────────────────────────────────────────
function initCursorDot() {
  if (!ALLOW_INTERACTIVE_POINTER_MOTION) return

  const dot = document.createElement('div')
  dot.id = 'cursor-dot'
  dot.style.cssText = [
    'position:fixed',
    'pointer-events:none',
    'z-index:9000',
    'width:6px',
    'height:6px',
    'border-radius:50%',
    'background:rgba(255,255,255,0.85)',
    'transform:translate(-50%,-50%)',
    'transition:width 0.2s,height 0.2s,opacity 0.2s',
    'will-change:transform',
    'top:0',
    'left:0',
  ].join(';')

  const ring = document.createElement('div')
  ring.id = 'cursor-ring'
  ring.style.cssText = [
    'position:fixed',
    'pointer-events:none',
    'z-index:8999',
    'width:32px',
    'height:32px',
    'border-radius:50%',
    'border:1px solid rgba(255,255,255,0.22)',
    'transform:translate(-50%,-50%)',
    'transition:width 0.35s,height 0.35s,opacity 0.35s,border-color 0.2s',
    'will-change:transform',
    'top:0',
    'left:0',
  ].join(';')

  document.body.appendChild(ring)
  document.body.appendChild(dot)

  let dotX = -100, dotY = -100
  let ringX = -100, ringY = -100
  let rafId

  function lerp(a, b, t) { return a + (b - a) * t }

  window.addEventListener('mousemove', e => {
    dotX = e.clientX
    dotY = e.clientY
  }, { passive: true })

  function animateCursor() {
    rafId = requestAnimationFrame(animateCursor)
    ringX = lerp(ringX, dotX, 0.12)
    ringY = lerp(ringY, dotY, 0.12)
    dot.style.left  = dotX  + 'px'
    dot.style.top   = dotY  + 'px'
    ring.style.left = ringX + 'px'
    ring.style.top  = ringY + 'px'
  }
  animateCursor()

  // Expand ring on interactive elements
  const targets = 'a,button,.card,.step,.stat-3d,.problema-item,.spotlight-surface'
  document.querySelectorAll(targets).forEach(el => {
    el.addEventListener('mouseenter', () => {
      ring.style.width  = '52px'
      ring.style.height = '52px'
      ring.style.borderColor = 'rgba(180,210,255,0.4)'
      dot.style.opacity = '0.4'
    }, { passive: true })
    el.addEventListener('mouseleave', () => {
      ring.style.width  = '32px'
      ring.style.height = '32px'
      ring.style.borderColor = 'rgba(255,255,255,0.22)'
      dot.style.opacity = '1'
    }, { passive: true })
  })

  // Hide on mouse leave
  document.addEventListener('mouseleave', () => {
    dot.style.opacity  = '0'
    ring.style.opacity = '0'
  })
  document.addEventListener('mouseenter', () => {
    dot.style.opacity  = '1'
    ring.style.opacity = '1'
  })
}

// ── 3D card tilt ──────────────────────────────────────────────────────────────
function initCardTilt() {
  if (!ALLOW_INTERACTIVE_POINTER_MOTION) return

  const cards = document.querySelectorAll('.home-page .card, .home-page .stat-3d, .home-page .problema-item, .home-page .home-final-cta-inner')

  cards.forEach(card => {
    let rafId = null

    card.addEventListener('mousemove', e => {
      if (rafId) return
      rafId = requestAnimationFrame(() => {
        rafId = null
        const rect  = card.getBoundingClientRect()
        const cx    = rect.left + rect.width  / 2
        const cy    = rect.top  + rect.height / 2
        const dx    = (e.clientX - cx) / (rect.width  / 2)
        const dy    = (e.clientY - cy) / (rect.height / 2)
        const rotX  = -dy * 7
        const rotY  =  dx * 7
        card.style.transform    = `perspective(1000px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale3d(1.025,1.025,1.025)`
        card.style.transition   = 'transform 0.08s ease, background 0.35s, box-shadow 0.35s'
        card.style.willChange   = 'transform'
        card.style.zIndex       = '2'
      })
    }, { passive: true })

    card.addEventListener('mouseleave', () => {
      card.style.transition = 'transform 0.55s cubic-bezier(0.16,1,0.3,1), background 0.35s, box-shadow 0.35s'
      card.style.transform  = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1,1,1)'
      card.style.zIndex     = ''
      card.style.willChange = ''
    }, { passive: true })
  })
}

// ── Stat counter animation ────────────────────────────────────────────────────
function initStatCounters() {
  const els = document.querySelectorAll('.home-page .stat-3d-value, .home-page .stat-value')
  if (!els.length) return

  function parseVal(txt) {
    const m = String(txt).trim().match(/^([\d.,]+)(.*)$/)
    if (!m) return null
    const n = parseFloat(m[1].replace(',', '.'))
    return isNaN(n) ? null : { value: n, suffix: m[2], isInt: Number.isInteger(n) }
  }

  function easeOutCubic(t) { return 1 - (1 - t) ** 3 }

  function counter(el, from, to, suffix, isInt, dur) {
    const start = performance.now()
    ;(function frame(now) {
      const p = Math.min((now - start) / dur, 1)
      const v = from + (to - from) * easeOutCubic(p)
      el.textContent = (isInt ? Math.round(v) : v.toFixed(1)) + suffix
      if (p < 1) requestAnimationFrame(frame)
    })(start)
  }

  const animateCounter = el => {
    const parsed = parseVal(el.textContent)
    if (!parsed) return
    const duration = REDUCED_MOTION && ALLOW_DESKTOP_TIMELINE_MOTION ? 950 : REDUCED_MOTION ? 0 : 1600
    counter(el, 0, parsed.value, parsed.suffix, parsed.isInt, duration)
  }

  if (!supportsIntersectionObserver()) {
    els.forEach(animateCounter)
    return
  }

  const seen = new Set()
  const io = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting || seen.has(entry.target)) return
      seen.add(entry.target)
      animateCounter(entry.target)
    })
  }, { threshold: 0.5 })

  els.forEach(el => io.observe(el))
}

// ── Hero title character split animation ─────────────────────────────────────
function initHeroTextAnim() {
  if (!ALLOW_DESKTOP_TIMELINE_MOTION) return
  const title = document.querySelector('.hero-3d-title')
  if (!title) return

  title.innerHTML = [
    '<span class="hero-line"><span class="hero-word">Sistemi</span> <span class="hero-word">AI</span></span>',
    '<span class="hero-line"><span class="hero-word">per</span> <span class="hero-word">il</span> <span class="hero-word">lavoro</span></span>',
    '<span class="hero-line"><em><span class="hero-word">reale.</span></em></span>',
  ].join('')

  const words = title.querySelectorAll('.hero-word')
  const baseBlur = REDUCED_MOTION ? 8 : 18
  const baseOffset = REDUCED_MOTION ? 22 : 70
  const baseRotate = REDUCED_MOTION ? -8 : -28
  const duration = REDUCED_MOTION ? 0.58 : 1
  const blurDuration = REDUCED_MOTION ? 0.7 : 1.15
  const stagger = REDUCED_MOTION ? 0.045 : 0.105

  words.forEach((word, i) => {
    word.style.opacity   = '0'
    word.style.filter    = `blur(${baseBlur}px)`
    word.style.transform = `translateY(${baseOffset}px) rotateX(${baseRotate}deg) scale(0.98)`
    word.style.display   = 'inline-block'
    word.style.transition = [
      `opacity ${duration}s cubic-bezier(0.16,1,0.3,1) ${i * stagger}s`,
      `transform ${duration}s cubic-bezier(0.16,1,0.3,1) ${i * stagger}s`,
      `filter ${blurDuration}s cubic-bezier(0.16,1,0.3,1) ${i * stagger}s`,
    ].join(',')
  })

  // Trigger after first paint
  requestAnimationFrame(() => requestAnimationFrame(() => {
    words.forEach(word => {
      word.style.opacity   = '1'
      word.style.filter    = 'blur(0)'
      word.style.transform = 'translateY(0) rotateX(0deg) scale(1)'
    })
  }))
}

// ── ReactBits-inspired spotlight surfaces ────────────────────────────────────
function initSpotlightSurfaces() {
  if (!ALLOW_INTERACTIVE_POINTER_MOTION) return

  document.querySelectorAll('.home-page .spotlight-surface').forEach(surface => {
    let rafId = null
    surface.addEventListener('pointermove', e => {
      if (rafId) return
      rafId = requestAnimationFrame(() => {
        rafId = null
        const rect = surface.getBoundingClientRect()
        surface.style.setProperty('--spot-x', `${((e.clientX - rect.left) / rect.width) * 100}%`)
        surface.style.setProperty('--spot-y', `${((e.clientY - rect.top) / rect.height) * 100}%`)
      })
    }, { passive: true })
  })
}

// ── Gentle magnetic CTA behaviour ────────────────────────────────────────────
function initMagneticActions() {
  if (!ALLOW_INTERACTIVE_POINTER_MOTION) return

  document.querySelectorAll('.home-page .btn, .home-page .hero-3d-link, .home-page .nav-cta').forEach(el => {
    el.addEventListener('pointermove', e => {
      const rect = el.getBoundingClientRect()
      const dx = (e.clientX - rect.left - rect.width / 2) * 0.16
      const dy = (e.clientY - rect.top - rect.height / 2) * 0.22
      el.style.transform = `translate3d(${dx}px, ${dy}px, 0)`
    }, { passive: true })

    el.addEventListener('pointerleave', () => {
      el.style.transition = 'transform 520ms cubic-bezier(0.16,1,0.3,1)'
      el.style.transform = 'translate3d(0,0,0)'
      window.setTimeout(() => { el.style.transition = '' }, 540)
    }, { passive: true })
  })
}

// ── Scroll state machine: active chapter, lit surfaces, method progress ───────
function initHomeChapterState() {
  if (IS_SMALL_VIEWPORT) return

  const chapters = [...document.querySelectorAll('.home-page [data-home-chapter]')]
  if (!chapters.length) return

  const director = document.createElement('div')
  director.className = 'chapter-director'
  director.setAttribute('aria-hidden', 'true')
  director.innerHTML = [
    '<span class="chapter-director-label"></span>',
    '<i class="chapter-director-line"></i>',
    '<span class="chapter-director-index"></span>',
  ].join('')
  document.body.appendChild(director)

  const directorLabel = director.querySelector('.chapter-director-label')
  const directorIndex = director.querySelector('.chapter-director-index')
  const stage = document.querySelector('.experience-stage')
  const stageKicker = stage?.querySelector('.stage-kicker')
  const stageTitle = stage?.querySelector('.stage-title')

  let ticking = false

  function clamp(n, min, max) { return Math.max(min, Math.min(max, n)) }

  function update() {
    ticking = false
    const viewportCenter = window.innerHeight * 0.48
    let active = chapters[0]
    let best = Infinity

    chapters.forEach(section => {
      const rect = section.getBoundingClientRect()
      const sectionCenter = rect.top + rect.height * 0.42
      const distance = Math.abs(sectionCenter - viewportCenter)
      if (distance < best) {
        best = distance
        active = section
      }

      const visibility = clamp((window.innerHeight - Math.abs(rect.top)) / window.innerHeight, 0, 1)
      const localProgress = clamp((window.innerHeight * 0.82 - rect.top) / (rect.height + window.innerHeight * 0.2), 0, 1)
      section.style.setProperty('--chapter-presence', visibility.toFixed(3))
      section.style.setProperty('--chapter-local-progress', localProgress.toFixed(3))
    })

    const chapterName = active?.dataset.homeChapter || 'hero'
    document.body.dataset.homeChapter = chapterName
    if (stage) {
      const copy = STAGE_COPY[chapterName] || [chapterName, 'system']
      stage.dataset.stage = chapterName
      if (stageKicker.textContent !== copy[0]) stageKicker.textContent = copy[0]
      if (stageTitle.textContent !== copy[1]) stageTitle.textContent = copy[1]
    }
    directorLabel.textContent = CHAPTER_LABELS[chapterName] || chapterName
    directorIndex.textContent = `${Math.max(1, chapters.indexOf(active) + 1).toString().padStart(2, '0')} / ${chapters.length.toString().padStart(2, '0')}`
    chapters.forEach(section => section.classList.toggle('is-active-chapter', section === active))

    const pageProgress = clamp(window.scrollY / (document.documentElement.scrollHeight - window.innerHeight || 1), 0, 1)
    document.documentElement.style.setProperty('--page-progress', pageProgress.toFixed(4))

    const heroProgress = clamp(window.scrollY / (window.innerHeight * 1.08), 0, 1)
    document.documentElement.style.setProperty('--hero-drift', `${(heroProgress * -54).toFixed(2)}px`)
    document.documentElement.style.setProperty('--hero-scale', (1 - heroProgress * 0.055).toFixed(3))
    document.documentElement.style.setProperty('--aperture-y', `${(heroProgress * 80).toFixed(2)}px`)
    document.documentElement.style.setProperty('--aperture-scale', (1 + heroProgress * 0.12).toFixed(3))

    const method = document.querySelector('.home-page .method-grid')
    const methodSection = document.querySelector('.home-page .method-architecture')
    if (method && methodSection) {
      const rect = methodSection.getBoundingClientRect()
      const progress = clamp((window.innerHeight * 0.78 - rect.top) / (rect.height * 0.76), 0.18, 1)
      method.style.setProperty('--method-progress', progress.toFixed(3))
    }

    document.querySelectorAll('.home-page .chapter-handoff').forEach(handoff => {
      const rect = handoff.getBoundingClientRect()
      const p = clamp((window.innerHeight * 0.88 - rect.top) / (window.innerHeight * 0.72), 0, 1)
      const exit = clamp((-rect.top) / (window.innerHeight * 0.28), 0, 1)
      handoff.style.setProperty('--handoff-progress', (p - exit * 0.35).toFixed(3))
      handoff.style.setProperty('--handoff-opacity', (0.18 + p * 0.82 - exit * 0.7).toFixed(3))
      handoff.style.setProperty('--handoff-shift', `${((1 - p) * 28 - exit * 34).toFixed(2)}px`)
    })

    document.querySelectorAll('.home-page .spotlight-surface').forEach(surface => {
      const rect = surface.getBoundingClientRect()
      const lit = rect.top < window.innerHeight * 0.64 && rect.bottom > window.innerHeight * 0.2
      surface.classList.toggle('is-lit', lit)
    })

    const titleOcclusionPairs = [
      ['.home-page .context-chapter', '.home-page .context-chapter .statement', '.home-page .transformation-sequence'],
      ['.home-page .method-architecture', '.home-page .method-architecture .statement', '.home-page .method-grid'],
      ['.home-page .principles-manifesto', '.home-page .principles-manifesto .statement', '.home-page .manifesto-list'],
    ]

    titleOcclusionPairs.forEach(([sectionSel, titleSel, blockerSel]) => {
      const section = document.querySelector(sectionSel)
      const title = document.querySelector(titleSel)
      const blocker = document.querySelector(blockerSel)
      if (!section || !title || !blocker) return

      const titleRect = title.getBoundingClientRect()
      const blockerRect = blocker.getBoundingClientRect()
      const overlapStart = titleRect.top + titleRect.height * 0.22
      const overlapRange = Math.max(titleRect.height * 0.72, 1)
      const occlusion = clamp((overlapStart - blockerRect.top) / overlapRange, 0, 1)
      section.style.setProperty('--title-occlusion', occlusion.toFixed(3))
    })

    document.querySelectorAll('.home-page .reveal, .home-page .card, .home-page .step, .home-page .problema-item, .home-page .diagnosi-point').forEach((el, index) => {
      const rect = el.getBoundingClientRect()
      const center = rect.top + rect.height / 2
      const viewportMid = window.innerHeight * 0.5
      const hasPassedMidpoint = center < viewportMid
      const afterMidpointProgress = hasPassedMidpoint
        ? clamp((viewportMid - center) / (window.innerHeight * 0.42), 0, 1)
        : 0
      const distance = Math.abs(center - window.innerHeight * 0.52)
      const proximity = clamp(1 - distance / (window.innerHeight * 0.68), 0, 1)
      el.style.setProperty('--focus-proximity', proximity.toFixed(3))
      el.style.setProperty('--after-midpoint-progress', afterMidpointProgress.toFixed(3))
      el.style.setProperty('--decay-index', String(index % 8))
    })
  }

  function requestUpdate() {
    if (ticking) return
    ticking = true
    requestAnimationFrame(update)
  }

  window.addEventListener('scroll', requestUpdate, { passive: true })
  window.addEventListener('resize', requestUpdate, { passive: true })
  update()
}

// ── Step hover glow line ──────────────────────────────────────────────────────
function initStepGlow() {
  if (IS_SMALL_VIEWPORT || !HAS_FINE_POINTER) return
  document.querySelectorAll('.home-page .step').forEach(step => {
    step.addEventListener('mouseenter', () => {
      step.style.boxShadow = 'inset 2px 0 0 rgba(180,210,255,0.35)'
    }, { passive: true })
    step.addEventListener('mouseleave', () => {
      step.style.boxShadow = ''
    }, { passive: true })
  })
}

// ── Scroll-linked opacity on hero elements ────────────────────────────────────
function initHeroParallax() {
  if (!ALLOW_DESKTOP_TIMELINE_MOTION) return
  const inner = document.querySelector('.hero-3d-inner')
  if (!inner) return

  let ticking = false
  window.addEventListener('scroll', () => {
    if (ticking) return
    ticking = true
    requestAnimationFrame(() => {
      const s = window.scrollY / window.innerHeight
      const fadeStrength = REDUCED_MOTION ? 0.42 : 1.5
      inner.style.opacity = Math.max(0, 1 - s * fadeStrength)
      ticking = false
    })
  }, { passive: true })
}

// ── Boot ──────────────────────────────────────────────────────────────────────
function boot() {
  initCursorDot()
  initCardTilt()
  initStatCounters()
  initHeroTextAnim()
  initSpotlightSurfaces()
  initMagneticActions()
  initHomeChapterState()
  initStepGlow()
  initHeroParallax()
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot, { once: true })
} else {
  boot()
}

// ── Chapter disappearance choreography ───────────────────────────────────────
function initChapterChoreography() {
  if (!ALLOW_DESKTOP_TIMELINE_MOTION) return

  const sections = [...document.querySelectorAll('.home-page section')]
    .filter(section => !section.classList.contains('hero-3d-section'))
  if (!sections.length) return

  sections.forEach(section => section.classList.add('chapter-choreography'))

  let ticking = false
  function clamp(n, min, max) { return Math.max(min, Math.min(max, n)) }

  function update() {
    ticking = false
    const vh = window.innerHeight || 1

    sections.forEach(section => {
      const rect = section.getBoundingClientRect()
      const enter = clamp((vh * 0.94 - rect.top) / (vh * 0.48), 0, 1)
      const exit = clamp((-rect.top - rect.height * 0.3) / (vh * 0.52), 0, 1)
      const presence = clamp(enter - exit, 0, 1)
      const blur = 0
      const shift = 0
      const opacity = 1
      const scale = 1
      const clipTop = 0
      const clipBottom = 0

      section.style.setProperty('--chapter-opacity', opacity.toFixed(3))
      section.style.setProperty('--chapter-blur', `${blur.toFixed(2)}px`)
      section.style.setProperty('--chapter-shift', `${shift.toFixed(2)}px`)
      section.style.setProperty('--chapter-scale', scale.toFixed(4))
      section.style.setProperty('--chapter-clip-top', `${clipTop.toFixed(2)}%`)
      section.style.setProperty('--chapter-clip-bottom', `${clipBottom.toFixed(2)}%`)
    })
  }

  function requestUpdate() {
    if (ticking) return
    ticking = true
    requestAnimationFrame(update)
  }

  window.addEventListener('scroll', requestUpdate, { passive: true })
  window.addEventListener('resize', requestUpdate, { passive: true })
  update()
}

// Re-open boot with the chapter choreography without disturbing earlier effects.
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initChapterChoreography, { once: true })
} else {
  initChapterChoreography()
}
