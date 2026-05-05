import { canRunHeavyGraphics, hasFinePointer, prefersReducedMotion } from './runtime-guards.js'

const body = document.body
const eligible = ['method-page', 'workshop-page', 'cases-page', 'analysis-page', 'contact-page']
const page = eligible.find(cls => body.classList.contains(cls))
const reducedMotion = prefersReducedMotion()
const hasPointer = hasFinePointer()
const isMobile = window.innerWidth < 768 || !hasPointer || /Android|iPhone|iPad|iPod/i.test(navigator.userAgent)
let THREE_NS = null

if (page) {
  enhanceNavigation()
  enhanceSpotlights()
  enhancePointerField()
  if (canRunHeavyGraphics(960)) {
    initAmbientScene(page).catch(error => {
      console.warn('K2 immersive scene disabled:', error)
    })
  }
}

function enhanceNavigation() {
  const nav = document.getElementById('navbar')
  const markScrolled = () => nav?.classList.toggle('scrolled', window.scrollY > 36)
  markScrolled()
  window.addEventListener('scroll', markScrolled, { passive: true })

  const path = window.location.pathname.replace(/\.html$/, '').replace(/\/$/, '') || '/'
  document.querySelectorAll('.nav-links a, .nav-overlay a').forEach(link => {
    const href = new URL(link.getAttribute('href'), window.location.origin).pathname.replace(/\.html$/, '').replace(/\/$/, '') || '/'
    if (href === path) link.setAttribute('aria-current', 'page')
  })
}

function enhanceSpotlights() {
  const targets = document.querySelectorAll('.card, .case-card, .offerta-card, #contact-form, .newsletter-block, .analysis-chat-widget')
  targets.forEach(el => {
    el.addEventListener('pointermove', event => {
      const rect = el.getBoundingClientRect()
      el.style.setProperty('--spot-x', `${event.clientX - rect.left}px`)
      el.style.setProperty('--spot-y', `${event.clientY - rect.top}px`)
    }, { passive: true })
  })
}

function enhancePointerField() {
  if (isMobile) return

  // Pointer tracking and cursor ball are interactive, not autonomous animations —
  // do not gate them on prefers-reduced-motion.
  window.addEventListener('pointermove', event => {
    document.documentElement.style.setProperty('--k2-pointer-x', `${event.clientX}px`)
    document.documentElement.style.setProperty('--k2-pointer-y', `${event.clientY}px`)
  }, { passive: true })

  const cursor = document.createElement('div')
  cursor.className = 'k2-cursor'
  document.body.appendChild(cursor)

  let x = window.innerWidth / 2
  let y = window.innerHeight / 2
  let tx = x
  let ty = y

  window.addEventListener('pointermove', event => {
    tx = event.clientX
    ty = event.clientY
    cursor.style.opacity = '1'
  }, { passive: true })

  document.querySelectorAll('a, button, input, textarea, select, .card, .case-card, .offerta-card').forEach(el => {
    el.addEventListener('pointerenter', () => cursor.classList.add('is-active'), { passive: true })
    el.addEventListener('pointerleave', () => cursor.classList.remove('is-active'), { passive: true })
  })

  function loop() {
    x += (tx - x) * 0.18
    y += (ty - y) * 0.18
    cursor.style.transform = `translate3d(${x}px, ${y}px, 0) translate(-50%, -50%)`
    requestAnimationFrame(loop)
  }
  loop()
}

async function initAmbientScene(pageName) {
  const THREE = await import('three')
  THREE_NS = THREE
  const canvas = document.createElement('canvas')
  canvas.id = 'k2-immersive-canvas'
  canvas.setAttribute('aria-hidden', 'true')
  document.body.prepend(canvas)

  const renderer = new THREE.WebGLRenderer({
    canvas,
    alpha: true,
    antialias: true,
    powerPreference: 'low-power',
  })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.35))
  renderer.setClearColor(0x000000, 0)

  const scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2(0x05070a, 0.008)
  const camera = new THREE.PerspectiveCamera(54, window.innerWidth / window.innerHeight, 0.1, 520)
  camera.position.set(0, 2, 112)

  const root = new THREE.Group()
  scene.add(root)

  const palette = getPalette(pageName)
  const nodeCount = pageName === 'analysis-page' || pageName === 'contact-page' ? 62 : 96
  const positions = []
  const nodeGeo = new THREE.TetrahedronGeometry(0.42, 0)
  const hubGeo = new THREE.TetrahedronGeometry(1.05, 0)

  for (let i = 0; i < nodeCount; i++) {
    const hub = i < (pageName === 'method-page' ? 4 : 10)
    const p = getPosition(pageName, i, nodeCount)
    positions.push(p)

    const color = hub ? palette.hub : (Math.random() > 0.78 ? palette.accent : palette.node)
    const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: hub ? 0.68 : 0.18 + Math.random() * 0.28 })
    const mesh = new THREE.Mesh(hub ? hubGeo : nodeGeo, mat)
    mesh.position.copy(p)
    mesh.scale.setScalar(hub ? 1.15 + Math.random() * 0.6 : 0.42 + Math.random() * 0.72)
    mesh.userData = { phase: Math.random() * Math.PI * 2, base: mat.opacity, hub }
    root.add(mesh)
  }

  const lineVerts = []
  const maxDistance = pageName === 'method-page' ? 38 : 24
  const maxDSq = maxDistance * maxDistance
  for (let i = 0; i < positions.length; i++) {
    let made = 0
    for (let j = i + 1; j < positions.length && made < 1; j++) {
      if (positions[i].distanceToSquared(positions[j]) < maxDSq) {
        lineVerts.push(positions[i].x, positions[i].y, positions[i].z, positions[j].x, positions[j].y, positions[j].z)
        made++
      }
    }
  }

  if (lineVerts.length) {
    const lineGeo = new THREE.BufferGeometry()
    lineGeo.setAttribute('position', new THREE.Float32BufferAttribute(lineVerts, 3))
    const lineMat = new THREE.LineBasicMaterial({ color: palette.line, transparent: true, opacity: pageName === 'contact-page' ? 0.018 : 0.028, depthWrite: false })
    root.add(new THREE.LineSegments(lineGeo, lineMat))
  }


  createOperationalMotifs(root, palette, pageName)

  let scrollPct = 0
  let mx = 0
  let my = 0
  let cmx = 0
  let cmy = 0
  let hidden = false

  const onResize = () => {
    const w = window.innerWidth
    const h = window.innerHeight
    camera.aspect = w / h
    camera.updateProjectionMatrix()
    renderer.setSize(w, h, false)
  }
  onResize()

  window.addEventListener('resize', onResize, { passive: true })
  window.addEventListener('scroll', () => {
    const max = document.documentElement.scrollHeight - window.innerHeight
    scrollPct = max > 0 ? window.scrollY / max : 0
  }, { passive: true })
  window.addEventListener('pointermove', event => {
    mx = (event.clientX / window.innerWidth - 0.5) * 0.22
    my = (event.clientY / window.innerHeight - 0.5) * -0.14
  }, { passive: true })
  document.addEventListener('visibilitychange', () => { hidden = document.hidden })

  function tick() {
    requestAnimationFrame(tick)
    if (hidden) return
    const t = performance.now() * 0.001
    cmx += (mx - cmx) * 0.035
    cmy += (my - cmy) * 0.035

    root.rotation.y = t * (pageName === 'contact-page' ? 0.005 : 0.011) + cmx
    root.rotation.x = Math.sin(t * 0.12) * 0.035 + cmy
    root.position.y = -scrollPct * 28
    camera.position.z = 112 - scrollPct * 36

    for (const child of root.children) {
      if (!child.isMesh || !child.userData.base) continue
      const { phase, base, hub } = child.userData
      child.material.opacity = Math.max(0.025, base + Math.sin(t * (hub ? 0.52 : 0.72) + phase) * base * 0.22)
    }

    root.traverse(child => {
      if (child.userData?.route) {
        const u = (child.userData.offset + t * 0.055 + scrollPct * 0.18) % 1
        child.position.copy(child.userData.route.getPointAt(u))
        child.material.opacity = 0.22 + Math.sin(t * 2.2 + u * 6.28) * 0.08
      }
    })

    renderer.render(scene, camera)
  }
  tick()

  if (import.meta.hot) {
    import.meta.hot.dispose(() => {
      renderer.dispose()
      window.removeEventListener('resize', onResize)
    })
  }
}

function getPalette(pageName) {
  const palettes = {
    'method-page': { hub: 0x58f0d7, accent: 0x8fd8ff, node: 0xc8d2d8, line: 0x8fd8ff, ring: 0x58f0d7 },
    'workshop-page': { hub: 0x8fd8ff, accent: 0x58f0d7, node: 0xd8e6ea, line: 0x58f0d7, ring: 0x8fd8ff },
    'cases-page': { hub: 0xb7ff5e, accent: 0x58f0d7, node: 0xc8d2d8, line: 0x58f0d7, ring: 0xb7ff5e },
    'analysis-page': { hub: 0x58f0d7, accent: 0x8fd8ff, node: 0xe4eef2, line: 0x58f0d7, ring: 0x58f0d7 },
    'contact-page': { hub: 0x8fd8ff, accent: 0x58f0d7, node: 0xc8d2d8, line: 0x8fd8ff, ring: 0x8fd8ff },
  }
  return palettes[pageName] || palettes['method-page']
}

function getPosition(pageName, i, total) {
  const THREE = THREE_NS
  if (pageName === 'method-page' && i < 4) {
    return new THREE.Vector3(-54 + i * 36, Math.sin(i * 1.3) * 6, (i - 1.5) * -9)
  }

  if (pageName === 'workshop-page') {
    const layer = i % 5
    return new THREE.Vector3((Math.random() - 0.5) * 118, (Math.random() - 0.5) * 58 + layer * 2.2, (Math.random() - 0.5) * 92)
  }

  if (pageName === 'cases-page') {
    const a = (i / total) * Math.PI * 10
    const r = 12 + Math.random() * 62
    return new THREE.Vector3(Math.cos(a) * r, (Math.random() - 0.5) * 72, Math.sin(a) * r)
  }

  if (pageName === 'analysis-page') {
    const a = Math.random() * Math.PI * 2
    const r = 10 + Math.random() * 58
    return new THREE.Vector3(Math.cos(a) * r, Math.sin(a) * r * 0.72, (Math.random() - 0.5) * 52)
  }

  return new THREE.Vector3((Math.random() - 0.5) * 126, (Math.random() - 0.5) * 52, (Math.random() - 0.5) * 84)
}

function createOperationalMotifs(root, palette, pageName) {
  const THREE = THREE_NS
  const motif = new THREE.Group()
  motif.position.set(18, -2, 8)
  root.add(motif)

  if (pageName === 'method-page') {
    const hubs = [
      new THREE.Vector3(-54, 8, 0),
      new THREE.Vector3(-18, -4, -10),
      new THREE.Vector3(18, 5, 4),
      new THREE.Vector3(54, -5, -6),
    ]
    hubs.forEach((pos, i) => {
      const hub = createHub(palette.hub, i === 3 ? 0xffd28a : palette.hub, i === 3 ? 1.18 : 1)
      hub.position.copy(pos)
      motif.add(hub)
    })
    createCurve(motif, hubs, palette.line, 0.22)
    return
  }

  if (pageName === 'workshop-page') {
    for (let i = 0; i < 5; i++) {
      const panel = createPanel(palette.accent, 0.22)
      panel.position.set(-34 + i * 17, Math.sin(i) * 8, -12 + i * 3)
      panel.rotation.set(-0.16, -0.34 + i * 0.08, 0.04 * i)
      motif.add(panel)
    }
    createCurve(motif, [
      new THREE.Vector3(-62, -18, 16),
      new THREE.Vector3(-28, 0, 2),
      new THREE.Vector3(16, 12, -6),
      new THREE.Vector3(62, 4, 10),
    ], palette.line, 0.18)
    return
  }

  if (pageName === 'cases-page') {
    for (let i = 0; i < 6; i++) {
      const a = i / 6 * Math.PI * 2
      const hub = createHub(i % 2 ? palette.accent : palette.hub, i === 2 ? 0xb7ff5e : palette.hub, 0.74 + i * 0.04)
      hub.position.set(Math.cos(a) * 38, Math.sin(a * 1.3) * 16, Math.sin(a) * 22)
      motif.add(hub)
    }
    return
  }

  if (pageName === 'analysis-page') {
    const core = createHub(palette.hub, palette.hub, 1.35)
    core.position.set(16, 0, 0)
    motif.add(core)
    ;[-34, -18, -2].forEach((x, i) => {
      const panel = createPanel(palette.line, 0.13)
      panel.position.set(x, -10 + i * 10, -6 + i * 3)
      panel.rotation.set(-0.1, -0.46, 0.08)
      motif.add(panel)
    })
    createCurve(motif, [
      new THREE.Vector3(-58, -18, 8),
      new THREE.Vector3(-24, -8, 0),
      new THREE.Vector3(16, 0, 0),
      new THREE.Vector3(58, 16, -10),
    ], palette.line, 0.2)
    return
  }

  const channel = [
    new THREE.Vector3(-58, -10, 4),
    new THREE.Vector3(-22, -2, 0),
    new THREE.Vector3(18, 2, -4),
    new THREE.Vector3(58, 8, -8),
  ]
  createCurve(motif, channel, palette.line, 0.16)
  channel.forEach((pos, i) => {
    const hub = createHub(i === channel.length - 1 ? palette.accent : palette.hub, palette.accent, 0.54 + i * 0.08)
    hub.position.copy(pos)
    motif.add(hub)
  })
}

function createHub(color, ringColor, scale = 1) {
  const THREE = THREE_NS
  const group = new THREE.Group()
  group.scale.setScalar(scale)

  const pointCount = 22
  const pointPositions = new Float32Array(pointCount * 3)
  const filamentVerts = []
  for (let i = 0; i < pointCount; i++) {
    const v = new THREE.Vector3(Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5).normalize().multiplyScalar(1.1 + Math.random() * 4.2)
    pointPositions.set([v.x, v.y, v.z], i * 3)
    if (Math.random() > 0.36) filamentVerts.push(0, 0, 0, v.x, v.y, v.z)
  }

  const pointsGeo = new THREE.BufferGeometry()
  pointsGeo.setAttribute('position', new THREE.BufferAttribute(pointPositions, 3))
  const points = new THREE.Points(
    pointsGeo,
    new THREE.PointsMaterial({ color, size: 0.54, transparent: true, opacity: 0.62, depthWrite: false, blending: THREE.AdditiveBlending }),
  )
  points.userData.base = 0.62
  group.add(points)

  const filaments = new THREE.LineSegments(
    new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(filamentVerts, 3)),
    new THREE.LineBasicMaterial({ color: ringColor, transparent: true, opacity: 0.18, depthWrite: false, blending: THREE.AdditiveBlending }),
  )
  filaments.userData.base = 0.18
  group.add(filaments)
  return group
}

function createPanel(color, opacity) {
  const THREE = THREE_NS
  const group = new THREE.Group()
  const panelGeo = new THREE.PlaneGeometry(12, 7)
  const panel = new THREE.Mesh(
    panelGeo,
    new THREE.MeshBasicMaterial({ color: 0x101a20, transparent: true, opacity, side: THREE.DoubleSide, depthWrite: false }),
  )
  panel.userData.base = opacity
  group.add(panel)
  const edge = new THREE.LineSegments(
    new THREE.EdgesGeometry(panelGeo),
    new THREE.LineBasicMaterial({ color, transparent: true, opacity: opacity * 1.45, depthWrite: false }),
  )
  edge.userData.base = opacity * 1.45
  group.add(edge)
  return group
}

function createCurve(root, points, color, opacity) {
  const THREE = THREE_NS
  const curve = new THREE.CatmullRomCurve3(points, false, 'catmullrom', 0.32)
  const line = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(curve.getPoints(80)),
    new THREE.LineBasicMaterial({ color, transparent: true, opacity, depthWrite: false }),
  )
  root.add(line)

  for (let i = 0; i < 3; i++) {
    const packetGeo = new THREE.BufferGeometry()
    packetGeo.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3))
    const packet = new THREE.Points(
      packetGeo,
      new THREE.PointsMaterial({ color, size: 0.92, transparent: true, opacity: 0.38, depthWrite: false, blending: THREE.AdditiveBlending }),
    )
    packet.userData.route = curve
    packet.userData.offset = i / 3
    root.add(packet)
  }
}
