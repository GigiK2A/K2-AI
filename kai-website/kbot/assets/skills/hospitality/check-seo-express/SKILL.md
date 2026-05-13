---
name: check-seo-express
description: >-
  Genera un pagellino SEO rapido (punteggio 0-100) con le 5 criticita piu urgenti per PMI italiane.
  Trigger: "check SEO", "punteggio sito", "pagella sito", "quanto e messo il mio sito",
  "analisi rapida sito", "score SEO", "check rapido", "il mio sito va bene?",
  "farsi trovare da ChatGPT", "SEO per AI", "sito visibile su ChatGPT", "AI-readiness".
  Input: URL del sito. Analizza 11 fattori (HTTPS, mobile-friendly, velocita, title tag,
  meta description, H1, alt tag, internal linking, sitemap.xml, Google Business Profile,
  AI-readiness per citabilita LLM). Output: pagella HTML visiva con semafori verde/giallo/rosso,
  score globale, top 5 criticita spiegate in italiano semplice senza gergo tecnico,
  stima impatto su clienti persi, CTA verso audit SEO tecnico completo. Deliverable:
  HTML single-page e JSON strutturato. Lead magnet per titolari PMI italiane 5-50 dipendenti.
  Primo touchpoint consulenza web.
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

## Gli 11 fattori analizzati

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
| 11 | AI-readiness (citabilita LLM) | 6 |

**Peso totale**: 76 punti, normalizzati a 100.

### Dettaglio fattore 11 — AI-readiness

Valuta quanto il sito e "citabile" dai motori conversazionali (ChatGPT, Perplexity, Bing Copilot, Gemini). Si basa su tre sotto-criteri operativi:

| Sotto-criterio | Cosa verificare | Verde | Giallo | Rosso |
|----------------|-----------------|:-----:|:------:|:-----:|
| Struttura H pulita | H1 unico per pagina, H2/H3 gerarchici e tematici, niente salti (es. H1 → H4) | H1 unico + almeno 2 H2 tematici | H1 presente ma gerarchia irregolare | H1 assente o multipli, niente H2 |
| FAQ strutturate schema.org | Presenza di FAQPage markup su almeno una pagina principale | FAQ schema presente e compilato | FAQ testuali ma senza markup | Nessuna FAQ e nessuno schema |
| Autori dichiarati | Byline visibile, bio autore, link a profilo (LinkedIn o simile) | Autore + bio + link | Autore nominato ma senza bio | Nessuna indicazione di autore |

Il punteggio del fattore 11 e la media dei tre sotto-criteri. In fascia rossa significa che il sito non compare nelle risposte di ChatGPT anche se il contenuto e pertinente: l'LLM non trova blocchi isolabili da citare.

Spiegazione al titolare (linguaggio semplice): "Oggi molti clienti chiedono a ChatGPT o Gemini invece di cercare su Google. Se il tuo sito non e strutturato in modo che questi motori possano leggerlo e citarlo, stai perdendo una fetta di potenziali clienti che non ti vedranno mai, anche se sei in prima pagina su Google".

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

---

Aggiornato: 2026-04-17 — integrati contenuti SEO 2025 (AI search) + evoluzione algoritmo + case italiani.
