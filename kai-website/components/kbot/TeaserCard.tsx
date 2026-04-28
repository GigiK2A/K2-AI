import React from 'react'

export function TeaserCard({ signal }: { signal: any }) {
  return (
    <div className="kbot-teaser-card">
      <div className={`kbot-priority ${signal.priorita || 'media'}`}>{(signal.priorita || 'media').toUpperCase()}</div>
      <h4>{signal.titolo}</h4>
      <p>{signal.sintesi}</p>
      {signal.causa_strutturale && (
        <p className="kbot-teaser-causa"><strong>Causa:</strong> {signal.causa_strutturale}</p>
      )}
      <div className="kbot-teaser-blur">{signal.anteprima_analisi}</div>
    </div>
  )
}
