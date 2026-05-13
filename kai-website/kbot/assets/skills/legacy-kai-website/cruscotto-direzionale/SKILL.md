---
name: cruscotto-direzionale
description: >-
  Dashboard KPI mensile per titolari PMI italiane (5-50 dipendenti). Genera un cruscotto direzionale
  con le 4 prospettive Balanced Scorecard (finanziaria, cliente, processi interni, crescita) adattate
  alla realta delle piccole e medie imprese. Raccoglie dati mensili (fatturato, costi, incassi, clienti,
  ore lavorate, scarti), calcola KPI con confronto vs target/budget, mese precedente e stesso mese anno
  prima, genera sistema alert a semaforo (verde/giallo/rosso) con cause probabili e azioni suggerite.
  Output: dashboard HTML interattiva self-contained con Chart.js, file XLSX con input/KPI/storico/grafici,
  JSON strutturato. Servizio ricorrente mensile: il titolare inserisce i dati, riceve il cruscotto
  aggiornato in 5 minuti. Ogni anomalia salta all'occhio. Tono sintetico, visivo, actionable.
---

# Cruscotto Direzionale — Dashboard KPI Mensile per PMI

## Trigger

Questa skill si attiva quando l'utente chiede:
- "cruscotto"
- "dashboard aziendale"
- "KPI mensili"
- "monitoraggio aziendale"
- "report mensile"
- "come va l'azienda questo mese"
- "indicatori aziendali"
- "cruscotto direzionale"
- "tableau de bord"
- "BSC"
- "balanced scorecard"
- "cockpit aziendale"

## Input richiesti

### Dati mensili (adattabili per settore)
- **Fatturato** del mese
- **Costi operativi** del mese (personale, materie prime, servizi, affitti, utenze)
- **Incassi** del mese e **pagamenti** effettuati
- **Nuovi clienti** acquisiti nel mese
- **Clienti persi** (churn) nel mese
- **Ore lavorate** (totali e fatturabili, per aziende di servizi)
- **Scarti / resi / reclami** (per aziende di produzione)
- **Posizione di cassa** a fine mese

### KPI target
- Da budget annuale (se disponibile) oppure da impostazione iniziale concordata col titolare
- Se non disponibili, usare benchmark di settore via skill `benchmark-italia-business`

### Dati storici
- Dati dei mesi precedenti per calcolo trend (idealmente 12 mesi)
- Se primo mese, il cruscotto parte senza confronti storici e li costruisce progressivamente

## Workflow (4 step)

### Step 1 — Raccolta e validazione dati mensili

1. Richiedere al titolare i dati del mese tramite checklist strutturata
2. Validare completezza: segnalare dati mancanti, proporre stime ragionevoli per dati non disponibili
3. Verificare coerenza: fatturato vs incassi, costi vs pagamenti, totali vs dettagli
4. Se dati arrivano da XLSX precedente (tab "Input Mensile"), estrarre automaticamente

**Output step 1:** dataset mensile validato

### Step 2 — Calcolo KPI per le 4 prospettive BSC

Invocare skill `controllo-gestione-bocconi` per framework BSC e `programmazione-controllo` per analisi scostamenti.

Per ogni KPI selezionato (10-12 rilevanti per il settore specifico, vedi `references/kpi-selection-pmi.md`):

1. **Calcolo valore attuale** con formula specifica
2. **Confronto vs target** (da budget o benchmark): calcolo scostamento % e assoluto
3. **Confronto vs mese precedente**: variazione % e direzione (freccia su/giu)
4. **Confronto vs stesso mese anno precedente**: variazione % anno su anno
5. **Assegnazione semaforo** secondo `references/alert-system.md`

**Prospettive calcolate:**

| Prospettiva | KPI principali |
|---|---|
| Finanziaria | Fatturato, EBITDA, Cash flow operativo, GG medi incasso, Posizione cassa |
| Cliente | Clienti attivi, Nuovi clienti, Churn, Fatturato medio/cliente, Concentrazione top 5 |
| Processi | Ore fatturabili/totali, Tasso scarti, Lead time, Reclami, Tempo evasione ordine |
| Crescita | Ore formazione, Nuovi prodotti/servizi, Investimenti innovazione, Turnover |

Invocare `benchmark-italia-business` per confronto con medie di settore quando i target interni non sono disponibili.

**Output step 2:** tabella KPI completa con valori, target, scostamenti, semafori

### Step 3 — Generazione alert

Per ogni KPI, applicare il sistema alert definito in `references/alert-system.md`:

1. **Semaforo a 3 livelli:** verde (in target), giallo (deviazione 10-20%), rosso (deviazione >20%)
2. **Alert descrittivi per KPI rossi:** descrizione deviazione + 2-3 ipotesi di causa + azione suggerita
3. **Trend alert:** identificare KPI in peggioramento per 3+ mesi consecutivi anche se ancora verdi
4. **Concentrazione alert:** segnalare se top 3 clienti pesano >40% del fatturato
5. **Executive summary:** 3-5 righe che sintetizzano lo stato dell'azienda nel mese

**Output step 3:** lista alert con priorita, executive summary

### Step 4 — Generazione deliverable

Generare tre output usando i template in `assets/`:

1. **Dashboard HTML** (template: `assets/template-cruscotto-html.md`)
   - File HTML self-contained con Chart.js embedded
   - Card KPI principali con semafori e frecce
   - Grafici interattivi per ogni prospettiva BSC
   - Sezione alert con cause e azioni
   - Responsive e stampabile

2. **File XLSX** (template: `assets/template-cruscotto-xlsx.md`)
   - Invocare skill `xlsx` per generazione
   - 4 tab: Input Mensile, KPI Dashboard, Storico 12 mesi, Grafici
   - Formattazione condizionale per semafori
   - Pronto per il mese successivo (tab Input gia preparata)

3. **JSON strutturato** (schema: `schemas/output-schema.json`)
   - Tutti i KPI con metadati completi
   - Alert strutturati
   - Trend 12 mesi
   - Utilizzabile per integrazioni e automazioni

**Output step 4:** 3 file (HTML, XLSX, JSON)

## Skill invocate

| Skill | Utilizzo |
|---|---|
| `controllo-gestione-bocconi` | Framework BSC, metriche di controllo, analisi scostamenti |
| `programmazione-controllo` | Budget vs consuntivo, analisi varianze |
| `benchmark-italia-business` | Confronto con medie di settore per target e posizionamento |
| `xlsx` | Generazione file XLSX con formattazione e grafici |

## Deliverable finali

1. **Dashboard HTML interattiva** — file `.html` self-contained, apribile in qualsiasi browser
2. **XLSX aggiornato** — file `.xlsx` con dati, KPI, storico e grafici, pronto per il mese successivo
3. **JSON strutturato** — file `.json` conforme allo schema in `schemas/output-schema.json`

## Modello di servizio ricorrente

Questo cruscotto e pensato come servizio **mensile ricorrente** (499 euro/mese):

- **Mese 1:** Setup iniziale — definizione KPI rilevanti per il settore, impostazione target, primo cruscotto
- **Mesi successivi:** Il titolare inserisce i dati nella tab "Input Mensile" dell'XLSX (o li comunica), riceve il cruscotto aggiornato
- **Ogni trimestre:** Revisione KPI selezionati e target sulla base dell'andamento
- **Valore per il titolare:** In 5 minuti capisce come va l'azienda, cosa richiede attenzione, cosa fare

## Tono e stile

- **Sintetico:** niente muri di testo, solo numeri e visual
- **Visivo:** semafori, frecce, grafici — tutto deve essere comprensibile a colpo d'occhio
- **Actionable:** ogni anomalia ha una causa ipotizzata e un'azione suggerita
- **Professionale ma accessibile:** il titolare non e un controller, deve capire tutto senza glossario
