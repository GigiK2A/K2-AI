import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { Resend } from 'resend'
import { SECTOR_LABELS } from '@/lib/skills/sectors.config'

const resend = new Resend(process.env.RESEND_API_KEY)

export async function POST(req: NextRequest) {
  try {
    const { session_id, email, disponibilita, nome } = await req.json()
    const supabase = createClient()

    if (!session_id || !email || !disponibilita) {
      return NextResponse.json({ error: 'session_id, email e disponibilita sono obbligatori' }, { status: 400 })
    }

    const { data: session } = await supabase
      .from('kbot_sessions')
      .select('*')
      .eq('id', session_id)
      .single()

    if (!session) return NextResponse.json({ error: 'Session not found' }, { status: 404 })

    await supabase
      .from('kbot_sessions')
      .update({ status: 'contacted', email, nome: nome || null, disponibilita })
      .eq('id', session_id)

    await supabase
      .from('kbot_conversions')
      .insert({ session_id, type: 'path_b_contact', email })

    const sectorLabel = SECTOR_LABELS[session.sector] || session.sector

    if (process.env.RESEND_API_KEY) {
      await resend.emails.send({
        from: 'K2-AI <noreply@k2-ai.it>',
        to: [email],
        cc: process.env.KBOT_NOTIFY_EMAIL ? [process.env.KBOT_NOTIFY_EMAIL] : undefined,
        subject: `Richiesta ricevuta — ${sectorLabel}`,
        html: `<p>Grazie, abbiamo ricevuto la tua richiesta dal K-BOT. Ti contattiamo entro 24 ore.</p>`,
      })
    }

    return NextResponse.json({ ok: true })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
