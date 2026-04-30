import { ensurePost, parseJsonBody, sendJson } from './_shared'
import { createKbotSession } from '../../lib/kbot/sessions'

export default async function handler(req: any, res: any) {
  if (!ensurePost(req, res)) return

  try {
    const body = await parseJsonBody(req)
    const session = await createKbotSession(body)
    return sendJson(res, 200, { session_id: session.id, session })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    const status = message.includes('obbligatorio') || message.includes('non valido') ? 400 : 500
    return sendJson(res, status, { error: message })
  }
}
