---
name: check-competitivo-express
description: >-
  Mappa competitiva rapida per PMI italiane con Competitiveness Index 0-100, lead magnet gratuito/49 euro.
  Trigger: "check competitivo", "come sono messo rispetto ai competitor", "analisi competitor rapida",
  "mappa competitiva", "chi sono i miei rivali", "quanto sono competitivo", "posizione nel mercato",
  "check strategico", "analisi concorrenza veloce".
  Input: settore, descrizione attivita, fatturato indicativo, 2-3 nomi competitor,
  elemento differenziante. Valuta 5 dimensioni (prezzo, qualita/differenziazione,
  distribuzione/accessibilita, notorieta/brand, innovazione). Output: HTML single-page con scatter chart
  posizionamento, gauge score, semafori, 2 minacce, 2 opportunita, CTA verso analisi-settore-pmi.
  Tono diretto, visivo, zero gergo strategico. Invoca strategia-competitiva e benchmark-italia-business.
  Deliverable: HTML mappa competitiva + JSON strutturato. Per titolari PMI 5-50 dip.
---

# check-competitivo-express

Mappa competitiva rapida per PMI italiane: Competitiveness Index 0-100 con 2 minacce e 2 opportunita.

## Panoramica

Questa skill genera un report competitivo sintetico pensato per titolari di PMI italiane che vogliono capire dove si posizionano rispetto ai competitor senza dover leggere analisi strategiche di 50 pagine. Il titolare descrive la sua azienda e i principali rivali, e riceve una mappa visiva immediata con indicazioni operative.

## Input

Parametri richiesti:

- **Settore**: settore merceologico di riferimento
- **Descrizione attivita**: 2-3 righe su cosa fa l'azienda
- **Fatturato indicativo**: ordine di grandezza (es. 500K, 2M, 10M)
- **2-3 nomi competitor**: i principali rivali percepiti
- **Elemento differenziante**: cosa ritieni ti differenzi dai competitor

## Workflow

1. **Inquadramento settore**: identifica dinamiche competitive del settore, margini tipici, trend. Invoca `benchmark-italia-business` per dati di riferimento settoriali.
2. **Valutazione 5 dimensioni competitive**: analizza ciascuna dimensione secondo il modello di scoring in `references/scoring-model-competitivo.md`. Invoca `strategia-competitiva` per framework di analisi.
3. **Confronto vs competitor**: posiziona l'azienda rispetto ai competitor su ciascuna dimensione, stima coordinate per scatter chart.
4. **Output**: genera mappa competitiva HTML (template in `assets/template-mappa-competitiva.md`) + JSON strutturato (schema in `schemas/output-schema.json`).

## Le 5 dimensioni competitive

| # | Dimensione | Peso | Cosa misura |
|---|-----------|------|-------------|
| 1 | Prezzo | 4 | Competitivita di prezzo rispetto al mercato |
| 2 | Qualita / Differenziazione | 5 | Unicita dell'offerta, valore percepito |
| 3 | Distribuzione / Accessibilita | 3 | Facilita di accesso per il cliente (canali, copertura, online) |
| 4 | Notorieta / Brand | 4 | Riconoscibilita, reputazione, presenza online e offline |
| 5 | Innovazione | 4 | Capacita di innovare prodotto, processo, modello di business |

**Peso totale**: 20 punti, normalizzati a indice 0-100.

## Competitiveness Index

Score globale 0-100 calcolato come media ponderata delle 5 dimensioni (dettagli in `references/scoring-model-competitivo.md`).

### Fasce di giudizio

| Fascia | Punteggio | Significato |
|--------|-----------|-------------|
| Vulnerabile | 0-30 | Posizione critica, i competitor ti stanno mangiando quote |
| In difesa | 31-50 | Reggi ma sei sotto pressione, serve reagire |
| Competitivo | 51-70 | Buona posizione, margini di miglioramento concreti |
| Forte | 71-85 | Posizione solida, puoi consolidare e attaccare |
| Dominante | 86-100 | Sei il riferimento del mercato, proteggi il vantaggio |

## Output

- **Competitiveness Index**: punteggio 0-100
- **Mappa posizionamento**: scatter chart con bolle (tu vs competitor)
- **Semaforo per dimensione**: verde/giallo/rosso per ciascuna delle 5 dimensioni
- **2 Minacce**: rischi competitivi principali, spiegati in modo concreto
- **2 Opportunita**: leve competitive da sfruttare subito
- **CTA**: rimando ad analisi-settore-pmi per approfondimento completo
- **Deliverable**: HTML single-page (mappa competitiva) + JSON strutturato

## Skill invocate

- `strategia-competitiva`: framework di analisi competitiva (5 forze, catena del valore)
- `benchmark-italia-business`: dati di riferimento settoriali per PMI italiane

## Tono e linguaggio

- Diretto, visivo, zero gergo strategico
- Il titolare deve capire tutto senza consulente accanto
- Esempi: "I tuoi competitor hanno prezzi piu bassi e sono piu visibili online -- ma tu hai una specializzazione che loro non hanno. Ecco come sfruttarla."
- Mai usare termini come "value proposition", "positioning", "market share" senza spiegarli
- Sempre orientato all'azione: ogni osservazione deve suggerire cosa fare
