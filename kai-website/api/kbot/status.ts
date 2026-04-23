import { createSupabaseAdminClient, sendJson } from './_shared'

export default async function handler(req: any, res: any) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET')
    return sendJson(res, 405, { error: 'Method not allowed' })
  }

  const sessionId =
    req.query?.id ||
    new URL(req.url || '/', `http://${req.headers?.host || 'localhost'}`).searchParams.get('id')

  if (!sessionId) return sendJson(res, 400, { error: 'id obbligatorio' })

  try {
    const supabase = createSupabaseAdminClient()
    const { data, error } = await supabase
      .from('kbot_sessions')
      .select('status, pdf_url')
      .eq('id', String(sessionId))
      .single()

    if (error || !data) return sendJson(res, 404, { error: 'Session not found' })

    return sendJson(res, 200, {
      status: data.status,
      pdf_url: data.pdf_url || null,
    })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return sendJson(res, 500, { error: message })
  }
}
