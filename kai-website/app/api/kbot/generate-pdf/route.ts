import { NextRequest, NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'
import { Resend } from 'resend'
import { createClient } from '@/lib/supabase/server'
import { loadSkillBundle } from '@/lib/skills/loader'
import { SECTOR_BUNDLES, SECTOR_LABELS } from '@/lib/skills/sectors.config'
import { getAnthropicApiKey } from '@/lib/env/system'

const resend = new Resend(process.env.RESEND_API_KEY)

export async function POST(req: NextRequest) {
  try {
    const payload = await req.json()
    const { session_id, test_mode } = payload
    const internalApiKey = process.env.INTERNAL_API_KEY
    if (internalApiKey) {
      const incomingKey = req.headers.get('x-internal-key')
      if (incomingKey !== internalApiKey && !Boolean(test_mode)) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
      }
    }
    const supabase = createClient()

    const { data: session } = await supabase
      .from('kbot_sessions')
      .select('*')
      .eq('id', session_id)
      .single()

    if (!session) return NextResponse.json({ error: 'Not found' }, { status: 404 })

    const skillNames = SECTOR_BUNDLES[session.sector] || ['diagnosi-ai-operativa-pmi']
    const systemPrompt = loadSkillBundle(skillNames)
    const anthropic = new Anthropic({ apiKey: getAnthropicApiKey() })

    const userPrompt = `
Produci l'ANALISI COMPLETA JSON per il PDF della Diagnosi AI Operativa.

SETTORE: ${SECTOR_LABELS[session.sector] || session.sector}
DATI RACCOLTI: ${JSON.stringify(session.collected_data || {}, null, 2)}
CONVERSAZIONE: ${(session.messages || []).map((m: any) => `${m.role}: ${m.content}`).join('\n')}

Il JSON deve seguire ESATTAMENTE lo schema definito nella skill diagnosi-ai-operativa-pmi
(sezione "Formato ANALISI COMPLETA"). Includi almeno:
- 3 sezioni di analisi verticale con elementi visivi (tabelle + 1 grafico barre + 1 gauge)
- 3-4 automazioni consigliate con stime concrete
- Executive summary dettagliato (5-6 righe)

Produci SOLO il JSON valido. Niente testo fuori dal JSON.
`

    const response = await anthropic.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 4096,
      system: systemPrompt,
      messages: [{ role: 'user', content: userPrompt }],
    })

    const rawText = response.content[0]?.type === 'text' ? response.content[0].text : '{}'
    const analysisJson = JSON.parse(rawText.replace(/```json\n?|\n?```/g, '').trim())

    const pdfRuntime = (await import('@/lib/pdf/generator.js')) as any
    const generatePdfFn =
      pdfRuntime.generateDiagnosiPDF || pdfRuntime.default?.generateDiagnosiPDF
    if (typeof generatePdfFn !== 'function') {
      return NextResponse.json({ error: 'generateDiagnosiPDF non disponibile' }, { status: 500 })
    }
    const pdfBuffer = await generatePdfFn(analysisJson)

    const REPORTS_BUCKET = 'kbot-reports'
    const fileName = `kbot-${session_id}-${Date.now()}.pdf`
    let { error: uploadError } = await supabase.storage
      .from(REPORTS_BUCKET)
      .upload(fileName, pdfBuffer, { contentType: 'application/pdf', upsert: true })

    if (uploadError?.message?.toLowerCase().includes('bucket not found')) {
      await supabase.storage.createBucket(REPORTS_BUCKET, { public: true })
      const retry = await supabase.storage
        .from(REPORTS_BUCKET)
        .upload(fileName, pdfBuffer, { contentType: 'application/pdf', upsert: true })
      uploadError = retry.error
    }

    if (uploadError) return NextResponse.json({ error: `Upload PDF fallito: ${uploadError.message}` }, { status: 500 })

    const { data: publicData } = supabase.storage
      .from(REPORTS_BUCKET)
      .getPublicUrl(fileName)

    const publicUrl = publicData.publicUrl

    await supabase
      .from('kbot_sessions')
      .update({ status: 'paid', pdf_url: publicUrl, paid_at: new Date().toISOString() })
      .eq('id', session_id)

    if (session.email) {
      await resend.emails.send({
        from: 'K2-AI <noreply@k2-ai.it>',
        to: [session.email],
        cc: process.env.KBOT_NOTIFY_EMAIL ? [process.env.KBOT_NOTIFY_EMAIL] : undefined,
        subject: `La tua Diagnosi AI Operativa - ${SECTOR_LABELS[session.sector] || session.sector}`,
        html: buildEmailHtml(session, publicUrl),
        attachments: [{
          filename: `Diagnosi-K2-AI-${SECTOR_LABELS[session.sector] || session.sector}.pdf`,
          content: pdfBuffer.toString('base64'),
        }],
      })
    }

    return NextResponse.json({ pdf_url: publicUrl })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}

function buildEmailHtml(session: any, pdfUrl: string): string {
  return `
    <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto;color:#212529">
      <div style="background:#1A1F36;padding:32px;border-radius:8px 8px 0 0">
        <p style="color:#A5B4FC;font-size:12px;margin:0">K2-AI · Diagnosi AI Operativa</p>
        <h1 style="color:#fff;font-size:22px;margin:8px 0 0">Il tuo report è qui</h1>
      </div>
      <div style="padding:32px;border:1px solid #DEE2E6;border-top:none;border-radius:0 0 8px 8px">
        <p>Ciao,</p>
        <p>la tua Diagnosi AI Operativa per il settore <strong>${SECTOR_LABELS[session.sector] || session.sector}</strong>
           è allegata a questa email.</p>
        <p>Il PDF contiene l'analisi specializzata basata sulle skill K2-AI e un orientamento
           su cosa vale la pena automatizzare nella tua situazione.</p>
        <a href="${pdfUrl}" style="display:inline-block;background:#3B5BDB;color:#fff;
           padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;margin:16px 0">
          Apri il report →
        </a>
        <hr style="border:none;border-top:1px solid #DEE2E6;margin:24px 0">
        <p style="font-size:13px;color:#868E96">
          Vuoi approfondire le opportunità emerse?
          <a href="https://k2-ai.it/contatti" style="color:#3B5BDB">Contattaci</a> —
          il form è già pre-compilato con la tua situazione.
        </p>
      </div>
    </div>
  `
}
