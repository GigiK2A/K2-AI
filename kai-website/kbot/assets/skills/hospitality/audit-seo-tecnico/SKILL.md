---
name: audit-seo-tecnico
version: 3.0
description: >-
  Audit SEO tecnico per PMI italiane 5-50 dipendenti. Report DOCX 14-20 pagine con diagnosi
  tecnica, AI Search readiness (citabilita ChatGPT/Perplexity/Gemini), lettura storica algoritmo
  Google, sezione LOCAL SEO Italia (Google Business Profile, NAP consistency su 8 directory
  italiane, schema LocalBusiness, recensioni) e BRIDGE AGEVOLAZIONI (mappa problemi a bandi
  italiani: PNRR Digitalizzazione, Bonus Pubblicita, Credito R&S/Innovazione, Nuova Sabatini,
  Transizione 5.0, Punto Impresa Digitale). Trigger: "audit SEO", "audit SEO PMI", "audit tecnico
  sito", "il sito non si posiziona", "perche non mi trova Google", "SEO piccola impresa", "Google
  Business Profile audit", "report SEO con agevolazioni", "local SEO Italia", "SEO per AI",
  "citabilita ChatGPT", "come farsi citare dagli LLM", "SEO per ChatGPT", "AI search optimization",
  "generative engine optimization", "GEO". Input: URL sito, settore, regione, dipendenti.
  Analizza crawlability, Core Web Vitals, mobile, on-page, schema, AI-readiness, local SEO, GBP,
  NAP, citations. Per ogni problema: severita, impatto, istruzione operativa per webmaster, e
  mappa a bando italiano finanziabile. Output: DOCX + JSON. Differenziatori unici: italiano nativo
  tono titolare, bridge bandi italiani, Local SEO Italia, AI search readiness, lettura storica
  update Google.
allowed-tools:
  - WebFetch
  - WebSearch
  - Read
  - Write
  - Bash
---

# audit-seo-tecnico v3 — Italia + AI + Bandi edition

Audit SEO tecnico per PMI italiane con cinque differenziatori unici sul mercato:

1. **Italiano nativo + tono titolare**: report leggibile dal proprietario PMI, non solo dal webmaster
2. **Bridge Agevolazioni**: ogni problema serio mappato al bando italiano che lo finanzia
3. **Local SEO Italia**: focus GBP, recensioni Google, directory italiane (no clone Semrush)
4. **AI Search readiness**: citabilita su ChatGPT, Perplexity, Bing Copilot, Gemini (GEO)
5. **Lettura storica algoritmo Google**: diagnosi mancato adeguamento update 2010-2024 (Panda, Penguin, Mobile-First, Helpful Content, Core Web Vitals, E-E-A-T)

## Posizionamento competitivo

Mercato saturo (Semrush, Ahrefs, Sitebulb, Screaming Frog). K2-AI vince perche:

| Concorrente | Cosa fa | Cosa NON fa |
|---|---|---|
| Semrush/Ahrefs | Audit globale, gergo SEO, dashboard | Italiano titolare-friendly, bandi PMI, local SEO Italia, AI search |
| Lighthouse/PageSpeed | Performance tecnica gratuita | Strategia, prioritizzazione, bridge agevolazioni |
| Agenzia SEO locale | Consulenza umana 1500-5000 EUR | Velocita (3 giorni), prezzo (99 EUR), trasparenza |

**Tagline interna:** "L'unico audit SEO che ti dice anche con quale bando finanziare gli interventi — e se ChatGPT ti cita."

## Input

| Parametro | Obbligatorio | Descrizione |
|-----------|:------------:|-------------|
| URL sito | Si | URL homepage del sito da analizzare |
| Settore | Si | ATECO o descrizione (per benchmark + bandi pertinenti) |
| Regione | Si | Per bandi regionali + benchmark local SEO |
| N. dipendenti | Si | Per dimensionamento de minimis e fascia bandi |
| Note specifiche | No | Problematiche segnalate dal cliente |

## Workflow

### Step 1 — Crawl & analisi struttura

- Fetch homepage + max 20 pagine principali via `WebFetch`
- Analisi struttura navigazione, profondita click, orphan pages
- Verifica sitemap.xml e robots.txt
- Mappa URL e relazioni interne
- `WebSearch` per verifiche esterne (indicizzazione site:, citazioni)

### Step 2 — SEO tecnico

Analisi approfondita di:
- **HTTPS e sicurezza**: certificato SSL, mixed content, HSTS
- **Velocita e performance**: Core Web Vitals (LCP, INP, CLS), TTFB, compressione, caching, immagini, lazy loading, JS render-blocking
- **Mobile**: responsive, viewport, tap target, font size, mobile-first indexing
- **Crawlability**: robots.txt, sitemap.xml, noindex/nofollow, canonical, redirect chain, 404, crawl budget
- **Indicizzazione**: pagine indicizzate vs totali, canonical duplicati

Riferimento benchmark: `references/benchmark-core-web-vitals.md`

**Check trasversale lettura storica**: durante lo Step 2 verifica adeguamento agli update Google (Panda, Penguin, Mobile-First, Page Experience, Helpful Content, E-E-A-T). Tabella cronologica 2010-2024 con cosa misura ogni update e come adeguarsi oggi: `references/evoluzione-algoritmo-google.md`. Ogni problema diagnosticato deve essere ricondotto, dove pertinente, all'update Google che lo penalizza.

**Bandi PNRR Digitalizzazione**: per ogni problema con impatto stimato > 30%, segnalare se finanziabile dal bando regionale corrente. Invocare la skill `matching-bandi-agevolazioni` con keyword ["digitalizzazione PMI", "trasformazione digitale", "innovazione web"].

### Step 3 — SEO on-page

Analisi per ciascuna pagina crawlata:
- **Title tag**: lunghezza 50-60 char, keyword, unicita
- **Meta description**: lunghezza 150-160 char, CTA, unicita
- **Heading**: H1 unico, gerarchia H2-H6
- **Contenuto**: thin content, duplicate content, keyword density, E-E-A-T (autori dichiarati, expertise visibile)
- **Immagini**: alt tag, dimensioni, formati WebP/AVIF, lazy loading
- **Internal linking**: anchor text, distribuzione, link rotti
- **URL structure**: URL parlanti, lunghezza, parametri
- **Schema markup**: focus su **LocalBusiness italiano** (P.IVA, indirizzo italiano, orari, telefono +39), **Organization con sameAs** (LinkedIn Italia, Pagine Gialle, profili italiani), BreadcrumbList, FAQ, Product, Review

Checklist completa: `references/checklist-audit-completa.md`

### Step 4 — AI Search readiness (DIFFERENZIANTE)

Il traffico informativo si sta spostando su ChatGPT, Perplexity, Bing Copilot, Gemini. Un sito ben posizionato su Google puo essere invisibile agli LLM, e viceversa.

Checklist AI-readiness 10 punti operativi (struttura H semantica, FAQ schema, autori dichiarati, HTML pulito senza JS-render obbligatorio, list mentions in fonti citabili, recensioni esterne, dati strutturati ricchi, paragrafi citation-friendly, claim verificabili, brand mention extra-sito).

Riferimento operativo completo: `references/seo-ai-search-2025.md`

Test pratico: query brand su ChatGPT/Perplexity con `WebSearch` per verificare se e come il sito viene citato.

Score AI-readiness 0-100 + raccomandazioni operative.

### Step 5 — Local SEO Italia (DIFFERENZIANTE)

Verifica completa presenza locale italiana.

#### 5a. Google Business Profile (GBP)
- Esiste? Verificato? Categorie corrette?
- Foto: minimo 10 + 1 video
- Post settimanali ultimi 30 giorni
- Q&A: domande senza risposta
- Recensioni: numero, rating medio, ultima risposta titolare
- **Score GBP 0-100** + checklist azioni

#### 5b. NAP consistency (Name-Address-Phone)
Verifica coerenza Nome+Indirizzo+Telefono su 8 directory italiane prioritarie:
1. Google Business Profile
2. Bing Places
3. PagineGialle.it
4. Trovaprezzi.it (se e-commerce)
5. Cylex Italia
6. Tuugo Italia
7. Hotfrog Italia
8. Misterimprese.it

Per ogni directory: presente/assente, NAP coincide/divergente, link diretto correzione. Fai fetch reali via `WebFetch`, segna esplicitamente "non verificato" se la directory non risponde.

Lista completa con priorita: `references/directory-italiane-nap.md`

#### 5c. Recensioni e reputation
- Volume recensioni Google ultimi 12 mesi
- Risposte titolare: %
- Recensioni negative: presenza risposta + tono
- TripAdvisor (se ricettivo), Trustpilot
- Score reputation 0-100

#### 5d. Local citations & backlinks italiani
- Citazioni in news locali (giornali regionali)
- Link da camera di commercio, associazioni di categoria, enti locali
- Mancanze critiche da colmare

Checklist 40 item: `references/checklist-local-seo-italia.md`

### Step 6 — Analisi problemi e prioritizzazione

Per ogni problema trovato (Step 2, 3, 4, 5) assegna:
- **Severita**: critico / importante / minore
- **Impatto stimato sul traffico**: % stimata di traffico organico perso o non acquisito
- **Area**: crawlability, performance, mobile, sicurezza, on-page, immagini, schema, AI-readiness, GBP, NAP, reputation, citations
- **Update Google correlato** (se pertinente): es. Core Web Vitals 2021, Helpful Content 2022, E-E-A-T 2023
- **Istruzione operativa concreta**: non "ottimizza i title" ma "WordPress > Yoast SEO > Titoli e Metadati > pagina X, compila il campo Titolo SEO con [esempio]"

Costruisci matrice **impatto x sforzo**: quick win, progetti importanti, miglioramenti facili, deprioritizzare.

### Step 7 — Bridge Agevolazioni (DIFFERENZIANTE)

Per ogni problema con impatto > 30%, mappa a strumenti di finanza agevolata applicabili.

1. Invoca la skill `matching-bandi-agevolazioni` con dimensione PMI + regione + settore
2. Filtra strumenti pertinenti a digitalizzazione/web/marketing:
   - **Voucher PNRR Digitalizzazione PMI** (regionale)
   - **Bonus Pubblicita** (se investimento > 10K EUR in pubblicita incrementale)
   - **Credito d'imposta R&S/Innovazione** (se sviluppo sito custom o app)
   - **Nuova Sabatini** (se acquisto hardware/software)
   - **Transizione 5.0** (se digitalizzazione + sostenibilita)
   - **Bandi camerali Punto Impresa Digitale** (regionali)
3. Per ogni strumento applicabile: % copertura, tetto massimo, finestra apertura, link
4. **Calcolo de minimis residuo** se applicabile via skill `calcolo-de-minimis`

Output: tabella "Problema → Soluzione → Costo stimato → Bando applicabile → Quota finanziabile"

Mapping problemi → bandi: `references/bandi-digitalizzazione-pmi.md`

### Step 8 — Generazione report DOCX

Struttura report (14-20 pagine):

1. **Copertina** + dati progetto (URL, settore, regione, data)
2. **Executive Summary 1 pagina** per il titolare:
   - Score globale 0-100 (composito: tecnico + AI + Local)
   - Top 3 criticita
   - Stima traffico perso (se applicabile)
   - **Stima agevolazioni recuperabili in EUR** (numero forte!)
3. **Metodologia** (1 pagina)
4. **Diagnosi tecnica** (4-5 pagine):
   - Performance & Core Web Vitals
   - Mobile & Crawlability
   - On-page & Schema
   - Riferimento update Google penalizzanti
5. **AI Search readiness 2025** (2 pagine, DIFFERENZIANTE) — score 10 punti + raccomandazioni
6. **Local SEO Italia** (3-4 pagine, DIFFERENZIANTE):
   - GBP score + azioni
   - NAP consistency tabella 8 directory
   - Recensioni & reputation
   - Citations italiane
7. **Matrice priorita** (impatto x sforzo)
8. **Piano d'azione** ordinato per priorita con istruzioni operative
9. **Bridge Agevolazioni** (2-3 pagine, DIFFERENZIANTE):
   - Tabella problema → bando applicabile
   - Stima totale finanziabile
   - Prossimi passi per accesso bando
10. **KPI da monitorare post-intervento**
11. **Appendici**: dati raw Lighthouse, screenshot, dettaglio NAP, JSON

Template: `assets/template-report-audit.md` (aggiornato a v3)

Invoca la skill `docx` per la generazione del DOCX. Output JSON strutturato secondo `schemas/output-schema.json`.

## Severita dei problemi

| Severita | Definizione | Esempio |
|----------|-------------|---------|
| Critico | Impedisce indicizzazione o rende il sito inutilizzabile | Sito HTTP, robots.txt blocca tutto, LCP > 10s, GBP non verificato |
| Importante | Penalizza significativamente posizionamento | Title mancanti, no mobile-friendly, CLS > 0.25, NAP divergente, no schema LocalBusiness |
| Minore | Opportunita di miglioramento | Alt tag su decorative, meta desc corta, Q&A GBP senza risposta |

## Tono e linguaggio

- **Professionale ma accessibile**: il titolare deve capire l'executive summary senza aiuto tecnico
- **Due livelli di lettura**: executive summary in italiano semplice per il titolare, dettaglio tecnico per il webmaster
- **Istruzioni operative concrete**: riferimenti a CMS specifici (WordPress, Joomla, Shopify, PrestaShop, Wix), nomi esatti dei menu
- **Quantificazione**: stimare impatto in traffico/clienti quando possibile

## Tiering output (pricing modulare)

| Versione | Prezzo | Cosa include |
|---|---|---|
| **Light** | Free (lead magnet) | Score 0-100 + top 5 problemi (no AI, no Local, no Bridge) |
| **Standard** | 99 EUR | Audit completo + AI readiness + Local SEO + Bridge Agevolazioni |
| **Pro** | 199 EUR | Standard + 30 min call review + 1 follow-up dopo 60gg |

Light alimenta lead generation, Standard e il prodotto di default, Pro e l'upsell con accompagnamento.

## Skill invocate

- `matching-bandi-agevolazioni` — mapping problemi → bandi italiani
- `calcolo-de-minimis` — verifica plafond residuo
- `digital-marketing-performance` — benchmark di settore
- `docx` — generazione report DOCX finale

## Deliverable

1. **Report DOCX** (14-20 pagine) — documento professionale con diagnosi e piano d'azione
2. **JSON strutturato** — dati completi audit machine-readable (`schemas/output-schema.json`)

## Differenziazione finale (copy marketing)

> "L'audit SEO che non ti lascia con una lista di problemi, ma con la lista dei **bandi italiani che possono pagarli** — e ti dice se **ChatGPT ti cita**. Per PMI 5-50 dipendenti che vogliono crescere su Google e sugli LLM senza buttare 3000 EUR in agenzie. 99 EUR, 5 minuti, DOCX 18 pagine, esempio reale scaricabile."

## Note implementative

- Invocando `matching-bandi-agevolazioni`, passa SEMPRE settore + regione + dipendenti del cliente
- Per il GBP score, analisi visuale via `WebFetch` su `google.com/maps/place/...` (no API senza autorizzazione)
- Per NAP consistency, fetch reali delle directory; segna "non verificato" se non rispondono
- Per AI-readiness, oltre alla checklist statica, esegui query brand reali su ChatGPT/Perplexity (via `WebSearch` quando possibile)
- "Stima agevolazioni recuperabili in EUR" e la metrica marketing piu forte — tienila **conservativa** per non over-promising
- Ogni problema diagnosticato dovrebbe (dove sensato) referenziare l'update Google correlato — aiuta il titolare a capire perche oggi e un problema

## File di supporto

Esistenti:
- `references/benchmark-core-web-vitals.md`
- `references/checklist-audit-completa.md`
- `references/seo-ai-search-2025.md`
- `references/evoluzione-algoritmo-google.md`
- `assets/template-report-audit.md`
- `schemas/output-schema.json`

Da creare (stub iniziali):
- `references/checklist-local-seo-italia.md` — 40 item checklist Local SEO
- `references/directory-italiane-nap.md` — 8+ directory italiane con priorita
- `references/bandi-digitalizzazione-pmi.md` — mapping problemi → bandi

---

Aggiornato: 2026-05-04 — v3 merge: integrati Local SEO Italia + Bridge Agevolazioni + tiering esplicito (da v2 proposta) mantenendo AI Search readiness + lettura storica algoritmo Google (da v1).
