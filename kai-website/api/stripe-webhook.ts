import Stripe from 'stripe'
import { createSupabaseAdminClient, ensurePost, sendJson } from './kbot/_shared'
import { getSystemEnvVar } from '../lib/env/system'

async function readRawBody(req: any): Promise<string> {
  if (typeof req.body === 'string') return req.body
  if (Buffer.isBuffer(req.body)) return req.body.toString('utf-8')

  const chunks: Uint8Array[] = []
  for await (const chunk of req) {
    chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk)
  }
  return Buffer.concat(chunks).toString('utf-8')
}

export default async function handler(req: any, res: any) {
  if (!ensurePost(req, res)) return

  try {
    const stripeSecret = getSystemEnvVar('STRIPE_SECRET_KEY') || process.env.STRIPE_SECRET_KEY
    const webhookSecret = getSystemEnvVar('STRIPE_WEBHOOK_SECRET') || process.env.STRIPE_WEBHOOK_SECRET
    if (!stripeSecret || !webhookSecret) {
      return sendJson(res, 500, { error: 'Missing STRIPE_SECRET_KEY or STRIPE_WEBHOOK_SECRET' })
    }
    const stripe = new Stripe(stripeSecret, { apiVersion: '2026-03-25.dahlia' })

    const signature = (req.headers['stripe-signature'] || req.headers['Stripe-Signature']) as string | undefined
    if (!signature) return sendJson(res, 400, { error: 'Missing stripe-signature header' })

    const body = await readRawBody(req)

    let event: ReturnType<typeof stripe.webhooks.constructEvent>
    try {
      event = stripe.webhooks.constructEvent(body, signature, webhookSecret)
    } catch {
      return sendJson(res, 400, { error: 'Invalid signature' })
    }

    if (event.type === 'checkout.session.completed') {
      const session = event.data.object as any
      const kbotSessionId = session.client_reference_id || session.metadata?.kbot_session_id

      if (!kbotSessionId) {
        console.error('Webhook Stripe: nessun client_reference_id/kbot_session_id trovato')
        return sendJson(res, 200, { ok: true })
      }

      const supabase = createSupabaseAdminClient()

      // Idempotenza: se PDF già generato, non rigenerare
      const { data: existingSession } = await supabase
        .from('kbot_sessions')
        .select('pdf_url, status, collected_data')
        .eq('id', kbotSessionId)
        .single()

      if (existingSession?.pdf_url || existingSession?.status === 'paid') {
        console.log(`Webhook Stripe: PDF già generato per sessione ${kbotSessionId}, skip.`)
        return sendJson(res, 200, { ok: true })
      }

      const email = session.customer_email || session.customer_details?.email || null

      await supabase
        .from('kbot_sessions')
        .update({
          stripe_session_id: session.id,
          email,
          paid_at: new Date().toISOString(),
        })
        .eq('id', kbotSessionId)

      // Idempotenza sulla tabella conversioni: inserisci solo se non esiste già
      const { count } = await supabase
        .from('kbot_conversions')
        .select('id', { count: 'exact', head: true })
        .eq('stripe_session_id', session.id)

      if (!count || count === 0) {
        await supabase.from('kbot_conversions').insert({
          session_id: kbotSessionId,
          type: 'path_a_paid',
          amount_eur: (session.amount_total || 0) / 100,
          stripe_session_id: session.id,
          email,
        })
      }

      const baseUrl =
        getSystemEnvVar('NEXT_PUBLIC_SITE_URL') ||
        process.env.NEXT_PUBLIC_SITE_URL ||
        `https://${req.headers.host}`
      const internalKey = getSystemEnvVar('INTERNAL_API_KEY') || process.env.INTERNAL_API_KEY || ''

      const pdfResp = await fetch(`${baseUrl}/api/kbot/generate-pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(internalKey ? { 'x-internal-key': internalKey } : {}),
        },
        body: JSON.stringify({ session_id: kbotSessionId }),
      })

      if (!pdfResp.ok) {
        const errText = await pdfResp.text().catch(() => '')
        console.error(`Webhook Stripe: errore generazione PDF [${pdfResp.status}]`, errText)
        // Salva flag di errore per debug
        await supabase
          .from('kbot_sessions')
          .update({ collected_data: { ...(existingSession?.collected_data || {}), pdf_error: `${pdfResp.status}: ${errText.slice(0, 200)}` } })
          .eq('id', kbotSessionId)
      } else {
        console.log(`Webhook Stripe: PDF generato con successo per sessione ${kbotSessionId}`)
      }
    }

    return sendJson(res, 200, { ok: true })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return sendJson(res, 500, { error: message })
  }
}
