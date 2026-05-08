import { createSupabaseAdminClient, sendJson } from './_shared'

export default async function handler(req: any, res: any) {
  if (req.method !== 'GET') return sendJson(res, 405, { error: 'Method not allowed' })

  const slug = String(req.query?.slug || '').trim()
  if (!slug) return sendJson(res, 400, { error: 'Missing slug' })

  const supabase = createSupabaseAdminClient()
  const { data, error } = await supabase
    .from('newsletter_issues')
    .select('slug,subject,preview_text,html,published_at')
    .eq('slug', slug)
    .single()

  if (error || !data) return sendJson(res, 404, { error: 'Not found' })

  return sendJson(res, 200, { ok: true, item: data })
}
