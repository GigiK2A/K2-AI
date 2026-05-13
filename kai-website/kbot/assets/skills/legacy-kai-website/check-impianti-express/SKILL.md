---
name: check-impianti-express
description: >-
  Genera un pagellino impiantistico rapido (punteggio 0-100) sulla conformita impianti elettrici e HVAC.
  Trigger: "check impianti", "verifica impianti", "punteggio impianti",
  "i miei impianti sono a norma", "analisi impiantistica express", "score impianti",
  "check rapido impianti", "impianto elettrico a norma?", "MEPBoost".
  Input: tipo edificio, anno impianti, potenza impegnata, sistema riscaldamento,
  classe energetica attuale (se nota).
  Output: pagella HTML visiva con semafori verde/giallo/rosso, score globale, top 5 criticita
  spiegate in italiano semplice, stima rischio non conformita,
  CTA verso audit impiantistico completo / diagnosi energetica.
  Lead magnet MEPBoost per proprietari, amministratori e facility manager.
allowed-tools:
  - WebFetch
---

# check-impianti-express

Pagellino impiantistico rapido per edifici: punteggio 0-100 con le 5 criticita piu urgenti.

## Panoramica

Questa skill genera un report impiantistico sintetico ("pagella") pensato per proprietari di immobili, amministratori di condominio e facility manager che necessitano di una prima valutazione rapida della conformita e dell'efficienza degli impianti elettrici e termici del proprio edificio. Il report e comprensibile, visivo e orientato all'azione.

## Input

Parametri richiesti:

- **Tipo edificio**: residenziale / commerciale / industriale / terziario
- **Anno impianti**: anno di installazione o ultima revisione importante
- **Potenza impegnata**: potenza elettrica contrattuale in kW
- **Sistema riscaldamento**: caldaia autonoma / centralizzato / pompa di calore / altro
- **Classe energetica attuale**: A4-G (se nota, altrimenti "non nota")

## Workflow

1. **Raccolta dati**: acquisisci i parametri di input dall'utente; se la classe energetica non e nota, stimala sulla base dell'anno e del tipo di impianto
2. **Analisi 7 fattori**: valuta ciascun fattore secondo il modello di scoring in `references/scoring-model.md`
3. **Calcolo score**: media ponderata normalizzata a 100
4. **Generazione report**: pagella HTML visiva (template in `assets/template-pagella.md`) + JSON strutturato (schema in `schemas/output-schema.json`)

## I 7 fattori analizzati

| # | Fattore | Peso |
|---|---------|------|
| 1 | Conformita DM 37/2008 | 20 |
| 2 | Impianto di terra | 15 |
| 3 | Protezioni differenziali | 10 |
| 4 | Classe energetica | 15 |
| 5 | Efficienza generazione | 15 |
| 6 | Regolazione e contabilizzazione | 10 |
| 7 | Manutenzione | 15 |

**Peso totale**: 100 punti.

## Output

- **Punteggio globale**: 0-100
- **Semaforo per fattore**: verde (8-10), giallo (5-7), rosso (0-4)
- **Top 5 criticita**: spiegate in italiano semplice con stima del rischio e del potenziale risparmio
- **Deliverable**: HTML single-page (pagella visiva) + JSON strutturato

## Fasce di giudizio

| Fascia | Punteggio | Significato |
|--------|-----------|-------------|
| Critico | 0-30 | Gli impianti presentano gravi non conformita: rischio sicurezza e sanzioni |
| Insufficiente | 31-50 | Diverse criticita da risolvere per garantire sicurezza e conformita |
| Sufficiente | 51-70 | Gli impianti funzionano ma ci sono margini importanti di adeguamento |
| Buono | 71-85 | Buona conformita, possibili miglioramenti di efficienza energetica |
| Eccellente | 86-100 | Impianti a norma ed efficienti, solo manutenzione ordinaria |

## Tono e linguaggio

- Diretto, comprensibile, zero gergo tecnico non spiegato
- Il proprietario deve capire tutto senza essere un impiantista
- Spiegare le sigle (DM, DiCo, DiRi, APE, COP, ecc.)
- Usare esempi concreti e analogie del mondo reale
- Quando si parla di rischio elettrico, essere chiari ma non allarmistici

## Skills invocate

- `impianti-elettrici` — per riferimenti normativi CEI e DM 37/2008
- `impianti-termici-hvac` — per riferimenti su efficienza energetica e normativa termica

## CTA

Ogni pagella chiude con un invito all'azione verso il servizio successivo: **Audit Impiantistico Completo / Diagnosi Energetica** (verifica approfondita con sopralluogo e strumentazione).
