import { createSupabaseAdminClient, sendJson } from './_shared'

export default async function handler(req: any, res: any) {
  if (req.method !== 'GET') return sendJson(res, 405, { error: 'Method not allowed' })

  const limitRaw = Number(req.query?.limit || 100)
  const limit = Number.isFinite(limitRaw) ? Math.min(Math.max(limitRaw, 1), 200) : 100

  const supabase = createSupabaseAdminClient()
  const { data, error } = await supabase
    .from('newsletter_issues')
    .select('slug,subject,preview_text,published_at')
    .order('published_at', { ascending: false })
    .limit(limit)

  if (error) {
    console.error('Newsletter list error:', error)
    return sendJson(res, 500, { error: 'List failed' })
  }

  return sendJson(res, 200, { ok: true, items: data || [] })
}
