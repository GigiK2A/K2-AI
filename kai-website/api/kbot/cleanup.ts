import { createSupabaseAdminClient, sendJson } from './_shared'
import { getSystemEnvVar } from '../../lib/env/system'

const CLEANUP_SECRET = 'x-cleanup-key'
const SESSION_TTL_DAYS = 30
const PAID_SESSION_TTL_DAYS = 90

export default async function handler(req: any, res: any) {
  // Accetta GET (Vercel cron) e POST (chiamata manuale)
  if (req.method !== 'GET' && req.method !== 'POST') {
    res.setHeader('Allow', 'GET, POST')
    return sendJson(res, 405, { error: 'Method not allowed' })
  }

  // Verifica chiave segreta (Vercel cron passa Authorization: Bearer <secret>)
  // Accetta CLEANUP_SECRET_KEY (manuale) o CRON_SECRET (Vercel cron built-in)
  const cleanupKey = getSystemEnvVar('CLEANUP_SECRET_KEY')
  const cronSecret = process.env.CRON_SECRET
  const acceptedKey = cleanupKey || cronSecret
  if (acceptedKey) {
    const authHeader = (req.headers?.['authorization'] || '') as string
    const incomingKey = authHeader.replace(/^Bearer\s+/i, '').trim() ||
      (req.headers?.[CLEANUP_SECRET] || '') as string

    if (incomingKey !== acceptedKey) {
      return sendJson(res, 401, { error: 'Unauthorized' })
    }
  }

  try {
    const supabase = createSupabaseAdminClient()
    const cutoffDate = new Date()
    cutoffDate.setDate(cutoffDate.getDate() - SESSION_TTL_DAYS)
    const cutoffIso = cutoffDate.toISOString()

    // Recupera sessioni vecchie da eliminare
    const { data: oldSessions, error: fetchError } = await supabase
      .from('kbot_sessions')
      .select('id, collected_data')
      .lt('created_at', cutoffIso)
      .in('status', ['active'])
      .limit(100)

    if (fetchError) {
      return sendJson(res, 500, { error: `Fetch sessioni fallito: ${fetchError.message}` })
    }

    if (!oldSessions || oldSessions.length === 0) {
      return sendJson(res, 200, { deleted: 0, message: 'Nessuna sessione da eliminare.' })
    }

    const sessionIds = oldSessions.map(s => s.id)

    // Elimina file Supabase Storage per queste sessioni
    let storageDeletedCount = 0
    for (const session of oldSessions) {
      const uploadedFiles = Array.isArray(session.collected_data?.uploaded_files)
        ? session.collected_data.uploaded_files
        : []

      const paths = uploadedFiles.map((f: any) => f.path).filter(Boolean)

      if (paths.length > 0) {
        const { error: storageError } = await supabase.storage
          .from('kbot-uploads')
          .remove(paths)

        if (storageError) {
          console.warn(`Cleanup: errore eliminazione file sessione ${session.id}:`, storageError.message)
        } else {
          storageDeletedCount += paths.length
        }
      }
    }

    // Elimina le sessioni dal DB
    const { error: deleteError } = await supabase
      .from('kbot_sessions')
      .delete()
      .in('id', sessionIds)

    if (deleteError) {
      return sendJson(res, 500, { error: `Eliminazione sessioni fallita: ${deleteError.message}` })
    }

    // Elimina sessioni paid vecchie (GDPR: rimozione dati dopo 90 giorni)
    const paidCutoff = new Date()
    paidCutoff.setDate(paidCutoff.getDate() - PAID_SESSION_TTL_DAYS)
    const paidCutoffIso = paidCutoff.toISOString()

    const { data: oldPaid } = await supabase
      .from('kbot_sessions')
      .select('id, collected_data')
      .lt('paid_at', paidCutoffIso)
      .in('status', ['paid', 'contacted', 'teaser_shown'])
      .limit(100)

    let deletedPaid = 0
    if (oldPaid && oldPaid.length > 0) {
      // Rimuovi file storage anche per sessioni paid
      for (const session of oldPaid) {
        const uploadedFiles = Array.isArray(session.collected_data?.uploaded_files)
          ? session.collected_data.uploaded_files
          : []
        const paths = uploadedFiles.map((f: any) => f.path).filter(Boolean)
        if (paths.length > 0) {
          await supabase.storage.from('kbot-uploads').remove(paths)
          storageDeletedCount += paths.length
        }
      }

      const paidIds = oldPaid.map(s => s.id)
      await supabase.from('kbot_sessions').delete().in('id', paidIds)
      deletedPaid = paidIds.length
    }

    console.log(`Cleanup: eliminate ${sessionIds.length} sessioni active, ${deletedPaid} sessioni paid, ${storageDeletedCount} file.`)
    return sendJson(res, 200, {
      deleted_active: sessionIds.length,
      deleted_paid: deletedPaid,
      deleted_files: storageDeletedCount,
      cutoff_active: cutoffIso,
      cutoff_paid: paidCutoffIso,
    })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return sendJson(res, 500, { error: message })
  }
}
