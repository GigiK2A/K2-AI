# Deploy Checklist — Security + Tracking Setup

**Status post-setup automatico**:
- ✅ PostHog Cloud EU project creato (ID 179781), keys salvate in 4 `.env` locali
- ✅ PostHog ingest verificato end-to-end (capture + query funzionano)
- ✅ Dev server kai-website boota, analytics.js caricato
- ⚠️ Resta: Supabase migrations da applicare + Railway env vars da settare

---

## 1) Apply Supabase migrations (5 min)

Vai su **Supabase dashboard → SQL editor**.

### A) ai-board project
Apri il file:
```
/Volumes/PARASSITA/K-AI/docs/security-audit/APPLY-NOW-ai-board.sql
```
Copia tutto, paste in SQL editor, click **Run**.

Verifica: tutte le tabelle elencate ora hanno il toggle RLS verde + esiste tabella `analytics_snapshots`.

### B) kai-website project
Apri:
```
/Volumes/PARASSITA/K-AI/docs/security-audit/APPLY-NOW-kai-website.sql
```
Paste in SQL editor (stesso o diverso progetto Supabase, dipende da come hai diviso), click **Run**.

Verifica: `kbot_sessions`, `kbot_conversions`, `newsletter_subscribers`, `newsletter_issues` hanno RLS attiva.

### C) Test post-applicazione
Lancia il K-BOT locale per verificare che le RLS non rompano niente:
```bash
cd /Volumes/PARASSITA/K-AI/kai-website/kbot/backend
.venv/bin/uvicorn app.main:app --port 8001
# Poi in altro terminale:
curl -X POST http://localhost:8001/api/kbot/session -H "Content-Type: application/json" -d '{"service_id":"P12","mode":"report"}'
```

Atteso: `{"sessionId": "...", "linkToken": "..."}`. Se torna errore "permission denied", manca service-role key in backend env.

---

## 2) Railway env vars — bundle pronto-paste

Per OGNI servizio Railway, aggiungi/aggiorna queste variabili. Vai su Railway → tuo progetto → **Variables**.

### Servizio: kai-website (Node)
```
KBOT_CORS_ORIGINS=https://www.k2-ai.it,https://k2-ai.it
NEWSLETTER_PUBLISH_PATH_TOKEN=<GENERA NUOVO — vecchio compromesso>
VITE_POSTHOG_KEY=<PROJECT_API_KEY_phc_…>
VITE_POSTHOG_HOST=https://eu.i.posthog.com
INTERNAL_API_KEY=<già impostato — opzionale rotate>
LOG_FORMAT=json

# Opzionali (lascia vuoto per disabilitare):
SENTRY_DSN=
SLACK_ALERTS_WEBHOOK=
```

**Comando per generare token sicuro a 256 bit** (esegui localmente):
```bash
openssl rand -hex 32
```
Usa l'output come nuovo valore di `NEWSLETTER_PUBLISH_PATH_TOKEN`.

### Servizio: kbot Next.js standalone
```
NEXT_PUBLIC_POSTHOG_KEY=<PROJECT_API_KEY_phc_…>
NEXT_PUBLIC_POSTHOG_HOST=https://eu.i.posthog.com
NEXT_PUBLIC_API_BASE_URL=https://www.k2-ai.it
```

### Servizio: kbot Python backend
```
POSTHOG_API_KEY=<PROJECT_API_KEY_phc_…>
POSTHOG_HOST=https://eu.i.posthog.com
KBOT_CORS_ORIGINS=https://www.k2-ai.it,https://k2-ai.it
LOG_FORMAT=json

# Tutto il resto (ANTHROPIC_API_KEY, SUPABASE_*, STRIPE_*, RESEND_*, JWT_*) — già configurato in produzione

# Opzionale:
SENTRY_DSN=
```

### Servizio: ai-board
```
POSTHOG_PERSONAL_API_KEY=<PERSONAL_API_KEY_phx_…>
POSTHOG_PROJECT_ID=179781
POSTHOG_HOST=https://eu.i.posthog.com
TELEGRAM_WEBHOOK_SECRET=<GENERA con openssl rand -hex 32>
APP_BIND_HOST=0.0.0.0    # Railway needs 0.0.0.0
LOG_FORMAT=json

# Opzionali:
SENTRY_DSN=
SLACK_ALERTS_WEBHOOK=
```

**⚠️ Ai-board — segreti da RUOTARE** (vedi [SECRET-ROTATION-PROCEDURE.md](SECRET-ROTATION-PROCEDURE.md)):
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `SUPABASE_SERVICE_KEY` (la versione VERA service-role, non lo swap)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` (mettici la VERA anon/publishable, non service-role)
- `TELEGRAM_BOT_TOKEN`
- `RESEND_API_KEY`
- `BOARD_PASSWORD` (almeno 16 char random)

---

## 3) Redeploy

Railway: trigger redeploy manuale per ciascun servizio dopo aver settato le env vars.

```
Railway → service → Deployments → click "Redeploy"
```

O via git push se hai auto-deploy on push.

---

## 4) Smoke test in produzione

Dopo deploy:

```bash
# 1) Site risponde + analytics.js caricato
curl -s https://www.k2-ai.it | grep -E "analytics\.js|posthog"

# 2) Health checks tutti up
curl -s https://www.k2-ai.it/api/health
curl -s https://api.k2-ai.it/health    # kbot backend
# ai-board health: se accessibile pubblicamente

# 3) PostHog riceve eventi reali
# Apri https://www.k2-ai.it in browser, naviga 2-3 pagine
# Poi vai su PostHog → Activity → dovresti vedere $pageview entro 30s

# 4) Conta click pillar dopo qualche minuto
# Apri PostHog → Product analytics → New insight → Trends → Event = profile_click
```

---

## 5) Cron backup off-site

Setta cron su Railway (oppure GitHub Actions schedule), riferimento: [BACKUP-PROCEDURE.md](BACKUP-PROCEDURE.md)

Quick start:
```bash
# Daily backup at 03:00 UTC
0 3 * * * /Volumes/PARASSITA/K-AI/scripts/backup-supabase.sh --target r2 >> /var/log/backup.log 2>&1
0 4 * * * /Volumes/PARASSITA/K-AI/scripts/backup-notion.sh >> /var/log/backup-notion.log 2>&1
```

Storage off-site consigliato: **Cloudflare R2** (EU residency, zero egress fee, 10GB free).

---

## 6) Verifica scheduler ai-board pickup eventi PostHog

Dopo che ai-board è deployato e migration `006_analytics_snapshots.sql` applicata:

```bash
# Attendi 1h (cron) oppure forza un sync manuale via API se esposta
# Poi controlla che la tabella sia popolata:
# Via Supabase SQL editor:
SELECT * FROM analytics_snapshots ORDER BY ts DESC LIMIT 5;
```

Dashboard ai-board → naviga a `/analytics` → dovrebbe mostrare bar chart click profili + funnel K-BOT.

---

## Riepilogo cose fatte automaticamente

- ✅ 4 .env locali popolate con keys PostHog
- ✅ Smoke test PostHog (capture + query): event ricevuto
- ✅ Build kai-website con vite 7 + Next.js kbot — entrambi OK
- ✅ Pytest kbot 19/19
- ✅ Tutti gli scanner clean (npm, pip, semgrep, gitleaks reali)
- ✅ Bundle SQL Supabase pronti-paste in `APPLY-NOW-*.sql`

## Cose ancora TUE

- ⏳ Paste 2 SQL bundle in Supabase dashboard
- ⏳ Settare env vars su Railway (4 servizi)
- ⏳ Generare e ruotare segreti (Anthropic, OpenAI, Stripe, etc.)
- ⏳ Setup cron backup
- ⏳ Smoke test prod dopo redeploy
- ⏳ (Opzionale) Account Sentry per errori
- ⏳ (Opzionale) Slack webhook per alert
