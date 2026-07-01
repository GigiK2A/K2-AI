# Report Premium K2-AI — Design System & Composition Rules

> **Skill obbligatoria per ogni report PDF generato dal kbot premium.**
> Questa skill definisce il formato esatto del JSON di output e le regole di composizione visive del documento. **Devi rispettare lo schema senza deviazioni**: il renderer Python costruisce il PDF mappando ogni blocco a un partial deterministico. Se inventi tipi di blocco non documentati qui, il rendering fallisce.

---

## 1. Obiettivo del report premium

Generare un documento PDF A4 professionale (8-12 pagine), che dia all'utente un output operativo concreto:

- **Valutazioni di investimento** (es. casa vacanze, locazione, ecommerce)
- **Strategie di marketing** (posizionamento, piano canali, naming, content)
- **Analisi di processo / efficienza** (automazione, AI operativa)
- **Diagnosi finanziaria** (bilancio, controllo di gestione, budget)
- **Pareri legali e compliance** (revisione contratti, GDPR, normative)
- **Studi di fattibilità tecnica** (progettazione, edilizia, energia)
- **Audit SEO / digitali** (sito, canali, performance)

Il report deve essere **adattato al caso specifico**: non c'è una struttura fissa di sezioni, scegli i blocchi giusti per il tipo di analisi richiesta.

---

## 2. Output: JSON con `meta` + `blocks`

```json
{
  "meta": {
    "kicker": "REPORT PREMIUM",
    "title": "Titolo del report (max 70 caratteri, descrittivo del caso)",
    "subtitle_lines": ["Riga 1 contesto", "Riga 2 cliente"],
    "client_meta_lines": [
      "Nome cliente / progetto",
      "Generato il 14 maggio 2026",
      "Codice: K2AI-XXX-2026-NNNN"
    ]
  },
  "blocks": [
    { "type": "<tipo blocco>", ...campi... },
    { "type": "<tipo blocco>", ...campi... }
  ]
}
```

Tutti i tipi di `blocks` sono elencati alla §4. Devi usare **solo** quelli.

---

## 3. Principi di composizione

### 3.0 Struttura a 3 livelli di lettura (OBBLIGATORIA)

Il report NON è "piatto" (10 pagine tutte con lo stesso peso). Si organizza in **3 livelli** separati da bande `section_break`, così ogni lettore trova subito il suo strato:

- **Livello 1 — Executive** (lettura 30 secondi, per chi decide): apri con `executive_dashboard` (punteggio + subscore + top-3 criticità/opportunità + verdetto). Un `section_break` con `layer:"executive"` lo introduce.
- **Livello 2 — Analisi** (5-10 minuti, per il management): `benchmark_table`, `severity_matrix`, `data_table`, `two_column`, `financial_impact`, `recommendations`. Introdotto da `section_break` con `layer:"analysis"`.
- **Livello 3 — Appendice tecnica** (per tecnici/auditor): `source_legend` con assunzioni, fonti, formule. Introdotto da `section_break` con `layer:"appendix"`.

Chiudi il Livello 2 con un `decision_board` (la pagina che fa decidere) **prima** dell'appendice.

### 3.1 Regole

1. **Apri il Livello 1 con `executive_dashboard`** (non più `executive_summary` piatto): deve dare punteggio generale, 5 subscore standard, top-3 criticità, top-3 opportunità, verdetto secco. `executive_summary` resta valido solo per report brevi/qualitativi.
2. **Meno testo, più densità**: max 30-40% testo, 60-70% blocchi visual/dato (card, score, matrici, tabelle). Mai 3 paragrafi di fila: spezza con una tabella o una matrice.
3. **Scoring universale**: ogni report genera un punteggio 0-100 + subscore standardizzati (es. Salute finanziaria, Efficienza operativa, Potenziale di crescita, Esposizione al rischio, Prontezza AI). Adatta le etichette al dominio ma mantieni 4-6 subscore.
4. **Severity su ogni criticità**: usa `severity_matrix` (Critical/High/Medium/Low + Effort + ROI). Trasforma l'analisi in supporto alle decisioni.
5. **Distingui fatti da inferenze**: usa i tag affidabilità (`verified`/`inference`/`benchmark`/`assumption`) su KPI e nella `source_legend`. Non spacciare stime per dati certi.
6. **Impatto economico obbligatorio** dove ha senso: `financial_impact` con costo dell'inazione vs upside potenziale (risparmio + ricavi addizionali).
7. **Benchmark esterni**: confronta sempre il cliente col mercato via `benchmark_table` (Azienda vs Settore vs Delta).
8. **Recommendation engine**: `recommendations` con orizzonti temporali (0-30 giorni / 1-3 mesi / 3-12 mesi). Rispondi a "cosa devo fare domani?".
9. **Decision Board finale**: `decision_board` con stato, urgenza, investimento, ROI atteso, decisione consigliata.
10. **Tra 8 e 12 blocchi totali** (incluse le 3 bande `section_break`). Ogni numero quantificato e plausibile — mai "X", "TBD", placeholder.
11. **Tono**: pragmatico, da pari a pari, italiano corretto (è, à, ù, ò, ì). Mai marketing, mai "rivoluzionario", "all'avanguardia", "ecosistema".
12. **Coerenza interna**: se scrivi €31.500 ricavi in un blocco, lo stesso numero appare identico altrove (KPI, dashboard, conclusioni).
13. **Adatta i titoli al dominio** e attiva i **moduli verticali** della §9 (SWOT/Porter per strategy, DSCR/break-even per financial, compliance gaps per legal, funnel/CAC/LTV per marketing).

---

## 4. Tipi di blocchi disponibili

Tutti i campi `optional` possono essere omessi. **Non aggiungere campi non documentati**.

### 4.1 `executive_summary`
Card riassuntiva iniziale con narrativa + opzionale gauge + opzionale badges.

```json
{
  "type": "executive_summary",
  "title": "Executive Summary",
  "body_html": "<p>L'investimento in 2 appartamenti per casa vacanza presenta <strong>ottime potenzialità</strong>...</p><p><strong>Potenziale di ricavo stimato:</strong> €28.000-35.000 annui...</p>",
  "gauge": {                              // optional
    "value": 75,
    "max": 100,
    "label": "/ 100"
  },
  "badges": [                             // optional, max 4
    {"variant": "ok", "label": "Investimento Consigliato"},
    {"variant": "warning", "label": "Richiede Piano Marketing"}
  ]
}
```

`body_html` è HTML semplice: `<p>`, `<strong>`, `<em>`, `<br>`. No tag pericolosi, no inline CSS.

`variant` accetta: `ok` (verde), `warning` (giallo), `alert` (rosso), `info` (blu).

### 4.2 `kpi_grid`
Griglia di carte metriche. 2-6 elementi. Renderer mette in 2 colonne se ≤4, 3 colonne se ≥5.

```json
{
  "type": "kpi_grid",
  "title": "KPI di Investimento",
  "items": [
    {
      "label": "REVPAR STIMATO",
      "value": "€52",
      "subtitle": "Mediana Centro case vacanza: €48 (benchmark mercato)",
      "note": "Superiore alla media di zona grazie alle dotazioni premium",
      "verified": true,
      "variant": "ok"
    },
    {
      "label": "TRAFFICO ORGANICO 12M",
      "value": "180–250 vis/mese",
      "note": "† proiezione su CTR 2.5% — richiede GSC/Analytics per baseline",
      "verified": false,
      "variant": "warning"
    }
  ]
}
```

**Regole obbligatorie kpi_grid items:**
- `value`: SOLO numero/range secco, max 20 caratteri. **Mai** disclaimer inline tipo `"€52 [stima]"`.
- `note`: disclaimer o contesto, max 80 caratteri. Per dati non verificati, prefissa con `†`.
- `verified`: boolean. `true` se il dato proviene da fonte misurata in sessione (Analytics, GSC, crawl reale, file caricato). `false` se è stima/proiezione/benchmark.
- Il renderer aggiunge automaticamente il marker dagger `†` davanti al value quando `verified:false` e renderizza la `note` in corsivo arancione.
- `variant` colora il bordo superiore: `ok`, `warning`, `alert`, `neutral` (default).

### 4.3 `two_column`
Sezione con due colonne. Tipico: narrativa + lista qualificata, oppure tabella + insight.

```json
{
  "type": "two_column",
  "title": "Analisi di Mercato — Umbria Centro",
  "left": {
    "heading": "Posizionamento Competitivo",
    "body_html": "<p>San Giovanni Profiamma beneficia di una posizione...</p>",
    "table": {                            // optional
      "columns": ["Tipologia Struttura", "ADR Medio", "Occupancy"],
      "rows": [
        ["Casa vacanza standard", "€87", "55%"],
        ["Casa vacanza premium", "€105-120", "48-52%"],
        ["Agriturismo zona", "€128", "58%"]
      ]
    }
  },
  "right": {
    "heading": "Fattori di Successo",
    "badges": [                           // optional, alternative to body
      {"variant": "ok", "label": "Forte", "description": "Dotazioni uniche (serra biochimica)"},
      {"variant": "ok", "label": "Forte", "description": "Posizione Via di Francesco"},
      {"variant": "warning", "label": "Medio", "description": "Notorietà brand (da costruire)"}
    ],
    "callout": {                          // optional
      "tone": "info",
      "label": "Insight strategico",
      "body": "Il mercato premia strutture che combinano autenticità e comfort moderni."
    }
  }
}
```

### 4.4 `data_table`
Tabella full-width con intro opzionale e callout opzionale sotto.

```json
{
  "type": "data_table",
  "title": "Proiezioni Finanziarie Triennali",
  "intro": "Scenario conservativo basato su crescita graduale...",
  "columns": ["Anno", "Occupancy", "ADR Medio", "RevPAR", "Ricavi Lordi", "Costi Operativi", "EBITDA"],
  "rows": [
    ["Anno 1", "42%", "€95", "€40", "€26.200", "€11.800", "€14.400"],
    ["Anno 2", "50%", "€105", "€52", "€31.500", "€13.200", "€18.300"],
    ["Anno 3", "55%", "€115", "€63", "€38.100", "€14.800", "€23.300"]
  ],
  "callout": {                            // optional
    "tone": "warning",
    "label": "Assunzioni chiave",
    "body": "2 appartamenti × 4 posti letto × 300 giorni apertura annui. Costi operativi includono pulizie..."
  }
}
```

Tone callout: `info` (azzurro), `warning` (sabbia), `ok` (verde), `alert` (rosso).

### 4.5 `narrative_split`
Sezione con narrativa principale (col sinistra) e sidebar di approfondimento (col destra). Usato per "Strategia di Posizionamento e Naming" o simili.

```json
{
  "type": "narrative_split",
  "title": "Strategia di Posizionamento e Naming",
  "left": {
    "heading": "Concept e Target",
    "body_html": "<p><strong>Posizionamento:</strong> \"Dimora storica umbra con wellness esperienziale\". Target primario: coppie 35-55 anni...</p>",
    "card": {                             // optional inset card
      "heading": "Naming Proposto",
      "body_html": "<p><strong>Appartamento 1:</strong> \"Dimora del Pellegrino\" (più tranquillo)</p><p><strong>Appartamento 2:</strong> \"Casa del Priore\" (con veranda, più esclusivo)</p>"
    },
    "footnote": "I nomi richiamano la tradizione religiosa del territorio..."
  },
  "right": {
    "heading": "Piano Marketing Essenziale",
    "body_html": "<h4>Canali Prioritari (Anno 1)</h4><ul><li><strong>Booking.com:</strong> 60% prenotazioni</li><li><strong>Airbnb:</strong> 25% prenotazioni</li></ul><h4>Investimenti Anno 1</h4><ul><li>Fotografia professionale: €1.200</li><li>Sito web: €2.800</li></ul><p><strong>Totale: €8.200</strong></p>"
  }
}
```

### 4.6 `action_list`
Lista numerata di azioni prioritarie con impatto stimato sul margine destro.

```json
{
  "type": "action_list",
  "title": "Piano di Azione Prioritario",
  "intro": "Roadmap operativa per massimizzare il ROI nei primi 12 mesi.",
  "items": [
    {"index": 1, "title": "Setup Operativo e Compliance", "meta": "Impatto: €0 (prerequisito)"},
    {"index": 2, "title": "Allestimento e Fotografia Professionale", "meta": "Impatto: +25% ADR"},
    {"index": 3, "title": "Lancio Digitale e Prime Prenotazioni", "meta": "Impatto: €26.200/anno"}
  ]
}
```

L'`index` è facoltativo (il renderer assegna numerazione progressiva se omesso).

### 4.7 `risk_mitigation`
Due colonne: rischi (sinistra, con severity badge) e strategie di mitigazione (destra, narrative cards).

```json
{
  "type": "risk_mitigation",
  "title": "Analisi Rischi e Mitigazioni",
  "risks": [
    {"severity": "alta", "title": "Stagionalità estrema", "body": "Occupancy sotto 20% nei mesi invernali"},
    {"severity": "media", "title": "Concorrenza crescente", "body": "Nuove strutture in zona Foligno-Assisi"},
    {"severity": "media", "title": "Dipendenza OTA", "body": "85% prenotazioni via Booking/Airbnb"}
  ],
  "mitigations": [
    {"title": "Contro stagionalità", "body": "Pacchetti wellness invernali, tariffe corporate per trasferte lavoro, partnership con terme di Foligno"},
    {"title": "Differenziazione", "body": "Focus su wellness esperienziale unico, certificazione bio, storytelling Via di Francesco"},
    {"title": "Canale diretto", "body": "Obiettivo 30% prenotazioni dirette entro Anno 2, newsletter, programma fedeltà"}
  ]
}
```

`severity` accetta: `alta`, `media`, `bassa`.

### 4.8 `conclusions`
Blocco finale con narrativa principale (col sx) + serie di milestone con KPI (col dx). Sempre l'ultimo blocco prima del footer.

```json
{
  "type": "conclusions",
  "title": "Conclusioni e Raccomandazioni",
  "left": {
    "heading": "Investimento Consigliato",
    "heading_variant": "ok",
    "body_html": "<p>L'investimento presenta <strong>solide basi economiche</strong>...</p><h4>Fattori critici di successo:</h4><ul><li>Investimento iniziale in fotografia (€8.200 Anno 1)</li><li>Focus su esperienza ospite</li></ul>",
    "callout": {
      "tone": "warning",
      "label": "Raccomandazione operativa",
      "body": "Procedere con l'investimento pianificando un budget marketing di €8.200 per il primo anno e un fondo di riserva di €5.000 per imprevisti."
    }
  },
  "right": {
    "heading": "KPI di Controllo",
    "milestones": [
      {
        "label": "Mese 6",
        "tone": "neutral",
        "items": ["Occupancy ≥ 35%", "ADR ≥ €90", "Rating ≥ 8.5", "15+ recensioni"]
      },
      {
        "label": "Anno 1",
        "tone": "neutral",
        "items": ["Ricavi ≥ €26.000", "Occupancy ≥ 42%", "ADR ≥ €95", "Rating ≥ 9.0"]
      },
      {
        "label": "Anno 2 Target",
        "tone": "ok",
        "items": ["Ricavi ≥ €31.500", "Occupancy ≥ 50%", "ADR ≥ €105", "30% prenotazioni dirette"]
      }
    ]
  }
}
```

### 4.9 `narrative`
Blocco testuale full-width, solo se necessario per contestualizzazioni lunghe. Usalo sparingly.

```json
{
  "type": "narrative",
  "title": "Contesto del Mercato",
  "intro": "1 frase di apertura opzionale",
  "body_html": "<p>...</p><h4>Sotto-sezione</h4><ul><li>punto</li></ul>"
}
```

### 4.10 `section_break` — banda di livello
Divide il report nei 3 livelli di lettura. Breve per definizione.

```json
{
  "type": "section_break",
  "layer": "executive",
  "title": "Livello 1 — Executive",
  "subtitle": "lettura 30 secondi · per chi decide"
}
```

`layer` accetta: `executive` (accento teal), `analysis` (grigio), `appendix` (grigio muto).

### 4.11 `executive_dashboard` — cruscotto direzionale (Livello 1)
Il blocco di apertura. Punteggio + subscore + top-3 + verdetto in una schermata.

```json
{
  "type": "executive_dashboard",
  "title": "Cruscotto direzionale",
  "gauge": { "value": 74, "max": 100 },
  "status": { "label": "Da ottimizzare", "variant": "warning" },
  "priority": { "label": "Alta", "variant": "alert" },
  "subscores": [
    { "label": "Salute finanziaria", "value": 62, "trend": "down" },
    { "label": "Efficienza operativa", "value": 78, "trend": "flat" },
    { "label": "Potenziale di crescita", "value": 65, "trend": "up" },
    { "label": "Esposizione al rischio", "value": 58, "trend": "down" },
    { "label": "Prontezza AI", "value": 41, "trend": "down" }
  ],
  "problems": ["Margine operativo sotto media (-6 pt)", "Processi manuali", "CRM assente"],
  "opportunities": ["Automazione preventivi", "Ottimizzazione pricing", "Cross-selling"],
  "verdict": { "text": "Business solido ma sotto-ottimizzato: con 85k€ il margine recupera 6 punti in 14 mesi.", "decision": "Procedere", "variant": "ok" }
}
```

`trend` accetta: `up` (triangolo verde), `flat` (trattino grigio), `down` (triangolo rosso). `variant` (status/priority/verdict): `ok`/`warning`/`alert`/`info`/`neutral`. 4-6 subscore, max 4 problems, max 4 opportunities.

### 4.12 `benchmark_table` — confronto col settore
KPI | Azienda | Settore | Delta. Il delta è colorato dal campo `tone`.

```json
{
  "type": "benchmark_table",
  "title": "Benchmark vs settore",
  "intro": "Ingegneria / servizi professionali, campione Italia PMI 5-50 dipendenti.",
  "columns": ["KPI", "Azienda", "Settore", "Delta"],
  "rows": [
    { "kpi": "Margine EBITDA", "company": "12%", "sector": "18%", "delta": "-6 pt", "tone": "alert" },
    { "kpi": "Costo acquisizione", "company": "€300", "sector": "€210", "delta": "+€90", "tone": "alert" },
    { "kpi": "Tasso rinnovo commesse", "company": "71%", "sector": "64%", "delta": "+7 pt", "tone": "ok" }
  ],
  "note": "Fonte benchmark: Mediobanca PMI 2024."
}
```

`tone` del delta: `ok` (verde, favorevole), `alert` (rosso, sfavorevole), `neutral` (grigio). Scegli in base alla direzione favorevole del KPI, non al segno.

### 4.13 `severity_matrix` — matrice priorità
Ogni criticità con severity + effort + ROI. Trasforma l'analisi in decisione.

```json
{
  "type": "severity_matrix",
  "title": "Matrice priorità",
  "items": [
    { "problem": "Costi operativi alti", "severity": "Critical", "effort": "Medio", "roi": "Alto" },
    { "problem": "CRM assente", "severity": "High", "effort": "Basso", "roi": "Alto" },
    { "problem": "Branding datato", "severity": "Low", "effort": "Medio", "roi": "Medio" }
  ]
}
```

`severity` accetta: `Critical` (rosso), `High` (arancione), `Medium` (ambra), `Low` (grigio). `roi`: `Alto`/`Medio`/`Basso`.

### 4.14 `financial_impact` — impatto economico
Due pannelli: costo dell'inazione vs upside potenziale.

```json
{
  "type": "financial_impact",
  "title": "Impatto economico",
  "inaction": { "label": "Se non agisci", "value": "-120k€/anno", "note": "margine eroso + ore perse su lavoro manuale" },
  "action": { "label": "Se agisci", "value": "+280k€", "note": "80k€ risparmio operativo + 200k€ ricavi addizionali" }
}
```

### 4.15 `recommendations` — azioni per orizzonte temporale
Risponde a "cosa devo fare domani?". Raggruppa per tempo.

```json
{
  "type": "recommendations",
  "title": "Azioni raccomandate",
  "horizons": [
    { "label": "0-30 giorni", "tone": "alert", "items": ["Attivare agente AI su preventivi", "Installare CRM base"] },
    { "label": "1-3 mesi", "tone": "warning", "items": ["Automazione documentale su commesse ripetitive", "Revisione pricing"] },
    { "label": "3-12 mesi", "tone": "ok", "items": ["Cross-selling manutenzione", "Dashboard controllo di gestione"] }
  ]
}
```

`tone`: `alert` (immediato, rosso), `warning` (breve termine, ambra), `ok` (strategico, verde).

### 4.16 `decision_board` — pagina decisionale (chiude il Livello 2)
La board vuole questo: stato, urgenza, investimento, ROI, decisione.

```json
{
  "type": "decision_board",
  "title": "Decision Board",
  "cells": [
    { "label": "Stato attuale", "value": "Da ottimizzare", "variant": "warning" },
    { "label": "Urgenza", "value": "Alta", "variant": "alert" },
    { "label": "Investimento richiesto", "value": "85k€" },
    { "label": "ROI atteso", "value": "14 mesi" },
    { "label": "Decisione consigliata", "value": "Procedere", "variant": "ok" }
  ]
}
```

3-6 celle. `variant` colora il valore e (per ok/alert) lo sfondo cella.

### 4.17 `source_legend` — affidabilità dati (Livello 3)
Appendice tecnica: separa fatti certi da inferenze/benchmark/assunzioni.

```json
{
  "type": "source_legend",
  "title": "Affidabilità dei dati",
  "items": [
    { "tag": "verified", "text": "Fatturato 2.4M€", "note": "da bilancio depositato 2024" },
    { "tag": "inference", "text": "EBITDA stimato 12%", "note": "proiezione su costi dichiarati" },
    { "tag": "benchmark", "text": "Margine settore 18%", "note": "Mediobanca PMI 2024" },
    { "tag": "assumption", "text": "Upside ricavi 200k€", "note": "assunzione conversione 15% base clienti" }
  ]
}
```

`tag`: `verified` (verde, dato misurato), `inference` (ambra, deduzione AI), `benchmark` (blu, confronto mercato), `assumption` (rosso, ipotesi).

---

## 5. Schema completo riassuntivo

| Blocco | Livello | Quando usarlo |
|---|---|---|
| `section_break` | tutti | Divide i 3 livelli di lettura (3 per report) |
| `executive_dashboard` | 1 | Apertura: score + subscore + top-3 + verdetto |
| `executive_summary` | 1 | Alternativa breve per report qualitativi |
| `kpi_grid` | 2 | 2-6 metriche numeriche chiave |
| `benchmark_table` | 2 | Confronto Azienda vs Settore vs Delta |
| `severity_matrix` | 2 | Criticità con severity/effort/ROI |
| `two_column` | 2 | Analisi laterali: dato + qualifier |
| `narrative_split` | 2 | Strategia / posizionamento con sidebar |
| `data_table` | 2 | Proiezioni, scenari, comparativi numerici |
| `financial_impact` | 2 | Costo inazione vs upside |
| `recommendations` | 2 | Azioni per orizzonte temporale |
| `risk_mitigation` | 2 | Rischi vs mitigazioni (paired) |
| `narrative` | 2 | Contesto narrativo lungo (parsimonia) |
| `decision_board` | 2 | Pagina finale decisionale |
| `source_legend` | 3 | Appendice: fatti vs inferenze, fonti |
| `conclusions` | — | Chiusura alternativa a decision_board |

---

## 9. Moduli verticali per tipo di report

Core comune (i blocchi sopra) + moduli specifici. Attiva quelli pertinenti al dominio, mappandoli sui blocchi disponibili:

- **Strategy**: SWOT (`two_column` forze/debolezze + opportunità/minacce), Porter (`data_table` 5 forze), scenario planning (`data_table` scenari).
- **Financial**: cash flow (`data_table`), ratios/indici (`kpi_grid`), DSCR + break-even (`kpi_grid` o `data_table`).
- **Legal**: compliance gaps (`severity_matrix`), rischi regolatori (`risk_mitigation`), norme citate (`data_table`).
- **Marketing**: funnel (`data_table`), CAC/ROAS/LTV (`kpi_grid` + `benchmark_table`), piano canali (`recommendations`).

I moduli NON cambiano lo scheletro a 3 livelli: si inseriscono nel Livello 2.

---

## 6. Regole per `body_html`

Tag ammessi: `<p>`, `<strong>`, `<em>`, `<br>`, `<ul>`, `<ol>`, `<li>`, `<h4>`, `<h5>`.
Vietati: `<style>`, `<script>`, `<img>`, `<details>`, `<summary>`, accordion/collapse classes,
attributi `style=`, `class=`, `id=`, `aria-expanded`, `hidden`. **Nessun elemento collassabile,
toggleable o nascosto**: il documento è un PDF, ogni sezione deve essere sempre visibile.
Caratteri italiani: `è`, `à`, `ì`, `ò`, `ù`, `é` — sempre con accento corretto.
Numeri: `€31.500` (italiano), non `€31,500` (anglosassone). Percentuali con `%`. Range con trattino corto: `48-52%`.

---

## 7. Esempio di buona composizione (caso: report investimento ricettivo)

```
blocks: [
  section_break (layer="executive", "Livello 1 — Executive"),
  executive_dashboard (gauge 74/100, 5 subscore, top-3 criticità/opportunità, verdetto),
  section_break (layer="analysis", "Livello 2 — Analisi"),
  benchmark_table ("Benchmark vs settore", 4 righe Azienda/Settore/Delta),
  severity_matrix ("Matrice priorità", 4 criticità con severity/effort/ROI),
  data_table ("Proiezioni Finanziarie Triennali", 3 righe, callout assunzioni),
  financial_impact (costo inazione vs upside),
  recommendations (3 orizzonti: 0-30gg / 1-3m / 3-12m),
  decision_board ("Decision Board", 5 celle),
  section_break (layer="appendix", "Livello 3 — Appendice tecnica"),
  source_legend ("Affidabilità dei dati", 4 item con tag)
]
```

11 blocchi totali (3 bande + 8 contenuto), ~10 pagine A4. Documento che fa decidere, non che spiega.

---

## 8. Output finale

**Restituisci SOLO il JSON**, senza:
- testo prima o dopo l'oggetto JSON
- code fence ```` ```json ```` o ```` ``` ````
- commenti
- markdown

Il primo carattere della tua risposta deve essere `{`, l'ultimo `}`. Niente altro.
