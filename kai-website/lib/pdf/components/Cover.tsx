import React from 'react'
import { Page, View, Text } from '@react-pdf/renderer'
import { styles } from '../styles'

export function Cover({ analysisJson }: { analysisJson: any }) {
  return (
    <Page size="A4" style={styles.coverPage}>
      <View>
        <Text style={styles.coverBadge}>Diagnosi AI Operativa</Text>
        <Text style={styles.coverTitle}>Analisi specializzata{`\n`}{analysisJson.meta.settore}</Text>
        <Text style={styles.coverSubtitle}>Generata da K2-AI - Skill specializzate per il tuo settore</Text>
      </View>
      <View>
        <Text style={styles.coverMeta}>
          Data: {new Date(analysisJson.meta.data_generazione).toLocaleDateString('it-IT')}
          {`\n`}Skill attive: {(analysisJson.meta.skill_attive || []).join(' · ')}
          {`\n`}k2-ai.it
        </Text>
      </View>
    </Page>
  )
}
