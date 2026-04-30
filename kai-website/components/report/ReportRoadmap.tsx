import React from 'react'
import type { RoadmapItem } from '../../src/types/report'

interface Props {
  items: RoadmapItem[]
}

export function ReportRoadmap({ items }: Props) {
  if (items.length === 0) {
    return <p className="empty-state">Dato non fornito</p>
  }

  return (
    <div className="roadmap-list">
      {items.map((item, index) => (
        <article className="roadmap-item" key={`${item.phaseTitle}-${index}`}>
          <div className="roadmap-index">{String(index + 1).padStart(2, '0')}</div>
          <div className="roadmap-content">
            <div className="roadmap-meta">
              <span>{item.timeframe || 'Dato non fornito'}</span>
              <span>{item.owner || 'Dato non fornito'}</span>
            </div>
            <h3>{item.phaseTitle || 'Dato non fornito'}</h3>
            <p>{item.phaseDescription || 'Dato non fornito'}</p>
          </div>
        </article>
      ))}
    </div>
  )
}
