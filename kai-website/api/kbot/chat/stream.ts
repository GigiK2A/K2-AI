/**
 * /api/kbot/chat/stream
 *
 * SSE streaming variant of /api/kbot/chat.
 * Emits:  data: {"delta":"..."}   — per token
 *         data: {"done":true,"message":"...","next_action":"...","session":{...}}  — final
 *         data: [DONE]            — stream closed
 *         data: {"error":"..."}   — on failure
 */
import {
  buildSystemPromptV2,
  compactMessages,
  createAnthropicClient,
  createSupabaseAdminClient,
  extractV2Summary,
  MODEL,
  parseJsonBody,
  resolveSkillNamesForSession,
  stripSummaryBlock,
  type V2SummaryData,
} from '../_shared'

// Re-use normalizeAssistantReply from the chat handler
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

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST')
    res.statusCode = 405
    res.end(JSON.stringify({ error: 'Method not allowed' }))
    return
  }

  // SSE headers
  res.setHeader('Content-Type', 'text/event-stream; charset=utf-8')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Connection', 'keep-alive')
  res.setHeader('X-Accel-Buffering', 'no')
  res.statusCode = 200

  const sseWrite = (data: unknown) => {
    try { res.write(`data: ${JSON.stringify(data)}\n\n`) } catch { /* ignore */ }
  }
  const sseDone = () => {
    try { res.write('data: [DONE]\n\n'); res.end() } catch { /* ignore */ }
  }
  const sseError = (msg: string) => {
    try { res.write(`data: ${JSON.stringify({ error: msg })}\n\n`); res.end() } catch { /* ignore */ }
  }

  try {
    const body = await parseJsonBody(req)
    const { session_id, message, step } = body
    const supabase = createSupabaseAdminClient()
    const anthropic = createAnthropicClient()

    const userMessage = String(message || '').slice(0, 4000)
    const stepNum = Number(step || 1)

    const { data: session, error: sessionError } = await supabase
      .from('kbot_sessions')
      .select('*')
      .eq('id', session_id)
      .single()

    if (sessionError || !session) return sseError('Session not found')

    const skillNames = resolveSkillNamesForSession(session)
    const systemPrompt = buildSystemPromptV2(skillNames, session)

    type ChatMessage = { role: 'user' | 'assistant'; content: string; ts?: string }
    const persistedMessages: ChatMessage[] = [
      ...((session.messages || []) as ChatMessage[]),
      { role: 'user', content: userMessage, ts: new Date().toISOString() },
    ]
    const modelMessages = compactMessages(persistedMessages).map(m => ({ role: m.role, content: m.content }))

    let rawAssistant = ''

    const stream = anthropic.messages.stream({
      model: MODEL,
      max_tokens: 1200,
      system: systemPrompt,
      messages: modelMessages,
    })

    stream.on('text', (delta: string) => {
      rawAssistant += delta
      sseWrite({ delta })
    })

    await stream.finalMessage()

    const v2Summary: V2SummaryData | null = extractV2Summary(rawAssistant)
    const assistantMessage = normalizeAssistantReply(stripSummaryBlock(rawAssistant))

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
        step: stepNum + 1,
        path: session.collected_data?.mode === 'lead' ? 'B' : 'A',
        collected_data: updatedData,
        updated_at: new Date().toISOString(),
      })
      .eq('id', session_id)

    const nextAction = v2Summary ? 'show_summary' : 'continue'

    sseWrite({
      done: true,
      message: assistantMessage,
      next_action: nextAction,
      session: { step: stepNum + 1 },
      ...(v2Summary ? { v2_summary: v2Summary } : {}),
    })
    sseDone()
  } catch (err: any) {
    const msg = err instanceof Error ? err.message : 'Errore interno'
    const isTimeout = /timeout/i.test(msg)
    sseError(isTimeout ? 'K-BOT è temporaneamente lento, riprova tra qualche secondo.' : msg)
  }
}
