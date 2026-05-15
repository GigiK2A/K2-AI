// Inline-extracted bootstrap for suite-ai.html (strict CSP requires no
// 'unsafe-inline' in script-src).
import { initSuiteAiServices } from './suite-ai-services.js'
import { initSuiteAiHeroBg } from './suite-ai-hero-bg.js'

try { initSuiteAiHeroBg('sas-hero-canvas') } catch (_) { /* ignore */ }
initSuiteAiServices()
