import React from 'react'

interface Props {
  items: string[]
}

export function ReportChecklist({ items }: Props) {
  if (items.length === 0) {
    return <p className="empty-state">Dato non fornito</p>
  }

  return (
    <ul className="report-checklist">
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>{item || 'Dato non fornito'}</li>
      ))}
    </ul>
  )
}
