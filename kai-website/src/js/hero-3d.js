import * as THREE from 'three'
import { getGraphicsCapabilityReport } from './runtime-guards.js'

const capability = getGraphicsCapabilityReport(960)

if (!capability.allowed) {
  throw new Error(`Hero 3D disabled on this device profile: ${capability.reasons.join(', ')}`)
}

const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches
const IS_MOBILE = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) || window.innerWidth < 768

const CFG = {
  dust: IS_MOBILE ? 180 : 520,
  dpr: IS_MOBILE ? 1 : 1.45,
  camZStart: 118,
  camZEnd: 76,
  camYEnd: -9,
  mouseStr: 0.13,
  lerp: 0.045,
}

const COLORS = {
  dark: 0x05070a,
  dust: 0x8fa2aa,
  signal: 0x58f0d7,
  cold: 0x8fd8ff,
  human: 0xffc982,
}

const canvas = document.getElementById('scene-3d')
if (!canvas) throw new Error('#scene-3d not found')

let renderer
try {
  renderer = new THREE.WebGLRenderer({
    canvas,
    alpha: true,
    antialias: !IS_MOBILE,
    powerPreference: 'low-power',
  })
} catch (error) {
  throw new Error(`WebGL renderer unavailable: ${error instanceof Error ? error.message : String(error)}`)
}
renderer.setPixelRatio(Math.min(devicePixelRatio, CFG.dpr))
renderer.setClearColor(0x000000, 0)
renderer.setSize(window.innerWidth, window.innerHeight, false)

const scene = new THREE.Scene()
scene.fog = new THREE.FogExp2(COLORS.dark, IS_MOBILE ? 0.014 : 0.007)

const camera = new THREE.PerspectiveCamera(52, window.innerWidth / window.innerHeight, 0.1, 520)
camera.position.set(0, 0, CFG.camZStart)

const root = new THREE.Group()
const dustLayer = new THREE.Group()
const membranes = new THREE.Group()
const neuralField = new THREE.Group()
const impulses = new THREE.Group()
root.add(dustLayer, membranes, neuralField, impulses)
scene.add(root)

const dust = createDustField()
dustLayer.add(dust.points)

const membraneRefs = createMembranes()
const synapseRefs = createSynapticArchitecture()
const impulseRefs = createImpulses()

let scrollPct = 0
let mx = 0
let my = 0
let cmx = 0
let cmy = 0
let hidden = false
let rafId

function onResize() {
  const w = window.innerWidth
  const h = window.innerHeight
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h, false)
}
window.addEventListener('resize', onResize, { passive: true })
window.addEventListener('scroll', () => {
  const max = document.documentElement.scrollHeight - window.innerHeight
  scrollPct = max > 0 ? window.scrollY / max : 0
}, { passive: true })
document.addEventListener('visibilitychange', () => { hidden = document.hidden })

if (!REDUCED_MOTION) {
  window.addEventListener('pointermove', event => {
    mx = (event.clientX / window.innerWidth - 0.5) * CFG.mouseStr
    my = (event.clientY / window.innerHeight - 0.5) * -CFG.mouseStr * 0.65
  }, { passive: true })
}

const navbar = document.getElementById('navbar')
window.addEventListener('scroll', () => {
  navbar?.classList.toggle('scrolled', window.scrollY > 40)
}, { passive: true })

function tick() {
  rafId = requestAnimationFrame(tick)
  if (hidden) return

  const t = performance.now() * 0.001
  const awaken = smoothstep(0.02, 0.22, scrollPct)
  const classify = smoothstep(0.22, 0.44, scrollPct)
  const route = smoothstep(0.44, 0.68, scrollPct)
  const quiet = smoothstep(0.72, 0.96, scrollPct)

  camera.position.z += (CFG.camZStart + (CFG.camZEnd - CFG.camZStart) * scrollPct - camera.position.z) * CFG.lerp
  camera.position.y += (CFG.camYEnd * scrollPct - camera.position.y) * CFG.lerp

  cmx += (mx - cmx) * 0.04
  cmy += (my - cmy) * 0.04
  root.rotation.y = cmx + Math.sin(t * 0.04) * 0.012
  root.rotation.x = cmy + Math.sin(t * 0.05) * 0.01
  root.position.y = -scrollPct * 14

  updateDust(t, awaken, quiet)
  updateMembranes(t, classify, quiet)
  updateSynapses(t, awaken, classify, route, quiet)
  updateImpulses(t, awaken, route, quiet)

  renderer.render(scene, camera)
}

tick()

function createDustField() {
  const positions = new Float32Array(CFG.dust * 3)
  const origin = new Float32Array(CFG.dust * 3)
  const target = new Float32Array(CFG.dust * 3)
  const phase = new Float32Array(CFG.dust)

  for (let i = 0; i < CFG.dust; i++) {
    const i3 = i * 3
    const p = randomPoint(160, 78, 130)
    const lane = i / CFG.dust
    const q = new THREE.Vector3(
      THREE.MathUtils.lerp(-88, 86, lane) + Math.sin(lane * 16) * 7,
      Math.sin(lane * 11) * 18 + (Math.random() - 0.5) * 10,
      (Math.random() - 0.5) * 80,
    )
    positions.set([p.x, p.y, p.z], i3)
    origin.set([p.x, p.y, p.z], i3)
    target.set([q.x, q.y, q.z], i3)
    phase[i] = Math.random() * Math.PI * 2
  }

  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  const mat = new THREE.PointsMaterial({
    color: COLORS.dust,
    size: IS_MOBILE ? 0.48 : 0.64,
    transparent: true,
    opacity: 0.26,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  })
  return { points: new THREE.Points(geo, mat), geo, positions, origin, target, phase, mat }
}

function createMembranes() {
  const refs = []
  const specs = [
    { pos: [-30, 4, -28], rot: [-0.12, -0.48, 0.08], size: [72, 34], opacity: 0.08 },
    { pos: [34, -10, 10], rot: [0.08, 0.36, -0.06], size: [66, 28], opacity: 0.055 },
    { pos: [12, 16, 36], rot: [-0.22, 0.14, 0.12], size: [54, 24], opacity: 0.04 },
  ]

  specs.forEach(spec => {
    const geo = new THREE.PlaneGeometry(spec.size[0], spec.size[1], 8, 4)
    const pos = geo.attributes.position
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i)
      const y = pos.getY(i)
      pos.setZ(i, Math.sin(x * 0.07) * 1.4 + Math.cos(y * 0.12) * 0.9)
    }
    pos.needsUpdate = true

    const mat = new THREE.MeshBasicMaterial({
      color: COLORS.cold,
      transparent: true,
      opacity: spec.opacity,
      wireframe: true,
      depthWrite: false,
      side: THREE.DoubleSide,
    })
    const mesh = new THREE.Mesh(geo, mat)
    mesh.position.set(...spec.pos)
    mesh.rotation.set(...spec.rot)
    mesh.userData.baseOpacity = spec.opacity
    membranes.add(mesh)
    refs.push(mesh)
  })
  return refs
}

function createSynapticArchitecture() {
  const refs = []
  const anchors = [
    new THREE.Vector3(-62, -18, 10),
    new THREE.Vector3(-26, 8, 4),
    new THREE.Vector3(8, -8, -10),
    new THREE.Vector3(38, 14, -2),
    new THREE.Vector3(66, -6, 8),
  ]

  anchors.forEach((anchor, index) => {
    const cluster = createSynapseCluster(anchor, index)
    neuralField.add(cluster.group)
    refs.push(cluster)
  })

  const dendrites = [
    [anchors[0], anchors[1], anchors[2]],
    [anchors[1], new THREE.Vector3(-6, 20, 12), anchors[3]],
    [anchors[2], new THREE.Vector3(24, -18, -4), anchors[4]],
    [anchors[3], new THREE.Vector3(54, 8, 6), anchors[4]],
  ]
  dendrites.forEach((points, index) => {
    neuralField.add(createFilament(points, index === 3 ? COLORS.human : COLORS.signal, index === 3 ? 0.22 : 0.18))
  })

  return refs
}

function createSynapseCluster(anchor, index) {
  const group = new THREE.Group()
  group.position.copy(anchor)
  group.userData.baseScale = index === 3 ? 1.14 : 1

  const count = index === 3 ? 34 : 24
  const pos = new Float32Array(count * 3)
  const branchVerts = []
  for (let i = 0; i < count; i++) {
    const v = randomUnit().multiplyScalar(1.4 + Math.random() * (index === 3 ? 4.2 : 3.4))
    pos.set([v.x, v.y, v.z], i * 3)
    if (Math.random() > 0.42) branchVerts.push(0, 0, 0, v.x, v.y, v.z)
  }

  const pointsGeo = new THREE.BufferGeometry()
  pointsGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
  const pointsMat = new THREE.PointsMaterial({
    color: index === 3 ? COLORS.human : COLORS.signal,
    size: index === 3 ? 0.72 : 0.58,
    transparent: true,
    opacity: index === 3 ? 0.62 : 0.48,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  })
  group.add(new THREE.Points(pointsGeo, pointsMat))

  const branchGeo = new THREE.BufferGeometry()
  branchGeo.setAttribute('position', new THREE.Float32BufferAttribute(branchVerts, 3))
  const branchMat = new THREE.LineBasicMaterial({
    color: index === 3 ? COLORS.human : COLORS.cold,
    transparent: true,
    opacity: index === 3 ? 0.20 : 0.15,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  })
  group.add(new THREE.LineSegments(branchGeo, branchMat))

  return { group, pointsMat, branchMat, anchor, index }
}

function createFilament(points, color, opacity) {
  const curve = new THREE.CatmullRomCurve3(points, false, 'catmullrom', 0.42)
  const line = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(curve.getPoints(96)),
    new THREE.LineBasicMaterial({ color, transparent: true, opacity, depthWrite: false, blending: THREE.AdditiveBlending }),
  )
  line.userData.baseOpacity = opacity
  line.userData.curve = curve
  return line
}

function createImpulses() {
  const refs = []
  neuralField.children.forEach(child => {
    if (!child.isLine || !child.userData.curve) return
    const count = IS_MOBILE ? 1 : 3
    for (let i = 0; i < count; i++) {
      const geo = new THREE.BufferGeometry()
      geo.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3))
      const mat = new THREE.PointsMaterial({
        color: child.material.color,
        size: 1.15,
        transparent: true,
        opacity: 0.0,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      })
      const point = new THREE.Points(geo, mat)
      point.userData.curve = child.userData.curve
      point.userData.offset = (i / count + refs.length * 0.17) % 1
      impulses.add(point)
      refs.push(point)
    }
  })
  return refs
}

function updateDust(t, awaken, quiet) {
  const settle = Math.min(1, awaken * 0.86 + quiet * 0.18)
  for (let i = 0; i < CFG.dust; i++) {
    const i3 = i * 3
    const phase = dust.phase[i]
    dust.positions[i3] = THREE.MathUtils.lerp(dust.origin[i3], dust.target[i3], settle) + Math.sin(t * 0.16 + phase) * 0.8
    dust.positions[i3 + 1] = THREE.MathUtils.lerp(dust.origin[i3 + 1], dust.target[i3 + 1], settle) + Math.cos(t * 0.13 + phase) * 0.55
    dust.positions[i3 + 2] = THREE.MathUtils.lerp(dust.origin[i3 + 2], dust.target[i3 + 2], settle)
  }
  dust.geo.attributes.position.needsUpdate = true
  dust.mat.opacity = 0.24 + awaken * 0.06 - quiet * 0.12
}

function updateMembranes(t, classify, quiet) {
  membraneRefs.forEach((mesh, i) => {
    mesh.rotation.z += Math.sin(t * 0.07 + i) * 0.0008
    mesh.material.opacity = mesh.userData.baseOpacity * (0.72 + classify * 1.5 - quiet * 0.65)
  })
}

function updateSynapses(t, awaken, classify, route, quiet) {
  synapseRefs.forEach(ref => {
    const activity = ref.index === 0 ? awaken : ref.index === 1 ? classify : ref.index === 3 ? route : Math.max(classify, route * 0.7)
    const pulse = 1 + Math.sin(t * 0.9 + ref.index) * 0.025 + activity * 0.06
    ref.group.scale.setScalar(ref.group.userData.baseScale * pulse)
    ref.group.rotation.z = Math.sin(t * 0.12 + ref.index) * 0.045
    ref.pointsMat.opacity = Math.max(0.10, (0.28 + activity * 0.34) * (1 - quiet * 0.38))
    ref.branchMat.opacity = Math.max(0.04, (0.10 + activity * 0.16) * (1 - quiet * 0.44))
  })

  neuralField.children.forEach((child, i) => {
    if (!child.isLine || !child.userData.baseOpacity) return
    const active = i % 2 ? classify : route
    child.material.opacity = child.userData.baseOpacity * (0.38 + active * 1.8 - quiet * 0.52)
  })
}

function updateImpulses(t, awaken, route, quiet) {
  impulseRefs.forEach((impulse, index) => {
    const active = index % 2 ? route : awaken
    const u = (impulse.userData.offset + t * (0.055 + active * 0.075)) % 1
    impulse.position.copy(impulse.userData.curve.getPointAt(u))
    impulse.material.opacity = Math.max(0, 0.12 + active * 0.68 - quiet * 0.28)
  })
}

function randomPoint(width, height, depth) {
  return new THREE.Vector3((Math.random() - 0.5) * width, (Math.random() - 0.5) * height, (Math.random() - 0.5) * depth)
}

function randomUnit() {
  return new THREE.Vector3(Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5).normalize()
}

function smoothstep(edge0, edge1, x) {
  const t = THREE.MathUtils.clamp((x - edge0) / (edge1 - edge0), 0, 1)
  return t * t * (3 - 2 * t)
}

if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    cancelAnimationFrame(rafId)
    renderer.dispose()
    window.removeEventListener('resize', onResize)
  })
}
