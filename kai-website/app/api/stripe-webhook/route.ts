import { NextRequest, NextResponse } from 'next/server'
import Stripe from 'stripe'
import { createClient } from '@/lib/supabase/server'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: '2024-06-20' })

export async function POST(req: NextRequest) {
  const body = await req.text()
  const signature = req.headers.get('stripe-signature') || ''

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(body, signature, process.env.STRIPE_WEBHOOK_SECRET!)
  } catch {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
  }

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object as Stripe.Checkout.Session
    const kbotSessionId = session.client_reference_id || session.metadata?.kbot_session_id

    if (!kbotSessionId) {
      console.error('Webhook: nessun kbot_session_id/client_reference_id trovato in Stripe')
      return NextResponse.json({ ok: true })
    }

    const supabase = createClient()
    const email = session.customer_email || session.customer_details?.email || null

    await supabase
      .from('kbot_sessions')
      .update({
        stripe_session_id: session.id,
        email,
        paid_at: new Date().toISOString(),
      })
      .eq('id', kbotSessionId)

    await supabase.from('kbot_conversions').insert({
      session_id: kbotSessionId,
      type: 'path_a_paid',
      amount_eur: (session.amount_total || 0) / 100,
      stripe_session_id: session.id,
      email,
    })

    const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://k2-ai.it'
    await fetch(`${baseUrl}/api/kbot/generate-pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-internal-key': process.env.INTERNAL_API_KEY || '',
      },
      body: JSON.stringify({ session_id: kbotSessionId }),
    })
  }

  return NextResponse.json({ ok: true })
}

export const config = { api: { bodyParser: false } }

