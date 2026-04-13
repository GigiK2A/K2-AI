# AI Board deploy

Il board non va trattato come una function serverless: contiene FastAPI, scheduler APScheduler, Telegram bot e chiamate LLM. Serve un servizio container always-on con una sola replica, almeno nella prima fase.

## Scelta consigliata

Usare un host container con Dockerfile, per esempio Railway, Render, Fly.io o un VPS. Il sito pubblico può restare su Vercel, mentre il board espone un dominio separato, per esempio:

- sito: `https://k-ai.it`
- board/API: `https://board.k-ai.it`

Vercel è adatto al frontend statico, ma non è il target giusto per questo processo long-running: il board ha scheduler e Telegram attivi in memoria.

Riferimenti utili:

- Railway: https://docs.railway.com/deploy/dockerfiles
- Fly.io: https://fly.io/docs/languages-and-frameworks/dockerfile/

## Variabili ambiente

Impostare queste variabili nel pannello dell'host:

```env
APP_ENV=production
PORT=8000
LOG_LEVEL=INFO

APP_ALLOWED_ORIGINS=https://k-ai.it,https://www.k-ai.it,https://board.k-ai.it

BOARD_AUTH_ENABLED=true
BOARD_USERNAME=admin
BOARD_PASSWORD=una-password-lunga-generata
BOARD_AUTH_REALM=AI Board
BOARD_SESSION_HOURS=12

BOARD_DATA_BACKEND=notion
NOTION_TOKEN=secret_xxx
NOTION_PAGE_ID=5c439dd1231642828b71cc43c52d4fa9
NOTION_VERSION=2022-06-28

ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...

TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
TELEGRAM_MODE=webhook
TELEGRAM_WEBHOOK_URL=https://board.k-ai.it

SCHEDULER_WEEKLY_PLAN_CRON=0 8 * * 1
SCHEDULER_DAILY_BRIEF_CRON=0 8 * * *
SCHEDULER_KPI_UPDATE_CRON=0 18 * * *
```

Note:

- L'host spesso imposta `PORT` automaticamente. Il board ora lo legge e lo preferisce ad `APP_PORT`.
- In produzione `APP_ENV=production` evita il tentativo locale di liberare porte con `lsof`.
- `BOARD_AUTH_ENABLED=true` abilita il login del software board. `BOARD_USERNAME` e `BOARD_PASSWORD` restano credenziali di emergenza per creare il primo account admin.
- `BOARD_DATA_BACKEND=notion` usa Notion come database operativo del board per Lavori/Task, Pipeline, Approvazioni, Log AI e Memoria/Decisioni. Il token deve essere rigenerato se è stato condiviso in chat o in altri canali.
- L'integrazione Notion deve essere aggiunta alla pagina `K-AI Operativo` con `Share` / `Add connections`, altrimenti le API rispondono senza permessi.
- In modalità Notion-only, Supabase non è più richiesto all'avvio.
- Supabase resta opzionale solo per feature legacy (login/accounts `/login` e `/admin`).
- `TELEGRAM_MODE=webhook` è preferibile al polling in hosting.
- Con scheduler in memoria tenere una sola replica. Se servono più repliche, separare web e worker/scheduler.

## Build e start

Il Dockerfile è nella root di `ai-board`:

```bash
docker build -t ai-board .
docker run --env-file .env -p 8000:8000 ai-board
```

Healthcheck:

```bash
curl http://localhost:8000/healthz
```

## Migrazioni database (solo se usi Supabase legacy)

Applicare su Supabase solo se vuoi usare login/account legacy:

```text
db/migrations/001_initial.sql
db/migrations/002_projects.sql
db/migrations/003_agent_logs_archive.sql
db/migrations/004_board_accounts.sql
```

## Collegamento con il sito

Nel sito pubblico impostare:

```env
VITE_KAI_API_BASE_URL=https://board.k-ai.it
```

Poi fare rebuild del sito. In locale Vite usa il proxy `/api`, ma in produzione il bundle deve sapere dove raggiungere il board.

## Checklist pre-produzione

- Dominio `board.k-ai.it` puntato al servizio container.
- HTTPS attivo sul dominio del board.
- `APP_ALLOWED_ORIGINS` include solo domini reali del sito.
- `BOARD_AUTH_ENABLED=true` e `BOARD_PASSWORD` lunga impostata nel pannello hosting.
- Primo accesso: usa Basic Auth di emergenza con `BOARD_USERNAME` + `BOARD_PASSWORD`.
- Verifica Notion: invia un form test dal sito e controlla che compaiano una voce in `Pipeline Lead`, una in `Task` e una in `Log AI`.
- Telegram webhook configurato e raggiungibile su `https://board.k-ai.it/webhook`.
- Una sola replica finché scheduler e Telegram restano nello stesso processo.
- Log level `INFO` in produzione.
