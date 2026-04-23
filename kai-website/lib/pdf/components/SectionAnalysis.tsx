import React from 'react'
import { Page, View, Text } from '@react-pdf/renderer'
import { styles } from '../styles'

export function SectionAnalysis({ section, children }: { section: any; children?: React.ReactNode }) {
  return (
    <Page size="A4" style={styles.page}>
      <Text style={styles.sectionTitle}>{section.titolo}</Text>
      <Text style={styles.bodyText}>{section.contenuto}</Text>
      <View style={{ marginTop: 12 }}>{children}</View>
    </Page>
  )
}
