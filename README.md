# K2-AI Workspace

Contenitore unico per il sito pubblico e il software operativo.

## Struttura

- `kai-website` -> sito pubblico K2-AI
- `apps/board` -> **K2-AI AIOS**, il sistema operativo del board di agenti (ex "AI Board", ora dismesso)

## Logica

- Il sito pubblico resta un frontend separato e deployabile in autonomia.
- L'AIOS è il backend operativo: cockpit, agenti per dominio, approvazioni, autonomia e audit.
- Il form contatti del sito e K-BOT inviano le richieste agli endpoint di intake dell'AIOS.

## Locale

- Sito: `cd kai-website && npm run dev`
- AIOS: `cd apps/board && pip install -e ".[dev]" && python serve_cockpit.py`

## Deploy

- Guida completa GitHub -> Railway: `DEPLOY_GITHUB_RAILWAY.md`
- Publish sicuro del sito via GitHub: `./scripts/deploy-website-via-git.sh`
- Servizio Railway `k2-board`: Root Directory = `apps/board`, builder = Dockerfile.
