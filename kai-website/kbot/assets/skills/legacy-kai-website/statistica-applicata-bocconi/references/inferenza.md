# Statistica Applicata Bocconi: Inferenza, Probabilità, Stimatori

## 1. STATISTICA DESCRITTIVA AVANZATA

### 1.1 Misure di Tendenza Centrale

| Misura | Formula | Nota |
|--------|---------|------|
| **Media** | $\bar{x} = \frac{1}{n} \sum_{i=1}^{n} x_i$ | Sensibile a outlier |
| **Mediana** | Valore centrale (50° percentile) | Robusta ad outlier |
| **Moda** | Modalità con freq. massima | Per distribuzioni multimodali |
| **Media troncata** | Media senza k% code | Robusto ai valori estremi |

### 1.2 Misure di Dispersione

| Misura | Formula | Nota |
|--------|---------|------|
| **Range** | $R = \max(x_i) - \min(x_i)$ | Non robusto |
| **IQR (Interquartile Range)** | $IQR = Q_3 - Q_1$ | Robusto |
| **Varianza** | $\sigma^2 = \frac{1}{n} \sum_{i=1}^{n} (x_i - \bar{x})^2$ | Biased; campionaria: dividi per n-1 |
| **Deviazione standard** | $\sigma = \sqrt{\sigma^2}$ | Stessa unità di misura di X |
| **Coeff. variazione** | $CV = \frac{\sigma}{\bar{x}} \times 100\%$ | Confronto tra variabilità relative |

### 1.3 Percentili e Quartili

- **P-esimo percentile**: valore sotto cui cade il P% dei dati
- **Q1 (25°)**, **Q2 (50°)**, **Q3 (75°)**
- **Outliers (metodo IQR)**: 
  - Outlier superiore: $x > Q_3 + 1.5 \times IQR$
  - Outlier inferiore: $x < Q_1 - 1.5 \times IQR$

### 1.4 Forma Distribuzione (Asimmetria e Curtosi)

| Indice | Formula | Interpretazione |
|--------|---------|-----------------|
| **Skewness** | $\gamma_1 = \frac{1}{n} \sum_{i=1}^{n} \left(\frac{x_i - \bar{x}}{\sigma}\right)^3$ | >0: asimm. destra; <0: asimm. sinistra |
| **Kurtosis** | $\gamma_2 = \frac{1}{n} \sum_{i=1}^{n} \left(\frac{x_i - \bar{x}}{\sigma}\right)^4 - 3$ | >0: code pesanti (leptocurtica); <0: code leggere |

---

## 2. PROBABILITÀ E VARIABILI ALEATORIE

### 2.1 Distribuzioni Discrete Canoniche

#### Bernoulli: $X \sim \text{Bernoulli}(p)$
- **PMF**: $P(X = x) = p^x (1-p)^{1-x}$, $x \in \{0,1\}$
- **E[X]**: $p$
- **Var(X)**: $p(1-p)$
- **MGF**: $m_X(t) = 1 - p + pe^t$

#### Binomiale: $X \sim \text{Binomial}(n, p)$
- **PMF**: $P(X = x) = \binom{n}{x} p^x (1-p)^{n-x}$, $x = 0,1,...,n$
- **E[X]**: $np$
- **Var(X)**: $np(1-p)$
- **MGF**: $m_X(t) = (1-p + pe^t)^n$

#### Poisson: $X \sim \text{Poisson}(\lambda)$
- **PMF**: $P(X = x) = \frac{\lambda^x e^{-\lambda}}{x!}$, $x = 0,1,2,...$
- **E[X]**: $\lambda$
- **Var(X)**: $\lambda$
- **MGF**: $m_X(t) = e^{\lambda(e^t - 1)}$
- **Uso**: conteggio eventi rari in intervallo fisso

#### Geometrica: $X \sim \text{Geom}(p)$
- **PMF**: $P(X = x) = p(1-p)^{x-1}$, $x = 1,2,...$
- **E[X]**: $\frac{1}{p}$
- **Var(X)**: $\frac{1-p}{p^2}$
- **Uso**: numero trial fino al primo successo

### 2.2 Distribuzioni Continue Canoniche

#### Normale: $X \sim N(\mu, \sigma^2)$
- **PDF**: $f_X(x) = \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)$
- **E[X]**: $\mu$
- **Var(X)**: $\sigma^2$
- **Standardizzazione**: $Z = \frac{X - \mu}{\sigma} \sim N(0,1)$
- **MGF**: $m_X(t) = \exp(\mu t + \frac{1}{2}\sigma^2 t^2)$

#### t-Student: $X \sim t_\nu$
- **PDF**: $f_X(x) = \frac{\Gamma(\frac{\nu+1}{2})}{\sqrt{\pi\nu} \Gamma(\frac{\nu}{2})} \left(1 + \frac{x^2}{\nu}\right)^{-\frac{\nu+1}{2}}$
- **E[X]**: 0 (se $\nu > 1$)
- **Var(X)**: $\frac{\nu}{\nu-2}$ (se $\nu > 2$)
- **Uso**: inferenza su media quando $\sigma$ ignoto; campioni piccoli

#### Chi-quadro: $X \sim \chi^2_\nu$
- **PDF**: $f_X(x) = \frac{1}{2^{\nu/2}\Gamma(\nu/2)} x^{\nu/2-1} e^{-x/2}$, $x > 0$
- **E[X]**: $\nu$
- **Var(X)**: $2\nu$
- **Uso**: test di indipendenza, test adattamento, inferenza varianza

#### F di Fisher: $X \sim F_{\nu_1, \nu_2}$
- **Def**: Rapporto due chi-quadro indip. standardizzati
- **Uso**: test uguaglianza varianze, ANOVA, test significatività globale regressione

#### Uniforme: $X \sim \text{Unif}(a, b)$
- **PDF**: $f_X(x) = \frac{1}{b-a}$, $x \in [a,b]$
- **E[X]**: $\frac{a+b}{2}$
- **Var(X)**: $\frac{(b-a)^2}{12}$

#### Esponenziale: $X \sim \text{Exp}(\lambda)$
- **PDF**: $f_X(x) = \lambda e^{-\lambda x}$, $x > 0$
- **E[X]**: $\frac{1}{\lambda}$
- **Var(X)**: $\frac{1}{\lambda^2}$
- **Uso**: survival analysis, time-to-event

### 2.3 Teoremi Fondamentali

#### Legge dei Grandi Numeri (LLN)
Se $X_1, X_2, ...$ i.i.d. con $E[X_i] = \mu$:
$$\bar{X}_n = \frac{1}{n} \sum_{i=1}^{n} X_i \xrightarrow{P} \mu \quad \text{(convergenza in probabilità)}$$

#### Teorema del Limite Centrale (CLT)
Se $X_1, X_2, ...$ i.i.d. con $E[X_i] = \mu$, $\text{Var}(X_i) = \sigma^2$:
$$\sqrt{n}\left(\bar{X}_n - \mu\right) \xrightarrow{d} N(0, \sigma^2)$$
Equivalentemente: $\bar{X}_n \approx N\left(\mu, \frac{\sigma^2}{n}\right)$ per n grande

---

## 3. STIMATORI E PROPRIETÀ

### 3.1 Proprietà di Uno Stimatore

| Proprietà | Formula/Def | Nota |
|-----------|-------------|------|
| **Correttezza (Unbiasedness)** | $E[\hat{\theta}] = \theta$ | Errore medio nullo |
| **Consistenza** | $\hat{\theta}_n \xrightarrow{P} \theta$ | Converge a valore vero |
| **Efficienza** | $\text{Var}(\hat{\theta}_1) < \text{Var}(\hat{\theta}_2)$ | Minima varianza tra stimatori corretti |
| **Sufficiency** | Contiene tutta informazione campionaria | Riduzione dimesionalità dati |

### 3.2 Stimatori Campionari Principali

| Parametro | Stimatore | Proprietà |
|-----------|-----------|-----------|
| $\mu$ (media pop.) | $\hat{\mu} = \bar{X} = \frac{1}{n}\sum X_i$ | Corretto, consistente, efficiente |
| $\sigma^2$ (varianza) | $\hat{\sigma}^2 = S^2 = \frac{1}{n-1}\sum (X_i - \bar{X})^2$ | Corretto |
| $p$ (proporzione) | $\hat{p} = \frac{x}{n}$ (successi/n) | Corretto, consistente |

### 3.3 Stima di Massima Verosimiglianza (MLE)

$$\hat{\theta}_{MLE} = \arg\max_\theta L(\theta; \mathbf{x}) = \arg\max_\theta \prod_{i=1}^n f(x_i; \theta)$$

**Log-verosimiglianza**: $\ell(\theta) = \sum_{i=1}^n \log f(x_i; \theta)$

**Condizione primo ordine**: $\frac{\partial \ell(\theta)}{\partial \theta} = 0$

**Proprietà MLE**: Asintoticamente normale, efficiente, invariante a trasformazioni monotone.

---

## 4. INTERVALLI DI CONFIDENZA (IC)

### 4.1 Media Popolazione Normale

#### Caso 1: $\sigma$ noto
$$IC_{1-\alpha}(\mu) = \left[\bar{x} - z_{\alpha/2} \frac{\sigma}{\sqrt{n}}, \bar{x} + z_{\alpha/2} \frac{\sigma}{\sqrt{n}}\right]$$
dove $z_{\alpha/2} = \Phi^{-1}(1 - \alpha/2)$

#### Caso 2: $\sigma$ ignoto
$$IC_{1-\alpha}(\mu) = \left[\bar{x} - t_{n-1, \alpha/2} \frac{s}{\sqrt{n}}, \bar{x} + t_{n-1, \alpha/2} \frac{s}{\sqrt{n}}\right]$$
dove $s = \sqrt{\frac{1}{n-1}\sum(x_i - \bar{x})^2}$ e $t_{n-1, \alpha/2}$ quantile t-Student

### 4.2 Proporzione

$$IC_{1-\alpha}(p) = \left[\hat{p} - z_{\alpha/2} \sqrt{\frac{\hat{p}(1-\hat{p})}{n}}, \hat{p} + z_{\alpha/2} \sqrt{\frac{\hat{p}(1-\hat{p})}{n}}\right]$$

**Nota**: Valido per $n\hat{p} \geq 5$ e $n(1-\hat{p}) \geq 5$

### 4.3 Differenza tra Medie (Campioni Indipendenti)

#### Varianze uguali e note
$$IC_{1-\alpha}(\mu_1 - \mu_2) = \left[(\bar{x}_1 - \bar{x}_2) - z_{\alpha/2} \sqrt{\frac{\sigma_1^2}{n_1} + \frac{\sigma_2^2}{n_2}}\right]$$

#### Varianze uguali e ignote
Stimatore pooled: $s_p^2 = \frac{(n_1-1)s_1^2 + (n_2-1)s_2^2}{n_1 + n_2 - 2}$

$$IC_{1-\alpha}(\mu_1 - \mu_2) = \left[(\bar{x}_1 - \bar{x}_2) \pm t_{n_1+n_2-2, \alpha/2} s_p \sqrt{\frac{1}{n_1} + \frac{1}{n_2}}\right]$$

### 4.4 Varianza Popolazione Normale

$$IC_{1-\alpha}(\sigma^2) = \left[\frac{(n-1)s^2}{\chi^2_{n-1, \alpha/2}}, \frac{(n-1)s^2}{\chi^2_{n-1, 1-\alpha/2}}\right]$$

---

## 5. TEST DI IPOTESI PARAMETRICI

### 5.1 Struttura Generale di un Test

1. **Ipotesi**: $H_0$ (nulla) vs $H_1$ (alternativa)
2. **Statistica test**: T (sotto $H_0$)
3. **Regione critica**: valori T che portano a rifiuto $H_0$
4. **Errori**:
   - **Tipo I** ($\alpha$): $P(\text{rifiuto } H_0 | H_0 \text{ vera})$ ← controllato
   - **Tipo II** ($\beta$): $P(\text{non rifiuto } H_0 | H_0 \text{ falsa})$
   - **Potenza**: $1 - \beta = P(\text{rifiuto } H_0 | H_1 \text{ vera})$

### 5.2 Test su Media (Popolazione Normale)

#### $H_0: \mu = \mu_0$ vs $H_1: \mu > \mu_0$ (una coda destra)

**Con $\sigma$ noto**:
$$Z = \frac{\bar{x} - \mu_0}{\sigma/\sqrt{n}} \sim N(0,1) \text{ sotto } H_0$$
Rifiuto se $Z > z_\alpha$ oppure p-value $= 1 - \Phi(Z) < \alpha$

**Con $\sigma$ ignoto**:
$$T = \frac{\bar{x} - \mu_0}{s/\sqrt{n}} \sim t_{n-1} \text{ sotto } H_0$$
Rifiuto se $T > t_{n-1, \alpha}$ oppure p-value $= 1 - F_{t_{n-1}}(T) < \alpha$

#### Due code: $H_0: \mu = \mu_0$ vs $H_1: \mu \neq \mu_0$
Rifiuto se $|Z| > z_{\alpha/2}$ o $|T| > t_{n-1, \alpha/2}$

p-value $= 2 \times [1 - \Phi(|Z|)]$ per test normale

### 5.3 Test su Proporzione

#### $H_0: p = p_0$ vs $H_1: p > p_0$

$$Z = \frac{\hat{p} - p_0}{\sqrt{p_0(1-p_0)/n}} \sim N(0,1) \text{ sotto } H_0$$

Rifiuto se $Z > z_\alpha$

### 5.4 Test su Differenza Medie (Due Popolazioni)

#### Indipendenti, varianze uguali ignote
$$T = \frac{(\bar{x}_1 - \bar{x}_2) - 0}{s_p \sqrt{1/n_1 + 1/n_2}} \sim t_{n_1+n_2-2}$$

**Rifiuto** (test 2 code): $|T| > t_{n_1+n_2-2, \alpha/2}$

#### Test di Levene per uguaglianza varianze
Valida assunzione di uguaglianza prima di pooling.

### 5.5 Test Chi-Quadro

#### Test di Adattamento (Goodness-of-fit)
$$\chi^2 = \sum_{i=1}^k \frac{(O_i - E_i)^2}{E_i} \sim \chi^2_{k-1} \text{ sotto } H_0$$

dove $O_i$ = frequenza osservata, $E_i = n \times p_i$ = frequenza attesa

**Rifiuto**: $\chi^2 > \chi^2_{k-1, \alpha}$ oppure p-value $= 1 - F_{\chi^2_{k-1}}(\chi^2) < \alpha$

#### Test di Indipendenza (Tabella Contingenza)
$$\chi^2 = \sum_{i=1}^r \sum_{j=1}^c \frac{(n_{ij} - E_{ij})^2}{E_{ij}} \sim \chi^2_{(r-1)(c-1)}$$

dove $E_{ij} = \frac{n_{i\cdot} n_{\cdot j}}{n}$ (frequenza attesa sotto indipendenza)

---

## 6. FUNZIONI R CHIAVE (da formulari Bocconi)

```r
# Intervalli di confidenza
CI.mean(x, sigma=NULL, conf.level=0.95)      # Media
CI.prop(x, success, conf.level=0.95)         # Proporzione
CI.diffmean(x, y, type='independent', ...)   # Diff medie
CI.diffprop(x, y, success.x, success.y, ...) # Diff proporzioni

# Test di ipotesi
TEST.mean(x, mu0, alternative='greater')     # Test su media
TEST.prop(x, success, p0, alternative=...)   # Test su proporzione
TEST.diffmean(x, y, type='independent', ...) # Test diff medie
TEST.diffprop(x, y, success.x, success.y, ...) # Test diff proporzioni

# Statistiche
pnorm(q), qnorm(p)    # Normale standard
pt(q, df), qt(p, df)  # t-Student
pchisq(q, df), qchisq(p, df) # Chi-quadro
pf(q, df1, df2), qf(p, df1, df2) # F-Fisher
```

---

**Fonte**: Formulari Bocconi (BEMACS, CLEAM, BEMACC)  
**Ultima revisione**: Aprile 2026
