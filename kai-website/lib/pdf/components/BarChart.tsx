import React from 'react'
import { View, Svg, Rect, Text as SvgText, G } from '@react-pdf/renderer'
import { COLORS } from '../styles'

interface BarChartProps {
  labels: string[]
  valori: number[]
  unita: string
  width?: number
  height?: number
}

export function BarChart({ labels, valori, unita, width = 440, height = 160 }: BarChartProps) {
  const safeLabels = labels || []
  const safeValori = valori || []
  const maxVal = Math.max(...safeValori, 1)
  const bars = Math.max(safeLabels.length, 1)
  const barWidth = (width - 60) / bars - 8
  const chartHeight = height - 30

  return (
    <View style={{ marginVertical: 10 }}>
      <Svg width={width} height={height}>
        {safeValori.map((val, i) => {
          const barH = (val / maxVal) * chartHeight
          const x = 48 + i * (barWidth + 8)
          const y = chartHeight - barH + 4
          return (
            <G key={i}>
              <Rect x={x} y={y} width={barWidth} height={barH} fill={COLORS.accent} rx={3} />
              <SvgText x={x + barWidth / 2} y={y - 4} textAnchor="middle" fontSize={8} fill={COLORS.primary} fontWeight="600">
                {val}{unita}
              </SvgText>
              <SvgText x={x + barWidth / 2} y={height - 8} textAnchor="middle" fontSize={7.5} fill={COLORS.gray600}>
                {safeLabels[i]}
              </SvgText>
            </G>
          )
        })}
        <Rect x={44} y={4} width={1} height={chartHeight} fill={COLORS.gray300} />
      </Svg>
    </View>
  )
}
