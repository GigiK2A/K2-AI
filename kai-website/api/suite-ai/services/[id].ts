import { sendJson } from '../../kbot/_shared'
import { getSuiteAiServiceById, toPublicService } from '../../../lib/kbot/services'

export default async function handler(req: any, res: any) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET')
    return sendJson(res, 405, { error: 'Method not allowed' })
  }

  const id =
    req.query?.id ||
    new URL(req.url || '/', `http://${req.headers?.host || 'localhost'}`).pathname.split('/').pop()

  const service = getSuiteAiServiceById(id)
  if (!service) return sendJson(res, 404, { error: 'Service not found' })

  return sendJson(res, 200, { service: toPublicService(service) })
}
