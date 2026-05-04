import {
  buildSystemPromptV2,
  extractV2Summary,
  stripSummaryBlock,
  compactMessages,
  createAnthropicClient,
  createSupabaseAdminClient,
  ensurePost,
  MODEL,
  parseJsonBody,
  resolveSkillNamesForSession,
  sendJson,
  type V2SummaryData,
} from './_shared'

type ChatMessage = { role: 'user' | 'assistant'; content: string; ts?: string }

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
    .replace(/\n{3,}/g, '\n\n')
    .trim()

  if (!text) return 'Ricevuto. Procedo con il prossimo passaggio.'
  if (text.length > 1200) return `${text.slice(0, 1197).trim()}...`
  return text
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

    // Path determined by mode, not router question
    const sessionMode: string = session.mode || 'report'
    const path: 'A' | 'B' = sessionMode === 'lead' ? 'B' : 'A'

    const skillNames = resolveSkillNamesForSession(session)
    const systemPrompt = buildSystemPromptV2(skillNames, session)

    const modelMessages = compactMessages(modelMessagesInput).map(m => ({ role: m.role, content: m.content }))

    const response = await anthropic.messages.create({
      model: MODEL,
      max_tokens: 1200,
      system: systemPrompt,
      messages: modelMessages,
    })

    const rawAssistantMessage = response.content[0]?.type === 'text' ? response.content[0].text : ''

    // Extract structured summary before stripping block
    const v2Summary: V2SummaryData | null = extractV2Summary(rawAssistantMessage)
    const strippedRaw = stripSummaryBlock(rawAssistantMessage)
    const assistantMessage = normalizeAssistantReply(strippedRaw)

    // Persist v2 summary data into collected_data
    const updatedData: Record<string, any> = { ...(session.collected_data || {}) }
    if (v2Summary) {
      Object.assign(updatedData, v2Summary)
      updatedData.analysis_ready = true
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

    const nextAction = v2Summary ? 'show_summary' : 'continue'

    return sendJson(res, 200, {
      message: assistantMessage,
      path,
      next_action: nextAction,
      v2_summary: v2Summary || undefined,
      contact_summary: v2Summary?.summary || undefined,
      session: { path, step: stepNum + 1 },
    })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return sendJson(res, 500, { error: message })
  }
}
