# Audit Codebase K2-AI — Prompt 1 Report

> Generato: 2026-04-20 | Branch: feat/v2-bootstrap

---

## A) Stato attuale sintetico

**Stack confermato**:
- Frontend: Vite 5.2.0 + HTML/CSS/JS vanilla (NO Next.js, NO React)
- Backend: Node.js HTTP server (`server.js`, port 4173/8000)
- Deploy: Vercel + Docker (railway.toml)
- Zero npm packages frontend (solo Vite come devDependency)

**Pagine live** (entry points in vite.config.js):
| URL | File | Status |
|-----|------|--------|
| `/` | index.html | ✅ Live |
| `/metodo.html` | metodo.html | ✅ Live |
| `/laboratorio.html` | laboratorio.html | ✅ Live (era casi-studio) |
| `/k-bot.html` | k-bot.html | ✅ Live |
| `/suite-ai.html` | suite-ai.html | ✅ Live (era workshop) |
| `/contatti.html` | contatti.html | ✅ Live |
| `/analisi.html` | analisi.html | ⚠ Esiste, non è in nav, no canonical |
| `/privacy.html` | privacy.html | ✅ Live |
| `/cookie.html` | cookie.html | ✅ Live |
| `/note-legali.html` | note-legali.html | ✅ Live |

**Gap vs CLAUDE.md**:
- CLAUDE.md descriveva Next.js 14 App Router → **ERRATO**, stack reale è Vite+HTML
- CLAUDE.md è stato aggiornato in questa sessione per riflettere lo stack reale

---

## B) Gap analysis v2

| Elemento | Stato | Gap |
|----------|-------|-----|
| 10 pillar hub `/suite-ai/[slug].html` | ❌ Mancanti | Da creare (Prompt 2) |
| K-BOT 5° esito paid (19€) | ❌ Mancante | Da implementare (Prompt 3) |
| Schema.org Service per pillar | ❌ Mancante | Da aggiungere ai pillar |
| PostHog tracking eventi custom | ❌ Non trovato | Da implementare (Prompt 5) |
| Stripe Payment Link | ❌ Non trovato | Da integrare (Prompt 3) |
| Resend email transazionale | ❌ Non trovato | Da integrare (Prompt 3) |
| Sitemap aggiornata con pillar | ❌ Solo 8 URL | Da aggiornare dopo Prompt 2 |
| Canonical tag in analisi.html | ❌ Mancante | Quick fix |
| Meta description in privacy.html | ❌ Mancante | Quick fix |
| Meta description in cookie.html | ❌ Mancante | Quick fix |

**Già a posto** (non richiedono intervento):
- ✅ Nessun termine v1 trovato (advisor, AdvisorBoost, ecc.) — già puliti
- ✅ SEO tecnico solido: canonical, OG, Twitter Card, Schema.org Organization/Service/FAQ/HowTo
- ✅ Robots.txt permissivo con AI crawlers (Claude, GPT, Perplexity)
- ✅ Sitemap presente e aggiornata (2026-04-16)
- ✅ 301 redirect corretti: workshop→suite-ai, casi-studio→laboratorio
- ✅ llms.txt presente con KPI verificati
- ✅ Font ottimizzati (woff2, self-hosted)

---

## C) Piano di lavoro — 6 task

| Priority | Task | Stima | ROI/Sforzo |
|----------|------|-------|------------|
| 1 | **Quick fix SEO** (canonical analisi.html, meta desc privacy/cookie) | 1h | Basso sforzo, SEO fix immediato |
| 2 | **10 pillar hub** HTML pages sotto /suite-ai/ con copy, schema.org Service+FAQ | 8-12h | Alto volume (9000+ vol/mese totale) |
| 3 | **K-BOT 5° esito paid** (Stripe link, webhook, PDF, Resend) | 12-16h | Revenue diretto |
| 4 | **PostHog eventi custom** (9 eventi KPI v2) | 3-4h | Misurabilità traction |
| 5 | **SEO on-page pagine v1** (H1/H2/meta → lessico v2, se necessario) | 2-3h | Basso — già in v2 positioning |
| 6 | **Lighthouse pass + ottimizzazioni** (LCP, CLS, favicon size) | 2-4h | UX + ranking |

**Note**:
- Task 5 probabilmente minimo: nessun termine v1 trovato, copy già in v2
- favicon.png pesa 520KB → da ottimizzare in Task 6
- analisi.html orfana → valutare se eliminare o reinserire in nav

---

## D) Rischi tecnici

| Rischio | Impatto | Mitigazione |
|---------|---------|-------------|
| Vite config con 11 entry points: aggiungere 10 pillar richiede aggiornamento rollupOptions | Medio | Aggiungere i 10 entry nel vite.config.js, uno per pagina pillar |
| suite-ai.html usa API dinamica per packages — i pillar sono statici | Basso | I pillar sono HTML statici, no conflitto |
| workshop.html = copia identica di suite-ai.html | Basso | Redirect 301 già in place, file da rimuovere nel cleanup |
| favicon.png 520KB | Medio Lighthouse | Convertire in WebP/ICO ottimizzato |
| analisi.html senza canonical, non in nav | Basso SEO | Aggiungere canonical o redirect a k-bot.html |
| docs/piano-strategico/ vuota (mancano i 3 file canonici) | Medio | Copiare i file dalla cartella Cowork prima del Prompt 2 |

---

## E) Domande per Luca

1. **analisi.html**: da mantenere (con canonical), redirigere a `/k-bot.html`, o rimuovere? Ha backlink?
2. **docs/piano-strategico/**: i tre file (JSON, xlsx, docx) vanno copiati prima del Prompt 2 — quando disponibili?
3. **K-BOT 5° esito**: la logica di "intent alto = 2+ approfondisci" è hardcodata nel frontend o viene dal backend? Dove vive la state machine degli esiti 1-4?
