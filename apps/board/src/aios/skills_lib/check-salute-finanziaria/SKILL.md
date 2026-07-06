---
name: check-salute-finanziaria
description: >-
  Genera un semaforo finanziario con 5 KPI colorati per PMI italiane partendo da 5-6 numeri di bilancio.
  Trigger: "check finanziario", "come sta la mia azienda", "salute finanziaria", "semaforo bilancio",
  "KPI azienda", "check bilancio rapido", "la mia azienda va bene?", "controllo finanziario veloce",
  "pagella finanziaria". Input minimi: fatturato, utile netto, totale attivo, debiti totali,
  crediti commerciali, settore. Opzionali: magazzino, debiti commerciali, patrimonio netto.
  Calcola 5 KPI (ROE, Current Ratio, Indebitamento D/E, Margine Netto, Giorni Crediti) con semaforo
  verde/giallo/rosso e soglie specifiche per settore tramite benchmark-italia-business. Output: pagella
  HTML responsiva con score globale 0-100, 5 semafori KPI con confronto settore, 3 aree da approfondire,
  CTA verso analisi-bilancio-pmi. Tono: comprensibile dal titolare senza competenze contabili.
  Lead magnet gratuito o 49 euro per PMI italiane 5-50 dipendenti.
---

# check-salute-finanziaria

Semaforo finanziario rapido per PMI italiane: 5 KPI colorati + score 0-100 partendo da pochi numeri di bilancio.

## Panoramica

Questa skill genera un report di salute finanziaria ("semaforo") pensato per titolari di PMI italiane che non sanno leggere un bilancio. Il titolare inserisce 5-6 numeri, riceve una pagella visiva con semafori colorati, confronto con il proprio settore e indicazioni chiare su cosa migliorare.

## Input

### Obbligatori
- **Fatturato** (ricavi netti annui)
- **Utile netto** (risultato netto di esercizio)
- **Totale attivo** (totale attivo stato patrimoniale)
- **Debiti totali** (totale debiti)
- **Crediti commerciali** (crediti verso clienti)
- **Settore** (manifatturiero, servizi, commercio, ristorazione, edilizia, IT, trasporti, professionisti)

### Opzionali
- **Magazzino** (rimanenze) - migliora precisione Current Ratio
- **Debiti commerciali** (debiti verso fornitori) - usato come proxy debiti a breve se non specificato
- **Patrimonio netto** - se non fornito, calcolato come Totale Attivo - Debiti Totali

## Workflow

1. **Raccolta dati**: chiedi i 6 input obbligatori in modo semplice, con esempi ("il fatturato lo trovi nella prima riga del conto economico"). Se il titolare non sa un dato, guida con domande semplici.
2. **Calcolo patrimonio netto**: se non fornito, PN = Totale Attivo - Debiti Totali.
3. **Calcolo 5 KPI**: applica le formule del modello di scoring in `references/scoring-model-finanziario.md`.
4. **Benchmark settore**: invoca la skill `benchmark-italia-business` per ottenere le mediane di settore dei 5 KPI e confrontarle con i valori calcolati.
5. **Assegnazione semafori**: per ogni KPI, verde/giallo/rosso secondo le soglie settoriali definite nel modello di scoring.
6. **Score globale**: media ponderata normalizzata 0-100.
7. **Top 3 approfondimenti**: seleziona i 3 KPI piu critici (rosso prima, poi giallo) e genera suggerimenti concreti in italiano semplice.
8. **Generazione output**: pagella HTML responsiva (template in `assets/template-semaforo.md`) + JSON strutturato (schema in `schemas/output-schema.json`).

## I 5 KPI analizzati

| # | KPI | Formula | Cosa misura |
|---|-----|---------|-------------|
| 1 | ROE | Utile Netto / Patrimonio Netto | Quanto rende il capitale investito dai soci |
| 2 | Current Ratio | (Crediti + Magazzino) / Debiti a breve | Se riesci a pagare i debiti che scadono presto |
| 3 | Indebitamento (D/E) | Debiti Totali / Patrimonio Netto | Quanto pesa il debito rispetto al capitale proprio |
| 4 | Margine Netto | Utile Netto / Fatturato | Quanto guadagni davvero su ogni euro fatturato |
| 5 | Giorni Crediti | (Crediti / Fatturato) x 365 | Quanti giorni aspetti prima di incassare |

## Regole di comunicazione

- **Mai usare gergo tecnico** senza spiegarlo: "ROE" diventa "quanto rende il tuo capitale"
- **Ogni KPI ha un giudizio in una frase**: "I tuoi clienti ti pagano in 95 giorni, la media del tuo settore e 60. Stai facendo da banca ai tuoi clienti."
- **Semaforo visivo**: verde = tutto ok, giallo = attenzione, rosso = agire subito
- **Score globale**: un numero da 0 a 100 con fascia (Critico/Fragile/Sufficiente/Solido/Eccellente)
- **Sempre chiudere con azione**: le 3 cose che dovresti approfondire + CTA verso analisi completa

## Skill invocate

- `benchmark-italia-business`: per ottenere mediane e percentili di settore dei KPI finanziari

## Output

Due file consegnati:

1. **Pagella HTML** (`semaforo-finanziario.html`): report visivo responsivo con score circolare, 5 card KPI con semafori, box approfondimenti, CTA upsell
2. **JSON strutturato** (`semaforo-finanziario.json`): dati machine-readable secondo lo schema in `schemas/output-schema.json`

## Pricing

- **Versione gratuita**: semaforo con 5 KPI e score globale
- **Versione 49 euro**: include confronto settore dettagliato, trend storici, piano d'azione personalizzato e call con consulente
