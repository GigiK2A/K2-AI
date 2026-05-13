import { readFileSync, readdirSync, existsSync } from 'fs'
import path from 'path'

const SKILLS_DIR = path.join(process.cwd(), 'lib', 'skills')
const SKILL_CACHE = new Map<string, string>()
const BUNDLE_CACHE = new Map<string, string>()

export type LoadSkillOptions = {
  includeReferences?: boolean
  maxChars?: number
}

export type LoadSkillBundleOptions = {
  maxTotalChars?: number
  maxPerSkillChars?: number
  includeReferences?: boolean
}

function truncateText(text: string, maxChars?: number): string {
  if (!maxChars || maxChars <= 0) return text
  if (text.length <= maxChars) return text
  const head = text.slice(0, maxChars)
  return `${head}\n\n[CONTENUTO TRONCATO PER LIMITI DI CONTESTO]`
}

/**
 * Carica una skill e la trasforma in system prompt.
 * Concatena SKILL.md + tutti i file in references/.
 */
export function loadSkill(skillName: string, options: LoadSkillOptions = {}): string {
  const cacheKey = JSON.stringify({
    skillName,
    includeReferences: options.includeReferences !== false,
    maxChars: options.maxChars || 0,
  })
  const cached = SKILL_CACHE.get(cacheKey)
  if (cached) return cached

  const skillDir = path.join(SKILLS_DIR, skillName)

  if (!existsSync(skillDir)) {
    throw new Error(`Skill non trovata: ${skillName}`)
  }

  const skillMd = readFileSync(path.join(skillDir, 'SKILL.md'), 'utf-8')

  const refDir = path.join(skillDir, 'references')
  let references = ''

  if (options.includeReferences !== false && existsSync(refDir)) {
    const refFiles = readdirSync(refDir)
      .filter(f => f.endsWith('.md'))
      .sort()

    references = refFiles
      .map(f => {
        const content = readFileSync(path.join(refDir, f), 'utf-8')
        return `\n\n---\n## ${f.replace('.md', '')}\n\n${content}`
      })
      .join('')
  }

  const result = truncateText(skillMd + references, options.maxChars)
  SKILL_CACHE.set(cacheKey, result)
  return result
}

/**
 * Carica più skill e le unisce in un unico system prompt.
 * La skill base viene sempre prima.
 */
export function loadSkillBundle(skillNames: string[], options: LoadSkillBundleOptions = {}): string {
  const cacheKey = JSON.stringify({
    skillNames,
    maxTotalChars: options.maxTotalChars || 0,
    maxPerSkillChars: options.maxPerSkillChars || 0,
    includeReferences: options.includeReferences !== false,
  })
  const cached = BUNDLE_CACHE.get(cacheKey)
  if (cached) return cached

  const chunks: string[] = []

  for (const name of skillNames) {
    try {
      const content = loadSkill(name, {
        includeReferences: options.includeReferences,
        maxChars: options.maxPerSkillChars,
      })

      const block = `\n\n${'='.repeat(60)}\n# SKILL: ${name}\n${'='.repeat(60)}\n\n${content}`
      chunks.push(block)
    } catch {
      console.warn(`Skill ${name} non trovata, saltata.`)
    }
  }

  const result = truncateText(chunks.join(''), options.maxTotalChars)
  BUNDLE_CACHE.set(cacheKey, result)
  return result
}

/**
 * Lista tutte le skill disponibili.
 */
export function listAvailableSkills(): string[] {
  if (!existsSync(SKILLS_DIR)) return []
  return readdirSync(SKILLS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name)
    .sort()
}
