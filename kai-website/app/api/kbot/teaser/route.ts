import { NextRequest, NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'
import { createClient } from '@/lib/supabase/server'
import { getAnthropicApiKey } from '@/lib/env/system'
import { loadSkillBundle } from '@/lib/skills/loader'
import { SECTOR_BUNDLES, SECTOR_LABELS } from '@/lib/skills/sectors.config'

function stripPreciseNumbers(text: string): string {
  return String(text || '')
    .replace(/€\s*\d[\d.,]*/g, '€...')
    .replace(/\b\d[\d.,]*\s*%/g, '...%')
    .replace(/\b\d[\d.,]*\b/g, '...')
    .replace(/\s{2,}/g, ' ')
    .trim()
}

function sanitizeTeaser(teaser: any, sector: string, skills: string[]) {
  const signals = Array.isArray(teaser?.segnali) ? teaser.segnali.slice(0, 3) : []
  return {
    settore: teaser?.settore || sector,
    skill_attive: Array.isArray(teaser?.skill_attive) && teaser.skill_attive.length > 0
      ? teaser.skill_attive
      : skills,
    segnali: signals.map((signal: any) => {
      const previewRaw = stripPreciseNumbers(String(signal?.anteprima_analisi || 'Approfondimento disponibile nel report completo...'))
      const preview = previewRaw.endsWith('...') ? previewRaw : `${previewRaw.replace(/[.!?]+$/, '')}...`
      return {
        priorita: ['critica', 'rilevante', 'da_monitorare'].includes(String(signal?.priorita))
          ? signal.priorita
          : 'rilevante',
        titolo: String(signal?.titolo || 'Segnale operativo').slice(0, 80),
        sintesi: stripPreciseNumbers(String(signal?.sintesi || 'È emerso un segnale operativo da verificare con priorità.')).slice(0, 220),
        anteprima_analisi: preview.slice(0, 180),
      }
    }),
    hook_pdf: stripPreciseNumbers(String(teaser?.hook_pdf || 'Nel report completo trovi cause, impatti e priorità operative con piano di azione.')).slice(0, 240),
  }
}

export async function POST(req: NextRequest) {
  try {
    const client = new Anthropic({ apiKey: getAnthropicApiKey() })
    const { session_id } = await req.json()
    const supabase = createClient()

    const { data: session, error: sessionError } = await supabase
      .from('kbot_sessions')
      .select('*')
      .eq('id', session_id)
      .single()

    if (sessionError || !session) {
      return NextResponse.json({ error: 'Not found' }, { status: 404 })
    }

    const skillNames = SECTOR_BUNDLES[session.sector] || ['diagnosi-ai-operativa-pmi']
    const systemPrompt = loadSkillBundle(skillNames)

    const userPrompt = `
Produci il TEASER JSON per questo caso:

SETTORE: ${SECTOR_LABELS[session.sector] || session.sector}
DATI RACCOLTI: ${JSON.stringify(session.collected_data || {}, null, 2)}
CONVERSAZIONE: ${((session.messages || []) as Array<{ role: string; content: string }>)
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

    const response = await client.messages.create({
      model: 'claude-haiku-4-5',
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

      return NextResponse.json({ teaser })
    } catch {
      await supabase
        .from('kbot_sessions')
        .update({
          status: 'teaser_shown',
          collected_data: { ...(session.collected_data || {}), teaser: fallbackTeaser },
          updated_at: new Date().toISOString(),
        })
        .eq('id', session_id)

      return NextResponse.json({ teaser: fallbackTeaser, warning: 'teaser_fallback' })
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
