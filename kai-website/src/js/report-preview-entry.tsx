import React from 'react'
import { createRoot } from 'react-dom/client'
import { K2AIReportTemplate } from '../../components/report/K2AIReportTemplate'
import { mockReportData } from '../data/mockReportData'

const rootEl = document.getElementById('report-preview-root')

if (rootEl) {
  createRoot(rootEl).render(
    <React.StrictMode>
      <K2AIReportTemplate reportData={mockReportData} />
    </React.StrictMode>
  )
}
