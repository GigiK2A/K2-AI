import { createClient as createSupabaseClient } from '@supabase/supabase-js'
import { Resend } from 'resend'

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

function escapeHtml(value: string): string {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

async function sendWelcomeEmail(email: string) {
  const resendApiKey = getEnvVar('RESEND_API_KEY')
  if (!resendApiKey) return

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://www.k2-ai.it'
  const resend = new Resend(resendApiKey)

  await resend.emails.send({
    from: 'K2-AI <noreply@k2-ai.it>',
    to: [email],
    subject: 'Iscrizione confermata alla newsletter K2-AI',
    html: `
      <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto;color:#212529">
        <h2 style="margin-bottom:8px;color:#0d1117">Iscrizione confermata</h2>
        <p>Sei dentro: da ora riceverai il briefing K2-AI con le novità più utili dal mondo dell'intelligenza artificiale.</p>
        <p>La newsletter è pensata per essere semplice: poche notizie, spiegate bene, con attenzione a creator, PMI e team operativi.</p>
        <a href="${escapeHtml(siteUrl)}/contatti"
           style="display:inline-block;margin:16px 0;padding:12px 24px;background:#0d1117;color:#fff;text-decoration:none;border-radius:6px;font-weight:600">
          Visita K2-AI
        </a>
        <hr style="border:none;border-top:1px solid #DEE2E6;margin:20px 0"/>
        <p style="font-size:11px;color:#adb5bd">K2A S.R.L.S. - P.IVA IT03655920548</p>
      </div>
    `,
  })
}

export default async function handler(req: any, res: any) {
  const url = new URL(req.url || '', `https://${req.headers?.host || 'www.k2-ai.it'}`)
  const token = url.searchParams.get('token') || ''

  if (!token || token.length < 32) {
    res.statusCode = 400
    res.setHeader('Content-Type', 'text/html; charset=utf-8')
    res.end('<html><body><p>Link non valido o scaduto.</p></body></html>')
    return
  }

  const supabase = createSupabaseAdminClient()

  const { data, error } = await supabase
    .from('newsletter_subscribers')
    .update({
      confirmed: true,
      confirmed_at: new Date().toISOString(),
      confirm_token: null,
      updated_at: new Date().toISOString(),
    })
    .eq('confirm_token', token)
    .eq('confirmed', false)
    .select('email')
    .single()

  if (error || !data) {
    res.statusCode = 302
    res.setHeader('Location', '/newsletter-error')
    res.end()
    return
  }

  await sendWelcomeEmail(data.email)

  res.statusCode = 302
  res.setHeader('Location', '/newsletter-ok')
  res.end()
}
