import React from 'react'
import { View, Svg, Rect, Line, Text as SvgText } from '@react-pdf/renderer'
import { COLORS } from '../styles'

interface Node { id: string; label: string }
interface Edge { da: string; a: string }

export function FlowSchema({
  nodi,
  archi,
  width = 440,
  height = 140,
}: {
  nodi: Node[]
  archi: Edge[]
  width?: number
  height?: number
}) {
  const nodeWidth = 90
  const nodeHeight = 30
  const gap = Math.max(12, Math.floor((width - nodi.length * nodeWidth) / Math.max(nodi.length + 1, 1)))
  const y = 46

  const positions = nodi.map((n, i) => ({ ...n, x: gap + i * (nodeWidth + gap), y }))

  return (
    <View style={{ marginVertical: 10 }}>
      <Svg width={width} height={height}>
        {archi.map((a, i) => {
          const from = positions.find(p => p.id === a.da)
          const to = positions.find(p => p.id === a.a)
          if (!from || !to) return null
          return (
            <Line
              key={`edge-${i}`}
              x1={from.x + nodeWidth}
              y1={from.y + nodeHeight / 2}
              x2={to.x}
              y2={to.y + nodeHeight / 2}
              stroke={COLORS.gray600}
              strokeWidth={1}
            />
          )
        })}
        {positions.map((n, i) => (
          <React.Fragment key={`node-${i}`}>
            <Rect x={n.x} y={n.y} width={nodeWidth} height={nodeHeight} rx={4} fill={COLORS.gray100} stroke={COLORS.gray300} />
            <SvgText x={n.x + nodeWidth / 2} y={n.y + 19} textAnchor="middle" fontSize={8} fill={COLORS.primary}>
              {n.label}
            </SvgText>
          </React.Fragment>
        ))}
      </Svg>
    </View>
  )
}
