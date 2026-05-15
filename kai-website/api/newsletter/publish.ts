import DOMPurify from 'isomorphic-dompurify'
import { createSupabaseAdminClient, datePrefix, getEnvVar, parseBody, sendJson, slugify } from './_shared'

const NEWSLETTER_SANITIZE_OPTS = {
  USE_PROFILES: { html: true },
  FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'form', 'input', 'button', 'style', 'link', 'meta'],
  FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'onfocus', 'onblur', 'onchange', 'onsubmit', 'formaction', 'srcdoc'],
  ALLOWED_URI_REGEXP: /^(?:https?:|mailto:|tel:|#|\/[^/])/i,
} as const

function sanitizeNewsletterHtml(raw: string): string {
  return DOMPurify.sanitize(String(raw || ''), NEWSLETTER_SANITIZE_OPTS as any) as string
}

function normalizeText(value: unknown, maxLen: number): string {
  return String(value || '').trim().slice(0, maxLen)
}

function formatItalianIssueTitle(date: Date): string {
  return `Newsletter del ${date.toLocaleDateString('it-IT', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })}`
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
  // Sanitize publisher-supplied HTML before storing. The newsletter is later
  // rendered via innerHTML on the public archive page; anything that survives
  // here is what visitors execute.
  const html = sanitizeNewsletterHtml(String(body.html || '').trim())

  if (!subject) return sendJson(res, 400, { error: 'Missing subject' })
  if (!html) return sendJson(res, 400, { error: 'Missing html' })

  const publishedAt = new Date()
  const displaySubject = formatItalianIssueTitle(publishedAt)
  const customSlug = normalizeText(body.slug, 120)
  const safeBase = slugify(customSlug || subject) || 'newsletter'
  const finalSlug = `${datePrefix()}-${safeBase}`.slice(0, 120)

  const supabase = createSupabaseAdminClient()

  const payload = {
    slug: finalSlug,
    subject: displaySubject,
    preview_text: previewText,
    html,
    source: normalizeText(body.source, 120) || 'n8n',
    published_at: publishedAt.toISOString(),
    updated_at: publishedAt.toISOString(),
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
