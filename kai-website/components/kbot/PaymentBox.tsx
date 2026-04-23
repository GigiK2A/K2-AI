import React, { useState } from 'react'

interface PaymentBoxProps {
  sessionId: string
  isGeneratingPdf: boolean
  pdfUrl: string
  onTestGenerate: () => void
}

type CheckoutState = 'idle' | 'loading' | 'error'

export function PaymentBox({ sessionId, isGeneratingPdf, pdfUrl, onTestGenerate }: PaymentBoxProps) {
  const [checkoutState, setCheckoutState] = useState<CheckoutState>('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const [email, setEmail] = useState('')

  if (pdfUrl) {
    return (
      <div className="kbot-payment-box kbot-payment-done">
        <p className="kbot-payment-ready">Report pronto.</p>
        <a href={pdfUrl} target="_blank" rel="noreferrer" className="kbot-btn-primary">
          Apri il PDF →
        </a>
      </div>
    )
  }

  async function startCheckout() {
    if (checkoutState === 'loading') return
    setCheckoutState('loading')
    setErrorMsg('')

    try {
      sessionStorage.setItem('kbot_pending_session', sessionId)

      const resp = await fetch('/api/kbot/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, email: email.trim() || undefined }),
      })

      const data = await resp.json().catch(() => ({}))

      if (!resp.ok) {
        throw new Error(data?.error || `Errore ${resp.status}`)
      }

      if (!data.checkout_url) throw new Error('URL checkout non ricevuto')

      try {
        window.posthog?.capture?.('kbot_payment_clicked', { session_id: sessionId })
      } catch {}

      window.location.href = data.checkout_url
    } catch (err) {
      sessionStorage.removeItem('kbot_pending_session')
      setCheckoutState('error')
      setErrorMsg(err instanceof Error ? err.message : 'Errore avvio pagamento')
    }
  }

  return (
    <div className="kbot-payment-box">
      <p className="kbot-payment-label">Piano d'azione operativo</p>
      <p className="kbot-payment-desc">
        7 pagine con priorità, tempi e template pronti — consegna in 10 minuti via email.
      </p>
      <p className="kbot-payment-price">19€</p>

      <input
        type="email"
        className="kbot-payment-email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        placeholder="La tua email (dove ti mandiamo il PDF)"
        autoComplete="email"
      />

      <button
        type="button"
        className="kbot-btn-primary"
        onClick={startCheckout}
        disabled={checkoutState === 'loading'}
      >
        {checkoutState === 'loading' ? 'Apertura pagamento…' : 'Ottieni il report completo →'}
      </button>

      {checkoutState === 'error' && (
        <p className="kbot-payment-error">
          {errorMsg} —{' '}
          <button
            type="button"
            className="kbot-link-btn"
            onClick={() => { setCheckoutState('idle'); setErrorMsg('') }}
          >
            riprova
          </button>
        </p>
      )}

      <p className="kbot-payment-fallback">
        Oppure{' '}
        <button
          type="button"
          className="kbot-link-btn"
          onClick={onTestGenerate}
          disabled={isGeneratingPdf}
        >
          {isGeneratingPdf ? 'generazione in corso…' : 'genera PDF in modalità demo'}
        </button>
      </p>
    </div>
  )
}
