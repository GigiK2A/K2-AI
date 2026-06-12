# Deploy K2-AI AIOS

Tutto è **deploy-ready** e **env-gated**: senza una chiave il relativo connettore
resta inattivo (vuoto), la piattaforma gira lo stesso. Per andare "full" basta
aggiungere le credenziali in `.env` / nelle variabili del deploy.

## 1. Variabili
Copia `.env.example` → `.env` e riempi almeno i CORE (`AIOS_SUPABASE_URL`,
`AIOS_SUPABASE_SERVICE_KEY`, `ANTHROPIC_API_KEY`). In produzione imposta anche
`AIOS_API_TOKEN` (bearer) e `AIOS_ALLOWED_ORIGIN`.

## 2. Processi (Procfile)
- `web`    → `serve_cockpit.py` (cockpit + API). In deploy imposta `AIOS_HOST=0.0.0.0`; usa `PORT` (Railway lo inietta).
- `worker` → `telegram_bot.py` (canale Telegram bidirezionale: invia card, riceve approva/rifiuta).
- cron giornaliero → `scheduler.py` (fa girare tutti gli agenti e accoda le proposte L1).

## 3. Railway (esempio)
```bash
cd aios
railway init           # o collega il progetto esistente
railway variables set $(grep -v '^#' .env | xargs)   # carica le env
railway up --detach    # deploy
# imposta start command del servizio web: python serve_cockpit.py  (AIOS_HOST=0.0.0.0)
# aggiungi un cron job Railway: python scheduler.py  (es. 0 7 * * *)
```

## 4. Sicurezza pre-produzione (vedi SECURITY.md)
1. `AIOS_API_TOKEN` impostato (senza, l'auth API è disabilitata).
2. HTTPS davanti a uvicorn (reverse proxy); non esporre la porta in chiaro.
3. Ruotare i segreti usati in sviluppo.
4. Chiavi esterne con **privilegi minimi** (es. Stripe restricted **read-only**; IMAP app-password; Google service account scope `readonly`).

## 5. Connettori e relative env
Vedi il pannello **Settings** del cockpit (`/api/integrations`): elenca ogni
servizio con stato "connesso / manca credenziale" e le variabili da impostare.
