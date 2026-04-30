export type PriorityLevel = 'high' | 'medium' | 'low'

export interface Metric {
  value: string
  label: string
}

export interface ProblemRow {
  area: string
  criticalIssue: string
  effect: string
  priority: string
  priorityClass: PriorityLevel
}

export interface AnalysisCard {
  title: string
  description: string
}

export interface AnalysisTableRow {
  parameter: string
  detectedStatus: string
  evaluation: string
  note: string
}

export interface Opportunity {
  title: string
  description: string
  impact: string
  effort: string
}

export interface RoadmapItem {
  phaseTitle: string
  timeframe: string
  owner: string
  phaseDescription: string
}

export interface PriorityItem {
  priorityLevel: string
  priorityClass: PriorityLevel
  action: string
  reason: string
  impact: string
  timing: string
}

export interface ImpactRow {
  dimension: string
  expectedImpact: string
  indicator: string
}

export interface RecommendedPlanStep {
  step: string
  activity: string
  output: string
  owner: string
}

export interface ReportSectionVisibility {
  cover: boolean
  executiveSummary: boolean
  context: boolean
  problem: boolean
  analysis: boolean
  opportunity: boolean
  solution: boolean
  roadmap: boolean
  priorities: boolean
  impact: boolean
  recommendedPlan: boolean
  nextSteps: boolean
  disclaimer: boolean
}

export interface ReportMeta {
  title: string
  subtitle: string
  category: string
  code: string
  date: string
  version: string
}

export interface ClientInfo {
  name: string
  scope: string
}

export interface ExecutiveSummaryData {
  title: string
  text: string
  metrics: [Metric, Metric, Metric]
  operationalTakeaway: string
}

export interface ContextData {
  title: string
  currentScenario: string
  reportObjective: string
  tags: string[]
}

export interface ProblemData {
  title: string
  main: string
  rows: ProblemRow[]
}

export interface AnalysisData {
  title: string
  intro: string
  cards: AnalysisCard[]
  table: AnalysisTableRow[]
}

export interface OpportunityData {
  title: string
  intro: string
  items: Opportunity[]
}

export interface SolutionData {
  title: string
  description: string
  components: string[]
  expectedResult: string
}

export interface RoadmapData {
  title: string
  items: RoadmapItem[]
}

export interface PrioritiesData {
  title: string
  items: PriorityItem[]
}

export interface ImpactData {
  title: string
  metrics: [Metric, Metric, Metric]
  rows: ImpactRow[]
}

export interface RecommendedPlanData {
  title: string
  summary: string
  steps: RecommendedPlanStep[]
}

export interface NextStepsData {
  title: string
  immediateActions: string[]
  requiredDecisions: string[]
  suggestedNextStep: string
}

export interface DisclaimerData {
  title: string
  text: string
}

export interface ReportData {
  meta: ReportMeta
  client: ClientInfo
  sections: ReportSectionVisibility
  executiveSummary: ExecutiveSummaryData
  context: ContextData
  problem: ProblemData
  analysis: AnalysisData
  opportunity: OpportunityData
  solution: SolutionData
  roadmap: RoadmapData
  priorities: PrioritiesData
  impact: ImpactData
  recommendedPlan: RecommendedPlanData
  nextSteps: NextStepsData
  disclaimer: DisclaimerData
}
