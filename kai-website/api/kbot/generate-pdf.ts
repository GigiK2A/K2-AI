import Anthropic from '@anthropic-ai/sdk'
import { Resend } from 'resend'
import {
  compactMessages,
  createSupabaseAdminClient,
  createAnthropicClient,
  ensurePost,
  escapeHtml,
  parseJsonBody,
  PDF_SYSTEM_MAX_CHARS,
  resolveSectorLabel,
  resolveSkillNames,
  sendJson,
} from './_shared'
import { loadSkillBundle } from '../../lib/skills/loader'
import { getSystemEnvVar } from '../../lib/env/system'

function buildFallbackAnalysis(session: any, sectorLabel: string, skillNames: string[]) {
  const teaserSignals = Array.isArray(session?.collected_data?.teaser?.segnali)
    ? session.collected_data.teaser.segnali
    : []
  const uploadedFiles = Array.isArray(session?.collected_data?.uploaded_files)
    ? session.collected_data.uploaded_files
    : []

  return {
    meta: {
      settore: sectorLabel,
      skill_attive: skillNames,
      data_generazione: new Date().toISOString(),
      versione_modello: 'fallback-local',
    },
    executive_summary:
      'Report generato in modalita fallback. Sono stati usati i dati raccolti in chat e gli allegati disponibili per produrre una diagnosi operativa preliminare.',
    sezioni: [
      {
        tipo: 'analisi_verticale',
        titolo: 'Contesto raccolto',
        contenuto:
          `Settore: ${sectorLabel}\n\n` +
          `Problema dichiarato: ${session?.collected_data?.problem_description || 'Non specificato'}\n\n` +
          `Path: ${session?.path || 'unknown'}`,
        elementi_visivi: [
          {
            tipo: 'tabella',
            titolo: 'Allegati ricevuti',
            dati: {
              colonne: ['File', 'Tipo', 'Dimensione'],
              righe: uploadedFiles.map((f: any) => [f.name || '-', f.type || '-', String(f.size || '-')]),
            },
          },
        ],
      },
      {
        tipo: 'benchmark',
        titolo: 'Segnali emersi',
        contenuto:
          teaserSignals.length > 0
            ? teaserSignals.map((s: any, i: number) => `${i + 1}. ${s.titolo || 'Segnale'} - ${s.sintesi || ''}`).join('\n')
            : 'Non sono presenti segnali teaser consolidati: serve una nuova elaborazione completa.',
        elementi_visivi: [],
      },
      {
        tipo: 'roadmap',
        titolo: 'Prossimi passi consigliati',
        contenuto:
          '1. Verifica qualita dati allegati\n2. Conferma obiettivo decisionale del report\n3. Esegui elaborazione completa con modello AI e benchmark settore',
        elementi_visivi: [],
      },
    ],
    automazioni_consigliate: [
      {
        area: 'Raccolta documentale',
        descrizione: 'Pipeline automatica ingestione e normalizzazione allegati bilancio',
        impatto_stimato: '2-4 ore/settimana risparmiate',
        complessita: 'media',
        orizzonte: '0-3 mesi',
      },
    ],
    prossimo_passo: {
      testo: 'Conferma i dati chiave mancanti per ricevere il report completo.',
      messaggio_precompilato: `Ciao K2-AI, vorrei completare la Diagnosi AI Operativa per il settore ${sectorLabel}.`,
    },
  }
}

export default async function handler(req: any, res: any) {
  if (!ensurePost(req, res)) return

  try {
    const payload = await parseJsonBody(req)
    const { session_id, test_mode } = payload
    const internalApiKey = getSystemEnvVar('INTERNAL_API_KEY')
    const incomingKey = (req.headers?.['x-internal-key'] || req.headers?.['X-Internal-Key']) as string | undefined
    const isTestMode = Boolean(test_mode)
    if (internalApiKey && incomingKey !== internalApiKey && !isTestMode) {
      return sendJson(res, 401, { error: 'Unauthorized' })
    }

    const resendApiKey = getSystemEnvVar('RESEND_API_KEY')
    const supabase = createSupabaseAdminClient()
    const anthropic = createAnthropicClient() as Anthropic

    const { data: session, error: sessionError } = await supabase
      .from('kbot_sessions')
      .select('*')
      .eq('id', session_id)
      .single()

    if (sessionError || !session) return sendJson(res, 404, { error: 'Not found' })

    // Blocca test_mode su sessioni già pagate
    if (isTestMode && session.status === 'paid') {
      return sendJson(res, 403, { error: 'Non disponibile: sessione già acquistata.' })
    }
    // Idempotenza: se PDF già esiste e non siamo in test_mode, restituisci URL esistente
    if (session.pdf_url && !isTestMode) {
      return sendJson(res, 200, { pdf_url: session.pdf_url, cached: true })
    }

    const skillNames = resolveSkillNames(session.sector)
    const systemPrompt = loadSkillBundle(skillNames, {
      maxTotalChars: PDF_SYSTEM_MAX_CHARS,
      maxPerSkillChars: 30000,
      includeReferences: true,
    })
    const compactConversation = compactMessages(
      ((session.messages || []) as Array<{ role: 'user' | 'assistant'; content: string }>),
      24,
      2600,
    )

    const userPrompt = `
Produci l'ANALISI COMPLETA JSON per il PDF della Diagnosi AI Operativa.

SETTORE: ${resolveSectorLabel(session.sector)}
DATI RACCOLTI: ${JSON.stringify(session.collected_data || {}, null, 2)}
CONVERSAZIONE: ${compactConversation.map((m: any) => `${m.role}: ${m.content}`).join('\n')}

Il JSON deve seguire ESATTAMENTE lo schema definito nella skill diagnosi-ai-operativa-pmi
(sezione "Formato ANALISI COMPLETA"). Includi almeno:
- 3 sezioni di analisi verticale con elementi visivi (tabelle + 1 grafico barre + 1 gauge)
- 3-4 automazioni consigliate con stime concrete
- Executive summary dettagliato (5-6 righe)

Produci SOLO il JSON valido. Niente testo fuori dal JSON.
`

    let analysisJson: any
    try {
      const response = await anthropic.messages.create({
        model: 'claude-sonnet-4-6',
        max_tokens: 4096,
        system: systemPrompt,
        messages: [{ role: 'user', content: userPrompt }],
      })

      const rawText = response.content[0]?.type === 'text' ? response.content[0].text : '{}'
      analysisJson = JSON.parse(rawText.replace(/```json\n?|\n?```/g, '').trim())
    } catch {
      analysisJson = buildFallbackAnalysis(session, resolveSectorLabel(session.sector), skillNames)
    }

    const pdfRuntime = (await import('../../lib/pdf/generator.js')) as any
    const generatePdfFn =
      pdfRuntime.generateDiagnosiPDF || pdfRuntime.default?.generateDiagnosiPDF
    if (typeof generatePdfFn !== 'function') {
      return sendJson(res, 500, { error: 'generateDiagnosiPDF non disponibile' })
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

    if (uploadError) return sendJson(res, 500, { error: `Upload PDF fallito: ${uploadError.message}` })

    const { data: publicData } = supabase.storage
      .from(REPORTS_BUCKET)
      .getPublicUrl(fileName)

    const publicUrl = publicData.publicUrl

    await supabase
      .from('kbot_sessions')
      .update({ status: 'paid', pdf_url: publicUrl, paid_at: new Date().toISOString() })
      .eq('id', session_id)

    if (session.email) {
      const resend = resendApiKey ? new Resend(resendApiKey) : null
      if (!resend) return sendJson(res, 200, { pdf_url: publicUrl, warning: 'RESEND_API_KEY mancante: email non inviata' })

      await resend.emails.send({
        from: 'K2-AI <noreply@k2-ai.it>',
        to: [session.email],
        cc: process.env.KBOT_NOTIFY_EMAIL ? [process.env.KBOT_NOTIFY_EMAIL] : undefined,
        subject: `La tua Diagnosi AI Operativa - ${resolveSectorLabel(session.sector)}`,
        html: buildEmailHtml(resolveSectorLabel(session.sector), publicUrl),
        attachments: [{
          filename: `Diagnosi-K2-AI-${resolveSectorLabel(session.sector)}.pdf`,
          content: pdfBuffer.toString('base64'),
        }],
      })
    }

    return sendJson(res, 200, { pdf_url: publicUrl })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return sendJson(res, 500, { error: message })
  }
}

function buildEmailHtml(sectorLabelRaw: string, pdfUrlRaw: string): string {
  const sectorLabel = escapeHtml(sectorLabelRaw)
  const pdfUrl = escapeHtml(pdfUrlRaw)
  return `
    <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto;color:#212529">
      <div style="background:#1A1F36;padding:32px;border-radius:8px 8px 0 0">
        <p style="color:#A5B4FC;font-size:12px;margin:0">K2-AI · Diagnosi AI Operativa</p>
        <h1 style="color:#fff;font-size:22px;margin:8px 0 0">Il tuo report è qui</h1>
      </div>
      <div style="padding:32px;border:1px solid #DEE2E6;border-top:none;border-radius:0 0 8px 8px">
        <p>Ciao,</p>
        <p>la tua Diagnosi AI Operativa per il settore <strong>${sectorLabel}</strong> è allegata a questa email.</p>
        <p>Il PDF contiene l'analisi specializzata basata sulle skill K2-AI e un orientamento su cosa vale la pena automatizzare nella tua situazione.</p>
        <a href="${pdfUrl}" style="display:inline-block;background:#3B5BDB;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;margin:16px 0">Apri il report →</a>
        <hr style="border:none;border-top:1px solid #DEE2E6;margin:24px 0">
        <p style="font-size:13px;color:#868E96">Vuoi approfondire le opportunità emerse? <a href="https://k2-ai.it/contatti" style="color:#3B5BDB">Contattaci</a> — il form è già pre-compilato con la tua situazione.</p>
      </div>
    </div>
  `
}
