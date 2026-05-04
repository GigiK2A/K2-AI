import type {
  AnalysisCard,
  AnalysisTableRow,
  ClientInfo,
  ContextData,
  DisclaimerData,
  ExecutiveSummaryData,
  ImpactData,
  ImpactRow,
  Metric,
  NextStepsData,
  Opportunity,
  OpportunityData,
  PrioritiesData,
  PriorityItem,
  PriorityLevel,
  ProblemData,
  ProblemRow,
  RecommendedPlanData,
  RecommendedPlanStep,
  ReportData,
  ReportMeta,
  ReportSectionVisibility,
  RoadmapData,
  RoadmapItem,
  SolutionData,
} from '../../src/types/report'
import { mockReportData } from '../../src/data/mockReportData'
import { getSuiteAiServiceById, normalizeServiceId } from './services'

const FALLBACK = 'Dato non fornito'
const DEFAULT_SERVICE_ID = 'P12'

type PlainObject = Record<string, unknown>

export interface KbotReportSessionData {
  id?: string
  serviceId?: unknown
  service_id?: unknown
  selectedService?: unknown
  recommendedTier?: unknown
  recommended_tier?: unknown
  conversationSummary?: unknown
  summary?: unknown
  extractedData?: unknown
  collected_data?: unknown
  messages?: unknown
  created_at?: unknown
  updated_at?: unknown
}

function isObject(value: unknown): value is PlainObject {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}

function text(value: unknown): string {
  if (typeof value === 'string' && value.trim()) return value.trim()
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return FALLBACK
}

function cloneMockReportData(): ReportData {
  return JSON.parse(JSON.stringify(mockReportData)) as ReportData
}

function cleanString(value: unknown): string {
  const normalized = text(value)
  return normalized.trim() || FALLBACK
}

function cleanArray<T>(value: unknown, mapper: (item: unknown, index: number) => T): T[] {
  if (!Array.isArray(value)) return []
  return value.map(mapper)
}

function isMetricValueNonsense(value: string): boolean {
  const normalized = value.trim().toLowerCase()
  return !normalized ||
    normalized === FALLBACK.toLowerCase() ||
    normalized === 'nan' ||
    normalized === 'infinity' ||
    normalized === '-infinity' ||
    normalized === 'undefined' ||
    normalized === 'null' ||
    normalized === '[object object]' ||
    normalized === 'object object' ||
    normalized === '{}' ||
    normalized === '[]'
}

function cleanMetric(value: unknown): Metric {
  const source = isObject(value) ? value : {}
  const metricValue = cleanString(source.value)
  return {
    value: isMetricValueNonsense(metricValue) ? FALLBACK : metricValue,
    label: cleanString(source.label),
  }
}

function cleanMetrics(value: unknown): [Metric, Metric, Metric] {
  const metrics = cleanArray(value, cleanMetric)
  return [
    metrics[0] || { value: FALLBACK, label: FALLBACK },
    metrics[1] || { value: FALLBACK, label: FALLBACK },
    metrics[2] || { value: FALLBACK, label: FALLBACK },
  ]
}

function cleanStringArray(value: unknown): string[] {
  return cleanArray(value, item => cleanString(item))
}

function cleanPriorityLabel(value: unknown, priorityClass: PriorityLevel): string {
  const normalized = cleanString(value)
  return normalized === FALLBACK ? priorityLabel(priorityClass) : normalized
}

function optionalText(value: unknown): string | null {
  const normalized = text(value)
  return normalized === FALLBACK ? null : normalized
}

function stringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return value.map(item => text(item)).filter(item => item !== FALLBACK)
}

function objectArray(value: unknown): PlainObject[] {
  return Array.isArray(value) ? value.filter(isObject) : []
}

function normalizePriority(value: unknown): PriorityLevel {
  const normalized = String(value || '').trim().toLowerCase()
  if (normalized === 'high' || normalized === 'alta' || normalized === 'alto') return 'high'
  if (normalized === 'low' || normalized === 'bassa' || normalized === 'basso') return 'low'
  return 'medium'
}

function priorityLabel(priorityClass: PriorityLevel): string {
  if (priorityClass === 'high') return 'Alta'
  if (priorityClass === 'low') return 'Bassa'
  return 'Media'
}

function readPath(source: PlainObject, path: string): unknown {
  return path.split('.').reduce<unknown>((current, key) => {
    if (!isObject(current)) return undefined
    return current[key]
  }, source)
}

function firstValue(source: PlainObject, paths: string[]): unknown {
  for (const path of paths) {
    const value = readPath(source, path)
    if (optionalText(value) || isObject(value) || (Array.isArray(value) && value.length > 0)) return value
  }
  return undefined
}

function getConversationText(messages: unknown): string {
  if (!Array.isArray(messages)) return FALLBACK

  const userTurns = messages
    .filter(isObject)
    .filter(message => message.role === 'user')
    .map(message => text(message.content || message.text))
    .filter(message => message !== FALLBACK)

  return userTurns.length ? userTurns.join('\n') : FALLBACK
}

function normalizeSessionData(sessionData: KbotReportSessionData): PlainObject {
  const collectedData = isObject(sessionData.collected_data) ? sessionData.collected_data : {}
  const extractedData = isObject(sessionData.extractedData)
    ? sessionData.extractedData
    : isObject(collectedData.extractedData)
      ? collectedData.extractedData
      : {}

  return {
    ...sessionData,
    ...collectedData,
    extractedData,
    conversation: getConversationText(sessionData.messages),
  }
}

function resolveService(source: PlainObject) {
  const selectedService = firstValue(source, ['selectedService', 'service'])
  if (isObject(selectedService)) {
    const id = normalizeServiceId(selectedService.id)
    const knownService = getSuiteAiServiceById(id)
    return knownService || {
      id: id || DEFAULT_SERVICE_ID,
      name: text(selectedService.name),
      shortDescription: text(selectedService.shortDescription || selectedService.description),
      target: text(selectedService.target),
      recommendedTier: text(selectedService.recommendedTier),
      tags: stringArray(selectedService.tags),
      useCases: stringArray(selectedService.useCases),
    }
  }

  const serviceId = normalizeServiceId(firstValue(source, [
    'selectedService',
    'serviceId',
    'service_id',
    'extractedData.recommendedServiceId',
  ]) || DEFAULT_SERVICE_ID)

  return getSuiteAiServiceById(serviceId) || getSuiteAiServiceById(DEFAULT_SERVICE_ID)
}

function fallbackList(items: string[], fallback: string): string[] {
  return items.length ? items : [fallback]
}

function makeMetric(value: unknown, label: unknown): Metric {
  return { value: text(value), label: text(label) }
}

function mapMetrics(source: PlainObject, fallbackMetrics: [Metric, Metric, Metric]): [Metric, Metric, Metric] {
  const metrics = objectArray(firstValue(source, ['metrics', 'extractedData.metrics']))
    .map(metric => makeMetric(metric.value, metric.label))
    .slice(0, 3)

  return [
    metrics[0] || fallbackMetrics[0],
    metrics[1] || fallbackMetrics[1],
    metrics[2] || fallbackMetrics[2],
  ]
}

function mapProblemRows(source: PlainObject): ProblemRow[] {
  const rows = objectArray(firstValue(source, ['problemRows', 'problems', 'extractedData.problemRows', 'extractedData.problems']))
    .map(row => {
      const priorityClass = normalizePriority(row.priorityClass || row.priority)
      return {
        area: text(row.area || row.title || row.parameter),
        criticalIssue: text(row.criticalIssue || row.issue || row.problem || row.description),
        effect: text(row.effect || row.impact || row.note),
        priority: text(row.priority) === FALLBACK ? priorityLabel(priorityClass) : text(row.priority),
        priorityClass,
      }
    })

  if (rows.length > 0) return rows

  return [{
    area: text(firstValue(source, ['extractedData.businessType', 'businessType', 'serviceName'])),
    criticalIssue: text(firstValue(source, ['extractedData.problem', 'problem'])),
    effect: text(firstValue(source, ['extractedData.urgency', 'urgency', 'extractedData.notes', 'notes'])),
    priority: 'Media',
    priorityClass: 'medium',
  }]
}

function mapAnalysisCards(source: PlainObject): AnalysisCard[] {
  const cards = objectArray(firstValue(source, ['analysisCards', 'analysis.cards', 'extractedData.analysisCards']))
    .map(card => ({
      title: text(card.title),
      description: text(card.description || card.text),
    }))

  if (cards.length > 0) return cards

  return [
    {
      title: 'Processo attuale',
      description: text(firstValue(source, ['extractedData.currentProcess', 'currentProcess'])),
    },
    {
      title: 'Dati disponibili',
      description: text(firstValue(source, ['extractedData.dataAvailable', 'dataAvailable'])),
    },
    {
      title: 'Note operative',
      description: text(firstValue(source, ['extractedData.notes', 'notes', 'conversation'])),
    },
  ]
}

function mapAnalysisTable(source: PlainObject): AnalysisTableRow[] {
  const rows = objectArray(firstValue(source, ['analysisTable', 'analysis.table', 'extractedData.analysisTable']))
    .map(row => ({
      parameter: text(row.parameter),
      detectedStatus: text(row.detectedStatus || row.status),
      evaluation: text(row.evaluation || row.rating),
      note: text(row.note || row.description),
    }))

  if (rows.length > 0) return rows

  return [
    {
      parameter: 'Urgenza',
      detectedStatus: text(firstValue(source, ['extractedData.urgency', 'urgency'])),
      evaluation: text(firstValue(source, ['extractedData.recommendedTier', 'recommendedTier', 'recommended_tier'])),
      note: 'Dato raccolto da K-BOT.',
    },
    {
      parameter: 'Integrazioni',
      detectedStatus: text(firstValue(source, ['extractedData.integrations', 'integrations'])),
      evaluation: FALLBACK,
      note: 'Da validare in fase di scoping.',
    },
    {
      parameter: 'Budget',
      detectedStatus: text(firstValue(source, ['extractedData.budget', 'budget'])),
      evaluation: FALLBACK,
      note: 'Da confermare con il cliente.',
    },
  ]
}

function mapOpportunities(source: PlainObject, serviceUseCases: string[]): Opportunity[] {
  const opportunities = objectArray(firstValue(source, ['opportunities', 'extractedData.opportunities']))
    .map(item => ({
      title: text(item.title),
      description: text(item.description || item.text),
      impact: text(item.impact),
      effort: text(item.effort),
    }))

  if (opportunities.length > 0) return opportunities

  return fallbackList(serviceUseCases, FALLBACK).slice(0, 4).map(useCase => ({
    title: useCase,
    description: text(firstValue(source, ['extractedData.goal', 'goal'])),
    impact: 'Da stimare',
    effort: 'Da stimare',
  }))
}

function mapRoadmap(source: PlainObject): RoadmapItem[] {
  const items = objectArray(firstValue(source, ['roadmap', 'roadmap.items', 'extractedData.roadmap']))
    .map(item => ({
      phaseTitle: text(item.phaseTitle || item.title),
      timeframe: text(item.timeframe),
      owner: text(item.owner),
      phaseDescription: text(item.phaseDescription || item.description),
    }))

  if (items.length > 0) return items

  return [
    {
      phaseTitle: 'Fase 1 - Scoping',
      timeframe: 'Settimana 1',
      owner: 'Cliente + K2-AI',
      phaseDescription: 'Confermare processo, dati disponibili, vincoli e risultato atteso.',
    },
    {
      phaseTitle: 'Fase 2 - Prototipo',
      timeframe: 'Settimane 2-3',
      owner: 'K2-AI',
      phaseDescription: 'Preparare un primo flusso operativo sul perimetro selezionato.',
    },
    {
      phaseTitle: 'Fase 3 - Validazione',
      timeframe: 'Settimana 4',
      owner: 'Cliente + K2-AI',
      phaseDescription: 'Testare casi reali, raccogliere feedback e misurare gli indicatori principali.',
    },
  ]
}

function mapPriorities(source: PlainObject): PriorityItem[] {
  const items = objectArray(firstValue(source, ['priorities', 'priorities.items', 'extractedData.priorities']))
    .map(item => {
      const priorityClass = normalizePriority(item.priorityClass || item.priorityLevel || item.priority)
      return {
        priorityLevel: text(item.priorityLevel || item.priority) === FALLBACK
          ? priorityLabel(priorityClass)
          : text(item.priorityLevel || item.priority),
        priorityClass,
        action: text(item.action || item.title),
        reason: text(item.reason || item.description),
        impact: text(item.impact),
        timing: text(item.timing || item.timeframe),
      }
    })

  if (items.length > 0) return items

  return [{
    priorityLevel: 'Alta',
    priorityClass: 'high',
    action: text(firstValue(source, ['extractedData.goal', 'goal', 'nextStep'])),
    reason: text(firstValue(source, ['extractedData.problem', 'problem'])),
    impact: text(firstValue(source, ['extractedData.urgency', 'urgency'])),
    timing: 'Subito',
  }]
}

function mapImpactRows(source: PlainObject): ImpactRow[] {
  const rows = objectArray(firstValue(source, ['impactRows', 'impact.rows', 'extractedData.impactRows']))
    .map(row => ({
      dimension: text(row.dimension),
      expectedImpact: text(row.expectedImpact || row.impact),
      indicator: text(row.indicator),
    }))

  if (rows.length > 0) return rows

  return [
    {
      dimension: 'Tempo',
      expectedImpact: text(firstValue(source, ['extractedData.goal', 'goal'])),
      indicator: 'Ore risparmiate o tempi ciclo ridotti.',
    },
    {
      dimension: 'Qualita operativa',
      expectedImpact: text(firstValue(source, ['extractedData.problem', 'problem'])),
      indicator: 'Riduzione errori, rilavorazioni o passaggi manuali.',
    },
  ]
}

function mapPlanSteps(source: PlainObject): RecommendedPlanStep[] {
  const steps = objectArray(firstValue(source, ['recommendedPlan.steps', 'planSteps', 'extractedData.planSteps']))
    .map((step, index) => ({
      step: text(step.step) === FALLBACK ? String(index + 1).padStart(2, '0') : text(step.step),
      activity: text(step.activity || step.title),
      output: text(step.output),
      owner: text(step.owner),
    }))

  if (steps.length > 0) return steps

  return [
    { step: '01', activity: 'Validazione dati K-BOT', output: 'Perimetro confermato', owner: 'Cliente + K2-AI' },
    { step: '02', activity: 'Disegno flusso operativo', output: 'Schema soluzione e requisiti', owner: 'K2-AI' },
    { step: '03', activity: 'Prototipo e test', output: 'Demo funzionante su casi reali', owner: 'K2-AI' },
  ]
}

function dateLabel(value: unknown): string {
  const date = optionalText(value) ? new Date(String(value)) : new Date()
  if (Number.isNaN(date.getTime())) return new Date().toLocaleDateString('it-IT')
  return date.toLocaleDateString('it-IT', { day: '2-digit', month: 'long', year: 'numeric' })
}

function validateReportMeta(value: unknown): ReportMeta {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    subtitle: cleanString(source.subtitle),
    category: cleanString(source.category),
    code: cleanString(source.code),
    date: cleanString(source.date),
    version: cleanString(source.version),
  }
}

function validateClientInfo(value: unknown): ClientInfo {
  const source = isObject(value) ? value : {}
  return {
    name: cleanString(source.name),
    scope: cleanString(source.scope),
  }
}

function validateSections(value: unknown): ReportSectionVisibility {
  const source = isObject(value) ? value : {}
  return {
    cover: source.cover !== false,
    executiveSummary: source.executiveSummary !== false,
    context: source.context !== false,
    problem: source.problem !== false,
    analysis: source.analysis !== false,
    opportunity: source.opportunity !== false,
    solution: source.solution !== false,
    roadmap: source.roadmap !== false,
    priorities: source.priorities !== false,
    impact: source.impact !== false,
    recommendedPlan: source.recommendedPlan !== false,
    nextSteps: source.nextSteps !== false,
    disclaimer: source.disclaimer !== false,
  }
}

function validateExecutiveSummary(value: unknown): ExecutiveSummaryData {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    text: cleanString(source.text),
    metrics: cleanMetrics(source.metrics),
    operationalTakeaway: cleanString(source.operationalTakeaway),
  }
}

function validateContext(value: unknown): ContextData {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    currentScenario: cleanString(source.currentScenario),
    reportObjective: cleanString(source.reportObjective),
    tags: cleanStringArray(source.tags),
  }
}

function validateProblemRow(value: unknown): ProblemRow {
  const source = isObject(value) ? value : {}
  const priorityClass = normalizePriority(source.priorityClass || source.priority)
  return {
    area: cleanString(source.area),
    criticalIssue: cleanString(source.criticalIssue),
    effect: cleanString(source.effect),
    priority: cleanPriorityLabel(source.priority, priorityClass),
    priorityClass,
  }
}

function validateProblem(value: unknown): ProblemData {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    main: cleanString(source.main),
    rows: cleanArray(source.rows, validateProblemRow),
  }
}

function validateAnalysisCard(value: unknown): AnalysisCard {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    description: cleanString(source.description),
  }
}

function validateAnalysisTableRow(value: unknown): AnalysisTableRow {
  const source = isObject(value) ? value : {}
  return {
    parameter: cleanString(source.parameter),
    detectedStatus: cleanString(source.detectedStatus),
    evaluation: cleanString(source.evaluation),
    note: cleanString(source.note),
  }
}

function validateAnalysis(value: unknown) {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    intro: cleanString(source.intro),
    cards: cleanArray(source.cards, validateAnalysisCard),
    table: cleanArray(source.table, validateAnalysisTableRow),
  }
}

function validateOpportunity(value: unknown): Opportunity {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    description: cleanString(source.description),
    impact: cleanString(source.impact),
    effort: cleanString(source.effort),
  }
}

function validateOpportunityData(value: unknown): OpportunityData {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    intro: cleanString(source.intro),
    items: cleanArray(source.items, validateOpportunity),
  }
}

function validateSolution(value: unknown): SolutionData {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    description: cleanString(source.description),
    components: cleanStringArray(source.components),
    expectedResult: cleanString(source.expectedResult),
  }
}

function validateRoadmapItem(value: unknown): RoadmapItem {
  const source = isObject(value) ? value : {}
  return {
    phaseTitle: cleanString(source.phaseTitle),
    timeframe: cleanString(source.timeframe),
    owner: cleanString(source.owner),
    phaseDescription: cleanString(source.phaseDescription),
  }
}

function validateRoadmap(value: unknown): RoadmapData {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    items: cleanArray(source.items, validateRoadmapItem),
  }
}

function validatePriorityItem(value: unknown): PriorityItem {
  const source = isObject(value) ? value : {}
  const priorityClass = normalizePriority(source.priorityClass || source.priorityLevel)
  return {
    priorityLevel: cleanPriorityLabel(source.priorityLevel, priorityClass),
    priorityClass,
    action: cleanString(source.action),
    reason: cleanString(source.reason),
    impact: cleanString(source.impact),
    timing: cleanString(source.timing),
  }
}

function validatePriorities(value: unknown): PrioritiesData {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    items: cleanArray(source.items, validatePriorityItem),
  }
}

function validateImpactRow(value: unknown): ImpactRow {
  const source = isObject(value) ? value : {}
  return {
    dimension: cleanString(source.dimension),
    expectedImpact: cleanString(source.expectedImpact),
    indicator: cleanString(source.indicator),
  }
}

function validateImpact(value: unknown): ImpactData {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    metrics: cleanMetrics(source.metrics),
    rows: cleanArray(source.rows, validateImpactRow),
  }
}

function validateRecommendedPlanStep(value: unknown): RecommendedPlanStep {
  const source = isObject(value) ? value : {}
  return {
    step: cleanString(source.step),
    activity: cleanString(source.activity),
    output: cleanString(source.output),
    owner: cleanString(source.owner),
  }
}

function validateRecommendedPlan(value: unknown): RecommendedPlanData {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    summary: cleanString(source.summary),
    steps: cleanArray(source.steps, validateRecommendedPlanStep),
  }
}

function validateNextSteps(value: unknown): NextStepsData {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    immediateActions: cleanStringArray(source.immediateActions),
    requiredDecisions: cleanStringArray(source.requiredDecisions),
    suggestedNextStep: cleanString(source.suggestedNextStep),
  }
}

function validateDisclaimer(value: unknown): DisclaimerData {
  const source = isObject(value) ? value : {}
  return {
    title: cleanString(source.title),
    text: cleanString(source.text),
  }
}

export function validateReportData(data: unknown): ReportData {
  if (!isObject(data)) return cloneMockReportData()

  try {
    return {
      meta: validateReportMeta(data.meta),
      client: validateClientInfo(data.client),
      sections: validateSections(data.sections),
      executiveSummary: validateExecutiveSummary(data.executiveSummary),
      context: validateContext(data.context),
      problem: validateProblem(data.problem),
      analysis: validateAnalysis(data.analysis),
      opportunity: validateOpportunityData(data.opportunity),
      solution: validateSolution(data.solution),
      roadmap: validateRoadmap(data.roadmap),
      priorities: validatePriorities(data.priorities),
      impact: validateImpact(data.impact),
      recommendedPlan: validateRecommendedPlan(data.recommendedPlan),
      nextSteps: validateNextSteps(data.nextSteps),
      disclaimer: validateDisclaimer(data.disclaimer),
    }
  } catch {
    return cloneMockReportData()
  }
}

export function generateReportData(sessionData: KbotReportSessionData): ReportData {
  const source = normalizeSessionData(sessionData)
  const service = resolveService(source)
  const serviceName = text(firstValue(source, ['selectedService.name', 'extractedData.recommendedServiceName']) || service?.name)
  const recommendedTier = text(firstValue(source, [
    'recommendedTier',
    'recommended_tier',
    'extractedData.recommendedTier',
  ]) || service?.recommendedTier)
  const conversationSummary = text(firstValue(source, [
    'conversationSummary',
    'summary',
    'extractedData.summary',
    'conversation',
  ]))
  const problem = text(firstValue(source, ['problem', 'extractedData.problem']))
  const goal = text(firstValue(source, ['goal', 'extractedData.goal']))
  const currentProcess = text(firstValue(source, ['currentProcess', 'extractedData.currentProcess']))
  const businessType = text(firstValue(source, ['businessType', 'extractedData.businessType', 'client.scope', 'scope']))
  const tags = [
    serviceName,
    recommendedTier,
    ...stringArray(service?.tags),
  ].filter(tag => tag !== FALLBACK).slice(0, 6)

  const fallbackMetrics: [Metric, Metric, Metric] = [
    { value: recommendedTier, label: 'tier consigliato' },
    { value: text(firstValue(source, ['urgency', 'extractedData.urgency'])), label: 'urgenza dichiarata' },
    { value: text(firstValue(source, ['budget', 'extractedData.budget'])), label: 'budget indicato' },
  ]

  return validateReportData({
    meta: {
      title: `Report K-BOT - ${serviceName}`,
      subtitle: service?.shortDescription || FALLBACK,
      category: 'Diagnosi operativa K2-AI',
      code: `K2AI-KBOT-${normalizeServiceId(service?.id || DEFAULT_SERVICE_ID)}`,
      date: dateLabel(firstValue(source, ['updated_at', 'created_at'])),
      version: '1.0',
    },
    client: {
      name: text(firstValue(source, ['client.name', 'companyName', 'extractedData.companyName', 'businessType', 'extractedData.businessType'])),
      scope: businessType,
    },
    sections: {
      cover: true,
      executiveSummary: true,
      context: true,
      problem: true,
      analysis: true,
      opportunity: true,
      solution: true,
      roadmap: true,
      priorities: true,
      impact: true,
      recommendedPlan: true,
      nextSteps: true,
      disclaimer: true,
    },
    executiveSummary: {
      title: 'Executive summary',
      text: conversationSummary,
      metrics: mapMetrics(source, fallbackMetrics),
      operationalTakeaway: text(firstValue(source, ['nextStep', 'extractedData.nextStep', 'goal', 'extractedData.goal'])),
    },
    context: {
      title: 'Contesto aziendale',
      currentScenario: currentProcess,
      reportObjective: goal,
      tags: fallbackList(tags, FALLBACK),
    },
    problem: {
      title: 'Problema rilevato',
      main: problem,
      rows: mapProblemRows(source),
    },
    analysis: {
      title: 'Analisi operativa',
      intro: conversationSummary,
      cards: mapAnalysisCards(source),
      table: mapAnalysisTable(source),
    },
    opportunity: {
      title: 'Opportunita AI',
      intro: service?.shortDescription || FALLBACK,
      items: mapOpportunities(source, service?.useCases || []),
    },
    solution: {
      title: 'Soluzione proposta',
      description: service?.shortDescription || FALLBACK,
      components: fallbackList(stringArray(firstValue(source, ['components', 'solution.components', 'extractedData.components'])), service?.target || FALLBACK),
      expectedResult: goal,
    },
    roadmap: {
      title: 'Roadmap di implementazione',
      items: mapRoadmap(source),
    },
    priorities: {
      title: 'Priorita operative',
      items: mapPriorities(source),
    },
    impact: {
      title: 'Impatto atteso',
      metrics: mapMetrics(source, fallbackMetrics),
      rows: mapImpactRows(source),
    },
    recommendedPlan: {
      title: `Piano consigliato - ${recommendedTier}`,
      summary: text(firstValue(source, ['nextStep', 'extractedData.nextStep']) || service?.target),
      steps: mapPlanSteps(source),
    },
    nextSteps: {
      title: 'Next step',
      immediateActions: fallbackList(stringArray(firstValue(source, ['immediateActions', 'nextSteps.immediateActions', 'extractedData.immediateActions'])), text(firstValue(source, ['nextStep', 'extractedData.nextStep']))),
      requiredDecisions: fallbackList(stringArray(firstValue(source, ['requiredDecisions', 'nextSteps.requiredDecisions', 'extractedData.requiredDecisions'])), 'Confermare perimetro, dati disponibili e responsabile operativo.'),
      suggestedNextStep: text(firstValue(source, ['nextStep', 'extractedData.nextStep'])),
    },
    disclaimer: {
      title: 'Disclaimer',
      text: 'Questo report e generato tramite mapping deterministico dei dati raccolti da K-BOT. Le informazioni mancanti sono indicate come "Dato non fornito" e devono essere validate prima di qualsiasi implementazione.',
    },
  })
}
