import { Resend } from 'resend'
import { createClient as createSupabaseClient } from '@supabase/supabase-js'

function getEnvVar(name: string, fallbacks: string[] = []): string {
  for (const key of [name, ...fallbacks]) {
    const value = process.env[key]
    if (value) return value
  }
  return ''
}

function createSupabaseAdminClient() {
  const supabaseUrl = getEnvVar('NEXT_PUBLIC_SUPABASE_URL', ['SUPABASE_URL'])
  const serviceRoleKey = getEnvVar('SUPABASE_SERVICE_ROLE_KEY', ['SUPABASE_SERVICE_KEY', 'SUPABASE_KEY'])

  if (!supabaseUrl || !serviceRoleKey) {
    throw new Error('Missing Supabase newsletter env vars')
  }

  return createSupabaseClient(supabaseUrl, serviceRoleKey, {
    auth: { persistSession: false },
  })
}

function sendJson(res: any, status: number, payload: unknown) {
  res.statusCode = status
  res.setHeader('Content-Type', 'application/json; charset=utf-8')
  res.end(JSON.stringify(payload))
}

function escapeHtml(value: string): string {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function generateToken(): string {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return Array.from(array, b => b.toString(16).padStart(2, '0')).join('')
}

export default async function handler(req: any, res: any) {
  // CORS preflight
  res.setHeader('Access-Control-Allow-Origin', 'https://www.k2-ai.it')
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')

  if (req.method === 'OPTIONS') {
    res.statusCode = 204
    res.end()
    return
  }

  if (req.method !== 'POST') {
    return sendJson(res, 405, { error: 'Method not allowed' })
  }

  let body: Record<string, any> = {}
  try {
    if (req.body && typeof req.body === 'object') {
      body = req.body
    } else {
      const raw = typeof req.body === 'string' ? req.body : await new Promise<string>((resolve, reject) => {
        let data = ''
        req.on('data', (chunk: Buffer) => { data += chunk.toString() })
        req.on('end', () => resolve(data))
        req.on('error', reject)
      })
      body = raw ? JSON.parse(raw) : {}
    }
  } catch {
    return sendJson(res, 400, { error: 'Invalid JSON' })
  }

  const email = typeof body.email === 'string' ? body.email.trim().toLowerCase() : ''
  // Il workflow n8n corrente usa il campo "name" come destinatario Outlook.
  // Per compatibilita, nelle iscrizioni dal sito salviamo qui la mail.
  const recipientName = email
  const source = typeof body.source === 'string' ? body.source.trim().slice(0, 100) : 'website'

  if (!email || !isValidEmail(email)) {
    return sendJson(res, 400, { error: 'Email non valida' })
  }

  const supabase = createSupabaseAdminClient()

  // Check duplicate
  const { data: existing } = await supabase
    .from('newsletter_subscribers')
    .select('id, confirmed')
    .eq('email', email)
    .single()

  if (existing) {
    if (existing.confirmed) {
      return sendJson(res, 200, { ok: true, already: true })
    }
    // Resend confirmation if not yet confirmed
    const token = generateToken()
    await supabase
      .from('newsletter_subscribers')
      .update({ name: recipientName, confirm_token: token, updated_at: new Date().toISOString() })
      .eq('email', email)

    await sendConfirmationEmail(email, token)
    return sendJson(res, 200, { ok: true, resent: true })
  }

  const token = generateToken()
  const { error } = await supabase.from('newsletter_subscribers').insert({
    email,
    name: recipientName,
    confirmed: false,
    confirm_token: token,
    source,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  })

  if (error) {
    return sendJson(res, 500, { error: 'Errore salvataggio' })
  }

  await sendConfirmationEmail(email, token)
  return sendJson(res, 200, { ok: true })
}

async function sendConfirmationEmail(email: string, token: string) {
  const resendApiKey = getEnvVar('RESEND_API_KEY')
  if (!resendApiKey) return

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://www.k2-ai.it'
  const confirmUrl = `${siteUrl}/api/newsletter/confirm?token=${token}`

  const resend = new Resend(resendApiKey)
  await resend.emails.send({
    from: 'K2-AI <noreply@k2-ai.it>',
    to: [email],
    subject: 'Conferma iscrizione alla newsletter K2-AI',
    html: `
      <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto;color:#212529">
        <h2 style="margin-bottom:8px;color:#0d1117">Conferma la tua iscrizione</h2>
        <p>Hai richiesto di ricevere aggiornamenti da K2-AI su automazioni AI per PMI italiane.</p>
        <p>Clicca il pulsante per confermare:</p>
        <a href="${escapeHtml(confirmUrl)}"
           style="display:inline-block;margin:16px 0;padding:12px 24px;background:#0d1117;color:#fff;text-decoration:none;border-radius:6px;font-weight:600">
          Conferma iscrizione
        </a>
        <p style="font-size:13px;color:#6c757d">
          Se non hai fatto questa richiesta, ignora questa email.<br/>
          Il link scade tra 48 ore.
        </p>
        <hr style="border:none;border-top:1px solid #DEE2E6;margin:20px 0"/>
        <p style="font-size:11px;color:#adb5bd">K2A S.R.L.S. — P.IVA IT03655920548</p>
      </div>
    `,
  })
}
