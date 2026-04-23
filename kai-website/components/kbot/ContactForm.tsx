import React from 'react'

interface ContactFormProps {
  email: string
  disponibilita: string
  loading: boolean
  onEmailChange: (value: string) => void
  onDisponibilitaChange: (value: string) => void
  onSubmit: () => void
  onCrossoverToA?: () => void
}

export function ContactForm({
  email,
  disponibilita,
  loading,
  onEmailChange,
  onDisponibilitaChange,
  onSubmit,
  onCrossoverToA,
}: ContactFormProps) {
  const canSubmit = !loading

  return (
    <div className="kbot-contact-form">
      <h4>Concludiamo con i dati per la call (opzionali)</h4>
      <label>Email (opzionale)</label>
      <input
        type="email"
        value={email}
        onChange={e => onEmailChange(e.target.value)}
        placeholder="nome@azienda.it"
      />
      <label>Disponibilità call (opzionale)</label>
      <input
        type="text"
        value={disponibilita}
        onChange={e => onDisponibilitaChange(e.target.value)}
        placeholder="Es. martedì 10:00-12:00"
      />

      <button type="button" className="kbot-next-btn" onClick={onSubmit} disabled={!canSubmit}>
        {loading ? 'Invio in corso...' : 'Invia richiesta →'}
      </button>

      <div className="kbot-crossover-box">
        <span>Mentre aspetti una risposta, puoi vedere il check rapido gratuito del caso.</span>
        <button type="button" className="kbot-link-btn" onClick={onCrossoverToA}>Vai al check rapido →</button>
      </div>
    </div>
  )
}
