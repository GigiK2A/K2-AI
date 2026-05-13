# Template Pagella Ricettiva HTML — check-host-express

HTML single-page self-contained. File `check-host-{slug_struttura}-{YYYYMMDD}.html`. Zero dipendenze esterne, apribile offline.

## Scopo

Il titolare apre il file, in 5 minuti capisce dove si trova rispetto al mercato, cosa gli sta costando di più e i 3 passi concreti da fare subito. Stampabile, shareabile.

---

## Design Language

Stile consulenza premium, non SaaS generico. Ispirato a report McKinsey / BCG adattato per PMI ricettive.

### Palette
```css
:root {
  --primary: #0F2544;
  --primary-light: #1A3A6B;
  --accent: #E8A020;
  --accent-soft: #FDF3E3;
  --green: #1A7A4A;
  --green-bg: #E8F5EE;
  --green-border: #A8D5BC;
  --yellow: #C07A00;
  --yellow-bg: #FFF8E8;
  --yellow-border: #F0C060;
  --red: #B02020;
  --red-bg: #FDF0F0;
  --red-border: #F0A0A0;
  --bg: #F5F6F8;
  --surface: #FFFFFF;
  --text: #1A1A2E;
  --text-secondary: #4A5568;
  --text-muted: #8090A8;
  --border: #E2E8F0;
  --shadow: 0 2px 12px rgba(15,37,68,0.08);
  --shadow-lg: 0 8px 32px rgba(15,37,68,0.12);
}
```

### Tipografia
- Font system stack: `-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif`
- Header struttura: 28px bold `--primary`
- Score centrale: 72px bold `--primary`
- KPI value: 36px bold
- Label uppercase: 11px, letter-spacing 1px, `--text-muted`
- Body: 15px, line-height 1.6

---

## Struttura Completa

### 0. Barra top (8px)
Gradiente orizzontale `--primary` → `--accent`. Solo decorativa, segnala house style K2-AI.

### 1. Header (padding 24px 32px)
Layout tre colonne:
- Sinistra: "K2-AI" in bold `--primary` + label "Report Ricettivo"
- Centro: nome struttura (22px bold) + tipologia + comune/regione
- Destra: data generazione + codice report (es. CHX-20260512-001)

Sottobarra: thin line `--border` + breadcrumb "K2-AI > Check Ricettivo > {nome}"

### 2. Executive Summary Card (full width, sfondo `--primary`, testo bianco)
Una singola card prominente con:
- Sinistra: Score globale 0-100 con gauge SVG (diametro 160px), giudizio testuale sotto ("Eccellente" / "Buono" / "Sufficiente" / "Preoccupante" / "Critico")
- Centro: 3 bullet punti del tipo "✓ Il tuo punto di forza: canali diretti al 42%" / "⚠ Attenzione: RevPAR del 28% sotto la mediana zona" / "→ Azione prioritaria: ribilanciare ADR nei weekend"
- Destra: Posizionamento percentile → cerchio con "Meglio del **X%** delle strutture simili nella tua area"

Gauge SVG: arco semicircolare 180°, colore da rosso (0) a verde (100), puntatore animato, valore al centro.

### 3. Sezione "Dove ti trovi" — 6 KPI Semaforo (grid 3×2)

**KPI obbligatori:** RevPAR, ADR, Occupancy rate, Dipendenza OTA, Rating medio, ALOS (soggiorno medio)

Ogni card KPI:
```
┌─────────────────────────────────┐
│ [●] VERDE/GIALLO/ROSSO  [nome KPI]
│                                 │
│   €42          Zona: €58        │
│   (il tuo)     (mediana)        │
│                                 │
│ ████████░░░░░░ 72%              │
│ tu↑      mediana                │
│                                 │
│ "Sotto del 28% rispetto         │
│  alla tua zona. Possibile       │
│  recupero: +€3.200/anno."       │
└─────────────────────────────────┘
```

Elementi card:
- Badge semaforo colorato top-left (cerchio 12px) + nome KPI top-right
- Valore struttura (36px bold) affiancato a "Zona: X" (18px, `--text-muted`)
- Barra progress con marker "tu" e marker "mediana zona" (barra bicolore)
- Riga impatto economico stimato: quanti euro stai lasciando sul tavolo (o guadagnando in più)
- 1 riga commento sintetico in italiano naturale

Hover effect: box-shadow più pronunciata, cursore pointer → tooltip con spiegazione metodologia calcolo.

### 4. Sezione "Il tuo anno a colpo d'occhio" — Stagionalità stimata

Se disponibili dati mensili: grafico combo Chart.js (barre Occupancy + linea ADR, 12 mesi).
Se non disponibili dati mensili: skip questa sezione.

Sopra il grafico: 3 micro-card con "Mese migliore", "Mese peggiore", "Stagionalità: alta/media/bassa varianza".

### 5. Sezione "Confronto zona dettagliato" — Benchmark Table

Tabella comparativa a 4 colonne:

| Metrica | La tua struttura | Mediana zona | Top 25% zona | Tuo posizionamento |
|---|---|---|---|---|
| RevPAR | €42 | €58 | €78 | 🔴 Sotto mediana |
| ADR | €115 | €128 | €165 | 🟡 In range |
| Occupancy | 55% | 58% | 72% | 🟡 In range |
| Quota diretta | 38% | 42% | 60% | 🟡 Migliorabile |
| Rating medio | 8.4 | 8.1 | 9.0 | 🟢 Sopra mediana |
| ALOS | 2.1 gg | 2.4 gg | 3.2 gg | 🔴 Sotto mediana |

Sotto la tabella: nota metodologica 2 righe su fonte benchmark (es. "Benchmark basati su dati di mercato 2024-2025 per strutture simili nella tua area geografica").

### 6. Sezione "Cosa ti sta costando" — Gap Analysis

3 card orizzontali, ognuna calcola il gap economico annuo:

**Card 1 — Gap RevPAR:**
- "Se raggiungessi la mediana zona (+€16 RevPAR)"
- Calcolo: delta × camere × giorni apertura = €X/anno
- "Se raggiungessi il top 25% (+€36 RevPAR)" = €Y/anno
- Barra orizzontale: tua posizione → mediana → top 25%

**Card 2 — Gap Occupancy:**
- Stesso schema con punti percentuali e ricavi aggiuntivi stimati

**Card 3 — Gap Canali Diretti:**
- "Ogni 10% in più di vendite dirette = risparmio commissioni OTA stimato €Z/anno"

Intestazione sezione: "**€X.XXX/anno** è il potenziale non ancora sfruttato" (numero grande, colore `--accent`)

### 7. Sezione "I 3 passi prioritari" — Piano d'azione

3 card accordion (`<details>`/`<summary>`), ordinate per impatto/difficoltà:

Header card:
```
[1]  RIBILANCIA I PREZZI NEL WEEKEND          Impatto: Alto  ●●●○○  Difficoltà: Bassa
     "ADR weekend €105 vs €142 compset. Gap chiudibile in 30 giorni."
```

Body espanso (click):
- **Situazione attuale:** 2-3 righe con i numeri specifici della struttura
- **Perché conta:** impatto economico stimato (es. "+€1.800/anno se porti l'ADR weekend a €125")
- **Come fare - 3 step concreti:**
  1. Step operativo specifico (es. "Vai su Extranet Booking → Gestione prezzi → Imposta +18% ven-sab")
  2. Step operativo
  3. Step operativo
- **Tempo necessario:** 30 min / 1 settimana / 1 mese
- **Come misurare:** KPI da monitorare e soglia di successo

### 8. Sezione "I tuoi punti di forza" (non tralasciare)

2-3 card compatte con evidenza di cosa sta funzionando bene. Tono rinforzante, non solo critico. Es: "Il tuo rating 8.4 è sopra la mediana zona: è un asset da sfruttare nel marketing."

### 9. CTA HostBoost

Banner full-width, sfondo `--accent-soft`, bordo sinistro 4px `--accent`:

```
Questo check ti ha mostrato il quadro.
HostBoost costruisce il piano.

HostBoost analizza 12 mesi di dati, costruisce il tuo cruscotto KPI permanente,
disegna il calendario di pricing stagione per stagione e ti consegna
5 azioni prioritarie con ROI atteso e istruzioni operative passo per passo.

[ Prenota una call con K2-AI ]        da 899 EUR una tantum
```

Bottone: sfondo `--primary`, testo bianco, border-radius 6px, padding 12px 28px.

### 10. Footer

2 righe:
- "Check rapido generato il {data}. I benchmark sono stime su dati pubblici di mercato — non costituiscono consulenza professionale certificata."
- "Powered by **K2-AI** — k2-ai.it | Per supporto: info@k2-ai.it"

---

## CSS Avanzato

```css
/* Cards con ombra sottile e hover */
.kpi-card {
  background: var(--surface);
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--shadow);
  border-top: 3px solid transparent;
  transition: box-shadow 0.2s, transform 0.2s;
}
.kpi-card:hover { box-shadow: var(--shadow-lg); transform: translateY(-2px); }
.kpi-card.green { border-top-color: var(--green); }
.kpi-card.yellow { border-top-color: var(--yellow); }
.kpi-card.red { border-top-color: var(--red); }

/* Mini progress bar */
.mini-bar-track {
  height: 6px; background: var(--border); border-radius: 3px; position: relative; margin: 8px 0;
}
.mini-bar-fill { height: 100%; border-radius: 3px; }
.mini-bar-marker {
  position: absolute; top: -3px; width: 12px; height: 12px;
  border-radius: 50%; background: var(--primary); transform: translateX(-50%);
}

/* Accordion priorities */
details { border: 1px solid var(--border); border-radius: 10px; margin-bottom: 8px; overflow: hidden; }
details[open] { box-shadow: var(--shadow); }
summary {
  padding: 16px 20px; cursor: pointer; display: flex; align-items: center; gap: 12px;
  background: var(--surface); list-style: none; user-select: none;
}
summary:hover { background: #F8FAFC; }
.priority-badge {
  width: 28px; height: 28px; border-radius: 50%; background: var(--primary);
  color: white; font-size: 13px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.details-body { padding: 0 20px 20px; border-top: 1px solid var(--border); }

/* Executive summary dark card */
.exec-summary {
  background: var(--primary);
  color: white;
  border-radius: 16px;
  padding: 32px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 32px;
  align-items: center;
  margin-bottom: 32px;
}

/* Benchmark table */
.benchmark-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.benchmark-table th {
  background: var(--primary); color: white; padding: 10px 14px;
  text-align: left; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;
}
.benchmark-table td { padding: 10px 14px; border-bottom: 1px solid var(--border); }
.benchmark-table tr:nth-child(even) td { background: #FAFBFC; }
.benchmark-table tr:hover td { background: var(--accent-soft); }

/* Gap analysis */
.gap-card {
  background: var(--surface); border-radius: 12px; padding: 24px;
  border-left: 4px solid var(--accent); box-shadow: var(--shadow);
}
.gap-amount { font-size: 28px; font-weight: 700; color: var(--accent); }

/* Responsive */
@media (max-width: 900px) {
  .exec-summary { grid-template-columns: 1fr; text-align: center; }
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .benchmark-table { font-size: 13px; }
}
@media (max-width: 600px) {
  .kpi-grid { grid-template-columns: 1fr; }
  .gap-grid { grid-template-columns: 1fr; }
}
@media print {
  details { display: block; }
  details summary::after { display: none; }
  .exec-summary { background: var(--primary) !important; -webkit-print-color-adjust: exact; }
  .cta-section { display: none; }
  body { font-size: 13px; }
}
```

---

## Gauge SVG (score centrale)

```html
<svg viewBox="0 0 200 120" width="180" height="108" role="img" aria-label="Score {score} su 100">
  <defs>
    <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#B02020"/>
      <stop offset="45%" stop-color="#C07A00"/>
      <stop offset="100%" stop-color="#1A7A4A"/>
    </linearGradient>
  </defs>
  <!-- Track -->
  <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#E2E8F0" stroke-width="16" stroke-linecap="round"/>
  <!-- Fill (dasharray calcolato: 251.2 = semicircumference, score/100 × 251.2) -->
  <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="url(#gaugeGrad)" stroke-width="16"
        stroke-linecap="round" stroke-dasharray="{score_dash} 251.2"/>
  <!-- Valore -->
  <text x="100" y="85" text-anchor="middle" font-size="42" font-weight="700" fill="#0F2544">{score}</text>
  <text x="100" y="105" text-anchor="middle" font-size="13" fill="#8090A8">/ 100</text>
</svg>
```

---

## Accorgimenti Comunicativi

- **Impatto in euro sempre**: non solo percentuali, tradurre tutto in €/anno — il titolare ragiona in cassa
- **Confronto sempre doppio**: "tu vs mediana" E "tu vs top 25%" — mostra dove c'è spazio
- **Tono: consulente amico, non auditor**: "stai lasciando €3.200 sul tavolo" non "sei sotto benchmark"
- **Priorità per impatto/sforzo**: ordinare azioni per ROI atteso, non per gravità del problema
- **Mai solo diagnosi**: ogni semaforo rosso ha il suo passo successivo concreto
- **Stime oneste**: quando si stima, scrivere "(stima)" ma dare comunque il numero — l'incertezza non deve bloccare l'azione
- **Footer disclaimer onesto** sempre presente

## File size target
< 120 KB totale (HTML + CSS + SVG inline). Chart.js solo se ci sono dati mensili disponibili.
