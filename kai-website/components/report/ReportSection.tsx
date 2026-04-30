import React from 'react'

interface Props {
  title: string
  eyebrow?: string
  children: React.ReactNode
  className?: string
}

export function ReportSection({ title, eyebrow, children, className = '' }: Props) {
  return (
    <section className={`report-section ${className}`.trim()}>
      <div className="section-heading">
        {eyebrow && <p className="section-eyebrow">{eyebrow}</p>}
        <h2>{title || 'Dato non fornito'}</h2>
      </div>
      {children}
    </section>
  )
}
