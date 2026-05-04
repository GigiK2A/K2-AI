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
  resolveSkillNamesForSession,
  sendJson,
} from './_shared'
import { loadSkillBundle } from '../../lib/skills/loader'
import { getSystemEnvVar } from '../../lib/env/system'

function extractJsonRobust(raw: string): any {
  const cleaned = raw.replace(/```json\n?/g, '').replace(/\n?```/g, '').trim()
  try { return JSON.parse(cleaned) } catch {}
  const start = cleaned.indexOf('{')
  const end = cleaned.lastIndexOf('}')
  if (start !== -1 && end > start) {
    try { return JSON.parse(cleaned.slice(start, end + 1)) } catch {}
  }
  throw new Error('No valid JSON in response')
}

function buildFileExtracts(session: any): string {
  const uploadedFiles = Array.isArray(session?.collected_data?.uploaded_files)
    ? session.collected_data.uploaded_files : []
  if (uploadedFiles.length === 0) return ''
  const parts = uploadedFiles.map((f: any) => {
    const text = String(f.extractedText || f.extractedSummary || '').slice(0, 12000)
    return text ? `### ${f.name}\n${text}` : `### ${f.name}\n(Contenuto non estraibile)`
  })
  return `\n\nMATERIALE ALLEGATO:\n${parts.join('\n\n---\n\n')}`
}

function buildFallbackAnalysis(session: any, sectorLabel: string, skillNames: string[]) {
  const teaserSignals = Array.isArray(session?.collected_data?.teaser?.segnali)
    ? session.collected_data.teaser.segnali : []
  const uploadedFiles = Array.isArray(session?.collected_data?.uploaded_files)
    ? session.collected_data.uploaded_files : []
  const problem = session?.collected_data?.problem_description || ''

  const fileContents = uploadedFiles
    .map((f: any) => {
      const text = String(f.extractedText || f.extractedSummary || '').slice(0, 4000)
      return text ? `**${f.name}**\n${text}` : null
    })
    .filter(Boolean)
    .join('\n\n')

  const segnaliContent = teaserSignals.length > 0
    ? teaserSignals.map((s: any, i: number) =>
        `**${i + 1}. ${s.titolo || 'Segnale'}** (${s.priorita || 'rilevante'})\n${s.sintesi || ''}`
      ).join('\n\n')
    : 'Segnali non disponibili: è necessaria una nuova elaborazione con il modello AI.'

  return {
    meta: {
      settore: sectorLabel,
      skill_attive: skillNames,
      data_generazione: new Date().toISOString(),
      versione_modello: 'fallback-local',
    },
    executive_summary: problem
      ? `Diagnosi per: ${sectorLabel}. Problema dichiarato: ${problem.slice(0, 400)}`
      : `Diagnosi per: ${sectorLabel}. Analisi basata sul materiale allegato.`,
    sezioni: [
      {
        tipo: 'analisi_verticale',
        titolo: 'Contesto e materiale analizzato',
        contenuto: [
          problem && `**Problema dichiarato:**\n${problem}`,
          fileContents && `**Contenuto allegati:**\n${fileContents}`,
        ].filter(Boolean).join('\n\n') || 'Nessun dato disponibile.',
        elementi_visivi: uploadedFiles.length > 0 ? [{
          tipo: 'tabella',
          titolo: 'Allegati ricevuti',
          dati: {
            colonne: ['File', 'Tipo'],
            righe: uploadedFiles.map((f: any) => [f.name || '-', f.type || '-']),
          },
        }] : [],
      },
      {
        tipo: 'benchmark',
        titolo: 'Segnali principali emersi',
        contenuto: segnaliContent,
        elementi_visivi: [],
      },
      {
        tipo: 'roadmap',
        titolo: 'Priorità operative',
        contenuto: '1. Consolidare i dati chiave mancanti\n2. Identificare le cause strutturali dei segnali emersi\n3. Definire le azioni prioritarie a 90 giorni con il team K2-AI',
        elementi_visivi: [],
      },
    ],
    automazioni_consigliate: [
      {
        area: 'Raccolta e analisi documentale',
        descrizione: 'Pipeline AI per ingestione, lettura e sintesi automatica dei documenti aziendali',
        impatto_stimato: '3-5 ore/settimana risparmiate',
        complessita: 'media',
        orizzonte: '0-3 mesi',
      },
    ],
    prossimo_passo: {
      testo: 'Contatta il team K2-AI per approfondire i segnali emersi e definire il piano operativo.',
      messaggio_precompilato: `Ciao K2-AI, ho ricevuto la diagnosi per ${sectorLabel} e vorrei approfondire i risultati.`,
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

    const skillNames = resolveSkillNamesForSession(session)
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
    const fileExtracts = buildFileExtracts(session)
    const sectorLabel = resolveSectorLabel(session.sector)

    const userPrompt = `
Produci l'ANALISI COMPLETA JSON per il PDF della Diagnosi AI Operativa.

SETTORE: ${sectorLabel}
SKILL ATTIVE: ${skillNames.join(', ')}
PROBLEMA DICHIARATO: ${session?.collected_data?.problem_description || 'non specificato'}
${fileExtracts}

CONVERSAZIONE:
${compactConversation.map((m: any) => `${m.role}: ${m.content}`).join('\n')}

SCHEMA OBBLIGATORIO (produci SOLO questo JSON, niente altro):
{
  "meta": { "settore": "...", "skill_attive": [...], "data_generazione": "ISO", "versione_modello": "claude-sonnet-4-6" },
  "executive_summary": "3-4 righe: situazione attuale, problema principale, opportunità principale.",
  "sezioni": [
    {
      "tipo": "analisi_verticale",
      "titolo": "...",
      "contenuto": "testo dettagliato in italiano, cita numeri e dati dal materiale allegato",
      "elementi_visivi": [{ "tipo": "tabella|grafico_barre|gauge", "titolo": "...", "dati": {} }]
    }
  ],
  "automazioni_consigliate": [
    { "area": "...", "descrizione": "...", "impatto_stimato": "X ore/settimana", "complessita": "bassa|media|alta", "orizzonte": "0-3 mesi|3-6 mesi" }
  ],
  "prossimo_passo": { "testo": "CTA verso call K2-AI", "messaggio_precompilato": "..." }
}

Includi almeno 3 sezioni analisi verticale basate sul materiale allegato, 3-4 automazioni con stime concrete.
Produci SOLO il JSON valido, senza markdown attorno.
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
      analysisJson = extractJsonRobust(rawText)
    } catch {
      analysisJson = buildFallbackAnalysis(session, sectorLabel, skillNames)
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

    // test_mode: store pdf_url but don't mark as paid (preserves real checkout flow)
    await supabase
      .from('kbot_sessions')
      .update(isTestMode
        ? { pdf_url: publicUrl, updated_at: new Date().toISOString() }
        : { status: 'paid', pdf_url: publicUrl, paid_at: new Date().toISOString() },
      )
      .eq('id', session_id)

    if (!isTestMode && session.email) {
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
