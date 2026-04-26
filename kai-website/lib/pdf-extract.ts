import { PDFParse } from 'pdf-parse'

export type ExtractPdfResult = {
  text?: string
  method: 'pdf-parse' | 'none'
}

export function normalizeExtractedText(text: string, maxChars: number): string {
  return text
    .replace(/\u0000/g, ' ')
    .replace(/\r\n/g, '\n')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
    .slice(0, maxChars)
}

export function decodePlainText(fileBuffer: Buffer, maxChars = 12000): string {
  return normalizeExtractedText(
    fileBuffer
      .toString('utf-8')
      .replace(/\u0000/g, '')
      .replace(/\r\n/g, '\n')
      .trim(),
    maxChars,
  )
}

export function isPlainTextLike(mime: string, name: string): boolean {
  const lower = name.toLowerCase()
  return (
    mime.startsWith('text/') ||
    lower.endsWith('.txt') ||
    lower.endsWith('.md') ||
    lower.endsWith('.csv') ||
    lower.endsWith('.json') ||
    lower.endsWith('.xml')
  )
}

export async function extractPdfText(fileBuffer: Buffer, maxChars = 30000): Promise<ExtractPdfResult> {
  const parser = new PDFParse({ data: fileBuffer })
  try {
    const parsed = await parser.getText()
    const normalized = normalizeExtractedText(String(parsed?.text || ''), maxChars)
    return normalized.length > 120
      ? { text: normalized, method: 'pdf-parse' }
      : { method: 'none' }
  } catch {
    return { method: 'none' }
  } finally {
    await parser.destroy().catch(() => undefined)
  }
}
