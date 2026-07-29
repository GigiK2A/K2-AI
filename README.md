# K2-AI Workspace

Contenitore unico per il sito pubblico e il software operativo.

## Struttura

- `kai-website` -> sito pubblico K2-AI
- `apps/board` -> AIOS, il software operativo del board

## Logica

- Il sito pubblico resta un frontend separato e deployabile in autonomia.
- AIOS (`apps/board`) è il backend operativo: cockpit, agenti di dominio, coda di
  approvazione e attuatore che esegue le azioni approvate su Supabase / n8n.
- Il form contatti del sito è servito da `kai-website/server.js`, che fa da proxy
  verso `api/intake/contact.ts` (Resend). Non dipende dal board.

> **Nota storica (lug 2026)**: `ai-board/` era un secondo board mai andato in
> produzione (tabelle Supabase sempre a zero righe). È stato rimosso; il board
> operativo è `apps/board`.

## Locale

- Sito: `cd kai-website && npm run dev`
- Board: `cd apps/board && python3 serve_cockpit.py` (test: `python3 -m pytest`)

## Deploy

- Guida completa GitHub -> Railway: `DEPLOY_GITHUB_RAILWAY.md`
- Publish sicuro del sito via GitHub: `./scripts/deploy-website-via-git.sh`
- In modalità Notion-only Supabase non è richiesto per avvio e intake pubblico.
