import React from 'react'
import type { PriorityLevel } from '../../src/types/report'

interface Props {
  level: string
  variant: PriorityLevel
}

export function ReportPriorityBadge({ level, variant }: Props) {
  return (
    <span className={`priority ${variant}`}>
      {level || 'Dato non fornito'}
    </span>
  )
}
