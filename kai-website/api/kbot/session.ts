import { createSupabaseAdminClient, ensurePost, parseJsonBody, sendJson } from './_shared'
import { SECTOR_BUNDLES, CONTENT_TYPE_BUNDLES } from '../../lib/skills/sectors.config'

const VALID_SECTORS = new Set(Object.keys(SECTOR_BUNDLES))
const VALID_CONTENT_TYPES = new Set(Object.keys(CONTENT_TYPE_BUNDLES))

export default async function handler(req: any, res: any) {
  if (!ensurePost(req, res)) return

  try {
    const supabase = createSupabaseAdminClient()
    const { sector, content_type, mode } = await parseJsonBody(req)

    if (!sector || !VALID_SECTORS.has(String(sector))) {
      return sendJson(res, 400, { error: 'Settore non valido.' })
    }

    const validContentType = content_type && VALID_CONTENT_TYPES.has(String(content_type))
      ? String(content_type) : null

    const { data, error } = await supabase
      .from('kbot_sessions')
      .insert({
        sector,
        status: 'active',
        messages: [],
        path: 'unknown',
        step: 1,
        collected_data: validContentType ? { content_type: validContentType } : {},
        ...(mode ? { mode } : {}),
      })
      .select('id')
      .single()

    if (error) return sendJson(res, 500, { error: error.message })
    return sendJson(res, 200, { session_id: data.id })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return sendJson(res, 500, { error: message })
  }
}
