# Casi Numerici — Bilancio Consolidato & IFRS

## Caso 1: Consolidamento Metodo Integrale (Acquisition)

**Contesto:** Società Holding "Rossi SpA" acquisisce 100% di "Bianchi Srl" (full consolidation). Sono dati al 31/12/2024.

**Bilanci individuali (€000):**

| Voce | Rossi SpA | Bianchi Srl |
|------|-----------|-----------|
| **Attivo Fisso** | 8,000 | 2,500 |
| **Crediti/Liquid.** | 3,500 | 1,200 |
| **Passività** | −5,000 | −1,500 |
| **Equity** | 6,500 | 2,200 |
| **Ricavi** | 12,000 | 4,500 |
| **Costi** | −10,500 | −3,800 |
| **Utile** | 1,500 | 700 |

**Prezzo di acquisto:** €2,500k. Fair value assets Bianchi: €3,500k; Liabilities: €1,500k.

**Calcolo Goodwill:**

1. **Fair Value dell'equity acquisito:**
   - FV assets = €3,500k
   - FV liabilities = €1,500k
   - FV net assets = €2,000k

2. **Goodwill:**
   - Considerazione trasferita = €2,500k
   - Fair value net assets = €2,000k
   - **Goodwill = €500k** (positive, da ammortizzare/testare annualmente)

**Consolidamento (eliminazioni):**

1. **Eliminazione investimento:**
   - Dr. Equity Bianchi €2,200k
   - Dr. Goodwill €500k
   - Cr. Investimento in Bianchi €2,700k
   - (Acquis. differenza: €2,500k − €2,200k = €300k → altri comp.ri/ perdita)

2. **Tabella di controllo post-consolidamento:**

| | Rossi SpA | Bianchi Srl | Consolid. | Consolidato |
|---|---|---|---|---|
| **Attivo Fisso** | 8,000 | 2,500 | − | 10,500 |
| **Goodwill** | − | − | +500 | 500 |
| **Crediti/Liquid.** | 3,500 | 1,200 | − | 4,700 |
| **Tot. Attivo** | 11,500 | 3,700 | 500 | 15,700 |
| **Passività** | −5,000 | −1,500 | − | −6,500 |
| **Equity Gruppo** | 6,500 | − | − | 9,200 |
| **Utile Gruppo** | 1,500 | 700 | − | 2,200 |

**Risultato:** Bilancio consolidato post-acquisition (goodwill €500k, utile consolid. €2.2M).

---

## Caso 2: Analisi DuPont Applicata (Retail Italiana)

**Contesto:** Azienda retail "Moda Italiana Srl" (2024). ROE dal bilancio al 31/12.

**Dati (€000):**
- Net Income: €450
- Sales: €8,500
- Total Assets: €4,200
- Total Equity: €2,100

**Calcolo DuPont (3-factor):**

1. **Net Profit Margin:**
   - NPM = Net Income / Sales = 450 / 8,500 = **5.29%**

2. **Asset Turnover:**
   - AT = Sales / Total Assets = 8,500 / 4,200 = **2.02x**

3. **Equity Multiplier (Financial Leverage):**
   - EM = Total Assets / Total Equity = 4,200 / 2,100 = **2.0x**

4. **ROE (via decomposition):**
   - ROE = NPM × AT × EM
   - ROE = 5.29% × 2.02 × 2.0 = **21.4%**

5. **Check diretto:**
   - ROE = Net Income / Equity = 450 / 2,100 = 21.4% ✓

**Interpretazione dettagliata:**
- **5.29% net margin** è buono per retail (media sector ~4%)
- **2.02x asset turnover** mostra efficienza operativa (ogni €1 di asset genera €2.02 vendite)
- **2.0x leva** è moderata per retail (non eccessivamente indebitata)
- **21.4% ROE** è eccellente, vicino a target 20%+ per equity investors

**Leverage Analysis:** Se leva fosse 2.5x invece di 2.0x → ROE = 26.8%. Ma rischio insolvenza aumenterebbe. Equilibrio attuale è buono.

---

## Caso 3: Rendiconto Finanziario (Metodo Indiretto)

**Contesto:** PMI TLC "Telefonica Piccoli" (2024). Costruzione cash flow statement da bilancio.

**Dati bilancio (€000):**

| | 31/12/2024 | 31/12/2023 | Δ |
|---|---|---|---|
| **Utile netto** | 320 | − | − |
| **Ammortamenti** | 180 | − | − |
| **Crediti clienti** | 1,200 | 1,100 | +100 |
| **Magazzino** | 450 | 500 | −50 |
| **Debiti fornitori** | 600 | 550 | +50 |
| **Mutui** | 2,000 | 1,500 | +500 |
| **Dividendi pagati** | 100 | − | − |

**Rendiconto (metodo indiretto):**

```
ATTIVITÀ OPERATIVE
Utile netto                           €320k
+ Ammortamenti                        €180k
= Utile rettificato                   €500k
- Aumento crediti clienti (−100k)     −€100k
+ Diminuzione magazzino (+50k)        +€50k
+ Aumento debiti fornitori (+50k)     +€50k
= CASH FLOW OPERATIVO                 €500k
```

**Calcolo dettagliato WC:**
- Δ crediti = 1,200 − 1,100 = +100 (cash out, riduce CFO)
- Δ magazzino = 450 − 500 = −50 (cash in, aumenta CFO)
- Δ fornitori = 600 − 550 = +50 (cash in, aumenta CFO)

**ATTIVITÀ DI INVESTIMENTO**
- Acquisiti PP&E                      −€250k
= CASH FLOW INVESTIMENTO              −€250k

**ATTIVITÀ DI FINANZIAMENTO**
+ Mutui nuovi                         +€500k
- Dividendi pagati                    −€100k
= CASH FLOW FINANZIAMENTO             +€400k

**VARIAZIONE NETTA CASSA**
€500k + (−€250k) + €400k = **€650k aumento di cassa**

**Interpretazione:** Azienda genera cash robusto (€500k da ops), investe moderato (€250k) e finanzia crescita con debito. Situazione healthy.

---

## Caso 4: Leasing IFRS 16 (Right-of-Use Asset)

**Contesto:** Azienda TLC affitta server in data center. Lease 5 anni, canone annuale €300k.

**Parametri:**
- Lease payment annuale: €300k
- Lease term: 5 anni
- Incremental borrowing rate: 3.5% (tasso con cui azionariato si finanzierebbe)
- Residual value guarantee: €0 (non c'è)

**Calcolo PV Lease Liability:**

| Anno | Pagamento | Fattore PV (3.5%) | PV Pagamento |
|------|-----------|-------------------|--------------|
| 1 | €300k | 0.9662 | €289.9k |
| 2 | €300k | 0.9335 | €280.1k |
| 3 | €300k | 0.9019 | €270.6k |
| 4 | €300k | 0.8714 | €261.4k |
| 5 | €300k | 0.8420 | €252.6k |
| **TOTALE** | | | **€1,354.6k** |

**Riconoscimento iniziale (t=0):**

**Stato Patrimoniale:**
```
Attivo:
+ Right-of-Use Asset                  €1,354.6k

Passivo:
+ Lease Liability (current)           €281.1k (pagam. anno 1)
+ Lease Liability (non-current)       €1,073.5k (anni 2-5)
```

**Conto Economico anno 1:**
- Interesse passivo (3.5% × €1,354.6k) = €47.4k
- Ammortamento ROU (€1,354.6k / 5) = €270.9k
- Canone pagato: €300k (cassa)

**Journal entry anno 1:**
```
Dr. Lease Liability               €300.0k
Cr. Cassa                                      €300.0k
(Pagamento canone)

Dr. Interesse Passivo              €47.4k
Dr. Leasing ROU (amm.to)          €270.9k
Cr. ROU Asset Accumulated Deprec.              €270.9k
Cr. Debito per interessi                       €47.4k
```

**Interpretazione:** Con IFRS 16, lease non è fuori bilancio: azienda riconosce sia asset che liability. Impatta ROA, ROE e debt ratios.

