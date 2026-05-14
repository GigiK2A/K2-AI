import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ChatBubble } from './ChatBubble'
import { TeaserCard } from './TeaserCard'
import { PaymentBox } from './PaymentBox'

type PathType = 'A' | 'B' | 'unknown'
type KBotMode = 'report' | 'lead' | ''
type Stage = 'mode' | 'problem' | 'conversation'
type V2Summary = {
  businessType?: string; problem?: string; goal?: string; urgency?: string
  currentProcess?: string; dataAvailable?: string; notes?: string
  summary?: string; recommendedServiceId?: string; recommendedServiceName?: string
  recommendedTier?: 'HOST' | 'WEB' | 'STUDIO'; nextStep?: string
  budget?: string; integrations?: string
}
type ChatMsg = { role: 'user' | 'assistant'; text: string }
type UploadedFile = { name: string; type: string; size: number; publicUrl: string }
type AdaptiveAnswers = Record<string, string>

declare global {
  interface Window {
    posthog?: { capture: (event: string, props?: Record<string, any>) => void }
  }
}

const ROUTER_TEXT =
  "Quello che descrivi è un caso specifico su cui vuoi un'analisi rapida, o fa parte di un progetto più ampio che vorresti strutturare?"
const TYPING_FRAMES = ['K-BOT sta scrivendo...', 'K-BOT sta elaborando...', 'K-BOT sta ragionando...']
const ADAPTIVE_OTHER_LABEL = 'Altro da aggiungere (opzionale)'

type ServicePreset = { name: string; sector: string; contentType: string; url: string }
const SERVICE_MAP: Record<string, ServicePreset> = {
  P01: { name: 'Agenti AI Email & CRM',            sector: 'servizi-b2b',      contentType: 'processo-operativo', url: '/suite-ai/agenti-email-crm.html' },
  P02: { name: 'Automazioni Amministrative',        sector: 'commercialista',   contentType: 'bilancio', url: '/suite-ai/automazioni-amministrative.html' },
  P03: { name: 'AI Legale & Contratti',             sector: 'studio-legale',    contentType: 'contratto-legale', url: '/suite-ai/ai-legale-contratti.html' },
  P04: { name: 'AI Ingegneria & Progettazione',     sector: 'studio-ingegneria',contentType: 'documento-tecnico', url: '/suite-ai/ai-ingegneria-progettazione.html' },
  P05: { name: 'Microapp Documenti Tecnici',        sector: 'servizi-b2b',      contentType: 'documento-tecnico', url: '/suite-ai/microapp-documenti-tecnici.html' },
  P06: { name: 'AI Customer Service & Ticket',      sector: 'servizi-b2b',      contentType: 'processo-operativo', url: '/suite-ai/ai-customer-service-ticket.html' },
  P07: { name: 'RAG Knowledge Base',                sector: 'servizi-b2b',      contentType: 'generico', url: '/suite-ai/rag-knowledge-base.html' },
  P08: { name: 'AI Compliance & Audit',             sector: 'commercialista',   contentType: 'contratto-legale', url: '/suite-ai/ai-compliance-audit.html' },
  P09: { name: 'AI Controllo di Gestione',          sector: 'commercialista',   contentType: 'bilancio', url: '/suite-ai/ai-controllo-gestione-reporting.html' },
  P10: { name: 'Integrazione Gestionali & ERP',     sector: 'studio-ingegneria',contentType: 'documento-tecnico', url: '/suite-ai/integrazione-gestionali-erp.html' },
  P11: { name: 'AI Marketing & Contenuti',          sector: 'servizi-b2b',      contentType: 'marketing-seo', url: '/suite-ai/ai-marketing-contenuti.html' },
  P12: { name: 'Diagnosi Strategica PMI',           sector: 'servizi-b2b',      contentType: 'generico', url: '/suite-ai/diagnosi-strategica-pmi.html' },
  P13: { name: 'Agevolazioni & Finanza Agevolata',  sector: 'commercialista',   contentType: 'bilancio', url: '/suite-ai/agevolazioni-finanza-agevolata.html' },
  P14: { name: 'AI Edilizia & Appalti Pubblici',    sector: 'studio-ingegneria',contentType: 'documento-tecnico', url: '/suite-ai/ai-edilizia-appalti-pubblici.html' },
  P15: { name: 'AI HR & Recruiting',                sector: 'servizi-b2b',      contentType: 'processo-operativo', url: '/suite-ai/ai-hr-recruiting.html' },
  P16: { name: 'AI Real Estate & Tokenizzazione',   sector: 'servizi-b2b',      contentType: 'generico', url: '/suite-ai/ai-real-estate-tokenizzazione.html' },
  P17: { name: 'AI Data Analytics & BI',            sector: 'servizi-b2b',      contentType: 'generico', url: '/suite-ai/ai-data-analytics-bi.html' },
  P18: { name: 'AI UX & Design System',             sector: 'servizi-b2b',      contentType: 'processo-operativo', url: '/suite-ai/ai-ux-design-system.html' },
  P19: { name: 'AI Efficienza Energetica',          sector: 'studio-ingegneria',contentType: 'documento-tecnico', url: '/suite-ai/ai-efficienza-energetica.html' },
  P20: { name: 'AI Hospitality & Revenue',          sector: 'hospitality',      contentType: 'processo-operativo', url: '/suite-ai/ai-hospitality-revenue.html' },
}

function getServiceParam(): string | null {
  if (typeof window === 'undefined') return null
  const id = new URLSearchParams(window.location.search).get('service')
  return (id && SERVICE_MAP[id]) ? id : null
}

function getInitialService(): string | null {
  if (typeof window === 'undefined') return null
  const fromUrl = getServiceParam()
  if (fromUrl) return fromUrl
  const root = document.getElementById('kbot-react-root')
  const fromDataset = root?.dataset.service?.trim().toUpperCase()
  return fromDataset && SERVICE_MAP[fromDataset] ? fromDataset : null
}

const SECTORS = [
  { slug: 'studio-ingegneria', label: 'Studio ingegneria / architettura' },
  { slug: 'commercialista', label: 'Studio commercialista / CdL' },
  { slug: 'manifatturiero', label: 'Manifatturiero / produzione' },
  { slug: 'servizi-b2b', label: 'Servizi B2B / consulenza' },
  { slug: 'hospitality', label: 'Hospitality / ricettivo' },
  { slug: 'commercio-ecommerce', label: 'Commercio / e-commerce' },
  { slug: 'tlc', label: 'TLC / infrastrutture' },
  { slug: 'studio-legale', label: 'Studio legale' },
  { slug: 'pubblica-amministrazione', label: 'Pubblica Amministrazione' },
]

const SECTOR_PLACEHOLDERS: Record<string, string> = {
  'studio-ingegneria': 'Es. Perdiamo ore ogni settimana a compilare relazioni tecniche e computi metrici a mano.',
  'commercialista': 'Es. Riconciliare i movimenti bancari di 120 clienti ci occupa 2 giorni al mese.',
  'manifatturiero': 'Es. Il tracciamento della produzione è tutto su Excel, i dati arrivano in ritardo.',
  'servizi-b2b': 'Es. Il follow-up sui preventivi è manuale, molti lead si perdono senza risposta.',
  'hospitality': 'Es. Rispondo manualmente alle stesse domande OTA ogni giorno, mattina e sera.',
  'commercio-ecommerce': 'Es. La gestione resi e il customer service ci rubano 3 ore al giorno.',
  'tlc': 'Es. Compilare la documentazione PE per ogni sito richiede mezze giornate intere.',
  'studio-legale': 'Es. La ricerca giurisprudenziale per ogni fascicolo è lenta e ripetitiva.',
  'pubblica-amministrazione': 'Es. Processiamo centinaia di istanze standard con lo stesso iter manuale.',
}

const ERROR_MESSAGES: Record<string, string> = {
  '429': 'Stai andando troppo veloce. Aspetta qualche secondo e riprova.',
  '500': 'Problema tecnico temporaneo. Riprova tra 30 secondi.',
  '503': 'Il servizio è momentaneamente occupato. Riprova tra un minuto.',
  'network': 'Connessione assente o instabile. Controlla la rete e riprova.',
  'default': 'Qualcosa non ha funzionato. Riprova o scrivi a info@k2-ai.it.',
}

function friendlyError(err: unknown): string {
  const msg = String(err instanceof Error ? err.message : err || '')
  if (msg.includes('429') || msg.toLowerCase().includes('troppe') || msg.toLowerCase().includes('limite')) return ERROR_MESSAGES['429']
  if (msg.includes('503')) return ERROR_MESSAGES['503']
  if (msg.includes('500')) return ERROR_MESSAGES['500']
  if (msg.toLowerCase().includes('network') || msg.toLowerCase().includes('fetch') || msg.toLowerCase().includes('failed to fetch')) return ERROR_MESSAGES['network']
  return msg.length > 0 && msg.length < 120 ? msg : ERROR_MESSAGES['default']
}

function capture(event: string, props?: Record<string, any>) {
  window.posthog?.capture?.(event, props)
}

async function postJson(url: string, body: Record<string, any>) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data?.error || `Errore ${response.status}`)
  return data
}

async function fileToBase64(file: File): Promise<string> {
  return await new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error('Errore lettura file'))
    reader.onload = () => {
      const raw = String(reader.result || '')
      const base64 = raw.includes(',') ? raw.split(',')[1] : raw
      resolve(base64)
    }
    reader.readAsDataURL(file)
  })
}

function humanSize(size: number): string {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function wait(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function extractQuestions(text: string): string[] {
  const lines = text
    .replace(/```[\s\S]*?```/g, '')
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean)

  const collected: string[] = []

  for (const rawLine of lines) {
    const normalized = rawLine
      .replace(/\*\*/g, '')
      .replace(/^[-*]\s+/, '')
      .replace(/^\d+[.)]\s+/, '')
      .trim()

    if (!normalized) continue

    if (normalized.includes('?')) {
      const parts = (normalized.match(/[^?]*\?/g) || [])
        .map(part => part.trim())
        .filter(part => part.endsWith('?') && part.length > 8)
      if (parts.length > 0) {
        // Unifica domande consecutive nello stesso contesto in una singola domanda
        const merged = parts
          .map(part => part.replace(/\?+$/g, '').trim())
          .filter(Boolean)
          .join(' · ')
        if (merged.length > 8) collected.push(`${merged}?`)
      }
      continue
    }

    if (/^(\d+[.)]|[-*])\s+/.test(rawLine) && normalized.length > 14) {
      collected.push(normalized)
    }
  }

  const unique = Array.from(new Set(collected)).slice(0, 4)
  if (unique.length <= 1) return unique

  // Se sono domande consecutive sullo stesso tema, usa un solo campo
  const merged = unique
    .map(q => q.replace(/\?+$/g, '').trim())
    .filter(Boolean)
    .join(' · ')

  if (merged.length > 18 && merged.length < 420) {
    return [`${merged}?`]
  }

  return unique
}

function detectAdaptiveKind(question: string): 'email' | 'budget' | 'long' | 'text' {
  const q = question.toLowerCase()
  if (q.includes('email')) return 'email'
  if (q.includes('budget') || q.includes('euro') || q.includes('€') || q.includes('range')) return 'budget'
  if (q.includes('descrivi') || q.includes('dettaglia') || q.includes('spiega') || q.length > 95) return 'long'
  return 'text'
}

function prettifyAssistantText(text: string): string {
  const raw = String(text || '')
  if (!raw.trim()) return ''

  const isLikelyJsonDump =
    (/^\s*\{/.test(raw) && raw.length > 800) ||
    raw.includes('"meta"') ||
    raw.includes('"executive_summary"')

  if (isLikelyJsonDump) {
    return 'Analisi completata. Ho preparato il report strutturato e posso procedere con la generazione del PDF.'
  }

  return raw
    .replace(/```[\s\S]*?```/g, 'Contenuto tecnico elaborato.')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^\s*\|.*\|\s*$/gm, '')
    .replace(/^\s*[-=_]{3,}\s*$/gm, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/^\s*[-*]\s+/gm, '• ')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function prettifyUserText(text: string): string {
  const raw = String(text || '')
  if (!raw.trim()) return ''

  if (/Risposta(?: opzionale)?:/i.test(raw)) {
    const answers = raw
      .split('\n')
      .map(line => line.trim())
      .filter(line => /^Risposta(?: opzionale)?:/i.test(line))
      .map(line => line.replace(/^Risposta(?: opzionale)?:\s*/i, '').trim())
      .filter(answer => answer && !/^saltata$/i.test(answer))

    if (answers.length > 0) {
      return `Risposte inviate:\n${answers.map(a => `• ${a}`).join('\n')}`
    }

    return 'Risposte rapide saltate.'
  }

  if (raw.includes('Allegati caricati:')) {
    const lines = raw.split('\n')
    const clean: string[] = []
    for (const line of lines) {
      if (/^-\s+/.test(line) && /https?:\/\//.test(line)) {
        clean.push(line.replace(/\s+https?:\/\/\S+$/i, ''))
      } else if (!/^-\s+/.test(line) || !/https?:\/\//.test(line)) {
        clean.push(line)
      }
    }
    return clean.join('\n').trim()
  }

  return raw.trim()
}

function normalizeMsgText(text: string): string {
  return String(text || '').trim().toLowerCase().replace(/\s+/g, ' ')
}

function mergeDisplayMessages(items: ChatMsg[]): ChatMsg[] {
  const merged: ChatMsg[] = []

  for (const item of items) {
    const text = String(item.text || '').trim()
    if (!text) continue

    const last = merged[merged.length - 1]
    const normalized = normalizeMsgText(text)
    if (last && last.role === item.role) {
      const lastNormalized = normalizeMsgText(last.text)
      if (lastNormalized === normalized || lastNormalized.includes(normalized)) continue
      if (normalized.includes(lastNormalized)) {
        last.text = text
        continue
      }
      if (item.role === 'user' && text.length < 900 && last.text.length < 1800) {
        last.text = `${last.text}\n\n${text}`
        continue
      }
    }

    merged.push({ role: item.role, text })
  }

  return merged
}

const SECTOR_TO_CONTACT_SETTORE: Record<string, string> = {
  'studio-ingegneria': 'ops',
  'commercialista': 'finance',
  'manifatturiero': 'ops',
  'servizi-b2b': 'altro',
  'hospitality': 'altro',
  'commercio-ecommerce': 'marketing',
  'tlc': 'tech',
  'studio-legale': 'legale',
  'pubblica-amministrazione': 'altro',
}

export function KBot() {
  const [selectedService, setSelectedService] = useState<string | null>(getInitialService)
  const [stage, setStage] = useState<Stage>('problem')
  const [mode, setMode] = useState<KBotMode>('lead')
  const [selectedSector, setSelectedSector] = useState<string>(() => {
    const id = getInitialService(); return id ? SERVICE_MAP[id].sector : 'servizi-b2b'
  })
  const [contentType, setContentType] = useState<string>(() => {
    const id = getInitialService(); return id ? SERVICE_MAP[id].contentType : 'generico'
  })
  const [problem, setProblem] = useState('')
  const [sessionId, setSessionId] = useState('')
  const [path, setPath] = useState<PathType>('B')
  const [step, setStep] = useState(1)
  const [messages, setMessages] = useState<ChatMsg[]>(() => {
    const id = getInitialService()
    if (!id) return [{ role: 'assistant', text: 'Ciao, sono Lead K-BOT. Raccontami cosa vuoi automatizzare o migliorare: capisco se esiste già un prodotto nella Suite AI o preparo un brief per il team K2-AI.' }]
    const svc = SERVICE_MAP[id]
    return [
      { role: 'assistant', text: `Ciao, sono Lead K-BOT. Sei arrivato dal servizio ${svc.name}.` },
      { role: 'assistant', text: 'Descrivimi il tuo caso: verifico se questo prodotto è adatto, se c’è un servizio Suite migliore oppure se conviene passare al form contatti già precompilato.' },
    ]
  })
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [typingLabel, setTypingLabel] = useState('K-BOT sta scrivendo...')
  const [teaser, setTeaser] = useState<any>(null)
  const [pdfUrl, setPdfUrl] = useState('')
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false)
  const [contactSummary, setContactSummary] = useState('')
  const [conversationSummary, setConversationSummary] = useState('')
  const [queuedFiles, setQueuedFiles] = useState<File[]>([])
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)
  const [adaptiveQuestions, setAdaptiveQuestions] = useState<string[]>([])
  const [adaptiveAnswers, setAdaptiveAnswers] = useState<AdaptiveAnswers>({})
  const [paidReturn, setPaidReturn] = useState<{ sessionId: string | null; pdfUrl: string | null } | null>(null)
  const [cancelledReturn, setCancelledReturn] = useState(false)
  const [teaserLoading, setTeaserLoading] = useState(false)
  const [v2Summary, setV2Summary] = useState<V2Summary | null>(null)

  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const chatStreamRef = useRef<HTMLDivElement | null>(null)
  const rootRef = useRef<HTMLDivElement | null>(null)
  const inputRef = useRef<HTMLTextAreaElement | null>(null)

  const canReply = (inputValue.trim().length > 0 || queuedFiles.length > 0) && !isLoading
  const canStart = !isLoading
  const teaserSignals = useMemo(() => teaser?.segnali || [], [teaser])
  const hasAdaptiveForm = adaptiveQuestions.length > 0
  const canSendAdaptive = !isLoading

  useEffect(() => {
    if (chatStreamRef.current) {
      chatStreamRef.current.scrollTop = chatStreamRef.current.scrollHeight
    }
  }, [messages, isTyping, stage, teaser, contactSummary])

  useEffect(() => {
    document.body.classList.toggle('kbot-fullscreen-open', isFullscreen)
    return () => document.body.classList.remove('kbot-fullscreen-open')
  }, [isFullscreen])

  useEffect(() => {
    if (!isTyping) return
    let idx = 0
    const timer = window.setInterval(() => {
      idx = (idx + 1) % TYPING_FRAMES.length
      setTypingLabel(prev => (prev.startsWith('Sto analizzando') ? prev : TYPING_FRAMES[idx]))
    }, 900)
    return () => window.clearInterval(timer)
  }, [isTyping])

  // Rileva ritorno da pagamento Stripe (paid o cancelled)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    window.history.replaceState({}, '', window.location.pathname)

    if (params.get('paid') === '1') {
      const pendingSessionId = sessionStorage.getItem('kbot_pending_session') || null
      sessionStorage.removeItem('kbot_pending_session')
      setPaidReturn({ sessionId: pendingSessionId, pdfUrl: null })
      capture('kbot_payment_completed', { session_id: pendingSessionId })
    } else if (params.get('cancelled') === '1') {
      sessionStorage.removeItem('kbot_pending_session')
      setCancelledReturn(true)
    }
  }, [])

  useEffect(() => {
    if (!paidReturn || paidReturn.pdfUrl || !paidReturn.sessionId) return

    let attempts = 0
    const MAX_ATTEMPTS = 24 // 2 minuti a 5s

    async function checkStatus() {
      attempts++
      if (attempts > MAX_ATTEMPTS) {
        clearInterval(timer)
        return
      }
      try {
        const resp = await fetch(`/api/kbot/status?id=${encodeURIComponent(paidReturn!.sessionId!)}`)
        const data = await resp.json().catch(() => ({}))
        if (data.pdf_url) {
          setPaidReturn(prev => prev ? { ...prev, pdfUrl: data.pdf_url } : null)
          clearInterval(timer)
        }
      } catch {}
    }

    checkStatus()
    const timer = setInterval(checkStatus, 5000)
    return () => clearInterval(timer)
  }, [paidReturn?.sessionId])

  function addMessage(role: 'user' | 'assistant', text: string) {
    const formatted = role === 'assistant' ? prettifyAssistantText(text) : prettifyUserText(text)
    if (!formatted) return
    setMessages(prev => mergeDisplayMessages([...prev, { role, text: formatted }]))
  }

  function syncConversationState(data: any) {
    const nextSummary =
      data?.conversation_summary ||
      data?.session?.extractedData?.conversationSummary ||
      data?.session?.extractedData?.contactPrefillSummary ||
      ''
    if (nextSummary) setConversationSummary(String(nextSummary))

    const nextContactSummary =
      data?.contact_summary ||
      data?.session?.extractedData?.contactPrefillSummary ||
      data?.session?.extractedData?.summary ||
      data?.v2_summary?.summary ||
      ''
    if (nextContactSummary && data?.next_action === 'show_contact_form') {
      setContactSummary(String(nextContactSummary))
    }

    if (data?.v2_summary) {
      setV2Summary(data.v2_summary)
    } else if (data?.summary && typeof data.summary === 'object') {
      setV2Summary(data.summary)
    }
  }

  function maybeShowAdaptiveForm(text: string) {
    const questions = extractQuestions(text)
    if (questions.length > 1 && stage === 'conversation') {
      const nextAnswers: AdaptiveAnswers = {}
      for (const q of questions) {
        nextAnswers[q] = adaptiveAnswers[q] || ''
      }
      nextAnswers[ADAPTIVE_OTHER_LABEL] = adaptiveAnswers[ADAPTIVE_OTHER_LABEL] || ''
      setAdaptiveQuestions(questions)
      setAdaptiveAnswers(nextAnswers)
      return
    }
    setAdaptiveQuestions([])
    setAdaptiveAnswers({})
  }

  async function botSay(text: string, delay = 180) {
    setTypingLabel('K-BOT sta scrivendo...')
    setIsTyping(true)
    await wait(delay)
    setIsTyping(false)
    addMessage('assistant', text)
    maybeShowAdaptiveForm(text)
  }

  async function botAnalyzeThenSay(text: string) {
    setTypingLabel('Sto analizzando il tuo caso...')
    setIsTyping(true)
    await wait(900)
    setIsTyping(false)
    addMessage('assistant', text)
    maybeShowAdaptiveForm(text)
  }

  function resetChat() {
    setSelectedService(null)
    setStage('problem')
    setMode('lead')
    setSelectedSector('servizi-b2b')
    setContentType('generico')
    setProblem('')
    setSessionId('')
    try { sessionStorage.removeItem('kbot.site_session_id') } catch {}
    setPath('B')
    setStep(1)
    setMessages([{ role: 'assistant', text: 'Ciao, sono Lead K-BOT. Raccontami cosa vuoi automatizzare o migliorare: capisco se esiste già un prodotto nella Suite AI o preparo un brief per il team K2-AI.' }])
    setInputValue('')
    setIsLoading(false)
    setIsTyping(false)
    setTypingLabel('K-BOT sta scrivendo...')
    setTeaser(null)
    setPdfUrl('')
    setIsGeneratingPdf(false)
    setContactSummary('')
    setConversationSummary('')
    setQueuedFiles([])
    setIsDragOver(false)
    setIsFullscreen(false)
    setAdaptiveQuestions([])
    setAdaptiveAnswers({})
    setV2Summary(null)
  }

  async function toggleFullscreen() {
    setIsFullscreen(prev => !prev)
  }

  async function onSelectMode(nextMode: Exclude<KBotMode, ''>) {
    if (stage !== 'mode' || isLoading) return

    setMode(nextMode)
    setPath(nextMode === 'lead' ? 'B' : 'A')
    // Default sector/contentType — v2 flow collects these naturally via conversation
    setSelectedSector('servizi-b2b')
    setContentType('generico')
    addMessage('user', nextMode === 'report' ? 'Voglio un report di analisi' : 'Voglio capire se parlarne con voi')
    await botSay(
      nextMode === 'report'
        ? 'Perfetto. Descrivimi il caso o carica un documento: raccoglierò il contesto e produrrò il report.'
        : 'Perfetto. Raccontami il tuo caso: capirò contesto, urgenza e fit, poi ti preparo un riepilogo ordinato per il team.',
    )
    setStage('problem')
  }

  async function startFromProblem() {
    if (!canStart) return

    setIsLoading(true)
    setTypingLabel('K-BOT sta elaborando la tua richiesta…')
    setIsTyping(true)
    try {
      const session = await postJson('/api/kbot/session', {
        sector: selectedSector,
        mode,
        content_type: contentType || undefined,
        ...(selectedService ? { service_id: selectedService } : {}),
      })
      const sid = session.session_id
      setSessionId(sid)
      // Expose for cross-bot bridge (site widget → kbot standalone /app/?continue=<sid>)
      try { sessionStorage.setItem('kbot.site_session_id', sid) } catch {}
      capture('kbot_started', { sector: selectedSector, mode })

      const initialProblem = problem.trim() || 'Non ho dettagli aggiuntivi al momento.'
      addMessage('user', initialProblem)
      capture('kbot_problem_submitted', { sector: selectedSector, mode, has_problem: problem.trim().length > 0 })
      const outgoingMessages = mergeDisplayMessages([...messages, { role: 'user', text: initialProblem }])
      const data = await postJson('/api/kbot/chat', {
        session_id: sid,
        message: initialProblem,
        step: 1,
        messages: outgoingMessages.map(message => ({ role: message.role, content: message.text })),
      })
      syncConversationState(data)
      setIsTyping(false)

      const startPath: PathType = mode === 'lead' ? 'B' : 'A'
      setPath(startPath)
      setStep(data.session?.step || 2)
      setStage('conversation')

      if (data.pdf_url && !pdfUrl) setPdfUrl(data.pdf_url)

      if (data.next_action === 'show_summary' && data.v2_summary) {
        if (mode === 'report' || startPath === 'A') {
          await botAnalyzeThenSay(data.message || 'Analisi completata.')
          await fetchTeaser()
        } else {
          await botSay(data.message || 'Ok, continuiamo da qui.', 120)
          setContactSummary(data.contact_summary || data.v2_summary.summary || data.message || '')
        }
      } else {
        await botSay(data.message || 'Ok, continuiamo da qui.', 120)
        if (mode === 'report' && startPath === 'A' && !teaser &&
            (data.next_action === 'show_report' || data.next_action === 'show_teaser' || data.pdf_url)) {
          await fetchTeaser()
        }
        if (mode === 'lead' && data.next_action === 'show_contact_form') {
          setContactSummary(data.contact_summary || data.message || '')
        }
      }
    } catch (error) {
      setIsTyping(false)
      addMessage('assistant', friendlyError(error))
    } finally {
      setIsLoading(false)
    }
  }

  async function uploadQueuedFiles(): Promise<UploadedFile[]> {
    if (!sessionId || queuedFiles.length === 0) return []

    const payloadFiles = await Promise.all(
      queuedFiles.map(async file => ({
        name: file.name,
        type: file.type || 'application/octet-stream',
        size: file.size,
        base64: await fileToBase64(file),
      })),
    )

    const resp = await postJson('/api/kbot/upload', {
      session_id: sessionId,
      files: payloadFiles,
    })

    return Array.isArray(resp.files) ? resp.files : []
  }

  async function runConversationTurn(rawText: string) {
    if ((!rawText.trim() && queuedFiles.length === 0) || !sessionId || isLoading) return
    setIsLoading(true)
    setTypingLabel(queuedFiles.length > 0 ? 'Sto caricando gli allegati…' : 'K-BOT sta elaborando la tua risposta…')
    setIsTyping(true)
    try {
      const uploaded = await uploadQueuedFiles()
      if (uploaded.length > 0) {
        setTypingLabel('Allegati ricevuti. Sto analizzando il contenuto…')
      }
      const fileContext = uploaded.length
        ? `\n\nAllegati caricati:\n${uploaded.map(f => `- ${f.name} (${humanSize(f.size)})`).join('\n')}`
        : ''

      const finalText = `${rawText.trim() || 'Ho allegato dei file da analizzare. Procedi con l’analisi del contenuto.'}${fileContext}`
      const userDisplayText = `${rawText.trim() || 'Ho allegato dei file da analizzare.'}${fileContext}`
      const outgoingMessages = mergeDisplayMessages([...messages, { role: 'user', text: prettifyUserText(userDisplayText) }])

      addMessage('user', userDisplayText)
      setInputValue('')
      setQueuedFiles([])
      setAdaptiveQuestions([])
      setAdaptiveAnswers({})

      const currentStep = step
      setTypingLabel('Sto preparando la risposta…')
      const data = await postJson('/api/kbot/chat', {
        session_id: sessionId,
        message: finalText,
        step: currentStep,
        messages: outgoingMessages.map(message => ({ role: message.role, content: message.text })),
      })
      syncConversationState(data)

      const nextStep = data.session?.step || currentStep + 1
      const nextPath: PathType = data.path || path
      setStep(nextStep)
      setPath(nextPath)
      setIsTyping(false)

      if (data.pdf_url && !pdfUrl) setPdfUrl(data.pdf_url)

      if (data.next_action === 'show_summary' && data.v2_summary) {
        if (mode === 'report' || nextPath === 'A') {
          await botAnalyzeThenSay(data.message || 'Analisi completata.')
          await fetchTeaser()
        } else {
          await botSay(data.message || '')
          setContactSummary(data.contact_summary || data.v2_summary.summary || data.message || '')
        }
      } else if (mode === 'report' && nextPath === 'A' && !teaser &&
          (data.next_action === 'show_teaser' || data.next_action === 'show_report' || data.pdf_url)) {
        await botAnalyzeThenSay(data.message || 'Analisi completata.')
        await fetchTeaser()
      } else {
        await botSay(data.message || '')
      }

      if (nextPath === 'B' && data.next_action === 'show_contact_form') {
        setContactSummary(data.contact_summary || data.message || '')
      }
    } catch (error) {
      setIsTyping(false)
      addMessage('assistant', friendlyError(error))
    } finally {
      setIsLoading(false)
    }
  }

  async function sendConversationMessage() {
    const text = inputValue.trim()
    await runConversationTurn(text)
  }

  async function submitAdaptiveForm() {
    if (!canSendAdaptive) return
    const payloadItems = adaptiveQuestions.map((q, idx) => {
      const value = (adaptiveAnswers[q] || '').trim()
      return `${idx + 1}. ${q}\nRisposta opzionale: ${value || 'Saltata'}`
    })
    const payloadCore = payloadItems.join('\n\n')
    const extra = (adaptiveAnswers[ADAPTIVE_OTHER_LABEL] || '').trim()
    const payload = extra ? `${payloadCore}\n\nAltro contesto:\n${extra}` : payloadCore
    await runConversationTurn(payload)
  }


  async function fetchTeaser() {
    if (!sessionId || teaser) return
    setTeaserLoading(true)
    try {
      const data = await postJson('/api/kbot/teaser', { session_id: sessionId })
      if (data?.teaser) setTeaser(data.teaser)
    } catch (error) {
      addMessage('assistant', friendlyError(error))
    } finally {
      setTeaserLoading(false)
    }
  }

  async function generatePdfTest() {
    if (!sessionId || isGeneratingPdf) return
    setIsGeneratingPdf(true)
    try {
      const resp = await postJson('/api/kbot/generate-pdf', { session_id: sessionId, test_mode: true })
      if (resp?.pdf_url) {
        setPdfUrl(resp.pdf_url)
      } else {
        addMessage('assistant', 'Non sono riuscito a generare il report in questo tentativo. Riprova tra poco.')
      }
    } catch (error) {
      addMessage('assistant', friendlyError(error))
    } finally {
      setIsGeneratingPdf(false)
    }
  }

  function buildContactPrefill(summary?: string): string {
    const sectorLabel = SECTORS.find(s => s.slug === selectedSector)?.label || ''
    const serviceName = selectedService && SERVICE_MAP[selectedService] ? SERVICE_MAP[selectedService].name : ''
    const summaryText = (summary || contactSummary || conversationSummary || v2Summary?.summary || '').trim()
    const userContext = messages
      .filter(message => message.role === 'user')
      .map(message => message.text.trim())
      .filter(Boolean)
      .slice(-6)
      .join('\n\n')

    return [
      serviceName ? `Servizio di partenza: ${serviceName}` : '',
      sectorLabel ? `Settore: ${sectorLabel}` : '',
      v2Summary?.recommendedTier ? `Tier consigliato: ${v2Summary.recommendedTier}` : '',
      v2Summary?.recommendedServiceName ? `Servizio consigliato: ${v2Summary.recommendedServiceName}` : '',
      summaryText ? `Sintesi K-BOT:\n${summaryText}` : '',
      userContext ? `Contesto conversazione:\n${userContext}` : '',
    ].filter(Boolean).join('\n\n').slice(0, 3000)
  }

  function goToContacts(summary?: string) {
    const text = buildContactPrefill(summary)
    const settore = SECTOR_TO_CONTACT_SETTORE[selectedSector] || ''
    const sectorLabel = SECTORS.find(s => s.slug === selectedSector)?.label || ''
    const recommendedId = String(v2Summary?.recommendedServiceId || selectedService || '').toUpperCase()
    const recommendedService = SERVICE_MAP[recommendedId]
    try {
      sessionStorage.setItem('kai-contact-prefill', text)
      sessionStorage.setItem('kai-contact-prefill-meta', `Lead da K-BOT — settore: ${sectorLabel}, sessione: ${sessionId}`)
      sessionStorage.setItem('kai-contact-prefill-source', 'k-bot_lead')
      sessionStorage.setItem('kai-contact-prefill-fields', JSON.stringify({
        sector: settore,
        company_role: v2Summary?.businessType || '',
        service: selectedService || '',
        recommendedTier: v2Summary?.recommendedTier || '',
      }))
    } catch {}
    const params = new URLSearchParams()
    if (settore) params.set('settore', settore)
    if (recommendedService) {
      params.set('pkg', recommendedId)
      params.set('pkg_title', recommendedService.name)
    }
    capture('kbot_contact_clicked', { sector: selectedSector, session_id: sessionId })
    window.location.href = `/contatti.html${params.toString() ? `?${params.toString()}` : ''}`
  }

  function crossoverToB() {
    setPath('B')
    setContactSummary('__pending__')
    capture('kbot_crossover_clicked', { from: 'A', to: 'B' })
  }

  function onFilesSelected(list: FileList | null) {
    if (!list) return
    const picked = Array.from(list)
    setQueuedFiles(prev => [...prev, ...picked].slice(0, 5))
  }

  function onDropFiles(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault()
    event.stopPropagation()
    setIsDragOver(false)
    if (event.dataTransfer?.files?.length) onFilesSelected(event.dataTransfer.files)
  }

  function fileIcon(name: string): string {
    const lower = name.toLowerCase()
    if (lower.endsWith('.pdf')) return 'PDF'
    if (lower.endsWith('.xls') || lower.endsWith('.xlsx') || lower.endsWith('.csv')) return 'XLS'
    if (lower.endsWith('.doc') || lower.endsWith('.docx')) return 'DOC'
    if (lower.endsWith('.png') || lower.endsWith('.jpg') || lower.endsWith('.jpeg')) return 'IMG'
    if (lower.endsWith('.txt')) return 'TXT'
    return 'FILE'
  }

  function removeQueuedFile(name: string) {
    setQueuedFiles(prev => prev.filter(f => f.name !== name))
  }

  return (
    <>
      <div className={`kbot-overlay ${isFullscreen ? 'on' : ''}`} onClick={toggleFullscreen} />
      <div ref={rootRef} className={`kbot-shell lead-router ${isFullscreen ? 'fullscreen' : ''}`}>

      {cancelledReturn && (
        <div className="kbot-cancelled-banner">
          <span>Pagamento annullato — nessun importo addebitato. Puoi riprovare quando vuoi.</span>
          <button type="button" className="kbot-paid-close" onClick={() => setCancelledReturn(false)} aria-label="Chiudi">×</button>
        </div>
      )}

      {paidReturn && (
        <div className="kbot-paid-banner">
          <div className="kbot-paid-banner-body">
            {paidReturn.pdfUrl ? (
              <>
                <span className="kbot-paid-icon">✓</span>
                <span>Report pronto.</span>
                <a href={paidReturn.pdfUrl} target="_blank" rel="noreferrer" className="kbot-paid-link">Apri il PDF →</a>
              </>
            ) : (
              <>
                <span className="kbot-paid-icon kbot-paid-spinning">⟳</span>
                <span>Pagamento confermato. PDF in generazione — arriva via email tra pochi minuti.</span>
              </>
            )}
          </div>
          <button type="button" className="kbot-paid-close" onClick={() => setPaidReturn(null)} aria-label="Chiudi">×</button>
        </div>
      )}

      <div className="kbot-header">
        <div className="kbot-header-main">
          <span className="kbot-status-dot" />
          <div>
            <div className="kbot-header-text">K-BOT</div>
            <div className="kbot-header-sub">Lead router · Suite AI</div>
          </div>
        </div>
        <div className="kbot-header-actions">
          <button type="button" className="kbot-top-btn" onClick={resetChat}>RESET CHAT</button>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={e => onFilesSelected(e.target.files)}
        style={{ display: 'none' }}
        accept=".pdf,.xls,.xlsx,.csv,.doc,.docx,.txt,.png,.jpg,.jpeg"
      />

      <div className="kbot-chat-stream" ref={chatStreamRef}>
        {messages.map((m, i) => (
          <ChatBubble key={`${m.role}-${i}`} role={m.role} text={m.text} />
        ))}

        {isTyping && (
          <div className="kbot-typing-row">
            <span className="kbot-avatar typing">K</span>
            <span className="td" />
            <span className="td" />
            <span className="td" />
            <span className="kbot-typing-label">{typingLabel}</span>
          </div>
        )}

        {v2Summary && !teaser && !contactSummary && (
          <div className="kbot-v2-summary msg-in">
            <div className="kbot-v2-summary-header">
              {v2Summary.businessType && (
                <span className="kbot-v2-chip">{v2Summary.businessType}</span>
              )}
              {v2Summary.urgency && (
                <span className={`kbot-v2-urgency kbot-v2-urgency-${v2Summary.urgency}`}>{v2Summary.urgency}</span>
              )}
              {v2Summary.recommendedTier && (
                <span className={`kbot-v2-tier kbot-v2-tier-${v2Summary.recommendedTier.toLowerCase()}`}>
                  {v2Summary.recommendedTier}
                </span>
              )}
            </div>
            {v2Summary.summary && (
              <p className="kbot-v2-summary-text">{v2Summary.summary}</p>
            )}
            {v2Summary.recommendedServiceName && (
              <div className="kbot-v2-service">
                <span className="kbot-v2-service-label">Servizio consigliato</span>
                <span className="kbot-v2-service-name">{v2Summary.recommendedServiceName}</span>
              </div>
            )}
            {(v2Summary.integrations || v2Summary.budget) && (
              <div className="kbot-v2-details">
                {v2Summary.integrations && <span>Strumenti: {v2Summary.integrations}</span>}
                {v2Summary.budget && <span>Budget: {v2Summary.budget}</span>}
              </div>
            )}
            {v2Summary.nextStep && (
              <p className="kbot-v2-next">{v2Summary.nextStep}</p>
            )}
          </div>
        )}

        {stage === 'problem' && (
          <div className="kbot-option-panel msg-in">
            {selectedService && SERVICE_MAP[selectedService] && (
              <div className="kbot-service-badge">
                <span className="kbot-service-badge-dot" />
                {SERVICE_MAP[selectedService].name}
                <a href="/suite-ai.html" className="kbot-service-badge-change">Cambia</a>
              </div>
            )}
            <p className="kbot-stage-label">Descrivi in parole tue cosa ti serve</p>
            <textarea
              className="kbot-problem-textarea"
              value={problem}
              onChange={e => setProblem(e.target.value)}
              placeholder={SECTOR_PLACEHOLDERS[selectedSector] || 'Descrivi il processo che ti costa più tempo: cosa succede oggi, dove si perde tempo, quali strumenti usi.'}
            />
            <div className="kbot-choice-row">
              <button type="button" className="kbot-choice-chip" onClick={startFromProblem} disabled={!canStart}>
                Fai la scrematura →
              </button>
            </div>
          </div>
        )}

        {hasAdaptiveForm && !contactSummary && !teaser && (
          <div className="kbot-option-panel msg-in">
            <p className="kbot-stage-label">Compila le risposte rapide (tutto opzionale)</p>
            <div className="kbot-adaptive-form">
              {adaptiveQuestions.map(question => (
                <label key={question} className="kbot-adaptive-field">
                  <span>{question}</span>
                  {detectAdaptiveKind(question) === 'long' ? (
                    <textarea
                      value={adaptiveAnswers[question] || ''}
                      onChange={e => setAdaptiveAnswers(prev => ({ ...prev, [question]: e.target.value }))}
                      placeholder="Risposta opzionale…"
                    />
                  ) : detectAdaptiveKind(question) === 'budget' ? (
                    <select
                      value={adaptiveAnswers[question] || ''}
                      onChange={e => setAdaptiveAnswers(prev => ({ ...prev, [question]: e.target.value }))}
                    >
                      <option value="">Salta o scegli un range…</option>
                      <option value="< 2.000€">{"< 2.000€"}</option>
                      <option value="2.000€ - 5.000€">{"2.000€ - 5.000€"}</option>
                      <option value="5.000€ - 10.000€">{"5.000€ - 10.000€"}</option>
                      <option value="> 10.000€">{"> 10.000€"}</option>
                    </select>
                  ) : (
                    <input
                      type={detectAdaptiveKind(question) === 'email' ? 'email' : 'text'}
                      value={adaptiveAnswers[question] || ''}
                      onChange={e => setAdaptiveAnswers(prev => ({ ...prev, [question]: e.target.value }))}
                      placeholder="Risposta opzionale…"
                    />
                  )}
                </label>
              ))}
              <label className="kbot-adaptive-field">
                <span>{ADAPTIVE_OTHER_LABEL}</span>
                <textarea
                  value={adaptiveAnswers[ADAPTIVE_OTHER_LABEL] || ''}
                  onChange={e => setAdaptiveAnswers(prev => ({ ...prev, [ADAPTIVE_OTHER_LABEL]: e.target.value }))}
                  placeholder="Indicazioni extra opzionali…"
                />
              </label>
              <button type="button" className="kbot-choice-chip" onClick={submitAdaptiveForm} disabled={!canSendAdaptive}>
                Invia / salta
              </button>
            </div>
          </div>
        )}

        {teaserLoading && !teaser && (
          <div className="kbot-teaser-wrap msg-in">
            <h4>Analisi in corso…</h4>
            <div className="kbot-teaser-grid">
              {[0, 1, 2].map(i => (
                <div key={i} className="kbot-teaser-card kbot-skeleton">
                  <div className="kbot-skeleton-line kbot-skeleton-badge" />
                  <div className="kbot-skeleton-line kbot-skeleton-title" />
                  <div className="kbot-skeleton-line" />
                  <div className="kbot-skeleton-line kbot-skeleton-short" />
                </div>
              ))}
            </div>
          </div>
        )}

        {teaser && path === 'A' && (
          <div className="kbot-teaser-wrap msg-in">
            <h4>Segnali emersi</h4>
            <div className="kbot-teaser-grid">
              {teaserSignals.map((signal: any, idx: number) => (
                <TeaserCard key={idx} signal={signal} />
              ))}
            </div>
            <p className="kbot-hook">{teaser.hook_pdf}</p>
            {sessionId && (
              <PaymentBox
                sessionId={sessionId}
                isGeneratingPdf={isGeneratingPdf}
                pdfUrl={pdfUrl}
                onTestGenerate={generatePdfTest}
              />
            )}
            <button type="button" className="kbot-link-btn" onClick={crossoverToB}>Preferisci parlare direttamente con il team? →</button>
          </div>
        )}
      </div>

      {queuedFiles.length > 0 && (
        <div className="kbot-files-preview">
          {queuedFiles.map(file => (
            <span key={file.name} className="kbot-file-chip">
              <span className="kbot-file-icon">{fileIcon(file.name)}</span>
              {file.name} ({humanSize(file.size)})
              <button type="button" onClick={() => removeQueuedFile(file.name)}>×</button>
            </span>
          ))}
        </div>
      )}

      {stage === 'conversation' && !hasAdaptiveForm && !contactSummary && !teaser && (
        <div
          className={`kbot-input-row ${isDragOver ? 'drag-over' : ''}`}
          onDragOver={event => {
            event.preventDefault()
            event.stopPropagation()
            setIsDragOver(true)
          }}
          onDragLeave={event => {
            event.preventDefault()
            event.stopPropagation()
            setIsDragOver(false)
          }}
          onDrop={onDropFiles}
        >
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={e => {
              if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                e.preventDefault()
                if (canReply) sendConversationMessage()
              }
            }}
            placeholder="Scrivi qui la tua risposta…"
          />

          <div className="kbot-input-actions">
            <button type="button" className="kbot-attach-btn" onClick={() => fileInputRef.current?.click()}>Allega file</button>
            <button type="button" onClick={sendConversationMessage} disabled={!canReply}>Invia</button>
          </div>
          <div className="kbot-drop-hint">Trascina qui PDF, bilanci o documenti da analizzare (max 5 file)</div>
        </div>
      )}

      {contactSummary && contactSummary !== '__pending__' && (
        <div className="kbot-contact-cta">
          {(() => {
            const serviceId = String(v2Summary?.recommendedServiceId || '').toUpperCase()
            const service = SERVICE_MAP[serviceId]
            if (!service) return null
            return (
              <div className="kbot-route-card">
                <span className="kbot-route-label">Servizio Suite più vicino</span>
                <strong>{service.name}</strong>
                {v2Summary?.summary && <p>{v2Summary.summary}</p>}
                <a href={service.url} className="kbot-route-link">Apri scheda prodotto →</a>
              </div>
            )
          })()}
          <p className="kbot-contact-cta-hint">Ho preparato un riepilogo del tuo caso. Se serve un perimetro custom, il form contatti sarà già compilato.</p>
          <button type="button" className="kbot-btn-primary kbot-contact-btn" onClick={() => goToContacts()}>
            Vai al form precompilato →
          </button>
        </div>
      )}

      {contactSummary === '__pending__' && (
        <div className="kbot-contact-cta">
          <button type="button" className="kbot-btn-primary kbot-contact-btn" onClick={() => goToContacts()}>
            Contattaci →
          </button>
        </div>
      )}
      </div>
    </>
  )
}
