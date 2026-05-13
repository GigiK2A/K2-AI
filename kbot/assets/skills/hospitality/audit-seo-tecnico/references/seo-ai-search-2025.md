# SEO per AI Search — Citabilita su ChatGPT, Bing-Copilot, Perplexity, Gemini

Riferimento operativo 2025 per rendere un sito "leggibile" e "citabile" dagli LLM conversazionali. Integra l'audit tecnico classico: un sito che rispetta le regole SEO tradizionali ma trascura l'AI search rischia di scomparire dal nuovo flusso di traffico informativo.

## Perche importa adesso

A fine 2024 l'uso di ChatGPT ha superato quello di Bing come destinazione di ricerca. Il pubblico italiano sta spostando le query informative e di confronto verso interfacce conversazionali: quando il potenziale cliente chiede "qual e il miglior commercialista per PMI a Milano" direttamente a ChatGPT, il nostro sito o viene citato fra le fonti o sparisce. La SEO tradizionale resta necessaria (ChatGPT attinge massicciamente da Bing, e Microsoft detiene circa il 49% di OpenAI), ma non e piu sufficiente.

## Come "ragionano" i motori LLM — versione operativa

Quando un utente scrive una query su ChatGPT o SearchGPT, il motore svolge cinque fasi distinte:

1. **Parsing della query**: il sistema scompone il prompt in parole chiave, rimuove stopword, arricchisce semanticamente. Interessante: la lunghezza media di un prompt su ChatGPT e di 23 parole, contro le 4,2 parole di una query Google. Circa il 70% dei prompt su ChatGPT ha un intent unico, non sovrapponibile a quello di Google.
2. **Information Retrieval**: il motore interroga il proprio indice gia addestrato e, se serve, effettua una chiamata live al web (spesso via Bing).
3. **Ranking e filtraggio**: assegna uno score alle fonti trovate e le filtra in base al profilo utente.
4. **Generazione della risposta (RAG)**: un modello linguistico sintetizza le fonti recuperate in una risposta testuale. RAG sta per Retrieval Augmented Generation ed e il meccanismo che consente a ChatGPT di citare fonti aggiornate invece di limitarsi al training.
5. **Formattazione e training feedback**: l'output viene strutturato (liste, tabelle, link) e i click dell'utente vengono usati per migliorare il modello.

Un dato importante (ricerca Surfer citata nel PDF LSBA): solo il 52% delle fonti citate negli AI overview si trova fra i primi 10 risultati Google. Significa che essere in top 10 su Google non basta per comparire in ChatGPT, e viceversa pagine oltre la prima pagina possono emergere nelle risposte AI se strutturate bene.

## Cosa rende una pagina "citabile" da un LLM

Dall'analisi della checklist LSBA 2025 emergono sei cluster di segnali su cui lavorare.

**1. Struttura gerarchica H pulita.** Un H1 unico, H2 tematici e H3 di dettaglio permettono al crawler LLM di isolare blocchi informativi da citare. Evitare pagine-muro senza subheading.

**2. Chiarezza nelle prime 200 parole.** I motori LLM privilegiano l'incipit: la risposta alla domanda implicita della pagina deve comparire entro il primo terzo del contenuto, non annegata in cappelli introduttivi lunghi. Niente "lunghissime introduzioni alla Aranzulla".

**3. FAQ strutturate con schema.org FAQPage.** Le domande e risposte sono il formato che gli LLM estraggono piu volentieri. Aggiungere markup FAQPage sulle pagine chiave aumenta drasticamente la citabilita.

**4. Schema.org Article, FAQPage, LocalBusiness, Review, HowTo.** I dati strutturati restano il canale diretto per comunicare al motore cosa contiene la pagina. Includere statistiche uniche e fatti verificabili alza il valore di citazione.

**5. Autori dichiarati e verificabili.** ChatGPT e Perplexity premiano contenuti con byline chiara, bio autore, link a profili social professionali. Questo si collega al framework E-E-A-T di Google: Experience, Expertise, Authoritativeness, Trustworthiness.

**6. HTML pulito, JavaScript minimo.** I crawler LLM attuali (incluso ChatGPT) non renderizzano JavaScript come fanno Gemini o Applebot. Contenuto critico caricato via JS = contenuto invisibile. Servire tutto in HTML/Markdown statico per le sezioni informative.

## Il ruolo del RAG per la SEO

Capire il funzionamento del RAG cambia le priorita operative. Se il motore recupera fonti live per rispondere, tre fattori diventano decisivi:

- **List mentions**: essere presente in "listicle" autorevoli della nicchia ("migliori commercialisti Milano", "top 10 studi legali Roma"). ChatGPT pesca massicciamente da queste liste per costruire raccomandazioni.
- **Brand mentions**: essere citati su Wikipedia, siti di settore, Reddit, anche senza link. Il brand mention puro oggi vale quanto un backlink ai fini dell'AI search.
- **Online reviews**: recensioni su Trustpilot, G2, Capterra, Google Business Profile. I motori LLM consultano attivamente queste piattaforme per giudicare l'affidabilita.

## Checklist AI-readiness (10 punti operativi)

Da verificare in ogni audit tecnico dal 2025 in poi. Ogni voce e azionabile dal webmaster senza consulenze esterne.

1. **H1 unico** per pagina, contenente la query principale in forma naturale.
2. **Gerarchia H2/H3** coerente: ogni H2 introduce un sotto-tema citabile a se stante.
3. **Risposta chiave nei primi 200 parole**: la pagina risponde esplicitamente alla domanda implicita nell'URL/title.
4. **Schema FAQPage** su almeno una sezione per pagina principale, con domande reali del pubblico.
5. **Schema Article / LocalBusiness / Organization** con campo author compilato.
6. **Bio autore** pubblica e linkabile, con credenziali verificabili.
7. **Statistiche o dati unici** pubblicati sul sito (non solo citazioni di altri): goldmine per gli LLM.
8. **HTML pulito**: contenuto principale servito senza richiedere esecuzione JavaScript.
9. **Presenza su almeno 3 piattaforme di recensione** rilevanti per il settore (Trustpilot, Google Business, G2, Capterra, MioDottore, TripAdvisor).
10. **Monitoraggio citazioni AI**: testare mensilmente cosa ChatGPT e Perplexity dicono del brand, identificando da quali fonti attingono per correggere il racconto.

## Integrazione con l'audit DOCX

Nel report DOCX aggiungere una sezione dedicata "AI-readiness 2025" dopo l'analisi on-page, con lo scoring sui 10 punti della checklist. Ogni punto rosso/giallo deve generare una raccomandazione operativa concreta (es. "installare plugin Yoast FAQ e compilare schema su pagina Servizi") e una stima dell'impatto sulla visibilita conversazionale.
