import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ChatBubble } from './ChatBubble'
import { TeaserCard } from './TeaserCard'
import { ContactForm } from './ContactForm'
import { PaymentBox } from './PaymentBox'

type PathType = 'A' | 'B' | 'unknown'
type Stage = 'sector' | 'problem' | 'router' | 'conversation'
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
      collected.push(...parts)
      continue
    }

    if (/^(\d+[.)]|[-*])\s+/.test(rawLine) && normalized.length > 14) {
      collected.push(normalized)
    }
  }

  return Array.from(new Set(collected)).slice(0, 5)
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

export function KBot() {
  const [stage, setStage] = useState<Stage>('sector')
  const [selectedSector, setSelectedSector] = useState('')
  const [problem, setProblem] = useState('')
  const [sessionId, setSessionId] = useState('')
  const [path, setPath] = useState<PathType>('unknown')
  const [step, setStep] = useState(1)
  const [messages, setMessages] = useState<ChatMsg[]>([
    { role: 'assistant', text: 'Ciao! Sono K-BOT. Prima di tutto: in quale settore operi?' },
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [typingLabel, setTypingLabel] = useState('K-BOT sta scrivendo...')
  const [teaser, setTeaser] = useState<any>(null)
  const [pdfUrl, setPdfUrl] = useState('')
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false)
  const [showContactForm, setShowContactForm] = useState(false)
  const [email, setEmail] = useState('')
  const [disponibilita, setDisponibilita] = useState('')
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
  const canStart = selectedSector.length > 0 && !isLoading
  const teaserSignals = useMemo(() => teaser?.segnali || [], [teaser])
  const hasAdaptiveForm = adaptiveQuestions.length > 1
  const canSendAdaptive = hasAdaptiveForm && !isLoading

  useEffect(() => {
    if (chatStreamRef.current) {
      chatStreamRef.current.scrollTop = chatStreamRef.current.scrollHeight
    }
  }, [messages, isTyping, stage, teaser, showContactForm])

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
    setStage('sector')
    setSelectedSector('')
    setProblem('')
    setSessionId('')
    setPath('unknown')
    setStep(1)
    setMessages([{ role: 'assistant', text: 'Ciao! Sono K-BOT. Prima di tutto: in quale settore operi?' }])
    setInputValue('')
    setIsLoading(false)
    setIsTyping(false)
    setTypingLabel('K-BOT sta scrivendo...')
    setTeaser(null)
    setPdfUrl('')
    setIsGeneratingPdf(false)
    setShowContactForm(false)
    setEmail('')
    setDisponibilita('')
    setQueuedFiles([])
    setIsDragOver(false)
    setIsFullscreen(false)
    setAdaptiveQuestions([])
    setAdaptiveAnswers({})
  }

  async function toggleFullscreen() {
    setIsFullscreen(prev => !prev)
  }

  async function onSelectSector(slug: string) {
    if (stage !== 'sector' || isLoading) return

    const label = SECTORS.find(s => s.slug === slug)?.label || slug
    setSelectedSector(slug)
    addMessage('user', label)
    await botSay('Perfetto. Ora descrivi in parole tue cosa ti serve: processo, collo di bottiglia, strumenti in uso.')
    setStage('problem')
  }

  async function startFromProblem() {
    if (!canStart) return

    setIsLoading(true)
    setTypingLabel('K-BOT sta elaborando la tua richiesta…')
    setIsTyping(true)
    try {
      const session = await postJson('/api/kbot/session', { sector: selectedSector })
      const sid = session.session_id
      setSessionId(sid)
      capture('kbot_started', { sector: selectedSector })

      const initialProblem = problem.trim() || 'Non ho dettagli aggiuntivi al momento.'
      addMessage('user', initialProblem)
      capture('kbot_problem_submitted', { sector: selectedSector, has_problem: problem.trim().length > 0 })
      await postJson('/api/kbot/chat', { session_id: sid, message: initialProblem, step: 1 })
      setIsTyping(false)

      await botSay(ROUTER_TEXT, 120)
      setStep(2)
      setStage('router')
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

      if (nextPath === 'A' && !teaser && data.next_action === 'show_teaser') {
        await botAnalyzeThenSay(data.message || 'Analisi completata.')
        setTeaserLoading(true)
        try {
          const teaserResp = await postJson('/api/kbot/teaser', { session_id: sessionId })
          setTeaser(teaserResp.teaser)
          capture('kbot_teaser_viewed', { sector: selectedSector })
        } finally {
          setTeaserLoading(false)
        }
      } else {
        await botSay(data.message || '')
      }

      if (nextPath === 'B' && data.next_action === 'show_contact_form') {
        setShowContactForm(true)
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

  async function submitContact() {
    if (!sessionId) return
    setIsLoading(true)

    try {
      await postJson('/api/kbot/contact', {
        session_id: sessionId,
        email,
        disponibilita,
      })

      capture('kbot_contact_submitted', { sector: selectedSector })

      const summary = encodeURIComponent(messages.slice(-6).map(m => `${m.role}: ${m.text}`).join(' | '))
      const q = new URLSearchParams({
        email: email || '',
        settore: selectedSector,
        disponibilita: disponibilita || '',
        kbot_session_id: sessionId,
        messaggio: summary,
      })

      window.location.href = `/contatti.html?${q.toString()}`
    } catch (error) {
      addMessage('assistant', friendlyError(error))
    } finally {
      setIsLoading(false)
    }
  }

  async function generatePdfTest() {
    if (!sessionId || isGeneratingPdf || isLoading) return
    setIsGeneratingPdf(true)
    try {
      const resp = await postJson('/api/kbot/generate-pdf', { session_id: sessionId, test_mode: true })
      if (resp?.pdf_url) {
        setPdfUrl(resp.pdf_url)
        await botSay('PDF generato. Puoi aprirlo dal link qui sotto.', 120)
      } else {
        addMessage('assistant', 'Non sono riuscito a generare il PDF in questo tentativo. Riprova tra poco.')
      }
    } catch (error) {
      addMessage('assistant', friendlyError(error))
    } finally {
      setIsGeneratingPdf(false)
    }
  }

  function crossoverToB() {
    setPath('B')
    setShowContactForm(true)
    capture('kbot_crossover_clicked', { from: 'A', to: 'B' })
  }

  function crossoverToA() {
    setPath('A')
    setShowContactForm(false)
    capture('kbot_crossover_clicked', { from: 'B', to: 'A' })
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
          <button type="button" className="kbot-top-btn" onClick={() => fileInputRef.current?.click()}>
            ALLEGA
          </button>
          <button type="button" className="kbot-top-btn" onClick={toggleFullscreen}>
            {isFullscreen ? 'RIDUCI' : 'FULLSCREEN'}
          </button>
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

      {stage !== 'sector' && !teaser && !showContactForm && (
        <div className="kbot-progress">
          {(['problem', 'router', 'conversation'] as const).map((s, i) => {
            const labels = ['Descrivi il caso', 'Tipo di analisi', path === 'B' ? 'Qualifica' : 'Approfondimento']
            const active = s === stage || (s === 'conversation' && stage === 'router' && step > 2)
            const done = (s === 'problem' && ['router', 'conversation'].includes(stage)) ||
                         (s === 'router' && stage === 'conversation')
            return (
              <div key={s} className={`kbot-progress-step ${done ? 'done' : ''} ${active && !done ? 'active' : ''}`}>
                <span className="kbot-progress-dot">{done ? '✓' : i + 1}</span>
                <span className="kbot-progress-label">{labels[i]}</span>
              </div>
            )
          })}
          <div className={`kbot-progress-step ${teaserLoading || teaser ? 'active' : ''}`}>
            <span className="kbot-progress-dot">4</span>
            <span className="kbot-progress-label">{path === 'B' ? 'Contatto' : 'Analisi'}</span>
          </div>
        </div>
      )}

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

        {stage === 'problem' && (
          <div className="kbot-option-panel msg-in">
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

        {hasAdaptiveForm && !showContactForm && !teaser && (
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
            <button type="button" className="kbot-link-btn" onClick={crossoverToB}>Preferisci un approccio su misura? →</button>
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

      {(stage === 'router' || stage === 'conversation') && !hasAdaptiveForm && !showContactForm && !teaser && (
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

      {path === 'B' && showContactForm && (
        <ContactForm
          email={email}
          disponibilita={disponibilita}
          loading={isLoading}
          onEmailChange={setEmail}
          onDisponibilitaChange={setDisponibilita}
          onSubmit={submitContact}
          onCrossoverToA={crossoverToA}
        />
      )}
      </div>
    </>
  )
}
