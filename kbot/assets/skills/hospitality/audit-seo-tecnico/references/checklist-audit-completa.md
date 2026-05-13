# Checklist Audit SEO Completa

Checklist esaustiva per l'audit SEO tecnico di siti web PMI italiane. Ogni voce include cosa verificare, come verificarlo, soglie di valutazione e impatto sul posizionamento.

---

## 1. Crawlability e Indicizzazione

### 1.1 robots.txt
- **Cosa verificare**: presenza, sintassi corretta, direttive coerenti
- **Come verificare**: `WebFetch` su `/robots.txt`; verificare che non blocchi risorse critiche (CSS, JS, immagini)
- **Soglie**: OK = presente e ben configurato | Warning = presente ma con errori o direttive troppo restrittive | Fail = assente o blocca Googlebot
- **Impatto**: Alto

### 1.2 Sitemap XML
- **Cosa verificare**: presenza, referenziata in robots.txt, URL valide, aggiornamento, coerenza con pagine effettive
- **Come verificare**: `fetch_sitemap` o `WebFetch` su `/sitemap.xml`; controllare status code delle URL elencate
- **Soglie**: OK = presente, aggiornata, tutte URL 200 | Warning = presente ma con URL 404/301 o non aggiornata | Fail = assente
- **Impatto**: Alto

### 1.3 Tag noindex / nofollow
- **Cosa verificare**: pagine importanti non marcate noindex; uso corretto nofollow su link esterni non affidabili
- **Come verificare**: ispezionare meta robots e header X-Robots-Tag su ogni pagina crawlata
- **Soglie**: OK = nessun noindex su pagine importanti | Warning = noindex su pagine secondarie discutibili | Fail = noindex su homepage o pagine chiave
- **Impatto**: Alto

### 1.4 Tag canonical
- **Cosa verificare**: presenza su tutte le pagine, punta alla URL corretta, coerenza con sitemap
- **Come verificare**: ispezionare `<link rel="canonical">` nel `<head>` di ogni pagina
- **Soglie**: OK = canonical presenti e corretti | Warning = canonical mancanti su alcune pagine | Fail = canonical errati o auto-referenziali su pagine duplicate
- **Impatto**: Alto

### 1.5 Catene di redirect
- **Cosa verificare**: assenza di catene di redirect (max 1 hop), assenza di redirect loop
- **Come verificare**: seguire i redirect di ogni URL in sitemap e link interni
- **Soglie**: OK = tutti redirect diretti (1 hop) | Warning = catene 2-3 hop | Fail = catene 4+ hop o loop
- **Impatto**: Medio

### 1.6 Pagine 404
- **Cosa verificare**: assenza di link interni che puntano a pagine 404, pagina 404 personalizzata
- **Come verificare**: crawl di tutti i link interni, verifica status code
- **Soglie**: OK = 0 link rotti | Warning = 1-5 link rotti | Fail = 6+ link rotti
- **Impatto**: Medio

### 1.7 Crawl budget
- **Cosa verificare**: assenza di pagine duplicate, parametri URL non filtrati, paginazione infinita
- **Come verificare**: analisi URL crawlate, identificazione pattern di URL duplicati o parametrici
- **Soglie**: OK = URL pulite senza duplicati | Warning = alcuni parametri non gestiti | Fail = centinaia di URL duplicate o parametriche
- **Impatto**: Medio (alto per siti grandi)

### 1.8 Stato indicizzazione
- **Cosa verificare**: rapporto pagine indicizzate vs pagine totali, pagine importanti indicizzate
- **Come verificare**: `WebSearch` con `site:dominio.it`; confronto con sitemap
- **Soglie**: OK = 90%+ pagine indicizzate | Warning = 50-89% | Fail = sotto 50%
- **Impatto**: Alto

---

## 2. Velocita e Performance

### 2.1 Largest Contentful Paint (LCP)
- **Cosa verificare**: tempo di rendering dell'elemento piu grande nel viewport
- **Come verificare**: `lighthouse_audit` o PageSpeed Insights API
- **Soglie**: OK = sotto 2.5s | Warning = 2.5-4.0s | Fail = sopra 4.0s
- **Impatto**: Alto

### 2.2 Interaction to Next Paint (INP)
- **Cosa verificare**: reattivita alle interazioni dell'utente (sostituto di FID dal marzo 2024)
- **Come verificare**: `lighthouse_audit`, CrUX data
- **Soglie**: OK = sotto 200ms | Warning = 200-500ms | Fail = sopra 500ms
- **Impatto**: Alto

### 2.3 Cumulative Layout Shift (CLS)
- **Cosa verificare**: stabilita visiva della pagina durante il caricamento
- **Come verificare**: `lighthouse_audit`
- **Soglie**: OK = sotto 0.1 | Warning = 0.1-0.25 | Fail = sopra 0.25
- **Impatto**: Alto

### 2.4 Time to First Byte (TTFB)
- **Cosa verificare**: tempo di risposta del server
- **Come verificare**: header di risposta HTTP, `lighthouse_audit`
- **Soglie**: OK = sotto 800ms | Warning = 800ms-1.8s | Fail = sopra 1.8s
- **Impatto**: Medio

### 2.5 Compressione GZIP/Brotli
- **Cosa verificare**: header `Content-Encoding` nelle risposte
- **Come verificare**: ispezionare header HTTP delle risposte
- **Soglie**: OK = Brotli o GZIP attivo | Warning = solo su alcune risorse | Fail = nessuna compressione
- **Impatto**: Medio

### 2.6 Cache del browser
- **Cosa verificare**: header `Cache-Control` e `Expires` su risorse statiche
- **Come verificare**: ispezionare header HTTP di CSS, JS, immagini
- **Soglie**: OK = cache 30+ giorni su statiche | Warning = cache sotto 7 giorni | Fail = no cache
- **Impatto**: Medio

### 2.7 Ottimizzazione immagini (performance)
- **Cosa verificare**: dimensioni file immagini, formato (WebP/AVIF vs PNG/JPG), dimensioni responsive
- **Come verificare**: analisi peso pagina e singole risorse
- **Soglie**: OK = immagini sotto 200KB, formato moderno | Warning = alcune immagini pesanti | Fail = immagini non ottimizzate, peso pagina sopra 5MB
- **Impatto**: Alto

### 2.8 Lazy loading
- **Cosa verificare**: attributo `loading="lazy"` su immagini below-the-fold
- **Come verificare**: ispezionare attributi `<img>` e `<iframe>`
- **Soglie**: OK = lazy loading su immagini below-fold | Warning = parziale | Fail = assente
- **Impatto**: Medio

### 2.9 JavaScript render-blocking
- **Cosa verificare**: script nel `<head>` senza `defer` o `async`, CSS render-blocking
- **Come verificare**: ispezionare `<script>` e `<link rel="stylesheet">` nel `<head>`
- **Soglie**: OK = tutti script con defer/async o in fondo | Warning = 1-2 script blocking | Fail = 3+ script blocking
- **Impatto**: Alto

### 2.10 Minificazione CSS/JS
- **Cosa verificare**: file CSS e JS minificati
- **Come verificare**: controllare se i file contengono whitespace e commenti superflui
- **Soglie**: OK = tutti minificati | Warning = alcuni non minificati | Fail = nessuno minificato
- **Impatto**: Basso

---

## 3. Mobile

### 3.1 Responsive design
- **Cosa verificare**: layout si adatta a schermi 320px-768px senza scroll orizzontale
- **Come verificare**: `lighthouse_audit` mobile, analisi CSS media queries
- **Soglie**: OK = fully responsive | Warning = responsive con problemi minori | Fail = non responsive
- **Impatto**: Alto

### 3.2 Meta viewport
- **Cosa verificare**: presenza `<meta name="viewport" content="width=device-width, initial-scale=1">`
- **Come verificare**: ispezionare `<head>`
- **Soglie**: OK = presente e corretto | Warning = presente ma incompleto | Fail = assente
- **Impatto**: Alto

### 3.3 Tap target
- **Cosa verificare**: pulsanti e link almeno 48x48px, distanziati almeno 8px
- **Come verificare**: `lighthouse_audit` mobile
- **Soglie**: OK = tutti i target adeguati | Warning = alcuni target piccoli | Fail = molti target troppo piccoli
- **Impatto**: Medio

### 3.4 Font size
- **Cosa verificare**: testo leggibile senza zoom (minimo 16px body)
- **Come verificare**: ispezionare CSS, `lighthouse_audit`
- **Soglie**: OK = 16px+ base | Warning = 14-15px | Fail = sotto 14px
- **Impatto**: Medio

### 3.5 Mobile-first indexing
- **Cosa verificare**: contenuto mobile identico a desktop, risorse non bloccate per mobile Googlebot
- **Come verificare**: confronto contenuto pagina desktop vs mobile
- **Soglie**: OK = contenuto identico | Warning = differenze minori | Fail = contenuto significativamente diverso
- **Impatto**: Alto

---

## 4. Sicurezza

### 4.1 HTTPS
- **Cosa verificare**: certificato SSL valido, redirect HTTP > HTTPS, tutte le pagine su HTTPS
- **Come verificare**: verifica certificato, test redirect da HTTP
- **Soglie**: OK = HTTPS ovunque con certificato valido | Warning = HTTPS ma certificato in scadenza | Fail = HTTP o certificato scaduto
- **Impatto**: Alto

### 4.2 Mixed content
- **Cosa verificare**: assenza di risorse (immagini, script, CSS) caricate via HTTP su pagine HTTPS
- **Come verificare**: ispezionare tutte le risorse nella pagina
- **Soglie**: OK = zero mixed content | Warning = mixed content passivo (immagini) | Fail = mixed content attivo (script)
- **Impatto**: Alto

### 4.3 HSTS (HTTP Strict Transport Security)
- **Cosa verificare**: header `Strict-Transport-Security` presente
- **Come verificare**: ispezionare header HTTP
- **Soglie**: OK = HSTS con max-age 1 anno+ | Warning = HSTS con max-age basso | Fail = assente
- **Impatto**: Basso

### 4.4 Header di sicurezza
- **Cosa verificare**: X-Content-Type-Options, X-Frame-Options, Content-Security-Policy
- **Come verificare**: ispezionare header HTTP
- **Soglie**: OK = tutti presenti | Warning = parziali | Fail = assenti
- **Impatto**: Basso

---

## 5. On-Page

### 5.1 Title tag
- **Cosa verificare**: presente, unico per pagina, 50-60 caratteri, contiene keyword principale
- **Come verificare**: ispezionare `<title>` di ogni pagina crawlata
- **Soglie**: OK = presente, 50-60 char, con keyword | Warning = presente ma troppo corto/lungo o senza keyword | Fail = assente o duplicato
- **Impatto**: Alto

### 5.2 Meta description
- **Cosa verificare**: presente, unica per pagina, 150-160 caratteri, persuasiva con CTA
- **Come verificare**: ispezionare `<meta name="description">` di ogni pagina
- **Soglie**: OK = presente, 150-160 char, con CTA | Warning = presente ma troppo corta/lunga | Fail = assente o duplicata
- **Impatto**: Medio

### 5.3 H1
- **Cosa verificare**: esattamente 1 H1 per pagina, contiene keyword, diverso dal title
- **Come verificare**: ispezionare tutti i tag `<h1>` nella pagina
- **Soglie**: OK = 1 H1 con keyword | Warning = H1 presente ma senza keyword o uguale al title | Fail = assente o multiplo
- **Impatto**: Alto

### 5.4 Gerarchia H2-H6
- **Cosa verificare**: gerarchia logica senza salti (non H1 > H3 senza H2), H2 per sezioni principali
- **Come verificare**: mappare tutti gli heading della pagina
- **Soglie**: OK = gerarchia corretta | Warning = salti minori | Fail = nessun heading o gerarchia completamente rotta
- **Impatto**: Medio

### 5.5 Keyword density
- **Cosa verificare**: keyword principale presente nel primo paragrafo, densita 1-3%, varianti semantiche
- **Come verificare**: analisi testuale del contenuto
- **Soglie**: OK = 1-3% con varianti | Warning = sotto 1% o sopra 3% | Fail = keyword assente o keyword stuffing
- **Impatto**: Medio

### 5.6 Thin content
- **Cosa verificare**: pagine con meno di 300 parole di contenuto utile
- **Come verificare**: conteggio parole del contenuto principale (escludendo nav, footer, sidebar)
- **Soglie**: OK = 300+ parole per pagina | Warning = 150-299 parole | Fail = sotto 150 parole
- **Impatto**: Alto

### 5.7 Duplicate content
- **Cosa verificare**: contenuti identici o molto simili tra pagine diverse del sito
- **Come verificare**: confronto contenuti tra pagine, verifica canonical
- **Soglie**: OK = contenuti unici | Warning = duplicazione parziale (30-50%) | Fail = duplicazione sostanziale (50%+)
- **Impatto**: Alto

### 5.8 Open Graph e meta social
- **Cosa verificare**: og:title, og:description, og:image presenti
- **Come verificare**: ispezionare meta tag Open Graph
- **Soglie**: OK = tutti presenti | Warning = parziali | Fail = assenti
- **Impatto**: Basso

---

## 6. Immagini

### 6.1 Alt tag
- **Cosa verificare**: tutte le immagini di contenuto hanno alt descrittivo; immagini decorative hanno alt vuoto
- **Come verificare**: ispezionare attributo `alt` di ogni `<img>`
- **Soglie**: OK = 90%+ immagini con alt | Warning = 50-89% | Fail = sotto 50%
- **Impatto**: Medio

### 6.2 Dimensioni immagini
- **Cosa verificare**: attributi width/height specificati (previene CLS), dimensioni coerenti con display
- **Come verificare**: ispezionare attributi `<img>`
- **Soglie**: OK = width/height su tutte le immagini | Warning = mancanti su alcune | Fail = mancanti sulla maggior parte
- **Impatto**: Medio

### 6.3 Formati moderni (WebP/AVIF)
- **Cosa verificare**: immagini servite in formato WebP o AVIF con fallback
- **Come verificare**: ispezionare Content-Type delle immagini, presenza `<picture>` con source
- **Soglie**: OK = 80%+ in formato moderno | Warning = 30-79% | Fail = sotto 30%
- **Impatto**: Medio

### 6.4 Lazy loading immagini
- **Cosa verificare**: `loading="lazy"` su immagini below-the-fold, NO lazy loading su immagini above-the-fold (LCP)
- **Come verificare**: ispezionare attributi `<img>`
- **Soglie**: OK = lazy loading corretto | Warning = parziale | Fail = assente o su immagini LCP
- **Impatto**: Medio

### 6.5 Nomi file immagini
- **Cosa verificare**: nomi file descrittivi con keyword (non IMG_1234.jpg)
- **Come verificare**: ispezionare attributo `src` di ogni `<img>`
- **Soglie**: OK = nomi descrittivi | Warning = mix | Fail = prevalenza nomi generici
- **Impatto**: Basso

---

## 7. Struttura

### 7.1 URL parlanti
- **Cosa verificare**: URL leggibili con keyword, senza parametri inutili, senza ID numerici
- **Come verificare**: analisi pattern URL di tutte le pagine crawlate
- **Soglie**: OK = URL parlanti e pulite | Warning = alcune URL con parametri | Fail = URL con ID o parametri incomprensibili
- **Impatto**: Medio

### 7.2 Breadcrumb
- **Cosa verificare**: breadcrumb presente su pagine interne, con markup Schema BreadcrumbList
- **Come verificare**: ispezionare HTML e JSON-LD
- **Soglie**: OK = breadcrumb con Schema | Warning = breadcrumb senza Schema | Fail = assente
- **Impatto**: Medio

### 7.3 Internal linking
- **Cosa verificare**: distribuzione link interni equilibrata, anchor text descrittivi, pagine importanti ben linkate
- **Come verificare**: mappare link interni di ogni pagina, calcolare distribuzione
- **Soglie**: OK = tutte le pagine importanti con 3+ link interni | Warning = alcune pagine con pochi link | Fail = orphan pages o distribuzione molto sbilanciata
- **Impatto**: Alto

### 7.4 Orphan pages
- **Cosa verificare**: pagine presenti in sitemap ma non raggiungibili da navigazione interna
- **Come verificare**: confronto URL in sitemap con URL raggiungibili dal crawl
- **Soglie**: OK = 0 orphan | Warning = 1-3 orphan | Fail = 4+ orphan
- **Impatto**: Medio

### 7.5 Profondita click
- **Cosa verificare**: tutte le pagine importanti raggiungibili in max 3 click dalla homepage
- **Come verificare**: calcolare profondita di ogni pagina dal crawl
- **Soglie**: OK = tutte entro 3 click | Warning = alcune a 4 click | Fail = pagine a 5+ click
- **Impatto**: Medio

### 7.6 Paginazione
- **Cosa verificare**: paginazione con link rel="next"/"prev" (deprecato ma utile) o infinite scroll con URL indicizzabili
- **Come verificare**: ispezionare pagine con elenchi paginati
- **Soglie**: OK = paginazione gestita correttamente | Warning = paginazione senza rel next/prev | Fail = contenuti nascosti in infinite scroll non indicizzabile
- **Impatto**: Medio

---

## 8. Schema Markup

### 8.1 Organization
- **Cosa verificare**: Schema Organization sulla homepage con nome, logo, contatti, social
- **Come verificare**: ispezionare JSON-LD o microdata
- **Soglie**: OK = presente e completo | Warning = presente ma incompleto | Fail = assente
- **Impatto**: Medio

### 8.2 LocalBusiness
- **Cosa verificare**: Schema LocalBusiness con indirizzo, telefono, orari, coordinate (per PMI con sede fisica)
- **Come verificare**: ispezionare JSON-LD
- **Soglie**: OK = presente e completo | Warning = presente ma incompleto | Fail = assente (se attivita locale)
- **Impatto**: Alto (per local SEO)

### 8.3 BreadcrumbList
- **Cosa verificare**: Schema BreadcrumbList coerente con breadcrumb visibile
- **Come verificare**: ispezionare JSON-LD, validare con Rich Results Test
- **Soglie**: OK = presente e valido | Warning = presente ma con errori | Fail = assente
- **Impatto**: Medio

### 8.4 FAQ
- **Cosa verificare**: Schema FAQ su pagine con domande frequenti
- **Come verificare**: ispezionare JSON-LD
- **Soglie**: OK = presente dove pertinente | Warning = assente ma pagine FAQ presenti | Fail = N/A se non ci sono FAQ
- **Impatto**: Medio

### 8.5 Product (se e-commerce)
- **Cosa verificare**: Schema Product con nome, prezzo, disponibilita, recensioni
- **Come verificare**: ispezionare JSON-LD su pagine prodotto
- **Soglie**: OK = presente e completo | Warning = presente ma incompleto | Fail = assente su pagine prodotto
- **Impatto**: Alto (per e-commerce)

### 8.6 Review / AggregateRating
- **Cosa verificare**: Schema Review o AggregateRating dove pertinente
- **Come verificare**: ispezionare JSON-LD
- **Soglie**: OK = presente dove pertinente | Warning = assente ma recensioni presenti | Fail = N/A
- **Impatto**: Medio

---

## 9. Internazionalizzazione

### 9.1 Hreflang (se sito multilingua)
- **Cosa verificare**: tag hreflang corretti per ogni versione linguistica, link bidirezionali, x-default
- **Come verificare**: ispezionare `<link rel="alternate" hreflang="...">` nel `<head>`
- **Soglie**: OK = hreflang corretti e bidirezionali | Warning = hreflang presenti ma con errori | Fail = assenti su sito multilingua
- **Impatto**: Alto (se multilingua)

### 9.2 Struttura URL multilingua
- **Cosa verificare**: sottodirectory (/it/, /en/) o sottodomini, non parametri (?lang=it)
- **Come verificare**: analisi pattern URL
- **Soglie**: OK = sottodirectory o sottodomini | Warning = mix | Fail = solo parametri GET
- **Impatto**: Medio (se multilingua)

---

## Riepilogo conteggio

| Area | Numero verifiche |
|------|:----------------:|
| Crawlability e Indicizzazione | 8 |
| Velocita e Performance | 10 |
| Mobile | 5 |
| Sicurezza | 4 |
| On-Page | 8 |
| Immagini | 5 |
| Struttura | 6 |
| Schema Markup | 6 |
| Internazionalizzazione | 2 |
| **Totale** | **54** |
