---
name: corporate-finance
description: >
  Finanza aziendale operativa per professionisti. Valutazione DCF, capital budgeting, struttura del capitale,
  analisi finanziaria, M&A, e gestione del rischio. Basato su corso Bocconi. Usa SEMPRE per: decisioni di
  investimento, NPV IRR payback, analisi di valore, WACC CAPM beta, negoziazioni finanziarie, fusioni
  acquisizioni, ristrutturazioni di debito, valutazione azienda, multipli EV/EBITDA P/E, DCF unlevered free
  cash flow, capital structure Modigliani-Miller, leverage buyout LBO, working capital, analisi di bilancio
  finanziaria, rating creditizio, costo del capitale, risk management finanziario. Attiva per "quanto vale
  questa azienda", "calcolo WACC", "analisi investimento", "conviene l'acquisizione", "struttura del capitale
  ottimale", "DCF valuation", "multipli di mercato".
---

# Finanza Aziendale Corporativa

Guida pratica alla valutazione e gestione finanziaria di aziende. Questo skill copre i framework fondamentali per decisioni di investimento, valutazione del valore aziendale, ottimizzazione della struttura del capitale, e analisi finanziaria operativa.

## 1. Decisioni di Investimento: NPV, IRR, e Profitability Index

### Net Present Value (NPV)
Il NPV è il criterio principale per accettare/rifiutare un progetto di investimento:

**NPV = -C₀ + Σ(Cₜ / (1+r)ᵗ)**

- **C₀** = Investimento iniziale
- **Cₜ** = Flussi di cassa nel periodo t
- **r** = Tasso di sconto (costo del capitale)

**Regola**: Accettare il progetto se NPV > 0. Un NPV positivo significa che il progetto crea valore superiore alla soglia di redditività richiesta dal mercato.

### Internal Rate of Return (IRR)
L'IRR è il tasso di sconto che rende NPV = 0:

**NPV = C₀ + C₁/(1+IRR) + C₂/(1+IRR)² + ... + Cₜ/(1+IRR)ᵗ = 0**

**Regola**: Accettare il progetto se IRR > r (costo del capitale). 

*Attenzione*: IRR e NPV possono dare risultati diversi con progetti mutuamente esclusivi o flussi di cassa non convenzionali. In questi casi, preferire NPV.

### Profitability Index
Per progetti a capitale limitato, usare l'indice di redditività:

**PI = NPV / Investimento Iniziale**

Scegliere il progetto con PI più alto tra i candidati.

---

## 2. Capital Budgeting: Cash Flows Incrementali e Sunk Costs

### Principi Fondamentali
- **Usare cash flows, non accounting profits**
- **Includere effetti incrementali**: solo i flussi che cambiano a causa del progetto
- **Escludere sunk costs**: costi già sostenuti, irrilevanti per la decisione

### Componenti del Cash Flow
1. **Investimento iniziale (CapEx)**: Acquisto di impianti, macchinari, infrastrutture
2. **Operating cash flow**: EBIT × (1 - Aliquota fiscale) + Ammortamenti
3. **Working capital**: Variazioni in crediti, scorte, debiti verso fornitori
4. **Terminal value / Salvage value**: Realizzo finale degli asset

### Trattamento Speciale
- **Opportunità costi**: Se una risorsa ha usi alternativi, considerare il valore di mercato
- **Effetti collaterali**: Cannibalizazione su altri prodotti vs. sinergie
- **Overhead allocation**: Solo i costi incrementali si considerano

---

## 3. Struttura del Capitale: Modigliani-Miller e Trade-off Theory

### Proposizioni MM (Mercati Perfetti)
In assenza di tasse, costi di fallimento e asimmetrie informative:
- **MM I**: Valore dell'azienda indipendente da capitale proprio vs. debito
- **MM II**: Cost of equity aumenta linearmente con leverage

**E(R_equity) = R_asset + (R_asset - R_debt) × (Debt/Equity)**

### Con Tasse Societarie
Il debito diventa vantaggioso per lo **scudo fiscale**:

**Valore dello scudo = Tasso fiscale × Debito**

Più debito = più interesse deducibile = minori tasse pagate = maggior valore dell'azienda.

### Trade-off Theory
Equilibrio tra:
- **Benefici del debito**: Scudo fiscale, disciplina manageriale
- **Costi del debito**: Rischio di fallimento, aumento costo del capitale, agency costs

Il **livello ottimale di debito** bilancia questi effetti.

### Pecking Order Theory
Manager seguono preferenza:
1. Autofinanziamento (utili non distribuiti)
2. Debito (meno asimmetria informativa)
3. Equity (segnale negativo al mercato)

---

## 4. Costo del Capitale: WACC, CAPM, Beta

### WACC (Weighted Average Cost of Capital)
**WACC = (E/V) × R_e + (D/V) × R_d × (1 - Tc)**

- **E/V** = % di equity sul totale
- **D/V** = % di debito sul totale
- **R_e** = Costo dell'equity
- **R_d** = Costo del debito
- **Tc** = Aliquota fiscale

### CAPM (Capital Asset Pricing Model)
**R_e = R_f + β × (R_m - R_f)**

- **R_f** = Risk-free rate (titoli di stato a lungo termine)
- **β** = Beta dell'azienda (sensibilità al mercato)
- **R_m - R_f** = Market risk premium (equity risk premium, tipicamente 5-8%)

### Beta
Misura di rischio sistematico:
- **β > 1**: Stock più volatile del mercato
- **β = 1**: Stock muove con il mercato
- **β < 1**: Stock meno volatile

Beta si modifica con il leverage:
**β_levered = β_unlevered × [1 + (1 - Tc) × (D/E)]**

---

## 5. Metodi di Valutazione Aziendale

### DCF (Discounted Cash Flow)
Metodo fondamentale basato sul valore attuale dei flussi futuri:

**Enterprise Value = Σ(FCFF_t / (1+WACC)ᵗ) + Terminal Value / (1+WACC)ⁿ**

Terminal Value (perpetuity growth):
**TV = FCFF_final × (1+g) / (WACC - g)**

**Equity Value = Enterprise Value - Net Debt**

### Valutazione per Comparabili (Multiples)
Confronto con aziende simili pubblicamente quotate:

- **EV/EBITDA**: Enterprise value / EBITDA operativo
  - Utile per comparare aziende con leverage diverso
  - Non sensibile a scelte contabili di ammortamento
  
- **P/E (Price-to-Earnings)**: Prezzo/Utile netto
  - Semplice, basato su utili
  - Sensibile a struttura del capitale e tasse
  
- **P/BV (Price-to-Book)**: Prezzo/Valore libri
  - Utile per aziende capital-intensive
  - Riflette aspettative di ROE futuro

### Valutazione Asset-Based
**Equity Value = Attivo totale - Passivo totale**

Appropriata solo quando:
- Azienda in liquidazione
- Valore contabile riflette valore di mercato
- Poche operazioni future attese

---

## 6. Analisi Finanziaria: Ratios e DuPont

### Profitabilità
- **ROE** = Net Income / Equity (redditività per azionista)
- **ROA** = Operating Income (post-tax) / Total Assets (efficienza operativa)
- **Operating Margin** = EBIT / Sales (efficienza operativa)

**DuPont Analysis**:
**ROA = Operating Margin × Asset Turnover**

Identifica se bassa redditività deriva da margini bassi (settore competitivo) o asset poco efficienti (cattiva gestione).

### Liquidità
- **Current Ratio** = Current Assets / Current Liabilities (> 1.5 tipico)
- **Quick Ratio** = (Cash + Receivables) / Current Liabilities (> 1)
- **Cash Ratio** = Cash / Current Liabilities (conservativo)

### Leva Finanziaria
- **Debt/Equity ratio**: Proporzione di debito vs. capitale proprio
- **Debt/Assets**: Percentuale di finanziamento tramite debito
- **Interest Coverage** = EBIT / Interest Payments (capacità di pagare gli interessi)
- **Debt Service Coverage** = (EBIT + Depreciation) / (Interest + Principal Repayment)

### Efficienza
- **Asset Turnover** = Sales / Total Assets
- **Inventory Turnover** = COGS / Average Inventory
- **Receivables Turnover** = Sales / Average Receivables
- **Cash Conversion Cycle** = DIO + DSO - DPO
  - **DIO** (Days Inventory Outstanding)
  - **DSO** (Days Sales Outstanding)
  - **DPO** (Days Payable Outstanding)

---

## 7. Politica dei Dividendi: Payout, Buyback, Segnali

### Decisioni di Payout
Dopo aver finanziato investimenti profittevoli, le aziende decidono il **payout ratio**:

**Payout Ratio = Dividendi / Net Income**

- **Alto payout** (50-70%): Aziende mature con flussi stabili
- **Basso payout** (0-30%): Aziende in crescita, reinvestimento opportunità
- **Zero payout**: Startup, ristrutturazioni, situazioni finanziarie tese

### Share Buybacks
Alternativa (o complemento) ai dividendi:
- Riduce numero di azioni outstanding
- Aumenta EPS (earnings per share) se ROE > costo del capitale
- Vantaggio fiscale (differito vs. immediato con dividendi)
- Segnale di fiducia nel valore dell'azienda

### Signaling Effect
Mercato interpreta dividendi/buyback come segnale sulle prospettive future:
- **Aumento dividendo**: Fiducia in stabilità flussi futuri
- **Taglio dividendo**: Difficoltà finanziarie o reinvestimento opportunità
- **Buyback aggressivo**: Stock sottovalutato oppure eccesso di liquidità

---

## 8. M&A: Tipi, Valutazione, Sinergie

### Tipologie di Fusioni
- **Orizzontale**: Concorrenti dello stesso settore
- **Verticale**: Fornitori/clienti
- **Conglomerato**: Settori diversi

### Valutazione M&A
1. **Stand-alone value**: Valore aziendale target come entità indipendente (DCF)
2. **Synergy value**: Valore aggiunto dalle sinergie
3. **Acquisition price** = Stand-alone + % sinergie

### Tipi di Sinergie
- **Revenue synergies**: Cross-selling, eliminazione duplicazioni di costi
- **Cost synergies**: Economie di scala, eliminazione overlaps manageriali
- **Financial synergies**: Tax shields, accesso a credito più economico
- **Diversification**: Riduzione rischio flussi (spesso sopravvalutato)

### Metriche Accretion/Dilution
- **Accretive deal**: EPS post-acquisition > EPS pre-acquisition
- **Dilutive deal**: EPS post-acquisition < EPS pre-acquisition
- Importanza: Sinergie devono compensare il prezzo pagato (acquisition premium)

---

## 9. Gestione del Capitale Circolante

### Componenti
- **Inventory**: Giorni di output rappresentati in magazzino
- **Receivables**: Crediti verso clienti (termini di pagamento)
- **Payables**: Debiti verso fornitori (termini di acquisto)

**Cash Conversion Cycle = DIO + DSO - DPO**

### Trade-offs
- **Inventory basso**: Riduce costo di finanziamento ma rischio stockout
- **Receivables basso**: Migliora cash flow ma rischi di perdita clienti
- **Payables elevato**: Finanziamento gratuito ma peggiora rapporti con fornitori

### Ottimizzazione
Il working capital target dipende dal settore:
- **Retail**: Cycle breve, spesso negativo (incassa prima di pagare)
- **Manifattura**: Cycle moderato (scorte + incassi - pagamenti)
- **Servizi professionali**: Receivables lunghi, inventory praticamente zero

---

## 10. Gestione del Rischio: Hedging e Derivative Basics

### Tipi di Rischio Aziendale
- **Rischio valutario**: Esposizione a cambi (aziende esportatrici)
- **Rischio di commodity**: Fluttuazioni prezzi materie prime
- **Rischio di tasso di interesse**: Esposizione a tassi su debito a tasso variabile
- **Rischio operativo**: Volatilità di ricavi e costi

### Hedging Strumenti Base
- **Forward contracts**: Bloccano prezzo futuro (non tradato)
- **Futures**: Forward standardizzati, tradati in borsa
- **Swap**: Scambio di flussi (es. tasso fisso vs. variabile)
- **Option**: Diritto senza obbligo (call = comprare, put = vendere)

### Decisione di Hedge
Hedge vale quando:
- Volatilità è sostenuta e misurabile
- Costo del derivato è inferiore a valore della protezione
- Riduce probabilità di distress finanziario
- Non crea nuove esposizioni (basis risk)

---

## Framework Operativo: Checklist Decisionale

### Prima di Investire
- [ ] Calcolare NPV a costo del capitale appropriato
- [ ] Verificare IRR > costo del capitale
- [ ] Analizzare effetti incremental: sunk costs esclusi
- [ ] Considerare opportunità costi e effetti collaterali
- [ ] Stress test con scenari pessimistici

### Prima di Finanziare
- [ ] Calcolare WACC target basato su D/E ottimale
- [ ] Considerare scudo fiscale del debito
- [ ] Verificare capacity di servizio debito (interesse coverage > 2x)
- [ ] Confrontare costo debito vs. equity

### Prima di Valutare Azienda
- [ ] DCF con proiezioni realistiche, g prudente
- [ ] Cross-check con comparabili (multiples)
- [ ] Sensibilità a WACC e g
- [ ] Per M&A: isolate target synergies, pay premium massimo sostenibile

### Prima di Distribuire Liquidità
- [ ] Verificare disponibilità di investimenti profittevoli (NPV > 0)
- [ ] Pianificare strategia payout coerente (segnale al mercato)
- [ ] Per buyback: verificare stock undervalued vs. WACC

---

## Riferimenti Rapidi: Formule Chiave

| Metrica | Formula | Uso |
|---------|---------|-----|
| **NPV** | -C₀ + Σ(Cₜ/(1+r)ᵗ) | Decisione investimento |
| **IRR** | NPV = 0 risolvere per r | Ranking progetti |
| **WACC** | (E/V)×Rₑ + (D/V)×Rₐ×(1-Tc) | Tasso di sconto |
| **CAPM** | Rₑ = Rₓ + β×(Rₘ-Rₓ) | Costo equity |
| **ROE** | Net Income / Equity | Redditività |
| **P/E** | Prezzo / EPS | Valutazione relativa |
| **EV/EBITDA** | (Market cap + Net Debt) / EBITDA | Valutazione asset-agnostic |
| **D/E** | Debito / Equity | Leverage |
| **CCC** | DIO + DSO - DPO | Efficienza circolante |

---

**Per consultazioni rapide, ricordare**: 
- Costo del capitale è la soglia di redditività: ogni investimento deve superarla
- Flussi di cassa incrementali sono il cuore dell'analisi: ignorare sunk costs e overhead allocati
- Valutazione è sensibile a ipotesi di crescita futura: stress test sempre
- Struttura del capitale ha effetti reali solo con tasse e costi di fallimento
- M&A crea valore solo se sinergie eccedono il premio pagato
