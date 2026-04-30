import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ChatBubble } from './ChatBubble'
import { TeaserCard } from './TeaserCard'
import { PaymentBox } from './PaymentBox'

type PathType = 'A' | 'B' | 'unknown'
type KBotMode = 'report' | 'lead' | ''
type Stage = 'mode' | 'sector' | 'content-type' | 'problem' | 'router' | 'conversation'
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

const CONTENT_TYPES = [
  { slug: 'bilancio',          label: 'Bilancio / contabilità',          desc: 'Bilancio, conto economico, nota integrativa, rendiconto' },
  { slug: 'contratto-legale',  label: 'Contratto / documento legale',    desc: 'Contratti, accordi, pareri, documenti normativi' },
  { slug: 'processo-operativo',label: 'Processo operativo / flusso',     desc: 'Flussi interni, CRM, ERP, procedure aziendali' },
  { slug: 'marketing-seo',     label: 'Marketing / SEO / digitale',      desc: 'Sito, campagne, analytics, posizionamento' },
  { slug: 'documento-tecnico', label: 'Documento tecnico / progettuale', desc: 'Relazioni, computi, tavole, perizie, capitolati' },
  { slug: 'generico',          label: 'Altro',                           desc: 'Qualsiasi altro tipo di documento o analisi' },
]

type ServicePreset = { name: string; sector: string; contentType: string }
const SERVICE_MAP: Record<string, ServicePreset> = {
  P01: { name: 'Agenti AI Email & CRM',            sector: 'servizi-b2b',      contentType: 'processo-operativo' },
  P02: { name: 'Automazioni Amministrative',        sector: 'commercialista',   contentType: 'bilancio' },
  P03: { name: 'AI Legale & Contratti',             sector: 'studio-legale',    contentType: 'contratto-legale' },
  P04: { name: 'AI Ingegneria & Progettazione',     sector: 'studio-ingegneria',contentType: 'documento-tecnico' },
  P05: { name: 'Microapp Documenti Tecnici',        sector: 'servizi-b2b',      contentType: 'documento-tecnico' },
  P06: { name: 'AI Customer Service & Ticket',      sector: 'servizi-b2b',      contentType: 'processo-operativo' },
  P07: { name: 'RAG Knowledge Base',                sector: 'servizi-b2b',      contentType: 'generico' },
  P08: { name: 'AI Compliance & Audit',             sector: 'commercialista',   contentType: 'contratto-legale' },
  P09: { name: 'AI Controllo di Gestione',          sector: 'commercialista',   contentType: 'bilancio' },
  P10: { name: 'Integrazione Gestionali & ERP',     sector: 'studio-ingegneria',contentType: 'documento-tecnico' },
  P11: { name: 'AI Marketing & Contenuti',          sector: 'servizi-b2b',      contentType: 'marketing-seo' },
  P12: { name: 'Diagnosi Strategica PMI',           sector: 'servizi-b2b',      contentType: 'generico' },
  P13: { name: 'Agevolazioni & Finanza Agevolata',  sector: 'commercialista',   contentType: 'bilancio' },
  P14: { name: 'AI Edilizia & Appalti Pubblici',    sector: 'studio-ingegneria',contentType: 'documento-tecnico' },
  P15: { name: 'AI HR & Recruiting',                sector: 'servizi-b2b',      contentType: 'processo-operativo' },
  P16: { name: 'AI Real Estate & Tokenizzazione',   sector: 'servizi-b2b',      contentType: 'generico' },
  P17: { name: 'AI Data Analytics & BI',            sector: 'servizi-b2b',      contentType: 'generico' },
  P18: { name: 'AI UX & Design System',             sector: 'servizi-b2b',      contentType: 'processo-operativo' },
  P19: { name: 'AI Efficienza Energetica',          sector: 'studio-ingegneria',contentType: 'documento-tecnico' },
  P20: { name: 'AI Hospitality & Revenue',          sector: 'hospitality',      contentType: 'processo-operativo' },
}

function getServiceParam(): string | null {
  if (typeof window === 'undefined') return null
  const id = new URLSearchParams(window.location.search).get('service')
  return (id && SERVICE_MAP[id]) ? id : null
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

  if (raw.includes('Risposta:')) {
    const answers = raw
      .split('\n')
      .map(line => line.trim())
      .filter(line => /^Risposta:/i.test(line))
      .map(line => line.replace(/^Risposta:\s*/i, '').trim())
      .filter(Boolean)

    if (answers.length > 0) {
      return `Risposte inviate:\n${answers.map(a => `• ${a}`).join('\n')}`
    }
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
  const [selectedService, setSelectedService] = useState<string | null>(getServiceParam)
  const [stage, setStage] = useState<Stage>(() => getServiceParam() ? 'problem' : 'mode')
  const [mode, setMode] = useState<KBotMode>(() => getServiceParam() ? 'report' : '')
  const [selectedSector, setSelectedSector] = useState<string>(() => {
    const id = getServiceParam(); return id ? SERVICE_MAP[id].sector : ''
  })
  const [contentType, setContentType] = useState<string>(() => {
    const id = getServiceParam(); return id ? SERVICE_MAP[id].contentType : ''
  })
  const [problem, setProblem] = useState('')
  const [sessionId, setSessionId] = useState('')
  const [path, setPath] = useState<PathType>(() => getServiceParam() ? 'A' : 'unknown')
  const [step, setStep] = useState(1)
  const [messages, setMessages] = useState<ChatMsg[]>(() => {
    const id = getServiceParam()
    if (!id) return [{ role: 'assistant', text: 'Ciao, sono K-BOT. Vuoi analizzare un documento/caso e ottenere un report, oppure vuoi capire se ha senso parlarne con il team K2-AI?' }]
    const svc = SERVICE_MAP[id]
    return [
      { role: 'assistant', text: `Ciao, sono K-BOT. Sei arrivato dal servizio ${svc.name}.` },
      { role: 'assistant', text: 'Descrivimi il tuo caso oppure carica direttamente un documento. Lo analizzo con le skill specifiche per questo servizio e produco la diagnosi operativa.' },
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
  const [queuedFiles, setQueuedFiles] = useState<File[]>([])
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)
  const [adaptiveQuestions, setAdaptiveQuestions] = useState<string[]>([])
  const [adaptiveAnswers, setAdaptiveAnswers] = useState<AdaptiveAnswers>({})
  const [paidReturn, setPaidReturn] = useState<{ sessionId: string | null; pdfUrl: string | null } | null>(null)
  const [cancelledReturn, setCancelledReturn] = useState(false)
  const [teaserLoading, setTeaserLoading] = useState(false)

  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const chatStreamRef = useRef<HTMLDivElement | null>(null)
  const rootRef = useRef<HTMLDivElement | null>(null)
  const inputRef = useRef<HTMLTextAreaElement | null>(null)

  const canReply = (inputValue.trim().length > 0 || queuedFiles.length > 0) && !isLoading
  const canStart = mode.length > 0 && selectedSector.length > 0 && (mode !== 'report' || contentType.length > 0) && !isLoading
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
    setMessages(prev => [...prev, { role, text: formatted }])
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
    setStage('mode')
    setMode('')
    setSelectedSector('')
    setContentType('')
    setProblem('')
    setSessionId('')
    setPath('unknown')
    setStep(1)
    setMessages([{ role: 'assistant', text: 'Ciao, sono K-BOT. Vuoi analizzare un documento/caso e ottenere un report, oppure vuoi capire se ha senso parlarne con il team K2-AI?' }])
    setInputValue('')
    setIsLoading(false)
    setIsTyping(false)
    setTypingLabel('K-BOT sta scrivendo...')
    setTeaser(null)
    setPdfUrl('')
    setIsGeneratingPdf(false)
    setContactSummary('')
    setQueuedFiles([])
    setIsDragOver(false)
    setIsFullscreen(false)
    setAdaptiveQuestions([])
    setAdaptiveAnswers({})
  }

  async function toggleFullscreen() {
    setIsFullscreen(prev => !prev)
  }

  async function onSelectMode(nextMode: Exclude<KBotMode, ''>) {
    if (stage !== 'mode' || isLoading) return

    setMode(nextMode)
    setPath(nextMode === 'lead' ? 'B' : 'A')
    addMessage('user', nextMode === 'report' ? 'Voglio un report di analisi' : 'Voglio capire se parlarne con voi')
    await botSay(
      nextMode === 'report'
        ? 'Perfetto. Lavoriamo sul report: mi serve solo il settore, poi puoi descrivere il caso o allegare il documento.'
        : 'Perfetto. Qui mi interessa capire bene contesto, problema e urgenza, poi ti mando su contatti con un riepilogo già pulito.',
    )
    setStage('sector')
  }

  async function onSelectSector(slug: string) {
    if (stage !== 'sector' || isLoading) return

    const label = SECTORS.find(s => s.slug === slug)?.label || slug
    setSelectedSector(slug)
    addMessage('user', label)
    if (mode === 'report') {
      await botSay('Perfetto. Ora dimmi: che tipo di materiale o analisi hai bisogno?')
      setStage('content-type')
    } else {
      await botSay('Ora raccontami il processo o il problema: cosa succede oggi, dove si blocca, e cosa vorresti ottenere.')
      setStage('problem')
    }
  }

  async function onSelectContentType(slug: string) {
    if (stage !== 'content-type' || isLoading) return

    const label = CONTENT_TYPES.find(c => c.slug === slug)?.label || slug
    setContentType(slug)
    addMessage('user', label)
    await botSay('Perfetto. Descrivi cosa vuoi analizzare, o allega direttamente il documento: lo uso come materiale del report.')
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
      capture('kbot_started', { sector: selectedSector, mode })

      const initialProblem = problem.trim() || 'Non ho dettagli aggiuntivi al momento.'
      addMessage('user', initialProblem)
      capture('kbot_problem_submitted', { sector: selectedSector, mode, has_problem: problem.trim().length > 0 })
      const data = await postJson('/api/kbot/chat', { session_id: sid, message: initialProblem, step: 1 })
      setIsTyping(false)

      setPath(mode === 'lead' ? 'B' : 'A')
      setStep(data.session?.step || 2)
      setStage('conversation')
      await botSay(data.message || 'Ok, continuiamo da qui.', 120)

      if (data.pdf_url && !pdfUrl) setPdfUrl(data.pdf_url)

      if (mode === 'report' && path === 'A' && !teaser &&
          (data.next_action === 'show_report' || data.next_action === 'show_teaser' || data.pdf_url)) {
        await fetchTeaser()
      }

      if (mode === 'lead' && data.next_action === 'show_contact_form') {
        setContactSummary(data.contact_summary || data.message || '')
      }
    } catch (error) {
      setIsTyping(false)
      addMessage('assistant', friendlyError(error))
    } finally {
      setIsLoading(false)
    }
  }

  async function sendRouterAnswer(answer: string) {
    if (!sessionId || isLoading) return

    const value = answer.trim()
    if (!value) return

    setIsLoading(true)
    if (inputValue.trim()) setInputValue('')
    setTypingLabel('K-BOT sta elaborando la tua risposta…')
    setIsTyping(true)
    addMessage('user', value)

    try {
      const data = await postJson('/api/kbot/chat', {
        session_id: sessionId,
        message: value,
        step: 2,
      })

      const nextPath: PathType = data.path || 'unknown'
      setPath(nextPath)
      setStep(data.session?.step || 3)
      capture('kbot_router_answered', { path: nextPath, sector: selectedSector, answer: value.slice(0, 40) })

      setStage('conversation')
      setIsTyping(false)
      await botSay(data.message || 'Ok, proseguiamo.', 120)
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
      })

      const nextStep = data.session?.step || currentStep + 1
      const nextPath: PathType = data.path || path
      setStep(nextStep)
      setPath(nextPath)
      setIsTyping(false)

      if (data.pdf_url && !pdfUrl) setPdfUrl(data.pdf_url)

      if (mode === 'report' && nextPath === 'A' && !teaser &&
          (data.next_action === 'show_teaser' || data.next_action === 'show_report' || nextStep >= 3 || data.pdf_url)) {
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
      return `${idx + 1}. ${q}\nRisposta: ${value || 'Non specificato'}`
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

  function goToContacts(summary?: string) {
    const text = (summary || contactSummary).trim()
    const settore = SECTOR_TO_CONTACT_SETTORE[selectedSector] || ''
    const sectorLabel = SECTORS.find(s => s.slug === selectedSector)?.label || ''
    try {
      sessionStorage.setItem('kai-contact-prefill', text)
      sessionStorage.setItem('kai-contact-prefill-meta', `Lead da K-BOT — settore: ${sectorLabel}, sessione: ${sessionId}`)
      sessionStorage.setItem('kai-contact-prefill-source', 'k-bot_lead')
    } catch {}
    const params = new URLSearchParams()
    if (settore) params.set('settore', settore)
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
      <div ref={rootRef} className={`kbot-shell ${isFullscreen ? 'fullscreen' : ''}`}>

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
            <div className="kbot-header-sub">Attiva ora</div>
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

        {stage === 'mode' && (
          <div className="kbot-option-panel msg-in">
            <p className="kbot-stage-label">Scegli cosa vuoi fare</p>
            <div className="kbot-mode-grid">
              <button
                type="button"
                className="kbot-mode-card"
                onClick={() => onSelectMode('report')}
                disabled={isLoading}
              >
                <span className="kbot-mode-title">Analisi e report</span>
                <span className="kbot-mode-copy">Carichi o descrivi un caso. K-BOT produce un report di lettura usando le skill interne.</span>
              </button>
              <button
                type="button"
                className="kbot-mode-card"
                onClick={() => onSelectMode('lead')}
                disabled={isLoading}
              >
                <span className="kbot-mode-title">Parlare con K2-AI</span>
                <span className="kbot-mode-copy">K-BOT capisce contesto, urgenza e fit, poi ti manda su contatti con un brief ordinato.</span>
              </button>
            </div>
          </div>
        )}

        {stage === 'sector' && (
          <div className="kbot-option-panel msg-in">
            <p className="kbot-stage-label">Seleziona il tuo settore</p>
            <div className="kbot-sector-grid">
              {SECTORS.map(sector => (
                <button
                  key={sector.slug}
                  type="button"
                  className={`kbot-sector-card ${selectedSector === sector.slug ? 'active' : ''} ${selectedSector && selectedSector !== sector.slug ? 'disabled' : ''}`}
                  onClick={() => onSelectSector(sector.slug)}
                  disabled={Boolean(selectedSector && selectedSector !== sector.slug) || isLoading}
                >
                  {sector.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {stage === 'content-type' && (
          <div className="kbot-option-panel msg-in">
            <p className="kbot-stage-label">Che tipo di materiale hai?</p>
            <div className="kbot-sector-grid">
              {CONTENT_TYPES.map(ct => (
                <button
                  key={ct.slug}
                  type="button"
                  className={`kbot-sector-card ${contentType === ct.slug ? 'active' : ''} ${contentType && contentType !== ct.slug ? 'disabled' : ''}`}
                  onClick={() => onSelectContentType(ct.slug)}
                  disabled={Boolean(contentType && contentType !== ct.slug) || isLoading}
                  title={ct.desc}
                >
                  {ct.label}
                </button>
              ))}
            </div>
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
                Avanti →
              </button>
            </div>
          </div>
        )}

        {hasAdaptiveForm && !contactSummary && !teaser && (
          <div className="kbot-option-panel msg-in">
            <p className="kbot-stage-label">Compila le risposte rapide</p>
            <div className="kbot-adaptive-form">
              {adaptiveQuestions.map(question => (
                <label key={question} className="kbot-adaptive-field">
                  <span>{question}</span>
                  {detectAdaptiveKind(question) === 'long' ? (
                    <textarea
                      value={adaptiveAnswers[question] || ''}
                      onChange={e => setAdaptiveAnswers(prev => ({ ...prev, [question]: e.target.value }))}
                      placeholder="Scrivi qui la risposta…"
                    />
                  ) : detectAdaptiveKind(question) === 'budget' ? (
                    <select
                      value={adaptiveAnswers[question] || ''}
                      onChange={e => setAdaptiveAnswers(prev => ({ ...prev, [question]: e.target.value }))}
                    >
                      <option value="">Seleziona range budget…</option>
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
                      placeholder="Scrivi qui la risposta…"
                    />
                  )}
                </label>
              ))}
              <label className="kbot-adaptive-field">
                <span>{ADAPTIVE_OTHER_LABEL}</span>
                <textarea
                  value={adaptiveAnswers[ADAPTIVE_OTHER_LABEL] || ''}
                  onChange={e => setAdaptiveAnswers(prev => ({ ...prev, [ADAPTIVE_OTHER_LABEL]: e.target.value }))}
                  placeholder="Indicazioni extra utili per adattare meglio la risposta…"
                />
              </label>
              <button type="button" className="kbot-choice-chip" onClick={submitAdaptiveForm} disabled={!canSendAdaptive}>
                Invia risposte
              </button>
            </div>
          </div>
        )}

        {stage === 'router' && (
          <div className="kbot-option-panel msg-in">
            <div className="kbot-choice-row">
              <button type="button" className="kbot-choice-chip" onClick={() => sendRouterAnswer('Caso specifico')} disabled={isLoading}>Caso specifico</button>
              <button type="button" className="kbot-choice-chip" onClick={() => sendRouterAnswer('Progetto più ampio')} disabled={isLoading}>Progetto più ampio</button>
              <button
                type="button"
                className="kbot-choice-chip"
                onClick={() => {
                  setInputValue('Altro: ')
                  inputRef.current?.focus()
                }}
                disabled={isLoading}
              >
                Altro
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

      {(stage === 'router' || stage === 'conversation') && !hasAdaptiveForm && !contactSummary && !teaser && (
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
                if (stage === 'router' && inputValue.trim()) sendRouterAnswer(inputValue)
                else if (stage === 'conversation' && canReply) sendConversationMessage()
              }
            }}
            placeholder={
              stage === 'router'
                ? 'Oppure rispondi a parole tue…'
                : 'Scrivi qui la tua risposta…'
            }
          />

          <div className="kbot-input-actions">
            <button type="button" className="kbot-attach-btn" onClick={() => fileInputRef.current?.click()}>Allega file</button>

            {stage === 'router' ? (
              <button type="button" onClick={() => sendRouterAnswer(inputValue)} disabled={!inputValue.trim() || isLoading}>Invia</button>
            ) : (
              <button type="button" onClick={sendConversationMessage} disabled={!canReply}>Invia</button>
            )}
          </div>
          <div className="kbot-drop-hint">Trascina qui PDF, bilanci o documenti da analizzare (max 5 file)</div>
        </div>
      )}

      {contactSummary && contactSummary !== '__pending__' && (
        <div className="kbot-contact-cta">
          <p className="kbot-contact-cta-hint">Ho preparato un riepilogo del tuo caso per il team K2-AI.</p>
          <button type="button" className="kbot-btn-primary kbot-contact-btn" onClick={() => goToContacts()}>
            Contattaci →
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
