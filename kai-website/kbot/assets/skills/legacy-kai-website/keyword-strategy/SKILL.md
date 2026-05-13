---
name: keyword-strategy
description: >-
  Ricerca keyword con intent mapping, gap analysis competitor e cluster tematici per PMI italiane.
  Trigger: "keyword research", "ricerca keyword", "parole chiave", "su cosa posizionarmi",
  "keyword strategy", "analisi keyword", "keyword competitor", "gap analysis keyword",
  "cluster keyword", "piano keyword", "quali keyword usare", "keyword per il mio sito",
  "strategia parole chiave". Input: URL sito, settore, 3-5 keyword seed, 1-3 competitor
  (opzionali), target geografico. Output: keyword map XLSX (4 tab: keyword master, cluster
  tematici, competitor gap, piano assegnazione pagine) e JSON strutturato. Workflow: analisi
  keyword attuali, ricerca ampliata con espansione long-tail, intent mapping 4 livelli,
  gap analysis vs competitor, clustering pillar/cluster con assegnazione keyword a pagine.
  Per ogni keyword: volume, difficolta, intent, pagina target, priorita.
  Terzo livello consulenza web PMI (249-399 euro).
allowed-tools:
  - WebSearch
  - WebFetch
  - keyword_research
  - serp_data
  - competitor_discovery
---

# keyword-strategy

Ricerca keyword con intent mapping, gap analysis competitor e cluster tematici per PMI italiane.

## Panoramica

Il cliente ha fatto l'audit SEO tecnico, sa che il sito funziona, ma sta puntando le keyword sbagliate. Questa skill gli dice SU COSA posizionarsi: quali keyword attaccare, con quale priorita, raggruppate in cluster tematici e assegnate a pagine specifiche (esistenti o da creare).

Terzo livello della scala di valore consulenza web PMI (249-399 euro).

## Input richiesto

| Parametro | Obbligatorio | Descrizione |
|-----------|:---:|-------------|
| URL sito | Si | Homepage o dominio del cliente |
| Settore | Si | Settore di attivita (es. "idraulico", "avvocato divorzista", "e-commerce scarpe") |
| Keyword seed | Si | 3-5 parole chiave di partenza che il cliente ritiene importanti |
| Competitor | No | 1-3 siti competitor diretti (se il cliente non li conosce, li individuiamo noi) |
| Target geografico | Si | Citta, provincia, regione o "nazionale" |

## Workflow (5 step)

### Step 1 — Analisi keyword attuali del sito

Obiettivo: capire per quali keyword il sito gia compare nelle SERP.

**Modalita consulenziale (WebSearch):**
- Cerca `site:dominio.it` per capire le pagine indicizzate
- Per ogni keyword seed, cerca `"keyword" site:dominio.it` per verificare la presenza
- Analizza title tag e meta description delle pagine principali per estrarre keyword implicite

**Modalita piattaforma:**
- Usa `serp_data` per verificare il posizionamento attuale del dominio
- Usa `keyword_research` con filtro dominio per estrarre keyword attuali

Registra: keyword attuali, posizione stimata, pagina che si posiziona.

### Step 2 — Keyword research ampliata

Obiettivo: partire dai seed ed espandere a un universo completo di keyword rilevanti.

Metodo di espansione (vedi `references/metodologia-keyword-research.md`):
- **Modificatori geografici**: keyword + citta, keyword + "vicino a me", keyword + zona
- **Modificatori intent**: "migliore" + keyword, keyword + "prezzo", keyword + "preventivo"
- **Domande**: "come" + keyword, "cosa" + keyword, "quando" + keyword, "perche" + keyword
- **Long-tail**: combinazioni a 3-4-5 parole che specificano bisogno preciso
- **Sinonimi e correlate**: termini alternativi usati dal pubblico italiano

**Modalita consulenziale (WebSearch):**
- Cerca ogni seed su Google e analizza: Google Suggest (autocompletamento), People Also Ask, ricerche correlate in fondo SERP
- Usa Google Trends per identificare trend e stagionalita

**Modalita piattaforma:**
- Usa `keyword_research` con seed per ottenere espansioni automatiche
- Usa `competitor_discovery` per trovare keyword dei competitor

Target: 50-150 keyword candidate per PMI locale, 100-300 per PMI nazionale.

### Step 3 — Intent mapping

Obiettivo: classificare ogni keyword per tipo di intent (vedi `references/intent-mapping-framework.md`).

Per ogni keyword, assegna uno dei 4 intent:
- **Informazionale** (I): l'utente cerca informazioni ("come sturare il lavandino")
- **Navigazionale** (N): l'utente cerca un brand o sito specifico ("idraulico rossi milano")
- **Commerciale** (C): l'utente confronta opzioni ("miglior idraulico zona 3 milano recensioni")
- **Transazionale** (T): l'utente vuole agire ("idraulico urgente milano preventivo")

Metodo di classificazione:
1. Analizza i modificatori nella keyword (segnali lessicali)
2. Controlla la SERP reale: presenza di ads, local pack, featured snippet, shopping results
3. Assegna intent primario e, se ambiguo, intent secondario

Priorita per PMI:
- **Lead-gen**: T > C > I > N
- **E-commerce**: T > C > I > N (ma I pesa di piu per content marketing)

### Step 4 — Gap analysis vs competitor

Obiettivo: trovare keyword per cui i competitor si posizionano e il cliente no.

**Modalita consulenziale (WebSearch):**
- Per ogni competitor, cerca le keyword principali e verifica chi compare
- Confronta: "keyword" → chi appare in top 10? Il cliente? I competitor?
- Identifica le keyword dove TUTTI i competitor sono presenti e il cliente e assente → massima opportunita

**Modalita piattaforma:**
- Usa `competitor_discovery` per estrarre keyword dei competitor
- Usa `serp_data` per confrontare posizionamenti
- Incrocia i dataset per trovare gap

Classifica le opportunita:
- **Gap critico**: competitor in top 5, cliente assente — keyword ad alto volume/intent commerciale
- **Gap importante**: competitor in top 10, cliente oltre pagina 2
- **Gap minore**: competitor presenti, cliente in pagina 1 ma posizione bassa

### Step 5 — Clustering tematico e assegnazione pagine

Obiettivo: raggruppare le keyword in cluster pillar/cluster e assegnare ogni keyword a una pagina.

Metodo di clustering:
1. Identifica 3-7 **pillar topic** (macro-argomenti del business)
2. Per ogni pillar, raggruppa le keyword correlate in **cluster** (sotto-argomenti)
3. Ogni cluster = 1 pagina (esistente o da creare)
4. Ogni pagina ha: 1 keyword primaria + 2-5 keyword secondarie

Assegnazione pagine:
- Verifica se esiste gia una pagina sul sito che tratta quel tema
- Se si: ottimizzare la pagina esistente per la keyword primaria del cluster
- Se no: creare una nuova pagina (specificare tipo: landing page, articolo blog, pagina servizio)

Per ogni keyword nel piano finale, registra:
- **Volume stimato** (mensile, mercato italiano)
- **Difficolta** (0-100, stima basata su autorita dei risultati in SERP)
- **Intent** (I/N/C/T)
- **Cluster** di appartenenza
- **Pagina target** (URL esistente o "DA CREARE: [tipo pagina]")
- **Priorita** (1-5, dove 1 = massima priorita)

Criteri di prioritizzazione:
1. Intent transazionale/commerciale + volume decente + difficulty bassa = priorita 1
2. Gap critico vs competitor + intent commerciale = priorita 1-2
3. Long-tail con intent chiaro + facile da posizionare = priorita 2-3
4. Informazionale con alto volume (brand awareness) = priorita 3-4
5. Head term con alta difficulty = priorita 4-5 (obiettivo lungo termine)

## Skills invocate

Questa skill puo invocare:

- **`digital-marketing-performance`** — per dati sulle performance attuali del sito
- **`marketing-analytics`** — per analisi quantitativa del traffico e conversioni
- **`marketing-bemacs-quant`** — per modelli quantitativi di stima volumi e ROI keyword
- **`xlsx`** — per generare il file XLSX della keyword map

## Deliverable

### 1. XLSX — Keyword Map (4 tab)

Generato tramite skill `xlsx`. Struttura dettagliata in `assets/template-keyword-map.md`.

**Tab 1 — Keyword Master**: elenco completo keyword con volume, difficulty, intent, cluster, pagina target, priorita.
**Tab 2 — Cluster Tematici**: vista per pillar/cluster con keyword raggruppate e volume totale.
**Tab 3 — Competitor Gap**: matrice posizionamento keyword × siti (cliente + competitor).
**Tab 4 — Piano Assegnazione**: mappa keyword → pagine con stato (esistente/da creare/da ottimizzare).

### 2. JSON — Output strutturato

Schema in `schemas/output-schema.json`. Contiene tutti i dati in formato machine-readable per integrazione con altri strumenti.

### 3. Executive summary

Incluso nel JSON e presentato al cliente. Deve rispondere a:
- Quante keyword totali analizzate e quante selezionate
- I 3-5 cluster piu importanti su cui concentrarsi
- Le 10 keyword a priorita massima (quick win)
- Quante pagine nuove servono e quante esistenti da ottimizzare
- Stima dell'impatto: traffico potenziale aggiuntivo mensile

## Tono e comunicazione

Strategico ma comprensibile. Il titolare PMI deve capire:
- PERCHE certe keyword contano piu di altre (non tutte le keyword sono uguali)
- QUALE keyword porta clienti vs quale porta solo traffico vanity
- DOVE concentrare le risorse limitate (regola 80/20)
- COSA fare concretamente: quale pagina creare/ottimizzare per quale keyword

Evitare gergo tecnico non spiegato. Ogni termine tecnico va accompagnato da una spiegazione pratica.
Usare esempi concreti dal settore del cliente.

## Riferimenti

- `references/metodologia-keyword-research.md` — framework completo di ricerca keyword per PMI italiane
- `references/intent-mapping-framework.md` — classificazione intent e mappatura su funnel/pagine
- `assets/template-keyword-map.md` — template dettagliato delle 4 tab XLSX
- `schemas/output-schema.json` — schema JSON dell'output strutturato
