import {
  compactMessages,
  createAnthropicClient,
  createSupabaseAdminClient,
  ensurePost,
  MODEL,
  parseJsonBody,
  TEASER_SYSTEM_MAX_CHARS,
  resolveSectorLabel,
  resolveSkillNames,
  sendJson,
} from './_shared'
import { loadSkillBundle } from '../../lib/skills/loader'

function stripPreciseNumbers(text: string): string {
  return String(text || '')
    .replace(/€\s*\d[\d.,]*/g, '€...')
    .replace(/\b\d[\d.,]*\s*%/g, '...%')
    .replace(/\b\d[\d.,]*\b/g, '...')
    .replace(/\s{2,}/g, ' ')
    .trim()
}

function sanitizeTeaser(teaser: any, fallbackSector: string, fallbackSkills: string[]) {
  const safeSignals = Array.isArray(teaser?.segnali) ? teaser.segnali.slice(0, 3) : []

  return {
    settore: teaser?.settore || fallbackSector,
    skill_attive: Array.isArray(teaser?.skill_attive) && teaser.skill_attive.length > 0
      ? teaser.skill_attive
      : fallbackSkills,
    segnali: safeSignals.map((signal: any) => {
      const anteprima = stripPreciseNumbers(String(signal?.anteprima_analisi || 'Approfondimento disponibile nel report completo...'))
      const anteprimaFinal = anteprima.endsWith('...') ? anteprima : `${anteprima.replace(/[.!?]+$/, '')}...`
      return {
        priorita: ['critica', 'rilevante', 'da_monitorare'].includes(String(signal?.priorita))
          ? signal.priorita
          : 'rilevante',
        titolo: String(signal?.titolo || 'Segnale operativo').slice(0, 80),
        sintesi: stripPreciseNumbers(String(signal?.sintesi || 'È emerso un segnale operativo da verificare con priorità.')).slice(0, 220),
        anteprima_analisi: anteprimaFinal.slice(0, 180),
      }
    }),
    hook_pdf: stripPreciseNumbers(String(teaser?.hook_pdf || 'Nel report completo trovi cause, impatti e priorità operative con piano di azione.')).slice(0, 240),
  }
}

export default async function handler(req: any, res: any) {
  if (!ensurePost(req, res)) return

  try {
    const { session_id } = await parseJsonBody(req)
    const supabase = createSupabaseAdminClient()
    const anthropic = createAnthropicClient()

    const { data: session, error: sessionError } = await supabase
      .from('kbot_sessions')
      .select('*')
      .eq('id', session_id)
      .single()

    if (sessionError || !session) return sendJson(res, 404, { error: 'Not found' })

    // Rate limiting: il teaser non si rigenera se già presente
    if (session.collected_data?.teaser) {
      return sendJson(res, 200, { teaser: session.collected_data.teaser, cached: true })
    }

    const skillNames = resolveSkillNames(session.sector)
    const systemPrompt = loadSkillBundle(skillNames, {
      maxTotalChars: TEASER_SYSTEM_MAX_CHARS,
      maxPerSkillChars: 24000,
      includeReferences: true,
    })
    const compactConversation = compactMessages(
      ((session.messages || []) as Array<{ role: 'user' | 'assistant'; content: string }>),
      20,
      2200,
    )

    const userPrompt = `
Produci il TEASER JSON per questo caso:

SETTORE: ${resolveSectorLabel(session.sector)}
DATI RACCOLTI: ${JSON.stringify(session.collected_data || {}, null, 2)}
CONVERSAZIONE: ${compactConversation
  .map(m => `${m.role}: ${m.content}`)
  .join('\n')}

Vincoli teaser (obbligatori):
- Teaser incompleto, orientato alla conversione, NON risolutivo.
- Niente tabelle e niente markdown.
- Niente numeri specifici (percentuali, importi, KPI puntuali): usa solo segnali qualitativi.
- Massimo 3 segnali.

Produci SOLO il JSON del teaser come definito nella skill diagnosi-ai-operativa-pmi.
Niente altro - solo il JSON valido.
`

    const response = await anthropic.messages.create({
      model: MODEL,
      max_tokens: 1500,
      system: systemPrompt,
      messages: [{ role: 'user', content: userPrompt }],
    })

    const rawText = response.content[0]?.type === 'text' ? response.content[0].text : '{}'

    const fallbackTeaser = sanitizeTeaser(
      {
        settore: session.sector || 'pmi',
        skill_attive: skillNames,
        segnali: [
          {
            priorita: 'rilevante',
            titolo: 'Segnale operativo emerso',
            sintesi: 'Dai dati raccolti emerge una criticità operativa che richiede verifica strutturata.',
            anteprima_analisi: 'Nel report completo trovi cause, impatto e priorità di intervento...',
          },
        ],
        hook_pdf:
          'Nel report completo trovi valutazione tecnica, benchmark e piano operativo prioritizzato.',
      },
      session.sector || 'pmi',
      skillNames,
    )

    try {
      const parsedTeaser = JSON.parse(rawText.replace(/```json\n?|\n?```/g, '').trim())
      const teaser = sanitizeTeaser(parsedTeaser, session.sector || 'pmi', skillNames)

      await supabase
        .from('kbot_sessions')
        .update({
          status: 'teaser_shown',
          collected_data: { ...(session.collected_data || {}), teaser },
          updated_at: new Date().toISOString(),
        })
        .eq('id', session_id)

      return sendJson(res, 200, { teaser })
    } catch {
      await supabase
        .from('kbot_sessions')
        .update({
          status: 'teaser_shown',
          collected_data: { ...(session.collected_data || {}), teaser: fallbackTeaser },
          updated_at: new Date().toISOString(),
        })
        .eq('id', session_id)

      return sendJson(res, 200, { teaser: fallbackTeaser, warning: 'teaser_fallback' })
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return sendJson(res, 500, { error: message })
  }
}
