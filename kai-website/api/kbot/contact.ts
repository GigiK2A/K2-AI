import { Resend } from 'resend'
import { ensurePost, parseJsonBody, createSupabaseAdminClient, sendJson, resolveSectorLabel, escapeHtml } from './_shared'
import { getSystemEnvVar } from '../../lib/env/system'

export default async function handler(req: any, res: any) {
  if (!ensurePost(req, res)) return

  // ENDPOINT DISMESSO — fail-closed.
  // La produzione (Railway/Docker) non spedisce affatto `api/`: server.js proxa
  // ogni /api/kbot/* al backend FastAPI, che questo endpoint non ce l'ha. Il file
  // resta però pubblicabile come serverless function da qualsiasi deploy Vercel
  // del progetto (i .vercel/project.json sono ancora tracciati), e senza auth
  // consegnerebbe gli ultimi 10 messaggi di UNA SESSIONE QUALSIASI a un indirizzo
  // scelto dal chiamante, da noreply@k2-ai.it (SPF/DKIM validi): esfiltrazione +
  // relay di phishing. Se serve di nuovo, va riscritto con JWT Supabase +
  // verifica di session.user_id e destinatario preso dalla sessione, non dal body.
  return sendJson(res, 410, { error: 'endpoint dismesso' })

  // eslint-disable-next-line no-unreachable
  try {
    const { session_id, email, disponibilita, nome } = await parseJsonBody(req)
    const resendApiKey = getSystemEnvVar('RESEND_API_KEY')

    if (!session_id) {
      return sendJson(res, 400, { error: 'session_id obbligatorio' })
    }

    const supabase = createSupabaseAdminClient()

    const { data: session, error: sessionError } = await supabase
      .from('kbot_sessions')
      .select('*')
      .eq('id', session_id)
      .single()

    if (sessionError || !session) {
      return sendJson(res, 404, { error: 'Session not found' })
    }

    const safeEmail = typeof email === 'string' && email.trim() ? email.trim() : null
    const safeDisponibilita = typeof disponibilita === 'string' && disponibilita.trim() ? disponibilita.trim() : null
    const safeNome = typeof nome === 'string' && nome.trim() ? nome.trim() : null

    const nowIso = new Date().toISOString()
    const updatedCollectedData = {
      ...(session.collected_data || {}),
      contact_email: safeEmail,
      contact_disponibilita: safeDisponibilita,
      contact_nome: safeNome || '',
    }

    await supabase
      .from('kbot_sessions')
      .update({
        status: 'contacted',
        email: safeEmail || session.email || null,
        nome: safeNome || null,
        disponibilita: safeDisponibilita || null,
        collected_data: updatedCollectedData,
        updated_at: nowIso,
      })
      .eq('id', session_id)

    const { count: existingContact } = await supabase
      .from('kbot_conversions')
      .select('id', { count: 'exact', head: true })
      .eq('session_id', session_id)
      .eq('type', 'path_b_contact')

    if (!existingContact || existingContact === 0) {
      await supabase
        .from('kbot_conversions')
        .insert({
          session_id,
          type: 'path_b_contact',
          email: safeEmail,
          amount_eur: null,
        })
    }

    const sectorLabel = resolveSectorLabel(session.sector)

    if (resendApiKey && safeEmail) {
      const resend = new Resend(resendApiKey)
      const messages = Array.isArray(session.messages) ? session.messages : []
      const shortChat = messages
        .slice(-10)
        .map((m: any) => `${m.role}: ${String(m.content || '').slice(0, 500)}`)
        .join('\n')

      await resend.emails.send({
        from: 'K2-AI <noreply@k2-ai.it>',
        to: [safeEmail],
        cc: process.env.KBOT_NOTIFY_EMAIL ? [process.env.KBOT_NOTIFY_EMAIL] : undefined,
        subject: `Richiesta ricevuta — ${sectorLabel}`,
        html: `
          <div style="font-family:Inter,sans-serif;max-width:620px;margin:0 auto;color:#212529">
            <h2 style="margin-bottom:8px">Richiesta ricevuta</h2>
            <p>Grazie, abbiamo ricevuto la tua richiesta dal K-BOT.</p>
            <p><strong>Settore:</strong> ${escapeHtml(sectorLabel)}<br/>
               <strong>Disponibilità:</strong> ${escapeHtml(safeDisponibilita || 'Da concordare')}</p>
            <p>Ti rispondiamo con una proposta di slot call entro 24 ore.</p>
            <hr style="border:none;border-top:1px solid #DEE2E6;margin:20px 0"/>
            <p style="font-size:12px;color:#6c757d">Sessione: ${escapeHtml(session_id)}</p>
            <pre style="white-space:pre-wrap;background:#F8F9FA;padding:12px;border-radius:6px;font-size:12px">${escapeHtml(shortChat)}</pre>
          </div>
        `,
      })
    }

    return sendJson(res, 200, { ok: true })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return sendJson(res, 500, { error: message })
  }
}
