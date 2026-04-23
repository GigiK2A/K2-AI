import {
  buildSystemPrompt,
  compactMessages,
  createAnthropicClient,
  createSupabaseAdminClient,
  detectPath,
  determineNextAction,
  ensurePost,
  extractStructuredData,
  MODEL,
  parseJsonBody,
  resolveSkillNames,
  sendJson,
} from './_shared'

type ChatMessage = { role: 'user' | 'assistant'; content: string; ts?: string }

function hasQuestion(text: string): boolean {
  return /\?/.test(String(text || ''))
}

function normalizeAssistantReply(raw: string): string {
  let text = String(raw || '')
  if (!text.trim()) return 'Ricevuto. Procedo con il prossimo passaggio.'

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
  if (!compact) return 'Ricevuto. Procedo con il prossimo passaggio.'
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
    const extractionMethod = String(f.extractionMethod || '')
    const extractedText = typeof f.extractedText === 'string' ? f.extractedText : ''
    const extractedSummary = typeof f.extractedSummary === 'string' ? f.extractedSummary : ''
    const source = extractedSummary.trim() ? extractedSummary : extractedText
    const excerpt = source.trim() ? source.trim().slice(0, 1600) : ''
    const note = extractionMethod === 'pdf-parse' || extractionMethod === 'text-decode'
      ? 'Estratto testuale diretto dal file'
      : 'Sintesi del file (non trattare come dato numerico definitivo)'
    return excerpt
      ? `${base}\n${note}:\n${excerpt}`
      : `${base}\nNessun contenuto testuale estraibile: evita numeri specifici e chiedi solo conferme mirate.`
  })

  return `\n\nCONTESTO ALLEGATI DISPONIBILE:\n${lines.join('\n\n')}`
}

export default async function handler(req: any, res: any) {
  if (!ensurePost(req, res)) return

  try {
    const { session_id, message, step } = await parseJsonBody(req)
    const supabase = createSupabaseAdminClient()
    const anthropic = createAnthropicClient()

    const stepNum = Number(step || 1)
    const userMessage = String(message || '').slice(0, 4000)

    const { data: session, error: sessionError } = await supabase
      .from('kbot_sessions')
      .select('*')
      .eq('id', session_id)
      .single()

    if (sessionError || !session) return sendJson(res, 404, { error: 'Session not found' })

    // Rate limiting: max 20 messaggi per sessione
    const messageCount = Array.isArray(session.messages) ? session.messages.length : 0
    if (messageCount >= 40) {
      return sendJson(res, 429, { error: 'Limite messaggi raggiunti per questa sessione. Riavvia la chat per un nuovo caso.' })
    }

    // Rate limiting: cooldown 2s tra messaggi
    const lastUpdate = session.updated_at ? new Date(session.updated_at).getTime() : 0
    if (Date.now() - lastUpdate < 2000) {
      return sendJson(res, 429, { error: 'Troppe richieste. Attendi un momento.' })
    }

    const attachmentsContext = buildAttachmentsContext(session)
    const persistedMessages: ChatMessage[] = [
      ...((session.messages || []) as ChatMessage[]),
      { role: 'user', content: userMessage, ts: new Date().toISOString() },
    ]

    const modelMessagesInput: ChatMessage[] = [
      ...persistedMessages.slice(0, -1),
      {
        role: 'user',
        content: `${userMessage}${attachmentsContext}`,
        ts: persistedMessages[persistedMessages.length - 1]?.ts,
      },
    ]

    let path = (session.path || 'unknown') as 'A' | 'B' | 'unknown'
    if (stepNum === 2 && path === 'unknown') {
      path = detectPath(userMessage, session.collected_data?.problem_description || '')
    }

    const skillNames = resolveSkillNames(session.sector)
    const systemPrompt = buildSystemPrompt(skillNames, path, stepNum, session)

    const modelMessages = compactMessages(modelMessagesInput).map(m => ({ role: m.role, content: m.content }))

    const response = await anthropic.messages.create({
      model: MODEL,
      max_tokens: 700,
      system: systemPrompt,
      messages: modelMessages,
    })

    const rawAssistantMessage = response.content[0]?.type === 'text' ? response.content[0].text : ''
    let assistantMessage = normalizeAssistantReply(rawAssistantMessage)

    const updatedData = extractStructuredData(
      userMessage,
      stepNum,
      session.collected_data || {},
      assistantMessage,
      path,
    )

    const hasUploadedFiles = Array.isArray(session?.collected_data?.uploaded_files) &&
      session.collected_data.uploaded_files.length > 0

    // Anti-stallo PATH A: se dopo upload file il bot non pone alcuna domanda, chiudi verso teaser.
    if (path === 'A' && stepNum >= 3 && hasUploadedFiles && !hasQuestion(assistantMessage)) {
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
        step: stepNum + 1,
        collected_data: updatedData,
        updated_at: new Date().toISOString(),
      })
      .eq('id', session_id)

    const nextAction = determineNextAction(path, stepNum, updatedData)

    return sendJson(res, 200, {
      message: assistantMessage,
      path,
      next_action: nextAction,
      session: { path, step: stepNum + 1 },
    })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return sendJson(res, 500, { error: message })
  }
}
