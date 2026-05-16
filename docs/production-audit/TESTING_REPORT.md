# TESTING_REPORT.md

**Data**: 2026-05-16
**Scope**: customer-facing — kai-website + K-BOT widget + K-BOT premium

---

## Test eseguiti

### 1) Unit + integration tests

| Suite | Pass | Fail | Notes |
|-------|------|------|-------|
| pytest kbot backend | **19/19** | 0 | url_fetcher (SSRF + estrazione), tests recenti aggiunti per timeout/rate-limit |
| K2-Board pytest | 23/23 (precedente) | 0 | Out-of-scope qui, ma riportato |

### 2) Build

| Target | Status | Notes |
|--------|--------|-------|
| `kai-website` Vite 7 build | ✅ OK | 13.64s, all 38 routes built |
| `kbot` Next.js 15 build | ✅ OK | All routes (incl. /sign-in, /sign-up, /dashboard) prerendered |
| `node -c server.js` | ✅ OK | Syntax valid |
| FastAPI import | ✅ OK | `from app.main import app` boots clean |

### 3) Linting

| Target | Errors | Warnings |
|--------|--------|----------|
| kai-website ESLint | 0 | n/a (vanilla JS, no strict ESLint) |
| kbot Next.js ESLint | 0 | 3 minor (unused vars) — acceptable |
| Python (mypy/ruff) | n/a | Not configured globally — code quality manual review |

### 4) Security scanners (post-fix)

| Tool | Result |
|------|--------|
| `pip-audit` (kbot backend) | **0 vulnerabilities** |
| `npm audit` (kai-website) | **0 vulnerabilities** |
| `npm audit` (kbot frontend) | **0 vulnerabilities** |
| `gitleaks` | 19 findings — **all documented**: 16 are repeated citations of the same compromised newsletter token (in audit reports themselves), 3 are public-by-design publishable keys (Supabase `sb_publishable_*`, Clerk `pk_test_*`). `.gitleaksignore` added. **Unique real secret leaks: 1** (newsletter token, rotation pending) |
| `semgrep` (490 rules, 2074 files) | **1 finding** — `apps/board/backend/playground/oauth2.py:114` (one-time OAuth helper script, NOT deployed) — acceptable |
| `bandit` (Python static) | 1 false-positive (Markup-after-bleach.clean, noqa documented) |

### 5) Code coverage

Not measured — no coverage tool configured. Manual code review covered all critical paths (auth, chat, file upload, payments, webhook, screenshot).

### 6) Manual smoke tests (locale)

| Test | Result |
|------|--------|
| `uvicorn app.main:app` boot | ✅ |
| `npm run dev` kai-website | ✅ (vite 7) |
| K-BOT session create | ✅ HTTP 200 + `link_token` |
| K-BOT fetch URL (k2-ai.it) | ✅ HTTP 200, content extracted |
| K-BOT SSRF block (169.254.169.254) | ✅ HTTP 422 "Host non consentito" |
| Screenshot endpoint | ✅ PNG 1080×1350 generato + uploaded Supabase |
| Stripe webhook signature verify | ✅ (test invalid signature → 400, valid → 200 + row) |

### 7) Test mancanti / non eseguiti

- ❌ **Lighthouse desktop/mobile** — non eseguito (richiede headless Chromium runtime + URL pubblico). Da eseguire post-deploy.
- ❌ **Test E2E browser reale** (iOS Safari, Chrome Android) — non eseguito. Smoke test visivo richiede device fisici o BrowserStack.
- ❌ **Test load/stress** — no setup load testing. Rate-limit testato logicamente, non sotto carico reale.
- ❌ **Test multi-replica rate-limit** — single instance only su Railway corrente, OK per ora.
- ❌ **Test Stripe webhook live end-to-end** — webhook signature verify testato unit, ma payment flow reale non eseguito (richiederebbe Stripe Sandbox + carta test).

---

## Problemi trovati durante test

### Risolti durante questo audit

1. K-BOT widget → backend endpoint 404 (`/api/intake/kbot-chat` non esisteva) → fix: `/api/kbot/session` + `/api/kbot/message`
2. No timeout Anthropic SDK → 10 min default → workers stallavano → fix: 60s in tutti i client
3. Rate limit FastAPI vedeva sempre 127.0.0.1 (Node proxy) → tutti i limit erano un singolo bucket globale → fix: SlowAPI usa X-Forwarded-For
4. Welcome K-BOT premium contraddiceva il cold-start guard → utente vedeva "diagnosi di bilancio" ma bot diceva di non assumere → fix: welcome neutralizzato

### Aperti / non bloccanti

1. **Newsletter token** in storia git (commit `1347095e`) — richiede rotazione Railway env (azione utente)
2. **No E2E browser tests automatici** — manuale necessario post-deploy
3. **Lighthouse non eseguito** — manuale necessario post-deploy
4. **Multi-replica rate-limit** — design limitation, non blocker per single instance
5. **playground/oauth2.py** finding semgrep — script setup, non deploy, accettato

---

## Comandi riproducibili

```bash
# pytest backend
cd /Volumes/PARASSITA/K-AI/kai-website/kbot/backend
.venv/bin/python -m pytest tests/ -v

# builds
cd /Volumes/PARASSITA/K-AI/kai-website && npm run build
cd /Volumes/PARASSITA/K-AI/kai-website/kbot && npm run build

# security
cd /Volumes/PARASSITA/K-AI/kai-website/kbot/backend && .venv/bin/pip-audit -r requirements.txt
cd /Volumes/PARASSITA/K-AI/kai-website && npm audit
cd /Volumes/PARASSITA/K-AI/kai-website/kbot && npm audit
cd /Volumes/PARASSITA/K-AI && gitleaks detect --source . --no-banner
cd /Volumes/PARASSITA/K-AI && semgrep scan --config auto --exclude=node_modules --exclude=.venv --exclude=dist --exclude=.next --severity=ERROR --severity=WARNING

# smoke prod (post Railway redeploy)
curl https://www.k2-ai.it/api/health
curl https://api.k2-ai.it/health
curl -X POST https://www.k2-ai.it/api/kbot/session -H "Content-Type: application/json" -d '{"service_id":"P12","mode":"report"}'
```

---

## Verdict testing

**Build/test/scan suite — VERDE**. Pronto a livello tecnico per deploy. Mancano:
- Lighthouse (post-deploy)
- E2E browser real (post-deploy, manuale o BrowserStack)
- Load test (opzionale, single instance OK per traffico atteso PMI)
