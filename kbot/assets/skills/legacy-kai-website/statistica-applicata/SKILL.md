---
name: statistica-applicata
description: >-
  Statistica applicata per PMI italiane: analisi descrittiva, regressione,
  forecasting vendite, test A/B, correlazioni, visualizzazione dati. Senza
  necessità di competenze matematiche avanzate — output orientato alla decisione.
---

# Statistica Applicata — Decisioni Basate sui Dati

## Analisi descrittiva — metriche base

| Metrica | Calcolo | Quando usarla |
|---------|---------|---------------|
| **Media** | Σx / n | Dati simmetrici, senza outlier forti |
| **Mediana** | Valore centrale ordinato | Dati con outlier (fatturati, tempi) |
| **Moda** | Valore più frequente | Categorie (prodotti più venduti) |
| **Dev. standard** | √(Σ(x-μ)²/n) | Variabilità, coerenza consegne |
| **Coefficiente variazione** | σ/μ × 100 | Confronto variabilità tra serie diverse |
| **Percentile 90** | Valore sotto cui cade il 90% | SLA: "il 90% delle consegne in X giorni" |

## Forecasting vendite — metodi pratici

### Media mobile (semplice)
```
Previsione mese M = Media degli ultimi N mesi
N = 3 per trend rapido, N = 12 per stagionale stabile
```

### Exponential Smoothing (ETS)
```
Previsione_t = α × Reale_{t-1} + (1-α) × Previsione_{t-1}
α = 0.3 → memoria lunga (stabile)
α = 0.7 → reattivo ai cambiamenti recenti
```

### Stagionalità — decomposizione
```
Vendite = Trend × Stagionalità × Irregolarità
Indice stagionale mese M = Media vendite M / Media annuale
```

Esempio: se luglio pesa 1.35 sulla media → aspettati +35% in luglio.

## Regressione lineare — uso pratico PMI

**Domanda**: "Le vendite dipendono dagli investimenti marketing?"

```
y = a + b×x

y = vendite mensili
x = spesa marketing mensile
b = incremento vendite per ogni €1 in marketing
R² = quanto x spiega y (0=nulla, 1=perfetto, > 0.7 = buono)
```

Interpretazione R²:
- R² = 0.85 → 85% della variazione vendite spiegata dalla variabile X
- Se R² < 0.3: cercare altre variabili esplicative

## Test A/B — quando e come

Quando: confrontare due versioni (email, landing page, prezzo, processo).

**Dimensione campione minima**:
```
n = 16 × σ² / δ²
σ = dev. standard attesa
δ = minima differenza rilevante

Regola pratica: almeno 100 osservazioni per gruppo per effetti > 10%
```

**Significatività statistica**: p-value < 0.05 (95% confidenza che la differenza non sia casuale).

Errore comune: concludere dopo 3 giorni → attendere almeno 2 cicli completi (es. 2 settimane per email settimanali).

## KPI PMI — analisi standard

### Vendite
- **Tasso conversione** = Ordini / Preventivi × 100 (target B2B: >30%)
- **Ticket medio** = Fatturato / N° ordini
- **Concentrazione clienti** = % fatturato top 3 clienti (rischio se >50%)

### Operatività
- **OTD** (On Time Delivery) = Consegne puntuali / Totale consegne
- **Lead time medio** = Media (data consegna - data ordine)
- **% scarti/resi** = Unità difettose / Totale prodotte

### Finanziario
- **DSO** (giorni credito) = (Crediti / Fatturato) × 365
- **DPO** (giorni debito) = (Debiti / Acquisti) × 365
- **Margine EBITDA** = EBITDA / Ricavi × 100

## Correlazione — interpretazione

| Valore r | Interpretazione |
|----------|-----------------|
| 0.9 — 1.0 | Correlazione molto forte |
| 0.7 — 0.9 | Correlazione forte |
| 0.5 — 0.7 | Correlazione moderata |
| 0.3 — 0.5 | Correlazione debole |
| < 0.3 | Correlazione trascurabile |

**Correlazione ≠ causalità**: prezzi gelati correlano con annegamenti (estate). Verificare sempre la logica causale.

## Visualizzazione — quale grafico per quale dato

| Dato | Grafico |
|------|---------|
| Trend temporale | Linea |
| Confronto categorie | Barre verticali |
| Composizione (parti/totale) | Torta (max 5 fette) |
| Distribuzione valori | Istogramma |
| Correlazione tra due variabili | Scatter plot |
| Performance vs target | Bullet chart o gauge |
| Mappa termica performance | Heatmap |

Regola: un grafico = un messaggio. Se serve spiegare il grafico, il grafico è sbagliato.
