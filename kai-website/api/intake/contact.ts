import { Resend } from 'resend'
import { parseJsonBody, sendJson } from '../kbot/_shared'
import { getSystemEnvVar } from '../../lib/env/system'

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function clean(value: unknown, max = 3000): string {
  return String(value || '').trim().slice(0, max)
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST')
    return sendJson(res, 405, { error: 'Method not allowed' })
  }

  try {
    const body = await parseJsonBody(req)
    const name = clean(body.name, 100)
    const email = clean(body.email, 160)
    const companyRole = clean(body.company_role, 180)
    const sector = clean(body.sector, 80)
    const message = clean(body.message, 3000)
    const sourcePage = clean(body.source_page, 120) || 'contatti'
    const internalContext = clean(body.internal_context, 3000)
    const website = clean(body.website, 200)

    if (website) return sendJson(res, 200, { ok: true })
    if (!name || name.length < 2) return sendJson(res, 400, { detail: 'Nome non valido.' })
    if (!email || !isValidEmail(email)) return sendJson(res, 400, { detail: 'Email non valida.' })
    if (!message || message.length < 10) return sendJson(res, 400, { detail: 'Messaggio troppo corto.' })

    const resendApiKey = getSystemEnvVar('RESEND_API_KEY')
    const notifyEmail = process.env.KBOT_NOTIFY_EMAIL || process.env.CONTACT_NOTIFY_EMAIL || 'info@k2-ai.it'

    if (!resendApiKey) {
      return sendJson(res, 503, { detail: 'Servizio email non configurato.' })
    }

    const resend = new Resend(resendApiKey)
    await resend.emails.send({
      from: 'K2-AI Contatti <noreply@k2-ai.it>',
      to: [notifyEmail],
      replyTo: email,
      subject: `Nuova richiesta contatto — ${name}`,
      html: `
        <div style="font-family:Inter,Arial,sans-serif;max-width:700px;margin:0 auto;color:#1f2937">
          <h2 style="margin:0 0 12px">Nuova richiesta contatto</h2>
          <p style="margin:0 0 8px"><strong>Nome:</strong> ${escapeHtml(name)}</p>
          <p style="margin:0 0 8px"><strong>Email:</strong> ${escapeHtml(email)}</p>
          <p style="margin:0 0 8px"><strong>Azienda/Ruolo:</strong> ${escapeHtml(companyRole || '-')}</p>
          <p style="margin:0 0 8px"><strong>Settore:</strong> ${escapeHtml(sector || '-')}</p>
          <p style="margin:0 0 8px"><strong>Source:</strong> ${escapeHtml(sourcePage)}</p>
          <hr style="border:none;border-top:1px solid #e5e7eb;margin:14px 0" />
          <p style="white-space:pre-wrap;margin:0 0 12px">${escapeHtml(message)}</p>
          ${
            internalContext
              ? `<p style="white-space:pre-wrap;background:#f8fafc;border:1px solid #e5e7eb;border-radius:8px;padding:10px;margin:0"><strong>Contesto interno</strong>\n${escapeHtml(internalContext)}</p>`
              : ''
          }
        </div>
      `,
    })

    return sendJson(res, 200, { ok: true })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return sendJson(res, 500, { detail: message })
  }
}
