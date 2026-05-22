import Stripe from 'stripe'
import {
  ensurePost,
  parseJsonBody,
  createSupabaseAdminClient,
  sendJson,
  resolveSectorLabel,
} from './_shared'
import { getSystemEnvVar } from '../../lib/env/system'

export default async function handler(req: any, res: any) {
  if (!ensurePost(req, res)) return

  try {
    const { session_id, email: emailFromForm } = await parseJsonBody(req)
    if (!session_id) return sendJson(res, 400, { error: 'session_id obbligatorio' })

    const stripeSecretKey = getSystemEnvVar('STRIPE_SECRET_KEY')
    if (!stripeSecretKey) return sendJson(res, 500, { error: 'Stripe non configurato: STRIPE_SECRET_KEY mancante' })

    const supabase = createSupabaseAdminClient()
    const { data: session, error } = await supabase
      .from('kbot_sessions')
      .select('sector, email, path, status')
      .eq('id', session_id)
      .single()

    if (error || !session) return sendJson(res, 404, { error: 'Session not found' })
    if (session.status === 'paid') return sendJson(res, 409, { error: 'Sessione già pagata' })

    // Salva email raccolta nel form PaymentBox (lead anche se non completa il pagamento)
    const resolvedEmail = emailFromForm?.trim() || session.email || undefined
    if (resolvedEmail && resolvedEmail !== session.email) {
      await supabase.from('kbot_sessions').update({ email: resolvedEmail }).eq('id', session_id)
    }

    const stripe = new Stripe(stripeSecretKey, { apiVersion: '2026-03-25.dahlia' })
    const siteUrl = (getSystemEnvVar('NEXT_PUBLIC_SITE_URL') || 'https://www.k2-ai.it').replace(/\/$/, '')
    const sectorLabel = resolveSectorLabel(session.sector)

    const checkoutSession = await stripe.checkout.sessions.create({
      mode: 'payment',
      client_reference_id: session_id,
      metadata: { kbot_session_id: session_id },
      customer_email: resolvedEmail,
      line_items: [
        {
          price_data: {
            currency: 'eur',
            unit_amount: 1900,
            product_data: {
              name: `Diagnosi AI Operativa — ${sectorLabel}`,
              description: "Piano d'azione operativo 7 pagine con priorità, tempi e template pronti. Consegna in 10 minuti via email.",
            },
          },
          quantity: 1,
        },
      ],
      payment_method_types: ['card'],
      success_url: `${siteUrl}/k-bot/grazie?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${siteUrl}/k-bot?cancelled=1`,
    })

    if (!checkoutSession.url) return sendJson(res, 500, { error: 'Stripe non ha restituito checkout URL' })

    return sendJson(res, 200, { checkout_url: checkoutSession.url })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return sendJson(res, 500, { error: message })
  }
}
