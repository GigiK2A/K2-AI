import { createClient as createSupabaseClient } from '@supabase/supabase-js'
import Anthropic from '@anthropic-ai/sdk'
import { loadSkillBundle } from '../../lib/skills/loader'
import {
  SECTOR_BUNDLES,
  SECTOR_LABELS,
  CONTENT_TYPE_BUNDLES,
  PATH_A_KEYWORDS,
  PATH_B_KEYWORDS,
} from '../../lib/skills/sectors.config'
import { getAnthropicApiKey, getSystemEnvVar } from '../../lib/env/system'
import { SUITE_AI_SERVICES } from '../../src/data/suiteAiServices'

const SERVICE_SKILLS_MAP: Record<string, string[]> = Object.fromEntries(
  SUITE_AI_SERVICES.map(s => [s.id, s.skills]),
)
export const VALID_SERVICE_IDS = new Set(SUITE_AI_SERVICES.map(s => s.id))

export const MODEL = 'claude-haiku-4-5-20251001'
export const CHAT_SYSTEM_MAX_CHARS = 26000
export const TEASER_SYSTEM_MAX_CHARS = 110000
export const PDF_SYSTEM_MAX_CHARS = 140000
export const MAX_HISTORY_MESSAGES = 12
export const MAX_MESSAGE_CHARS = 900

export type KbotPath = 'A' | 'B' | 'unknown'
export type SessionData = Record<string, any>
export type ChatMessage = { role: 'user' | 'assistant'; content: string; ts?: string }

export function createSupabaseAdminClient() {
  const supabaseUrl =
    getSystemEnvVar('NEXT_PUBLIC_SUPABASE_URL', ['SUPABASE_URL']) ||
    process.env.NEXT_PUBLIC_SUPABASE_URL ||
    process.env.SUPABASE_URL

  const serviceRoleKey =
    getSystemEnvVar('SUPABASE_SERVICE_ROLE_KEY', ['SUPABASE_SERVICE_KEY', 'SUPABASE_KEY']) ||
    process.env.SUPABASE_SERVICE_ROLE_KEY

  if (!supabaseUrl || !serviceRoleKey) {
    throw new Error(
      'Missing Supabase env vars: NEXT_PUBLIC_SUPABASE_URL/SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_SERVICE_KEY) are required',
    )
  }

  return createSupabaseClient(supabaseUrl, serviceRoleKey, {
    auth: { persistSession: false },
  })
}

export function createAnthropicClient() {
  return new Anthropic({ apiKey: getAnthropicApiKey() })
}

export async function parseJsonBody(req: any): Promise<Record<string, any>> {
  if (req.body && typeof req.body === 'object') return req.body

  if (typeof req.body === 'string') {
    try {
      return JSON.parse(req.body)
    } catch {
      return {}
    }
  }

  const chunks: Uint8Array[] = []
  for await (const chunk of req) {
    chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk)
  }

  if (chunks.length === 0) return {}

  const raw = Buffer.concat(chunks).toString('utf-8')
  if (!raw) return {}

  try {
    return JSON.parse(raw)
  } catch {
    return {}
  }
}

export function sendJson(res: any, status: number, payload: unknown) {
  res.statusCode = status
  res.setHeader('Content-Type', 'application/json; charset=utf-8')
  res.end(JSON.stringify(payload))
}

export function ensurePost(req: any, res: any): boolean {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST')
    sendJson(res, 405, { error: 'Method not allowed' })
    return false
  }
  return true
}

export function detectPath(routerAnswer: string, problemDescription: string): 'A' | 'B' {
  const text = `${routerAnswer} ${problemDescription}`.toLowerCase()

  let scoreA = PATH_A_KEYWORDS.filter(kw => text.includes(kw)).length
  let scoreB = PATH_B_KEYWORDS.filter(kw => text.includes(kw)).length

  if (/caso singolo|singolo|uno specifico|una cosa|un problema/.test(text)) scoreA += 3
  if (/progetto|ampio|tutto|intero|sistema|riorganiz/.test(text)) scoreB += 3

  return scoreB > scoreA ? 'B' : 'A'
}

const ROUTER_INSTRUCTIONS = `
Stai raccogliendo il problema dell'utente. Dopo che l'utente ha descritto la sua situazione,
poni questa domanda ESATTA: "Quello che descrivi è un caso specifico su cui vuoi
un'analisi rapida, o fa parte di un progetto più ampio che vorresti strutturare?"
Non aggiungere altro. Attendi la risposta per determinare il percorso.
`

function PATH_A_INSTRUCTIONS(step: number): string {
  const steps: Record<number, string> = {
    3: 'Fai UNA domanda tecnica mirata al caso. Se ci sono allegati già analizzati, usa quelli per evitare domande ridondanti.',
    4: 'Fai AL MASSIMO una seconda domanda tecnica. Nessuna terza domanda: dopo questo step vai alla chiusura verso teaser.',
    5: 'Chiudi la raccolta dati in 1-2 frasi e includi esattamente `analysis_ready: true`. Non fare altre domande.',
    6: 'Conferma in modo breve che stai passando al teaser. Niente nuove domande.',
  }
  return steps[step] || 'Chiedi una domanda di approfondimento rilevante per il settore.'
}

function PATH_B_INSTRUCTIONS(step: number): string {
  const steps: Record<number, string> = {
    3: 'Chiedi il budget indicativo disponibile per il progetto (range, non cifra esatta).',
    4: 'Chiedi i tempi: "Quando vorreste essere operativi con la prima soluzione?"',
    5: 'Scrivi una sintesi del caso in 3-4 righe: "Ecco come ho capito la tua situazione..." - sii specifico, cita settore, problema, vincolo, obiettivo. Chiedi conferma: "È corretto o vuoi aggiungere qualcosa?"',
    6: 'L\'utente ha confermato o corretto. Ringrazia e dì che passerai il brief al team. Chiedi email e disponibilità per una call di 20 minuti.',
  }
  return steps[step] || 'Continua a qualificare il progetto con domande specifiche.'
}

export function buildSystemPrompt(skillNames: string[], path: KbotPath, step: number, session: any): string {
  // Prompt chat ottimizzato per latenza: niente references complete in ogni turno.
  const skillContent = loadSkillBundle(skillNames, {
    maxTotalChars: CHAT_SYSTEM_MAX_CHARS,
    maxPerSkillChars: 5500,
    includeReferences: false,
  })
  const sectorLabel = session.sector || 'PMI italiana'
  const uploadedFiles = Array.isArray(session?.collected_data?.uploaded_files)
    ? session.collected_data.uploaded_files
    : []
  const hasDirectExtractedText = uploadedFiles.some((f: any) => {
    const extractionMethod = String(f?.extractionMethod || '')
    const extractedText = String(f?.extractedText || f?.extractedSummary || '')
    return (
      extractedText.trim().length > 80 &&
      (extractionMethod === 'pdf-parse' || extractionMethod === 'text-decode')
    )
  })

  const baseContext = `
Sei il K-BOT di K2-AI. Stai assistendo un professionista del settore: ${sectorLabel}.
Hai a disposizione skill specializzate per questo settore - usale per dare risposte precise e verticali.

PERCORSO ATTUALE: ${path === 'A' ? 'PATH A - Consulenza automatica' : path === 'B' ? 'PATH B - Contatto personalizzato' : 'Non ancora determinato'}
STEP: ${step}

REGOLE:
- Fai UNA SOLA domanda per volta. Mai elenchi di domande.
- Sii diretto e pragmatico. Mai "potrebbe", "forse", "si potrebbe valutare".
- Usa la terminologia del settore ${sectorLabel}.
- Risposte brevi in fase di raccolta dati (max 3 righe). Più dettagliato solo nel teaser/analisi.
- Mai fare domande su budget o commerciali nel PATH A.
- Usa sempre caratteri italiani corretti (è, à, ì, ò, ù) e punteggiatura naturale: niente fallback ASCII.
- Quando proponi opzioni, includi sempre "Altro (specifica)".
- Adatta le domande alle risposte già ricevute: evita pattern statici e ripetitivi.
- In chat NON usare markdown strutturale (niente #, tabelle, blocchi JSON, blocchi code fence).
- In chat non produrre report completi: raccogli dati e conferma i prossimi passi in modo sintetico.
- Nessuna domanda è obbligatoria: se l'utente non sa o non vuole rispondere, accetta la risposta e prosegui.
- In PATH A fai massimo 2 domande tecniche dopo il router, poi teaser.
- Se non hai estratti testuali diretti dagli allegati, NON inventare numeri, percentuali o KPI puntuali.
- Se citi numeri da allegati, indica chiaramente che provengono dagli estratti disponibili.

STATO ALLEGATI: ${hasDirectExtractedText ? 'estratti testuali diretti disponibili' : 'nessun estratto testuale diretto affidabile'}

${path === 'A' ? PATH_A_INSTRUCTIONS(step) : path === 'B' ? PATH_B_INSTRUCTIONS(step) : ROUTER_INSTRUCTIONS}
`

  return `${baseContext}\n\n${skillContent}`
}

export function compactMessages(
  messages: ChatMessage[],
  maxMessages = MAX_HISTORY_MESSAGES,
  maxCharsPerMessage = MAX_MESSAGE_CHARS,
): ChatMessage[] {
  const tail = messages.slice(-maxMessages)
  return tail.map(m => ({
    ...m,
    content:
      typeof m.content === 'string' && m.content.length > maxCharsPerMessage
        ? `${m.content.slice(0, maxCharsPerMessage)}\n\n[MESSAGGIO TRONCATO]`
        : m.content,
  }))
}

export function extractStructuredData(
  message: string,
  step: number,
  existing: SessionData,
  assistantMessage: string,
  path: KbotPath,
): SessionData {
  const updated: SessionData = { ...existing }

  if (step === 1) updated.problem_description = message
  if (step === 2) updated.router_answer = message
  if (step === 3) {
    if (path === 'B') updated.budget_range = message
    else updated.technical_detail = message
  }
  if (step >= 4) {
    if (/analysis_ready\s*[:=]\s*true/i.test(assistantMessage)) {
      updated.analysis_ready = true
    }
    if (path === 'B') updated.go_live_timing = message
  }
  if (path === 'A' && step >= 5) {
    // Limite hard del flusso PATH A: non oltre 2 domande tecniche.
    updated.analysis_ready = true
  }
  if (step >= 6) {
    const emailMatch = message.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)
    if (emailMatch) updated.email = emailMatch[0]
    if (/lun|mar|mer|gio|ven|sab|dom|mattina|pomeriggio|sera|ore|:/.test(message.toLowerCase())) {
      updated.disponibilita = message
    }
  }

  updated.path = path
  return updated
}

export function determineNextAction(path: KbotPath, step: number, data: SessionData): string {
  if (path === 'A' && (data.analysis_ready || step >= 5)) return 'show_teaser'
  if (path === 'B' && step >= 6) return 'show_contact_form'
  return 'continue'
}

export function resolveSkillNames(sector: string | undefined): string[] {
  return SECTOR_BUNDLES[sector || ''] || ['diagnosi-ai-operativa-pmi']
}

/** Rileva skill corrette: service_id → content_type → auto-detect da file → sector */
export function resolveSkillNamesForSession(session: any): string[] {
  // 0. service_id ha priorità massima: usa le skill specifiche del servizio
  const serviceId = session?.collected_data?.service_id
  if (serviceId && SERVICE_SKILLS_MAP[serviceId]?.length > 0) {
    return SERVICE_SKILLS_MAP[serviceId]
  }

  // 1. content_type esplicito salvato in sessione ('generico' = usa sector bundle)
  const contentType = session?.collected_data?.content_type
  if (contentType && contentType !== 'generico' && CONTENT_TYPE_BUNDLES[contentType]?.length > 0) {
    return CONTENT_TYPE_BUNDLES[contentType]
  }

  // 2. Auto-detect dal testo estratto dagli allegati
  const uploadedFiles = Array.isArray(session?.collected_data?.uploaded_files)
    ? session.collected_data.uploaded_files
    : []
  const allText = uploadedFiles
    .map((f: any) => String(f.extractedText || f.extractedSummary || '').toLowerCase().slice(0, 3000))
    .join(' ')

  if (allText.length > 80) {
    const financialHits = (allText.match(
      /\b(ricavi|fatturato|utile|perdita|patrimonio netto|stato patrimoniale|conto economico|nota integrativa|ebitda|debiti verso|crediti verso|capitale sociale|fondo)\b/g,
    ) || []).length
    if (financialHits >= 3) return CONTENT_TYPE_BUNDLES['bilancio']

    const legalHits = (allText.match(
      /\b(contratto|articolo\s+\d|comma\s+\d|decreto legislativo|legge n\.|sentenza|giurisprudenza|clausola|stipulato)\b/g,
    ) || []).length
    if (legalHits >= 3) return CONTENT_TYPE_BUNDLES['contratto-legale']
  }

  // 3. Fallback a sector
  return resolveSkillNames(session?.sector)
}

/* ── K-BOT 2.0 ───────────────────────────────────────────────────────────── */

export type V2SummaryData = {
  businessType?: string
  problem?: string
  currentProcess?: string
  goal?: string
  urgency?: 'alta' | 'media' | 'bassa'
  dataAvailable?: string
  integrations?: string
  budget?: string
  notes?: string
  summary?: string
  recommendedServiceId?: string
  recommendedServiceName?: string
  recommendedTier?: 'HOST' | 'WEB' | 'STUDIO'
  nextStep?: string
}

const SERVICES_OVERVIEW_COMPACT = `
SERVIZI K2-AI DISPONIBILI (usa per raccomandare il più adatto):
P01 · Agenti AI Email & CRM — HOST/WEB · automatizza follow-up, triage email, aggiornamento CRM
P02 · Automazioni Amministrative — HOST · fatture, riconciliazioni, documenti contabili ripetitivi
P03 · AI Legale & Contratti — WEB · analisi contratti, ricerca giurisprudenziale, redazione clausole
P04 · AI Ingegneria & Progettazione — WEB · relazioni tecniche, computi, tavole, documentazione progettuale
P05 · Microapp Documenti Tecnici — HOST · generazione documenti tecnici da template, perizie, capitolati
P06 · AI Customer Service & Ticket — HOST/WEB · triage ticket, risposta automatica, escalation intelligente
P07 · RAG Knowledge Base — WEB/STUDIO · base di conoscenza interrogabile su documenti aziendali
P08 · AI Compliance & Audit — WEB · verifica conformità, audit trail, checklist normative
P09 · AI Controllo di Gestione — WEB · reporting automatico, KPI, budget vs consuntivo
P10 · Integrazione Gestionali & ERP — STUDIO · connettori API, sync dati, automazioni tra gestionali
P11 · AI Marketing & Contenuti — HOST/WEB · copy, SEO, newsletter, campagne
P12 · Diagnosi Strategica PMI — WEB · analisi processi, gap operativi, roadmap AI
P13 · Agevolazioni & Finanza Agevolata — WEB · identificazione bandi, pratiche, documentazione
P14 · AI Edilizia & Appalti Pubblici — WEB · gare, pratiche, documentazione tecnica appalti
P15 · AI HR & Recruiting — HOST/WEB · screening CV, job description, onboarding automatico
P16 · AI Real Estate & Tokenizzazione — STUDIO · dossier immobiliari, due diligence, tokenizzazione
P17 · AI Data Analytics & BI — STUDIO · dashboard, report automatici, anomaly detection
P18 · AI UX & Design System — WEB · audit UX, design system, accessibilità
P19 · AI Efficienza Energetica — WEB · analisi consumi, report energetico, certificazioni
P20 · AI Hospitality & Revenue — HOST/WEB · revenue management, risposta OTA, upselling automatico

TIER:
HOST: <1.500€/mese — automazioni singole, microapp, agenti email
WEB: 1.500–4.000€/mese — sistemi integrati, RAG, customer service AI
STUDIO: >4.000€/mese — progetti custom, ERP, multi-sistema, analytics avanzato`.trim()

export function buildSystemPromptV2(skillNames: string[], session: any): string {
  const skillContent = loadSkillBundle(skillNames, {
    maxTotalChars: CHAT_SYSTEM_MAX_CHARS,
    maxPerSkillChars: 5500,
    includeReferences: false,
  })

  const mode: string = session?.mode || 'report'
  const serviceId: string | undefined = session?.collected_data?.service_id
  const serviceContext = serviceId
    ? `\nSERVIZIO SELEZIONATO DALL'UTENTE: ${serviceId} — orienta la conversazione su questo ambito.\n`
    : ''

  const uploadedFiles = Array.isArray(session?.collected_data?.uploaded_files)
    ? session.collected_data.uploaded_files : []
  const hasFiles = uploadedFiles.length > 0
  const hasExtractedText = uploadedFiles.some((f: any) => {
    const text = String(f?.extractedText || f?.extractedSummary || '')
    return text.trim().length > 80
  })

  const nextStepHint = mode === 'lead'
    ? 'Apri il servizio Suite consigliato se il caso combacia; altrimenti compila il form contatti precompilato per definire il perimetro custom'
    : 'Scarica il report operativo con priorità, tempi e template pronti'

  const basePrompt = `Sei K-BOT, il consulente AI di K2-AI per PMI italiane.
Il tuo ruolo: capire il problema operativo dell'utente con domande naturali, raccogliere il contesto necessario, poi produrre un riepilogo strutturato.
${serviceContext}
OBIETTIVO SPECIFICO IN MODALITÀ LEAD:
- Fai da scrematura iniziale dentro la Suite AI.
- Devi capire se il bisogno dell'utente corrisponde a uno dei servizi P01-P20.
- Se corrisponde, scegli recommendedServiceId e recommendedServiceName con decisione.
- Se non corrisponde bene a nessun servizio, usa comunque il servizio più vicino solo come riferimento, ma nel campo nextStep indica chiaramente che serve contatto custom con K2-AI.
- Non vendere report premium in questo flusso: qui l'obiettivo è qualificare il lead e indirizzarlo.

COMPORTAMENTO:
- Fai UNA sola domanda per volta, specifica e contestuale a ciò che l'utente ha già detto
- Se l'utente ha già risposto a qualcosa, non richiederlo
- Se l'utente fa una domanda, rispondi prima di fare la tua
- Accetta risposte vaghe e prosegui senza forzare dettagli
- Tono: diretto, professionale, da pari a pari — non commerciale
- Niente elenchi di domande multiple in un singolo messaggio
- Niente markdown strutturale in chat (no #, tabelle, blocchi code)
- Risposte brevi in fase raccolta (max 4 righe)
- Usa sempre caratteri italiani corretti (è, à, ì, ò, ù)
- Nessuna risposta è obbligatoria: se l'utente non sa, accetta e prosegui
- STATO ALLEGATI: ${hasFiles ? (hasExtractedText ? 'estratti testuali disponibili — usali, non fare domande già rispondibili dai file' : 'file caricati ma senza testo estraibile') : 'nessun allegato'}

CAMPI DA RACCOGLIERE (naturalmente, non come modulo):
businessType · problem · currentProcess · goal · urgency (alta/media/bassa)
dataAvailable · integrations · budget (solo se lo menziona) · notes

QUANDO GENERARE IL RIEPILOGO:
Dopo 3-5 turni, quando conosci almeno businessType + problem + goal (anche in modo approssimativo), oppure quando l'utente dice di procedere.
Prima del blocco scrivi 1-2 frasi di chiusura naturale. Poi aggiungi il blocco ESATTO:

CONSULENZA_SUMMARY_START
{"businessType":"...","problem":"...","currentProcess":"...","goal":"...","urgency":"alta|media|bassa","dataAvailable":"...","integrations":"...","budget":"...","notes":"...","summary":"2-3 frasi specifiche e concrete che descrivono il caso","recommendedServiceId":"PXX","recommendedServiceName":"Nome completo servizio","recommendedTier":"HOST|WEB|STUDIO","nextStep":"${nextStepHint}"}
CONSULENZA_SUMMARY_END

Il blocco sarà estratto automaticamente e non mostrato all'utente.

${SERVICES_OVERVIEW_COMPACT}
`

  return `${basePrompt}\n\n${skillContent}`
}

export function extractV2Summary(text: string): V2SummaryData | null {
  const match = text.match(/CONSULENZA_SUMMARY_START\s*\n([\s\S]*?)\nCONSULENZA_SUMMARY_END/)
  if (!match) return null
  try {
    return JSON.parse(match[1].trim()) as V2SummaryData
  } catch {
    return null
  }
}

export function stripSummaryBlock(text: string): string {
  return text.replace(/\s*CONSULENZA_SUMMARY_START[\s\S]*?CONSULENZA_SUMMARY_END\s*/g, '').trim()
}

/** Rimuove l'ultima domanda da un messaggio di chiusura */
export function stripClosingQuestion(text: string): string {
  const cleaned = text.trim()
  // Se finisce con ?, rimuovi l'ultima frase interrogativa
  if (!cleaned.endsWith('?')) return cleaned
  // Trova l'ultima frase che inizia dopo . ! ?
  const stripped = cleaned.replace(/[.!?]\s+[^.!?]*\?[^?]*$/, '.').replace(/\s*[^.!?]*\?[^?]*$/, '')
  return stripped.trim() || cleaned
}

export function resolveSectorLabel(sector: string | undefined): string {
  if (!sector) return 'PMI italiana'
  return SECTOR_LABELS[sector] || 'PMI italiana'
}

export function escapeHtml(s: string): string {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}
