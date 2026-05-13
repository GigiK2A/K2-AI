# Benchmark Core Web Vitals

Soglie ufficiali Google, benchmark per settore italiano e impatto stimato sul ranking.

---

## Soglie ufficiali Google (aggiornate marzo 2024)

### Largest Contentful Paint (LCP)
Misura il tempo di rendering dell'elemento di contenuto piu grande visibile nel viewport.

| Fascia | Soglia | Giudizio |
|--------|--------|----------|
| Buono | 0 - 2.5s | Esperienza veloce, nessuna penalizzazione |
| Da migliorare | 2.5s - 4.0s | Esperienza accettabile, possibile penalizzazione lieve |
| Scarso | oltre 4.0s | Esperienza lenta, penalizzazione ranking |

**Elementi tipici LCP**: immagine hero, video, blocco testo grande, immagine di sfondo CSS.

### Interaction to Next Paint (INP)
Sostituto di FID dal marzo 2024. Misura la latenza di tutte le interazioni dell'utente (click, tap, tastiera) e riporta il valore peggiore (al 98esimo percentile).

| Fascia | Soglia | Giudizio |
|--------|--------|----------|
| Buono | 0 - 200ms | Interazioni reattive |
| Da migliorare | 200ms - 500ms | Ritardo percepibile |
| Scarso | oltre 500ms | Interfaccia percepita come bloccata |

**Cause comuni INP alto**: JavaScript pesante nel main thread, event handler costosi, layout thrashing, librerie di terze parti.

### Cumulative Layout Shift (CLS)
Misura la stabilita visiva: quantifica quanto gli elementi si spostano durante il caricamento.

| Fascia | Soglia | Giudizio |
|--------|--------|----------|
| Buono | 0 - 0.1 | Layout stabile |
| Da migliorare | 0.1 - 0.25 | Spostamenti percepibili |
| Scarso | oltre 0.25 | Layout instabile, esperienza frustrante |

**Cause comuni CLS alto**: immagini senza dimensioni, font web che causano FOUT/FOIT, contenuto iniettato dinamicamente, annunci senza spazio riservato.

---

## Metriche complementari

### Time to First Byte (TTFB)
| Fascia | Soglia | Note |
|--------|--------|------|
| Buono | 0 - 800ms | Server reattivo |
| Da migliorare | 800ms - 1.8s | Ottimizzare server o CDN |
| Scarso | oltre 1.8s | Hosting inadeguato o backend lento |

### First Contentful Paint (FCP)
| Fascia | Soglia | Note |
|--------|--------|------|
| Buono | 0 - 1.8s | Primo contenuto rapido |
| Da migliorare | 1.8s - 3.0s | Ritardo percepibile |
| Scarso | oltre 3.0s | Pagina percepita come lenta |

### Total Blocking Time (TBT)
| Fascia | Soglia | Note |
|--------|--------|------|
| Buono | 0 - 200ms | Main thread libero |
| Da migliorare | 200ms - 600ms | Qualche task lungo |
| Scarso | oltre 600ms | JS pesante blocca interazioni |

---

## Benchmark per settore italiano

Dati aggregati da CrUX (Chrome User Experience Report) e analisi di mercato per il panorama italiano PMI. Valori mediani (p50) su connessione mobile 4G tipica italiana.

### E-commerce (Shopify, WooCommerce, PrestaShop)

| Metrica | Mediana Italia | Best practice | Note |
|---------|---------------|---------------|------|
| LCP | 3.8s | sotto 2.5s | Immagini prodotto pesanti, slider homepage |
| INP | 350ms | sotto 200ms | Plugin pesanti, carrello JS-intensive |
| CLS | 0.18 | sotto 0.1 | Banner promo, lazy loading immagini prodotto |
| TTFB | 1.2s | sotto 800ms | Hosting condiviso, no CDN |

**Problemi tipici**: immagini prodotto non ottimizzate, troppi plugin WooCommerce/PrestaShop, mancanza di CDN, slider con immagini full-size.

### Servizi professionali (studi legali, commercialisti, consulenti)

| Metrica | Mediana Italia | Best practice | Note |
|---------|---------------|---------------|------|
| LCP | 3.2s | sotto 2.5s | Template WordPress pesanti |
| INP | 250ms | sotto 200ms | Form di contatto JS |
| CLS | 0.12 | sotto 0.1 | Google Maps embed, font loading |
| TTFB | 1.0s | sotto 800ms | Hosting entry-level |

**Problemi tipici**: tema WordPress sovraccarico di funzionalita non usate, font Google caricati in modo bloccante, Google Maps iframe pesante.

### Ristorazione (ristoranti, pizzerie, bar)

| Metrica | Mediana Italia | Best practice | Note |
|---------|---------------|---------------|------|
| LCP | 4.2s | sotto 2.5s | Foto piatti ad alta risoluzione |
| INP | 180ms | sotto 200ms | Siti semplici, poco JS |
| CLS | 0.22 | sotto 0.1 | Menu PDF embed, immagini senza dimensioni |
| TTFB | 1.5s | sotto 800ms | Hosting economico, spesso Wix/Squarespace |

**Problemi tipici**: foto piatti non compresse (spesso 2-5MB ciascuna), menu in PDF non indicizzabile, siti su piattaforme lente, mancanza LocalBusiness schema.

### Manifatturiero (PMI industriali, artigiani)

| Metrica | Mediana Italia | Best practice | Note |
|---------|---------------|---------------|------|
| LCP | 3.5s | sotto 2.5s | Catalogo prodotti con foto pesanti |
| INP | 280ms | sotto 200ms | Filtri catalogo JS |
| CLS | 0.15 | sotto 0.1 | Tabelle specifiche tecniche |
| TTFB | 1.3s | sotto 800ms | Siti spesso datati |

**Problemi tipici**: siti non aggiornati da anni, immagini catalogo enormi, mancanza di schema Product, siti non responsive (ancora layout fisso).

### B2B (servizi alle imprese, software, consulenza)

| Metrica | Mediana Italia | Best practice | Note |
|---------|---------------|---------------|------|
| LCP | 3.0s | sotto 2.5s | Hero video o animazioni |
| INP | 320ms | sotto 200ms | Form multi-step, chat widget |
| CLS | 0.14 | sotto 0.1 | Cookie banner, chat popup |
| TTFB | 0.9s | sotto 800ms | Hosting migliore della media |

**Problemi tipici**: chat widget di terze parti che rallenta, cookie banner che causa CLS, video hero non ottimizzato, tracking script multipli.

---

## Impatto ranking stimato per fascia performance

Basato su studi di correlazione e dichiarazioni ufficiali Google (Page Experience Update).

### Tutte le metriche in fascia "Buono"
- **Impatto ranking**: positivo, requisito per comparire in Top Stories e caroselli
- **Stima traffico**: +5-15% rispetto a concorrenti con performance scarsa nella stessa nicchia
- **Note**: il contenuto resta il fattore principale; la performance e un fattore di tie-breaking

### Metriche in fascia "Da migliorare"
- **Impatto ranking**: neutro, nessun bonus ne penalizzazione significativa
- **Stima traffico**: baseline, nessun vantaggio competitivo dalla performance
- **Note**: concentrarsi sul miglioramento se i concorrenti sono in fascia "Buono"

### Una o piu metriche in fascia "Scarso"
- **Impatto ranking**: negativo, possibile penalizzazione soprattutto su mobile
- **Stima traffico**: -10-25% rispetto al potenziale, con impatto maggiore su mobile
- **Note**: intervento urgente consigliato, specialmente su LCP e CLS

### Tabella riassuntiva impatto

| Scenario | Variazione traffico stimata | Priorita intervento |
|----------|----------------------------|---------------------|
| LCP scarso (oltre 4s) | -10-20% | Critica |
| INP scarso (oltre 500ms) | -5-10% | Alta |
| CLS scarso (oltre 0.25) | -5-15% | Alta |
| LCP + CLS scarsi | -15-25% | Critica |
| Tutti scarsi | -20-30% | Critica |
| Tutti buoni vs tutti "da migliorare" | +5-15% | Media |

---

## Tool di riferimento

### PageSpeed Insights (PSI)
- **URL**: https://pagespeed.web.dev/
- **Dati**: Lighthouse lab data + CrUX field data (se disponibili)
- **Uso nell'audit**: fonte primaria per Core Web Vitals e raccomandazioni specifiche
- **Limiti**: lab data puo differire da field data; non tutti i siti hanno dati CrUX

### Lighthouse
- **Integrazione**: disponibile via `lighthouse_audit` nella piattaforma
- **Dati**: lab data (simulazione su device mobile mid-tier con 4G)
- **Uso nell'audit**: analisi dettagliata performance, accessibilita, best practice, SEO
- **Limiti**: lab data, non riflette esperienza utenti reali; punteggio variabile tra esecuzioni

### Chrome UX Report (CrUX)
- **URL**: https://developer.chrome.com/docs/crux/
- **Dati**: field data reali da utenti Chrome (aggregati 28 giorni)
- **Uso nell'audit**: dati reali di performance, suddivisi per device e connessione
- **Limiti**: disponibile solo per siti con traffico sufficiente; dati aggregati, non per singola pagina

### Google Search Console
- **Dati**: report Core Web Vitals con stato per URL, raggruppate per pattern
- **Uso nell'audit**: confronto lab vs field, identificazione URL problematiche
- **Limiti**: richiede accesso al profilo del cliente; dati con ritardo di qualche giorno

### WebPageTest
- **URL**: https://www.webpagetest.org/
- **Dati**: test da location specifiche (disponibile Milano), waterfall dettagliato
- **Uso nell'audit**: analisi waterfall per diagnosi problemi specifici di caricamento
- **Limiti**: richiede interpretazione esperta; test singoli, non dati aggregati
