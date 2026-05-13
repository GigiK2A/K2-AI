# Semantic SEO: LSI, content cluster, silos, intent mapping

Riferimento operativo per strutturare la strategia keyword di una PMI italiana oltre la vecchia logica "una keyword, una pagina, keyword density alta". Dopo Hummingbird (2013), RankBrain (2015), BERT (2019) e l'arrivo degli LLM, il ranking si gioca sulla topical authority — cioe sulla capacita di dimostrare competenza approfondita su un tema, non sulla ripetizione ossessiva di una parola.

## LSI keywords — di cosa si tratta davvero

LSI sta per Latent Semantic Indexing. Il motore di ricerca, e oggi anche gli LLM, non cerca solo la keyword esatta: cerca l'insieme di termini semanticamente correlati che dimostrano che la pagina tratta davvero quel tema. Se scrivi un articolo su "mutuo prima casa" e non menzioni mai "tasso", "TAEG", "istruttoria", "notaio", "garanzia", "Consap", Google capisce che la pagina e superficiale — indipendentemente da quante volte ripeti "mutuo prima casa".

**Esempi italiani pratici di cluster LSI**:

- Keyword principale: **"commercialista Milano"**. LSI attese: partita IVA, regime forfettario, dichiarazione dei redditi, fatturazione elettronica, bilancio, ordine dei dottori commercialisti, F24, studio associato, consulenza fiscale.
- Keyword principale: **"agriturismo Toscana"**. LSI attese: degustazione, cantina, piscina, colline senesi, camere, mezza pensione, prodotti tipici, cinta senese, Chianti, visita in fattoria.
- Keyword principale: **"idraulico Roma"**. LSI attese: pronto intervento, perdita, caldaia, scaldabagno, scarico, rubinetto, installazione, preventivo gratuito, zona, 24 ore.

Per ogni pillar keyword dell'audit, costruire una lista di 10-15 termini LSI con cui arricchire naturalmente il testo, i subtitle e le FAQ.

## Content cluster: pillar page + cluster page

Il modello pillar/cluster e la struttura con cui si dimostra topical authority post-Hummingbird. Funziona cosi:

- Un **pillar page** copre un tema ampio in modo esaustivo (tipicamente 2.000-4.000 parole). Esempio: "Mutuo prima casa: guida completa 2026".
- Una serie di **cluster page** approfondisce sotto-temi specifici, ognuno con la sua long-tail dedicata. Esempio: "Mutuo prima casa per giovani under 36", "Mutuo prima casa con cessione del quinto", "Simulazione mutuo prima casa INPS", "Mutuo prima casa senza busta paga".
- Ogni cluster page linka alla pillar. La pillar linka alle cluster. Il linking interno rinforza la percezione algoritmica che il dominio e esperto sull'intera area tematica.

**Schema topologico**:

```
                [PILLAR PAGE: mutuo prima casa]
                          /|\
            ______________|______________________
           /     /     /     |     \     \       \
     [cluster] [cluster] [cluster] [cluster] [cluster]
      under36  cessione   INPS    no-busta   surroga
```

Ogni cluster ha al massimo 2-3 cluster satelliti a sua volta, evitando profondita eccessive.

**Perche funziona post-Hummingbird**: il motore non ragiona piu per keyword atomiche ma per entita e topic. Un dominio che copre in modo organizzato e interlinkato un topic segnala una competenza strutturale che una singola pagina ben scritta non potra mai segnalare.

## Content silos: fisici vs virtuali

I silos sono il modo con cui si implementa concretamente la struttura pillar/cluster sul sito.

**Silos fisici (URL structure)**: la struttura degli URL riflette la topologia.

Esempio:
```
studio-commercialista.it/
├── /regime-forfettario/                        ← pillar
│   ├── /regime-forfettario/limite-85000/       ← cluster
│   ├── /regime-forfettario/codici-ateco/       ← cluster
│   └── /regime-forfettario/flat-tax/           ← cluster
├── /fatturazione-elettronica/                  ← pillar
│   ├── /fatturazione-elettronica/sdi/          ← cluster
│   └── /fatturazione-elettronica/forfettari/   ← cluster
└── /dichiarazione-redditi/                     ← pillar
```

Questa struttura e preferibile quando si parte da zero o durante una migrazione: dice al motore e all'utente dove si trova una pagina nella gerarchia tematica.

**Silos virtuali (internal linking)**: la gerarchia tematica esiste solo a livello di link, non di URL. Il sito e piatto (es. tutte le pagine a un livello), ma i link interni raggruppano le pagine per topic.

Quando scegliere uno o l'altro:
- Silos fisici: siti nuovi, siti in ristrutturazione, CMS flessibili (WordPress con custom permalink, Webflow).
- Silos virtuali: siti gia lanciati con autorita sugli URL esistenti (migrare URL significa perdere ranking), e-commerce con vincoli di piattaforma.

In pratica, per la PMI italiana media (sito piccolo-medio su WordPress): silos fisici per le nuove aree tematiche, silos virtuali per le sezioni legacy che non si vogliono toccare.

## Intent mapping a 4 vie con esempi italiani per settore

Ogni keyword va classificata in uno dei quattro intent principali. L'errore tipico e assegnare a una stessa pagina keyword di intent diversi: la pagina poi non performa su nessuna.

### Informazionale (I) — l'utente vuole sapere

**Segnali**: "come", "cosa", "perche", "quando", "guida", "significato".

| Settore | Esempio keyword italiana |
|---------|--------------------------|
| Commercialista | "cosa e il regime forfettario" |
| Idraulico | "come sturare un lavandino" |
| E-commerce moda | "come abbinare le scarpe beige" |
| Ristorazione | "differenza tra carbonara e amatriciana" |
| Studio legale | "quanto dura un divorzio consensuale" |

Pagina target: articolo di blog, guida, FAQ dedicata.

### Navigazionale (N) — l'utente cerca un brand o un sito specifico

**Segnali**: nome brand, dominio, nomi prodotto specifici.

| Settore | Esempio keyword italiana |
|---------|--------------------------|
| E-commerce | "zalando scarpe uomo" |
| Software | "aruba posta elettronica" |
| Banca | "unicredit home banking" |

Pagina target: homepage, pagina brand, pagina prodotto. Raramente opportunita per chi non e il brand cercato.

### Commerciale (C) — l'utente confronta opzioni prima di decidere

**Segnali**: "migliore", "miglior", "top", "recensioni", "opinioni", "vs", "confronto", "alternativa a".

| Settore | Esempio keyword italiana |
|---------|--------------------------|
| Commercialista | "miglior commercialista online forfettari" |
| Idraulico | "idraulico Milano recensioni" |
| E-commerce moda | "migliori sneakers uomo 2026" |
| Ristorazione | "migliore pizzeria napoletana Roma" |
| SaaS | "alternative a Salesforce per PMI" |

Pagina target: landing di confronto, recensioni clienti, case studies, guida comparativa.

### Transazionale (T) — l'utente e pronto ad agire

**Segnali**: "prezzo", "preventivo", "acquista", "prenota", "ordina", "sconto", "offerta", "vicino a me", "urgente", "subito".

| Settore | Esempio keyword italiana |
|---------|--------------------------|
| Commercialista | "commercialista online preventivo" |
| Idraulico | "idraulico Milano urgente 24 ore" |
| E-commerce moda | "acquista sneakers Nike Air Max" |
| Ristorazione | "prenota tavolo pizzeria Trastevere" |
| Studio legale | "avvocato divorzista Roma prezzo" |

Pagina target: landing page di conversione, pagina prodotto, pagina servizio con modulo preventivo, scheda GBP per locali.

**Priorita per PMI italiana media**: T > C > I > N. Le PMI tendono a sprecare budget su contenuti informazionali generici invece di presidiare prima le query transazionali e commerciali che portano clienti realmente.

## Come clusterizzare 50-100 keyword in pillar + satelliti

Metodo operativo che funziona quando si esce dalla keyword research con una lista lunga.

1. **Esporta la lista in foglio di calcolo** con colonne: keyword, volume, intent (I/N/C/T), difficulty.
2. **Ordina per volume decrescente** e identifica 3-7 "head term" con volume alto e intent C o T: questi saranno i candidati pillar.
3. **Per ogni head term, raggruppa sotto di esso tutte le keyword che condividono la stessa entita principale**. Esempio: sotto "mutuo prima casa" raggruppi "mutuo prima casa under 36", "mutuo prima casa senza garante", "simulazione mutuo prima casa", ecc.
4. **Controlla la SERP reale per 3-4 keyword campione per cluster**. Se Google mostra le stesse pagine per keyword diverse del cluster, significa che le tratta come sinonimi e vale una sola pagina. Se mostra pagine diverse, servono pagine diverse (cluster page distinte).
5. **Assegna ogni keyword a una e una sola pagina target**. Mai la stessa keyword su due pagine (keyword cannibalization).
6. **Definisci per ciascun cluster una gerarchia di keyword**: 1 primaria + 2-5 secondarie + 5-10 LSI. La primaria va in title, URL, H1; le secondarie nei H2 e nel testo; le LSI distribuite naturalmente.
7. **Indica lo stato**: pagina esistente da ottimizzare / pagina nuova da creare / articolo blog / FAQ / landing.

## Collegamento con l'intent mapping framework

Questo file integra `intent-mapping-framework.md`: l'intent mapping dice come classificare la singola keyword, il clustering semantico dice come organizzare il sito intero in modo che il motore e gli LLM riconoscano l'esperienza tematica. Le due viste lavorano insieme: senza intent mapping si creano cluster confusi; senza clustering si creano pagine orfane che non si rinforzano a vicenda.
