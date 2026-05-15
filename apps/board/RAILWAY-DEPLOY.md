# K2-Board — Railway deploy

Due servizi separati nello stesso progetto Railway, entrambi via Docker.

## Servizio 1 — `k2-board-api` (FastAPI backend)

- **Root directory**: `apps/board/backend`
- **Builder**: Dockerfile (vedi `railway.toml`)
- **Internal port**: `8000`
- **Healthcheck**: `GET /health`
- **Public domain**: `board-api.k2-ai.it`

### Variabili d'ambiente (Railway → Variables)

| Variabile               | Valore                                           | Note                                          |
| ----------------------- | ------------------------------------------------ | --------------------------------------------- |
| `SUPABASE_URL`          | `https://uiuvwzrmrdqbfajguuab.supabase.co`       | dal `.env.example`                            |
| `SUPABASE_SERVICE_KEY`  | *(service role)*                                 | da Supabase → Settings → API                  |
| `BOARD_USERNAME`        | `luigi`                                          |                                               |
| `BOARD_PASSWORD_HASH`   | *(bcrypt hash)*                                  | `python -c "import bcrypt; print(bcrypt.hashpw(b'PW', bcrypt.gensalt()).decode())"` |
| `BOARD_SESSION_SECRET`  | *(48+ random bytes)*                             | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `BOARD_CORS_ORIGINS`    | `https://board.k2-ai.it`                         | aggiungere localhost solo in dev              |
| `ANTHROPIC_API_KEY`     | `sk-ant-...`                                     | per il K-BOT                                  |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...`                                      | vedi `backend/STRIPE-WEBHOOK-SETUP.md`        |
| `SENTRY_DSN`            | *(opzionale)*                                    | telemetria errori                             |
| `LOG_FORMAT`            | `json`                                           |                                               |
| `ENVIRONMENT`           | `production`                                     |                                               |
| `PORT`                  | *(non impostare — Railway lo inietta)*           |                                               |

Stub Google Calendar (lasciare vuoti finché Sprint 9):
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`.

## Servizio 2 — `k2-board-web` (Next.js 15 frontend)

- **Root directory**: `apps/board/web`
- **Builder**: Dockerfile (multi-stage, `output: "standalone"`)
- **Internal port**: `3000`
- **Healthcheck**: `GET /login`
- **Public domain**: `board.k2-ai.it`

### Variabili d'ambiente

| Variabile                   | Valore                              | Note                                  |
| --------------------------- | ----------------------------------- | ------------------------------------- |
| `NEXT_PUBLIC_API_BASE_URL`  | `https://board-api.k2-ai.it`        | espone al browser → punta al backend  |
| `POSTHOG_PERSONAL_API_KEY`  | *(opzionale)*                       | server-only, non `NEXT_PUBLIC_*`      |
| `POSTHOG_PROJECT_ID`        | `179781`                            |                                       |
| `POSTHOG_HOST`              | `https://eu.i.posthog.com`          |                                       |
| `NODE_ENV`                  | `production`                        | (di default su Railway)               |
| `PORT`                      | *(iniettato da Railway)*            |                                       |

## DNS — record da creare su Cloudflare (o registrar del dominio `k2-ai.it`)

Railway, dopo aver aggiunto un *Custom Domain* per ciascun servizio,
ritorna un hostname tipo `<service>.up.railway.app`. Imposta:

| Tipo  | Nome (host)        | Valore                                | Proxy | TTL  |
| ----- | ------------------ | ------------------------------------- | ----- | ---- |
| CNAME | `board-api`        | *hostname fornito da Railway*         | DNS only | Auto |
| CNAME | `board`            | *hostname fornito da Railway*         | DNS only | Auto |

> **Importante**: se usi Cloudflare, lascia il proxy **disattivato (grigio)**
> finché Railway non emette il certificato Let's Encrypt. Puoi accenderlo
> dopo la prima emissione.

Verifica:
```bash
dig board.k2-ai.it +short
dig board-api.k2-ai.it +short
curl -I https://board-api.k2-ai.it/health
```

## Ordine di deploy

1. **Crea progetto Railway** dal repo GitHub (collega `K-AI`).
2. **Add service** → seleziona root `apps/board/backend` → nome `k2-board-api`.
3. **Variables** → copia/incolla dalla tabella sopra
   (lascia `STRIPE_WEBHOOK_SECRET` vuoto in prima istanza).
4. **Settings → Domains** → *Add custom domain* `board-api.k2-ai.it`.
5. Crea il CNAME DNS, aspetta verifica + emissione cert.
6. Quando `/health` risponde 200, segui `backend/STRIPE-WEBHOOK-SETUP.md`
   per impostare la webhook.
7. **Add service** → root `apps/board/web` → nome `k2-board-web`.
8. Variables + `board.k2-ai.it` come custom domain.
9. Apri `https://board.k2-ai.it/login` → autentica → tutto deve girare.

## Costi attesi

Railway hobby plan: ~5€/mese (con scale to zero) o ~10€/mese always-on.
Rispettato il budget tech 65€/mese (CLAUDE.md §3).
