---
name: analisi-bilancio-pmi
description: >
  Analisi di bilancio completa per PMI italiane (299 EUR). Riclassificazione SP e CE, calcolo 25+ indici, trend 3 anni, benchmark settore, report DOCX professionale. Usa SEMPRE per: analisi bilancio, leggere il bilancio, indici di bilancio, ROE ROI ROS, riclassificazione, come va l'azienda, analisi finanziaria, bilancio PMI, capire il bilancio, confronto bilancio settore, margini EBITDA, solidita patrimoniale, liquidita aziendale, cash conversion cycle, Du Pont scomposizione, rendiconto finanziario, radar benchmark, equilibrio finanziario, leva finanziaria, rotazione capitale, copertura immobilizzazioni, autonomia finanziaria, current ratio, quick ratio, CAGR fatturato, trend redditualita, diagnosi aziendale da bilancio, check-up finanziario PMI.
---

# Analisi di Bilancio Completa per PMI Italiane

Skill professionale per l'analisi di bilancio di piccole e medie imprese italiane. Produce un report DOCX di 12-15 pagine con riclassificazione, 25+ indici, trend triennale, benchmark settoriale e raccomandazioni operative.

## Input Richiesti

1. **Bilancio ultimi 2-3 anni**: PDF, XLSX oppure inserimento manuale delle voci principali (SP + CE secondo schema civilistico artt. 2424-2425 c.c.)
2. **Settore ATECO**: codice o descrizione del settore per il confronto benchmark

Se l'utente fornisce un PDF o XLSX, estrarre le voci di bilancio e strutturarle prima di procedere. Se l'utente inserisce manualmente, guidarlo voce per voce con un template chiaro.

## Workflow — 5 Step

### Step 1: Acquisizione e Strutturazione Dati

1. Leggere il bilancio fornito (PDF/XLSX) o raccogliere le voci manualmente
2. Organizzare i dati in formato tabellare per ciascun anno
3. Verificare la quadratura: Attivo = Passivo + PN; Ricavi - Costi = Utile
4. Segnalare eventuali anomalie o voci mancanti
5. Confermare i dati con l'utente prima di procedere

**Consultare** `references/riclassificazione-guide.md` per il mapping voci civilistiche.

### Step 2: Riclassificazione SP e CE

1. **Stato Patrimoniale** — riclassificare secondo:
   - Criterio liquidita/esigibilita (attivo corrente/fisso, passivo corrente/consolidato/PN)
   - Criterio funzionale (capitale investito operativo vs accessorio)
2. **Conto Economico** — riclassificare secondo:
   - Schema a valore aggiunto (Ricavi - Costi esterni = VA - Personale = MOL/EBITDA - Ammortamenti = EBIT - OF = EBT - Imposte = Utile)
   - Schema a margini (Ricavi - COGS = Margine lordo - Spese operative = EBIT)
3. Produrre tabelle comparative 2-3 anni con variazioni assolute e percentuali

**Consultare** `references/riclassificazione-guide.md` per le istruzioni dettagliate.

### Step 3: Calcolo Indici Completi + Du Pont

1. Calcolare tutti gli indici raggruppati per area:
   - **Redditivita**: ROE, ROI, ROS, ROD, EBITDA margin, utile netto/fatturato
   - **Liquidita**: current ratio, quick ratio, CCN, CCN operativo, CCC, GG crediti, GG debiti, GG magazzino
   - **Solidita**: D/E, leverage, autonomia finanziaria, copertura immobilizzazioni, copertura oneri finanziari
   - **Efficienza**: rotazione capitale investito, fatturato/dipendente, VA/dipendente, costo lavoro/VA, incidenza materie prime
   - **Crescita**: CAGR fatturato, trend EBITDA, capex/ammortamenti, autofinanziamento
2. Eseguire la scomposizione Du Pont: ROE = ROS x Rotazione x Leva
3. Assegnare semaforo (verde/giallo/rosso) a ciascun indice in base alle soglie

**Consultare** `references/indici-bilancio-completi.md` per formule, soglie e interpretazioni.

### Step 4: Analisi Trend e Benchmark Settore

1. Analizzare il trend triennale di ogni indice (miglioramento/peggioramento/stabilita)
2. Recuperare i benchmark di settore tramite la skill `benchmark-italia-business`
3. Posizionare l'azienda rispetto alla mediana di settore per ogni area
4. Identificare i 3 principali punti di forza e le 3 principali criticita
5. Preparare i dati per il radar chart (5 aree x posizionamento vs benchmark)

### Step 5: Generazione Report DOCX + XLSX

1. **Invocare la skill `docx`** per generare il report 12-15 pagine seguendo il template in `assets/template-report-bilancio.md`
2. **Invocare la skill `xlsx`** per generare il foglio indici con:
   - Tutte le voci di bilancio riclassificate
   - Formule collegate (non valori fissi)
   - Fogli separati: SP riclassificato, CE riclassificato, Indici, Benchmark
3. Produrre il JSON di output conforme a `schemas/output-schema.json`

## Skill Invocate

| Skill | Quando |
|---|---|
| `contabilita-bilancio` | Step 1-2: verifica voci civilistiche, riclassificazione, quadratura |
| `bilancio-consolidato-analisi` | Step 2-3: riclassificazione avanzata, Du Pont, rendiconto finanziario |
| `benchmark-italia-business` | Step 4: dati benchmark mediani per settore ATECO |
| `docx` | Step 5: generazione report DOCX professionale |
| `xlsx` | Step 5: generazione foglio Excel con formule |

## Tono e Stile

- **Professionale ma didattico**: ogni indice va spiegato come se il titolare della PMI lo vedesse per la prima volta
- Usare analogie semplici (es. "Il current ratio e come il saldo disponibile rispetto alle bollette in scadenza")
- Evidenziare sempre: cosa misura, qual e il valore dell'azienda, come si confronta col settore, cosa fare per migliorarlo
- Evitare gergo tecnico non spiegato; se necessario, aggiungere una parentesi esplicativa
- Nel report, usare icone semaforo per rendere immediata la lettura

## Deliverable Finali

1. **Report DOCX** (12-15 pagine): analisi completa con tabelle, grafici e raccomandazioni
2. **Foglio XLSX**: bilancio riclassificato + indici con formule editabili
3. **JSON**: output strutturato conforme allo schema per integrazioni downstream
