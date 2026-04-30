import React from 'react'
import type { ReportData } from '../../src/types/report'
import { ReportChecklist } from './ReportChecklist'
import { ReportCover } from './ReportCover'
import { ReportFooter } from './ReportFooter'
import { ReportMetricCard } from './ReportMetricCard'
import { ReportPriorityBadge } from './ReportPriorityBadge'
import { ReportRoadmap } from './ReportRoadmap'
import { ReportSection } from './ReportSection'
import { ReportTable } from './ReportTable'

interface Props {
  reportData: ReportData
}

export function K2AIReportTemplate({ reportData }: Props) {
  const { sections } = reportData

  return (
    <div className="k2ai-report">
      <main className="document">
        {sections.cover && <ReportCover reportData={reportData} />}

        {sections.executiveSummary && (
          <ReportSection title={reportData.executiveSummary.title} eyebrow="01">
            <p className="lead-copy">{reportData.executiveSummary.text || 'Dato non fornito'}</p>
            <div className="metric-grid">
              {reportData.executiveSummary.metrics.map((metric, index) => (
                <ReportMetricCard metric={metric} key={`${metric.label}-${index}`} />
              ))}
            </div>
            <div className="takeaway">
              <span>Takeaway operativo</span>
              <p>{reportData.executiveSummary.operationalTakeaway || 'Dato non fornito'}</p>
            </div>
          </ReportSection>
        )}

        {sections.context && (
          <ReportSection title={reportData.context.title} eyebrow="02">
            <div className="two-column">
              <div>
                <h3>Scenario attuale</h3>
                <p>{reportData.context.currentScenario || 'Dato non fornito'}</p>
              </div>
              <div>
                <h3>Obiettivo del report</h3>
                <p>{reportData.context.reportObjective || 'Dato non fornito'}</p>
              </div>
            </div>
            <div className="tag-list">
              {reportData.context.tags.length > 0
                ? reportData.context.tags.map(tag => <span key={tag}>{tag || 'Dato non fornito'}</span>)
                : <span>Dato non fornito</span>}
            </div>
          </ReportSection>
        )}

        {sections.problem && (
          <ReportSection title={reportData.problem.title} eyebrow="03">
            <p className="lead-copy">{reportData.problem.main || 'Dato non fornito'}</p>
            <ReportTable
              rows={reportData.problem.rows}
              columns={[
                { key: 'area', label: 'Area' },
                { key: 'criticalIssue', label: 'Criticita' },
                { key: 'effect', label: 'Effetto' },
                {
                  key: 'priority',
                  label: 'Priorita',
                  render: row => (
                    <ReportPriorityBadge level={row.priority} variant={row.priorityClass} />
                  ),
                },
              ]}
            />
          </ReportSection>
        )}

        {sections.analysis && (
          <ReportSection title={reportData.analysis.title} eyebrow="04">
            <p className="lead-copy">{reportData.analysis.intro || 'Dato non fornito'}</p>
            <div className="card-grid">
              {reportData.analysis.cards.length > 0
                ? reportData.analysis.cards.map((card, index) => (
                    <article className="card analysis-card" key={`${card.title}-${index}`}>
                      <h3>{card.title || 'Dato non fornito'}</h3>
                      <p>{card.description || 'Dato non fornito'}</p>
                    </article>
                  ))
                : <p className="empty-state">Dato non fornito</p>}
            </div>
            <ReportTable
              rows={reportData.analysis.table}
              columns={[
                { key: 'parameter', label: 'Parametro' },
                { key: 'detectedStatus', label: 'Stato rilevato' },
                { key: 'evaluation', label: 'Valutazione' },
                { key: 'note', label: 'Note' },
              ]}
            />
          </ReportSection>
        )}

        {sections.opportunity && (
          <ReportSection title={reportData.opportunity.title} eyebrow="05">
            <p className="lead-copy">{reportData.opportunity.intro || 'Dato non fornito'}</p>
            <div className="opportunity-grid">
              {reportData.opportunity.items.length > 0
                ? reportData.opportunity.items.map((item, index) => (
                    <article className="opportunity-item" key={`${item.title}-${index}`}>
                      <h3>{item.title || 'Dato non fornito'}</h3>
                      <p>{item.description || 'Dato non fornito'}</p>
                      <dl>
                        <div>
                          <dt>Impatto</dt>
                          <dd>{item.impact || 'Dato non fornito'}</dd>
                        </div>
                        <div>
                          <dt>Effort</dt>
                          <dd>{item.effort || 'Dato non fornito'}</dd>
                        </div>
                      </dl>
                    </article>
                  ))
                : <p className="empty-state">Dato non fornito</p>}
            </div>
          </ReportSection>
        )}

        {sections.solution && (
          <ReportSection title={reportData.solution.title} eyebrow="06">
            <p className="lead-copy">{reportData.solution.description || 'Dato non fornito'}</p>
            <ReportChecklist items={reportData.solution.components} />
            <div className="takeaway">
              <span>Risultato atteso</span>
              <p>{reportData.solution.expectedResult || 'Dato non fornito'}</p>
            </div>
          </ReportSection>
        )}

        {sections.roadmap && (
          <ReportSection title={reportData.roadmap.title} eyebrow="07">
            <ReportRoadmap items={reportData.roadmap.items} />
          </ReportSection>
        )}

        {sections.priorities && (
          <ReportSection title={reportData.priorities.title} eyebrow="08">
            <div className="priority-list">
              {reportData.priorities.items.length > 0
                ? reportData.priorities.items.map((item, index) => (
                    <article className="priority-item" key={`${item.action}-${index}`}>
                      <ReportPriorityBadge level={item.priorityLevel} variant={item.priorityClass} />
                      <h3>{item.action || 'Dato non fornito'}</h3>
                      <p>{item.reason || 'Dato non fornito'}</p>
                      <div className="priority-meta">
                        <span>{item.impact || 'Dato non fornito'}</span>
                        <span>{item.timing || 'Dato non fornito'}</span>
                      </div>
                    </article>
                  ))
                : <p className="empty-state">Dato non fornito</p>}
            </div>
          </ReportSection>
        )}

        {sections.impact && (
          <ReportSection title={reportData.impact.title} eyebrow="09">
            <div className="metric-grid">
              {reportData.impact.metrics.map((metric, index) => (
                <ReportMetricCard metric={metric} key={`${metric.label}-${index}`} />
              ))}
            </div>
            <ReportTable
              rows={reportData.impact.rows}
              columns={[
                { key: 'dimension', label: 'Dimensione' },
                { key: 'expectedImpact', label: 'Impatto atteso' },
                { key: 'indicator', label: 'Indicatore' },
              ]}
            />
          </ReportSection>
        )}

        {sections.recommendedPlan && (
          <ReportSection title={reportData.recommendedPlan.title} eyebrow="10">
            <p className="lead-copy">{reportData.recommendedPlan.summary || 'Dato non fornito'}</p>
            <ReportTable
              rows={reportData.recommendedPlan.steps}
              columns={[
                { key: 'step', label: 'Step' },
                { key: 'activity', label: 'Attivita' },
                { key: 'output', label: 'Output' },
                { key: 'owner', label: 'Owner' },
              ]}
            />
          </ReportSection>
        )}

        {sections.nextSteps && (
          <ReportSection title={reportData.nextSteps.title} eyebrow="11">
            <div className="two-column">
              <div>
                <h3>Azioni immediate</h3>
                <ReportChecklist items={reportData.nextSteps.immediateActions} />
              </div>
              <div>
                <h3>Decisioni richieste</h3>
                <ReportChecklist items={reportData.nextSteps.requiredDecisions} />
              </div>
            </div>
            <div className="next-step-box">
              <span>Prossimo passo suggerito</span>
              <p>{reportData.nextSteps.suggestedNextStep || 'Dato non fornito'}</p>
            </div>
          </ReportSection>
        )}

        {sections.disclaimer && (
          <ReportSection title={reportData.disclaimer.title} eyebrow="12" className="disclaimer-section">
            <p>{reportData.disclaimer.text || 'Dato non fornito'}</p>
          </ReportSection>
        )}

        <ReportFooter reportData={reportData} />
      </main>
    </div>
  )
}
