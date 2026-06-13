---
name: audit-seo-tecnico
description: >-
  Audit SEO tecnico approfondito per PMI italiane. Genera report DOCX 10-15 pagine con diagnosi
  completa e istruzioni operative per il webmaster. Trigger: "audit SEO", "audit tecnico sito",
  "problemi SEO", "il sito non si posiziona", "analisi SEO completa", "perche non mi trova Google",
  "verifica SEO", "SEO check approfondito", "report SEO tecnico". Input: URL sito, settore
  (opzionale), note specifiche (opzionale). Analizza crawlability, indicizzazione, Core Web Vitals,
  performance, mobile, sicurezza, on-page, immagini, struttura URL, schema markup. Per ogni problema:
  severita, impatto traffico, istruzione operativa concreta per il webmaster. Output: report DOCX
  executive con summary per titolare e dettaglio tecnico per webmaster, piu JSON strutturato.
  Secondo livello scala valore consulenza web PMI dopo il pagellino SEO rapido.
allowed-tools:
  - WebFetch
  - WebSearch
  - fetch_page_content
  - fetch_sitemap
  - lighthouse_audit
---

# audit-seo-tecnico

Audit SEO tecnico approfondito per PMI italiane: report DOCX 10-15 pagine con diagnosi completa e istruzioni operative per il webmaster.

## Panoramica

Questa skill esegue un audit SEO tecnico completo su un sito web di una PMI italiana. Produce un report professionale DOCX con due livelli di lettura: un executive summary di 1 pagina per il titolare e il dettaglio tecnico completo per il webmaster o l'agenzia web. Ogni problema individuato include severita, impatto stimato sul traffico e istruzioni operative concrete (non generiche).

Si posiziona come secondo livello della scala di valore della consulenza web PMI (249-349 EUR), destinato al cliente che ha visto i problemi nel pagellino SEO rapido e vuole capire come risolverli.

## Input

| Parametro | Obbligatorio | Descrizione |
|-----------|:------------:|-------------|
| URL sito | Si | URL della homepage del sito da analizzare |
| Settore | No | Settore merceologico (per benchmark specifici) |
| Note | No | Problematiche specifiche segnalate dal cliente |

## Workflow

### Step 1 — Crawl e analisi struttura sito

- Fetch homepage e pagine principali (max 20 pagine)
- Analisi struttura navigazione, profondita click, orphan pages
- Verifica sitemap.xml e robots.txt
- Mappa delle URL e relazioni interne

**Modalita consulenziale**: `WebFetch` per scaricare le pagine, `WebSearch` per verifiche esterne.
**Modalita piattaforma**: `fetch_page_content`, `fetch_sitemap`.

### Step 2 — SEO tecnico

Analisi approfondita di:
- **HTTPS e sicurezza**: certificato SSL, mixed content, HSTS
- **Velocita e performance**: Core Web Vitals (LCP, INP, CLS), TTFB, compressione, caching, immagini, lazy loading, JS render-blocking
- **Mobile**: responsive design, viewport, tap target, font size, mobile-first indexing
- **Crawlability**: robots.txt, sitemap.xml, noindex/nofollow, canonical, redirect chain, 404, crawl budget
- **Indicizzazione**: stato indicizzazione, pagine indicizzate vs totali, canonical duplicati

Riferimento benchmark: `references/benchmark-core-web-vitals.md`

**Modalita piattaforma**: `lighthouse_audit` per dati performance.

### Step 3 — SEO on-page

Analisi per ciascuna pagina crawlata:
- **Title tag**: lunghezza 50-60 char, keyword, unicita
- **Meta description**: lunghezza 150-160 char, call-to-action, unicita
- **Heading**: H1 unico per pagina, gerarchia H2-H6 corretta
- **Contenuto**: thin content, duplicate content, keyword density
- **Immagini**: alt tag, dimensioni, formati (WebP/AVIF), lazy loading
- **Internal linking**: anchor text, distribuzione link, link rotti
- **URL structure**: URL parlanti, lunghezza, parametri
- **Schema markup**: Organization, LocalBusiness, BreadcrumbList, FAQ, Product, Review

Checklist completa: `references/checklist-audit-completa.md`

### Step 4 — Analisi problemi critici e prioritizzazione

Per ogni problema trovato, assegna:
- **Severita**: critico / importante / minore
- **Impatto stimato sul traffico**: percentuale stimata di traffico organico perso o non acquisito
- **Area**: crawlability, performance, mobile, sicurezza, on-page, immagini, struttura, schema
- **Istruzione operativa concreta**: non "ottimizza i title tag" ma "vai su WordPress > Aspetto > Editor > header.php e modifica il tag title, oppure installa il plugin Yoast SEO, vai su SEO > Titoli e Metadati, e compila il campo Titolo SEO per la pagina X"

Costruisci la **matrice impatto x sforzo** per prioritizzare:
- Quick win (alto impatto, basso sforzo) — fare subito
- Progetti importanti (alto impatto, alto sforzo) — pianificare
- Miglioramenti facili (basso impatto, basso sforzo) — quando possibile
- Deprioritizzare (basso impatto, alto sforzo) — rimandare

### Step 5 — Generazione report DOCX

Genera il report seguendo il template in `assets/template-report-audit.md`:
1. Copertina con dati progetto
2. Executive Summary (1 pagina per il titolare)
3. Metodologia
4. Diagnosi per area con score, problemi e istruzioni operative
5. Matrice priorita (impatto x sforzo)
6. Piano d'azione ordinato per priorita
7. KPI da monitorare post-intervento
8. Appendice tecnica

Invoca la skill `docx` per la generazione del file DOCX.

Output JSON strutturato secondo lo schema in `schemas/output-schema.json`.

## Severita dei problemi

| Severita | Definizione | Esempio |
|----------|-------------|---------|
| Critico | Impedisce indicizzazione o rende il sito inutilizzabile | Sito HTTP, robots.txt che blocca tutto, LCP > 10s |
| Importante | Penalizza significativamente il posizionamento | Title tag mancanti, no mobile-friendly, CLS > 0.25 |
| Minore | Opportunita di miglioramento | Alt tag mancanti su immagini decorative, meta desc troppo corta |

## Tono e linguaggio

- **Professionale ma accessibile**: il titolare deve capire l'executive summary senza aiuto tecnico
- **Due livelli di lettura**: executive summary in italiano semplice per il titolare, dettaglio tecnico per il webmaster
- **Istruzioni operative concrete**: riferimenti a CMS specifici (WordPress, Joomla, Shopify, PrestaShop, Wix), schermate di riferimento, nomi esatti dei menu
- **Quantificazione**: sempre stimare l'impatto in termini di traffico/clienti quando possibile

## Skills invocate

- `digital-marketing-performance` — per benchmark di settore e riferimenti performance
- `marketing:seo-audit` — per checklist SEO di riferimento e best practice
- `docx` — per generazione del report DOCX finale

## Deliverable

1. **Report DOCX** (10-15 pagine) — documento professionale con diagnosi e piano d'azione
2. **JSON strutturato** — dati completi dell'audit in formato machine-readable (schema: `schemas/output-schema.json`)
