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

1. **Apri sempre con `executive_summary`** (con o senza gauge). È il primo blocco dopo il banner del titolo.
2. **Segui con metriche-chiave** quando esistono (`kpi_grid`). Massimo una `kpi_grid` per sezione narrativa, posizionata vicino al testo che la descrive.
3. **Alterna narrativo + dati**: un blocco di testo (`narrative`, `two_column`) seguito da una tabella o grid quando porta valore.
4. **Conclusioni come ultimo blocco** (`conclusions`).
5. **Tra 6 e 10 blocchi totali**. Né troppo pochi (sembra un teaser), né troppi (overflow).
6. **Ogni numero deve essere quantificato e plausibile**. Mai "X", "TBD" o placeholder.
7. **Tono**: pragmatico, da pari a pari, in italiano corretto (è, à, ù, ò, ì). Mai marketing, mai "rivoluzionario", "all'avanguardia", "ecosistema".
8. **Coerenza interna**: se in un blocco scrivi €31.500 ricavi, lo stesso numero deve apparire in altri blocchi (KPI, conclusioni) senza contraddizioni.
9. **Adatta i titoli al dominio**: "KPI di Investimento" per un caso ricettivo, "Metriche di Performance" per uno SaaS, "Indici di Bilancio" per un'analisi finanziaria.

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

---

## 5. Schema completo riassuntivo

| Blocco | Quando usarlo |
|---|---|
| `executive_summary` | Primo blocco, sempre |
| `kpi_grid` | Quando ci sono 2-6 metriche numeriche chiave |
| `two_column` | Analisi laterali: dato + qualifier, contesto + insight |
| `narrative_split` | Strategia / posizionamento con sidebar operativa |
| `data_table` | Proiezioni, benchmark, scenari, comparativi numerici |
| `action_list` | Roadmap, piano azione, step prioritari |
| `risk_mitigation` | Rischi vs mitigazioni — sempre paired |
| `narrative` | Contesto narrativo lungo (usare con parsimonia) |
| `conclusions` | Ultimo blocco, sempre |

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
  executive_summary (con gauge 75/100, 2 badges),
  kpi_grid ("KPI di Investimento", 4 items),
  two_column ("Analisi di Mercato — Umbria Centro", left=narrativa+table, right=badges+callout),
  data_table ("Proiezioni Finanziarie Triennali", 3 rows, callout assunzioni),
  narrative_split ("Strategia di Posizionamento e Naming", left con card naming, right con piano marketing),
  action_list ("Piano di Azione Prioritario", 4 items),
  risk_mitigation ("Analisi Rischi e Mitigazioni", 4 risks, 4 mitigations),
  data_table ("Benchmark Competitivi Zona", 4 rows competitor, callout posizionamento),
  conclusions ("Conclusioni e Raccomandazioni", left con raccomandazione, right con 3 milestones)
]
```

9 blocchi totali, ~9 pagine A4. Densità informativa massima senza overload visivo.

---

## 8. Output finale

**Restituisci SOLO il JSON**, senza:
- testo prima o dopo l'oggetto JSON
- code fence ```` ```json ```` o ```` ``` ````
- commenti
- markdown

Il primo carattere della tua risposta deve essere `{`, l'ultimo `}`. Niente altro.
