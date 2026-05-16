# K2-Board — Railway deploy (single service)

A **single** Railway service runs both Next.js (frontend, public on `$PORT`) and
FastAPI (backend, internal on `127.0.0.1:8000`) in one container. The frontend
talks to the backend via relative URLs proxied through Next.js rewrites; server
components hit FastAPI directly on loopback via `INTERNAL_API_URL`.

One domain: `board.k2-ai.it`. No separate `board-api` host.

## Configure the existing `k2-ai-board` service (or create new)

1. **Settings → Source**
   - Root Directory: `apps/board`
   - Dockerfile Path: `Dockerfile`
   - Builder: Dockerfile (auto-detected from `railway.toml`)
2. **Settings → Networking**
   - Custom Domain: `board.k2-ai.it`
   - Internal port: leave blank (Railway uses `$PORT`, container default 3000)
3. **Variables** — paste the block below (from `.env.example`)
4. **Settings → Deploy → Healthcheck**: `/health` (60s timeout) — already in `railway.toml`
5. Redeploy.

If you previously had two services (`k2-board-api` + `k2-board-web`), delete the
API service and its `board-api.k2-ai.it` custom domain. Only `k2-ai-board` remains.

## Environment variables (Railway → Variables)

| Variable                  | Value                                    | Notes                                                                                  |
| ------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------- |
| `SUPABASE_URL`            | `https://uiuvwzrmrdqbfajguuab.supabase.co` |                                                                                        |
| `SUPABASE_SERVICE_KEY`    | *(service role)*                         | Supabase → Settings → API                                                              |
| `BOARD_USERNAME`          | `luigi`                                  |                                                                                        |
| `BOARD_PASSWORD_HASH`     | *(bcrypt hash)*                          | `python -c "import bcrypt; print(bcrypt.hashpw(b'PW', bcrypt.gensalt()).decode())"`    |
| `BOARD_SESSION_SECRET`    | *(48+ random bytes)*                     | `python -c "import secrets; print(secrets.token_urlsafe(48))"`                         |
| `BOARD_CORS_ORIGINS`      | `https://board.k2-ai.it`                 | Same-origin in prod — kept for local dev (`http://localhost:3000`).                    |
| `ANTHROPIC_API_KEY`       | `sk-ant-...`                             | K-BOT                                                                                  |
| `STRIPE_WEBHOOK_SECRET`   | `whsec_...`                              | see `backend/STRIPE-WEBHOOK-SETUP.md`                                                  |
| `SENTRY_DSN`              | *(optional)*                             |                                                                                        |
| `LOG_FORMAT`              | `json`                                   |                                                                                        |
| `ENVIRONMENT`             | `production`                             |                                                                                        |
| `NEXT_PUBLIC_API_BASE_URL`| *(empty)*                                | Browser uses relative `/api/*` → Next.js rewrite → FastAPI.                            |
| `POSTHOG_PERSONAL_API_KEY`| *(optional)*                             | server-side only, never `NEXT_PUBLIC_*`                                                |
| `POSTHOG_PROJECT_ID`      | `179781`                                 |                                                                                        |
| `POSTHOG_HOST`            | `https://eu.i.posthog.com`               |                                                                                        |
| `PORT`                    | *(injected by Railway)*                  |                                                                                        |
| `INTERNAL_API_URL`        | *(leave default `http://127.0.0.1:8000`)* | Override only if you ever split the services again.                                    |

Google Calendar stubs (Sprint 9): `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`,
`GOOGLE_REFRESH_TOKEN` — leave empty.

### Sprint 9B/9C/9D — Approval execution, daily brief, email triage

| Variable                  | Default                    | Notes                                                                                       |
| ------------------------- | -------------------------- | ------------------------------------------------------------------------------------------- |
| `RESEND_API_KEY`          | *(empty)*                  | Se vuoto, le email approvate restano come memo. Setta per inviare via Resend.               |
| `BOARD_OWNER_EMAIL`       | `rluigiluca@gmail.com`     | Destinatario del brief mattutino.                                                           |
| `BOARD_EMAIL_FROM`        | `noreply@k2-ai.it`         | Mittente delle mail in uscita.                                                              |
| `DAILY_BRIEF_ENABLED`     | `true`                     | Setta `false` per disattivare il cron.                                                      |
| `DAILY_BRIEF_CRON`        | `0 7 * * *`                | Crontab in fuso Europe/Rome.                                                                |
| `DAILY_BRIEF_TZ`          | `Europe/Rome`              | TZ del scheduler.                                                                           |
| `EMAIL_TRIAGE_ENABLED`    | `false`                    | Setta `true` quando hai configurato Gmail OAuth (vedi `backend/GMAIL-OAUTH-SETUP.md`).      |
| `EMAIL_TRIAGE_CRON`       | `0 */2 * * *`              | Ogni 2 ore di default.                                                                      |

### Migrations da applicare

Dopo aver fatto pull del nuovo codice, apri Supabase → SQL editor e
applica nell'ordine:

1. `backend/app/db/migrations/002_agent_conversations.sql` (Sprint 9A, se non già applicata)
2. `backend/app/db/migrations/003_inbox_pending.sql` (Sprint 9C — stub email triage)

### Verifica post-deploy

```bash
# brief mattutino manuale
curl -X POST https://board.k2-ai.it/api/agent/brief/run-now \
    -H "Cookie: k2board_session=..."

# stato provider email
curl https://board.k2-ai.it/api/agent/email/providers \
    -H "Cookie: k2board_session=..."
```

## DNS

One CNAME on Cloudflare (or the registrar for `k2-ai.it`):

| Type  | Name     | Value                                  | Proxy    |
| ----- | -------- | -------------------------------------- | -------- |
| CNAME | `board`  | *hostname returned by Railway*         | DNS only |

Disable Cloudflare proxy until Let's Encrypt has issued. Then optionally re-enable.

Verify:
```bash
dig board.k2-ai.it +short
curl -I https://board.k2-ai.it/health
curl -I https://board.k2-ai.it/login
```

## Local Docker (optional)

```bash
cd apps/board
docker build -t k2-board .
docker run --rm -p 3000:3000 --env-file .env k2-board
# open http://localhost:3000
```

## Costs

Railway hobby: ~5€/mo (scale-to-zero) or ~10€/mo always-on. One service =
half the previous footprint. Well within the 65€/mo tech budget (CLAUDE.md §3).
