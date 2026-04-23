---
name: check-sicurezza-express
description: >-
  Genera un pagellino sicurezza cantiere rapido (punteggio 0-100) sulla conformita D.Lgs. 81/2008.
  Trigger: "check sicurezza", "verifica sicurezza cantiere", "punteggio sicurezza",
  "il mio cantiere e in regola", "analisi sicurezza express", "score sicurezza",
  "check rapido cantiere", "devo fare il PSC?", "SafetyBoost".
  Input: tipo cantiere/attivita, numero imprese, durata presunta, entita lavoro (uomo/giorno),
  tipo committente.
  Output: pagella HTML visiva con semafori verde/giallo/rosso, score globale, top 5 criticita
  spiegate in italiano semplice, stima rischio sanzioni,
  CTA verso redazione PSC completo / DVR.
  Lead magnet SafetyBoost per committenti, imprese e coordinatori.
allowed-tools:
  - WebFetch
---

# check-sicurezza-express

Pagellino sicurezza cantiere rapido: punteggio 0-100 con le 5 criticita piu urgenti.

## Panoramica

Questa skill genera un report sintetico ("pagella") sulla conformita in materia di sicurezza nei cantieri e nei luoghi di lavoro, pensato per committenti, imprese e responsabili della sicurezza che necessitano di una prima valutazione rapida degli obblighi e delle criticita. Il report e comprensibile, visivo e orientato all'azione.

## Input

Parametri richiesti:

- **Tipo cantiere/attivita**: edile, impiantistico, manutenzione, ristrutturazione, ecc.
- **Numero imprese**: quante imprese esecutrici sono coinvolte
- **Durata presunta**: durata stimata dei lavori in giorni
- **Entita lavoro**: stima uomini/giorno complessivi
- **Tipo committente**: pubblico / privato

## Workflow

1. **Raccolta dati**: acquisisci i parametri di input dall'utente; verifica soglie Allegato XI D.Lgs. 81/2008
2. **Analisi 6 fattori**: valuta ciascun fattore secondo il modello di scoring in `references/scoring-model.md`
3. **Calcolo score**: media ponderata normalizzata a 100
4. **Generazione report**: pagella HTML visiva (template in `assets/template-pagella.md`) + JSON strutturato (schema in `schemas/output-schema.json`)

## I 6 fattori analizzati

| # | Fattore | Peso |
|---|---------|------|
| 1 | Obbligo PSC | 20 |
| 2 | Nomina CSP/CSE | 15 |
| 3 | Notifica preliminare | 10 |
| 4 | POS imprese | 15 |
| 5 | Formazione lavoratori | 20 |
| 6 | DPI e attrezzature | 20 |

**Peso totale**: 100 punti.

## Output

- **Punteggio globale**: 0-100
- **Semaforo per fattore**: verde (8-10), giallo (5-7), rosso (0-4)
- **Top 5 criticita**: spiegate in italiano semplice con stima del rischio sanzionatorio
- **Deliverable**: HTML single-page (pagella visiva) + JSON strutturato

## Fasce di giudizio

| Fascia | Punteggio | Significato |
|--------|-----------|-------------|
| Critico | 0-30 | Il cantiere presenta gravi carenze: rischio sanzioni penali e sospensione lavori |
| Insufficiente | 31-50 | Diverse criticita da risolvere urgentemente per evitare sanzioni |
| Sufficiente | 51-70 | Il cantiere e avviabile ma servono integrazioni documentali importanti |
| Buono | 71-85 | Buona conformita, pochi aspetti da perfezionare |
| Eccellente | 86-100 | Cantiere ben organizzato, solo verifiche di routine |

## Tono e linguaggio

- Diretto, comprensibile, zero gergo tecnico non spiegato
- Il committente deve capire tutto senza essere un esperto di sicurezza
- Spiegare le sigle (PSC, POS, CSP, CSE, DPI, DVR, ecc.)
- Essere chiari sui rischi sanzionatori senza creare allarmismo
- Usare esempi concreti legati al tipo di cantiere

## Skills invocate

- `psc-coordinamento-sicurezza` — per riferimenti normativi e struttura PSC
- `consulente-sicurezza-lavoro` — per obblighi D.Lgs. 81/2008 e DVR

## CTA

Ogni pagella chiude con un invito all'azione verso il servizio successivo: **Redazione PSC Completo / DVR** (piano di sicurezza e coordinamento o documento di valutazione rischi).
