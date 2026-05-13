---
name: check-seo-express
description: >-
  Genera un pagellino SEO rapido (punteggio 0-100) con le 5 criticita piu urgenti per PMI italiane.
  Trigger: "check SEO", "punteggio sito", "pagella sito", "quanto e messo il mio sito",
  "analisi rapida sito", "score SEO", "check rapido", "il mio sito va bene?".
  Input: URL del sito. Analizza 10 fattori (HTTPS, mobile-friendly, velocita, title tag,
  meta description, H1, alt tag, internal linking, sitemap.xml, Google Business Profile).
  Output: pagella HTML visiva con semafori verde/giallo/rosso, score globale, top 5 criticita
  spiegate in italiano semplice senza gergo tecnico, stima impatto su clienti persi,
  CTA verso audit SEO tecnico completo. Deliverable: HTML single-page e JSON strutturato.
  Lead magnet per titolari PMI italiane 5-50 dipendenti. Primo touchpoint consulenza web.
allowed-tools:
  - WebFetch
  - fetch_page_content
  - lighthouse_audit
---

# check-seo-express

Pagellino SEO rapido per PMI italiane: punteggio 0-100 con le 5 criticita piu urgenti.

## Panoramica

Questa skill genera un report SEO sintetico ("pagella") pensato per titolari di PMI italiane che non hanno competenze tecniche. Il report e comprensibile, visivo e orientato all'azione.

## Input

Un solo parametro richiesto:

- **URL del sito** da analizzare (homepage)

## Workflow

1. **Fetch homepage**: usa `WebFetch` (modalita consulenziale) oppure `fetch_page_content` + `lighthouse_audit` (modalita piattaforma) per scaricare la pagina e ottenere dati tecnici
2. **Analisi 10 fattori**: esamina l'HTML scaricato valutando ciascun fattore secondo il modello di scoring in `references/scoring-model.md`
3. **Calcolo score**: media ponderata normalizzata a 100
4. **Generazione report**: pagella HTML visiva (template in `assets/template-pagella.md`) + JSON strutturato (schema in `schemas/output-schema.json`)

## I 10 fattori analizzati

| # | Fattore | Peso |
|---|---------|------|
| 1 | HTTPS attivo | 8 |
| 2 | Mobile-friendly | 10 |
| 3 | Velocita caricamento | 9 |
| 4 | Title tag | 8 |
| 5 | Meta description | 7 |
| 6 | H1 presente e pertinente | 7 |
| 7 | Alt tag immagini | 5 |
| 8 | Internal linking | 6 |
| 9 | Presenza sitemap.xml | 5 |
| 10 | Google Business Profile | 5 |

**Peso totale**: 70 punti, normalizzati a 100.

## Output

- **Punteggio globale**: 0-100
- **Semaforo per fattore**: verde (8-10), giallo (5-7), rosso (0-4)
- **Top 5 criticita**: spiegate in italiano semplice con stima qualitativa dell'impatto ("stai probabilmente perdendo X% di clienti potenziali")
- **Deliverable**: HTML single-page (pagella visiva) + JSON strutturato

## Fasce di giudizio

| Fascia | Punteggio | Significato |
|--------|-----------|-------------|
| Critico | 0-30 | Il sito ha problemi gravi che allontanano i clienti |
| Insufficiente | 31-50 | Ci sono parecchie cose da sistemare |
| Sufficiente | 51-70 | Il sito funziona ma perde opportunita |
| Buono | 71-85 | Buona base, si puo migliorare |
| Eccellente | 86-100 | Ottimo lavoro, dettagli da perfezionare |

## Tono e linguaggio

- Diretto, comprensibile, zero gergo tecnico
- Il titolare deve capire tutto senza aiuto
- Evitare sigle non spiegate
- Usare esempi concreti e analogie del mondo reale

## Skills invocate

- `digital-marketing-performance` — per riferimenti e benchmark SEO di settore
- `marketing:seo-audit` — per checklist SEO completa di riferimento

## CTA

Ogni pagella chiude con un invito all'azione verso il servizio successivo: **Audit SEO Tecnico** (analisi approfondita completa).
