import { createAnthropicClient, createSupabaseAdminClient, ensurePost, parseJsonBody, sendJson } from './_shared'
import pdfParse from 'pdf-parse'
import { getSystemEnvVar } from '../../lib/env/system'

type UploadFileInput = {
  name: string
  type: string
  size: number
  base64: string
}

type UploadedMeta = {
  name: string
  type: string
  size: number
  path: string
  publicUrl: string
  extractedSummary?: string
  extractedText?: string
  extractionMethod?: 'text-decode' | 'pdf-parse' | 'claude-summary' | 'none'
}

function sanitizeFileName(name: string): string {
  return name.replace(/[^a-zA-Z0-9._-]/g, '_').slice(0, 120)
}

function decodePlainText(fileBuffer: Buffer): string {
  return fileBuffer
    .toString('utf-8')
    .replace(/\u0000/g, '')
    .replace(/\r\n/g, '\n')
    .trim()
}

function isPlainTextLike(mime: string, name: string): boolean {
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

function normalizeExtractedText(text: string, maxChars: number): string {
  return text
    .replace(/\u0000/g, ' ')
    .replace(/\r\n/g, '\n')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
    .slice(0, maxChars)
}

async function extractPdfText(fileBuffer: Buffer): Promise<string | undefined> {
  try {
    const parsed = await pdfParse(fileBuffer)
    const normalized = normalizeExtractedText(String(parsed?.text || ''), 30000)
    return normalized.length > 120 ? normalized : undefined
  } catch {
    return undefined
  }
}

async function summarizePdfWithClaude(fileBase64: string, fileName: string): Promise<string | undefined> {
  try {
    const anthropic = createAnthropicClient()
    const response = await anthropic.messages.create({
      model: 'claude-haiku-4-5',
      max_tokens: 700,
      messages: [
        {
          role: 'user',
          content: [
            {
              type: 'text',
              text:
                `Analizza il PDF allegato (${fileName}) e restituisci solo un riassunto operativo in italiano.\n` +
                `Formato obbligatorio:\n` +
                `- Tipo documento\n- Dati economici chiave trovati\n- Periodo di riferimento\n- Eventuali mancanze o incertezze\n` +
                `Massimo 12 righe, senza markdown complesso. Se un dato non è chiaro, scrivi "non leggibile".`,
            },
            {
              type: 'document',
              source: {
                type: 'base64',
                media_type: 'application/pdf',
                data: fileBase64,
              },
            } as any,
          ],
        } as any,
      ],
    })

    const text = response.content[0]?.type === 'text' ? response.content[0].text : ''
    return text?.trim() || undefined
  } catch {
    return undefined
  }
}

export default async function handler(req: any, res: any) {
  if (!ensurePost(req, res)) return

  try {
    const { session_id, files } = await parseJsonBody(req)
    if (!session_id || !Array.isArray(files) || files.length === 0) {
      return sendJson(res, 400, { error: 'session_id e files sono obbligatori' })
    }

    const supabase = createSupabaseAdminClient()
    const enableSlowPdfFallback =
      (getSystemEnvVar('KBOT_UPLOAD_PDF_FALLBACK', ['KBOT_UPLOAD_CLAUDE_FALLBACK']) || '')
        .toLowerCase() === 'true'
    const BUCKET = 'kbot-uploads'
    const out: UploadedMeta[] = []

    for (const f of files as UploadFileInput[]) {
      if (!f?.name || !f?.base64) continue
      const cleanName = sanitizeFileName(String(f.name))
      const raw = String(f.base64).replace(/^data:.*;base64,/, '')
      const fileBuffer = Buffer.from(raw, 'base64')
      const size = Number(f.size || fileBuffer.length)

      if (size > 3 * 1024 * 1024) {
        return sendJson(res, 413, { error: `File troppo grande: ${cleanName}. Max 3MB per file.` })
      }

      const path = `${session_id}/${Date.now()}-${cleanName}`
      let { error: uploadError } = await supabase.storage
        .from(BUCKET)
        .upload(path, fileBuffer, {
          contentType: f.type || 'application/octet-stream',
          upsert: true,
        })

      if (uploadError?.message?.toLowerCase().includes('bucket not found')) {
        await supabase.storage.createBucket(BUCKET, { public: true })
        const retry = await supabase.storage
          .from(BUCKET)
          .upload(path, fileBuffer, {
            contentType: f.type || 'application/octet-stream',
            upsert: true,
          })
        uploadError = retry.error
      }

      if (uploadError) {
        return sendJson(res, 500, { error: `Upload fallito per ${cleanName}: ${uploadError.message}` })
      }

      const { data } = supabase.storage.from(BUCKET).getPublicUrl(path)
      let extractedSummary: string | undefined
      let extractedText: string | undefined
      let extractionMethod: UploadedMeta['extractionMethod'] = 'none'
      const mime = f.type || 'application/octet-stream'
      if (isPlainTextLike(mime, cleanName)) {
        const decoded = decodePlainText(fileBuffer)
        extractedText = normalizeExtractedText(decoded, 12000)
        extractedSummary = extractedText.slice(0, 2200)
        extractionMethod = 'text-decode'
      } else if (mime === 'application/pdf' || cleanName.toLowerCase().endsWith('.pdf')) {
        extractedText = await extractPdfText(fileBuffer)
        if (extractedText) {
          extractedSummary = extractedText.slice(0, 2200)
          extractionMethod = 'pdf-parse'
        } else if (enableSlowPdfFallback) {
          extractedSummary = await summarizePdfWithClaude(raw, cleanName)
          extractionMethod = extractedSummary ? 'claude-summary' : 'none'
        }
      }

      if (!extractedSummary) {
        extractedSummary =
          'Nessun testo estraibile in modo affidabile da questo file. Per evitare errori numerici, usa questo allegato solo come contesto generale.'
      }

      out.push({
        name: cleanName,
        type: mime,
        size,
        path,
        publicUrl: data.publicUrl,
        extractedSummary,
        extractedText,
        extractionMethod,
      })
    }

    const { data: session } = await supabase
      .from('kbot_sessions')
      .select('collected_data')
      .eq('id', session_id)
      .single()

    const prevFiles = Array.isArray(session?.collected_data?.uploaded_files)
      ? session.collected_data.uploaded_files
      : []

    await supabase
      .from('kbot_sessions')
      .update({
        collected_data: {
          ...(session?.collected_data || {}),
          uploaded_files: [...prevFiles, ...out],
        },
        updated_at: new Date().toISOString(),
      })
      .eq('id', session_id)

    return sendJson(res, 200, { files: out })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return sendJson(res, 500, { error: message })
  }
}
