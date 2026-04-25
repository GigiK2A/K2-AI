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
    res.setHeader('Location', '/newsletter-error.html')
    res.end()
    return
  }

  res.statusCode = 302
  res.setHeader('Location', '/newsletter-ok.html')
  res.end()
}
