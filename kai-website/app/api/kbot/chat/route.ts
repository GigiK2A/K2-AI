import { NextRequest, NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'
import { createClient } from '@/lib/supabase/server'
import { getAnthropicApiKey } from '@/lib/env/system'
import { loadSkillBundle } from '@/lib/skills/loader'
import { SECTOR_BUNDLES, PATH_A_KEYWORDS, PATH_B_KEYWORDS } from '@/lib/skills/sectors.config'

const MODEL = 'claude-haiku-4-5'

type ChatMessage = { role: 'user' | 'assistant'; content: string; ts?: string }
type SessionData = Record<string, any>
const MAX_HISTORY_MESSAGES = 12
const MAX_MESSAGE_CHARS = 900

function hasQuestion(text: string): boolean {
  return /\?/.test(String(text || ''))
}

function normalizeAssistantReply(raw: string): string {
  let text = String(raw || '')
  if (!text.trim()) return 'Ricevuto. Procediamo.'

  text = text
    .replace(/```[\s\S]*?```/g, '')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^\s*\|.*\|\s*$/gm, '')
    .replace(/^\s*[-=_]{3,}\s*$/gm, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/^\s*[-*]\s+/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim()

  const lines = text
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean)
    .slice(0, 4)

  const compact = lines.join('\n').trim()
  if (!compact) return 'Ricevuto. Procediamo.'
  if (compact.length > 680) return `${compact.slice(0, 677).trim()}...`
  return compact
}

function buildAttachmentsContext(session: any): string {
  const files = Array.isArray(session?.collected_data?.uploaded_files)
    ? session.collected_data.uploaded_files
    : []
  if (files.length === 0) return ''

  const tail = files.slice(-2)
  const lines = tail.map((f: any, idx: number) => {
    const base = `${idx + 1}. ${f.name || 'file'} (${f.type || 'n/d'})`
    const extractedText = typeof f.extractedText === 'string' ? f.extractedText : ''
    const extractedSummary = typeof f.extractedSummary === 'string' ? f.extractedSummary : ''
    const source = extractedSummary.trim() ? extractedSummary : extractedText
    const excerpt = source.trim() ? source.trim().slice(0, 1600) : ''
    return excerpt
      ? `${base}\nEstratto allegato:\n${excerpt}`
      : `${base}\nNessun testo estraibile: evita numeri specifici non verificati.`
  })

  return `\n\nCONTESTO ALLEGATI DISPONIBILE:\n${lines.join('\n\n')}`
}

function compactMessages(messages: ChatMessage[]): ChatMessage[] {
  return messages
    .slice(-MAX_HISTORY_MESSAGES)
    .map(message => ({
      ...message,
      content:
        typeof message.content === 'string' && message.content.length > MAX_MESSAGE_CHARS
          ? `${message.content.slice(0, MAX_MESSAGE_CHARS)}\n\n[MESSAGGIO TRONCATO]`
          : message.content,
    }))
}

export async function POST(req: NextRequest) {
  try {
    const client = new Anthropic({ apiKey: getAnthropicApiKey() })
    const { session_id, message, step } = await req.json()
    const supabase = createClient()

    const { data: session, error: sessionError } = await supabase
      .from('kbot_sessions')
      .select('*')
      .eq('id', session_id)
      .single()

    if (sessionError || !session) {
      return NextResponse.json({ error: 'Session not found' }, { status: 404 })
    }

    const attachmentsContext = buildAttachmentsContext(session)
    const messageWithContext = `${String(message || '')}${attachmentsContext}`
    const persistedMessages: ChatMessage[] = [
      ...((session.messages || []) as ChatMessage[]),
      { role: 'user', content: String(message || ''), ts: new Date().toISOString() },
    ]
    const modelMessagesInput: ChatMessage[] = [
      ...persistedMessages.slice(0, -1),
      { role: 'user', content: messageWithContext, ts: persistedMessages[persistedMessages.length - 1]?.ts },
    ]

    let path: 'A' | 'B' | 'unknown' = (session.path || 'unknown') as 'A' | 'B' | 'unknown'
    if (step === 2 && path === 'unknown') {
      path = detectPath(String(message || ''), session.collected_data?.problem_description || '')
    }

    const skillNames = SECTOR_BUNDLES[session.sector] || ['diagnosi-ai-operativa-pmi']
    const systemPrompt = buildSystemPrompt(skillNames, path, step, session)

    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 700,
      system: systemPrompt,
      messages: compactMessages(modelMessagesInput).map(m => ({ role: m.role, content: m.content })),
    })

    const rawAssistantMessage = response.content[0]?.type === 'text' ? response.content[0].text : ''
    let assistantMessage = normalizeAssistantReply(rawAssistantMessage)
    const updatedData = extractStructuredData(
      String(message || ''),
      step,
      session.collected_data || {},
      assistantMessage,
      path,
    )

    const hasUploadedFiles = Array.isArray(session?.collected_data?.uploaded_files) &&
      session.collected_data.uploaded_files.length > 0

    if (path === 'A' && step >= 3 && hasUploadedFiles && !hasQuestion(assistantMessage)) {
      updatedData.analysis_ready = true
      assistantMessage = 'Ho ricevuto il bilancio e ho dati sufficienti. Ti mostro subito i segnali principali nel teaser.'
    }

    const updatedMessages: ChatMessage[] = [
      ...persistedMessages,
      { role: 'assistant', content: assistantMessage, ts: new Date().toISOString() },
    ]

    await supabase
      .from('kbot_sessions')
      .update({
        messages: updatedMessages,
        path,
        step: Number(step || 1) + 1,
        collected_data: updatedData,
        updated_at: new Date().toISOString(),
      })
      .eq('id', session_id)

    const nextAction = determineNextAction(path, step, updatedData)

    return NextResponse.json({
      message: assistantMessage,
      path,
      next_action: nextAction,
      session: { path, step: Number(step || 1) + 1 },
    })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}

function detectPath(routerAnswer: string, problemDescription: string): 'A' | 'B' {
  const text = `${routerAnswer} ${problemDescription}`.toLowerCase()

  let scoreA = PATH_A_KEYWORDS.filter(kw => text.includes(kw)).length
  let scoreB = PATH_B_KEYWORDS.filter(kw => text.includes(kw)).length

  if (/caso singolo|singolo|uno specifico|una cosa|un problema/.test(text)) scoreA += 3
  if (/progetto|ampio|tutto|intero|sistema|riorganiz/.test(text)) scoreB += 3

  return scoreB > scoreA ? 'B' : 'A'
}

function buildSystemPrompt(skillNames: string[], path: string, step: number, session: any): string {
  const skillContent = loadSkillBundle(skillNames, {
    maxTotalChars: 26000,
    maxPerSkillChars: 5500,
    includeReferences: false,
  })
  const sectorLabel = session.sector || 'PMI italiana'

  const baseContext = `
Sei il K-BOT di K2-AI. Stai assistendo un professionista del settore: ${sectorLabel}.
Hai a disposizione skill specializzate per questo settore - usale per dare risposte precise e verticali.

PERCORSO ATTUALE: ${path === 'A' ? 'PATH A - Consulenza automatica' : path === 'B' ? 'PATH B - Contatto personalizzato' : 'Non ancora determinato'}
STEP: ${step}

REGOLE:
- Fai UNA SOLA domanda per volta. Mai elenchi di domande.
- Sii diretto e pragmatico. Mai "potrebbe", "forse", "si potrebbe valutare".
- Usa la terminologia del settore ${sectorLabel}.
- Risposte brevi in fase di raccolta dati (max 3 righe). Piu dettagliato solo nel teaser/analisi.
- Mai fare domande su budget o commerciali nel PATH A.
- In PATH A fai massimo 2 domande tecniche dopo il router.
- In chat non usare markdown strutturale: no #, no tabelle, no JSON, no code block.
- Nessuna domanda e obbligatoria: se l'utente non sa, accetta e prosegui.
- Se non hai estratti testuali affidabili dagli allegati, non dichiarare numeri specifici.

${path === 'A' ? PATH_A_INSTRUCTIONS(step) : path === 'B' ? PATH_B_INSTRUCTIONS(step) : ROUTER_INSTRUCTIONS}
`

  return `${baseContext}\n\n${skillContent}`
}

const ROUTER_INSTRUCTIONS = `
Stai raccogliendo il problema dell'utente. Dopo che l'utente ha descritto la sua situazione,
poni questa domanda ESATTA: "Quello che descrivi e un caso specifico su cui vuoi
un'analisi rapida, o fa parte di un progetto piu ampio che vorresti strutturare?"
Non aggiungere altro. Attendi la risposta per determinare il percorso.
`

function PATH_A_INSTRUCTIONS(step: number): string {
  const steps: Record<number, string> = {
    3: 'Fai UNA domanda tecnica mirata al caso.',
    4: 'Fai AL MASSIMO una seconda domanda tecnica. Niente terza domanda.',
    5: 'Chiudi la raccolta dati in 1-2 frasi e includi esattamente `analysis_ready: true`. Non fare altre domande.',
  }
  return steps[step] || 'Chiedi una domanda di approfondimento rilevante per il settore.'
}

function PATH_B_INSTRUCTIONS(step: number): string {
  const steps: Record<number, string> = {
    3: 'Chiedi il budget indicativo disponibile per il progetto (range, non cifra esatta).',
    4: 'Chiedi i tempi: "Quando vorreste essere operativi con la prima soluzione?"',
    5: 'Scrivi una sintesi del caso in 3-4 righe: "Ecco come ho capito la tua situazione..." - sii specifico, cita settore, problema, vincolo, obiettivo. Chiedi conferma: "E corretto o vuoi aggiungere qualcosa?"',
    6: 'L\'utente ha confermato o corretto. Ringrazia e di\' che passerai il brief al team. Chiedi email e disponibilita per una call di 20 minuti.',
  }
  return steps[step] || 'Continua a qualificare il progetto con domande specifiche.'
}

function extractStructuredData(
  message: string,
  step: number,
  existing: SessionData,
  assistantMessage: string,
  path: 'A' | 'B' | 'unknown',
): SessionData {
  const updated: SessionData = { ...existing }

  if (step === 1) updated.problem_description = message
  if (step === 2) updated.router_answer = message
  if (step === 3) {
    if (path === 'B') updated.budget_range = message
    else updated.technical_detail = message
  }
  if (step === 4) {
    if (/analysis_ready\s*[:=]\s*true/i.test(assistantMessage)) {
      updated.analysis_ready = true
    }
    if (path === 'B') updated.go_live_timing = message
  }
  if (path === 'A' && step >= 5) {
    updated.analysis_ready = true
  }
  if (step >= 6) {
    const emailMatch = message.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)
    if (emailMatch) updated.email = emailMatch[0]
    if (/lun|mar|mer|gio|ven|sab|dom|mattina|pomeriggio|sera|ore|:/.test(message.toLowerCase())) {
      updated.disponibilita = message
    }
  }

  return updated
}

function determineNextAction(path: string, step: number, data: SessionData): string {
  if (path === 'A' && (data.analysis_ready || step >= 5)) return 'show_teaser'
  if (path === 'B' && step >= 6) return 'show_contact_form'
  return 'continue'
}
