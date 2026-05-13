# Checklist SEO — WebBoost

Usa questa checklist durante lo **Step 2** (audit SEO tecnico e on-page). Per ogni voce è indicato il **perché conta** e l'**impatto tipico** su una PMI italiana, così puoi prioritizzare senza spegnere il cervello.

---

## A. On-page per singola pagina

### A.1 Title tag
- **Cosa verificare**: presenza, lunghezza 50–60 caratteri, keyword primaria nella prima metà, brand alla fine separato da `|` o `–`, unicità tra pagine.
- **Perché**: il title è ancora il fattore on-page più pesante e determina il click nella SERP.
- **Impatto**: alto. Un title scritto male può dimezzare il CTR.

### A.2 Meta description
- **Cosa verificare**: presenza, lunghezza 140–160 caratteri, contiene CTA esplicito, include keyword (anche se non pesa su ranking aiuta il CTR via bold).
- **Perché**: non pesa direttamente sul ranking ma sul CTR che poi pesa indirettamente.
- **Impatto**: medio.

### A.3 H1
- **Cosa verificare**: uno solo per pagina, contiene keyword primaria (variante naturale ok), non è uguale al title (può divergere leggermente).
- **Perché**: conferma a Google il topic della pagina.
- **Impatto**: medio-alto.

### A.4 Gerarchia H2-H6
- **Cosa verificare**: struttura logica (H2 per sezioni macro, H3 per sotto-sezioni), niente salti (no H2→H4), keyword variant naturali in almeno 2-3 H2.
- **Perché**: aiuta Google a capire la struttura e migliora l'accessibility.
- **Impatto**: medio.

### A.5 Contenuto testuale
- **Cosa verificare**: lunghezza adeguata al topic e all'intent (pagine servizio 600–1200 parole, articoli guida 1500–3000, landing commerciali 300–800), keyword density naturale (mai stuffing), presenza di entità correlate (NLP: termini che un esperto userebbe davvero), no contenuti duplicati tra pagine.
- **Perché**: Google misura expertise via presenza di entità correlate, non via ripetizione keyword.
- **Impatto**: alto.

### A.6 Immagini
- **Cosa verificare**: alt text descrittivo (no keyword stuffing, no "immagine 1"), formato moderno (WebP preferibile), dimensioni ottimizzate, lazy loading per immagini below-the-fold.
- **Perché**: SEO immagini + accessibility + velocità.
- **Impatto**: medio.

### A.7 Internal linking
- **Cosa verificare**: ogni pagina ha almeno 2–3 link interni verso pagine rilevanti, anchor text descrittivo (non "clicca qui"), pagine orfane assenti, presenza di breadcrumb.
- **Perché**: distribuisce autorità e aiuta Google a scoprire e indicizzare.
- **Impatto**: medio-alto.

### A.8 URL structure
- **Cosa verificare**: URL brevi, descrittivi, con keyword, trattini (non underscore), no parametri quando non necessari, no date quando non necessarie, struttura gerarchica coerente con architettura sito.
- **Perché**: UX e micro-fattore di ranking.
- **Impatto**: basso-medio (ma sistemarli dopo è un incubo, meglio farlo bene dall'inizio).

---

## B. Technical SEO

### B.1 HTTPS
- **Cosa verificare**: certificato valido, redirect 301 da HTTP a HTTPS, nessun mixed content.
- **Perché**: fattore di ranking confermato + trust.
- **Impatto**: critico (problemi qui = escalation immediata).

### B.2 Mobile-friendliness
- **Cosa verificare**: responsive design, tap target adeguati (min 48x48px), testo leggibile senza zoom, viewport meta tag.
- **Perché**: Google usa mobile-first indexing. Oltre il 60% delle ricerche PMI italiane è mobile.
- **Impatto**: critico.

### B.3 Core Web Vitals
- **Cosa verificare**: LCP < 2.5s, INP < 200ms, CLS < 0.1. Strumenti: PageSpeed Insights, Lighthouse.
- **Perché**: fattore di ranking diretto e correlato a conversion.
- **Impatto**: alto.

### B.4 robots.txt
- **Cosa verificare**: presenza, non blocca accidentalmente risorse CSS/JS, indica sitemap.
- **Perché**: una riga sbagliata può deindicizzare mezzo sito.
- **Impatto**: critico.

### B.5 sitemap.xml
- **Cosa verificare**: presenza, include solo URL validi e canonici, aggiornata automaticamente, sottomessa a Google Search Console.
- **Perché**: accelera l'indicizzazione di nuovi contenuti.
- **Impatto**: medio.

### B.6 Schema markup (structured data)
- **Cosa verificare** (varia per tipo business):
  - PMI locale: `LocalBusiness` con NAP (name, address, phone), orari, geo coordinates, serviceArea.
  - E-commerce: `Product`, `Offer`, `AggregateRating`, `Review`.
  - Content: `Article`, `BreadcrumbList`, `FAQPage`, `HowTo`.
  - Sempre: `Organization` o `WebSite` in home.
- **Perché**: rich snippet → +15–40% CTR quando appaiono.
- **Impatto**: alto e sottovalutato.

### B.7 Canonical tags
- **Cosa verificare**: ogni pagina ha un canonical, canonical verso se stessa per default, gestione corretta per contenuti duplicati (filtri, varianti).
- **Perché**: previene penalizzazioni per duplicati.
- **Impatto**: medio (alto se c'è duplicazione pesante).

### B.8 Indicizzazione
- **Cosa verificare**: query `site:dominio.it` su Google per stimare pagine indicizzate, confronto con sitemap, pagine importanti indicizzate, pagine inutili non indicizzate (admin, thank you, ecc.).
- **Perché**: Google non può mostrare ciò che non vede.
- **Impatto**: critico.

---

## C. Off-page e autorità

### C.1 Google Business Profile (per business locali)
- **Cosa verificare**: presenza, categorie corrette, orari aggiornati, foto professionali, descrizione con keyword naturali, post periodici, Q&A curate, recensioni > 20 con risposta, NAP consistente col sito.
- **Perché**: per un business locale PMI è spesso più importante del sito stesso.
- **Impatto**: critico se locale.

### C.2 Citazioni NAP
- **Cosa verificare**: Name/Address/Phone identici su directory italiane (Pagine Gialle, Pagine Bianche, TripAdvisor se ristorazione, Miodottore se sanità, ecc.).
- **Perché**: Google usa la consistenza NAP come segnale di trust.
- **Impatto**: medio-alto per locale.

### C.3 Backlink quality (analisi qualitativa)
- **Cosa verificare**: presenza di menzioni su siti autorevoli di settore, stampa locale, associazioni di categoria, fornitori/partner. Link tossici (schemi, PBN) da disavow.
- **Perché**: l'autorità resta un pilastro del ranking.
- **Impatto**: alto sul medio periodo (ma lavoro lento).

### C.4 Social signal
- **Cosa verificare**: presenza attiva sui social rilevanti per il target (LinkedIn per B2B, Instagram per B2C visual, Facebook per locale 40+), frequenza post, engagement reale, traffico dai social al sito.
- **Perché**: non ranking diretto ma brand search e referral traffic.
- **Impatto**: medio.

---

## D. Matrice prioritizzazione (da usare sempre)

Ogni issue trovata va classificata su due dimensioni:

- **Impatto** (alto / medio / basso): quanto sposta traffico/conversion.
- **Sforzo** (rapido / medio / intenso): ore/giorni per implementare.

Poi collocata in una matrice 2x2:

| | Rapido | Medio | Intenso |
|---|---|---|---|
| **Alto impatto** | P1 — fai subito | P1 — schedula questa settimana | P2 — pianifica trimestre |
| **Medio impatto** | P2 — inserisci sprint | P3 — valuta ROI | P4 — solo se budget |
| **Basso impatto** | P3 — quando c'è tempo | P4 — probabilmente no | Scarta |

Il report deve sempre contenere 5–10 azioni P1 e 5–10 azioni P2. Oltre questo numero, il cliente si paralizza.

---

## E. Errori comuni da non fare

- **Report enciclopedici**: 40 issue senza priorità = cliente che non fa nulla. Preferisci 10 ben scelte.
- **Keyword stuffing nelle raccomandazioni**: non suggerire mai "ripeti la keyword 15 volte". Consiglia entità correlate.
- **Ignorare il business locale**: se la PMI vende in una città, il Google Business Profile vale più di 100 backlink.
- **Promettere risultati in 30 giorni**: la SEO è un asset, non un'ads campaign. Orizzonte minimo 3 mesi, standard 6–12.
- **Confondere traffic con lead**: un sito con 10k visite e 0 lead è peggio di uno con 500 visite e 20 lead. Porta sempre il discorso sul business outcome.
