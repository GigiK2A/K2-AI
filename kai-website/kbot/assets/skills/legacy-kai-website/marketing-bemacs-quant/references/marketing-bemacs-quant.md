# Marketing quantitativo BEMACS — Integrazioni distintive

Questo file documenta contenuti **aggiuntivi** della dispensa Bocconi BEMACS (2024-25, Giorgio Micaletto) non coperti dalle reference di base della skill `marketing-analytics`.

## Competizione di mercato: Herfindahl-Hirschman Index (HHI)

L'HHI quantifica la concentrazione di mercato e il potere concorrenziale relativo:

$$HHI = s_1^2 + s_2^2 + \cdots + s_n^2$$

dove $s_i = \frac{\text{Sales}_i}{\sum_{j=1}^{n} \text{Sales}_j} \cdot 100$ è la quota di mercato percentuale del competitor $i$.

**Interpretazione:**
- HHI < 1500: mercato concentrato, ampia concorrenza
- 1500 < HHI < 2500: concentrazione moderata
- HHI > 2500: alta concentrazione, barriere all'entrata

**Variabilità di mercato (Market Turbulence):**

$$\text{Market Turbulence} = \frac{\text{sd}(\text{Sales}_k)}{\mathbb{E}[\text{Sales}_k]}$$

Misura la volatilità delle vendite in una finestra temporale $k$. Indica instabilità competitiva e opportunità di riacquisizione di quote.

---

## Crescita di mercato

La tassa di crescita di un mercato quantifica l'espansione del segmento:

$$\text{Market Growth} = \frac{\text{Sales}_t - \text{Sales}_{t-1}}{\text{Sales}_{t-1}}$$

Usata per identificare mercati emergenti (alta crescita) vs. maturi (bassa/negativa).

---

## Metriche media pubblicitaria

### Impressions e Reach-Frequency

$$\text{Impressions} = \text{Reach} \times \text{Average Frequency}$$

- **Reach**: numero di individui unici esposti ad almeno un'inserzione.
- **Average Frequency**: numero medio di esposizioni per individuo.
- Applicazione: budget allocation across channels per massimizzare coverage mantenendo efficienza di frequenza.

### Gross Rating Points (GRP)

$$GRP = \sum (\text{Rating Points} \times \text{Frequency})$$

dove i Rating Points sono la percentuale di una demografica specifica esposta. Il GRP sintetizza reach e frequency in una metrica unica di media planning.

---

## Effetti non-lineari e interazioni nella pubblicità

### Lag Effects (Carryover)

L'effetto della pubblicità si distribuisce nel tempo secondo un modello dinamico:

$$y_{i,t} = \beta_0 + \beta_1 X_{i,t} + \beta_2 X_{i,t-1} + \varepsilon_{i,t}$$

Il parametro $\beta_2$ cattura l'effetto ritardato (stock di brand awareness), critico per valutare il ROI a lungo termine versus il mero effetto contemporaneo.

### Interaction Effects

Quando due variabili di marketing si rafforzano mutuamente:

$$y = \beta_0 + \beta_1 X_1 + \beta_2 X_2 + \beta_3 X_1 \cdot X_2 + \varepsilon$$

**Requisito:** il modello deve includere $X_1$ e $X_2$ separatamente; l'omissione di uno rende il coefficiente $\beta_3$ biased.

**Esempio:** Effetto combinato di advertising nazionale + local store promotion è superiore alla somma degli effetti individuali se $\beta_3 > 0$.

---

## Modelli di scelta discreta: logistic regression

Modello probabilistico per outcomes binari (acquisto sì/no, click sì/no):

$$\log\left(\frac{\mathbb{P}[y_i = 1]}{1 - \mathbb{P}[y_i = 1]}\right) = z_i = \beta X_i + \varepsilon_i$$

dove il predittore lineare $z_i$ è trasformato in probabilità via logit:

$$\mathbb{P}[y_i = 1] = \frac{e^{z_i}}{1 + e^{z_i}}$$

**Nota interpretativa:** Un cambiamento unitario in $X$ altera il log-odds (non la probabilità direttamente). Per elasticità, si calcola:

$$\frac{\partial \mathbb{P}[y=1]}{\partial X} = \beta \cdot \mathbb{P}[y=1] \cdot (1 - \mathbb{P}[y=1])$$

---

## Metriche di redditività e valore cliente

### Customer Lifetime Value (CLV) semplificato

$$CLV = M \times \frac{r}{1 + i - r} - AC$$

**Parametri:**
- $M$ = margine di profitto per transazione
- $r$ = retention rate (probabilità di ripetere acquisto)
- $i$ = discount rate (tasso di sconto annuale)
- $AC$ = acquisition cost

**Ipotesi:** $M$, $r$, $i$ costanti nel tempo; orizzonte infinito.

**Uso strategico:** Definisce il massimo acceptable customer acquisition cost. Se $AC < CLV$, l'acquisition è profittevole.

### Customer Referral Value (CRV)

$$CRV = \sum_{j=1}^{N_{\text{referrals}}} CLV_j$$

Somma del CLV dei clienti acquisiti per referral dal cliente primario. Differisce dal CLV perché:
- Referrals hanno typically lower $AC$ (minimal)
- Corr(CLV, referral propensity) è spesso negativa (best spenders ≠ best advocates)

### RFM Analysis

Segmentazione retrospettiva basata su tre dimensioni:

| Dimensione | Definizione | Implicazione |
|---|---|---|
| **Recency** | Giorni dall'ultimo acquisto | Proxy di engagement attuale |
| **Frequency** | Numero acquisti in periodo T | Propensione a ripetere |
| **Monetary Value** | Spesa totale in periodo T | Redditività diretta |

Ogni dimensione è rankizzata (es. quintili 1–5). Combinazioni (es. 5,5,5 = Champions; 1,1,1 = Lost Causes) guidano l'allocazione di retention budget.

---

## Digital Marketing: Consumer Behavior Segmentation

Ricerca di Liu, Lee, Srinivasan (2019) identifica 5 profili basati su search e purchase patterns:

1. **Type 1:** Acquisto diretto (no search, no reviews)
2. **Type 2:** Solo ricerca di prodotto
3. **Type 3:** Ricerca + acquisto (sequential)
4. **Type 4:** Ricerca + lettura review
5. **Type 5:** Omnichannel completo (search, review, purchase)

**Finding critico:** Review content influisce significativamente su sales quando:
- Varianza dei rating è bassa (consenso)
- Rating medio è alto
- Mercato è competitivo/immaturo
- Brand information è scarsa

Implicazione: per mercati emergenti, investire in review collection prioritario.

---

## Social Tagging e Brand Associative Networks

Metriche estratte da social media tagging (Twitter, Instagram, TikTok):

$$\text{Brand Familiarity} = \frac{\text{# Non-Negative Tags Linked to Brand}}{\text{# All Tags Linked to Brand}}$$

$$\text{Brand Favorability} = \frac{\text{# Positive Tags Associated with Brand}}{\text{# All Tags Associated with Brand}}$$

**Applicazione:**
- Brand forti: gestire "category dominance" (mantener top-of-mind)
- Brand deboli: costruire connessioni con main category brand per "category entry"

---

## Performance Metrics: Stock Returns e Firm Value

### Tobin's Q

$$\text{Tobin's Q} = \frac{\text{Market Value of Firm}}{\text{Replacement Cost of Assets}}$$

Misura il premium che il mercato assegna al brand equity e agli asset intangibili rispetto al costo contabile.

### Stock Returns

$$\text{Return} = \frac{P_1 - P_0 + D}{P_0}$$

dove $P_0$ = prezzo iniziale, $P_1$ = prezzo finale, $D$ = dividendi. Risk-adjusted returns (CAPM) controllano per sistematic risk:

$$R_i - R_f = \alpha + \beta(R_m - R_f) + \varepsilon$$

**Insight:** CMO presence e marketing investment correlano con higher risk-adjusted stock returns (McAlister et al. 2016), suggerendo effetto long-term su firm value.

---

## Note di integrazione

### Gaps rimasti nella dispensa BEMACS

La dispensa **non tratta:**
- Econometria causale (IV, FE/RE, DiD) per isolamento effetti endogeni
- Modelli di scelta avanzati (nested logit, mixed logit per eterogeneità)
- Hazard models per churn prediction e duration analysis
- Modelli di diffusione (Bass, SIS epidemic models)
- Bayesian hierarchical modeling (random coefficients, priors)
- Machine learning (classification trees, neural nets per propensity)
- Pricing ottimale e revenue management
- Network effects e viral contagion formale

Questi temi rimangono **fuori scope** della dispensa introduttiva Bocconi, coerente con audience (studenti magistrali, no PhD).

### Quando usare questo documento

Allegare/integrare nei seguenti scenari:
1. **Market analysis:** HHI, turbulence per competitive positioning
2. **Media planning:** reach-frequency allocation, GRP optimization
3. **Digital/performance marketing:** consumer segmentation Liu-Lee-Srinivasan, social tagging metrics
4. **Causality & long-term effects:** lag modeling per advertising carryover, interaction terms
5. **Customer value:** CLV/CRV/RFM per retention strategy

Per approfondimenti quantitativi **avanzati** (econometria, Bayesian, ML), rimandare a:
- `modelli-regressione-segmentazione.md` (cluster, RFM base)
- `research-methodology.md` (inference, testing)
- `advertising-clv-performance.md` (CLV, attribution)
