---
name: ecommerce-marketing-pmi
description: >
  E-commerce marketing operativo per PMI italiane. Product page optimization, CRO checkout,
  abbandono carrello avanzato, upsell/cross-sell, marketplace italiani (Amazon IT, eBay,
  Trovaprezzi, Idealo, ePrice), email lifecycle e-commerce (welcome, post-purchase,
  win-back, replenishment), Google Shopping + Performance Max, Meta Advantage+ Shopping,
  recensioni prodotto (Feedaty, Trustpilot, Yotpo) con schema Review/AggregateRating,
  subscription commerce, pricing dinamico, logistica Italia (Poste, GLS, BRT, Amazon
  Logistics). Piattaforme: Shopify, Magento, WooCommerce, Prestashop. Usa SEMPRE per:
  "e-commerce", "Amazon seller", "Shopify", "Magento", "WooCommerce", "Prestashop",
  "carrello abbandonato", "Google Shopping", "Trovaprezzi", "vendere online", "product
  page SEO", "checkout optimization", "marketplace Italia", "recensioni e-commerce",
  "logistica e-commerce", "subscription box". Per SEO generico o ads non-commerce usa
  digital-marketing-performance; per aspetti psicologici del funnel usa psicologia-marketing.
---

# E-commerce Marketing PMI

Skill operativa per il marketing e-commerce di PMI italiane. Copre l'intero funnel da acquisizione traffico a retention cliente, con focus sulle piattaforme e i marketplace dominanti in Italia 2026.

## Quando attivarla

- Cliente ha un e-commerce (Shopify, Magento, WooCommerce, Prestashop)
- Cliente vende anche/solo su marketplace (Amazon IT, eBay, Trovaprezzi, Idealo)
- Interventi su product page, carrello, checkout, subscription
- Ottimizzazione campagne Google Shopping o Meta Advantage+
- Strategia recensioni prodotto e schema markup

Per attività trasversali (SEO off-site generico, email blast non-commerce) → digital-marketing-performance.

## 1. Product page optimization

Elementi critici da validare su ogni product page:

| Elemento | Best practice IT 2026 |
|---|---|
| Gallery | 6-10 foto reali (no solo render), almeno 1 con contesto d'uso, 1 video 30" |
| Titolo prodotto | Brand + modello + caratteristica chiave (max 70 char per SEO) |
| Prezzo visibile above-the-fold | Con eventuale prezzo barrato PRECEDENTE (attenzione Omnibus Directive IT: prezzo più basso ultimi 30gg) |
| Taglie/varianti | Selettore chiaro, disponibilità live, "solo X rimasti" se vero |
| CTA primario | "Aggiungi al carrello" colore accent, sempre visibile anche scroll |
| Trust signals | Reso gratuito 30gg, spedizione, pagamento sicuro (loghi circuiti) |
| Descrizione | Bullet 3-5 benefici + descrizione lunga SEO 300+ parole |
| Schema Product + Review + AggregateRating | Obbligatori per rich snippet |
| FAQ prodotto | Schema FAQPage (rich snippet + citazione AI Overview) |
| Cross-sell | "Spesso acquistati insieme", "Potrebbe piacerti" |
| Social proof | Min 10 recensioni verificate prima del launch |

### Schema Product esempio

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Nome Prodotto",
  "image": ["url1.jpg", "url2.jpg"],
  "description": "...",
  "brand": {"@type": "Brand", "name": "Marchio"},
  "sku": "SKU-123",
  "gtin13": "1234567890123",
  "offers": {
    "@type": "Offer",
    "url": "https://example.it/prodotto",
    "priceCurrency": "EUR",
    "price": "49.90",
    "priceValidUntil": "2026-12-31",
    "availability": "https://schema.org/InStock",
    "shippingDetails": {...}
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "reviewCount": "127"
  }
}
```

## 2. Carrello e checkout CRO

**Regola generale**: ogni step del checkout perde 15-30% degli utenti. Obiettivo: ridurre step e friction.

### Checkout one-page (standard 2026)
- Form unico con sezioni visivamente separate (dati, spedizione, pagamento, riepilogo)
- Guest checkout disponibile (account opzionale dopo acquisto)
- Auto-completamento indirizzo (Google Places API)
- Campi essenziali: email, nome, indirizzo, telefono, pagamento. Nient'altro.
- Pagamenti espressi: Apple Pay, Google Pay, PayPal, Scalapay IT (BNPL)
- Validazione inline dei campi (non al submit)
- Progress indicator se obbligato ad avere 2+ step
- Trust signals cumulati: SSL, resi, assistenza, money-back

### Abbandono carrello — sequenza 3 email

| # | Timing | Subject | Contenuto chiave |
|---|---|---|---|
| 1 | +1 ora | "Hai lasciato qualcosa" | Foto prodotto + link rapido + nessuna promo |
| 2 | +24 ore | "La [prodotto] ti aspetta" | Add social proof (recensione), FAQ rapida risolve obiezione |
| 3 | +72 ore | "Ultimo reminder" | Promo 10% se valore carrello >50€, altrimenti free shipping |

Retargeting paid parallelo (Meta + Google) con dynamic product ads sui 7 giorni successivi.

### KPI checkout target

- Cart abandonment rate: benchmark 65-75%; target post-ottimizzazione <60%
- Checkout conversion rate (visit cart → purchase): 25-35% benchmark, 40%+ target
- Average order value (AOV): misurare upsell impact
- Express payment adoption: 20-40% se disponibili

## 3. Marketplace Italia

### Amazon IT

**Setup base**:
- Seller Central Italia + Vendor Central (se eligible)
- Brand Registry con marchio registrato (protezione + A+ Content + Store)
- Categorizzazione prodotto corretta (browse tree) — errore qui = -50% visibilità
- Parole chiave in titolo + bullet points + backend keywords
- Immagini 2000x2000px min, 7 immagini totali (main pura sfondo bianco + lifestyle + infografica)
- A+ Content modulare (7 moduli consigliati per tier Premium)
- FBA vs FBM: FBA se prodotto <3kg e margine >25%

**PPC Amazon Ads**:
- Sponsored Products (obbligatorio dal giorno 1)
- Sponsored Brands (solo Brand Registry, ACOS target 15-25%)
- Sponsored Display (retargeting out-of-Amazon)
- Auto campaign per discovery keyword → manual campaign su top performer

**Recensioni Amazon**:
- Programma Vine (solo Brand Registry, primi 30 recensioni)
- "Richiedi recensione" button ogni ordine (conforme TOS)
- Follow-up email post-delivery (via Feedback Genius o simili) in TOS

### eBay, Trovaprezzi, Idealo

- **eBay IT**: listing ottimizzato, Spedizione Velocissima badge, Top Rated Seller program, promozioni strutturate
- **Trovaprezzi**: feed prodotti accurato, prezzi competitivi, badge verificato, recensioni gestite
- **Idealo**: parametro prezzo+disponibilità critico, pagamento Idealo Pay opzionale

### Google Shopping + Performance Max

- Merchant Center con feed prodotti ottimizzato (titoli, descrizioni, GTIN, immagini)
- Supplemental feed per dati aggiuntivi (promozioni, personalizzazioni)
- Performance Max per e-commerce: budget minimo 50€/giorno, 2-3 asset group per categoria, customer lists first-party upload
- Smart bidding target ROAS dopo 30 conversioni
- Escludere brand keyword (handled da Search dedicato)

### Meta Advantage+ Shopping

- Commerce Manager: catalogo collegato a piattaforma (Shopify auto, Magento via plugin)
- Advantage+ Shopping Campaigns (ASC): minimum budget 50€/giorno, no targeting manuale (AI-driven)
- Creative 4:5 e 1:1, video + statico mix, 10+ varianti per campaign
- CAPI (Conversions API) obbligatoria per attribution affidabile post-iOS14
- Benchmark ROAS e-commerce Meta IT: 2.5-4x

## 4. Email lifecycle e-commerce

### Sequenze standard da implementare

| Sequenza | Step | Trigger | Target |
|---|---|---|---|
| Welcome | 3-5 email | Signup newsletter | Conversion 15-25% primo acquisto |
| Post-purchase | 2-3 email | Ordine completato | NPS + review request |
| Win-back | 3 email | 90 giorni no acquisto | Recovery 8-12% |
| Replenishment | 1 email | 80% del ciclo consumo | Repeat purchase +20% |
| Wishlist | 1-2 email | Item in wishlist 7gg | Conversion 5-15% |
| Browse abandonment | 1 email | Visit prodotto no aggiunge | Recovery 3-8% |
| Cart abandonment | 3 email | Aggiunge no acquista | Recovery 15-25% |
| VIP | trimestrale | Top 20% customer | Retention + AOV |

### Strumenti consigliati per dimensione cliente

- **Micro PMI (<1000 contatti)**: Brevo (ex Sendinblue) — piano free fino a 300 email/giorno
- **PMI piccole (1-10k contatti)**: Klaviyo Essentials (pricing per contatti, integrazioni e-commerce native) o Brevo paid
- **PMI medie (10k+ contatti)**: Klaviyo Pro, Omnisend, ActiveCampaign Plus
- **Multicanale WhatsApp incluso**: MailUp IT, Mailchimp Essentials+SMS

## 5. Pricing e promo e-commerce

### Dynamic pricing leve

- Pricing geografico (CAP/regione → es. Sud -5% per margine vs Nord)
- Pricing tempo (surge pricing weekend, markdown fine stagione)
- Pricing comportamentale (nuovo visitatore vs returning con wishlist)
- Bundle pricing (3x2, -20% seconda unità)

### Promozioni Italia — attenzione legale

- **Prezzo barrato**: deve essere il **più basso degli ultimi 30 giorni** (Direttiva Omnibus, D.Lgs. 26/2023). Violazione = sanzione 5.000-5M €
- **Saldi**: date regionali, regolamento ciascuna regione
- **Black Friday / Cyber Monday**: stesso vincolo Omnibus
- **Concorsi a premi**: autorizzazione MISE art. 19 Dpr 430/2001 se non "operazioni a premio"
- **Sottocosto**: vincoli D.Lgs. 114/1998 art. 15 (3 volte/anno max, durata max 10gg, notifica Comune)

## 6. Recensioni prodotto e social proof

### Piattaforme verificate IT

- **Feedaty** (certificato Netcomm): più diffuso e-commerce IT
- **Trustpilot**: internazionale, ottimo SEO
- **Yotpo**: UGC + review + loyalty (tutto-in-uno)
- **Klaviyo Reviews**: integrato con sequences
- **Stamped.io**: più economico, buon markup schema

### Strategie di raccolta

- Email post-delivery (7-14 giorni) con one-click rating
- Incentivi etici: sconto 5% su prossimo ordine (mai condizionato a rating positivo)
- Display recensioni homepage, product page, checkout
- Risposta pubblica a tutte le recensioni negative (trasforma in opportunità)

## 7. Subscription commerce

Per prodotti ripetibili (food, beauty, petcare, integratori):

- **Piattaforme IT**: Shopify Subscriptions, Recharge, Bold Subscriptions, Prestashop moduli dedicati
- **Pricing**: 10-15% sconto vs one-time, free shipping incluso
- **Flessibilità critica**: pause, skip, modifica frequenza, cancellazione self-service (no dark pattern)
- **KPI**: MRR, churn rate mensile (target <5%), LTV, CAC payback
- **Onboarding first box**: experience wow che crea sunk cost emotivo (peak-end)

## 8. Logistica e-commerce Italia

| Corriere | Uso tipico | Cost range | Tracking quality |
|---|---|---|---|
| Poste Italiane / SDA | Documentali, pacchi standard | 5-9 €/pacco | Media |
| GLS | PMI e-commerce mainstream | 4-7 € | Buona |
| BRT/DPD | Rapido, nazionale | 5-8 € | Buona |
| TNT/FedEx | Express, B2B | 10-20 € | Ottima |
| Amazon Logistics | Solo se vendi su Amazon | incluso FBA | Ottima |
| InPost / lockers | Delivery economica urbana | 3-5 € | Buona |

Stack consigliato: **aggregatore** (Sendcloud, Qapla, ShippyPro) per multi-corriere + tracking branded + email post-spedizione + gestione resi self-service.

## 9. Output template — E-commerce Audit Rapido

Per un cliente e-commerce nuovo, produrre audit con questa struttura:

```
## Audit E-commerce [Brand]
### 1. Tech stack attuale
[Piattaforma, theme, plugin principali, hosting]

### 2. Funnel performance
- Conversion rate totale: X% (benchmark settore Y%)
- Cart abandonment rate: X%
- AOV: €X
- Repeat purchase rate: X%

### 3. Product page scorecard
[Tabella 11 elementi sezione 1 con voto]

### 4. Checkout scorecard
[Step analysis, friction points, trust signals]

### 5. Canali acquisizione
[Split SEO organico, Paid, Email, Social, Marketplace, Direct]

### 6. Retention & Loyalty
[Sequence email attive, subscription, VIP program]

### 7. Marketplace presence
[Amazon, Trovaprezzi, Google Shopping — voti e gap]

### 8. Piano 90 giorni
Mese 1: quick wins (CRO checkout, schema, cart abandonment)
Mese 2: acquisition (Google Shopping, Meta Advantage+)
Mese 3: retention (email lifecycle, recensioni)
```

## Cross-skill references

- `psicologia-marketing`: copy persuasivo product page, CTA, pricing anchoring
- `digital-marketing-performance`: Google Ads generici, email deliverability, growth loops
- `marketing-analytics`: CLV, cohort retention, attribution multi-touch, RFM
- `seo-italia`: SEO on-page, schema, Google Business Profile (se store fisico)
- `crm-customer-experience`: loyalty program design, churn prediction
- `it-law-privacy-ai`: Consent Mode, Direttiva Omnibus, concorsi a premi
- `k2-ai-marketing-consulenza`: orchestratore ciclo retainer e-commerce
