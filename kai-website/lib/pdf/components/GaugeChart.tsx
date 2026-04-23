import React from 'react'
import { Svg, Path, Text as SvgText } from '@react-pdf/renderer'
import { COLORS } from '../styles'

interface GaugeProps {
  valore: number
  label: string
  soglie: { verde: number; giallo: number }
}

export function GaugeChart({ valore, label, soglie }: GaugeProps) {
  const v = Math.max(0, Math.min(100, valore || 0))
  const r = 50
  const cx = 70
  const cy = 70

  const color = v >= soglie.verde ? COLORS.green : v >= soglie.giallo ? COLORS.orange : COLORS.red

  const bgPath = `M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`
  const valAngle = (v / 100) * 180
  const valRad = ((valAngle - 90) * Math.PI) / 180
  const valX = cx + r * Math.cos(valRad)
  const valY = cy + r * Math.sin(valRad)
  const largeArc = v > 50 ? 1 : 0
  const valPath = `M ${cx - r} ${cy} A ${r} ${r} 0 ${largeArc} 1 ${valX} ${valY}`

  return (
    <Svg width={140} height={90}>
      <Path d={bgPath} stroke={COLORS.gray300} strokeWidth={10} fill="none" />
      <Path d={valPath} stroke={color} strokeWidth={10} fill="none" strokeLinecap="round" />
      <SvgText x={cx} y={cy - 8} textAnchor="middle" fontSize={22} fontWeight="700" fill={color}>
        {v}
      </SvgText>
      <SvgText x={cx} y={cy + 8} textAnchor="middle" fontSize={8} fill={COLORS.gray600}>
        {label}
      </SvgText>
    </Svg>
  )
}
