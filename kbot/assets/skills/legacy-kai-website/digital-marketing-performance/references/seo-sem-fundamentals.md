# SEO On-Page, Technical, Off-Page & SEM Google Ads

## Parte 1: SEO On-Page

### Title Tag
| Elemento | Specifica | Best Practice |
|----------|-----------|---|
| **Lunghezza** | 50-60 caratteri | Google tronca oltre 600px (~60 char) |
| **Keyword** | Inserisci primaria all'inizio | "Primary Keyword + Brand" meglio di "Brand + Primary Keyword" |
| **Formato** | "[Keyword] - [Benefit/USP]" | "Digital Marketing Course - Learn SEO, SEM, Content (2024)" |
| **Evita** | Keyword stuffing, tutti maiuscoli | Calo di CTR e penali |

**Esempio italiano:**
```
❌ Sbagliato: "Digital Marketing Digital Marketing Digital Marketing Roma"
✓ Corretto: "Digital Marketing Roma - Corsi SEO, SEM, Content (2024)"
```

### Meta Description
| Aspetto | Dettaglio |
|---------|---|
| **Lunghezza** | 150-160 caratteri (Google mostra 920px) |
| **Funzione** | Non è ranking factor, ma CTR driver critico |
| **CTA** | Includi call-to-action (Scopri, Leggi, Scarica) |
| **Unique** | Personalizza per ogni pagina |
| **Formati** | Per article: "Scopri [topic]... Leggi la guida completa." Per product: "Acquista [prodotto] a €[prezzo]. [Benefit]. Spedizione gratuita." |

**Benchmark CTR per meta description ottimizzata:** +20-30% vs generico

### H1, H2, H3 Structure
| Livello | Quantity | Keyword | Descrizione |
|---------|----------|---------|---|
| **H1** | 1 per pagina | Keyword primaria | Topic principale, massima relevanza |
| **H2** | 2-4 | Keyword secondaria / Long-tail | Subtopic, approfondimenti |
| **H3+** | Illimitati | Keyword correlate | Dettagli, supporto al flusso logico |

**Schema HTML:**
```html
<h1>Come Fare SEO On-Page nel 2024 (Guida Completa)</h1>
  <h2>Cosa è SEO On-Page?</h2>
    <h3>Differenza tra SEO On-Page e Off-Page</h3>
  <h2>Title Tag: Come Ottimizzare</h2>
    <h3>Lunghezza ideale del Title Tag</h3>
    <h3>Posizionamento della keyword</h3>
```

### Keyword Density & Semantic Search
| Metrica | Target | Nota |
|---------|--------|---|
| **Keyword density** | 1-2% (keyword primaria) | Non è ranking factor diretto, ma influenza relevance |
| **LSI keywords** | 5-10 varianti semantiche | Sinonimi, correlati, long-tail |
| **Keyword placement** | Title, H1, primi 100 word, alt text | Distribuzione naturale |

**Esempio:**
```
Keyword primaria: "digital marketing"
LSI: "online marketing", "digital strategy", "marketing digitale", 
     "performance marketing", "digital campaigns"

Density = 12 occorrenze / 600 parole = 2% ✓
```

### Internal Linking Strategy
| Elemento | Best Practice |
|----------|---|
| **Anchor text** | Descrittivo, contiene keyword pertinente (es. "SEO on-page" non "clicca qui") |
| **Frequency** | 2-4 link interni per articolo (dipende lunghezza) |
| **Distribuzione** | Verso pillar content, topic cluster, conversione assets |
| **Profondità** | Massimo 3 click dal homepage per pagina importante |
| **Nofollowed links** | Usa per ads, sponsorizzati, non-relevant (non passa link juice) |

**Struttura Topic Cluster:**
```
Pillar Page: "SEO Completa" (una pagina madre)
├── Cluster 1: "SEO On-Page" → internal link to pillar
├── Cluster 2: "SEO Technical" → internal link to pillar
├── Cluster 3: "Link Building" → internal link to pillar
└── Cluster 4: "Keyword Research" → internal link to pillar

Ogni cluster linkarsi tra sé (contextual) e al pillar (top della gerarchia)
```

### Keyword Density Formula
```
Keyword Density (%) = (Occorrenze keyword / Total word count) × 100

Esempio:
"digital marketing" appare 8 volte in articolo di 400 parole
= (8 / 400) × 100 = 2% ✓

Target: 1-2% (primaria), 0.5-1% (secondaria)
```

---

## Parte 2: SEO Technical

### Core Web Vitals (CWV) - Google's Page Experience Signal

| Metrica | Acronimo | Descrizione | Target | Strumento |
|---------|----------|---|---|---|
| **Largest Contentful Paint** | LCP | Tempo rendering elemento più grande (immagine/testo) | <2.5 secondi | PageSpeed Insights, Chrome DevTools |
| **First Input Delay** | FID | Tempo tra input utente e risposta browser | <100 millisecondi | Deprecated → usiamo INP |
| **Cumulative Layout Shift** | CLS | Stabilità visuale pagina (unexpected layout changes) | <0.1 | PageSpeed Insights |
| **Interaction to Next Paint** | INP | Successore di FID; responsiveness | <200 ms | Chrome DevTools, PerformanceObserver |

**Impatto SEO:** Core Web Vitals sono ranking factor. Pagine con CWV pessimi perdono posizioni vs competitor.

### LCP Optimization (Largest Contentful Paint)
```
LCP = Tempo di caricamento elemento più grande visibile above-fold

Cause di LCP lento (>2.5s):
1. Server response time (>600ms) → ottimizza backend, CDN
2. Render-blocking CSS/JS → rimuovi unused CSS, defer JS
3. Immagini non ottimizzate → compressione, lazy load, responsive images
4. Client-side rendering → pre-render, static generation

Soluzione rapida:
- Comprimi immagini: TinyPNG, ImageOptim
- Usa <picture> con srcset per responsive image
- Lazy load: <img loading="lazy">
- Abilita GZIP e Brotli compression
- Usa CDN (Cloudflare, AWS CloudFront)
```

**Checklist LCP:**
- [ ] Image <200KB in size
- [ ] Server response time <600ms (Core Web Vitals)
- [ ] CSS/JS render-blocking rimossi o deferiti
- [ ] Font display: swap (evita invisible text)
- [ ] Static assets cached con long TTL (>1 anno)

### CLS Optimization (Cumulative Layout Shift)
```
CLS score = Σ (impact fraction × distance fraction) per ogni unexpected shift

Cause:
1. Dimensioni immagini non definite → <img width="300" height="200">
2. Ads, embed, iframe senza spazio riservato
3. Font-face caricamenti asincrone
4. Animazioni che modificano layout

Fix:
<div style="aspect-ratio: 16/9;">
  <img src="hero.jpg" alt=""> <!-- Immagine responsiva -->
</div>

<ins class="adsbygoogle" style="display:block; min-height:250px;"></ins>
```

### Technical SEO Checklist

| Area | Elemento | Check |
|------|----------|-------|
| **Crawlability** | robots.txt dichiarato | [ ] Exists in root, non blocca pagine importanti |
| | Sitemap XML | [ ] sitemap.xml, video sitemap, image sitemap se rilevante |
| | Robots meta tag | [ ] "index, follow" su pagine indexabili, noindex su parametri UTM |
| **Mobile** | Viewport meta tag | [ ] `<meta name="viewport" content="width=device-width, initial-scale=1">` |
| | Mobile-friendly test | [ ] Passa Google Mobile-Friendly Test |
| | Responsive design | [ ] CSS media queries, non user-agent sniffing |
| **Struttura URL** | Canonical tag | [ ] `<link rel="canonical">` per evitare duplicate content |
| | Trailing slash | [ ] Coerente (es. sempre `/blog/` o `/blog`) |
| | HTTPS** | [ ] SSL certificate valido, redirect HTTP→HTTPS |
| **Schema.org** | JSON-LD markup | [ ] Article, Product, BreadcrumbList, Organization |
| | Structured data test | [ ] Passa Rich Results Test (Google) |
| **Velocity** | Page load <3s | [ ] Core Web Vitals all "Good" |
| | Gzip compression | [ ] Abilita su web server |
| **Indexing** | Search Console | [ ] URL coverage 0 errori, sitemap inviata |
| | No crawl errors | [ ] 0 4xx/5xx in Search Console |

---

## Parte 3: SEO Off-Page & Link Building

### Backlink Quality Metrics

| Metrica | Descrizione | Fonte | Target |
|---------|---|---|---|
| **Domain Authority (DA)** | 1-100 score, autorità complessiva dominio (Moz) | Moz Link Explorer | >30 backlink da siti DA>30 |
| **Page Authority (PA)** | 1-100 score, autorità specifica pagina | Moz | Backlink da PA>40 più valido |
| **Domain Rating (DR)** | Scala 0-100, autorità dominio (Ahrefs) | Ahrefs | >40 DR ideale per backlink |
| **Traffic Metric (TF)** | 0-100, trust flow, affidabilità sito | Majestic | Correlato con spam; TF >40 buono |

**Regola empirica:** 1 backlink da DA 50 = 10 backlink da DA 30

### Anchor Text Diversity
| Tipo | Esempio | Distribuzione Target | Nota |
|------|---------|---|---|
| **Branded** | "Agenzia Digital Marketing" | 20-30% | Brand name |
| **Keyword exact match** | "corso SEO Roma" | 10-15% | Exatta, rischio over-optimization |
| **Keyword partial match** | "impara digital marketing" | 20-30% | LSI keyword variation |
| **Generic (URL)** | "www.example.com", "leggi di più" | 30-40% | Neutral, natural |
| **Branded + keyword** | "corso digital marketing Roma" | 5-10% | Branded + contextual |

**Distribuzione "naturale" di anchor text (algoritmo Penguin controlla abuse):**

```
100 backlink example:
- Branded (25 link): 25%
- Partial match (30 link): 30%
- Generic (35 link): 35%
- Exact match (10 link): 10%
```

### Link Building Strategie

| Tattica | Difficoltà | ROI | Timeline |
|---------|-----------|-----|----------|
| **Broken link building** | Bassa | Alta | 1-3 settimane |
| **Competitor backlink analysis** | Bassa | Medio | 2-4 settimane |
| **Digital PR / Guest posting** | Media | Alta | 1-3 mesi |
| **Skyscraper technique** | Media | Alta | 2-6 settimane |
| **Link reclamation** (unlinked mentions → link) | Bassa | Media | 1-2 settimane |

**Broken Link Building Process:**
```
1. Identifica competitor's backlink con tool (Ahrefs, SEMrush)
2. Controlla se link è broken (404 error)
3. Scopri contenuto simile tuo sito
4. Contatta webmaster: "Ho notato link rotto a [URL]. 
   Ecco alternativa rilevante: [il tuo link]"
5. ~30-40% conversion rate
```

---

## Parte 4: SEM - Google Ads Account Structure & Quality Score

### Google Ads Account Hierarchy
```
Account (1 per cliente)
├── Campaign 1 (e.g., "Brand Keywords")
│   ├── Ad Group 1 (e.g., "Exact Match Brand")
│   │   ├── Keyword 1: [marchio]
│   │   ├── Keyword 2: [brand name]
│   │   └── Ad Copy (1-3 ads per rotation)
│   └── Ad Group 2 (e.g., "Phrase Match Brand")
│       ├── Keyword: "marchio" (phrase match)
│       └── Ad Copy
├── Campaign 2 (e.g., "High-Intent Non-Brand")
│   ├── Ad Group 1 (e.g., "Competitor Keywords")
│   │   ├── Keyword: "competitor name"
│   │   └── Ad Copy
│   └── Ad Group 2 (e.g., "Generic High-Volume")
│       ├── Keyword: "digital marketing course"
│       └── Ad Copy
└── Campaign 3 (e.g., "Remarketing")
    ├── Ad Group 1 (e.g., "Cart Abandoners")
    └── Ad Group 2 (e.g., "High-Value Visitors")
```

**Principio:** Raggruppa keyword con intent simile e copy cohesivo. Ad Group specifico = QS più alto.

### Keyword Match Types

| Tipo | Sintassi | Esempi di Match | Reach | CPC | QS Impact |
|------|----------|---|---|---|---|
| **Broad Match** | `keyword` | "digital marketing", "learning online marketing", "marketing courses" | Altissimo (~200% vs broad) | Basso | ⬇️ Rischio QS basso |
| **Broad Match Modified** | `+digital +marketing` | Deve contenere tutte parole (any order) | Alto (~80%) | Medio | ⬆️ Meglio del broad |
| **Phrase Match** | `"digital marketing"` | "best digital marketing", "digital marketing course", "digital marketing for beginners" | Medio | Medio-Alto | ⬆️ QS medio-alto |
| **Exact Match** | `[digital marketing]` | Esattamente "digital marketing" o prossimo match (sinonimi) | Basso (~20% vs broad) | Alto | ⬆️ QS più alto |

**Strategia di match type:**
```
Fase 1 (Test): Usa broad match modified + negative keywords aggiunti
Fase 2 (Scale): Aggiungi phrase match per keyword ad alto volume
Fase 3 (Optimize): Scala exact match su keyword performer top

Goal: Massimizzare quality score = ridurre CPC per stesso ranking.
```

### Quality Score (QS) Formula & Optimization

```
Quality Score (scala 1-10) = f(
  A) Expected Click-Through Rate (CTR) → 40% della formula
  B) Ad Relevance → 40% della formula
  C) Landing Page Experience → 20% della formula
)

Calcolo indicativo:
QS = (CTR_relevance_score × 0.4) + (Ad_relevance_score × 0.4) + (LP_experience × 0.2)

Scala scoring per componente:
Below Average / Average / Above Average
```

**CTR Component (40%):**
```
Expected CTR per keyword si calcola in base a:
1. Historical CTR tuo account per simili keyword
2. CTR competitor per stessa keyword (Google sa)
3. Position (rank) ad in SERP

Optimization:
✓ Ad copy con keyword in headline (match intent)
✓ Unique selling point in description
✓ Clear CTA ("Scopri", "Acquista", "Registrati")
✓ Ad extensions (sitelinks, callout, structured snippet)
```

**Ad Relevance Component (40%):**
```
Google valuta:
1. Keyword ↔ Ad copy rilevanza (matcher algoritmo)
2. Keyword ↔ Ad group altri keyword coerenza

Optimization:
✓ Includi keyword esatta in headline (almeno una variante)
✓ Usa dynamic keyword insertion {keyword}
✓ Ad group monotemica (max 10-15 keyword per ad group)
✓ Scrivi copy specifico per intent keyword

Esempio:
❌ Ad group "Corsi marketing" contiene "SEO", "SEM", "Email", "Content"
   → Ad copy generico "Corsi Marketing Online"
   
✓ Ad group "Corsi SEO" contiene "corsi SEO", "learn SEO", "SEO tutorial"
   → Ad copy specifico "Corso SEO Avanzato - Certificato"
```

**Landing Page Experience (20%):**
```
Google valuta via PageSpeed Insights + manuale:
1. Page load speed (Core Web Vitals: LCP <2.5s)
2. Mobile-friendly design
3. Relevance: pagina corrisponde ad copy + keyword intent
4. Transparency: trust signals (contatti, privacy policy, testimonial)
5. Ease of navigation: clear CTA above fold

Optimization:
✓ LP load <2.5s (LCP target)
✓ Responsive mobile design
✓ CTA button above fold, colore contrastante
✓ Trust signals: testimonial, SSL, privacy/returns policy
✓ Minimal form fields (3-5 max per form)

Checklist per cada LP version:
[ ] Core Web Vitals all Green (LCP <2.5s, CLS <0.1, FID <100ms)
[ ] Mobile-friendly test passes
[ ] H1 corrisponde headline ad
[ ] CTA primaria above fold
[ ] Trust elements visibili
```

### Quality Score By Match Type (Benchmark)

| Match Type | QS Median | CTR Atteso | Primo Rank CPC |
|---|---|---|---|
| Exact Match | 7-8 | 5-8% | Baseline |
| Phrase Match | 6-7 | 3-5% | +15-25% vs exact |
| Broad Match Modified | 5-6 | 1.5-3% | +35-50% vs exact |
| Broad Match | 4-5 | 0.5-1.5% | +60-100% vs exact |

**Impatto CPC di QS basso:**
```
Stessa posizione ad (rank 1):
- QS 10/10: CPC baseline €2.00
- QS 7/10: CPC +25% = €2.50
- QS 4/10: CPC +75% = €3.50

Stessa spesa budget (€1000/mese):
- QS 10/10: 500 clicks
- QS 4/10: 286 clicks

Vantaggio QS alto = -43% click per stessa spesa
```

---

## Parte 5: SEM - Bidding Strategies

| Strategia | Best For | Requisiti Dati | Manualità | CPA Prevedibile |
|-----------|----------|---|---|---|
| **Manual CPC** | Testing, brand keywords | Nessuno | Altissima | No |
| **Enhanced CPC (eCPC)** | Campagne stabilizzate | >100 conv/mese | Alta | No |
| **Maximize Clicks** | Top of funnel, awareness | Nessuno | Bassa | No |
| **Maximize Conversions** | BOFU, con conversion tracking | >50-100 conv/mese | Nessuna | No |
| **Target Cost-Per-Acquisition (tCPA)** | Conversione-driven | >30-50 conv/mese + CPA storico | Nessuna | Sì ✓ |
| **Target Return-on-Ad-Spend (tROAS)** | Revenue-driven (e-commerce) | >30-50 conv/mese + value tracking | Nessuna | Sì ✓ |
| **Target Impression Share** | Brand awareness, defensive | Nessuno | Bassa | No |

**Decision Tree per Bidding Strategy Selection:**

```
Hai conversion data sufficiente (≥50 conversioni/mese)?
├─ NO → Manual CPC o eCPC (ottimizza QS primariamente)
└─ SÌ
   └─ Quali KPI primari?
      ├─ Conversioni (e.g., lead, iscritti) 
      │  └─ Usa tCPA → definisci target CPA accettabile
      ├─ Revenue (e-commerce, SaaS con deal value)
      │  └─ Usa tROAS → target 3-5x (e-commerce) o 4-6x (SaaS)
      └─ Top-funnel awareness
         └─ Maximize Clicks o Impression Share
```

### tCPA Strategy Deep Dive

```
Target CPA = Prezzo vendita × Gross Margin × [0.8-1.2]

Esempio:
Prodotto: €100 vendita
Gross Margin: 60%
Target CPA = €100 × 0.60 × 0.9 = €54

Regola: Google aggiusta bid per raggiungere target CPA.
Se conversione costa <€54, aumenta bid.
Se >€54, diminuisce bid.

Per attivare tCPA:
1. Configura conversion tracking (pixel, API)
2. Min 30-50 conv storico (Google consiglia 50)
3. Attiva tCPA in campaign bidding settings
4. Lascia settimana di learning prima valutazione
5. Monitora CPA settimanale vs target (tolleranza ±10%)
```

### tROAS Strategy for E-Commerce

```
Target ROAS = (Revenue desiderata / Ad Spend) 
            = Inverse di (Ad Spend / Revenue)

Esempio e-commerce:
Budget mese: €5,000
Target revenue: €20,000
Target ROAS = €20,000 / €5,000 = 4.0x

Google cerca keyword+audience combination per generare 4x ROAS.

Benchmark per industria:
- E-commerce standard: 3-4x (margen 30-40%)
- E-commerce premium: 4-5x (margin 40-50%)
- SaaS (free trial): 4-6x (alta LTV)
- B2B (lead gen): 5-8x (con sales follow-up)

Come configurare:
1. Setup value tracking (revenue per conversion)
2. Min 50 conv con revenue data
3. Activate tROAS in campaign
4. Attendi 2 settimane learning phase
5. Verifica ROAS weekly (accetta ±15% volatility)
```

---

## Parte 6: Keyword Research Framework

### Keyword Research Tools Comparison

| Tool | Pricing | Specialty | Best For |
|------|---------|-----------|---|
| **Ahrefs** | $99-999/mese | Backlinks, keyword difficulty, SERP features | Competitive analysis, domain authority |
| **SEMrush** | $120-450/mese | Full suite SEO+SEM, competitor tracking | SEM bidding, content gap, PPC ideas |
| **Google Keyword Planner** | Gratis (Google Ads account richiesto) | Google official, Impressions + CTR historico | Long-tail ideation, CPC bidding |
| **Moz Keyword Explorer** | $99-799/mese | Keyword difficulty, SERP feature forecast | Mid-range keyword difficulty, quick analysis |
| **Ubersuggest** | $12-40/mese | Affordable, SEO + UX | Budget-conscious, content ideas |

### Keyword Research Metrics

| Metrica | Definizione | Sorgente | Interpretazione |
|---------|---|---|---|
| **Search Volume (SV)** | Ricerche medie mese | Keyword Planner, Ahrefs, SEMrush | Volume >1000/mese = rilevante; <100 = niche |
| **Keyword Difficulty (KD)** | 0-100 score, difficoltà ranking | Ahrefs, SEMrush, Moz | <20 = facile, 20-50 = medio, >50 = difficile |
| **Cost-Per-Click (CPC)** | Prezzo medio per click SEM | Keyword Planner, SEMrush | Proxy per commercial intent; >€1 = high-intent |
| **Competition (Adwords)** | Low/Medium/High (SEM competition) | Keyword Planner | High = competitor saturation, difficile ranking |
| **Search Intent** | Informational / Navigational / Transactional / Commercial | Manuale SERP analysis | Critical per content strategy |

### Search Intent Classification

| Intent | Definizione | Segnali | Esempio | Content Type |
|--------|---|---|---|---|
| **Informational** | Ricerca consapevolezza / educazione | Query question ("how to", "what is", "best practices") | "come fare SEO" | Blog article, guide, tutorial |
| **Navigational** | Ricerca marchio specifico | Query con brand name | "Google Analytics" | Product page, brand site |
| **Transactional** | Intento d'acquisto | "buy", "price", "discount", product name | "corsi SEO online a Roma" | Product page, pricing page, landing page |
| **Commercial** | Ricerca pre-acquisto, comparison | "best", "review", "vs", "comparison" | "Ahrefs vs SEMrush" | Comparison, review, buying guide |

**Strategia:** Allinea content type a intent per massimizzare CTR organico e conversion.

### Keyword Research Process (Top-Down)

```
Step 1: Seed Keywords
→ Brainstorm 10-15 keyword idea seed
  "digital marketing course"
  "SEO training"
  "SEM Google Ads"

Step 2: Expand with Tools
→ Ahrefs / SEMrush keyword suggestion
  Aggiunge varianti: "best digital marketing course", 
                      "online digital marketing certification"

Step 3: Filter & Analyze
→ Filtra per:
  - Search Volume ≥500/mese (visibility minima)
  - KD ≤50 (ranking fattibile)
  - CPC ≥€0.50 (commercial intent)
  → Cluster per intent

Step 4: Competitor Benchmark
→ Analizza competitor top-ranking
  - Quante keyword rank? (Ahrefs, SEMrush)
  - Quali pagina types (article, product, category)?
  - Content depth (word count, H2 count)?

Step 5: Content Mapping
→ Definisci:
  - Pillar page (main topic, broad)
  - Cluster pages (sub-topics, long-tail)
  → Internal link strategy

Example output:
```
| Keyword | SV | KD | CPC | Intent | Content Type | Page |
|---------|-----|-----|-----|--------|---|---|
| "digital marketing" | 9,900 | 82 | $1.50 | Commercial | Pillar + guide | /digital-marketing |
| "digital marketing course" | 5,400 | 35 | $1.20 | Transactional | Comparison | /courses-comparison |
| "how to do digital marketing" | 1,200 | 15 | $0.80 | Informational | Blog article | /blog/how-to-digital-marketing |
| "digital marketing for small business" | 880 | 28 | $1.10 | Transactional | Guide | /small-business-digital-marketing |

---

## Parte 7: Content SEO - Pillar + Cluster Model

### Pillar Page Strategy (Topic Authority)

**Pillar page** = Pagina comprensiva, 2,000+ parole, che copre topic macro.

Caratteristiche:
```
Title: "Digital Marketing: Guida Completa 2024" (SEO on-page ottimizzato)
H1: "Digital Marketing: Cos'è, Strategie e Best Practices"
Word count: 2,000-3,000 parole
Covers: Definizione, storia, components (SEO/SEM/Email/Social), best practices, ROI

Internal linking: Rimanda a tutti cluster pages (topic cluster)
```

### Topic Cluster Architecture

```
PILLAR: "Digital Marketing Completa"
├── CLUSTER 1: "SEO" → Pillar links to cluster ("Impara SEO"), cluster links back
├── CLUSTER 2: "SEM Google Ads" → Internal links
├── CLUSTER 3: "Email Marketing" → Internal links
├── CLUSTER 4: "Social Media Marketing" → Internal links
└── CLUSTER 5: "Content Marketing" → Internal links

Ogni cluster (500-1000 parole) approfondisce subtopic.
Pillar (2000+ parole) fornisce overview + rimanda a cluster per dettagli.

Vantaggio:
- Google riconosce "topic authority" su dominio
- Cluster page ranking migliore grazie pillar linker autorevole
- Migliore CTR da featured snippet (pillar position zero)
```

### E-E-A-T Framework per Content Quality

| Attributo | Descrizione | Implementazione |
|-----------|---|---|
| **Experience** | Autore ha esperienza diretta con topic | "10+ anni consulente marketing digitale" + case study |
| **Expertise** | Competenze tecniche + credenziali | Certificazioni (Google Analytics, HubSpot), università, pubblicazioni |
| **Authoritativeness** | Riconoscimento industria + backlink | Featured su media autorevoli, speaking conference, citazioni |
| **Trustworthiness** | Trasparenza, GDPR, SSL, contatti | Author bio, privacy policy, clear contact form, updated regularly |

**Checklist E-E-A-T per pagina:**
- [ ] Author bio con foto + descrizione esperienza (E, E)
- [ ] Author credentials link esterno (E)
- [ ] 2-3 backlink da siti DA>50 (A)
- [ ] Pubblicato da 6+ mesi (T, trust = consistency)
- [ ] Aggiornato ultimi 3 mesi (T, freshness)
- [ ] SSL certificate (T)
- [ ] Privacy policy + terms (T)
- [ ] Contact email / form (T, accessibility)
- [ ] No grammatical errors (T, professionalism)

---

## Parte 8: Technical SEO Audit Checklist

### Crawlability & Indexation

- [ ] **robots.txt** esiste e non blocca pagine crawlabili
  ```
  User-agent: *
  Disallow: /admin/
  Disallow: /private/
  Allow: /
  Sitemap: https://example.com/sitemap.xml
  ```

- [ ] **sitemap.xml** inviato Search Console
  - [ ] Include tutte pagine importanti (URL structure, last modified)
  - [ ] Video sitemap (se video content)
  - [ ] Image sitemap (se immagini rilevanti)

- [ ] **robots meta tag** per ogni pagina
  - [ ] Pagine indexabili: `<meta name="robots" content="index, follow">`
  - [ ] Pagine filtered (parametri): `noindex, follow`
  - [ ] Pagine non-sensitive: `index, nofollow` (indexa ma non propaga link)

- [ ] **URL parameters** gestiti
  - [ ] Parametri UTM dichiarati in Search Console → "Crawl parameters"
  - [ ] Evita crawl duplicate parameter (session ID, etc.)

### On-Page SEO Checklist

- [ ] **Title tag** 50-60 char, keyword primaria, unique
- [ ] **Meta description** 150-160 char, CTA, unique
- [ ] **H1** singolo, keyword primaria, rilevanza
- [ ] **H2-H3** logica gerarchica, LSI keyword
- [ ] **Canonical tag** per evitare duplicate
  ```html
  <link rel="canonical" href="https://example.com/canonical-page">
  ```
- [ ] **Internal links** 2-4 per pagina, anchor text descrittivo
- [ ] **Alt text** immagini describe contenuto (keyword rilevante, non stuffing)

### Technical Performance Checklist

- [ ] **Core Web Vitals**
  - [ ] LCP <2.5s (verde in PageSpeed)
  - [ ] CLS <0.1 (stabile layout)
  - [ ] INP <200ms (responsiveness)

- [ ] **Mobile-friendly**
  - [ ] Viewport meta tag configurato
  - [ ] Responsive CSS (no fixed widths)
  - [ ] Passa Google Mobile-Friendly Test

- [ ] **HTTPS/SSL**
  - [ ] Certificato valido, non expired
  - [ ] Redirect HTTP → HTTPS con 301 permanent
  - [ ] Mixed content warning assente

- [ ] **Server response time**
  - [ ] <600ms TTFB (time to first byte)
  - [ ] Utilizza CDN per asset statici

- [ ] **Compression & caching**
  - [ ] Gzip enabled per testo
  - [ ] Brotli compression per font
  - [ ] Browser cache >30 giorni per static assets

### Structured Data Checklist

- [ ] **JSON-LD** markup per:
  - [ ] **Article** (news, blog)
    ```json
    {
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "...",
      "image": "...",
      "datePublished": "2024-01-15",
      "author": {
        "@type": "Person",
        "name": "John Doe"
      }
    }
    ```
  - [ ] **Product** (e-commerce)
  - [ ] **LocalBusiness** (location-based)
  - [ ] **BreadcrumbList** (navigation)
  - [ ] **Organization** (homepage)

- [ ] **Validazione** con Google Rich Results Test

### Security Checklist

- [ ] No malware detected (Google Safe Browsing)
- [ ] reCAPTCHA (if forms present) non blocca crawling
- [ ] No weak password fields (password input secured)

### Common Technical Issues & Fixes

| Problema | Causa | Fix |
|----------|------|-----|
| Low crawl rate | robots.txt over-restrictive | Remove Disallow per crawlabili pages |
| Duplicate content | Trailing slash inconsistency | Declare canonical, redirect one version |
| Slow LCP | Large unoptimized image | Compress, lazy load, use CDN |
| CLS shifts | No image dimensions | Add width/height attributes |
| Low mobile score | Fixed width layout | Convert to responsive CSS grid/flex |

---

## Summary: SEO + SEM Roadmap (12 Weeks)

| Fase | Settimane | Azioni | Owner |
|------|-----------|--------|-------|
| **Audit** | 1-2 | Technical SEO audit, QS analysis, keyword gap analysis | SEO Specialist |
| **Quick Wins** | 2-3 | Fix Core Web Vitals, meta tags, internal linking | Dev + SEO |
| **Keyword Strategy** | 3-4 | Keyword research, content mapping, pillar+cluster plan | SEO Strategist |
| **Content Production** | 4-8 | Write pillar + cluster pages, optimize for E-E-A-T | Content Team |
| **Link Building** | 4-12 | Outreach, guest posting, PR | Outreach |
| **SEM Optimization** | 1-12 | QS >7 target, match type optimization, tCPA/tROAS | SEM Specialist |
| **Monitor & Iterate** | Ongoing | Rankings, CTR, conversion, DA/PA | Analytics |
