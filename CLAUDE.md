# K2-AI — Memoria di progetto per Claude Code

> Questo file va messo nella **root della repo K-AI**. Claude Code lo legge automaticamente ad ogni sessione. NON cancellarlo, NON spostarlo.

---

## 1. Identità del progetto

- **Brand**: K2-AI
- **Dominio**: k2-ai.it (italiano, solo mercato IT)
- **Positioning v2** (aggiornato aprile 2026): *"Sistemi AI operativi per PMI italiane"*
- **ICP**: PMI 5-50 dipendenti, fatturato 500k-10M, settori prioritari servizi professionali (studi ingegneria/architettura/commercialisti), manifatturiero, servizi B2B
- **Claim operativo**: progetti di automazione AI (agenti email/CRM, microapp documentali, RAG, triage ticket) chiavi in mano in 30-60 giorni
- **Legal**: K2A S.R.L.S., P.IVA IT03655920548, REA PG-304896

> Termini v1 da NON usare mai: *"advisor finanziari PMI"*, *"diagnosi strategica"*, *"AdvisorBoost/StrategyBoost"*. Sono stati già rimossi. Non reintrodurli.

## 2. Principio base — ESTENDERE, NON RIPROGETTARE

Il sito v1 è live, ha traffico residuo e backlink. Architettura visiva, design system e pagine esistenti **si mantengono**. L'intervento v2 è additivo:

- si **conservano** homepage, pagine servizi esistenti, layout, palette, tipografia
- si **aggiungono** 10 pillar hub sotto `/suite-ai/[slug].html`
- si **riscrivono solo H1/H2 e meta** delle pagine v1 se necessario
- si **aggiunge** il 5° esito paid al K-BOT (Stripe Payment Link, 19€)
- **vietato**: redesign globale, cambio stack, migrazione framework, riscritture massicce

Se stai per proporre un refactor più ampio di 3 file esistenti, **fermati e chiedi**.

## 3. Stack tecnologico (vincolato — riverificato contro `origin/main` il 18 agosto 2026)

| Layer | Tecnologia | Note |
|---|---|---|
| Frontend | **Vite 7.3.3 + HTML/CSS/JS vanilla** | Le pagine del sito restano HTML vanilla: NON introdurre framework nel sito vetrina. React 19 è però già una dipendenza reale del repo (con `@vitejs/plugin-react`), usata fuori dalle pagine statiche. |
| Hosting | **Railway via Docker** (`kai-website/railway.toml` + `Dockerfile` + `server.js`) | dominio www.k2-ai.it già collegato. **`vercel.json` non esiste**: redirect 301 e header di sicurezza vivono in `server.js`. |
| API backend | Node.js HTTP server (`server.js`, porta 4173) | proxy verso FastAPI per `/api/kbot/*` e `/api/stripe/webhook` |
| DB | Supabase EU (region Frankfurt) | GDPR-compliant |
| Pagamenti | Stripe Payment Link | no integrazione custom, solo link |
| Email transazionale | Resend | free tier 3k email/mese |
| Analytics | PostHog self-host | no Google Analytics |
| LLM API | Claude API (Anthropic) | no OpenAI — **ECCEZIONE (giu 2026, OK Luca): OpenAI SOLO per la web search del K-BOT** (Responses API, dietro il client-tool `web_search` di Claude). Tutto il resto resta Claude. ⚠️ **Secondo uso di OpenAI constatato nel codice e mai documentato qui**: `tools/blog-bot/lib/images.ts` genera le 3 immagini di ogni articolo con `gpt-image-1`, e `OPENAI_API_KEY` è fra i secret di `blog-autopilot.yml`. **Da confermare o rimuovere con Luca.** |
| Form/CRM embedded | Airtable free + webhook | no HubSpot |

**Stato reale di `kai-website/package.json` (18 agosto 2026)**: devDependencies `vite ^7.3.3`, `typescript ^6.0.3`, `@vitejs/plugin-react`, tipi React/Node. Dependencies (14): `@anthropic-ai/sdk`, `@supabase/supabase-js`, `stripe`, `resend`, `posthog-js`, `three`, `react`, `react-dom`, `@react-pdf/renderer`, `docx`, `pdf-parse`, `puppeteer-core`, `@sparticuz/chromium`, `@sentry/node`.

> La vecchia dicitura *«package.json ha solo Vite 5.2.0, zero npm packages frontend»* era ferma ad aprile 2026 ed è stata rimossa perché falsa. La **regola** resta in vigore: niente nuove dipendenze senza motivare il peso sul bundle. Prima di stimare bundle o Lighthouse, leggi il `package.json`, non questa tabella.

**Vincolo Node**: Vite 7 richiede `^20.19.0 || >=22.12.0`. Il Node locale è 22.11 e **non basta** per buildare il sito (vedi §9).

**Budget tech fisso: 65€/mese**. Ogni SaaS aggiuntivo richiede OK di Luca.

Nessuna nuova libreria npm senza motivare peso bundle. Lighthouse mobile ≥ 90.

## 4. Architettura informativa target

```
/                         (index.html — homepage)
/metodo.html              (4-step metodologia)
/laboratorio.html         (casi studio interni — "i primi clienti siamo stati noi")
/k-bot.html               (diagnosi AI gratuita → aggiungere 5° esito paid)
/suite-ai.html            (overview pacchetti HOST/WEB/STUDIO)
/contatti.html
/analisi.html             (⚠ orphaned: esiste ma non è in nav, no canonical)
/privacy.html
/cookie.html
/note-legali.html

← NUOVI pillar hub da creare (HTML pages in kai-website/src/):
/suite-ai/agenti-email-crm.html           P01 — 1180 vol/mese
/suite-ai/automazioni-amministrative.html  P02 — 1210
/suite-ai/ai-legale-contratti.html        P03 — 1050
/suite-ai/ai-ingegneria-progettazione.html P04 — 1200
/suite-ai/microapp-documenti-tecnici.html  P05 — 1000
/suite-ai/ai-customer-service-ticket.html  P06 — 1610
/suite-ai/rag-knowledge-base.html          P07 — 1010
/suite-ai/ai-compliance-audit.html         P08 — 930
/suite-ai/ai-controllo-gestione-reporting.html P09 — 1110
/suite-ai/integrazione-gestionali-erp.html P10 — 1050
```

Ogni pillar ha 6 cluster articoli nel blog, linkati bidirezionalmente.

## 5. File canonici (fonte di verità)

In `docs/piano-strategico/` (da popolare se non presenti):

1. `piano-crescita-K2-AI.json` → pricing ladder, modello economico 3 anni, SEO v2, roadmap
2. `K2-AI_Keyword_Map.xlsx` → 10 pillar + 80 keyword con volumi, difficulty, intent, CPC
3. `K2-AI_Sintesi_Progetto_Luigi.docx` → executive summary

Se un'istruzione contraddice questi file, chiedi conferma a Luca prima di procedere.

## 6. Brand voice (obbligatoria su tutto il nuovo copy)

- **Italiano**, mai inglese nei titoli (eccezioni: termini tecnici consolidati tipo "agenti AI", "RAG", "API")
- **Tono**: pragmatico, diretto, orientato al fare. Mai "trasformazione digitale", "journey", "empower", "unlock"
- **Numeri sempre**: se dici "risparmi tempo", quantifica in ore/settimana
- **Niente buzzword**: evita "rivoluzionario", "innovativo", "all'avanguardia", "cutting-edge"
- **Tu diretto**: "ti diamo un agente che…" non "forniamo soluzioni per…"
- **Lunghezza H1**: 45-65 caratteri. H2: 30-70. Meta description: 140-155.

## 7. SEO — regole invariabili

- Una **keyword primaria per pagina**
- **Title tag**: keyword primaria + brand in coda (es. *"Agenti AI email CRM per PMI | K2-AI"*)
- **H1**: contiene keyword primaria, non uguale al title
- **Schema.org**: Organization in homepage, Service in ogni pillar, FAQPage dove ci sono FAQ
- **Internal linking**: ogni pillar linka ≥ 4 cluster figli, ogni cluster rilinka al pillar padre
- **Immagini**: WebP, alt text descrittivo, lazy loading
- **Canonical**: ogni pagina deve avere `<link rel="canonical">` esplicito
- **Sitemap** e **robots.txt** già presenti in `src/public/` — aggiorna sitemap quando aggiungi pagine

## 8. K-BOT — architettura e flusso paid

Il K-BOT **non vive più** in `k-bot.html + js/chat.js` (legacy landing). Quella pagina è solo brochure che linka a `/app/`. L'app reale è:

- **Frontend chat**: Next.js 16 standalone in `kbot/` (basePath `/app`, output standalone)
- **Backend**: FastAPI Python in `kbot/backend/`, deploy Railway separato
- **Auth**: Supabase (login-first prima di chattare)
- **DB**: tabella `kbot_sessions` con `user_id` su `auth.users`
- **LLM**: Anthropic Claude Haiku per chat, Sonnet per report PDF
- **PDF**: ReportLab nativo Python (no HTML/CSS print)

Vedi `kbot/AGENTS.md` per dettaglio endpoint, env e flusso completo.

### Flusso paid (già implementato)
1. Utente apre `/app/` → login Supabase → entra in chat
2. Conversazione → Claude Haiku emette blocco `CONSULENZA_SUMMARY_*` → `reportReady=true`
3. CTA "Sblocca il report PDF · 19€" in `kbot/src/components/chat/MessageBubble.tsx`
4. Click → `POST /api/kbot/checkout` (FastAPI) crea Stripe Checkout dinamico con `client_reference_id=<kbot_session_id>`
5. Pagamento → webhook FastAPI verifica firma → `status='paid'`, `has_paid:true` su Supabase
6. Webhook triggera `/api/kbot/generate-pdf` → Sonnet + ReportLab → upload Supabase Storage
7. Resend invia email con PDF allegato
8. Frontend polla `/api/kbot/status` → mostra link al report

### Payment Link statico (entry alternativo)
Esiste anche un **Stripe Payment Link statico** (`STRIPE_TIER0_PAYMENT_LINK` env var) come entry point indipendente dal chat, per:
- Distribuzione via email marketing / social / newsletter
- Link diretto in firma email, footer, social bio
- Demo / test esterno

Per agganciare un pagamento da Payment Link statico alla sessione K-BOT corrente, appendere `?client_reference_id=<kbot_session_id>&prefilled_email=<email>` all'URL. Senza `client_reference_id` il webhook accetta il pagamento ma fa skip silenzioso (nessuna sessione K-BOT da aggiornare).

Pagina conferma post-checkout: `/k-bot/grazie?session_id={CHECKOUT_SESSION_ID}` (servita dal sito principale, vedi `src/k-bot/grazie.html`).

### Upgrade path Tier 1
Bottone "Passa al Tier 1 da 49€" → form Airtable (lead qualificato, non self-serve).

## 9. File structure rilevanti

```
kai-website/                 ← sito principale (Vite + HTML vanilla)
├── src/
│   ├── *.html               ← pagine principali (k-bot.html è brochure, NON chat)
│   ├── k-bot/grazie.html    ← landing post-pagamento (gestisce session_id query)
│   ├── suite-ai/*.html      ← 20 pillar hub sul disco (P01-P20). I 10 di §4 sono quelli con keyword map e priorità SEO; gli altri esistono già come pagine.
│   ├── blog/                ← index.html (sentinel BLOG_INDEX_AUTO) + <slug>.html + img/
│   ├── css/                 ← base.css, nav.css, components.css, pages.css, k2-immersive.css
│   ├── js/
│   │   ├── chat.js          ← widget K-BOT lite per landing (qualificazione lead, NON la chat premium)
│   │   ├── k-bot-grazie.js  ← parser session_id su /k-bot/grazie
│   │   ├── nav.js, scroll.js, contact-form.js, hero-neural-bg.js, filter.js
│   └── public/              ← sitemap.xml, robots.txt, llms.txt, fonts/
├── api/                     ← API Node/TS (alcune deprecated, prod usa Python)
│   └── kbot/                ← endpoint K-BOT TS (legacy, prod proxia a Python)
├── server.js                ← Node HTTP server prod: proxy /api/kbot/* + /api/stripe/webhook a FastAPI,
│                              mappa REDIRECTS_301, clean-URL (.html → 301 senza estensione), apex → www
├── vite.config.js           ← entry points multi-page + header CSP del dev server
├── Dockerfile, entrypoint.sh, railway.toml   ← deploy reale (NON c'è vercel.json)
└── kbot/                    ← K-BOT Premium app (Next.js + Python, deploy Railway separato)

kai-website/kbot/            ← ⚠ percorso reale: è DENTRO kai-website, non alla root
├── src/                     ← Next.js 16 (basePath /app, output standalone)
│   ├── app/                 ← page.tsx, sign-in, dashboard, providers.tsx
│   ├── components/chat/     ← MessageBubble.tsx (CTA paid qui)
│   ├── lib/api.ts           ← client FastAPI
│   └── types/chat.ts
├── backend/                 ← FastAPI Python
│   └── app/api/             ← ~19 moduli: session, message, checkout, webhook, generate_pdf, status,
│                               upload, skills, report, billing_api, compute, conversations,
│                               deliverables, diagnostics, export, fetch_url, followups, checks, context
├── next.config.ts           ← basePath '/app'
└── AGENTS.md                ← guida specifica K-BOT (leggi anche questa)
```

## 10. Cosa NON fare mai senza chiedere

1. Cambiare il dominio o la configurazione DNS
2. Disattivare i redirect 301 esistenti, che vivono nella mappa `REDIRECTS_301` di `kai-website/server.js`: `/workshop` e `/workshop.html` → `/suite-ai`; `/casi-studio` e `/casi-studio.html` → `/laboratorio`. Ogni nuovo 301 va aggiunto lì, **non** in un `vercel.json` (che non esiste).
3. Rimuovere pagine v1 che hanno backlink
4. Integrare SaaS a pagamento non in elenco (eccezione approvata: **OpenAI per la SOLA web search del K-BOT**, giu 2026 — vedi §3)
5. Modificare pricing mostrato al pubblico senza conferma
6. Aggiungere npm packages frontend senza motivazione esplicita di peso bundle

## 11. Workflow Git

- Branch di lavoro: `feat/<area>-<descrizione-breve>` (es. `feat/pillar-hub-suite-ai`)
- Commit semantici: `feat:`, `fix:`, `chore:`, `docs:`, `style:`, `refactor:`
- PR verso `main` con descrizione, screenshot prima/dopo se visivo, checklist Lighthouse
- CI: type-check + lint + build devono passare

## 12. Contatti

- **Owner**: rluigiluca@gmail.com
