const fs = require('fs')
const path = require('path')

const FALLBACK = 'Dato non fornito'

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function text(value) {
  const normalized = String(value ?? '').trim()
  return normalized || FALLBACK
}

function list(items, className = '') {
  const values = Array.isArray(items) ? items : []
  if (values.length === 0) return `<p class="empty-state">${FALLBACK}</p>`
  return `<ul${className ? ` class="${className}"` : ''}>${values.map(item => `<li>${escapeHtml(text(item))}</li>`).join('')}</ul>`
}

function metricCards(metrics) {
  const values = Array.isArray(metrics) ? metrics : []
  return `<div class="metric-grid">${values.map(metric => `
    <div class="card metric">
      <div class="metric-value">${escapeHtml(text(metric && metric.value))}</div>
      <div class="metric-label">${escapeHtml(text(metric && metric.label))}</div>
    </div>
  `).join('')}</div>`
}

function checklist(items) {
  const values = Array.isArray(items) ? items : []
  if (values.length === 0) return `<p class="empty-state">${FALLBACK}</p>`
  return `<ul class="report-checklist">${values.map(item => `<li>${escapeHtml(text(item))}</li>`).join('')}</ul>`
}

function roadmap(items) {
  const values = Array.isArray(items) ? items : []
  if (values.length === 0) return `<p class="empty-state">${FALLBACK}</p>`
  return `<div class="roadmap-list">${values.map((item, index) => `
    <article class="roadmap-item">
      <div class="roadmap-index">${String(index + 1).padStart(2, '0')}</div>
      <div class="roadmap-content">
        <div class="roadmap-meta"><span>${escapeHtml(text(item.timeframe))}</span><span>${escapeHtml(text(item.owner))}</span></div>
        <h3>${escapeHtml(text(item.phaseTitle))}</h3>
        <p>${escapeHtml(text(item.phaseDescription))}</p>
      </div>
    </article>
  `).join('')}</div>`
}

function priorityBadge(level, variant) {
  const safeVariant = ['high', 'medium', 'low'].includes(String(variant)) ? String(variant) : 'medium'
  return `<span class="priority ${safeVariant}">${escapeHtml(text(level))}</span>`
}

function table(rows, columns) {
  const safeRows = Array.isArray(rows) ? rows : []
  const header = columns.map(column => `<th>${escapeHtml(column.label)}</th>`).join('')
  const body = safeRows.length
    ? safeRows.map(row => `<tr>${columns.map(column => {
        const raw = row && row[column.key]
        const value = column.render ? column.render(row) : escapeHtml(text(raw))
        return `<td>${value}</td>`
      }).join('')}</tr>`).join('')
    : `<tr><td colspan="${columns.length}">${FALLBACK}</td></tr>`

  return `<div class="report-table-wrap"><table class="report-table"><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table></div>`
}

function section(title, eyebrow, content) {
  return `
    <section class="report-section">
      <div class="section-heading">
        <p class="section-eyebrow">${escapeHtml(eyebrow)}</p>
        <h2>${escapeHtml(text(title))}</h2>
      </div>
      ${content}
    </section>
  `
}

function readIfExists(filePath) {
  try {
    return fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf8') : ''
  } catch {
    return ''
  }
}

function readReportCss() {
  const root = path.resolve(__dirname, '..', '..')
  const sourceCss = [
    path.join(root, 'src', 'css', 'base.css'),
    path.join(root, 'src', 'css', 'report.css'),
  ].map(readIfExists).join('\n')

  if (sourceCss.trim()) return sourceCss

  const assetsDir = path.join(root, 'dist', 'assets')
  try {
    return fs.readdirSync(assetsDir)
      .filter(file => file.endsWith('.css') && (file.startsWith('report-preview') || file.startsWith('base')))
      .map(file => readIfExists(path.join(assetsDir, file)))
      .join('\n')
  } catch {
    return ''
  }
}

function renderReportHtml(reportData) {
  const report = reportData || {}
  const sections = report.sections || {}
  const css = readReportCss()

  const parts = []

  if (sections.cover !== false) {
    parts.push(`
      <section class="report-cover">
        <div class="cover-topline">
          <span>${escapeHtml(text(report.meta && report.meta.category))}</span>
          <span>${escapeHtml(text(report.meta && report.meta.date))}</span>
        </div>
        <div class="cover-main">
          <p class="cover-client">${escapeHtml(text(report.client && report.client.name))}</p>
          <h1>${escapeHtml(text(report.meta && report.meta.title))}</h1>
          <p class="cover-subtitle">${escapeHtml(text(report.meta && report.meta.subtitle))}</p>
        </div>
        <div class="cover-bottom">
          <div><span>Perimetro</span><strong>${escapeHtml(text(report.client && report.client.scope))}</strong></div>
          <div><span>Codice report</span><strong>${escapeHtml(text(report.meta && report.meta.code))}</strong></div>
        </div>
      </section>
    `)
  }

  if (sections.executiveSummary !== false) {
    parts.push(section(report.executiveSummary && report.executiveSummary.title, '01', `
      <p class="lead-copy">${escapeHtml(text(report.executiveSummary && report.executiveSummary.text))}</p>
      ${metricCards(report.executiveSummary && report.executiveSummary.metrics)}
      <div class="takeaway"><span>Takeaway operativo</span><p>${escapeHtml(text(report.executiveSummary && report.executiveSummary.operationalTakeaway))}</p></div>
    `))
  }

  if (sections.context !== false) {
    const tags = Array.isArray(report.context && report.context.tags) ? report.context.tags : []
    parts.push(section(report.context && report.context.title, '02', `
      <div class="two-column">
        <div><h3>Scenario attuale</h3><p>${escapeHtml(text(report.context && report.context.currentScenario))}</p></div>
        <div><h3>Obiettivo del report</h3><p>${escapeHtml(text(report.context && report.context.reportObjective))}</p></div>
      </div>
      <div class="tag-list">${tags.length ? tags.map(tag => `<span>${escapeHtml(text(tag))}</span>`).join('') : `<span>${FALLBACK}</span>`}</div>
    `))
  }

  if (sections.problem !== false) {
    parts.push(section(report.problem && report.problem.title, '03', `
      <p class="lead-copy">${escapeHtml(text(report.problem && report.problem.main))}</p>
      ${table(report.problem && report.problem.rows, [
        { key: 'area', label: 'Area' },
        { key: 'criticalIssue', label: 'Criticita' },
        { key: 'effect', label: 'Effetto' },
        { key: 'priority', label: 'Priorita', render: row => priorityBadge(row.priority, row.priorityClass) },
      ])}
    `))
  }

  if (sections.analysis !== false) {
    const cards = Array.isArray(report.analysis && report.analysis.cards) ? report.analysis.cards : []
    parts.push(section(report.analysis && report.analysis.title, '04', `
      <p class="lead-copy">${escapeHtml(text(report.analysis && report.analysis.intro))}</p>
      <div class="card-grid">${cards.length ? cards.map(card => `<article class="card analysis-card"><h3>${escapeHtml(text(card.title))}</h3><p>${escapeHtml(text(card.description))}</p></article>`).join('') : `<p class="empty-state">${FALLBACK}</p>`}</div>
      ${table(report.analysis && report.analysis.table, [
        { key: 'parameter', label: 'Parametro' },
        { key: 'detectedStatus', label: 'Stato rilevato' },
        { key: 'evaluation', label: 'Valutazione' },
        { key: 'note', label: 'Note' },
      ])}
    `))
  }

  if (sections.opportunity !== false) {
    const items = Array.isArray(report.opportunity && report.opportunity.items) ? report.opportunity.items : []
    parts.push(section(report.opportunity && report.opportunity.title, '05', `
      <p class="lead-copy">${escapeHtml(text(report.opportunity && report.opportunity.intro))}</p>
      <div class="opportunity-grid">${items.length ? items.map(item => `
        <article class="opportunity-item">
          <h3>${escapeHtml(text(item.title))}</h3>
          <p>${escapeHtml(text(item.description))}</p>
          <dl><div><dt>Impatto</dt><dd>${escapeHtml(text(item.impact))}</dd></div><div><dt>Effort</dt><dd>${escapeHtml(text(item.effort))}</dd></div></dl>
        </article>
      `).join('') : `<p class="empty-state">${FALLBACK}</p>`}</div>
    `))
  }

  if (sections.solution !== false) {
    parts.push(section(report.solution && report.solution.title, '06', `
      <p class="lead-copy">${escapeHtml(text(report.solution && report.solution.description))}</p>
      ${checklist(report.solution && report.solution.components)}
      <div class="takeaway"><span>Risultato atteso</span><p>${escapeHtml(text(report.solution && report.solution.expectedResult))}</p></div>
    `))
  }

  if (sections.roadmap !== false) {
    parts.push(section(report.roadmap && report.roadmap.title, '07', `
      ${roadmap(report.roadmap && report.roadmap.items)}
    `))
  }

  if (sections.priorities !== false) {
    const items = Array.isArray(report.priorities && report.priorities.items) ? report.priorities.items : []
    parts.push(section(report.priorities && report.priorities.title, '08', `
      <div class="priority-list">${items.length ? items.map(item => `
        <article class="priority-item">
          ${priorityBadge(item.priorityLevel, item.priorityClass)}
          <h3>${escapeHtml(text(item.action))}</h3>
          <p>${escapeHtml(text(item.reason))}</p>
          <div class="priority-meta"><span>${escapeHtml(text(item.impact))}</span><span>${escapeHtml(text(item.timing))}</span></div>
        </article>
      `).join('') : `<p class="empty-state">${FALLBACK}</p>`}</div>
    `))
  }

  if (sections.impact !== false) {
    parts.push(section(report.impact && report.impact.title, '09', `
      ${metricCards(report.impact && report.impact.metrics)}
      ${table(report.impact && report.impact.rows, [
        { key: 'dimension', label: 'Dimensione' },
        { key: 'expectedImpact', label: 'Impatto atteso' },
        { key: 'indicator', label: 'Indicatore' },
      ])}
    `))
  }

  if (sections.recommendedPlan !== false) {
    parts.push(section(report.recommendedPlan && report.recommendedPlan.title, '10', `
      <p class="lead-copy">${escapeHtml(text(report.recommendedPlan && report.recommendedPlan.summary))}</p>
      ${table(report.recommendedPlan && report.recommendedPlan.steps, [
        { key: 'step', label: 'Step' },
        { key: 'activity', label: 'Attivita' },
        { key: 'output', label: 'Output' },
        { key: 'owner', label: 'Owner' },
      ])}
    `))
  }

  if (sections.nextSteps !== false) {
    parts.push(section(report.nextSteps && report.nextSteps.title, '11', `
      <div class="two-column">
        <div><h3>Azioni immediate</h3>${checklist(report.nextSteps && report.nextSteps.immediateActions)}</div>
        <div><h3>Decisioni richieste</h3>${checklist(report.nextSteps && report.nextSteps.requiredDecisions)}</div>
      </div>
      <div class="next-step-box"><span>Prossimo passo suggerito</span><p>${escapeHtml(text(report.nextSteps && report.nextSteps.suggestedNextStep))}</p></div>
    `))
  }

  if (sections.disclaimer !== false) {
    parts.push(section(report.disclaimer && report.disclaimer.title, '12', `
      <p>${escapeHtml(text(report.disclaimer && report.disclaimer.text))}</p>
    `))
  }

  parts.push(`
    <footer class="report-footer">
      <span>K2AI</span>
      <span>${escapeHtml(text(report.meta && report.meta.code))}</span>
      <span>${escapeHtml(text(report.meta && report.meta.version))}</span>
    </footer>
  `)

  return `<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(text(report.meta && report.meta.title))}</title>
  <style>
    ${css}
    @page { size: A4; margin: 16mm 12mm; }
    *, *::before, *::after { animation: none !important; transition: none !important; }
    body.report-preview-page { width: auto !important; }
  </style>
</head>
<body class="report-preview-page">
  <div class="k2ai-report"><main class="document">${parts.join('\n')}</main></div>
</body>
</html>`
}

async function resolveExecutablePath(chromium) {
  if (process.env.PUPPETEER_EXECUTABLE_PATH) return process.env.PUPPETEER_EXECUTABLE_PATH
  if (process.env.CHROME_BIN) return process.env.CHROME_BIN

  const projectBrowserExecutable = findProjectBrowserExecutable()
  if (projectBrowserExecutable) return projectBrowserExecutable

  const localCandidates = process.platform === 'darwin'
    ? [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
        '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
      ]
    : process.platform === 'win32'
      ? [
          'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
          'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
          'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
        ]
      : [
          '/usr/bin/google-chrome',
          '/usr/bin/google-chrome-stable',
          '/usr/bin/chromium',
          '/usr/bin/chromium-browser',
        ]

  const localExecutable = localCandidates.find(candidate => fs.existsSync(candidate))
  if (localExecutable) return localExecutable

  if (chromium && typeof chromium.executablePath === 'function') {
    const bundledExecutable = await chromium.executablePath()
    if (bundledExecutable) return bundledExecutable
  }

  if (process.platform !== 'linux') {
    throw new Error('Chrome/Chromium locale non trovato. Imposta PUPPETEER_EXECUTABLE_PATH per generare PDF su questa macchina.')
  }

  return undefined
}

function findProjectBrowserExecutable() {
  const browserRoot = path.join(__dirname, '..', '..', '.local-browsers')
  if (!fs.existsSync(browserRoot)) return null

  const executableNames = process.platform === 'darwin'
    ? new Set(['Google Chrome for Testing', 'Google Chrome', 'Chromium', 'Brave Browser', 'Microsoft Edge'])
    : process.platform === 'win32'
      ? new Set(['chrome.exe', 'msedge.exe'])
      : new Set(['chrome', 'chromium', 'google-chrome'])

  const stack = [browserRoot]
  while (stack.length > 0) {
    const currentDir = stack.pop()
    if (!currentDir) continue

    let entries = []
    try {
      entries = fs.readdirSync(currentDir, { withFileTypes: true })
    } catch {
      continue
    }

    for (const entry of entries) {
      if (entry.name.startsWith('._')) continue
      const absolutePath = path.join(currentDir, entry.name)
      if (entry.isDirectory()) {
        stack.push(absolutePath)
        continue
      }
      if (entry.isFile() && executableNames.has(entry.name)) {
        return absolutePath
      }
    }
  }

  return null
}

async function generatePDF(reportData) {
  const puppeteer = require('puppeteer-core')
  const chromium = require('@sparticuz/chromium')
  const executablePath = await resolveExecutablePath(chromium)
  const useChromiumLambdaRuntime = process.platform === 'linux' && String(executablePath || '').includes('/tmp/')
  const launchArgs = useChromiumLambdaRuntime
    ? (chromium.args || ['--no-sandbox', '--disable-setuid-sandbox'])
    : ['--no-sandbox', '--disable-setuid-sandbox']

  const browser = await puppeteer.launch({
    args: launchArgs,
    defaultViewport: { width: 1240, height: 1754, deviceScaleFactor: 1 },
    executablePath,
    headless: true,
  })

  try {
    const page = await browser.newPage()
    await page.emulateMediaType('print')
    await page.setContent(renderReportHtml(reportData), { waitUntil: 'networkidle0' })
    const pdf = await page.pdf({
      format: 'A4',
      printBackground: true,
      margin: {
        top: '16mm',
        bottom: '16mm',
        left: '12mm',
        right: '12mm',
      },
      preferCSSPageSize: false,
    })
    return Buffer.from(pdf)
  } finally {
    await browser.close()
  }
}

module.exports = {
  generatePDF,
  renderReportHtml,
}
