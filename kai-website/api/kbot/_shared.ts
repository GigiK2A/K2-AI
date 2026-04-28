import { createClient as createSupabaseClient } from '@supabase/supabase-js'
import Anthropic from '@anthropic-ai/sdk'
import { loadSkillBundle } from '../../lib/skills/loader'
import {
  SECTOR_BUNDLES,
  SECTOR_LABELS,
  PATH_A_KEYWORDS,
  PATH_B_KEYWORDS,
} from '../../lib/skills/sectors.config'
import { getAnthropicApiKey, getSystemEnvVar } from '../../lib/env/system'

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
