const {
  AlignmentType,
  BorderStyle,
  Document,
  Footer,
  HeadingLevel,
  Packer,
  PageNumber,
  Paragraph,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
} = require('docx')

const FALLBACK = 'Dato non fornito'

function text(value) {
  const normalized = String(value ?? '').trim()
  return normalized || FALLBACK
}

function array(value) {
  return Array.isArray(value) ? value : []
}

function heading(value, level = HeadingLevel.HEADING_1) {
  return new Paragraph({
    text: text(value),
    heading: level,
    spacing: { before: 360, after: 160 },
  })
}

function paragraph(value, options = {}) {
  return new Paragraph({
    children: [new TextRun({ text: text(value), size: 22 })],
    spacing: { after: 160, line: 300 },
    ...options,
  })
}

function labelValue(label, value) {
  return new Paragraph({
    children: [
      new TextRun({ text: `${text(label)}: `, bold: true, size: 21 }),
      new TextRun({ text: text(value), size: 21 }),
    ],
    spacing: { after: 100 },
  })
}

function bullet(value) {
  return paragraph(value, {
    bullet: { level: 0 },
    spacing: { after: 80, line: 280 },
  })
}

function bulletList(items) {
  const values = array(items)
  return values.length ? values.map(bullet) : [paragraph(FALLBACK)]
}

function tableCell(value, shaded = false) {
  return new TableCell({
    shading: shaded ? { fill: 'F3F4F6' } : undefined,
    margins: { top: 120, bottom: 120, left: 120, right: 120 },
    children: [
      new Paragraph({
        children: [new TextRun({ text: text(value), bold: shaded, size: 20 })],
        spacing: { after: 0 },
      }),
    ],
  })
}

function dataTable(headers, rows) {
  const safeRows = array(rows)
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 1, color: 'D1D5DB' },
      bottom: { style: BorderStyle.SINGLE, size: 1, color: 'D1D5DB' },
      left: { style: BorderStyle.SINGLE, size: 1, color: 'D1D5DB' },
      right: { style: BorderStyle.SINGLE, size: 1, color: 'D1D5DB' },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: 'E5E7EB' },
      insideVertical: { style: BorderStyle.SINGLE, size: 1, color: 'E5E7EB' },
    },
    rows: [
      new TableRow({ children: headers.map(header => tableCell(header, true)) }),
      ...(safeRows.length ? safeRows : [headers.map(() => FALLBACK)]).map(row =>
        new TableRow({ children: row.map(value => tableCell(value)) }),
      ),
    ],
  })
}

function spacer() {
  return new Paragraph({ text: '', spacing: { after: 120 } })
}

function metricTable(metrics) {
  return dataTable(
    ['Valore', 'Indicatore'],
    array(metrics).map(metric => [metric && metric.value, metric && metric.label]),
  )
}

function problemRows(rows) {
  return dataTable(
    ['Area', 'Criticita', 'Effetto', 'Priorita'],
    array(rows).map(row => [row.area, row.criticalIssue, row.effect, row.priority]),
  )
}

function analysisRows(rows) {
  return dataTable(
    ['Parametro', 'Stato rilevato', 'Valutazione', 'Note'],
    array(rows).map(row => [row.parameter, row.detectedStatus, row.evaluation, row.note]),
  )
}

function opportunityRows(rows) {
  return dataTable(
    ['Opportunita', 'Descrizione', 'Impatto', 'Effort'],
    array(rows).map(row => [row.title, row.description, row.impact, row.effort]),
  )
}

function roadmapRows(rows) {
  return dataTable(
    ['Fase', 'Timeframe', 'Owner', 'Descrizione'],
    array(rows).map(row => [row.phaseTitle, row.timeframe, row.owner, row.phaseDescription]),
  )
}

function priorityRows(rows) {
  return dataTable(
    ['Priorita', 'Azione', 'Motivo', 'Impatto', 'Timing'],
    array(rows).map(row => [row.priorityLevel, row.action, row.reason, row.impact, row.timing]),
  )
}

function impactRows(rows) {
  return dataTable(
    ['Dimensione', 'Impatto atteso', 'Indicatore'],
    array(rows).map(row => [row.dimension, row.expectedImpact, row.indicator]),
  )
}

function planRows(rows) {
  return dataTable(
    ['Step', 'Attivita', 'Output', 'Owner'],
    array(rows).map(row => [row.step, row.activity, row.output, row.owner]),
  )
}

function generateChildren(reportData) {
  const report = reportData || {}
  const children = [
    new Paragraph({
      text: text(report.meta && report.meta.title),
      heading: HeadingLevel.TITLE,
      alignment: AlignmentType.CENTER,
      spacing: { after: 240 },
    }),
    new Paragraph({
      children: [new TextRun({ text: text(report.meta && report.meta.subtitle), italics: true, size: 24 })],
      alignment: AlignmentType.CENTER,
      spacing: { after: 360 },
    }),
    labelValue('Categoria', report.meta && report.meta.category),
    labelValue('Data', report.meta && report.meta.date),
    labelValue('Codice report', report.meta && report.meta.code),
    labelValue('Cliente', report.client && report.client.name),
    labelValue('Perimetro', report.client && report.client.scope),
    heading('Executive summary'),
    paragraph(report.executiveSummary && report.executiveSummary.text),
    heading('Metriche principali', HeadingLevel.HEADING_2),
    metricTable(report.executiveSummary && report.executiveSummary.metrics),
    spacer(),
    labelValue('Takeaway operativo', report.executiveSummary && report.executiveSummary.operationalTakeaway),
    heading('Contesto aziendale'),
    labelValue('Scenario attuale', report.context && report.context.currentScenario),
    labelValue('Obiettivo del report', report.context && report.context.reportObjective),
    heading('Tag', HeadingLevel.HEADING_2),
    ...bulletList(report.context && report.context.tags),
    heading('Problema rilevato'),
    paragraph(report.problem && report.problem.main),
    problemRows(report.problem && report.problem.rows),
    spacer(),
    heading('Analisi operativa'),
    paragraph(report.analysis && report.analysis.intro),
    ...array(report.analysis && report.analysis.cards).flatMap(card => [
      heading(card.title, HeadingLevel.HEADING_2),
      paragraph(card.description),
    ]),
    analysisRows(report.analysis && report.analysis.table),
    spacer(),
    heading('Opportunita AI'),
    paragraph(report.opportunity && report.opportunity.intro),
    opportunityRows(report.opportunity && report.opportunity.items),
    spacer(),
    heading('Soluzione proposta'),
    paragraph(report.solution && report.solution.description),
    heading('Componenti', HeadingLevel.HEADING_2),
    ...bulletList(report.solution && report.solution.components),
    labelValue('Risultato atteso', report.solution && report.solution.expectedResult),
    heading('Roadmap di implementazione'),
    roadmapRows(report.roadmap && report.roadmap.items),
    spacer(),
    heading('Priorita operative'),
    priorityRows(report.priorities && report.priorities.items),
    spacer(),
    heading('Impatto atteso'),
    metricTable(report.impact && report.impact.metrics),
    spacer(),
    impactRows(report.impact && report.impact.rows),
    spacer(),
    heading('Piano consigliato'),
    paragraph(report.recommendedPlan && report.recommendedPlan.summary),
    planRows(report.recommendedPlan && report.recommendedPlan.steps),
    spacer(),
    heading('Next step'),
    heading('Azioni immediate', HeadingLevel.HEADING_2),
    ...bulletList(report.nextSteps && report.nextSteps.immediateActions),
    heading('Decisioni richieste', HeadingLevel.HEADING_2),
    ...bulletList(report.nextSteps && report.nextSteps.requiredDecisions),
    labelValue('Prossimo passo suggerito', report.nextSteps && report.nextSteps.suggestedNextStep),
    heading(report.disclaimer && report.disclaimer.title),
    paragraph(report.disclaimer && report.disclaimer.text),
  ]

  return children
}

async function generateDocx(reportData) {
  const doc = new Document({
    creator: 'K2-AI',
    description: 'Report K-BOT esportato in formato Word modificabile',
    title: text(reportData && reportData.meta && reportData.meta.title),
    styles: {
      default: {
        document: {
          run: { font: 'Aptos', size: 22, color: '111827' },
          paragraph: { spacing: { after: 140, line: 300 } },
        },
      },
      paragraphStyles: [
        {
          id: 'Title',
          name: 'Title',
          basedOn: 'Normal',
          next: 'Normal',
          run: { size: 38, bold: true, color: '111827', font: 'Aptos Display' },
          paragraph: { spacing: { after: 240 } },
        },
        {
          id: 'Heading1',
          name: 'Heading 1',
          basedOn: 'Normal',
          next: 'Normal',
          run: { size: 30, bold: true, color: '111827', font: 'Aptos Display' },
          paragraph: { spacing: { before: 420, after: 180 } },
        },
        {
          id: 'Heading2',
          name: 'Heading 2',
          basedOn: 'Normal',
          next: 'Normal',
          run: { size: 24, bold: true, color: '374151', font: 'Aptos' },
          paragraph: { spacing: { before: 240, after: 120 } },
        },
      ],
    },
    sections: [{
      properties: {
        page: {
          margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 },
        },
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [
                new TextRun({ text: 'K2-AI - ' }),
                new TextRun({ children: [PageNumber.CURRENT] }),
              ],
            }),
          ],
        }),
      },
      children: generateChildren(reportData),
    }],
  })

  return Packer.toBuffer(doc)
}

module.exports = {
  generateDocx,
}
