import React from 'react'
import type { ReportData } from '../../src/types/report'

interface Props {
  reportData: ReportData
}

export function ReportFooter({ reportData }: Props) {
  return (
    <footer className="report-footer">
      <span>K2AI</span>
      <span>{reportData.meta.code || 'Dato non fornito'}</span>
      <span>{reportData.meta.version || 'Dato non fornito'}</span>
    </footer>
  )
}
