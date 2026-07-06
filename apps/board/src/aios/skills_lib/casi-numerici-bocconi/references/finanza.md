# Casi Numerici — Finanza Aziendale

## Caso 1: Calcolo WACC per PMI Manifatturiera Italiana

**Contesto:** Ditta Ferrari SpA (manifatturiera, fatturato €15M) quotata su AIM. Necessario WACC per valutazione progetto di espansione.

**Input:**
- Equity value (market cap): €12M
- Debt (netto): €3M
- Risk-free rate (Btp 10y): 2.5%
- Market premium: 5.5%
- Beta levered: 1.2
- Tax rate: 24%
- Cost of debt (pre-tax): 4.2%

**Calcolo passo-passo:**

1. **Cost of Equity (CAPM):**
   - Re = Rf + β(Rm − Rf)
   - Re = 2.5% + 1.2 × 5.5% = 2.5% + 6.6% = **9.1%**

2. **Pesi di Capitale:**
   - V = Equity + Debt = 12 + 3 = €15M
   - We = 12/15 = 80%
   - Wd = 3/15 = 20%

3. **Cost of Debt (after-tax):**
   - Rd(after-tax) = 4.2% × (1 − 0.24) = 4.2% × 0.76 = **3.19%**

4. **WACC:**
   - WACC = We·Re + Wd·Rd(after-tax)
   - WACC = 0.80 × 9.1% + 0.20 × 3.19%
   - WACC = 7.28% + 0.64% = **7.92%**

**Risultato:** WACC = 7.92%

**Interpretazione:** Progetti con rendimento atteso > 7.92% creano valore per l'azienda. Tasso conservativo per PMI manifatturiera italiana in contesto 2024.

---

## Caso 2: Valutazione DCF Semplice (3 anni)

**Contesto:** Startup di e-commerce (settore retail) con proiezione semplificata.

**Input (€000):**
- Free Cash Flow anno 1: €200
- FCF anno 2: €350
- FCF anno 3: €450
- FCF anno 4+ (perpetua): €480 (crescita 1.5% annua)
- WACC: 10%
- Terminal Growth Rate: 1.5%

**Calcolo passo-passo:**

1. **PV dei FCF espliciti (anni 1-3):**
   - PV1 = 200 / 1.10¹ = €181.8
   - PV2 = 350 / 1.10² = €289.3
   - PV3 = 450 / 1.10³ = €338.0
   - **Σ PV (anni 1-3) = €809.1k**

2. **Terminal Value (Gordon Growth):**
   - TV = FCF4 / (WACC − g) = 480 / (0.10 − 0.015)
   - TV = 480 / 0.085 = €5,647k

3. **PV del Terminal Value:**
   - PV(TV) = 5,647 / 1.10³ = 5,647 / 1.331 = €4,244k

4. **Enterprise Value:**
   - EV = PV(FCF 1-3) + PV(TV) = 809.1 + 4,244 = **€5,053k**

**Risultato:** Enterprise Value ≈ €5.05M

**Interpretazione:** Se azienda ha debito €500k, equity value = 5,053 − 500 = €4,553k. Prezzo per quota da negoziare basato su questa valutazione.

---

## Caso 3: Calcolo Duration Bond Italiano

**Contesto:** Obbligazione corporate emessa da banca italiana.

**Input:**
- Valore nominale: €1,000
- Cedola annuale: 3.5% (€35/anno)
- Scadenza: 5 anni
- YTM (yield to maturity): 4%
- Frequency: annuale

**Calcolo passo-passo:**

1. **Prezzo dell'obbligazione (PV dei flussi):**
   - P = 35/(1.04)¹ + 35/(1.04)² + 35/(1.04)³ + 35/(1.04)⁴ + 1,035/(1.04)⁵
   - P = 33.65 + 32.36 + 31.12 + 29.92 + 850.36
   - **P = €977.41**

2. **Macaulay Duration (weighted average):**
   - t·CF_t / (1+y)^t per ogni periodo, sommare e dividere per prezzo
   
   | Anno | CF | PV(CF) | PV×t |
   |------|-----|--------|-------|
   | 1 | 35 | 33.65 | 33.65 |
   | 2 | 35 | 32.36 | 64.72 |
   | 3 | 35 | 31.12 | 93.36 |
   | 4 | 35 | 29.92 | 119.68 |
   | 5 | 1,035 | 850.36 | 4,251.80 |
   | | | **977.41** | **4,563.21** |

   - Duration = 4,563.21 / 977.41 = **4.67 anni**

3. **Modified Duration:**
   - DM = Duration / (1 + y) = 4.67 / 1.04 = **4.49 anni**

**Risultato:** Modified Duration = 4.49 anni

**Interpretazione:** Se YTM sale di 1%, prezzo scende di circa 4.49%. Misura di rischio tasso per investitori.

---

## Caso 4: Valutazione Opzione Call (Black-Scholes)

**Contesto:** Call option su azione Generali (titolo bancario-assicurativo italiano).

**Input:**
- Prezzo spot (S₀): €25
- Strike price (K): €27
- Scadenza (T): 0.25 anni (3 mesi)
- Risk-free rate (r): 2.5%
- Volatilità (σ): 18% annua
- Dividend yield: 0% (per semplicità)

**Calcolo passo-passo:**

1. **Parametri d1 e d2:**
   - d1 = [ln(S₀/K) + (r + σ²/2)·T] / (σ·√T)
   - d1 = [ln(25/27) + (0.025 + 0.18²/2)·0.25] / (0.18·√0.25)
   - d1 = [−0.0770 + 0.0226] / 0.09 = −0.0544 / 0.09 = **−0.604**

2. **N(d1) e N(d2):**
   - (da tavola normale) N(−0.604) ≈ 0.273
   - d2 = d1 − σ·√T = −0.604 − 0.09 = −0.694
   - N(d2) ≈ 0.244

3. **Valore Call:**
   - C = S₀·N(d1) − K·e^(−rT)·N(d2)
   - C = 25 × 0.273 − 27 × e^(−0.00625) × 0.244
   - C = 6.825 − 27 × 0.9938 × 0.244
   - C = 6.825 − 6.560 = **€0.27**

**Risultato:** Valore call ≈ €0.27 per azione

**Interpretazione:** Call è OTM (out of the money), valore basso. Sensato per opzioni a breve scadenza lontane da strike.

