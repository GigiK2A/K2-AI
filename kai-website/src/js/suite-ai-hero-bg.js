/* Soft AI grid background for Suite AI hero */
export function initSuiteAiHeroBg(canvasId) {
  const canvas = document.getElementById(canvasId)
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  let W, H, nodes, raf, paused = false

  const NODE_COUNT = 48
  const LINK_DIST = 160
  const SPEED = 0.18

  function resize() {
    const dpr = window.devicePixelRatio || 1
    W = canvas.parentElement.offsetWidth
    H = canvas.parentElement.offsetHeight
    canvas.width = W * dpr
    canvas.height = H * dpr
    canvas.style.width = W + 'px'
    canvas.style.height = H + 'px'
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    build()
  }

  function build() {
    nodes = Array.from({ length: NODE_COUNT }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * SPEED,
      vy: (Math.random() - 0.5) * SPEED,
      r: Math.random() * 1.4 + 0.6,
      pulse: Math.random() * Math.PI * 2,
      pulseSpeed: 0.008 + Math.random() * 0.006,
    }))
  }

  function draw() {
    ctx.clearRect(0, 0, W, H)

    /* connections */
    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i]
      for (let j = i + 1; j < nodes.length; j++) {
        const b = nodes[j]
        const dx = a.x - b.x, dy = a.y - b.y
        const d = Math.sqrt(dx * dx + dy * dy)
        if (d > LINK_DIST) continue
        const alpha = (1 - d / LINK_DIST) * 0.07
        ctx.beginPath()
        ctx.moveTo(a.x, a.y)
        ctx.lineTo(b.x, b.y)
        ctx.strokeStyle = `rgba(255,255,255,${alpha})`
        ctx.lineWidth = 0.5
        ctx.stroke()
      }
    }

    /* nodes */
    for (const n of nodes) {
      n.pulse += n.pulseSpeed
      const glow = 0.18 + Math.sin(n.pulse) * 0.12

      const g = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r * 5)
      g.addColorStop(0, `rgba(255,255,255,${glow})`)
      g.addColorStop(1, 'rgba(255,255,255,0)')
      ctx.beginPath()
      ctx.arc(n.x, n.y, n.r * 5, 0, Math.PI * 2)
      ctx.fillStyle = g
      ctx.fill()

      ctx.beginPath()
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(255,255,255,${0.35 + Math.sin(n.pulse) * 0.15})`
      ctx.fill()
    }
  }

  function tick() {
    if (paused) return
    for (const n of nodes) {
      n.x += n.vx
      n.y += n.vy
      if (n.x < 0 || n.x > W) n.vx *= -1
      if (n.y < 0 || n.y > H) n.vy *= -1
    }
    draw()
    raf = requestAnimationFrame(tick)
  }

  const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
  if (mq.matches) { draw(); return }

  document.addEventListener('visibilitychange', () => {
    paused = document.hidden
    if (!paused) tick()
  })

  window.addEventListener('resize', () => { cancelAnimationFrame(raf); resize(); tick() })

  resize()
  tick()
}
