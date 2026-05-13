# Evoluzione dell'algoritmo Google 2010-2024

Riferimento storico e operativo per l'audit SEO. Capire cosa misura ogni update permette di diagnosticare PERCHE un sito non posiziona e di prioritizzare correttamente gli interventi. Molti problemi che vediamo oggi sui siti italiani nascono dal mancato adeguamento a update usciti anni fa.

## Perche serve conoscere la storia degli update

Un sito PMI italiano medio e stato costruito in epoche diverse e stratifica buone pratiche di anni diversi. Quando l'audit trova thin content, keyword stuffing, pubblicita invasive, backlink spam, schede mobile zoppicanti, mancanza di struttura autoriale, significa che il sito non ha mai digerito l'update corrispondente. Ogni aggiornamento dell'algoritmo misura qualcosa di specifico: sapere cosa ha misurato guida l'intervento.

## Tabella cronologica degli update principali

| Anno | Update | Cosa misura / cosa penalizza | Come adeguarsi oggi |
|------|--------|------------------------------|---------------------|
| 2010 | **Caffeine** | Indicizzazione rapida: Google passa da settimane a secondi per inserire un contenuto nell'indice. Premia siti che pubblicano fresh content. | Pubblicare con regolarita, aggiornare articoli datati invece di lasciarli fermi. Usare sitemap.xml sempre aggiornata. |
| 2011 | **Panda** (alias Farmer) | Qualita del contenuto: colpisce content farm, spam, copie, contenuti non esaustivi. Segnali usati: bounce rate alto, duplicati, testi ripetuti, pubblicita eccessiva, title non coerente. | Content audit: rimuovere o accorpare thin content, riscrivere pagine generiche, ridurre la densita di ads sopra la piega. |
| 2012 | **Penguin** | Qualita dei backlink: penalizza link acquistati, link spam, ancore manipolative. | Disavow di link tossici, stop a guest post massivi con anchor ottimizzata, preferire branded link e menzioni naturali. |
| 2013 | **Hummingbird** | Comprensione semantica della query: l'algoritmo capisce "dove, come, perche" e le long-tail conversazionali. Impatta circa il 90% delle ricerche mondiali. | Strutturare contenuti per topic cluster, usare sinonimi e keyword correlate, rispondere a domande complete e non solo a keyword isolate. |
| 2014 | **Pigeon** | Ranking locale: risultati piu precisi in base alla geolocalizzazione. Utile per ristoranti, studi, cinema, negozi. | Scheda Google Business Profile completa, coerenza NAP su tutte le directory, citazioni locali italiane. |
| 2015 | **Mobilgeddon** | Mobile friendliness: penalizza siti non navigabili da smartphone. | Tema responsive, viewport corretto, tap target dimensionati, test su Mobile Friendly Test di Google. |
| 2015 | **RankBrain** | Machine learning applicato al ranking: interpreta query mai viste combinandole con cronologia, geo, intent. | Ottimizzare per intent (non per keyword esatta), produrre contenuti che soddisfino realmente il bisogno dell'utente, monitorare dwell time. |
| 2016 | **Possum** | Ulteriore raffinamento del local search con filtri di duplicazione sulla Maps. | Evitare doppie schede GBP, disambiguare attivita vicine, differenziare le categorie primarie. |
| 2017 | **Google Fred** | Colpisce pubblicita eccessiva, fake news, contenuti creati solo per ads. | Ridurre densita pubblicitaria, evitare clickbait, garantire valore informativo proporzionato alla monetizzazione. |
| 2017 | **Mobile-First Indexing** | Cambio di paradigma: il ranking si basa sulla versione mobile del sito, non piu su quella desktop. | Se desktop e mobile divergono, allineare contenuti, struttura e schema markup. Controllare che nulla sia nascosto nel mobile. |
| 2018 | **Medic Update** | Tentativo (poi parzialmente rivisto) di penalizzare contenuti medici senza autorita. Ha reso evidente il peso dell'E-A-T. | Pagine YMYL (Your Money Your Life) con autori certificati, fonti, revisione professionale dichiarata. |
| 2019 | **BERT** | Comprensione del contesto linguistico: capisce preposizioni e sfumature, supera Hummingbird sulla query complessa. Abilita la ricerca vocale (Alexa, Google Home). | Scrivere in italiano naturale, abbandonare il keyword stuffing, curare la coerenza frase-paragrafo. |
| 2020 | **Core Web Vitals** annunciati | Nuove metriche di performance UX: LCP (caricamento), FID poi INP (interattivita), CLS (stabilita layout). | LCP < 2,5s, CLS < 0,1, INP < 200ms. Lazy loading, immagini WebP, defer/async su JS, dimensioni fisse per immagini e banner. |
| 2021 | **Page Experience Update** | Core Web Vitals diventano fattore di ranking ufficiale. Etichetta UX visibile in SERP. | Monitoraggio continuo via PageSpeed Insights, Search Console > Core Web Vitals, correzione delle URL in rosso. |
| 2022 | **Helpful Content Update** | Premia contenuti scritti per le persone, penalizza contenuti generati solo per rankare. Segnale sitewide: una zona del sito di bassa qualita trascina giu tutto il dominio. | Audit sitewide, pruning di vecchi articoli SEO-first, riscrittura customer-centric, dichiarare expertise dell'autore. |
| 2022-2023 | **E-E-A-T aggiornato** | Aggiunge la "E" di Experience alle precedenti Expertise, Authoritativeness, Trustworthiness. | Inserire esperienza diretta nei contenuti (case, test personali, foto originali), non solo rielaborazione di fonti esterne. |
| 2023-2024 | **SGE / AI Overview rollout** | Google integra risposte generative in SERP, con citazioni dirette alle fonti. | Strutturare contenuti citabili (vedi `seo-ai-search-2025.md`): FAQ schema, risposte nette nei primi 200 parole, dati unici. |

## Come usare questa tabella durante l'audit

**Step 1 — Identifica l'eta del sito e gli update vissuti.** Un sito del 2008 che non ha mai ricevuto manutenzione probabilmente sbatte contro Panda, Penguin, Mobile-First e Helpful Content insieme.

**Step 2 — Cerca i sintomi, non le cause.** Traffic drop a gennaio 2020 + pattern di link gonfiati = quasi certamente Penguin retrospettivo su un core update. Crollo mobile = mancata digestione di Mobile-First. Rating basso su pagine di servizio ampie e generiche = Helpful Content.

**Step 3 — Prioritizza gli interventi per eta dell'update.** Gli update piu recenti (Core Web Vitals, Helpful Content, AI Overview) pesano di piu. Ma un sito che ancora non e HTTPS o non e responsive deve prima sanare i debiti storici.

**Step 4 — Spiegalo al cliente con parole comprensibili.** Nel DOCX, evita il gergo ("Penguin penalty") e traduci ("il sito ha troppi link comprati da fonti non attinenti — Google se n'e accorto nel 2012 e non ha mai dimenticato").

## Nota sul contesto italiano

Molte PMI italiane hanno siti costruiti fra 2010 e 2016 da agenzie locali che hanno ottimizzato per l'epoca di Panda-Penguin ma non hanno mai rivisto la base. L'audit 2025 trova spesso: testi "SEO-ottimizzati" vecchia maniera, keyword density alta, backlink da directory zombie (tipo Cylex, HotFrog 2014), zero schema markup, zero author bio. Questa tabella aiuta il webmaster e il titolare a capire perche il sito non si muove nonostante gli "interventi SEO" pagati in passato.
