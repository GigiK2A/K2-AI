import React from 'react'
import type { Metric } from '../../src/types/report'

interface Props {
  metric: Metric
}

export function ReportMetricCard({ metric }: Props) {
  return (
    <div className="card metric">
      <div className="metric-value">{metric.value || 'Dato non fornito'}</div>
      <div className="metric-label">{metric.label || ''}</div>
    </div>
  )
}
