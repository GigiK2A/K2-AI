# Template Dashboard HTML — HostBoost Full

Dashboard HTML self-contained. File `hostboost-{slug}-{YYYYMMDD}-dashboard.html`. Apribile offline, Chart.js da CDN.

## Scopo

Il revenue manager che il titolare non ha. In un file, tutto quello che serve per capire la performance, confrontarsi col mercato e sapere cosa fare. Livello professionale: questo documento può essere mostrato in banca, al consulente o al socio.

---

## Design Language

Stile "executive dashboard" — non cruscotto da startup, non foglio Excel colorato. Ispirato a report STR/CBRE adattati per strutture indipendenti italiane.

### Palette
```css
:root {
  --primary: #0F2544;
  --primary-light: #1A3A6B;
  --primary-ultra-light: #EEF2F8;
  --accent: #E8A020;
  --accent-light: #FDF3E3;
  --green: #1A7A4A;
  --green-bg: #E8F5EE;
  --yellow: #C07A00;
  --yellow-bg: #FFF8E8;
  --red: #B02020;
  --red-bg: #FDF0F0;
  --neutral: #4A5568;
  --bg: #F0F2F5;
  --surface: #FFFFFF;
  --surface-2: #F8FAFC;
  --border: #E2E8F0;
  --text: #1A1A2E;
  --text-secondary: #4A5568;
  --text-muted: #8090A8;
  --shadow: 0 2px 12px rgba(15,37,68,0.07);
  --shadow-lg: 0 8px 32px rgba(15,37,68,0.13);
}
```

### Tipografia
- Stack: `-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif`
- Section titles: 20px semibold `--primary`, border-bottom 2px `--accent`
- KPI hero numbers: 44px bold
- KPI secondary: 22px
- Table: 14px
- Caption/disclaimer: 12px `--text-muted`

---

## Struttura Completa

### 0. Sticky Header (72px)
- Gradiente `--primary` → `--primary-light`
- Sinistra: K2-AI logo (SVG) + "HostBoost Report"
- Centro: "{Nome Struttura} · {tipologia} · {comune}"
- Destra: data generazione + "Periodo: {mese/anno inizio} – {mese/anno fine}"
- Sotto header: nav-tabs sticky (scrollTo alle sezioni) — tab: Overview · KPI · Stagionalità · Canali · Benchmark · Recensioni · Forecast · Azioni

### 1. Executive Summary (full width, sfondo `--primary`)

Card scura orizzontale con 5 colonne:

| Score Generale | RevPAR | Occupancy | ADR | Rating |
|---|---|---|---|---|
| 74/100 (gauge) | €58 ▲+12% | 64% ▲+5pp | €142 ▼-3% | 8.6 ★ |

Sotto la riga KPI: 3 insight testuali autogenerati:
- 🟢 "Il tuo RevPAR è cresciuto del 12% vs periodo precedente"
- 🟡 "L'ADR è leggermente sotto il tuo compset (-€8). Margine di recupero stimato: €4.200/anno"
- 🔴 "La dipendenza OTA al 71% è sopra la soglia critica: stai pagando circa €9.800/anno di commissioni recuperabili"

### 2. Sezione KPI Core — grid 2×2 (poi 2 card aggiuntive sotto)

**Card RevPAR:**
- Numero grande (44px bold) + trend freccia + % vs periodo precedente
- Benchmark: mediana zona | top quartile zona
- Mini line chart 12 mesi (Chart.js, 200px altezza)
- Semaforo colored border-left
- 1 riga analisi: "Stagione estiva ha trainato il +12% — mantenere la pressione su luglio-agosto"

**Card ADR:**
- Stesso schema
- In più: "ADR weekend vs weekday" se disponibile (due numeri affiancati)
- Mini line chart

**Card Occupancy:**
- Numero con % grande
- "Giorni venduti: X su Y disponibili"
- Mini bar chart mensile (12 barre colorate per semaforo)

**Card ALOS (Average Length of Stay):**
- Numero giorni
- Breakdown: "Diretti: X.X gg | OTA: Y.Y gg"
- Commento: soggiorno medio più corto delle strutture simili → azione

**Card Booking Window (quanto prima prenota il cliente):**
- Media giorni di anticipo
- Distribution: last-minute (0-7gg) / short (8-30gg) / advance (31-90gg) / early (90+gg)
- Implicazione per pricing: "XX% last-minute = opportunità di yield management"

**Card Cancellation Rate:**
- % cancellazioni
- Benchmark zona
- Impatto economico: "X notti perse in media = €Y/mese di ricavo a rischio"

### 3. Sezione Stagionalità — full width

**3a. Grafico combo 12 mesi (Chart.js, altezza 360px)**
- Barre: Occupancy mensile (colorate per semaforo)
- Linea: ADR mensile
- Linea tratteggiata: RevPAR mensile
- Asse X: mesi | Asse Y sinistro: % Occ | Asse Y destro: € ADR/RevPAR
- Legenda interattiva (toggle series)
- Fasce stagionali colorate in background: BASSA (grigio) / SPALLA (azzurro) / ALTA (arancio)
- Tooltip rich: mostra tutti e 3 i valori al hover

**3b. Heatmap settimanale (se dati disponibili)**
- Grid 52 settimane × 7 giorni, colore intensità = Occupancy
- Identifica pattern weekday/weekend, festività, ponti

**3c. Analisi stagionalità testuale**
- "Periodo di punta: {mesi migliori} — RevPAR medio €X"
- "Periodo critico: {mesi peggiori} — RevPAR medio €Y"
- "Indice di stagionalità: {alto/medio/basso} — il tuo fatturato dipende per il XX% da 3 mesi"
- Opportunità: "Alzare i prezzi di XX% nei weekend di {mese X} porterebbe €Z aggiuntivi"

### 4. Sezione Distribuzione Canali — 2 colonne

**Colonna sinistra: Mix attuale (Pie chart)**
- Slice: Diretto web, Booking.com, Airbnb, Expedia, Telefono/email, Altri
- Tooltip: % notti + % ricavi + commissione media stimata per canale
- Sotto chart: "Commissioni OTA stimate pagate nell'anno: **€X.XXX**"

**Colonna destra: Mix target consigliato (Pie chart desaturato)**
- Basato su best practice strutture simili con performance top 25%
- Delta per canale: freccia + punti percentuali da guadagnare/cedere
- Risparmio stimato: "Raggiungendo il mix target: -€X.XXX commissioni/anno"

**Tabella dettaglio canali:**
| Canale | Notti % | Ricavi % | Commissione % | ADR medio | Score |
|---|---|---|---|---|---|
| Diretto web | 29% | 31% | 0% | €148 | 🟢 |
| Booking.com | 51% | 48% | 15% | €139 | 🔴 troppo alto |
| Airbnb | 12% | 13% | 3% | €162 | 🟢 |
| Telefono | 8% | 8% | 0% | €145 | 🟡 |

### 5. Sezione Benchmark Zona — full width

**Tabella comparativa principale:**
| Metrica | La tua struttura | Mediana zona | Top 25% | Gap mediana | Gap top 25% |
|---|---|---|---|---|---|
| RevPAR | €58 | €52 | €82 | 🟢 +€6 | 🟡 -€24 |
| ADR | €142 | €148 | €195 | 🟡 -€6 | 🔴 -€53 |
| Occupancy | 64% | 55% | 72% | 🟢 +9pp | 🟡 -8pp |
| Quota diretta | 29% | 38% | 62% | 🔴 -9pp | 🔴 -33pp |
| Rating medio | 8.6 | 8.1 | 9.1 | 🟢 +0.5 | 🟡 -0.5 |
| ALOS | 2.4 | 2.6 | 3.8 | 🟡 -0.2 | 🔴 -1.4 |
| Cancellation rate | 18% | 22% | 9% | 🟢 +4pp | 🔴 -9pp |

**Radar chart (Chart.js) — posizionamento visuale**
- 6 assi: RevPAR, ADR, Occupancy, Canali diretti, Rating, ALOS
- Serie 1: tua struttura (linea piena `--accent`)
- Serie 2: mediana zona (linea tratteggiata `--text-muted`)
- Serie 3: top 25% (area fill `--green-bg`)

**Narrative positioning:**
"Sei **forte su Occupancy e Rating**, ma lasci valore sull'ADR e sulla distribuzione diretta. Il profilo è tipico delle strutture che riempiono bene ma non prezzano abbastanza. Il potenziale non sfruttato è stimato in **€X.XXX/anno**."

### 6. Sezione Recensioni — grid 3 colonne

**Colonna 1 — Rating per piattaforma (gauge semi-circolari)**
- Booking.com: X.X / 10
- Google: X.X / 5 → normalizzato /10
- TripAdvisor: X.X / 5 → normalizzato /10
- Airbnb: X.X / 5 → normalizzato /10
- Rating composito K2-AI: media ponderata

Ogni gauge: SVG semicircolare colorato per semaforo, valore al centro, confronto benchmark zona sotto.

**Colonna 2 — Temi positivi più citati**
- Barre orizzontali con label e frequenza (% delle recensioni che le citano)
- Top 5: es. "Pulizia 87%" / "Posizione 81%" / "Colazione 74%" / "Staff 69%" / "Silenzio 58%"
- Highlight: "Questi sono i tuoi asset commerciali — usali nelle OTA e nel sito"

**Colonna 3 — Aree di miglioramento**
- Stesso schema, tonalità rosate
- Top 3-4 temi negativi con frequenza
- Sotto ognuno: suggerimento operativo in 1 riga (es. "WiFi lento: router su ogni piano — costo stimato €120")

**Analisi sentiment trend (se dati multi-periodo disponibili):**
Mini line chart rating medio per trimestre.

### 7. Sezione Pricing vs Compset — full width (se dati disponibili)

**Scatter/Line chart (Chart.js):**
- Asse X: date campione (30-90 gg)
- Asse Y: prezzo EUR
- Serie cliente: linea spessa `--primary`
- Serie compset 1-5: linee sottili colorate
- Linea tratteggiata: mediana compset
- Evidenziati i periodi dove sei troppo basso o troppo alto

**Analisi automatica:**
- "Nei weekend hai un gap di +€X rispetto al compset — stai prezzando in linea ✓"
- "Nei feriali di agosto sei €Y sotto la mediana — potenziale non sfruttato"
- "Nei ponti di primavera sei €Z sopra — rischio volume basso"

### 8. Sezione Forecast 12 mesi — full width

**Grafico barre grouped (3 scenari × 4 metriche):**
- Scenari: Conservativo / Base / Ottimistico
- Metriche: RevPAR | ADR | Occupancy % | Ricavi totali stimati
- Ogni barra: etichetta con valore + % vs anno corrente
- Colori: conservativo grigio / base blu / ottimistico verde

**Ipotesi per scenario (table):**
| Leva | Conservativo | Base | Ottimistico |
|---|---|---|---|
| ADR week | +3% | +8% | +15% |
| ADR weekend | +5% | +12% | +20% |
| Occupancy | stabile | +3pp | +6pp |
| Quota diretta | +2pp | +8pp | +15pp |

**ROI del piano HostBoost:**
- "Se raggiungi lo scenario Base: +€X.XXX ricavi aggiuntivi vs oggi"
- "Investimento HostBoost: da 899 EUR. Payback stimato: {N} mesi"

### 9. Sezione Piano Azioni — 5 card accordion

Ordinate per: impatto × fattibilità.

Ogni card:

**Header (sempre visibile):**
```
[N]  NOME AZIONE BREVE               Impatto ●●●●○  Difficoltà ●●○○○  Timeline: 2 settimane
     Sintesi una riga con numeri specifici
```

**Body espanso:**
- **Situazione attuale:** dati precisi della struttura
- **Opportunità:** quanto vale in € (stima specifica)
- **Piano operativo — 4 step:**
  1. Step specifico con tool/platform nominata
  2. Step specifico
  3. Step specifico
  4. Come misurare il risultato (KPI + soglia + timing)
- **Risorse necessarie:** tempo stimato + eventuale costo
- **Rischi:** 1 riga su cosa può andare storto + mitigazione

### 10. Footer

3 righe:
- "Report generato il {data} per {nome struttura}. Dati forniti dall'utente, benchmark da fonti pubbliche 2024-2025."
- "Per aggiornare il cruscotto o richiedere un nuovo ciclo di analisi: info@k2-ai.it"
- "Powered by **K2-AI** — Il revenue manager che non hai, costruito su misura sulla tua struttura. — k2-ai.it"

---

## Architettura dati JS

```html
<script id="reportData" type="application/json">
{
  "struttura": { "nome": "", "tipo": "", "comune": "", "regione": "", "camere": 0, "gg_apertura": 0 },
  "periodo": { "da": "", "a": "" },
  "kpi": {
    "revpar": { "valore": 0, "prev": 0, "mediana_zona": 0, "top25_zona": 0 },
    "adr": { "valore": 0, "prev": 0, "mediana_zona": 0, "top25_zona": 0 },
    "occupancy": { "valore": 0, "prev": 0, "mediana_zona": 0, "top25_zona": 0 },
    "alos": { "valore": 0, "mediana_zona": 0 },
    "booking_window": { "media_gg": 0, "last_minute_pct": 0 },
    "cancellation_rate": { "valore": 0, "mediana_zona": 0 }
  },
  "mensile": [
    { "mese": "Gen", "occupancy": 0, "adr": 0, "revpar": 0 }
  ],
  "canali": [
    { "nome": "Diretto", "notti_pct": 0, "ricavi_pct": 0, "commissione_pct": 0, "adr": 0 }
  ],
  "rating": {
    "booking": 0, "google": 0, "tripadvisor": 0, "airbnb": 0,
    "temi_positivi": [], "temi_negativi": []
  },
  "compset": [],
  "score_globale": 0,
  "azioni": []
}
</script>
```

Tutti i grafici si costruiscono leggendo `JSON.parse(document.getElementById('reportData').textContent)`. Nessun dato hardcoded nel JS. I valori stimati/non disponibili usano `null` e vengono gestiti con fallback testuali ("dato non disponibile").

---

## Accorgimenti Chiave

- **Sempre €, non %**: tradurre ogni gap in impatto economico annuo stimato
- **Comparazione doppia sempre**: tu vs mediana E tu vs top 25% — mostra sia dove sei sia dove puoi arrivare
- **Stima sempre preferibile a vuoto**: se manca un dato, stimare con "(stima K2-AI)" è meglio di un placeholder
- **Azioni ordinabili**: il titolare potrebbe voler vedere le azioni per "impatto" o per "facilità" — ordinare di default per impatto × facilità
- **Nessun wall of text**: massimo 3 righe per paragrafo, poi punto elenco
- **Numeri sempre arrotondati in modo intelligente**: €4.200 non €4.183 — la precisione falsa riduce la credibilità
- **Responsive mobile**: il titolare legge spesso dal telefono — sezioni stack su 1 colonna sotto 768px

## File size target
< 600 KB inclusi i dati. Chart.js da CDN (`https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`).
