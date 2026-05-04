import { ensurePost, parseJsonBody } from '../kbot/_shared'
import { validateReportData } from '../../lib/kbot/report-data'

function docxFileName(reportData: any): string {
  const rawCode = String(reportData?.meta?.code || 'report-kbot')
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return `${rawCode || 'report-kbot'}.docx`
}

export async function generateDocx(reportData: unknown): Promise<Buffer> {
  const docxRuntime = (await import('../../lib/report/docx-generator.js')) as any
  const generateDocxFn = docxRuntime.generateDocx || docxRuntime.default?.generateDocx
  if (typeof generateDocxFn !== 'function') {
    throw new Error('generateDocx non disponibile')
  }

  return generateDocxFn(validateReportData(reportData))
}

export default async function handler(req: any, res: any) {
  if (!ensurePost(req, res)) return

  try {
    const body = await parseJsonBody(req)
    const reportData = validateReportData(body.reportData || body.report_data || body)
    const docxBuffer = await generateDocx(reportData)

    res.statusCode = 200
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    res.setHeader('Content-Disposition', `attachment; filename="${docxFileName(reportData)}"`)
    res.setHeader('Cache-Control', 'no-store')
    res.end(docxBuffer)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    res.statusCode = 500
    res.setHeader('Content-Type', 'application/json; charset=utf-8')
    res.end(JSON.stringify({ error: message }))
  }
}
