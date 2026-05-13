---
name: content-factory
description: >-
  Servizio retainer mensile di produzione contenuti SEO per PMI italiane
  (599-1.299 EUR/mese). Tre piani: Light 4 articoli/mese, Standard 6
  articoli/mese, Intensive 8 articoli/mese. Workflow 6 step ricorrente:
  piano editoriale mensile, brief SEO per articolo, drafting con keyword
  primaria e secondarie, refresh 2-4 articoli esistenti, ottimizzazione
  on-page e meta, report KPI con posizionamento e traffico. Output
  ricorrente: calendario editoriale XLSX, brief DOCX per articolo, articoli
  DOCX pronti CMS, report mensile DOCX, JSON strutturato. Attiva per:
  content factory, produzione contenuti, piano editoriale, articoli per
  il blog, content marketing PMI, chi mi scrive gli articoli, blog
  aziendale, contenuti SEO ricorrenti, servizio editoriale mensile,
  refresh contenuti, aggiornare vecchi articoli, piano editoriale mensile,
  content strategy ricorrente, aumentare traffico organico, content
  retainer. Quarto livello della suite WebBoost dopo check express,
  audit tecnico e keyword strategy.
---

# content-factory

Servizio ricorrente mensile di produzione contenuti SEO per PMI italiane. Il cliente ha fatto l'audit SEO, ha la keyword map, ma non ha il tempo né le competenze per produrre contenuti mese dopo mese. Questa skill produce il calendario editoriale, scrive gli articoli, rinfresca i vecchi e misura i risultati.

## Posizionamento nella suite WebBoost

Questa skill è il quarto livello (retainer ricorrente) della suite WebBoost, dopo:

1. **check-seo-express** (gratis/49 EUR) — pagella SEO, lead magnet
2. **audit-seo-tecnico** (249 EUR) — diagnosi tecnica one-shot
3. **keyword-strategy** (349 EUR) — keyword map e piano assegnazione pagine (one-shot)
4. **content-factory** (599-1.299 EUR/mese) — ← **TU SEI QUI**, esecuzione ricorrente mensile

Presuppone che il cliente abbia già svolto (o stia per svolgere) `audit-seo-tecnico` e soprattutto `keyword-strategy`. Se manca la keyword map, il primo mese include la sua costruzione nel piano editoriale iniziale.

## Piani disponibili

| Piano | Prezzo/mese | Articoli nuovi | Refresh | Durata articolo | Altro |
|---|---|---|---|---|---|
| **Light** | 599 EUR | 4 | 2 | 800-1.200 parole | Meta title/description, 1 CTA |
| **Standard** | 899 EUR | 6 | 3 | 1.000-1.500 parole | + schema markup FAQ, internal link audit |
| **Intensive** | 1.299 EUR | 8 | 4 | 1.200-2.000 parole | + pillar page (1/trimestre), email brief prospect mensile |

Minimum commitment: 3 mesi (per dare tempo all'indicizzazione di produrre risultati misurabili).

## Input richiesto

### Mese 1 (setup)

| Parametro | Obbligatorio | Descrizione |
|-----------|:---:|-------------|
| URL sito | Sì | Dominio del cliente |
| Settore e micro-nicchia | Sì | es. "idraulico specializzato caldaie condensazione", "commercialista forfettari freelance" |
| Target cliente | Sì | Persona tipo, dolori, obiezioni, livello di consapevolezza |
| Tone of voice | Sì | Formale/informale, tu/lei, emoji sì/no, esempi di contenuti che piacciono al cliente |
| Keyword map | No | Se disponibile (da `keyword-strategy`), altrimenti la costruiamo |
| 3 competitor editoriali | Sì | Siti da cui vuole "rubare" temi e angoli |
| Piano scelto | Sì | Light / Standard / Intensive |
| Pagina blog del sito | Sì | Dove andranno pubblicati i contenuti (o se non esiste, proposta CMS) |
| Obiettivo business | Sì | Lead, vendite e-commerce, prenotazioni, visite al negozio |

### Mesi 2+ (esecuzione)

Feedback sul mese precedente: articoli performanti, temi da approfondire, cambiamenti nel business (nuovo servizio, promo stagionale, eventi).

## Workflow mensile — 6 step

### Step 1 — Piano editoriale del mese

Obiettivo: decidere i 4-8 argomenti del mese, basati su keyword map e calendario business.

Fonti degli argomenti (in ordine di priorità):
1. **Keyword cluster ad alta priorità** non ancora coperti (dalla keyword map)
2. **Stagionalità e ricorrenze** (meteo, scadenze fiscali, festività rilevanti per il settore)
3. **Eventi aziendali del cliente** (nuovo prodotto, fiera, promo)
4. **Trending topics del settore** (rilevati via Google Trends, forum, social)
5. **Gap vs competitor** (temi che i competitor trattano e il cliente no)

Per ogni argomento: keyword primaria, 2-4 keyword secondarie, intent dominante (I/N/C/T), pagina del sito di destinazione, data di pubblicazione, autore (Claude + review umana cliente), priorità.

**Skill invocata**: `keyword-strategy` se la keyword map non esiste o è da aggiornare. `digital-marketing-performance` per identificare trending topics.

**Deliverable step 1**: calendario editoriale XLSX con 4-8 righe, una per articolo.

### Step 2 — Brief SEO per ogni articolo

Obiettivo: dare al redattore (Claude o umano) tutto il necessario per scrivere senza improvvisare.

Template brief (vedi `references/template-brief-seo.md`):
- Titolo proposto (con keyword primaria)
- URL slug
- Meta title (≤60 caratteri) e meta description (≤155 caratteri)
- Keyword primaria e secondarie
- Intent e pagine SERP da battere (analisi top 5 Google su quella keyword)
- Outline H2/H3 dettagliato
- Domande da rispondere (People Also Ask)
- Internal link target (pagine del sito da linkare)
- CTA desiderata (contatto, preventivo, download, acquisto)
- Tone of voice memo
- Media: immagini/video suggeriti (alt text incluso)

**Deliverable step 2**: un file DOCX `brief-[slug].docx` per ogni articolo.

### Step 3 — Drafting articoli

Obiettivo: produrre i draft secondo brief, rispettando SEO on-page e tone of voice.

Regole tecniche:
- Keyword primaria nel primo paragrafo, nel H1, in 2-3 H2, nella conclusione
- Densità keyword 1-2% (mai keyword stuffing)
- Paragrafi brevi (3-5 righe) per mobile readability
- Internal link a 2-3 pagine del sito
- External link a 1-2 fonti autorevoli (se pertinente)
- Lunghezza da piano (vedi tabella Piani)
- FAQ finale con 3-5 domande (schema markup per Intensive)
- CTA in fondo e a metà articolo

Regole editoriali:
- Esempi concreti dal settore del cliente, non generici
- Evitare "il cliente", "l'utente" — parlare in seconda persona al lettore target
- Aprire con un hook concreto (caso, numero, domanda)
- Chiudere con azione chiara, non con "spero vi sia piaciuto"

**Skill invocata**: `psicologia-marketing` per hook, storytelling e CTA. `ux-copy-review` per qualità copy. `marketing-strategico` se il contenuto è commerciale (pagina servizio, landing).

**Deliverable step 3**: un file DOCX `articolo-[slug].docx` per ogni articolo, pronto per CMS (markdown + HTML ready, immagini placeholder con alt text).

### Step 4 — Refresh articoli esistenti

Obiettivo: aggiornare 2-4 articoli vecchi che stanno perdendo posizionamento o sono obsoleti.

Criteri di selezione articoli da refreshare:
- Posizionavano bene (pagina 1-2) e stanno scivolando
- Info obsolete (dati, prezzi, normativa, anno)
- Keyword primaria ora ha intent diverso
- Meta title/description vecchi o non ottimizzati
- Mancanza di CTA o CTA datata

Azioni tipiche refresh:
- Aggiornare dati, screenshot, anno, citazioni
- Espandere sezioni deboli (se la SERP oggi vuole più lunghezza)
- Riscrivere intro con hook più forte
- Aggiornare meta title/description
- Aggiungere FAQ / schema markup
- Rafforzare internal linking
- Aggiungere/modificare CTA

**Skill invocata**: `audit-seo-tecnico` per identificare articoli con problemi tecnici. `ux-copy-review` per il refresh CTA.

**Deliverable step 4**: per ogni articolo refreshato, un DOCX `refresh-[slug].docx` con modifiche evidenziate (tracked changes logic).

### Step 5 — Ottimizzazione on-page e pubblicazione guidata

Obiettivo: garantire che i contenuti, una volta pubblicati, siano ottimizzati tecnicamente.

Checklist per ogni articolo (vedi `references/checklist-pubblicazione.md`):
- Meta title/description corretti (preview Google)
- URL slug ottimizzato (short, keyword, trattini)
- H1 unico e con keyword primaria
- Immagini con alt text SEO e compressione (WebP se possibile)
- Internal link funzionanti
- CTA visibile sopra e sotto la piega
- Schema markup (Article, FAQ, Recipe, HowTo a seconda del tipo)
- Responsive check su mobile
- Open Graph e Twitter Card per condivisione social
- Indicizzazione: richiesta via Search Console

Il cliente pubblica sul proprio CMS (o il ns. redattore umano se previsto da contratto). Forniamo la checklist compilata pubblicazione per pubblicazione.

**Deliverable step 5**: file `checklist-[slug].md` con tutti gli item verificati o pending.

### Step 6 — Report KPI mensile

Obiettivo: misurare l'impatto dei contenuti prodotti e pianificare il mese successivo.

KPI tracciati mese su mese:
- **Traffico organico totale** (sessions, users) — trend vs mese precedente e stesso mese anno prima
- **Traffico articoli prodotti dalla factory** — sessioni generate dagli articoli degli ultimi 3, 6, 12 mesi
- **Posizionamento keyword target** — top 3, top 10, top 20, pagina 2+
- **Click-through rate SERP** (da Search Console)
- **Tempo di lettura medio** degli articoli
- **Scroll depth** (se Hotjar/Clarity attivi)
- **Conversioni assistite** dai contenuti (lead form, contatti, acquisti) se Analytics configurato
- **Backlink** generati organicamente

Benchmark di successo (realistici per PMI italiana):
- Mese 1-2: nessun risultato SEO visibile (articoli non indicizzati stabilmente). OK se le checklist sono green.
- Mese 3-4: primi articoli in top 20-30, traffico organico +10-15%.
- Mese 6: articoli nei top 10, traffico organico +30-50%.
- Mese 12: articoli di punta generano 20-40% del traffico organico totale.

Se i KPI non migliorano dopo 4-6 mesi, la skill propone diagnosi (audit-seo-tecnico refresh) e ricalibrazione keyword (keyword-strategy refresh).

**Deliverable step 6**: DOCX `report-kpi-[mese].docx` 6-8 pagine con executive summary, tabella KPI con semaforo, 3 takeaway, piano aggiustamenti mese successivo.

## Cross-sell verso altre suite

Durante il workflow, intercettare segnali per proporre altre skill:

- Se il cliente chiede "come mai non vendo anche se arriva traffico?" → cross-sell verso **ux-copy-review** (399 EUR) e **check-competitivo-express** (StrategyBoost)
- Se i KPI finanziari del cliente sono deboli → cross-sell verso **check-salute-finanziaria** (FinanceBoost)
- Se il cliente ha negozio fisico e arriva traffico informazionale → cross-sell verso **local-seo-boost** (199 EUR)
- Se gli articoli convertono ma il cliente non ha CRM per gestire lead → cross-sell verso **crm-customer-experience** o **loyalty-crm-pmi** (MarketingBoost)

## Skill invocate

- `keyword-strategy` — mese 1 (costruzione/aggiornamento keyword map)
- `audit-seo-tecnico` — diagnosi tecnica e refresh
- `digital-marketing-performance` — trending topics, CTR benchmarks, Analytics setup
- `psicologia-marketing` — hook, storytelling, CTA
- `marketing-strategico` — contenuti commerciali, pagine servizio
- `ux-copy-review` — qualità CTA e microcopy
- `docx` — generazione brief e articoli
- `xlsx` — calendario editoriale e report KPI

## Tono e comunicazione

Consulente editoriale pratico. Il titolare PMI deve sentire:

- Che ogni articolo ha un **perché commerciale** dietro, non è content vanity
- Che i risultati SEO richiedono **pazienza misurabile** (3-6 mesi per vedere, 12 per raccogliere)
- Che il **contenuto serve il business**, non viceversa (ogni articolo ha una CTA allineata a obiettivo business)
- Che il servizio si **adatta al calendario** del cliente (stagionalità, eventi, novità), non impone un canone rigido

Evitare gergo SEO ingombrante senza spiegazione. "Dwell time" diventa "quanto tempo i visitatori restano a leggere". "Internal linking" diventa "come i tuoi articoli si rimandano l'un l'altro".

## KPI di successo del servizio

Per il cliente, dopo 6 mesi di retainer:
- Almeno 3 articoli in top 10 Google su keyword commerciali
- Traffico organico +30% vs baseline
- Almeno 5 lead/mese attribuibili ai contenuti nuovi (se configurato tracking)
- Tempo risparmiato dal cliente: 15-25 ore/mese non spese a scrivere

Per il servizio (KPI interni di qualità):
- Lead time brief → articolo pubblicato ≤ 14 giorni
- Tasso refresh che recupera posizionamento ≥ 60%
- Churn mensile ≤ 5% dopo mese 3
- NPS cliente ≥ 8/10 a 6 mesi

## Riferimenti

- `references/metodologia-piano-editoriale.md` — come costruire il piano editoriale mensile per PMI
- `references/template-brief-seo.md` — template dettagliato del brief editoriale
- `references/checklist-pubblicazione.md` — checklist on-page per ogni articolo
- `references/framework-refresh-articoli.md` — criteri e procedura refresh contenuti esistenti
- `assets/template-calendario-editoriale.md` — struttura XLSX calendario editoriale
- `assets/template-report-kpi.md` — struttura DOCX report KPI mensile
- `schemas/output-schema.json` — schema JSON output mensile

## Output ricorrente (per ogni mese)

1. **XLSX calendario editoriale** (`content-plan-[mese-anno].xlsx`): 4-8 articoli programmati con metadata completi
2. **DOCX brief per articolo** (`brief-[slug].docx`): 1 file per ogni articolo, lunghezza 2-4 pagine
3. **DOCX articoli pronti CMS** (`articolo-[slug].docx`): 4-8 articoli completi secondo piano
4. **DOCX refresh articoli esistenti** (`refresh-[slug].docx`): 2-4 articoli aggiornati
5. **Checklist pubblicazione** (`checklist-[slug].md`): 1 per ogni contenuto
6. **DOCX report KPI mensile** (`report-kpi-[mese].docx`): 6-8 pagine con metriche, semaforo, takeaway
7. **JSON strutturato** (`content-factory-[mese].json`): dati machine-readable mensili

## Pricing

- **Light**: 599 EUR/mese (4 articoli nuovi + 2 refresh + report)
- **Standard**: 899 EUR/mese (6 nuovi + 3 refresh + schema markup + internal link audit)
- **Intensive**: 1.299 EUR/mese (8 nuovi + 4 refresh + 1 pillar page/trimestre + email brief mensile)

Minimum commitment: 3 mesi. Mese 1 include setup (keyword map se mancante, benchmark baseline, configurazione Analytics/Search Console).

Upsell naturale: se il cliente a 6 mesi vuole scalare → passaggio al piano superiore con sconto 10% sul primo mese.
