import { ensurePost, parseJsonBody } from '../kbot/_shared'
import { validateReportData } from '../../lib/kbot/report-data'

function pdfFileName(reportData: any): string {
  const rawCode = String(reportData?.meta?.code || 'report-kbot')
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return `${rawCode || 'report-kbot'}.pdf`
}

export async function generatePDF(reportData: unknown): Promise<Buffer> {
  const pdfRuntime = (await import('../../lib/report/pdf-generator.js')) as any
  const generatePdfFn = pdfRuntime.generatePDF || pdfRuntime.default?.generatePDF
  if (typeof generatePdfFn !== 'function') {
    throw new Error('generatePDF non disponibile')
  }

  return generatePdfFn(validateReportData(reportData))
}

export default async function handler(req: any, res: any) {
  if (!ensurePost(req, res)) return

  try {
    const body = await parseJsonBody(req)
    const reportData = validateReportData(body.reportData || body.report_data || body)
    const pdfBuffer = await generatePDF(reportData)

    res.statusCode = 200
    res.setHeader('Content-Type', 'application/pdf')
    res.setHeader('Content-Disposition', `attachment; filename="${pdfFileName(reportData)}"`)
    res.setHeader('Cache-Control', 'no-store')
    res.end(pdfBuffer)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    res.statusCode = 500
    res.setHeader('Content-Type', 'application/json; charset=utf-8')
    res.end(JSON.stringify({ error: message }))
  }
}
