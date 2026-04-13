# Deploy GitHub -> Railway (K2-AI)

Questa repo contiene due servizi separati:

- `kai-website` (sito pubblico Vite statico)
- `ai-board` (FastAPI + scheduler + Telegram + Notion)

## 1) GitHub

1. Crea il repository su GitHub.
2. Carica il progetto completo.
3. Verifica che siano presenti:
   - `kai-website/Dockerfile`
   - `kai-website/railway.toml`
   - `ai-board/Dockerfile`
   - `ai-board/railway.toml`

## 2) Railway Project

Nel progetto Railway crea **2 servizi** dallo stesso repo.

### Servizio A: `k2-ai-website`

- Source repo: questo repository
- Root Directory: `kai-website`
- Builder: Dockerfile (automatico)
- Porta: gestita da `PORT`
- Healthcheck: `/`

Variabile ambiente richiesta:

```env
VITE_KAI_API_BASE_URL=https://board.tuodominio.it
```

### Servizio B: `k2-ai-board`

- Source repo: questo repository
- Root Directory: `ai-board`
- Builder: Dockerfile (automatico)
- Healthcheck: `/healthz`
- Replica: 1 (il board usa scheduler e bot Telegram nel processo)

Variabili ambiente minime:

```env
APP_ENV=production
LOG_LEVEL=INFO
PORT=8000

APP_ALLOWED_ORIGINS=https://tuodominio.it,https://www.tuodominio.it,https://board.tuodominio.it

BOARD_AUTH_ENABLED=true
BOARD_USERNAME=admin
BOARD_PASSWORD=<password-lunga>
BOARD_DATA_BACKEND=notion

NOTION_TOKEN=<token>
NOTION_PAGE_ID=<page-id>
NOTION_VERSION=2022-06-28

OPENAI_API_KEY=<openai>
ANTHROPIC_API_KEY=<anthropic-opzionale>
TAVILY_API_KEY=<tavily-opzionale>

TELEGRAM_BOT_TOKEN=<bot-token>
TELEGRAM_CHAT_ID=<chat-id>
TELEGRAM_MODE=webhook
TELEGRAM_WEBHOOK_URL=https://board.tuodominio.it
```

## 3) Dominio

Configura due host:

- `tuodominio.it` -> servizio `k2-ai-website`
- `board.tuodominio.it` -> servizio `k2-ai-board`

## 4) Go-live check (10 minuti)

1. `https://board.tuodominio.it/healthz` risponde `ok`.
2. Dal sito invia un form contatti test.
3. Verifica in Notion:
   - nuovo record in `Clienti`
   - nuova `Commessa`
   - nuovo `Pipeline Lead`
   - nuovo `Task`
   - sottopagina cliente con messaggio completo.
4. Verifica Telegram: notifica con formattazione (grassetto/corsivo) corretta.

## Opzionale (legacy)

Solo se vuoi usare login/account board via `/login` e `/admin`, aggiungi anche:

```env
SUPABASE_URL=<supabase-url>
SUPABASE_KEY=<supabase-anon>
SUPABASE_SERVICE_KEY=<supabase-service-role>
```

## 5) Nota sicurezza

Il token Notion è stato condiviso in chat durante i test: rigeneralo prima del deploy e aggiorna Railway.
