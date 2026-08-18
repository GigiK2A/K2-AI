# Deploy GitHub -> Railway (K2-AI)

Questa repo contiene due servizi separati:

- `kai-website` (sito pubblico Vite statico)
- `apps/board` (AIOS: cockpit FastAPI + agenti + attuatore + Telegram, su Supabase)

> **Storico (lug 2026)**: esisteva un secondo board in `ai-board/` (FastAPI + Notion).
> Non è mai andato in produzione — le sue tabelle Supabase (`approvals`, `tasks`,
> `agent_logs`) sono rimaste a zero righe per tutta la sua vita — ed è stato rimosso.
> Il board vivo è **`apps/board`**. Se trovi documentazione che parla di `ai-board`,
> è obsoleta.

## 1) GitHub

1. Crea il repository su GitHub.
2. Carica il progetto completo.
3. Verifica che siano presenti:
   - `kai-website/Dockerfile`
   - `kai-website/railway.toml`
   - `apps/board/Dockerfile`
   - `apps/board/railway.toml`

## 2) Railway Project

Nel progetto Railway crea **2 servizi** dallo stesso repo.

### Servizio A: `k2-ai-website`

- Source repo: questo repository
- Root Directory: `kai-website`
- Builder: Dockerfile (automatico)
- Porta: gestita da `PORT`
- Healthcheck: `/`
- Auto-deploy: `main`

Nota operativa importante:

- Per `k2-ai-website` usare deploy Git-backed da GitHub.
- Evitare `railway up` per questo servizio: Railway puo fallire in modo intermittente
  nella risoluzione di `root directory` e `railway.toml` durante lo snapshot upload,
  anche con configurazione corretta.
- Se devi pubblicare dal terminale, usa lo script repo-root
  `scripts/deploy-website-via-git.sh`.

Variabile ambiente richiesta:

```env
VITE_KAI_API_BASE_URL=https://board.tuodominio.it
```

### Servizio B: `k2-board` (AIOS)

- Source repo: questo repository
- Root Directory: `apps/board`
- Builder: Dockerfile (automatico)
- Healthcheck: `/health`
- Replica: **1 obbligatoria** — il canale Telegram usa long-polling `getUpdates`:
  due repliche significano due poller in conflitto (Telegram ne serve uno solo).

Variabili ambiente minime:

```env
PORT=8000
AIOS_HOST=0.0.0.0

# Obbligatori per girare
AIOS_SUPABASE_URL=<https://xxx.supabase.co>
AIOS_SUPABASE_SERVICE_KEY=<service-key>
ANTHROPIC_API_KEY=<anthropic>

# Obbligatorio fuori da locale: senza, l'API resta SENZA autenticazione
# (serve_cockpit.py si rifiuta di partire con AIOS_HOST non locale e token vuoto)
AIOS_API_TOKEN=<token-lungo>
AIOS_ALLOWED_ORIGIN=https://app.k2-ai.it

# Autonomia + Telegram nello stesso processo del cockpit
AIOS_AUTONOMY=1
TELEGRAM_BOT_TOKEN=<bot-token>
TELEGRAM_CHAT_ID=<chat-id>
TELEGRAM_ALLOWED_CHAT_IDS=<altri-id-ammessi>

# Braccio esecutore ESTERNO: senza questo, ogni azione verso il mondo
# (invio email, pubblicazione) non parte e viene riportata come non eseguita
N8N_WEBHOOK_URL=https://n8n.tuodominio.it/webhook/k2ai
N8N_WEBHOOK_TOKEN=<token-firma-opzionale>

AIOS_IG_TOKEN=<instagram>
```

> ⚠️ Non usare il process `worker` del Procfile **insieme** a `AIOS_AUTONOMY=1`:
> sono due loop di autonomia e quindi due poller Telegram in conflitto. Scegline uno.

## 3) Dominio

Configura due host:

- `tuodominio.it` -> servizio `k2-ai-website`
- `board.tuodominio.it` -> servizio `k2-board`

## 4) Go-live check (10 minuti)

1. `https://board.tuodominio.it/health` risponde `ok`.
2. Il cockpit su `/api/approvals` risponde 401 senza token (auth attiva) e 200 col token.
3. Telegram riceve il messaggio di avvio `🟢 K2-AI è attivo`.
4. **Verifica che l'approvazione esegua davvero**: approva una decisione dalla card
   Telegram e controlla che la risposta dica *cosa* ha fatto (`✅ Eseguito: insert su
   <tabella>` o `✅ Inviato a n8n · workflow «…»`). Se leggi
   `⚠️ Approvato ma NON eseguito — …`, l'azione non è partita e il messaggio riporta
   la causa: quasi sempre `N8N_WEBHOOK_URL` mancante o credenziali del workflow scadute.
5. Controlla in `aios_audit` che l'evento sia `executed` e non `failed`.

## 4.1) Publish del sito da terminale

Per il solo sito pubblico:

```bash
./scripts/deploy-website-via-git.sh
```

Lo script:

- verifica che il branch corrente sia `main`
- blocca il deploy se la working tree non e pulita
- esegue `npm run build` in `kai-website`
- pubblica con `git push origin main`

Per saltare la build locale:

```bash
./scripts/deploy-website-via-git.sh --skip-build
```

## Opzionale (legacy)

Solo se vuoi usare login/account board via `/login` e `/admin`, aggiungi anche:

```env
SUPABASE_URL=<supabase-url>
SUPABASE_KEY=<supabase-anon>
SUPABASE_SERVICE_KEY=<supabase-service-role>
```

## 5) Variabili morte da ripulire su `k2-ai-board`

Reliquie del vecchio `ai-board` (Notion) rimaste sul servizio: **nessun codice le legge**,
e alcune sono attivamente ingannevoli. Da rimuovere:

- `TELEGRAM_MODE=webhook`, `TELEGRAM_WEBHOOK_URL` → il bot NON usa webhook: fa
  long-polling `getUpdates` dentro il loop di autonomia. Lette da zero righe di codice.
  Attenzione: se un giorno qualcuno registra davvero un webhook sul bot via
  `setWebhook`, `getUpdates` inizia a rispondere 409 e i bottoni Approva/Rifiuta
  smettono di funzionare in silenzio.
- `NOTION_TOKEN`, `NOTION_PAGE_ID`, `BOARD_*`, `APP_*`, `BOARD_DATA_BACKEND` → servivano
  ad `ai-board`. Il token Notion va comunque **rigenerato** (è girato in chat durante i
  test del vecchio servizio) e poi togliersi di mezzo.
- `AIOS_INTERNAL_AUTONOMY=1` → **non fa niente su `main`**: l'autonomia interna piena
  (scritture interne eseguite senza passare dalla coda) non è mai stata mergiata. Se la
  vuoi davvero è una decisione da prendere apposta, non un env da lasciare acceso.

## 6) Nota sicurezza

Ruota i segreti usati in sviluppo prima del go-live (vedi `apps/board/SECURITY.md`).
