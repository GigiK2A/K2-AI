---
name: check-strutturale-express
description: >-
  Genera un pagellino strutturale rapido (punteggio 0-100) per edifici esistenti.
  Trigger: "check strutturale", "verifica strutturale rapida", "punteggio edificio",
  "quanto e sicuro il mio edificio", "analisi strutturale express", "score strutturale",
  "check rapido struttura", "la mia struttura e sicura?", "StructBoost".
  Input: tipo edificio (residenziale/industriale/torre TLC), anno costruzione, numero piani,
  zona sismica, ultimo intervento strutturale.
  Output: pagella HTML visiva con semafori verde/giallo/rosso, score globale, top 5 criticita
  spiegate in italiano semplice, stima qualitativa del rischio,
  CTA verso verifica statica completa / relazione di calcolo.
  Lead magnet StructBoost per committenti, proprietari immobiliari e gestori patrimonio edilizio.
allowed-tools:
  - WebFetch
---

# check-strutturale-express

Pagellino strutturale rapido per edifici esistenti: punteggio 0-100 con le 5 criticita piu urgenti.

## Panoramica

Questa skill genera un report strutturale sintetico ("pagella") pensato per committenti, proprietari di immobili e gestori di patrimonio edilizio che necessitano di una prima valutazione rapida dell'adeguatezza strutturale del proprio edificio. Il report e comprensibile, visivo e orientato all'azione.

## Input

Parametri richiesti:

- **Tipo edificio**: residenziale / industriale / torre TLC / altro
- **Anno di costruzione**: anno di realizzazione dell'edificio
- **Numero di piani**: piani fuori terra (e interrati se noti)
- **Zona sismica**: zona 1 / 2 / 3 / 4 (o comune per derivarla)
- **Ultimo intervento strutturale**: anno e tipo (se presente)

## Workflow

1. **Raccolta dati**: acquisisci i parametri di input dall'utente; se manca la zona sismica, derivala dal comune tramite classificazione OPCM 3274
2. **Analisi 6 fattori**: valuta ciascun fattore secondo il modello di scoring in `references/scoring-model.md`
3. **Calcolo score**: media ponderata normalizzata a 100
4. **Generazione report**: pagella HTML visiva (template in `assets/template-pagella.md`) + JSON strutturato (schema in `schemas/output-schema.json`)

## I 6 fattori analizzati

| # | Fattore | Peso |
|---|---------|------|
| 1 | Zona sismica / PGA di riferimento | 15 |
| 2 | Vetusta della struttura | 15 |
| 3 | Stato conservativo | 15 |
| 4 | Conformita NTC 2018 + DM 58/2017 classe rischio | 20 |
| 5 | Documentazione disponibile | 15 |
| 6 | Interventi pregressi | 20 |

**Peso totale**: 100 punti.

## Output

- **Punteggio globale**: 0-100
- **Semaforo per fattore**: verde (8-10), giallo (5-7), rosso (0-4)
- **Top 5 criticita**: spiegate in italiano semplice con stima qualitativa del rischio
- **Deliverable**: HTML single-page (pagella visiva) + JSON strutturato

## Fasce di giudizio

| Fascia | Punteggio | Significato |
|--------|-----------|-------------|
| Critico | 0-30 | L'edificio presenta criticita strutturali gravi che richiedono intervento urgente |
| Insufficiente | 31-50 | Ci sono carenze significative da approfondire con urgenza |
| Sufficiente | 51-70 | La struttura regge ma ci sono margini di miglioramento importanti |
| Buono | 71-85 | Buona condizione strutturale, interventi di ottimizzazione consigliati |
| Eccellente | 86-100 | Struttura in ottimo stato, solo verifiche di routine necessarie |

## Tono e linguaggio

- Diretto, comprensibile, zero gergo tecnico non spiegato
- Il committente deve capire tutto senza essere un ingegnere
- Evitare sigle non spiegate (spiegare NTC, PGA, ecc.)
- Usare esempi concreti e analogie del mondo reale
- Quando si parla di rischio sismico, essere chiari ma non allarmistici

## Skills invocate

- `progettista-strutturale` — per riferimenti normativi NTC 2018 e criteri di verifica strutturale

## CTA

Ogni pagella chiude con un invito all'azione verso il servizio successivo: **Verifica Statica Completa / Relazione di Calcolo** (analisi approfondita con sopralluogo e prove in situ).
