const React = require('react')
const {
  renderToBuffer,
  Document,
  Page,
  View,
  Text,
  Svg,
  Rect,
  Line,
  Path,
  Text: SvgText,
  G,
  StyleSheet,
} = require('@react-pdf/renderer')

const COLORS = {
  primary: '#1A1F36',
  accent: '#3B5BDB',
  green: '#2F9E44',
  orange: '#E67700',
  red: '#C92A2A',
  gray100: '#F8F9FA',
  gray300: '#DEE2E6',
  gray600: '#868E96',
  white: '#FFFFFF',
}

const styles = StyleSheet.create({
  page: {
    fontFamily: 'Helvetica',
    fontSize: 10,
    color: '#212529',
    paddingTop: 48,
    paddingBottom: 56,
    paddingHorizontal: 48,
    backgroundColor: COLORS.white,
  },
  coverPage: {
    backgroundColor: COLORS.primary,
    padding: 56,
    justifyContent: 'space-between',
  },
  coverBadge: {
    backgroundColor: COLORS.accent,
    color: COLORS.white,
    fontSize: 9,
    fontWeight: 600,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 4,
    alignSelf: 'flex-start',
    textTransform: 'uppercase',
  },
  coverTitle: {
    color: COLORS.white,
    fontSize: 28,
    fontWeight: 700,
    marginTop: 24,
    lineHeight: 1.3,
  },
  coverSubtitle: {
    color: '#A5B4FC',
    fontSize: 13,
    marginTop: 12,
  },
  coverMeta: {
    color: COLORS.gray600,
    fontSize: 9,
    marginTop: 48,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 700,
    color: COLORS.primary,
    marginBottom: 12,
    paddingBottom: 6,
    borderBottomWidth: 2,
    borderBottomColor: COLORS.accent,
  },
  subsectionTitle: {
    fontSize: 11,
    fontWeight: 600,
    color: COLORS.primary,
    marginTop: 14,
    marginBottom: 6,
  },
  bodyText: {
    fontSize: 10,
    lineHeight: 1.6,
    color: '#343A40',
  },
  table: { width: '100%', marginVertical: 10 },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: COLORS.primary,
    paddingVertical: 6,
    paddingHorizontal: 8,
  },
  tableHeaderCell: {
    color: COLORS.white,
    fontSize: 9,
    fontWeight: 600,
    flex: 1,
  },
  tableRow: {
    flexDirection: 'row',
    paddingVertical: 5,
    paddingHorizontal: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray300,
  },
  tableCell: {
    fontSize: 9,
    color: '#343A40',
    flex: 1,
  },
  automationCard: {
    borderWidth: 1,
    borderColor: COLORS.gray300,
    borderRadius: 6,
    padding: 12,
    marginBottom: 8,
  },
  pageFooter: {
    position: 'absolute',
    bottom: 24,
    left: 48,
    right: 48,
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTopWidth: 1,
    borderTopColor: COLORS.gray300,
    paddingTop: 8,
  },
  pageFooterText: {
    fontSize: 8,
    color: COLORS.gray600,
  },
})

const h = React.createElement

function PageFooter({ settore }) {
  return h(
    View,
    { style: styles.pageFooter, fixed: true },
    h(Text, { style: styles.pageFooterText }, `K2-AI - Diagnosi AI Operativa · ${settore}`),
    h(Text, {
      style: styles.pageFooterText,
      render: ({ pageNumber, totalPages }) => `${pageNumber} / ${totalPages}`,
    }),
  )
}

function TableComponent({ colonne = [], righe = [] }) {
  return h(
    View,
    { style: styles.table },
    h(
      View,
      { style: styles.tableHeader },
      ...colonne.map((c, i) => h(Text, { key: `h-${i}`, style: styles.tableHeaderCell }, String(c))),
    ),
    ...righe.map((row, rIdx) =>
      h(
        View,
        { key: `r-${rIdx}`, style: [styles.tableRow, rIdx % 2 ? { backgroundColor: COLORS.gray100 } : null] },
        ...(Array.isArray(row) ? row : []).map((cell, cIdx) =>
          h(Text, { key: `c-${rIdx}-${cIdx}`, style: styles.tableCell }, String(cell)),
        ),
      ),
    ),
  )
}

function BarChart({ labels = [], valori = [], unita = '', width = 440, height = 160 }) {
  const maxVal = Math.max(...valori, 1)
  const bars = Math.max(labels.length, 1)
  const barWidth = (width - 60) / bars - 8
  const chartHeight = height - 30

  return h(
    View,
    { style: { marginVertical: 10 } },
    h(
      Svg,
      { width, height },
      ...valori.map((val, i) => {
        const barH = (val / maxVal) * chartHeight
        const x = 48 + i * (barWidth + 8)
        const y = chartHeight - barH + 4
        return h(
          G,
          { key: i },
          h(Rect, { x, y, width: barWidth, height: barH, fill: COLORS.accent, rx: 3 }),
          h(SvgText, { x: x + barWidth / 2, y: y - 4, textAnchor: 'middle', fontSize: 8, fill: COLORS.primary }, `${val}${unita}`),
          h(SvgText, { x: x + barWidth / 2, y: height - 8, textAnchor: 'middle', fontSize: 7.5, fill: COLORS.gray600 }, labels[i] || ''),
        )
      }),
      h(Rect, { x: 44, y: 4, width: 1, height: chartHeight, fill: COLORS.gray300 }),
    ),
  )
}

function GaugeChart({ valore = 0, label = '', soglie = { verde: 70, giallo: 40 } }) {
  const v = Math.max(0, Math.min(100, Number(valore) || 0))
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

  return h(
    Svg,
    { width: 140, height: 90 },
    h(Path, { d: bgPath, stroke: COLORS.gray300, strokeWidth: 10, fill: 'none' }),
    h(Path, { d: valPath, stroke: color, strokeWidth: 10, fill: 'none', strokeLinecap: 'round' }),
    h(SvgText, { x: cx, y: cy - 8, textAnchor: 'middle', fontSize: 22, fill: color }, String(v)),
    h(SvgText, { x: cx, y: cy + 8, textAnchor: 'middle', fontSize: 8, fill: COLORS.gray600 }, label),
  )
}

function FlowSchema({ dati = {}, width = 440, height = 140 }) {
  const nodi = Array.isArray(dati.nodi) ? dati.nodi : []
  const archi = Array.isArray(dati.archi) ? dati.archi : []
  const nodeWidth = 90
  const nodeHeight = 30
  const gap = Math.max(12, Math.floor((width - nodi.length * nodeWidth) / Math.max(nodi.length + 1, 1)))
  const y = 46
  const positions = nodi.map((n, i) => ({ ...n, x: gap + i * (nodeWidth + gap), y }))

  return h(
    View,
    { style: { marginVertical: 10 } },
    h(
      Svg,
      { width, height },
      ...archi.map((a, i) => {
        const from = positions.find(p => p.id === a.da)
        const to = positions.find(p => p.id === a.a)
        if (!from || !to) return null
        return h(Line, {
          key: `e-${i}`,
          x1: from.x + nodeWidth,
          y1: from.y + nodeHeight / 2,
          x2: to.x,
          y2: to.y + nodeHeight / 2,
          stroke: COLORS.gray600,
          strokeWidth: 1,
        })
      }),
      ...positions.flatMap((n, i) => [
        h(Rect, { key: `nr-${i}`, x: n.x, y: n.y, width: nodeWidth, height: nodeHeight, rx: 4, fill: COLORS.gray100, stroke: COLORS.gray300 }),
        h(SvgText, { key: `nt-${i}`, x: n.x + nodeWidth / 2, y: n.y + 19, textAnchor: 'middle', fontSize: 8, fill: COLORS.primary }, n.label || ''),
      ]),
    ),
  )
}

function AutomationCard({ data }) {
  const complexityColor = data.complessita === 'bassa' ? COLORS.green : data.complessita === 'media' ? COLORS.orange : COLORS.red
  return h(
    View,
    { style: styles.automationCard },
    h(Text, { style: { fontSize: 11, fontWeight: 600, color: COLORS.primary, marginBottom: 4 } }, data.area || ''),
    h(Text, { style: { ...styles.bodyText, marginBottom: 6 } }, data.descrizione || ''),
    h(Text, { style: { ...styles.bodyText, fontSize: 9, color: COLORS.gray600 } }, `Impatto stimato: ${data.impatto_stimato || ''}`),
    h(Text, { style: { ...styles.bodyText, fontSize: 9, color: complexityColor } }, `Complessita: ${data.complessita || ''} · Orizzonte: ${data.orizzonte || ''}`),
  )
}

function renderVisualElement(el, key) {
  const tipo = el && el.tipo
  const dati = (el && el.dati) || {}

  return h(
    View,
    { key, style: { marginTop: 16 } },
    h(Text, { style: styles.subsectionTitle }, el.titolo || 'Elemento visivo'),
    tipo === 'tabella' ? h(TableComponent, { colonne: dati.colonne || [], righe: dati.righe || [] }) : null,
    tipo === 'grafico_barre' ? h(BarChart, { labels: dati.labels || [], valori: dati.valori || [], unita: dati.unita || '' }) : null,
    tipo === 'gauge' ? h(GaugeChart, { valore: dati.valore || 0, label: dati.label || '', soglie: dati.soglie || { verde: 70, giallo: 40 } }) : null,
    tipo === 'schema_flusso' ? h(FlowSchema, { dati }) : null,
    tipo === 'lista_prioritizzata'
      ? h(
          View,
          null,
          ...((dati.elementi || []).map((it, i) =>
            h(Text, { key: `lp-${i}`, style: { ...styles.bodyText, marginBottom: 3 } }, `• [${it.priorita || 'media'}] ${it.testo || ''}`),
          )),
        )
      : null,
  )
}

async function generateDiagnosiPDF(analysisJson) {
  const meta = analysisJson && analysisJson.meta ? analysisJson.meta : {}
  const sezioni = Array.isArray(analysisJson.sezioni) ? analysisJson.sezioni : []
  const automazioni = Array.isArray(analysisJson.automazioni_consigliate) ? analysisJson.automazioni_consigliate : []

  const doc = h(
    Document,
    {
      title: `Diagnosi AI Operativa - ${meta.settore || 'PMI italiana'}`,
      author: 'K2-AI',
      creator: 'K2-AI · k2-ai.it',
    },
    h(
      Page,
      { size: 'A4', style: styles.coverPage },
      h(
        View,
        null,
        h(Text, { style: styles.coverBadge }, 'Diagnosi AI Operativa'),
        h(Text, { style: styles.coverTitle }, `Analisi specializzata\n${meta.settore || 'PMI italiana'}`),
        h(Text, { style: styles.coverSubtitle }, 'Generata da K2-AI · Skill specializzate per il tuo settore'),
      ),
      h(
        View,
        null,
        h(
          Text,
          { style: styles.coverMeta },
          `Data: ${new Date(meta.data_generazione || Date.now()).toLocaleDateString('it-IT')}\nSkill attive: ${Array.isArray(meta.skill_attive) ? meta.skill_attive.join(' · ') : ''}\nk2-ai.it`,
        ),
      ),
    ),
    h(
      Page,
      { size: 'A4', style: styles.page },
      h(Text, { style: styles.sectionTitle }, 'Sintesi esecutiva'),
      h(Text, { style: styles.bodyText }, analysisJson.executive_summary || ''),
      h(PageFooter, { settore: meta.settore || 'PMI italiana' }),
    ),
    ...sezioni.map((sezione, idx) =>
      h(
        Page,
        { key: `s-${idx}`, size: 'A4', style: styles.page },
        h(Text, { style: styles.sectionTitle }, sezione.titolo || `Sezione ${idx + 1}`),
        h(Text, { style: styles.bodyText }, sezione.contenuto || ''),
        ...((sezione.elementi_visivi || []).map((el, eIdx) => renderVisualElement(el, `v-${idx}-${eIdx}`))),
        h(PageFooter, { settore: meta.settore || 'PMI italiana' }),
      ),
    ),
    h(
      Page,
      { size: 'A4', style: styles.page },
      h(Text, { style: styles.sectionTitle }, 'Cosa vale la pena automatizzare'),
      h(
        Text,
        { style: { ...styles.bodyText, marginBottom: 12, color: COLORS.gray600 } },
        'Orientamento strategico - non un piano implementativo. Per il dettaglio operativo contatta il team K2-AI.',
      ),
      ...automazioni.map((auto, idx) => h(AutomationCard, { key: `a-${idx}`, data: auto })),
      h(PageFooter, { settore: meta.settore || 'PMI italiana' }),
    ),
    h(
      Page,
      { size: 'A4', style: { ...styles.page, backgroundColor: COLORS.primary } },
      h(
        View,
        { style: { flex: 1, justifyContent: 'center', alignItems: 'center' } },
        h(Text, { style: { color: '#A5B4FC', fontSize: 11, marginBottom: 8 } }, 'Prossimo passo'),
        h(
          Text,
          { style: { color: COLORS.white, fontSize: 18, fontWeight: 700, textAlign: 'center', marginBottom: 16 } },
          analysisJson.prossimo_passo && analysisJson.prossimo_passo.testo ? analysisJson.prossimo_passo.testo : '',
        ),
        h(
          Text,
          { style: { color: COLORS.gray600, fontSize: 9, textAlign: 'center' } },
          'Vai su k2-ai.it/contatti - il form e gia pre-compilato con la tua situazione.',
        ),
      ),
      h(
        View,
        { style: { position: 'absolute', bottom: 32, left: 48, right: 48, alignItems: 'center' } },
        h(Text, { style: { color: COLORS.gray600, fontSize: 8 } }, 'K2-AI · k2-ai.it · ciao@k2-ai.it'),
      ),
    ),
  )

  return renderToBuffer(doc)
}

module.exports = { generateDiagnosiPDF }
