export function prefersReducedMotion() {
  return typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function hasFinePointer() {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return false
  }

  const primaryFine = window.matchMedia('(pointer: fine)').matches
  const primaryHover = window.matchMedia('(hover: hover)').matches
  const anyFine = window.matchMedia('(any-pointer: fine)').matches
  const anyHover = window.matchMedia('(any-hover: hover)').matches

  if ((primaryFine && primaryHover) || (anyFine && anyHover)) {
    return true
  }

  // Windows hybrid devices can expose coarse primary pointers even when a
  // hardware mouse is connected. Keep desktop effects enabled in that case.
  const ua = typeof navigator !== 'undefined' ? navigator.userAgent : ''
  const isWindowsDesktop = /\bWindows\b/i.test(ua) && !/\b(Android|iPhone|iPad|iPod)\b/i.test(ua)
  const notSmallViewport = typeof window.innerWidth === 'number' ? window.innerWidth >= 960 : false
  const hasCoarseOnly = window.matchMedia('(any-pointer: coarse)').matches

  return isWindowsDesktop && notSmallViewport && hasCoarseOnly
}

export function isSmallViewport(minWidth = 768) {
  return typeof window !== 'undefined' && window.innerWidth < minWidth
}

export function isLowEndDevice() {
  const nav = typeof navigator !== 'undefined' ? navigator : null
  const memory = typeof nav?.deviceMemory === 'number' ? nav.deviceMemory : null
  const cores = typeof nav?.hardwareConcurrency === 'number' ? nav.hardwareConcurrency : null
  const saveData = Boolean(nav?.connection && nav.connection.saveData)

  // Save-Data is a hard stop. Memory/cores thresholds are kept loose to avoid
  // blocking mainstream Windows office PCs (dual-core HT = 4 logical, but some
  // budget machines still report 2; deviceMemory rounds down, 2 GB is very low).
  return saveData || (memory !== null && memory <= 1) || (cores !== null && cores <= 1)
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

export function getGraphicsCapabilityReport(minWidth = 768) {
  const reducedMotion = prefersReducedMotion()
  const smallViewport = isSmallViewport(minWidth)
  const finePointer = hasFinePointer()
  const lowEndDevice = isLowEndDevice()
  const webgl = supportsWebGL()
  const reasons = []

  if (reducedMotion) reasons.push('prefers-reduced-motion')
  if (smallViewport) reasons.push(`viewport<${minWidth}`)
  if (!finePointer) reasons.push('no-fine-pointer')
  if (lowEndDevice) reasons.push('low-end-device')
  if (!webgl) reasons.push('no-webgl')

  const blockingReasons = reasons.filter(reason =>
    reason !== 'prefers-reduced-motion' && reason !== 'no-fine-pointer'
  )

  return {
    allowed: blockingReasons.length === 0,
    reducedMotion,
    smallViewport,
    finePointer,
    lowEndDevice,
    webgl,
    reasons,
  }
}

export function canRunHeavyGraphics(minWidth = 768) {
  const report = getGraphicsCapabilityReport(minWidth)

  // On desktop we still allow the ambient 3D layer when reduced motion is
  // requested, but we keep interaction-heavy flourishes disabled elsewhere.
  return report.webgl
    && report.finePointer
    && !report.smallViewport
    && !report.lowEndDevice
}
