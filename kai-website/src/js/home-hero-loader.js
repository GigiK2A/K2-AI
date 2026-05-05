import { getGraphicsCapabilityReport } from './runtime-guards.js'

const heroGraphics = getGraphicsCapabilityReport(960)
const canRunHeroField = heroGraphics.allowed

if (canRunHeroField) {
  const load = () => import('./hero-3d.js')
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(load, { timeout: 1800 })
  } else {
    window.setTimeout(load, 300)
  }
} else {
  document.documentElement.dataset.hero3dFallback = heroGraphics.reasons.join(',')
  console.info('[K2 hero 3D] fallback active', heroGraphics)
}
