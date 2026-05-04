import {
  buildSystemPromptV2,
  compactMessages,
  createAnthropicClient,
  createSupabaseAdminClient,
  extractV2Summary,
  MODEL,
  stripSummaryBlock,
  type V2SummaryData,
} from '../../api/kbot/_shared'
import { CONTENT_TYPE_BUNDLES, SECTOR_BUNDLES } from '../skills/sectors.config'
import { generateReportData } from './report-data'
import { getSuiteAiServiceById, normalizeServiceId } from './services'

export type KbotRole = 'user' | 'assistant'
export type KbotMessage = { role: KbotRole; content: string; ts?: string }

export interface PublicKbotSession {
  id: string
  serviceId: string
  messages: KbotMessage[]
  extractedData: Record<string, unknown>
  summary: string | null
  recommendedTier: string | null
  timestamps: {
    createdAt: string | null
    updatedAt: string | null
  }
}

const VALID_SECTORS = new Set(Object.keys(SECTOR_BUNDLES))
const VALID_CONTENT_TYPES = new Set(Object.keys(CONTENT_TYPE_BUNDLES))
const DEFAULT_SECTOR = 'servizi-b2b'
const DEFAULT_SERVICE_ID = 'P12'

function nowIso(): string {
  return new Date().toISOString()
}

function isKbotRole(role: unknown): role is KbotRole {
  return role === 'user' || role === 'assistant'
}

export function normalizeMessages(value: unknown): KbotMessage[] {
  if (!Array.isArray(value)) return []

  return value
    .reduce<KbotMessage[]>((messages, item) => {
      if (!item || typeof item !== 'object') return messages

      const candidate = item as Record<string, unknown>
      const role = isKbotRole(candidate.role) ? candidate.role : null
      const content = String(candidate.content || '').trim()
      if (!role || !content) return messages

      messages.push({
        role,
        content: content.slice(0, 4000),
        ts: typeof candidate.ts === 'string' ? candidate.ts : nowIso(),
      })
      return messages
    }, [])
}

function mergeMessages(storedMessages: KbotMessage[], incomingMessages: KbotMessage[]): KbotMessage[] {
  const merged = [...storedMessages]
  for (const incoming of incomingMessages) {
    const exists = merged.some(stored =>
      stored.role === incoming.role &&
      stored.content === incoming.content &&
      (!incoming.ts || !stored.ts || stored.ts === incoming.ts),
    )
    if (!exists) merged.push(incoming)
  }
  return merged
}

function appendUserMessage(messages: KbotMessage[], message: unknown): KbotMessage[] {
  const content = String(message || '').trim().slice(0, 4000)
  if (!content) return messages

  const last = messages[messages.length - 1]
  if (last?.role === 'user' && last.content === content) return messages

  return [...messages, { role: 'user', content, ts: nowIso() }]
}

function resolveCollectedData(session: any): Record<string, any> {
  return session?.collected_data && typeof session.collected_data === 'object'
    ? session.collected_data
    : {}
}

export function serializeKbotSession(session: any): PublicKbotSession {
  const collectedData = resolveCollectedData(session)
  const serviceId = normalizeServiceId(collectedData.service_id || session?.service_id)
  const extractedData = collectedData.extractedData && typeof collectedData.extractedData === 'object'
    ? collectedData.extractedData
    : collectedData

  return {
    id: String(session?.id || ''),
    serviceId,
    messages: normalizeMessages(session?.messages),
    extractedData,
    summary: typeof collectedData.summary === 'string' ? collectedData.summary : null,
    recommendedTier: typeof collectedData.recommendedTier === 'string'
      ? collectedData.recommendedTier
      : typeof collectedData.recommended_tier === 'string'
        ? collectedData.recommended_tier
        : null,
    timestamps: {
      createdAt: typeof session?.created_at === 'string' ? session.created_at : null,
      updatedAt: typeof session?.updated_at === 'string' ? session.updated_at : null,
    },
  }
}

export function readServiceIdFromBody(body: Record<string, unknown>): string {
  return normalizeServiceId(body.serviceId || body.service_id || DEFAULT_SERVICE_ID)
}

export function validateServiceId(serviceId: string): { ok: true } | { ok: false; error: string } {
  if (!serviceId) return { ok: false, error: 'serviceId obbligatorio.' }
  if (!getSuiteAiServiceById(serviceId)) return { ok: false, error: 'serviceId non valido.' }
  return { ok: true }
}

export async function createKbotSession(body: Record<string, unknown>): Promise<PublicKbotSession> {
  const serviceId = readServiceIdFromBody(body)
  const validation = validateServiceId(serviceId)
  if (!validation.ok) throw new Error(validation.error)

  const sector = typeof body.sector === 'string' && VALID_SECTORS.has(body.sector)
    ? body.sector
    : DEFAULT_SECTOR
  const contentType = typeof body.content_type === 'string' && VALID_CONTENT_TYPES.has(body.content_type)
    ? body.content_type
    : null
  const mode = typeof body.mode === 'string' && body.mode.trim()
    ? body.mode.trim().slice(0, 40)
    : 'report'

  const collectedData: Record<string, unknown> = {
    service_id: serviceId,
    extractedData: {},
  }
  if (contentType) collectedData.content_type = contentType

  const supabase = createSupabaseAdminClient()
  const { data, error } = await supabase
    .from('kbot_sessions')
    .insert({
      sector,
      status: 'active',
      messages: [],
      path: 'unknown',
      step: 1,
      collected_data: collectedData,
      mode,
    })
    .select('*')
    .single()

  if (error) throw new Error(error.message)
  return serializeKbotSession(data)
}

export async function loadKbotSession(sessionId: unknown): Promise<any> {
  const id = String(sessionId || '').trim()
  if (!id) throw new Error('sessionId obbligatorio.')

  const supabase = createSupabaseAdminClient()
  const { data, error } = await supabase
    .from('kbot_sessions')
    .select('*')
    .eq('id', id)
    .single()

  if (error || !data) throw new Error('Session not found')
  return data
}

function normalizeAssistantReply(raw: string): string {
  const cleaned = String(raw || '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^\s*\|.*\|\s*$/gm, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\n{3,}/g, '\n\n')
    .trim()

  if (!cleaned) return 'Ricevuto. Procedo con il prossimo passaggio.'
  return cleaned.length > 1200 ? `${cleaned.slice(0, 1197).trim()}...` : cleaned
}

function buildSessionForPrompt(session: any, serviceId: string): any {
  return {
    ...session,
    collected_data: {
      ...resolveCollectedData(session),
      service_id: serviceId,
    },
  }
}

export async function appendKbotMessage(body: Record<string, unknown>) {
  const session = await loadKbotSession(body.sessionId || body.session_id)
  const collectedData = resolveCollectedData(session)
  const serviceId = normalizeServiceId(body.serviceId || body.service_id || collectedData.service_id || DEFAULT_SERVICE_ID)
  const validation = validateServiceId(serviceId)
  if (!validation.ok) throw new Error(validation.error)

  const storedMessages = normalizeMessages(session.messages)
  const incomingMessages = normalizeMessages(body.messages)
  const persistedMessages = appendUserMessage(mergeMessages(storedMessages, incomingMessages), body.message)

  if (persistedMessages.length === storedMessages.length) {
    throw new Error('message o messages obbligatori.')
  }

  const promptSession = buildSessionForPrompt(session, serviceId)
  const skillNames = getSuiteAiServiceById(serviceId)?.skills || []
  const systemPrompt = buildSystemPromptV2(skillNames, promptSession)
  const modelMessages = compactMessages(persistedMessages).map(message => ({
    role: message.role,
    content: message.content,
  }))

  const anthropic = createAnthropicClient()
  const response = await anthropic.messages.create({
    model: MODEL,
    max_tokens: 1200,
    system: systemPrompt,
    messages: modelMessages,
  })

  const rawAssistantMessage = response.content[0]?.type === 'text' ? response.content[0].text : ''
  const v2Summary: V2SummaryData | null = extractV2Summary(rawAssistantMessage)
  const assistantMessage = normalizeAssistantReply(stripSummaryBlock(rawAssistantMessage))
  const updatedMessages: KbotMessage[] = [
    ...persistedMessages,
    { role: 'assistant', content: assistantMessage, ts: nowIso() },
  ]

  const updatedCollectedData: Record<string, unknown> = {
    ...collectedData,
    service_id: serviceId,
  }

  if (v2Summary) {
    Object.assign(updatedCollectedData, v2Summary)
    updatedCollectedData.extractedData = {
      ...(typeof updatedCollectedData.extractedData === 'object' && updatedCollectedData.extractedData
        ? updatedCollectedData.extractedData as Record<string, unknown>
        : {}),
      ...v2Summary,
    }
    updatedCollectedData.summary = v2Summary.summary || updatedCollectedData.summary
    updatedCollectedData.recommendedTier = v2Summary.recommendedTier || updatedCollectedData.recommendedTier
    updatedCollectedData.analysis_ready = true
  }

  const supabase = createSupabaseAdminClient()
  const { data, error } = await supabase
    .from('kbot_sessions')
    .update({
      messages: updatedMessages,
      collected_data: updatedCollectedData,
      step: Number(session.step || 1) + 1,
      updated_at: nowIso(),
    })
    .eq('id', session.id)
    .select('*')
    .single()

  if (error) throw new Error(error.message)

  return {
    message: assistantMessage,
    nextAction: v2Summary ? 'show_summary' : 'continue',
    summary: v2Summary || null,
    session: serializeKbotSession(data),
  }
}

export async function buildKbotReport(body: Record<string, unknown>) {
  const session = await loadKbotSession(body.sessionId || body.session_id)
  const collectedData = resolveCollectedData(session)
  const serviceId = normalizeServiceId(body.serviceId || body.service_id || collectedData.service_id || DEFAULT_SERVICE_ID)
  const validation = validateServiceId(serviceId)
  if (!validation.ok) throw new Error(validation.error)

  const service = getSuiteAiServiceById(serviceId)
  const messages = normalizeMessages(session.messages)
  const recommendedTier = collectedData.recommendedTier || collectedData.recommended_tier || service?.recommendedTier || null
  const reportData = generateReportData({
    ...session,
    messages,
    selectedService: service || serviceId,
    serviceId,
    recommendedTier,
    conversationSummary: collectedData.conversationSummary || collectedData.summary,
    extractedData: collectedData.extractedData || collectedData,
  })

  const updatedCollectedData = {
    ...collectedData,
    service_id: serviceId,
    reportData,
    report: reportData,
    summary: reportData.executiveSummary.text,
    conversationSummary: reportData.executiveSummary.text,
    recommendedTier,
    extractedData: collectedData.extractedData || collectedData,
  }

  const supabase = createSupabaseAdminClient()
  const { data, error } = await supabase
    .from('kbot_sessions')
    .update({
      status: 'report_ready',
      collected_data: updatedCollectedData,
      updated_at: nowIso(),
    })
    .eq('id', session.id)
    .select('*')
    .single()

  if (error) throw new Error(error.message)

  return {
    reportData,
    report: reportData,
    session: serializeKbotSession(data),
  }
}
