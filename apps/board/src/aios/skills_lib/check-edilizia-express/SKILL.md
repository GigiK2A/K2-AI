---
name: check-edilizia-express
description: >-
  Genera un pagellino edilizio rapido (punteggio 0-100) sulla prontezza ai permessi edilizi.
  Trigger: "check edilizia", "verifica permessi", "punteggio pratica edilizia",
  "posso fare la ristrutturazione", "analisi edilizia express", "score edilizio",
  "check rapido permessi", "la mia pratica e in regola?", "BuildBoost".
  Input: tipo intervento (ristrutturazione/ampliamento/nuova costruzione/cambio uso),
  comune, zona PRG, vincoli noti.
  Output: pagella HTML visiva con semafori verde/giallo/rosso, score globale, top 5 criticita
  spiegate in italiano semplice, stima rischio bocciatura pratica,
  CTA verso progetto architettonico completo.
  Lead magnet BuildBoost per committenti e imprese edili.
allowed-tools:
  - WebFetch
---

# check-edilizia-express

Pagellino edilizio rapido per interventi edilizi: punteggio 0-100 con le 5 criticita piu urgenti.

## Panoramica

Questa skill genera un report edilizio sintetico ("pagella") pensato per committenti, imprese e professionisti che devono capire rapidamente se un intervento edilizio ha i presupposti per ottenere i necessari titoli abilitativi. Il report e comprensibile, visivo e orientato all'azione.

## Input

Parametri richiesti:

- **Tipo intervento**: ristrutturazione / ampliamento / nuova costruzione / cambio destinazione d'uso
- **Comune**: comune di riferimento dell'intervento
- **Zona PRG**: zona urbanistica (residenziale, produttiva, agricola, centro storico, ecc.)
- **Vincoli noti**: paesaggistici, monumentali, idrogeologici, altro (se conosciuti)

## Workflow

1. **Raccolta dati**: acquisisci i parametri di input dall'utente; se i vincoli non sono noti, segnala la necessita di verifica
2. **Analisi 7 fattori**: valuta ciascun fattore secondo il modello di scoring in `references/scoring-model.md`
3. **Calcolo score**: media ponderata normalizzata a 100
4. **Generazione report**: pagella HTML visiva (template in `assets/template-pagella.md`) + JSON strutturato (schema in `schemas/output-schema.json`)

## I 7 fattori analizzati

| # | Fattore | Peso |
|---|---------|------|
| 1 | Titolo abilitativo corretto | 20 |
| 2 | Conformita urbanistica | 20 |
| 3 | Vincoli paesaggistici / monumentali | 15 |
| 4 | Requisiti igienico-sanitari | 10 |
| 5 | Barriere architettoniche | 10 |
| 6 | Documentazione | 15 |
| 7 | Conformita catastale | 10 |

**Peso totale**: 100 punti.

## Output

- **Punteggio globale**: 0-100
- **Semaforo per fattore**: verde (8-10), giallo (5-7), rosso (0-4)
- **Top 5 criticita**: spiegate in italiano semplice con stima del rischio di bocciatura pratica
- **Deliverable**: HTML single-page (pagella visiva) + JSON strutturato

## Fasce di giudizio

| Fascia | Punteggio | Significato |
|--------|-----------|-------------|
| Critico | 0-30 | La pratica ha problemi gravi: alto rischio di rigetto o sanzioni |
| Insufficiente | 31-50 | Diverse criticita da risolvere prima di presentare la pratica |
| Sufficiente | 51-70 | La pratica e impostabile ma richiede integrazioni importanti |
| Buono | 71-85 | Buona base, pochi aspetti da perfezionare prima della presentazione |
| Eccellente | 86-100 | La pratica appare ben impostata, verifiche finali di dettaglio |

## Tono e linguaggio

- Diretto, comprensibile, zero gergo tecnico non spiegato
- Il committente deve capire tutto senza essere un architetto
- Spiegare le sigle (PRG, SCIA, PDC, CILA, ecc.)
- Usare esempi concreti legati al tipo di intervento
- Essere chiari sui rischi senza creare panico inutile

## Skills invocate

- `progettazione-architettonica` — per riferimenti normativi edilizi e urbanistici
- `diritto-italiano` — per quadro normativo DPR 380/2001 e regolamenti locali

## CTA

Ogni pagella chiude con un invito all'azione verso il servizio successivo: **Progetto Architettonico Completo** (progettazione integrale con gestione pratica edilizia).
