import React from 'react'
import { View, Text } from '@react-pdf/renderer'
import { styles } from '../styles'

interface TableProps {
  colonne: string[]
  righe: Array<Array<string | number>>
}

export function TableComponent({ colonne, righe }: TableProps) {
  return (
    <View style={styles.table}>
      <View style={styles.tableHeader}>
        {colonne.map((col, idx) => (
          <Text key={`${col}-${idx}`} style={styles.tableHeaderCell}>{col}</Text>
        ))}
      </View>
      {righe.map((row, ridx) => (
        <View key={`row-${ridx}`} style={[styles.tableRow, ridx % 2 === 1 ? styles.tableRowAlt : null]}>
          {row.map((cell, cidx) => (
            <Text key={`cell-${ridx}-${cidx}`} style={styles.tableCell}>{String(cell)}</Text>
          ))}
        </View>
      ))}
    </View>
  )
}
