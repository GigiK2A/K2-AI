import React from 'react'
import { Page, Text } from '@react-pdf/renderer'
import { styles } from '../styles'

export function ExecutiveSummary({ summary }: { summary: string }) {
  return (
    <Page size="A4" style={styles.page}>
      <Text style={styles.sectionTitle}>Sintesi esecutiva</Text>
      <Text style={styles.bodyText}>{summary}</Text>
    </Page>
  )
}
