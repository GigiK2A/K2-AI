---
name: solution-blueprint
description: Framework per progettazione soluzioni AI: stack, roadmap 4 fasi, effort, rischi
---

# Solution Blueprint

## Stack preferito K2-AI

Per i clienti target (PMI italiane, 5-50 dipendenti):

- **Backend/logica**: Python
- **Workflow automation**: n8n o Make
- **Database**: Supabase (EU Frankfurt, GDPR-compliant)
- **Interfaccia utente finale**: Telegram o WhatsApp
- **LLM**: Claude API (Anthropic) — no OpenAI
- **Email**: Resend

Non promettere integrazioni con sistemi legacy complessi senza analisi preventiva.

## Roadmap standard 4 fasi

1. **Setup** — accessi, ambienti, integrazioni base, test connettività
2. **Implementazione** — sviluppo core del sistema, agenti, workflow
3. **Test & Validazione** — test con dati reali, correzioni, approvazione cliente
4. **Consegna & Handoff** — documentazione, training, go-live

## Effort e stime

- Stima sempre in **giorni/uomo**, non in ore — più onesto e comprensibile.
- Indica range realistico (min-max), non numero puntuale.
- Segnala dipendenze che possono ritardare (accessi sistemi, dati cliente, decisioni).

## Rischi

Per ogni progetto identifica max **3 rischi principali** con:
- Descrizione rischio
- Probabilità (Alta/Media/Bassa)
- Impatto (Alto/Medio/Basso)
- Mitigazione proposta

## Scope of work

Specifica sempre:
- ✅ Cosa è incluso
- ❌ Cosa NON è incluso
- ⚠️ Condizioni al contorno (prerequisiti, responsabilità cliente)

## Comunicazione

Ogni blueprint deve essere comprensibile dal cliente non tecnico.
Usa analogie quando necessario — mai gergo tecnico senza spiegazione.
