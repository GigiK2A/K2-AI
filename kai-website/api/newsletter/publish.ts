import { createSupabaseAdminClient, datePrefix, getEnvVar, parseBody, sendJson, slugify } from './_shared'

function normalizeText(value: unknown, maxLen: number): string {
  return String(value || '').trim().slice(0, maxLen)
}

export default async function handler(req: any, res: any) {
  res.setHeader('Access-Control-Allow-Origin', 'https://www.k2-ai.it')
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-internal-key')

  if (req.method === 'OPTIONS') {
    res.statusCode = 204
    res.end()
    return
  }

  if (req.method !== 'POST') return sendJson(res, 405, { error: 'Method not allowed' })

  const expectedKey = getEnvVar('INTERNAL_API_KEY')
  const providedKey = String(req.headers?.['x-internal-key'] || '')
  if (!expectedKey || providedKey !== expectedKey) {
    return sendJson(res, 401, { error: 'Unauthorized' })
  }

  let body: Record<string, any> = {}
  try {
    body = await parseBody(req)
  } catch {
    return sendJson(res, 400, { error: 'Invalid JSON' })
  }

  const subject = normalizeText(body.subject, 220)
  const previewText = normalizeText(body.preview_text, 500)
  const html = String(body.html || '').trim()

  if (!subject) return sendJson(res, 400, { error: 'Missing subject' })
  if (!html) return sendJson(res, 400, { error: 'Missing html' })

  const customSlug = normalizeText(body.slug, 120)
  const safeBase = slugify(customSlug || subject) || 'newsletter'
  const finalSlug = `${datePrefix()}-${safeBase}`.slice(0, 120)

  const supabase = createSupabaseAdminClient()

  const payload = {
    slug: finalSlug,
    subject,
    preview_text: previewText,
    html,
    source: normalizeText(body.source, 120) || 'n8n',
    published_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }

  const { data, error } = await supabase
    .from('newsletter_issues')
    .upsert(payload, { onConflict: 'slug' })
    .select('slug, subject, published_at')
    .single()

  if (error || !data) {
    console.error('Newsletter publish error:', error)
    return sendJson(res, 500, { error: 'Publish failed' })
  }

  return sendJson(res, 200, {
    ok: true,
    slug: data.slug,
    url: `https://www.k2-ai.it/newsletter-entry?slug=${encodeURIComponent(data.slug)}`,
    published_at: data.published_at,
  })
}
