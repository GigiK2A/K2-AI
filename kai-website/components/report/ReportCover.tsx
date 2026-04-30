import React from 'react'
import type { ReportData } from '../../src/types/report'

interface Props {
  reportData: ReportData
}

export function ReportCover({ reportData }: Props) {
  return (
    <section className="report-cover">
      <div className="cover-topline">
        <span>{reportData.meta.category || 'Dato non fornito'}</span>
        <span>{reportData.meta.date || 'Dato non fornito'}</span>
      </div>
      <div className="cover-main">
        <p className="cover-client">{reportData.client.name || 'Dato non fornito'}</p>
        <h1>{reportData.meta.title || 'Dato non fornito'}</h1>
        <p className="cover-subtitle">{reportData.meta.subtitle || 'Dato non fornito'}</p>
      </div>
      <div className="cover-bottom">
        <div>
          <span>Perimetro</span>
          <strong>{reportData.client.scope || 'Dato non fornito'}</strong>
        </div>
        <div>
          <span>Codice report</span>
          <strong>{reportData.meta.code || 'Dato non fornito'}</strong>
        </div>
      </div>
    </section>
  )
}
