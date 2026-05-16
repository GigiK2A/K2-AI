# PRODUCTION_AUDIT_PLAN.md

**Data**: 2026-05-16
**Scope**: customer-facing surfaces — sito marketing K2-AI + K-BOT (widget e premium)
**Esclusi**: K2-Board (`api.k2-ai.it`, tool interno) — già auditato separatamente

---

## Struttura attuale

### Surfaces
| Componente | Path | Tech | Ruolo |
|---|---|---|---|
| Sito marketing | `kai-website/src/*.html` | HTML statico + Vite 7 + Vanilla JS | Lead generation |
| Pagine pillar | `kai-website/src/suite-ai/*.html` (20) | Stesso | SEO + funnel |
| Server Node | `kai-website/server.js` (2775 LOC) | Node http + proxy | Routing, SSR, proxy |
| K-BOT widget | `kai-website/src/js/chat.js` | Vanilla JS | Chat in-page |
| K-BOT premium | `kai-website/kbot/src/app/*.tsx` | Next.js 15 + Supabase Auth | Chat con report PDF |
| K-BOT backend | `kai-website/kbot/backend/app/` | FastAPI + Anthropic | LLM + sessioni + storage |

### Tech stack
- Frontend: Vite 7, Vanilla HTML/CSS/JS + React solo per K-BOT standalone (Next.js 15)
- Backend: Node http (server.js) → proxy `/api/kbot/*` a FastAPI Python interno
- LLM: Anthropic Claude (haiku/sonnet)
- DB: Supabase Postgres EU (RLS attiva)
- Storage: Supabase Storage (bucket `kbot-uploads`, `kbot-reports`)
- Payment: Stripe Payment Link 19€ + webhook
- Email: Resend (transactional)
- Analytics: PostHog Cloud EU (anonymous)
- Auth K-BOT premium: Supabase Auth (email/password)
- Deploy: Railway (1 servizio kai-website, container con Node + FastAPI Python interno + Next.js standalone)

### Routing principale (server.js)
- `/` → homepage statica
- `/k-bot`, `/per-te`, `/laboratorio`, `/metodo`, `/suite-ai`, `/suite-ai/<slug>` → pagine marketing
- `/app/*` → proxy a Next.js standalone (K-BOT premium)
- `/api/intake/contact` → form contatti
- `/api/intake/newsletter` → newsletter signup
- `/api/kbot/*` → proxy a FastAPI Python interno (porta 8000)
- `/api/stripe/webhook` → Stripe payment_intent
- `/api/report/{pdf,docx}` → generazione report Puppeteer/react-pdf
- `/api/health` → healthcheck

---

## Punti forti (verificati)

1. **CSP strict** su pagine marketing (`script-src 'self'`), rilassata solo `/app/*` per Next.js hydration
2. **PostHog tracking** anonimo end-to-end attivo (event ricevuti verificati)
3. **Stripe webhook** signature verified (`STRIPE_WEBHOOK_SECRET` required, idempotent)
4. **RLS Supabase** attiva su tutte le tabelle K-BOT (deny-all anon, service-role bypass)
5. **Rate limiting** attivo su endpoint costosi (chat, fetch-url, upload, report)
6. **SSRF protection** in `url_fetcher.py` (validate URL + redirect re-validation + IPv6 blocked + non-HTTP ports blocked)
7. **Prompt injection** wrapping (`<UNTRUSTED_FILE_CONTENT>`, `<UNTRUSTED_URL_CONTENT>`)
8. **Security headers**: HSTS, X-Frame-Options, X-Content-Type-Options, Permissions-Policy
9. **Auth premium**: Supabase Auth, session cookie httpOnly via Next.js
10. **HTTPS only**: Railway termina TLS, upgrade-insecure-requests in CSP
11. **Session link_token** (H-6 fix): anonymous session takeover bloccato
12. **Stripe success_token** opaque (H-7 fix): no session UUID leak in URL
13. **Newsletter HTML sanitize** server-side (isomorphic-dompurify)
14. **iOS Safari overflow guard** (commit 2068eae)
15. **No vulnerabilità npm/pip** (audit Sprint security precedente)

---

## Punti deboli da indagare

### Backend
- **server.js 2775 LOC** monolite — manca separazione concerns
- Manca **input validation schema-based** su form (al momento solo length check)
- Manca **rate limit per email** su contact form (rischio abuso 1 utente)
- Manca **CAPTCHA o anti-bot** su form pubblici
- **Logging**: structured, ma manca alert su 5xx ricorrenti
- **Fallback Anthropic down**: K-BOT mostra "Errore di connessione, riprova" generico — UX da migliorare
- **Timeout Anthropic**: settato sull'SDK? Da verificare
- **Payload size limit**: server.js limita `readJsonBody` a 16KB default. K-BOT upload usa 24MB. Da verificare per altri endpoint che il limit sia rispettato

### Frontend
- **Welcome message K-BOT premium** dopo rollback è ancora "Benvenuto. Sono K-BOT, l'analista K2-AI..." — bias diagnosi strategica risolto via service_id null + system prompt guard, ma copy ancora menziona "diagnosi di bilancio"
- **Email confirm Supabase Auth**: utente conferma manuale, ora disabilitato → ma il flusso registrazione non lo comunica chiaramente
- **Form contatti**: validation? Errori utente? Verifica casi limite
- **Form newsletter**: stessi check
- **K-BOT widget**: cosa succede se `/api/kbot/chat` 5xx? Utente vede solo errore generico
- **Loading states**: K-BOT premium "Caricamento…" mostra solo durante auth state — manca stato durante invio messaggio (3typing dots ma se backend lento >10s utente non sa)
- **Empty states**: K-BOT widget appena aperto OK, ma dopo errore network il widget rimane in stato confuso?
- **Mobile**: già fix iOS overflow recente — da verificare visivamente
- **Accessibility**: aria-labels su form? alt text immagini? keyboard navigation?

### Chatbot
- **System prompt** ora ha cold-start guard (chiede tipo report prima) ✓
- **Rate limit** 30/min message — verifica error 429 → UI mostra messaggio chiaro?
- **Prompt injection** via URL + file: wrap attivo ✓
- **Anthropic timeout**: client SDK default 10 min — troppo lungo, utente abbandona prima
- **Output Claude → frontend**: come viene renderizzato? Markdown? Plain text? Rischio XSS se HTML emesso?
- **Privacy disclosure**: K-BOT raccoglie email/dati nel flow → cookie banner? Privacy policy linkata in chat?

### Sicurezza
- Già audit precedente fatto (0 critical/high reali nel code dopo fix). Da rifare scan attuale per regressioni.
- Verifica nuova: la chiave SCREENSHOT_API_KEY è davvero solo server-side?

### UX
- **Homepage**: pulizia messaggio v2 "Sistemi AI operativi per PMI italiane" — verificare consistency
- **Suite-ai pages** (20): tutte popolate o alcune placeholder?
- **CTA chiare**: "Apri K-BOT", "Contattaci", "Diagnosi gratuita 19€" — coerenti?
- **Footer**: privacy, cookie, note legali presenti
- **Newsletter signup**: dove? Funzionale?
- **Trust signals**: testimonial, casi studio in `/laboratorio` — popolato?

---

## Rischi mappati

### Tecnici (gravità alta)
- **R1** Anthropic API down → K-BOT widget + premium falliscono → no fallback graceful
- **R2** Stripe webhook signing secret mancante in env → payment_intent.succeeded non popola `revenue_events` → revenue tracking broken
- **R3** Supabase Auth confirm email OFF → chiunque può claim qualsiasi email → low risk con 1 utente Luigi, ma rischio long-term
- **R4** Rate limit in-memory single-process → su scale-out 2 replica Railway, rate limit aggirabile per /api/kbot/*

### Sicurezza (gravità media)
- **R5** Newsletter publish token in `server.js:24` comprometto (in git history) → necessaria rotazione (già nota)
- **R6** Supabase service-role key in env Railway → accesso completo DB. Se Railway compromesso, full breach
- **R7** PostHog Personal API key (ai-board): privata, se leaked può leggere tutti i progetti dell'org

### UX (gravità media)
- **R8** K-BOT premium 401 Supabase "Invalid login credentials" senza distinzione tra "account non esiste" / "password sbagliata" → UX confusa (utente non sa se registrarsi o reset)
- **R9** Sito mostra "Diagnosi finanziaria del mio bilancio" come prompt suggerito, ma chatbot ora cold-start chiede tipo → coerenza non perfetta
- **R10** Welcome message K-BOT premium menziona "diagnosi di bilancio" ma cold-start dovrebbe essere neutro

### Legali (gravità media-alta)
- **R11** Privacy policy aggiornata con disclosure analytics PostHog + LLM Anthropic (US transfer)?
- **R12** Cookie banner: con PostHog anonymous + no localStorage si può evitare. Verifica policy
- **R13** GDPR DSR (Data Subject Request): procedura per delete account utente?

---

## Checklist produzione

### Backend (target produzione)
- [ ] Schema-based input validation tutti i form (Joi/Zod equivalente per server.js, già Pydantic kbot backend)
- [ ] Timeout esplicito Anthropic 60s
- [ ] Rate limit per email su contact form
- [ ] CAPTCHA opzionale (Cloudflare Turnstile?) — decisione: posporre se traffico basso
- [ ] Fallback graceful se Anthropic down (messaggio utente specifico)
- [ ] Alert su Sentry 5xx burst
- [ ] Health endpoint completo (DB ping, Anthropic ping)
- [ ] Backup off-site Supabase (script pronto, da schedulare cron Railway)

### Frontend
- [ ] Welcome K-BOT premium aggiornato neutrale  
- [ ] Prompt suggestion chip coerenti con cold-start neutro
- [ ] Login errore distinto: "Account non esiste" vs "Password errata" (se Supabase lo distingue)
- [ ] Privacy/Cookie banner: decisione finale
- [ ] Loading state messaggio K-BOT visibile dopo 3s (typing dots OK, aggiungere progress indicator se >10s)
- [ ] Error state K-BOT con retry button
- [ ] Form contact: validation visibile (email format, telefono opzionale ma formato)
- [ ] Form newsletter: feedback chiaro post-submit (success/error)
- [ ] Accessibility: lighthouse a11y >90
- [ ] Mobile: lighthouse mobile >85 (performance, accessibility, best practices, SEO)
- [ ] Test su iOS Safari + Chrome Android reali

### Chatbot
- [ ] Cold-start non assume tipo report ✓
- [ ] Output Claude sanitizzato (no HTML injection)
- [ ] Privacy disclosed in first message
- [ ] Lead capture flow chiaro (quando e come email viene chiesta)
- [ ] CTA finale conversation: chiara (contatti vs. 19€ PDF)
- [ ] Tone of voice coerente con sito (italiano, diretto, no buzzword)
- [ ] Gestione 429: UI dice "Hai inviato troppi messaggi, riprova tra 1 minuto"
- [ ] Gestione 500: UI dice "Problema temporaneo K-BOT, riprova" + retry button

### Sicurezza
- [ ] Re-run npm audit + pip-audit + semgrep + gitleaks
- [ ] CSP regression test (paste in browser, verifica nessun blocco)
- [ ] No NEW secrets in code (verifica grep)
- [ ] `.env` files gitignored
- [ ] Sentry DSN settato per error capture
- [ ] Rate limit funzionale: test manuale 35 richieste/min → 429
- [ ] SSRF test: tenta `http://localhost`, `http://169.254.169.254` → 422

### Tests
- [ ] pytest kbot backend: 19/19 pass
- [ ] npm run build kai-website: ✓
- [ ] npm run build kbot Next.js: ✓
- [ ] Smoke test prod: login, chat, upload, fetch URL, report PDF
- [ ] Lighthouse desktop + mobile (homepage, k-bot, suite-ai/un pillar)

---

## Piano operativo

### Wave 1 — Audit parallelo (4 subagent simultanei)
- **A1 Backend**: routing, validation, error handling, security headers, rate limit, timeout, fallback. Output: `BACKEND_AUDIT.md`
- **A2 Frontend**: HTML pages 18 + suite-ai 20, components consistency, copy, microcopy, accessibility. Output: `FRONTEND_AUDIT.md`
- **A3 Chatbot**: widget + premium, conversation quality, prompt injection, output sanitization, error UX. Output: `CHATBOT_AUDIT.md`
- **A4 User simulation**: 8 personas. Output: `USER_SIMULATION_REPORT.md`

### Wave 2 — Security + Tests
- Re-run scanner (pip-audit, npm audit, semgrep, gitleaks, bandit)
- Output: `SECURITY_AUDIT_REPORT.md` (aggiornato)

### Wave 3 — Fix critical + high
- Per ogni Critical: fix obbligatorio
- Per ogni High: fix se non blocca timeline
- Per ogni Medium: documentato + fix se quick win

### Wave 4 — Build + smoke test
- pytest kbot
- npm build x2
- curl smoke prod (URL pubblici)
- Lighthouse via WebFetch (3 pagine)

### Wave 5 — Report finale
- `TESTING_REPORT.md`
- `PRODUCTION_READINESS_REPORT.md` con verdetto

---

## Vincoli operativi

- **NO deploy/push automatico durante audit** — fix locali, commit pending
- **Push solo dopo approvazione finale utente** (o conferma esplicita)
- **Nessuna modifica config produzione** (env Railway, DNS, Supabase dashboard) — solo proposte
- **Documenta tutto** — ogni claim verificato con file:line o test eseguito

---

## Time estimate

- Wave 1 (audit parallelo): 30-45 min
- Wave 2 (security): 5 min
- Wave 3 (fix critical): 30-60 min (dipende da findings)
- Wave 4 (tests): 10 min
- Wave 5 (report finale): 15 min

Totale: **1.5-2.5 ore** di subagent work concorrente.
