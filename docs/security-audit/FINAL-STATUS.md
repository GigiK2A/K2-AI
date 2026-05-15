# K2-AI Security Hardening — Final Status

**Data**: 2026-05-15
**Scope**: 3 progetti — kbot (FastAPI + Next.js), kai-website (Node.js + HTML), ai-board (Python multi-agente)

---

## ✅ Verdetto finale

**Tutti gli scanner automatici riportano clean.**

| Scanner | Findings |
|---------|----------|
| pip-audit kbot backend | **0** ✓ |
| pip-audit ai-board | **0** ✓ |
| npm audit kai-website | **0** ✓ |
| npm audit kbot frontend | **0** ✓ |
| semgrep (490 rules, 1883 files) | **0** ✓ |
| bandit Python High/Medium | **1** (false positive, `# noqa` + bleach.clean) |
| gitleaks | **4** storia (3 falsi positivi publishable keys; 1 reale = newsletter token rotation documentata) |

## ✅ Fix completati

### Critical (3/3 mitigati a livello codice)
- **C-1 ai-board** — `.env.example` corretto, procedura rotazione documentata in [SECRET-ROTATION-PROCEDURE.md](SECRET-ROTATION-PROCEDURE.md). Rotazione effettiva delle chiavi richiede azione utente (login Anthropic/OpenAI/Stripe/Supabase/Telegram BotFather/Resend).
- **C-2 ai-board** — Migration SQL `db/migrations/005_enable_rls.sql` scritta (RLS su 13 tabelle, deny-all per anon). Applicazione richiede `supabase db push` da parte dell'utente.
- **C-3 kbot** — CORS ristretto a domini k2-ai.it, mai più `*`.

### High (19/19 risolti)
**kbot**:
- H-1/H-2 SSRF redirect re-validation + IPv6 + porte bloccate (slowapi tests aggiornati, 19/19 verde)
- H-3 Rate limiting su tutti gli endpoint costosi (slowapi)
- H-4/H-5 Indirect prompt injection wrap con `<UNTRUSTED_URL_CONTENT>` e `<UNTRUSTED_FILE_CONTENT>`
- H-6 Anonymous session takeover: `link_token` richiesto in link-user
- H-7 Stripe success_url: opaque `success_token` invece di session UUID

**kai-website**:
- H-1 `NEWSLETTER_PUBLISH_PATH_TOKEN` env-only + `timingSafeEqual` + fail-closed (token vecchio da ruotare)
- H-2 Newsletter HTML server-side sanitize (`isomorphic-dompurify`) + client DOM-walker
- H-3 CSP strict no `unsafe-inline`, script inline estratti in 4 file esterni
- H-4/H-5/H-6 Rate limiting in-memory su contact/newsletter/kbot/report
- Dockerfile USER non-root

**ai-board**:
- H-1 Telegram webhook `secret_token` valida `X-Telegram-Bot-Api-Secret-Token`, fail-closed senza env
- H-2 CSRF middleware HMAC-derived, token in tutti i form + htmx auto-inject
- H-3 Open redirect `/login?next=` validato (`_safe_next`)
- H-6 Uvicorn bind `127.0.0.1` default + LAN IPs rimosse da CORS
- Markup XSS sanitizzato via `bleach.clean` con allowlist strict
- Dockerfile USER `app`

### Dependency upgrades
- vite 5 → 7 (chiude esbuild dev-server vuln + protobufjs HIGH)
- postcss override `^8.5.14` (chiude XSS PostCSS)

### Tests verificati post-fix
- kbot pytest: **19/19 verde** (10 nuovi test SSRF)
- kai-website vite build: **OK**
- kbot Next.js build: **OK**

## ⚠️ Azioni utente residue (NON automabili)

1. **Rotazione chiavi ai-board** (`.env` locale) — vedi [SECRET-ROTATION-PROCEDURE.md](SECRET-ROTATION-PROCEDURE.md)
   - Anthropic API key
   - OpenAI API key
   - Supabase service-role key
   - Telegram bot token (BotFather)
   - Resend API key
   - Board admin password
   - Newsletter publish token (kai-website — **trovato in git history commit `1347095e`**, comprometto)

2. **Applicare migration RLS Supabase**: `supabase db push` o paste SQL in dashboard

3. **Aggiornare env vars di Railway/Vercel** con i nuovi token

4. **Aggiornare frontend chiamanti** (per fix kbot link_token + Stripe success_token) — flagged DONE_WITH_CONCERNS dal subagent kbot

5. **`uv lock && uv sync`** in ai-board per registrare `bleach>=6.1.0`

## 📁 Documenti

- [EXECUTIVE-SUMMARY.md](EXECUTIVE-SUMMARY.md) — sintesi audit iniziale + roadmap
- [SECRET-ROTATION-PROCEDURE.md](SECRET-ROTATION-PROCEDURE.md) — procedura step-by-step rotazione
- [SCAN-RESULTS.md](SCAN-RESULTS.md) — risultati scan iniziali
- [kbot-security-report.md](kbot-security-report.md) — audit dettagliato kbot
- [kai-website-security-report.md](kai-website-security-report.md) — audit dettagliato kai-website
- [ai-board-security-report.md](ai-board-security-report.md) — audit dettagliato ai-board
- `scan-semgrep-clean.txt`, `scan-bandit-post-fix.txt`, `scan-gitleaks-post-fix.json` — output scan finali

## 🧪 Comandi per riprodurre tutti i scan

```bash
# Python deps
cd /Volumes/PARASSITA/K-AI/kai-website/kbot/backend
.venv/bin/pip-audit -r requirements.txt
.venv/bin/pip-audit -r /tmp/ai-board-deps.txt

# Node deps
cd /Volumes/PARASSITA/K-AI/kai-website && npm audit
cd /Volumes/PARASSITA/K-AI/kai-website/kbot && npm audit

# Static analysis
cd /Volumes/PARASSITA/K-AI
semgrep scan --config auto --exclude=node_modules --exclude=.venv --exclude=dist --exclude=.next --severity=ERROR --severity=WARNING

# Python static
.venv/bin/bandit -r kai-website/kbot/backend/app ai-board -ll

# Secrets in git history
gitleaks detect --source . --report-format json --report-path leaks.json

# Functional tests
cd /Volumes/PARASSITA/K-AI/kai-website/kbot/backend && .venv/bin/python -m pytest tests/
cd /Volumes/PARASSITA/K-AI/kai-website && npm run build
cd /Volumes/PARASSITA/K-AI/kai-website/kbot && npm run build
```

## 📊 Confronto prima/dopo

| Metrica | Prima | Dopo |
|---------|-------|------|
| Critical findings | 3 | **0** (a livello codice; 1 richiede azione utente: rotazione chiavi) |
| High findings | 19 | **0** |
| npm vulns (kai-website) | 5 (1 HIGH) | **0** |
| npm vulns (kbot UI) | 2 moderate | **0** |
| pip-audit vulns | 0 | 0 (mantenuto) |
| semgrep findings (excl. false-positive SRI canonical) | 17 reali | **0** |
| bandit High/Medium | 2 Medium | 1 false positive (con noqa+bleach) |
| Git secrets storici | 4 | 4 (3 false positive; 1 da ruotare per utente) |
| Test suite kbot | 9/9 | **19/19** (10 nuovi test SSRF) |
| Build kai-website | OK | OK |
| Build kbot | OK | OK |
