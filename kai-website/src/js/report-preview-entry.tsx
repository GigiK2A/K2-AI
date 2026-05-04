import React from 'react'
import { createRoot } from 'react-dom/client'
import { K2AIReportTemplate } from '../../components/report/K2AIReportTemplate'
import { mockReportData } from '../data/mockReportData'
import { generateReportData } from '../../lib/kbot/report-data'

type BoardMockReport = {
  id: string
  createdAtLabel: string
  client: string
  service: string
  serviceId: string
  tier: string
  statusLabel: string
  summary: string
  problem: string
  currentProcess: string
}

const BOARD_REPORT_MOCKS: Record<string, BoardMockReport> = {
  'KAI-RPT-2026-001': {
    id: 'KAI-RPT-2026-001',
    createdAtLabel: '03/05/2026 09:12',
    client: 'Alfa Componenti S.r.l.',
    service: 'Agenti AI Email & CRM',
    serviceId: 'P01',
    tier: 'WEB',
    statusLabel: 'Pronto',
    summary: 'Opportunita concreta per automatizzare follow-up commerciali, aggiornamento CRM e sintesi operative post contatto senza togliere controllo al team vendita.',
    problem: 'I follow-up arrivano in ritardo, il CRM non viene aggiornato con continuita e la pipeline commerciale perde affidabilita.',
    currentProcess: 'Il team usa email, note manuali e CRM, ma il passaggio da conversazione a prossima azione richiede ancora molto lavoro ripetitivo.',
  },
  'KAI-RPT-2026-002': {
    id: 'KAI-RPT-2026-002',
    createdAtLabel: '02/05/2026 16:40',
    client: 'Studio Rinaldi',
    service: 'Automazioni Amministrative',
    serviceId: 'P02',
    tier: 'HOST',
    statusLabel: 'Inviato',
    summary: 'L area amministrativa puo ridurre errori e tempi di lavorazione automatizzando raccolta documenti, classificazione pratiche e passaggi ripetitivi di back office.',
    problem: 'Le pratiche vengono smistate e controllate manualmente con rischio di colli di bottiglia e poco tracciamento delle priorita.',
    currentProcess: 'Documenti, email e task interni vengono gestiti su piu strumenti, con molti passaggi manuali tra ricezione, verifica e lavorazione.',
  },
  'KAI-RPT-2026-003': {
    id: 'KAI-RPT-2026-003',
    createdAtLabel: '01/05/2026 11:08',
    client: 'Nord Est Hospitality',
    service: 'AI Hospitality & Revenue',
    serviceId: 'P20',
    tier: 'HOST',
    statusLabel: 'Pronto',
    summary: 'C e spazio per migliorare tempi di risposta, pricing operativo e coordinamento tra richieste ospiti e attivita di struttura.',
    problem: 'Le richieste arrivano da canali diversi e la gestione manuale rende difficile mantenere allineati disponibilita, risposte e priorita revenue.',
    currentProcess: 'Prenotazioni, email e messaggi vengono seguiti dal team con forte dipendenza dalle persone e poca orchestrazione centralizzata.',
  },
  'KAI-RPT-2026-004': {
    id: 'KAI-RPT-2026-004',
    createdAtLabel: '30/04/2026 14:25',
    client: 'Meccanica Umbra',
    service: 'Integrazione Gestionali & ERP',
    serviceId: 'P10',
    tier: 'STUDIO',
    statusLabel: 'Bozza',
    summary: 'Il valore principale sta nell allineare dati e flussi tra gestionale, reparti e attivita ricorrenti oggi replicate a mano.',
    problem: 'Ordini, avanzamenti e dati operativi passano tra sistemi non integrati, con doppie imputazioni e poca visibilita sullo stato reale.',
    currentProcess: 'ERP, fogli di lavoro e comunicazioni interne convivono senza un flusso unico, costringendo il team a ricontrolli continui.',
  },
  'KAI-RPT-2026-005': {
    id: 'KAI-RPT-2026-005',
    createdAtLabel: '29/04/2026 10:16',
    client: 'Lex & Partners',
    service: 'AI Legale & Contratti',
    serviceId: 'P03',
    tier: 'WEB',
    statusLabel: 'Pronto',
    summary: 'Le prime automazioni possono aiutare nel pre-screening documentale, nella preparazione bozze e nella sintesi di clausole ricorrenti.',
    problem: 'L analisi preliminare dei documenti richiede tempo e viene svolta con processi poco standardizzati tra studio, pratiche e clienti.',
    currentProcess: 'Contratti, allegati e note vengono letti e sintetizzati manualmente, con molto tempo speso su attivita ripetitive di confronto e riepilogo.',
  },
}

function parseCreatedAt(label: string): string {
  const match = label.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}):(\d{2}))?$/)
  if (!match) return new Date().toISOString()
  const [, day, month, year, hour = '00', minute = '00'] = match
  return new Date(`${year}-${month}-${day}T${hour}:${minute}:00`).toISOString()
}

function buildReportDataFromMockId(mockReportId: string) {
  const mock = BOARD_REPORT_MOCKS[mockReportId.trim().toUpperCase()]
  if (!mock) return mockReportData

  const reportData = generateReportData({
    id: mock.id,
    serviceId: mock.serviceId,
    service_id: mock.serviceId,
    selectedService: {
      id: mock.serviceId,
      name: mock.service,
      shortDescription: mock.summary,
      recommendedTier: mock.tier,
    },
    recommendedTier: mock.tier,
    recommended_tier: mock.tier,
    companyName: mock.client,
    businessType: mock.client,
    summary: mock.summary,
    conversationSummary: mock.summary,
    problem: mock.problem,
    currentProcess: mock.currentProcess,
    created_at: parseCreatedAt(mock.createdAtLabel),
    updated_at: parseCreatedAt(mock.createdAtLabel),
  })

  reportData.meta.code = mock.id
  reportData.meta.date = mock.createdAtLabel.split(' ')[0] || reportData.meta.date
  reportData.client.name = mock.client
  reportData.client.scope = mock.currentProcess
  reportData.executiveSummary.text = mock.summary
  reportData.context.currentScenario = mock.currentProcess
  reportData.problem.main = mock.problem
  reportData.solution.expectedResult = `Output mock ${mock.statusLabel} per anteprima board.`
  return reportData
}

function resolvePreviewReportData() {
  const params = new URLSearchParams(window.location.search)
  const mockReportId = params.get('mock_report_id')
  if (mockReportId) return buildReportDataFromMockId(mockReportId)
  return mockReportData
}

const rootEl = document.getElementById('report-preview-root')

if (rootEl) {
  createRoot(rootEl).render(
    <React.StrictMode>
      <K2AIReportTemplate reportData={resolvePreviewReportData()} />
    </React.StrictMode>
  )
}
