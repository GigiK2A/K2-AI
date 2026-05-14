# K2-AI K-BOT — Guida tecnica (storica + corrente)

> **Per agenti AI**: leggi prima `kbot/AGENTS.md` per il quadro corrente.
> Questo file aggiunge dettagli architetturali utili a chi modifica il kbot a fondo.

---

## 1. Filosofia del prodotto

Il K-BOT Premium è un **generatore di report operativi PDF** alimentato da Claude. Non è un chatbot generico, è un motore di reportistica premium con tre caratteristiche distintive:

1. **Skill verticali**: 274 skill caricate da `kai-website/lib/skills/` (markdown) coprono i 20 servizi della Suite AI K2-AI, dal marketing all'edilizia alla finanza.
2. **Skill master `report-premium-design`**: documenta lo schema JSON dei blocchi e le regole di composizione. Sempre caricata nel prompt di Sonnet.
3. **PDF deterministico**: Sonnet genera **solo i contenuti** (titoli, dati, narrativa); il layout è renderizzato da Jinja2 + Playwright in formato A4. Il design è uguale per ogni report.

---

## 2. Tipi di blocchi nel PDF

Il modello Sonnet sceglie caso per caso quali blocchi inserire. Tutti sono renderizzati da partial Jinja2 in `kbot/backend/app/templates/blocks/`.

| Tipo | Quando |
|---|---|
| `executive_summary` | Primo blocco, sempre. Supporta gauge SVG + badges. |
| `kpi_grid` | 2-6 metriche numeriche chiave con variant ok/warning/alert. |
| `two_column` | Analisi laterali: narrativa+tabella vs badges+callout. |
| `narrative_split` | Strategia con sidebar operativa (concept, naming, piano canali). |
| `data_table` | Proiezioni, benchmark, scenari numerici. |
| `action_list` | Roadmap numerata con impatto stimato. |
| `risk_mitigation` | Rischi (severity badge) ↔ mitigations (cards). |
| `conclusions` | Ultimo blocco. Raccomandazione + milestone KPI laterali. |
| `narrative` | Testo full-width, uso parco. |

Schema completo: `kai-website/lib/skills/report-premium-design/SKILL.md`.

---

## 3. Pipeline di generazione PDF

```
session.collected_data + messages + skills
        ↓
analysis.generate_analysis_json()           ← Claude Sonnet 4.5, max_tokens=8192
        ↓
pdf_renderer.render_html()                   ← Jinja2 + report.html.j2 + blocks/*
        ↓
pdf_renderer._html_to_pdf_bytes()            ← Playwright headless Chromium
   ↳ force-open: details, [aria-expanded], hidden, .collapse
   ↳ wait_until="networkidle"
   ↳ page.pdf(format="A4", print_background=True, prefer_css_page_size=True)
        ↓
storage.upload_pdf()                         ← Supabase Storage bucket "kbot-reports"
        ↓
email.send_report_ready_email()              ← Resend, dominio k2-ai.it verificato
```

Tempo medio: ~130s LLM + ~10s rendering = ~2-3 minuti end-to-end.

---

## 4. Schema database (Supabase)

### Tabella `kbot_sessions` (in `supabase/migrations/001_kbot_sessions.sql` + 004)

| Colonna | Tipo | Note |
|---|---|---|
| `id` | UUID PK | |
| `created_at` / `updated_at` | TIMESTAMPTZ | |
| `user_id` | UUID FK auth.users | NULL = sessione anonima (rara, gestita via link-user) |
| `sector` / `path` / `step` | — | legacy v1, può restare valorizzato |
| `status` | TEXT | `active`, `report_ready`, `paid`, `teaser_shown`, `contacted` |
| `messages` | JSONB | `[{role, content, ts}]` |
| `collected_data` | JSONB | `{service_id, mode, extractedData, uploaded_files, summary, recommendedServiceId, recommendedTier, reportData, ...}` |
| `email` / `nome` / `disponibilita` | TEXT | usati al checkout e post-pagamento |
| `stripe_session_id` | TEXT | |
| `pdf_url` | TEXT | URL pubblico Supabase Storage |
| `paid_at` | TIMESTAMPTZ | |

### Tabella `kbot_conversions`

Log delle conversioni Stripe. Vedi migration 001.

### Storage buckets

- `kbot-uploads` (pubblico): file caricati dall'utente
- `kbot-reports` (pubblico): PDF generati

---

## 5. Auth flow Supabase (corrente)

- Il **frontend Next.js** usa `@supabase/supabase-js` standard. Login `signInWithPassword`, registrazione con metadata GDPR (privacy, terms, marketing consent).
- Il **backend FastAPI** valida il JWT in `Authorization: Bearer ...` tramite **JWKS endpoint**:
  ```
  https://<project>.supabase.co/auth/v1/.well-known/jwks.json
  ```
  Supporta ECC P-256 (ES256, chiavi attuali di Supabase) e RSA (RS256). Per progetti legacy esiste un fallback HS256 (`SUPABASE_JWT_SECRET`).
- Lo Stripe webhook scrive `app_metadata.has_paid = true` via `client.auth.admin.update_user_by_id` quando il pagamento va a buon fine.

---

## 6. Deploy Railway (target)

Due servizi separati su Railway, stesso progetto monorepo:

| Servizio | Source dir | Build | Start | Dominio |
|---|---|---|---|---|
| `kbot-backend` | `kbot/backend/` | Nixpacks Python + `chromium` apt deps | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | `api.k2-ai.it` |
| `kbot-frontend` | `kbot/` | `npm run build` + `output: 'standalone'` | `node .next/standalone/server.js` (port `$PORT`) | `app.k2-ai.it` |
| `kai-website` (esistente) | `src/` | Vite | (statico) | `www.k2-ai.it` |

Auto-deploy su push a `main`. Env variables vanno configurate nel dashboard Railway di ciascun servizio (`.env.local` non viene committato).

---

## 7. Cose da NON fare

1. **Non re-introdurre Clerk** o vecchi endpoint v1 (`/api/chat`, `/api/leads`, `/api/dashboard` legacy).
2. **Non hardcodare URL backend nel frontend**: usa `NEXT_PUBLIC_API_BASE_URL`.
3. **Non bypassare il gate `paid`** in `generate-pdf` se non con `INTERNAL_API_KEY` esplicito.
4. **Non aggiungere streaming SSE finto** sul frontend: Claude restituisce risposta unica.
5. **Non committare** `.env.local`, `.venv/`, file di test, file `._*` macOS.
6. **Non modificare** `lib/skills/report-premium-design/SKILL.md` senza aggiornare anche i partial Jinja2 corrispondenti.

---

## 8. Riferimenti

- `kbot/AGENTS.md` — sintesi operativa per agenti
- `kbot/CLAUDE.md` — `@AGENTS.md` (import per Claude Code)
- `kbot/backend/app/lib/analysis.py` — prompt builder + Sonnet call
- `kbot/backend/app/templates/report.css` — design A4 print-ready
- `lib/skills/report-premium-design/SKILL.md` — schema blocchi
- `supabase/migrations/001_kbot_sessions.sql` + `004_kbot_user_link.sql` — schema DB
- `vercel.json` (root del sito kai-website) — rewrite/redirect del sito principale
