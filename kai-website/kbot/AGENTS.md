# K2-AI K-BOT Standalone — Guida per agenti

> File letto automaticamente dai tool AI (Claude Code, Codex, ecc.) ad ogni sessione.
> Mantieni questo file aggiornato quando l'architettura cambia.

---

## Cos'è questo progetto

Il **K-BOT Premium** è l'app dedicata alla generazione di report professionali in PDF a partire da una conversazione con Claude. È **separato dal sito principale** (`/Volumes/PARASSITA/K-AI/kai-website/`) ma vive nello stesso monorepo, sotto la directory `kbot/`.

### Due componenti distinti

```
kbot/
├── backend/                ← FastAPI Python, deploy Railway
│   ├── app/
│   │   ├── api/            (session, message, upload, report, checkout, generate-pdf, status, webhook)
│   │   ├── lib/            (auth, prompts, analysis, pdf_renderer, sessions, services, skills, storage, email)
│   │   ├── templates/      (Jinja2 HTML + CSS print-A4 + blocks/* partials)
│   │   ├── assets/         (logo K2-AI ufficiale)
│   │   ├── main.py
│   │   └── settings.py
│   ├── requirements.txt
│   ├── railway.toml        (Nixpacks + chromium apt deps per Playwright)
│   └── .env.local          (Anthropic, Supabase, Stripe, Resend — non committato)
│
└── (root)                  ← Next.js 16 frontend, deploy Railway
    ├── src/app/            (page.tsx, sign-in, sign-up, dashboard, providers.tsx)
    ├── src/components/     (auth, chat, layout, insights, report, ui)
    ├── src/lib/            (api.ts → backend FastAPI, supabase.ts, utils.ts)
    ├── src/types/chat.ts
    ├── next.config.ts      (basePath: '/app', output: 'standalone')
    └── .env.local
```

---

## Stack canonico

| Layer | Tech |
|---|---|
| Frontend | Next.js 16 + React 19 + TypeScript + Tailwind 4 |
| Backend | FastAPI + uvicorn + Python 3.12 |
| LLM | Anthropic Claude Haiku 4.5 (chat) + Sonnet 4.5 (report PDF) |
| Auth | **Supabase Auth** (JWT validation via JWKS endpoint, ECC P-256). **NESSUN Clerk.** |
| DB | Supabase Postgres — tabella `kbot_sessions` con `user_id` FK su `auth.users` |
| Storage | Supabase Storage — bucket `kbot-uploads`, `kbot-reports` |
| Payments | Stripe Checkout one-time 19€ + webhook su FastAPI |
| Email | Resend (dominio `k2-ai.it` verificato) |
| PDF | **ReportLab nativo Python** (Flowables + Platypus, BaseDocTemplate, no HTML/CSS) |

---

## Architettura: session-based, mirror del sito

Il backend kbot **replica l'architettura V2 del sito** (`kai-website/api/kbot/*.ts`), quindi:

- Tutti gli endpoint vivono sotto `/api/kbot/*`
- Ogni conversazione è una row di `kbot_sessions` identificata da UUID
- I messaggi sono salvati come array JSONB nel campo `messages`
- Il dato strutturato estratto da Claude finisce in `collected_data.extractedData`
- La generazione PDF è in due step: (a) JSON strutturato via Sonnet (single-call o multi-call 3-fase, flag `ANTHROPIC_PDF_MULTI_CALL`), (b) `pdf_renderer.py` mappa i blocchi su Flowables ReportLab nativi → A4 PDF
- Lo schema dei blocchi PDF è documentato in **`lib/skills/report-premium-design/SKILL.md`** del sito (skill master sempre caricata)

### Endpoint del backend Python

| Endpoint | Auth | Funzione |
|---|---|---|
| `POST /api/kbot/session` | opzionale | Crea una nuova session (anonima o user-linked) |
| `GET  /api/kbot/session/{id}` | opzionale | Restituisce la session |
| `POST /api/kbot/session/{id}/link-user` | obbligatoria | Lega una session anonima a un utente |
| `GET  /api/kbot/sessions` | obbligatoria | Storico sessioni dell'utente (dashboard) |
| `POST /api/kbot/message` | opzionale | Turno di chat, Claude Haiku |
| `POST /api/kbot/upload` | opzionale | Upload file → Supabase Storage |
| `POST /api/kbot/report` | opzionale | ReportData deterministico (no LLM) |
| `POST /api/kbot/checkout` | opzionale | Stripe Checkout session |
| `POST /api/kbot/generate-pdf` | `x-internal-key` o `status='paid'` | Sonnet → JSON → Jinja2 → Playwright PDF |
| `GET  /api/kbot/status` | no | Polling stato dopo checkout |
| `POST /api/stripe/webhook` | firma Stripe | Marca session paid, scrive `has_paid` su user metadata, triggera generate-pdf |

---

## Flusso utente (login-first)

1. Utente apre `/app/` (Next.js standalone) → vede `<LoginFirstScreen>`
2. Login Supabase email/password → `providers.tsx` rileva `SIGNED_IN` → entra in chat
3. Prima chat → `ensureSession({ mode: "report" })` crea row `kbot_sessions` con `user_id` valorizzato
4. Conversazione → Claude Haiku emette blocco `CONSULENZA_SUMMARY_*` quando ha dati sufficienti → `reportReady=true` → CTA "Sblocca il report PDF · 19€"
5. Click sblocca → `POST /api/kbot/checkout` → redirect Stripe
6. Post pagamento → webhook → `has_paid:true` su `app_metadata` Supabase + `status='paid'` → generate-pdf auto-triggerato → PDF su Supabase Storage + email Resend

### Cross-bot continuity (suite-ai → kbot premium)

Il sito principale ha un widget K-BOT su `suite-ai.html` (e altrove) per qualificazione lead. Quando l'utente vuole passare al premium:

1. Il widget salva il `session_id` corrente in `sessionStorage["kbot.site_session_id"]`
2. Una CTA "Continua su K-BOT Premium →" appare nelle pagine `suite-ai.html`, `k-bot.html`, `per-te.html` con `href="/app/?continue=<session_id>"`
3. La pagina del kbot standalone legge `?continue=` e adotta la session esistente invece di crearne una nuova

---

## Convenzioni operative

- **Quando aggiungi un endpoint**: aggiorna anche `kbot/AGENTS.md` (questo file) e `lib/api.ts` del frontend.
- **Quando cambi lo schema JSON del report PDF**: aggiorna `lib/skills/report-premium-design/SKILL.md`.
- **Nuove migrazioni Supabase**: file numerato in `supabase/migrations/NNN_descrizione.sql`, applica via SQL Editor del progetto KAI (lo stesso usato dal sito).
- **Niente Clerk**: l'auth è puramente Supabase. Se vedi import di `@clerk/*`, rimuovili.
- **Niente streaming finto sul frontend**: la chat usa risposta unica. Non rimettere il vecchio `streamAppend` con `setInterval`.
- **Niente endpoint v1 legacy**: `chat`, `teaser`, `cleanup`, `dashboard` (vecchia versione), `feedback`, `leads` sono morti. Non li ripristinare.

---

## K-BOT produce DELIVERABLE, non solo report (giu 2026)

Lo scope-lock "K-BOT = SOLO analisi e report" è stato rimosso. Oltre alle analisi, K-BOT
genera **deliverable operativi**: calendari editoriali, piani contenuti, checklist, tabelle,
bozze testi. Unico confine invariato: NON costruisce software/automazioni → rimanda a `suite-ai`.

- **Classifier** (`lib/analysis.py`): categoria `contenuti` con `data_table` "Calendario editoriale"
  (una riga per ogni uscita; **deroga esplicita** al cap globale "array max 8 voci", altrimenti i
  calendari venivano troncati a 8 righe). `deliverableType` dal summary guida la categoria insieme a `reportType`.
- **Routing skill per intento** (`lib/services.py` → `infer_service_id_from_session`): i messaggi
  utente pesano ×3 vs URL/file ×1, così l'intento (es. "calendario instagram" → P11 marketing/content)
  batte il dominio del sito analizzato (es. ingegneria). Regressione coperta in `tests/test_routing_and_profile.py`.
- **Export Excel**: `POST /api/kbot/render-deliverable-xlsx` (gated come generate-pdf: paid/internal/test)
  ri-renderizza l'`analysis_json` persistito in `collected_data` come `.xlsx` (`lib/xlsx_renderer.py`,
  ogni `data_table` → un foglio). Frontend: `downloadDeliverableXlsx` (`lib/api.ts`) + bottone "Scarica in
  Excel" in `MessageBubble`. Export PDF/Word per-messaggio restano in `api/export.py`.

---

## Comandi utili

```bash
# Backend Python (dev locale)
cd kbot/backend
source .venv/bin/activate                   # se esiste, altrimenti python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend Next.js (dev locale)
cd kbot
npm install
npm run dev                                  # serve su http://localhost:3000/app/

# Type-check frontend
cd kbot && npx tsc --noEmit

# Smoke test PDF rendering (mock JSON)
cd kbot/backend && .venv/bin/python -m app.lib.pdf_renderer  # se aggiungi un __main__
```

---

## Env variables

### Backend (`kbot/backend/.env.local` o Railway)

```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5
ANTHROPIC_PDF_MODEL=claude-sonnet-4-5
ANTHROPIC_PDF_MULTI_CALL=0                   # 1 per attivare generazione 3-fase (riduce troncamento conclusions)
NEXT_PUBLIC_SUPABASE_URL=https://<proj>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sb_secret_...
# JWT verification via JWKS (auto-derived from SUPABASE_URL); legacy HS256:
# SUPABASE_JWT_SECRET=...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
RESEND_API_KEY=re_...
INTERNAL_API_KEY=...                         # per generate-pdf server-to-server
FRONTEND_URL=https://app.k2-ai.it
NEXT_PUBLIC_SITE_URL=https://www.k2-ai.it
```

### Frontend (`kbot/.env.local` o Railway)

```
NEXT_PUBLIC_API_BASE_URL=https://api.k2-ai.it    # URL pubblico del backend
NEXT_PUBLIC_SUPABASE_URL=https://<proj>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

---

## Storia (per orientamento futuro)

- **Precedenti versioni** del backend (FastAPI + Clerk, FastAPI standalone con Stripe diretto, ecc.) sono state archiviate ed eliminate. **Non recuperarle**: il design corrente è canonico.
- L'auth è stata migrata da Clerk a Supabase (commit `981e034`).
- Il backend session-based attuale è stato introdotto col commit `37a5273` (rebuild completo).
