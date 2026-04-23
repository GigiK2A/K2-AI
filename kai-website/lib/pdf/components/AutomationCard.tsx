import React from 'react'
import { View, Text } from '@react-pdf/renderer'
import { COLORS, styles } from '../styles'

export function AutomationCard({ data }: { data: any }) {
  const complexityColor = data.complessita === 'bassa' ? COLORS.green : data.complessita === 'media' ? COLORS.orange : COLORS.red

  return (
    <View style={styles.automationCard}>
      <Text style={{ ...styles.badge, backgroundColor: '#EEF2FF', color: COLORS.accent }}>{data.orizzonte}</Text>
      <Text style={styles.automationCardTitle}>{data.area}</Text>
      <Text style={{ ...styles.bodyText, marginBottom: 6 }}>{data.descrizione}</Text>
      <Text style={{ ...styles.bodyText, fontSize: 9, color: COLORS.gray600 }}>Impatto stimato: {data.impatto_stimato}</Text>
      <Text style={{ ...styles.bodyText, fontSize: 9, color: complexityColor }}>Complessita: {data.complessita}</Text>
    </View>
  )
}
