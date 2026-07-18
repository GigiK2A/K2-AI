import { existsSync, readFileSync } from 'fs'
import path from 'path'

function parseEnvValue(raw: string): string {
  const value = raw.trim()
  if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
    return value.slice(1, -1)
  }
  return value
}

function readEnvVarFromFile(filePath: string, key: string): string | undefined {
  if (!existsSync(filePath)) return undefined

  const content = readFileSync(filePath, 'utf-8')
  const lines = content.split(/\r?\n/)

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue

    const normalized = trimmed.startsWith('export ') ? trimmed.slice(7).trim() : trimmed
    const idx = normalized.indexOf('=')
    if (idx <= 0) continue

    const k = normalized.slice(0, idx).trim()
    if (k !== key) continue

    const v = normalized.slice(idx + 1)
    return parseEnvValue(v)
  }

  return undefined
}

function envCandidateFiles(): string[] {
  const cwd = process.cwd()
  return [
    path.join(cwd, '.env.local'),
    path.join(cwd, '.env'),
    path.join(cwd, '..', '.env'),
    path.join(cwd, '..', 'apps', 'board', '.env'),
  ]
}

export function getSystemEnvVar(primaryKey: string, aliases: string[] = []): string | undefined {
  const keys = [primaryKey, ...aliases]

  for (const key of keys) {
    const runtimeValue = process.env[key]
    if (runtimeValue) return runtimeValue
  }

  const candidates = envCandidateFiles()

  for (const filePath of candidates) {
    for (const key of keys) {
      const value = readEnvVarFromFile(filePath, key)
      if (value) return value
    }
  }

  return undefined
}

export function getAnthropicApiKey(): string {
  const value = getSystemEnvVar('ANTHROPIC_API_KEY')
  if (value) return value

  throw new Error('ANTHROPIC_API_KEY non trovata in env runtime o file .env di sistema')
}
