import { sendJson } from '../kbot/_shared'
import { getSuiteAiServices } from '../../lib/kbot/services'

export default async function handler(req: any, res: any) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET')
    return sendJson(res, 405, { error: 'Method not allowed' })
  }

  return sendJson(res, 200, { services: getSuiteAiServices() })
}
