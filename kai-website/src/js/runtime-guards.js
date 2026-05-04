export function prefersReducedMotion() {
  return typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function hasFinePointer() {
  return typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(pointer: fine)').matches
    && window.matchMedia('(hover: hover)').matches
}

export function isSmallViewport(minWidth = 768) {
  return typeof window !== 'undefined' && window.innerWidth < minWidth
}

export function isLowEndDevice() {
  const nav = typeof navigator !== 'undefined' ? navigator : null
  const memory = typeof nav?.deviceMemory === 'number' ? nav.deviceMemory : null
  const cores = typeof nav?.hardwareConcurrency === 'number' ? nav.hardwareConcurrency : null
  const saveData = Boolean(nav?.connection && nav.connection.saveData)

  return saveData || (memory !== null && memory <= 4) || (cores !== null && cores <= 4)
}

export function supportsIntersectionObserver() {
  return typeof window !== 'undefined' && 'IntersectionObserver' in window
}

export function supportsWebGL() {
  if (typeof document === 'undefined') return false

  try {
    const canvas = document.createElement('canvas')
    return Boolean(
      window.WebGLRenderingContext
      && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    )
  } catch {
    return false
  }
}

export function canRunHeavyGraphics(minWidth = 768) {
  return !prefersReducedMotion()
    && !isSmallViewport(minWidth)
    && hasFinePointer()
    && !isLowEndDevice()
    && supportsWebGL()
}
