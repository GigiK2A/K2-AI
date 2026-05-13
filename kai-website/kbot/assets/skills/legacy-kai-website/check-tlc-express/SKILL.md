---
name: check-tlc-express
description: >-
  Genera un pagellino TLC rapido (punteggio 0-100) sulla complessita e prontezza di un sito telecomunicazioni.
  Trigger: "check TLC", "verifica sito TLC", "punteggio sito telecomunicazioni",
  "quanto e complesso il sito", "analisi TLC express", "score TLC",
  "check rapido sito", "il sito e fattibile?", "TLCBoost".
  Input: tipo sito (rawland/rooftop/colocation), operatore (Iliad/Cellnex/altro),
  coordinate, vincoli noti, tipo intervento (new site/upgrade/transfer).
  Output: pagella HTML visiva con semafori verde/giallo/rosso, score globale, top 5 criticita
  spiegate in italiano semplice, stima complessita progettuale,
  CTA verso progetto esecutivo PE completo.
  Lead magnet TLCBoost per operatori, towerco e progettisti TLC.
allowed-tools:
  - WebFetch
---

# check-tlc-express

Pagellino TLC rapido per siti telecomunicazioni: punteggio 0-100 con le 5 criticita piu urgenti.

## Panoramica

Questa skill genera un report sintetico ("pagella") sulla complessita e prontezza progettuale di un sito di telecomunicazioni, pensato per operatori, tower company e progettisti che necessitano di una prima valutazione rapida della fattibilita e delle criticita di un sito. Il report e comprensibile, visivo e orientato all'azione.

## Input

Parametri richiesti:

- **Tipo sito**: rawland / rooftop / colocation
- **Operatore**: Iliad / Cellnex / altro (specificare)
- **Coordinate**: latitudine e longitudine del sito
- **Vincoli noti**: paesaggistici, ENAC, militari, ambientali (se conosciuti)
- **Tipo intervento**: new site / upgrade / transfer

## Workflow

1. **Raccolta dati**: acquisisci i parametri di input dall'utente; se i vincoli non sono noti, segnala la necessita di verifica su geoportali
2. **Analisi 6 fattori**: valuta ciascun fattore secondo il modello di scoring in `references/scoring-model.md`
3. **Calcolo score**: media ponderata normalizzata a 100
4. **Generazione report**: pagella HTML visiva (template in `assets/template-pagella.md`) + JSON strutturato (schema in `schemas/output-schema.json`)

## I 6 fattori analizzati

| # | Fattore | Peso |
|---|---------|------|
| 1 | Complessita urbanistica | 15 |
| 2 | Vincoli paesaggistici / ENAC | 20 |
| 3 | Accessibilita area | 10 |
| 4 | Complessita strutturale | 20 |
| 5 | Complessita impiantistica | 15 |
| 6 | Documentazione necessaria | 20 |

**Peso totale**: 100 punti.

## Output

- **Punteggio globale**: 0-100 (dove 100 = massima prontezza, minima complessita)
- **Semaforo per fattore**: verde (8-10), giallo (5-7), rosso (0-4)
- **Top 5 criticita**: spiegate in italiano chiaro con stima dell'impatto su tempi e costi
- **Deliverable**: HTML single-page (pagella visiva) + JSON strutturato

## Fasce di giudizio

| Fascia | Punteggio | Significato |
|--------|-----------|-------------|
| Critico | 0-30 | Sito con complessita molto elevata: iter lungo e costoso, valutare alternative |
| Insufficiente | 31-50 | Diverse criticita da risolvere: iter complesso con rischi significativi |
| Sufficiente | 51-70 | Sito fattibile ma con complessita da gestire attentamente |
| Buono | 71-85 | Buona fattibilita, complessita gestibile con progettazione adeguata |
| Eccellente | 86-100 | Sito con iter semplice e complessita minima |

## Tono e linguaggio

- Diretto, comprensibile, tecnico ma accessibile
- Il project manager deve capire le criticita senza essere un progettista
- Spiegare le sigle (PE, ENAC, SRB, TSSR, ecc.)
- Usare esempi concreti legati al tipo di sito e operatore
- Essere pragmatici: focus su tempi, costi e rischi

## Skills invocate

- `progettazione-architettonica` — per riferimenti urbanistici e autorizzativi
- `architetto-beni-monumentali` — per vincoli paesaggistici e Soprintendenza

## CTA

Ogni pagella chiude con un invito all'azione verso il servizio successivo: **Progetto Esecutivo PE Completo** (progettazione esecutiva integrale del sito TLC).
