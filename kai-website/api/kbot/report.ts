import { parseJsonBody, sendJson } from './_shared'
import { buildKbotReport } from '../../lib/kbot/sessions'

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST')
    return sendJson(res, 405, { error: 'Method not allowed' })
  }

  try {
    const body = await parseJsonBody(req)
    const result = await buildKbotReport(body)
    return sendJson(res, 200, result)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    const status = message === 'Session not found' ? 404 : message.includes('obbligatorio') || message.includes('non valido') ? 400 : 500
    return sendJson(res, status, { error: message })
  }
}
