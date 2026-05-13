---
name: seo-italia
description: >
  SEO operativa per mercato italiano: Google.it, Google Business Profile (GBP), Search Console,
  recensioni Google/Trustpilot, directory italiane (PagineGialle, Yelp IT, Europages, Kompass,
  Trovaprezzi, Pagine Bianche, Misterimprese). Local SEO (local pack, NAP consistency, citazioni
  locali, schema LocalBusiness), SEO multilingua IT/EN, GDPR-compliant tracking (Consent Mode v2,
  server-side tagging, cookie banner art. 122 Codice Privacy), Google Analytics 4 configurazione
  IT. AI SEO / GEO (Generative Engine Optimization): ottimizzazione per risposte in ChatGPT,
  Perplexity, Google AI Overview, SGE, Gemini, Copilot. Structured data avanzato (FAQPage,
  HowTo, Product, Article, Organization, Breadcrumb, LocalBusiness, Review, AggregateRating).
  E-E-A-T applicato a siti italiani (trasparenza, autore, credenziali, partita IVA visibile,
  contatti). SERP italiane specifiche (featured snippet IT, People Also Ask IT, knowledge
  panel aziende italiane). Usa SEMPRE per: "SEO sito italiano", "ottimizzare Google My Business",
  "apparire in ChatGPT", "AI Overview visibility", "schema markup italiano", "consent mode Italia",
  "local SEO Italia", "directory italiane", "GEO generative optimization", "Google.it ranking",
  "recensioni Google per SEO". Per SEO internazionale generica → usa digital-marketing-performance.
---

# SEO Italia — Operativa 2026

Skill dedicata alla SEO nel mercato italiano: local, technical, contenuto, AI SEO (GEO), conformità GDPR. Complementa `digital-marketing-performance` (che copre SEO internazionale generica) con il contesto specifico Italia 2026.

---

## Quando usare questa skill

- Siti rivolti a utenza italiana (B2C o B2B locale)
- Attività con presenza fisica (ristoranti, studi professionali, negozi, showroom)
- Aziende italiane che vogliono apparire nelle risposte AI (ChatGPT/Perplexity/Google AI Overview)
- Audit siti italiani per conformità GDPR + SEO
- Migrazioni, rebranding, internazionalizzazione EN da base IT

Per SEO internazionale pura, tattiche generiche on-page, technical SEO universale → `digital-marketing-performance`.

---

## 1. Local SEO Italia

### Google Business Profile (ex Google My Business)

Il profilo GBP è il driver #1 della local visibility. Ottimizzazione checklist:

| Elemento | Best practice IT |
|---|---|
| **Ragione sociale** | Esatta come da Visura camerale (no keyword stuffing: è motivo di sospensione) |
| **Categorie** | 1 primaria + fino a 9 secondarie. Scegliere la più specifica (es. "Pizzeria napoletana" non "Ristorante") |
| **Indirizzo** | Esatto, formato italiano (Via XYZ, 12 – 20121 Milano MI) |
| **Telefono** | Fisso italiano preferibile; numero mobile italiano ok. Verifica NAP ovunque |
| **Orari** | Includere orari festivi italiani (Pasqua, 1 maggio, Ferragosto, Natale) |
| **Foto** | Min 10 foto realistiche. Geotaggate (EXIF GPS). Logo + copertina + interno + team + prodotti |
| **Post** | Pubblicare settimanalmente. Offerte, eventi, novità |
| **Recensioni** | Target: ≥ 50 recensioni, media ≥ 4,5. Rispondere a TUTTE entro 48h (anche positive) |
| **Q&A** | Seedare le FAQ più frequenti con risposta ufficiale |
| **Attributi** | Wi-Fi, accessibilità disabili, pagamenti accettati, menu online — compilare tutti |
| **Servizi / Prodotti** | Lista dettagliata con prezzi quando possibile |

### NAP Consistency e citazioni

NAP (Name, Address, Phone) deve essere identico su:
- Sito (footer + pagina contatti + schema LocalBusiness)
- Google Business Profile
- Directory italiane principali (vedi sotto)
- Social (Facebook, Instagram, LinkedIn)
- Recensioni (TripAdvisor, TheFork, Booking se applicabile)

Verifica con tool: BrightLocal, Whitespark, oppure manuale via Google "Nome azienda + Via".

### Directory italiane da censire (priorità)

| Directory | Rilevanza | Settore |
|---|---|---|
| PagineGialle.it | Alta | Generalista |
| PagineBianche.it | Media | Generalista |
| Virgilio.it / Tuttocitta | Media | Generalista |
| Misterimprese.it | Media | B2B |
| Europages / Kompass | Alta | B2B internazionale |
| TripAdvisor | Altissima | Ristoranti, hotel, attrazioni |
| TheFork | Alta | Ristoranti |
| Booking.com | Altissima | Hotel, B&B |
| Trovaprezzi.it | Altissima | E-commerce IT |
| Idealo.it | Alta | E-commerce IT |
| Dovecomodovado / Paginesi | Bassa | Generalista |
| Google Maps | Altissima | Tutti |
| Apple Maps | Media | Tutti (crescente) |
| Bing Places | Bassa | Tutti |

### Schema LocalBusiness

```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Ragione Sociale SRL",
  "image": "https://example.it/foto.jpg",
  "@id": "https://example.it",
  "url": "https://example.it",
  "telephone": "+39 02 1234567",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Via Roma 12",
    "addressLocality": "Milano",
    "postalCode": "20121",
    "addressRegion": "MI",
    "addressCountry": "IT"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 45.4642,
    "longitude": 9.1900
  },
  "openingHoursSpecification": [...],
  "priceRange": "€€",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "reviewCount": "127"
  }
}
```

---

## 2. AI SEO / GEO (Generative Engine Optimization)

**Nel 2026** gran parte delle ricerche informazionali avviene su ChatGPT, Perplexity, Google AI Overview, Gemini, Copilot. Essere citati in queste risposte è SEO di prima fascia.

### Cosa fanno i motori generativi per scegliere le fonti

1. **Authority + freshness**: preferiscono fonti recenti, autorevoli, con backlink da domini affidabili
2. **Structured data**: schema.org parsato direttamente (specialmente FAQPage, HowTo, Article con author)
3. **Markdown-friendly structure**: H2/H3 chiari, liste, tabelle, definizioni esplicite
4. **Claim + evidenza**: affermazioni seguite da dati/fonti verificabili
5. **Canonical URLs accessibili**: no JS-render obbligatorio, no paywall bloccante, robots.txt permissivo a user-agent AI (GPTBot, Google-Extended, PerplexityBot)

### Ottimizzazioni pratiche per GEO

**robots.txt**
```
User-agent: GPTBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: CCBot
Allow: /
```

Se vuoi escludere AI training ma restare nell'AI search, la situazione è sfumata: GPTBot è sia training che retrieval; Google-Extended è opt-out training Gemini ma NON influenza AI Overview (che usa Googlebot standard).

**Struttura contenuto GEO-friendly**
- Inizia ogni pagina con una **risposta sintetica di 40-80 parole** (il motore AI la cita direttamente)
- Usa **definizioni esplicite** ("X è Y che fa Z")
- Inserisci **tabelle comparative** (spesso citate in formato tabellare)
- Aggiungi **FAQ con schema FAQPage** (una delle strutture più parsate)
- **Data di pubblicazione e aggiornamento** visibili (meta + testo + schema)
- **Autore con pagina bio + credenziali verificabili** (E-E-A-T)

### Monitoraggio visibilità AI

Tool specifici 2026:
- **Profound** — monitora citazioni in ChatGPT, Perplexity, Google AI, Claude
- **Otterly.ai** — brand tracking in LLM
- **HubSpot AI Search Grader** — free
- **ChatGPT Atlas / Perplexity** manuale — query test mensili su prompt tipici del cliente

KPI da tracciare:
- % di query brand dove appari nella risposta AI
- Share of Voice AI vs SERP tradizionale
- Sentiment delle citazioni
- Fonti competitor citate

---

## 3. GDPR-compliant tracking (Italia 2026)

Condizione di legittimità SEO + analytics in Italia: conformità a **Regolamento UE 2016/679**, **Codice Privacy D.Lgs. 196/2003 art. 122**, linee guida **Garante Privacy** su cookie (maggio 2021 aggiornate), provvedimenti su Google Analytics e trasferimento extra-UE.

### Cookie banner

Requisiti minimi (Garante Privacy):
- **Prima pagina non traccia** (o solo cookie tecnici)
- **Opzioni equivalenti** "Accetta tutto" / "Rifiuta tutto" / "Personalizza" (no dark pattern)
- **Granularità per finalità**: tecnici (sempre), statistici, marketing, profilazione
- **X o "chiudi" non valgono come consenso**
- **Scroll non vale come consenso**
- **Durata del consenso ≤ 6 mesi** (dopo si richiede nuovamente)
- **Informativa privacy art. 13 GDPR** raggiungibile sempre

Piattaforme CMP (Consent Management) raccomandate IT: Iubenda, OneTrust, Cookiebot, Usercentrics, Axeptio.

### Google Consent Mode v2

Obbligatorio dal marzo 2024 per usare Google Ads e GA4 con conversioni EU. 4 parametri:

| Parametro | Scope |
|---|---|
| `ad_storage` | Cookie pubblicitari |
| `analytics_storage` | Cookie analytics |
| `ad_user_data` | Invio dati utente a Google Ads |
| `ad_personalization` | Personalizzazione ads |

**Modalità basic**: tag non parte senza consenso (nessun dato).
**Modalità advanced**: tag parte in modalità "cookieless pings" che invia dati anonimi aggregati anche senza consenso (modellazione conversioni).

### Server-side tagging (GTM Server)

Vantaggi SEO + privacy:
- Prima party cookies (durata più lunga, più affidabili)
- Filtraggio dati PII prima dell'invio
- Controllo granulare su cosa esce dal server
- Bypass di parte degli adblocker
- Conformità più robusta al GDPR

Stack tipico IT 2026: GTM Web → GTM Server (Cloud Run / App Engine) → GA4 + Meta CAPI + Google Ads Enhanced Conversions.

### Google Analytics 4 in Italia

- **IP anonymization**: di default in GA4 (non serve attivarla come in UA)
- **Data retention**: impostare max 14 mesi (default) o 2 mesi per conformità
- **Google Signals**: disattivare se non giustificato (trasferimento extra-UE)
- **Eventi custom**: sì, ma evitare PII (no email, no nome, no partita IVA nei parametri)
- **Alternative GDPR-safe**: Plausible Analytics, Matomo self-hosted, SimpleAnalytics, Umami

---

## 4. E-E-A-T per siti italiani

Experience, Expertise, Authoritativeness, Trust — Google Quality Rater Guidelines applicate a contesto IT:

| Segnale | Implementazione IT |
|---|---|
| **Chi siamo reale** | Pagina con volti, nomi, ruoli, credenziali. Non solo mission statement |
| **Partita IVA / REA / ragione sociale** visibile in footer (obbligo legale ex art. 2250 c.c.) |
| **Contatti veri**: PEC + telefono italiano + indirizzo fisico con Google Maps embed |
| **Author bio**: ogni articolo firmato con pagina autore, credenziali, LinkedIn, pubblicazioni |
| **Credenziali professionali**: albo (avvocato, commercialista, ingegnere, medico) citato e linkato |
| **Privacy policy + Termini + Cookie policy** — completi, non copy-paste generici |
| **Recensioni verificate** — Google Reviews, Trustpilot, Feedaty (certificato Netcomm) |
| **Schema Organization** con sameAs ai profili social ufficiali |
| **SSL** (HTTPS obbligatorio) + WCAG 2.1 AA per PA e grandi aziende |

---

## 5. Audit SEO sito italiano — checklist

### Livello 1: Base (quick wins, 1-2 ore)
- [ ] Google Search Console configurata con proprietà dominio
- [ ] Sitemap XML generata e inviata
- [ ] robots.txt presente e coerente
- [ ] Tutte le pagine hanno title (50-60 char) e meta description (150-160)
- [ ] H1 unico per pagina
- [ ] HTTPS attivo, no mixed content
- [ ] Mobile-friendly (test Google Mobile-Friendly)
- [ ] Schema Organization presente nel footer/home
- [ ] Google Business Profile rivendicato e ottimizzato al 100%
- [ ] Cookie banner conforme Garante
- [ ] Partita IVA in footer

### Livello 2: Medium (strategic, 1-2 giorni)
- [ ] Keyword research su Google.it con intent italiano
- [ ] Mappatura keyword → URL (no cannibalizzazione)
- [ ] Pagina città/servizio per ciascuna area servita (se local)
- [ ] Schema FAQPage su 5-10 pagine core
- [ ] Schema Product / LocalBusiness / Article dove pertinente
- [ ] Core Web Vitals ≥ 75° percentile in CrUX
- [ ] Internal linking con anchor ottimizzati
- [ ] Duplicate content audit (Siteliner / Screaming Frog)
- [ ] Hreflang se multi-lingua (IT + EN)
- [ ] Consent Mode v2 configurato
- [ ] Recensioni Google: strategy di raccolta attiva

### Livello 3: Avanzato (competitive advantage, ongoing)
- [ ] AI visibility test (ChatGPT, Perplexity, Google AI Overview) con query brand + query prodotto
- [ ] robots.txt configurato per bot AI (allow/disallow motivato)
- [ ] Content hub pillar + cluster su 2-3 topic core
- [ ] Backlink profile audit (Ahrefs/Semrush)
- [ ] Digital PR strategy (menzioni su testate italiane autorevoli)
- [ ] Server-side tagging GTM
- [ ] Monitoring AI citations con tool dedicato
- [ ] Local citations in 10+ directory IT rilevanti
- [ ] Schema Review + AggregateRating con recensioni verificate
- [ ] Programma di link-earning (tool, guide autorevoli, ricerche originali)

---

## 6. Output template — SEO Audit Report IT

Per ogni audit, produrre report con questa struttura:

```
# SEO Audit — [Dominio] — [Data]

## Executive Summary
- Punteggio SEO attuale: X/100
- Top 3 priorità (impatto alto, effort basso)
- Conformità GDPR: [Conforme / Parziale / Non conforme]
- AI visibility: [presente / assente / parziale]

## Sezione 1: Local SEO
[GBP, NAP, directory, recensioni]

## Sezione 2: On-page IT
[Title, meta, H, contenuto, schema]

## Sezione 3: Technical
[Core Web Vitals, mobile, crawlability, SSL, HTTPS]

## Sezione 4: AI SEO / GEO
[Test citazioni in ChatGPT/Perplexity/AI Overview, robots.txt bot AI, struttura content]

## Sezione 5: GDPR / Privacy
[Cookie banner, Consent Mode, informative, trasferimenti extra-UE]

## Sezione 6: Backlink & Authority
[Domini referenti, tossici, opportunità digital PR]

## Sezione 7: Competitor
[2-3 competitor italiani diretti + 1 best-in-class]

## Piano d'azione 90 giorni
- Quick wins (settimana 1): [lista]
- Strategic (mese 1-3): [lista]
- KPI da monitorare: [GSC clicks, local pack rank, AI citations, conversioni organiche]
```

---

## Cross-skill references

- `digital-marketing-performance`: SEO/SEM generico, keyword research avanzata, email, CRO
- `it-law-privacy-ai`: GDPR, cookie, Garante, provvedimenti su GA4
- `psicologia-marketing`: CTA, trust signals, copy persuasivo su landing
- `marketing-strategico`: posizionamento e contenuto strategico
- `marketing-analytics`: modelli quantitativi attribution, mix modeling
