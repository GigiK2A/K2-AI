# Casi Numerici — Controllo di Gestione

## Caso 1: Activity-Based Costing (ABC)

**Contesto:** Produttore di componenti automotive (settore manifatturiero). Costi comuni su due prodotti: "Bullone Standard" e "Bullone Premium".

**Dati annuali (€):**

| | Bullone Standard | Bullone Premium |
|---|---|---|
| **Unità prodotte** | 100,000 | 20,000 |
| **Costi materiali diretti** | €200,000 | €80,000 |
| **Costi MOD diretti** | €100,000 | €50,000 |
| **Ore lavorazione** | 5,000h | 3,000h |
| **Setup produttivi** | 5 volte | 15 volte |
| **Ispezioni qualità** | 10 volte | 40 volte |

**Costi comuni da ripartire:** €270,000

**Metodo tradizionale (su ore MOD):**
- Ore totali = 5,000 + 3,000 = 8,000h
- Tasso CG/ora = €270,000 / 8,000h = €33.75/h
- CG Standard = 5,000 × €33.75 = €168,750
- CG Premium = 3,000 × €33.75 = €101,250

**Metodo ABC (3 cost drivers):**

**Activity analysis:**

| Activity | Cost | Driver | Volume Std | Volume Prem | Total |
|----------|------|--------|---|---|---|
| **Setup** | €120,000 | Setup | 5 | 15 | 20 |
| **Ispez.ne** | €100,000 | Ispezioni | 10 | 40 | 50 |
| **Lavorazione** | €50,000 | Ore MOD | 5,000 | 3,000 | 8,000 |

**Tassi activity:**
- Setup: €120,000 / 20 setup = €6,000/setup
- Ispezione: €100,000 / 50 ispezioni = €2,000/ispezione
- Lavorazione: €50,000 / 8,000 ore = €6.25/ora

**Allocazione ABC:**

**Bullone Standard:**
- Setup: 5 × €6,000 = €30,000
- Ispezioni: 10 × €2,000 = €20,000
- Lavorazione: 5,000 × €6.25 = €31,250
- **CG Totale = €81,250**
- **CG/unità = €81,250 / 100,000 = €0.8125/unità**

**Bullone Premium:**
- Setup: 15 × €6,000 = €90,000
- Ispezioni: 40 × €2,000 = €80,000
- Lavorazione: 3,000 × €6.25 = €18,750
- **CG Totale = €188,750**
- **CG/unità = €188,750 / 20,000 = €9.4375/unità**

**Confronto e insight:**

| | Metodo Tradizionale | ABC | Δ |
|---|---|---|---|
| **CG/unità Std** | €1.69 | €0.81 | −52% |
| **CG/unità Prem** | €5.06 | €9.44 | +86% |

**Interpretazione:** Premium è sottocostato tradizionalmente perché consuma molti setup e ispezioni. ABC rivela che Premium dovrebbe avere margine più basso. Decisione: aumentare prezzo Premium o ridurre mix verso Standard.

---

## Caso 2: Analisi Scostamenti (Varianza Completa)

**Contesto:** Azienda alimentare (pasta fresca) traccia scostamenti su costi di produzione gennaio 2024.

**Budget prodotto (500 kg pasta):**

| Materiale | Quantità | Prezzo/unità | Costo Budget |
|-----------|----------|-------------|-------------|
| **Semola** | 600 kg | €2.50/kg | €1,500 |
| **Uova** | 150 kg | €8.00/kg | €1,200 |
| **MOD** | 40 ore | €25.00/ora | €1,000 |
| **CG variabili** | — | €15/unità prodotta | €7,500 |
| **TOTALE BUDGET** | | | **€11,200** |

**Dati consuntivi (500 kg):**

| Materiale | Quantità | Prezzo/unità | Costo Consuntivo |
|-----------|----------|-------------|-------------|
| **Semola** | 630 kg | €2.40/kg | €1,512 |
| **Uova** | 155 kg | €8.50/kg | €1,317.50 |
| **MOD** | 42 ore | €26.00/ora | €1,092 |
| **CG variabili** | — | €16/unità | €8,000 |
| **TOTALE CONSUNTIVO** | | | **€11,921.50** |

**Scostamento totale = €11,921.50 − €11,200 = €721.50 (sfavorevole)**

**Analisi dettagliata per input:**

**1. Semola**
- Scostamento quantità (efficiency): (630 − 600) × €2.50 = +€75 (uso eccessivo)
- Scostamento prezzo: (€2.40 − €2.50) × 630 = −€63 (risparmio)
- **Subtotal semola = +€12 (leggermente sfavorevole)**

**2. Uova**
- Scostamento quantità: (155 − 150) × €8.00 = +€40 (uso eccessivo)
- Scostamento prezzo: (€8.50 − €8.00) × 155 = +€77.50 (prezzo rialzato)
- **Subtotal uova = +€117.50 (sfavorevole)**

**3. MOD**
- Scostamento ore (efficiency): (42 − 40) × €25.00 = +€50 (ore extra)
- Scostamento tasso: (€26.00 − €25.00) × 42 = +€42 (tasso più alto)
- **Subtotal MOD = +€92 (sfavorevole)**

**4. CG Variabili**
- Scostamento volume: (500 − 500) × €15 = €0
- Scostamento spesa: (€16 − €15) × 500 = +€500 (costi più alti)
- **Subtotal CG = +€500 (sfavorevole)**

**Tabella riepilogativa scostamenti:**

| Elemento | Quantità | Prezzo | Totale |
|----------|----------|--------|--------|
| **Semola** | +€75 | −€63 | +€12 |
| **Uova** | +€40 | +€77.50 | +€117.50 |
| **MOD** | +€50 | +€42 | +€92 |
| **CG Var.** | — | — | +€500 |
| **TOTALE SCOSTAMENTI** | | | **+€721.50** |

**Azioni correttive:**
- **Semola:** varianza quantità piccola; controllare setup linea
- **Uova:** aumenti prezzi fornitori; negoziare contratti annuali
- **MOD:** tempi di produzione allungati; verificare manutenzione macchine
- **CG:** aumento sorprendente; audit costi indiretti variabili (energia?)

---

## Caso 3: Balanced Scorecard con KPI Numerici

**Contesto:** Catena retail di lusso (abbigliamento) costruisce scorecard 2024.

**Target annuali e Q1 actual:**

| **Prospettiva** | **KPI** | **Target 2024** | **Q1 Actual** | **Status** |
|---|---|---|---|---|
| **Finanziaria** | Revenue CAGR | +8% YoY | +5.2% | ⚠️ |
| | Gross Margin | 58% | 56.8% | ⚠️ |
| | EBITDA Margin | 18% | 16.2% | ⚠️ |
| **Cliente** | NPS (Net Promoter Score) | 65 | 62 | ⚠️ |
| | Customer Retention | 82% | 79% | ⚠️ |
| | Avg. Basket Value | €185 | €172 | ⚠️ |
| **Processi Interni** | On-Time Delivery | 95% | 93.5% | ⚠️ |
| | Inventory Turnover | 5.2x/anno | 4.8x | ⚠️ |
| | Returns Rate | <3% | 3.5% | ⚠️ |
| **Apprendimento/Crescita** | Employee Engagement | 7.5/10 | 7.1 | ⚠️ |
| | Training Hours/FTE | 30h | 18h | 🔴 |
| | Digital Capability Index | 72% | 65% | ⚠️ |

**Analisi causa-effetto:**
1. **Finanziaria:** Revenue bassa (5.2% vs 8%) causa margin compression
2. **Cliente:** NPS basso, retention bassa → basket value diminuisce
3. **Processi:** Inventory turnover basso → moglie di prodotto; returns alti → qualità issues
4. **Crescita:** Training insufficiente (18h vs 30h) → capability degradati

**Azioni Q2:**
- Revisione mix produttivo (più SKU ad alto margin)
- Programma intensivo customer experience training (−1 mese, +15h/FTE)
- Analisi returns: difetti vs gestione logistica
- Potenziamento supply chain (inventory: −10% stock, +velocity)

---

## Caso 4: Economic Value Added (EVA)

**Contesto:** Azienda automativa "Motori Italia Srl" valuta creazione di valore (2024).

**Dati (€M):**

| | Valore |
|---|---|
| **NOPAT (Net Operating Profit After Tax)** | €45.5 |
| **Invested Capital Iniziale** | €280 |
| **WACC** | 7.5% |

**Calcolo EVA:**

1. **Capital Charge (CC):**
   - CC = Invested Capital × WACC
   - CC = €280M × 0.075 = **€21M**

2. **EVA:**
   - EVA = NOPAT − CC
   - EVA = €45.5M − €21M = **€24.5M**

3. **EVA Margin (%):**
   - EVA% = EVA / NOPAT = 24.5 / 45.5 = **53.8%**

**Dinamica del valore:**

| | 2024 | 2025 target |
|---|---|---|
| **NOPAT** | €45.5M | €48.2M (+5.9%) |
| **Invested Capital** | €280M | €295M (+5.4%) |
| **WACC** | 7.5% | 7.5% |
| **CC** | €21.0M | €22.1M |
| **EVA** | €24.5M | €26.1M (+6.5%) |

**Interpretazione:**
- **EVA positivo (€24.5M)**: azienda crea valore; ROI (45.5/280=16.3%) > WACC (7.5%)
- **Trend target 2025**: EVA cresce più velocemente di NOPAT (+6.5% vs +5.9%) perché invested capital contiene efficienza
- **Benchmark:** Se settore automotive ha EVA margin medio 35-40%, Motori Italia è leader (53.8%)

**Decisioni strategiche:**
- Reinvestire surplus EVA in R&D / nuovi prodotti
- Valutare share buyback o dividendi se no opportunità di investimento ROI > WACC
- Monitorare WACC (se tassi salgono, CC aumenta, pressione su EVA)

