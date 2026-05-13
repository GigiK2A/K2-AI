---
name: flusso-webboost-pmi
description: Orchestratore WebBoost — diagnosi completa della presenza online di una PMI italiana (5–50 dipendenti) e piano di miglioramento attuabile. Usa SEMPRE questa skill quando l'utente dice "audit SEO sito", "analisi presenza web", "migliorare sito web", "WebBoost", "diagnosi sito PMI", "perché il mio sito non porta clienti", "farmi trovare su Google", "revisione sito aziendale", "piano SEO e contenuti", "audit web completo", "ottimizzare la presenza online", "report SEO mensile", "controllare sito PMI", "servizio WebBoost", oppure quando fornisce un URL di un sito aziendale italiano chiedendo di analizzarlo o migliorarlo. Attivala anche per piano editoriale PMI, revisione homepage, keyword research, UX audit sito PMI, generazione contenuti SEO per azienda italiana. Produce report DOCX executive, piano editoriale XLSX, dashboard HTML e output JSON strutturato.
---

# flusso-webboost-pmi — Orchestratore WebBoost

## 1. Cosa fa questa skill (e perché esiste)

Questa skill è il **motore del prodotto WebBoost** della piattaforma consulenziale per PMI italiane (5–50 dipendenti). Orchestra un workflow end-to-end che trasforma pochi input strutturati (URL sito, settore, target geografico, keyword obiettivo) in un pacchetto di deliverable pronti da consegnare al cliente: report executive DOCX, piano editoriale XLSX, dashboard HTML e output JSON strutturato per l'integrazione software.

Il nome "WebBoost" non è casuale: il prodotto promette al titolare di una PMI *un miglioramento misurabile e continuo* della sua presenza online, senza che debba imparare SEO, UX o copywriting. La skill deve comportarsi come un direttore marketing digitale senior con vent'anni di esperienza su PMI italiane: severo sulle diagnosi, pragmatico sulle soluzioni, capace di distinguere ciò che sposta davvero i numeri da ciò che è cosmetico.

**Due modalità di esecuzione** che la skill deve riconoscere e gestire:

- **Modalità consulenziale diretta** (oggi, in Cowork/Claude Code): l'utente — tipicamente un consulente che usa la piattaforma per servire un cliente PMI — fornisce input manualmente e la skill produce i deliverable finali. I "tool custom" (API SEO, Lighthouse, ecc.) non sono disponibili: si sopperisce con WebFetch, WebSearch e ragionamento strutturato, segnalando esplicitamente nel report i punti dove servirebbe uno strumento dedicato.
- **Modalità piattaforma SaaS** (domani): la skill gira dentro un backend con Agent SDK e tool custom disponibili (vedi `references/piattaforma-integration.md`). L'output JSON viene parsato dal frontend e renderizzato come dashboard live. Stessa skill, stesso workflow, solo con tool migliori sotto il cofano.

La skill deve essere scritta in modo che entrambe le modalità funzionino senza fork logici evidenti. Il comportamento degrada gracefully: se un tool non esiste, si fa con quello che c'è e si annota nel report.

## 2. Quando attivarsi

Attivati in modo proattivo — l'utente spesso non sa chiedere il prodotto giusto col nome giusto. Se senti uno di questi segnali, questa è la skill che serve:

- L'utente fornisce un URL di un sito PMI italiano e chiede qualsiasi forma di analisi o miglioramento.
- L'utente lamenta che il sito non porta clienti, non è trovato su Google, è "vecchio", o vuole capire se funziona.
- L'utente chiede un audit SEO, un piano editoriale, una revisione UX/copy, una keyword research, o una strategia di contenuti per un'azienda B2B o B2C italiana di piccole dimensioni.
- L'utente dice esplicitamente "WebBoost" o ne descrive le caratteristiche.
- L'utente vuole preparare un pitch o una proposta commerciale per un cliente PMI sul tema web/SEO/contenuti.

Non attivarti se: il target è una grande impresa (50+ dipendenti) con marketing interno strutturato, se la richiesta è puramente tecnica-dev (problemi hosting, bug), o se si parla di e-commerce complesso che richiede `k2-test-le:ecommerce-marketing-pmi` (in quel caso usa quella skill come primaria e WebBoost come supporto).

## 3. Input richiesti al cliente

Prima di partire, **raccogli in modo conversazionale** queste informazioni. Se mancano, chiedile una a una in modo gentile (non un form da compilare):

1. **URL del sito** (obbligatorio) — homepage del cliente.
2. **Settore** (obbligatorio) — es. "studio commercialista", "azienda serramenti", "ristorante", "clinica dentale", "software house B2B". Più specifico è, meglio è.
3. **Area geografica di target** (obbligatorio) — nazionale, regione, città. Determina la dimensione SEO locale vs nazionale.
4. **3 keyword obiettivo** (obbligatorio ma negoziabile) — le query che il cliente vorrebbe intercettare. Se il cliente non ne ha, proponi tu 3 ipotesi basate su settore+geo e fagliele validare.
5. **Obiettivo di business primario** (obbligatorio) — scegli uno: generare contatti qualificati, vendere online, costruire autorevolezza, ridurre costi del customer support, informare/educare. Questo cambia il peso di SEO vs UX vs content vs brand.
6. **Concorrenti principali** (facoltativo, molto utile) — 2–5 URL di competitor che il cliente considera riferimento.
7. **Brand voice / tono** (facoltativo) — se esistono guideline, caricale; altrimenti verrà estratta dall'analisi.
8. **Budget mensile indicativo** (facoltativo) — utile per calibrare il realismo del piano d'azione.

## 4. Workflow — i 7 step dell'orchestratore

Esegui questi step **in ordine**. Ogni step produce un artefatto intermedio che viene usato dallo step successivo. Non saltare step a meno che l'input manchi in modo definitivo — in quel caso annota il gap nel report e procedi.

### Step 1 — Discovery e contesto

Obiettivo: costruire il "gemello digitale leggero" del sito e dell'azienda.

Azioni:
- Fetch della homepage e di 3–5 pagine chiave (chi siamo, servizi/prodotti, contatti, blog se presente). Usa `WebFetch` in modalità consulenziale, `fetch_page_content()` in modalità piattaforma.
- Estrai: title, meta description, H1, CTA principali, form presenti, social embed, tecnologie visibili (Wordpress, Shopify, custom...), presenza schema markup.
- Inquadra l'azienda: descrizione sintetica, target dichiarato, value proposition dichiarata, prove sociali (recensioni, case history, clienti).
- Salva come `site-snapshot.json` intermedio.

Invoca la skill `digital-marketing-performance` per strutturare l'inquadramento e la skill `marketing-bocconi-trust` per estrarre la value proposition con metodo.

### Step 2 — Audit SEO tecnico e on-page

Obiettivo: diagnosi oggettiva dei problemi che bloccano il traffico organico.

Azioni:
- **On-page**: qualità di title e meta description (lunghezza, keyword, call-to-action), gerarchia H1-H6, densità keyword naturale, qualità dei contenuti (sottile vs sostanziale), struttura URL, alt text immagini, internal linking.
- **Technical**: HTTPS, mobile-friendliness (visibile da Lighthouse o ispezione responsive), velocità (Core Web Vitals stimati), presenza `robots.txt` e `sitemap.xml`, schema markup (LocalBusiness, Organization, Article, Product, Review, FAQ), canonical tag, indicizzazione Google (stima via `site:` query).
- **Off-page** (stima qualitativa): autorità di dominio percepita da menzioni, link da press/elenchi, presenza su Google Business Profile se locale.
- Classifica ogni issue per **impatto** (alto/medio/basso) e **sforzo** (rapido/medio/intenso). Questa matrice determina la roadmap.

Invoca `marketing:seo-audit` come skill di supporto per il framework, `digital-marketing-performance` per le best practice tecniche.

Se in modalità piattaforma: chiama `lighthouse_audit(url)` e `fetch_sitemap(url)`. Se in modalità consulenziale: usa WebFetch per ispezione manuale e annota "serve strumento dedicato per dati quantitativi precisi" dove opportuno.

### Step 3 — Keyword research e intent mapping

Obiettivo: passare dalle 3 keyword seed a un universo semantico di 30–60 query coerenti col business.

Azioni:
- Espandi le 3 seed in 30–60 keyword correlate usando: modificatori geografici, sinonimi, long-tail specifiche di settore, domande (how/what/why in italiano: "come", "cosa", "perché", "quanto costa", "migliore"), versioni transazionali vs informative.
- Per ogni keyword assegna: **intent** (informativo / navigazionale / transazionale / commerciale), **fase funnel** (TOFU/MOFU/BOFU), **stima volume** (alto/medio/basso/marginale — qualitativa se non hai API), **difficulty percepita**, **priorità** (1/2/3).
- Identifica **gap di posizionamento**: query dove il cliente è assente ma dovrebbe esserci.
- Mappa ogni keyword prioritaria a una **pagina di atterraggio** — esistente da ottimizzare o nuova da creare.

Invoca `marketing-analytics` per il framework di priorità e `marketing-bemacs-quant` per metriche quantitative.

In modalità piattaforma: `keyword_research(seed, geo)` + `serp_data(kw, geo)`. In modalità consulenziale: WebSearch per stimare competizione SERP.

### Step 4 — Analisi UX, copy e persuasione

Obiettivo: capire se il sito, una volta che arriva visita, *converte*. Il traffico senza conversione è fuoco di paglia.

Azioni:
- **Homepage review**: in 5 secondi un visitatore capisce cosa fai, per chi, perché sceglierti? La value proposition è sopra la piega? Il CTA principale è evidente, unico, senza attrito?
- **Social proof**: recensioni, loghi clienti, testimonianze, certificazioni, numeri sono presenti e credibili?
- **Friction audit**: form con troppi campi, step di checkout confusi, informazioni di contatto nascoste, tempi di risposta non dichiarati.
- **Copy audit**: il tono è coerente con il settore e il pubblico? Parla di benefici o di feature? Usa il linguaggio del cliente o il gergo interno? Sfrutta i leve psicologiche giuste (riprova sociale, scarsità onesta, autorevolezza, reciprocità)?
- **Microcopy**: pulsanti, label form, messaggi di errore, pagine vuote, thank you page.

Invoca `design:ux-copy` + `design:design-critique` + `design:accessibility-review` per il framework UX, `psicologia-marketing` per le leve persuasive, `marketing-bocconi-trust` per la costruzione di fiducia.

### Step 5 — Brand voice check e correzione

Obiettivo: verificare che il sito parli con una voce coerente e distintiva, e se no, proporne una.

Azioni:
- Estrai il tono attuale dai testi pubblicati (formale/informale, tecnico/divulgativo, istituzionale/umano, caldo/asciutto).
- Confronta con il posizionamento dichiarato e il target: c'è dissonanza?
- Se esistono guideline, usale come benchmark.
- Se non esistono, proponi una baseline di brand voice (3–5 attributi di tono, 5 parole da usare, 5 da evitare, esempi prima/dopo su 2 paragrafi reali del sito).

Invoca `brand-voice:brand-voice-enforcement` se esistono guideline da applicare, `brand-voice:guideline-generation` se vanno create da zero.

### Step 6 — Content plan e generazione parziale

Obiettivo: consegnare al cliente un piano editoriale *attuabile* nei prossimi 3 mesi + contenuti già pronti per partire.

Azioni:
- Costruisci un **piano editoriale di 8–12 articoli** per i prossimi 3 mesi, strutturato pillar + cluster: 2–3 pillar page (guide lunghe, evergreen, alta keyword authority) + 6–9 cluster article (articoli tematici che linkano alla pillar).
- Per ogni articolo: titolo, keyword target, intent, sintesi (3 righe), struttura H2/H3, CTA finale, data pubblicazione suggerita, priorità.
- **Genera integralmente 2 articoli pronti per la pubblicazione** — scegli i 2 con priorità più alta / sforzo più basso. Lunghezza 800–1500 parole, tono allineato alla brand voice del Step 5, SEO-friendly (keyword in title/H1/primo paragrafo/alt text, internal link agli altri contenuti del sito, meta description pronta).

Invoca `marketing:content-creation` + `marketing:draft-content` + `psicologia-marketing` per la persuasione nel corpo.

### Step 7 — Consolidamento deliverable e roadmap 90 giorni

Obiettivo: chiudere il cerchio con un pacchetto professionale che il cliente possa aprire e capire in 5 minuti.

Azioni:
- **Report executive DOCX** (`assets/template-report.md` come guida): executive summary 1 pagina, diagnosi per area (Tecnico, Contenuti, UX, Brand, Local), roadmap 90 giorni, KPI da monitorare. Massimo 15–20 pagine.
- **Piano editoriale XLSX** (`assets/piano-editoriale-template.md` come guida): tab "Calendario editoriale", "Keyword map", "Competitor", "Issue tracker", "KPI dashboard".
- **Dashboard HTML** (`assets/template-dashboard-html.md`): pagina singola con KPI principali, matrice impact/effort, lista azioni prioritizzate, stato mensile.
- **Output JSON strutturato** (`schemas/output-schema.json`): tutto in formato machine-readable per la piattaforma.
- **Piano d'azione prioritizzato**: matrice 2x2 (impatto x sforzo) con elenco azioni, ogni azione con responsabile suggerito (cliente vs consulente vs dev), deadline, KPI collegato.
- **KPI da monitorare mensilmente**: traffico organico, keyword in top 10/top 3, lead generati, conversion rate, tempo su pagina, bounce rate, backlink quality, Google Business Profile interactions se locale.

Per la creazione dei file:
- Usa skill `docx` per il report.
- Usa skill `xlsx` per il piano editoriale.
- Scrivi HTML inline per la dashboard (single-file, nessuna dipendenza esterna tranne Chart.js da CDN se serve).
- Scrivi il JSON validando contro `schemas/output-schema.json`.

Salva tutti i deliverable in `/sessions/focused-exciting-feynman/mnt/outputs/webboost-<nome-cliente>/` con nomi standard:
- `01_report_executive.docx`
- `02_piano_editoriale.xlsx`
- `03_dashboard.html`
- `04_output.json`
- `05_articoli_pronti/articolo-1.md`, `articolo-2.md`

## 5. Principi di comportamento che la skill deve seguire

**Rigore diagnostico, pragmatismo esecutivo.** Le PMI non leggono report lunghi. Il report executive deve avere una executive summary di UNA pagina con le 3–5 cose che cambiano il risultato, e solo dopo la diagnosi dettagliata. Gli imprenditori scansionano, non leggono.

**Sempre prioritizza per ROI.** Non elencare 50 issue SEO: elenca le 10 che spostano davvero il business e annota che "ci sono altre 40 ottimizzazioni minori non incluse perché a impatto marginale". Mostra che sei esigente.

**Parla come un consulente vero, non come un tool.** Evita il linguaggio da checklist impersonale. Usa frasi come "il rischio qui è che perda lead al primo scroll" invece di "la homepage presenta criticità di above-the-fold". Il cliente deve sentire un cervello dietro le parole.

**Onestà sui limiti dei dati.** Se stai stimando invece di misurare (perché non hai l'API), dillo. "Stima qualitativa, consigliato integrare con Google Search Console per dato preciso" è meglio di un numero inventato.

**Ogni raccomandazione ha un "perché".** Non "metti lo schema LocalBusiness" ma "metti lo schema LocalBusiness perché il 40% delle ricerche nel tuo settore sono locali e Google usa questi marker per decidere se mostrarti nel pacco mappe".

**Lingua: italiano sempre.** Il cliente è italiano, i deliverable sono in italiano, anche quando le skill sottostanti ragionano internamente in inglese.

**Niente fuffa.** Non raccomandare "migliorare la brand awareness" o "ottimizzare il funnel": raccomanda azioni concrete (titolo X, aggiungere form Y a pagina Z, scrivere articolo W entro la settimana V).

## 6. Gestione errori e casi limite

- **Sito non raggiungibile**: annota chiaramente e chiedi conferma URL. Procedi con quello che si può fare (solo keyword research e competitor).
- **Sito in lingua non italiana**: chiedi conferma target (se PMI italiana ma sito EN, è un errore grave di posizionamento → primo elemento del report).
- **Sito in costruzione / placeholder**: il deliverable diventa "piano di lancio" invece di "audit": setup brand voice, keyword strategy preliminare, piano editoriale di lancio.
- **Sito e-commerce complesso**: delega parti specifiche a `k2-test-le:ecommerce-marketing-pmi` e usa WebBoost per il frame generale.
- **Cliente B2B enterprise con ciclo vendita lungo**: il piano editoriale pesa più di SEO puro; usa `k2-test-le:linkedin-b2b-outreach` come complemento.

## 7. Riferimenti (caricare on-demand)

Per tenere questo SKILL.md sotto i 500 righe, i dettagli tecnici sono separati. Leggi il file appropriato *solo quando serve durante lo step rilevante*.

- `references/checklist-seo.md` — checklist dettagliata on-page/technical/off-page con spiegazione del "perché" per ogni voce. Leggi durante Step 2.
- `references/benchmark-settori-italia.md` — benchmark realistici di volume, CTR, conversion rate per settore PMI italiano. Leggi durante Step 3 e Step 7.
- `references/prompt-content-generation.md` — pattern di prompt per generare articoli di qualità coerenti con brand voice. Leggi durante Step 6.
- `references/piattaforma-integration.md` — contratto API tra questa skill e la piattaforma SaaS futura: tool custom attesi, schema JSON, flow sincrono/asincrono. Leggi quando l'ambiente è piattaforma o quando documenti per il team dev.
- `assets/template-report.md` — struttura del report DOCX, sezione per sezione.
- `assets/piano-editoriale-template.md` — struttura del file XLSX.
- `assets/template-dashboard-html.md` — struttura della dashboard HTML.
- `schemas/output-schema.json` — schema JSON dell'output strutturato.

## 8. Deliverable finali — checklist di chiusura

Prima di chiudere il flusso, verifica:

- [ ] Report DOCX salvato in outputs con nome standardizzato.
- [ ] Piano editoriale XLSX con tutti i tab previsti.
- [ ] Dashboard HTML apribile in browser senza errori, self-contained.
- [ ] Output JSON valido contro lo schema.
- [ ] 2 articoli di blog pronti, allineati a brand voice, ottimizzati SEO.
- [ ] Roadmap 90 giorni con azioni concrete e responsabili.
- [ ] Riassunto finale all'utente con link diretti ai file e 3 punti chiave.

Presenta all'utente solo al termine, con un messaggio sintetico del tipo: "Ecco il pacchetto WebBoost per [nome cliente]. [3 frasi sulle priorità emerse]. [Link ai 4 deliverable principali]."

Non commentare il tuo lavoro, non spiegare cosa hai fatto: lascia parlare i deliverable.
