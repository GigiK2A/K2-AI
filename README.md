# K2-AI Workspace

Contenitore unico per il sito pubblico e il software operativo.

## Struttura

- `kai-website` -> sito pubblico K2-AI
- `ai-board` -> software operativo AI Board

## Logica

- Il sito pubblico resta un frontend separato e deployabile in autonomia.
- AI Board resta il backend operativo, con dashboard, pipeline, memoria e agenti.
- Il form contatti del sito invia ora le richieste a `POST /api/intake/contact` su AI Board.
- Anche K-BOT invia i turni di diagnosi a `POST /api/intake/kbot-chat` su AI Board.

## Locale

- Sito: `cd kai-website && npm run dev`
- Software: `cd ai-board && uv sync && source .venv/bin/activate && python main.py`

## Deploy

- Guida completa GitHub -> Railway: `DEPLOY_GITHUB_RAILWAY.md`
- Publish sicuro del sito via GitHub: `./scripts/deploy-website-via-git.sh`
- In modalità Notion-only Supabase non è richiesto per avvio e intake pubblico.
