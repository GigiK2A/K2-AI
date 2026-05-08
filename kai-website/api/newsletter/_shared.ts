import { createClient as createSupabaseClient } from '@supabase/supabase-js'

export function getEnvVar(name: string, fallbacks: string[] = []): string {
  for (const key of [name, ...fallbacks]) {
    const value = process.env[key]
    if (value) return value
  }
  return ''
}

export function createSupabaseAdminClient() {
  const supabaseUrl = getEnvVar('NEXT_PUBLIC_SUPABASE_URL', ['SUPABASE_URL'])
  const serviceRoleKey = getEnvVar('SUPABASE_SERVICE_ROLE_KEY', ['SUPABASE_SERVICE_KEY', 'SUPABASE_KEY'])

  if (!supabaseUrl || !serviceRoleKey) {
    throw new Error('Missing Supabase newsletter env vars')
  }

  return createSupabaseClient(supabaseUrl, serviceRoleKey, {
    auth: { persistSession: false },
  })
}

export function sendJson(res: any, status: number, payload: unknown) {
  res.statusCode = status
  res.setHeader('Content-Type', 'application/json; charset=utf-8')
  res.end(JSON.stringify(payload))
}

export function slugify(input: string): string {
  return String(input || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, ' ')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .slice(0, 80)
}

export function parseBody(req: any): Promise<Record<string, any>> {
  return new Promise((resolve, reject) => {
    try {
      if (req.body && typeof req.body === 'object') return resolve(req.body)
      if (typeof req.body === 'string') return resolve(req.body ? JSON.parse(req.body) : {})

      let data = ''
      req.on('data', (chunk: Buffer) => {
        data += chunk.toString()
      })
      req.on('end', () => {
        resolve(data ? JSON.parse(data) : {})
      })
      req.on('error', reject)
    } catch (err) {
      reject(err)
    }
  })
}

export function datePrefix(d = new Date()): string {
  return d.toISOString().slice(0, 10)
}
