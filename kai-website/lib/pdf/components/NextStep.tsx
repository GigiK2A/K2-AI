import React from 'react'
import { Page, View, Text } from '@react-pdf/renderer'
import { COLORS, styles } from '../styles'

export function NextStep({ testo }: { testo: string }) {
  return (
    <Page size="A4" style={{ ...styles.page, backgroundColor: COLORS.primary }}>
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <Text style={{ color: '#A5B4FC', fontSize: 11, marginBottom: 8 }}>Prossimo passo</Text>
        <Text style={{ color: COLORS.white, fontSize: 18, fontWeight: 700, textAlign: 'center', marginBottom: 16 }}>{testo}</Text>
      </View>
    </Page>
  )
}
