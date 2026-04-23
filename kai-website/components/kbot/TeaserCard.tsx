import React from 'react'

export function TeaserCard({ signal }: { signal: any }) {
  return (
    <div className="kbot-teaser-card">
      <div className={`kbot-priority ${signal.priorita || 'da_monitorare'}`}>{signal.priorita || 'da_monitorare'}</div>
      <h4>{signal.titolo}</h4>
      <p>{signal.sintesi}</p>
      <div className="kbot-teaser-blur">{signal.anteprima_analisi}</div>
    </div>
  )
}
