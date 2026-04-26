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

## 3. Stack tecnologico (vincolato — verificato aprile 2026)

| Layer | Tecnologia | Note |
|---|---|---|
| Frontend | **Vite 5.2.0 + HTML/CSS/JS vanilla** | NO framework JS/React/Next.js |
| Hosting | Vercel + Docker (railway.toml presente) | dominio www.k2-ai.it già collegato |
| API backend | Node.js HTTP server (port 4173/8000) | proxied via Vite dev + Vercel rewrites |
| DB | Supabase EU (region Frankfurt) | GDPR-compliant |
| Pagamenti | Stripe Payment Link | no integrazione custom, solo link |
| Email transazionale | Resend | free tier 3k email/mese |
| Analytics | PostHog self-host | no Google Analytics |
| LLM API | Claude API (Anthropic) | no OpenAI |
| Form/CRM embedded | Airtable free + webhook | no HubSpot |

**Stack confermato da audit aprile 2026**: package.json ha solo Vite 5.2.0 come devDependency. Zero npm packages frontend.

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

## 8. K-BOT — upgrade al 5° esito paid

Il K-BOT (k-bot.html + js/chat.js) produce attualmente risposte via `/api/intake/kbot-chat`.

Aggiungere il 5° esito paid:
- Trigger: diagnosi completata + intent alto (2+ "approfondisci" nel flusso)
- CTA: *"Vuoi il piano d'azione operativo di 7 pagine con priorità, tempi e template pronti? 19€ — consegna in 10 minuti"*
- Flusso: click → redirect a `STRIPE_TIER0_PAYMENT_LINK` (env var) → webhook → Resend invia PDF
- PDF generato server-side dalle risposte della sessione
- Upgrade path: bottone "Passa al Tier 1 da 49€" → form Airtable

## 9. File structure rilevanti

```
kai-website/
├── src/
│   ├── *.html          ← pagine principali
│   ├── css/
│   │   ├── base.css    ← variabili, tipografia, layout
│   │   ├── nav.css     ← navigazione
│   │   ├── components.css ← cards, buttons, grids, chat widget
│   │   └── pages.css   ← layout page-specific
│   ├── js/
│   │   ├── chat.js     ← K-BOT logic (sessionStorage, API calls)
│   │   ├── nav.js      ← hamburger, active links
│   │   ├── scroll.js   ← reveal animations
│   │   ├── contact-form.js
│   │   ├── hero-neural-bg.js
│   │   └── filter.js
│   └── public/
│       ├── sitemap.xml ← aggiornare con nuove pagine
│       ├── robots.txt
│       ├── llms.txt
│       └── fonts/
├── api/                ← backend Vercel functions
├── server.js           ← Node HTTP server prod
├── vite.config.js      ← entry points + proxy config
└── vercel.json         ← rewrites + redirects
```

## 10. Cosa NON fare mai senza chiedere

1. Cambiare il dominio o la configurazione DNS
2. Disattivare redirect 301 esistenti (`/workshop.html` → `/suite-ai.html`, `/casi-studio.html` → `/laboratorio.html`)
3. Rimuovere pagine v1 che hanno backlink
4. Integrare SaaS a pagamento non in elenco
5. Modificare pricing mostrato al pubblico senza conferma
6. Fare deploy in produzione — Luca mergia manualmente su `main` dopo review
7. Push su `main` direttamente: sempre su feature branch `feat/...`
8. Aggiungere npm packages frontend senza motivazione esplicita di peso bundle

## 11. Workflow Git

- Branch di lavoro: `feat/<area>-<descrizione-breve>` (es. `feat/pillar-hub-suite-ai`)
- Commit semantici: `feat:`, `fix:`, `chore:`, `docs:`, `style:`, `refactor:`
- PR verso `main` con descrizione, screenshot prima/dopo se visivo, checklist Lighthouse
- CI: type-check + lint + build devono passare

## 12. Contatti

- **Owner**: rluigiluca@gmail.com
