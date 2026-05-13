# Statistica Applicata Bocconi: Regressione, ANOVA, Diagnostica

## 1. REGRESSIONE LINEARE SEMPLICE

### 1.1 Modello e Stima OLS

**Modello**: $Y_i = \beta_0 + \beta_1 X_i + \epsilon_i$, con $\epsilon_i \sim N(0, \sigma^2)$ i.i.d.

**Stimatori OLS** (Ordinary Least Squares):

$$\hat{\beta}_1 = \frac{\sum_{i=1}^n (X_i - \bar{X})(Y_i - \bar{Y})}{\sum_{i=1}^n (X_i - \bar{X})^2} = \frac{S_{XY}}{S_{XX}} = \frac{\text{Cov}(X,Y)}{\text{Var}(X)}$$

$$\hat{\beta}_0 = \bar{Y} - \hat{\beta}_1 \bar{X}$$

**Previsione**: $\hat{Y}_i = \hat{\beta}_0 + \hat{\beta}_1 X_i$

**Residui**: $\hat{\epsilon}_i = Y_i - \hat{Y}_i$

### 1.2 Proprietà Stimatori OLS

Sotto assunzioni (normalità residui, omoschedasticità, no autocorrelazione):

| Proprietà | Formula |
|-----------|---------|
| **E[$\hat{\beta}_1$]** | $\beta_1$ (corretto) |
| **Var($\hat{\beta}_1$)** | $\frac{\sigma^2}{\sum_{i=1}^n (X_i - \bar{X})^2} = \frac{\sigma^2}{S_{XX}}$ |
| **SE($\hat{\beta}_1$)** | $\sqrt{\frac{\hat{\sigma}^2}{S_{XX}}}$ dove $\hat{\sigma}^2 = \frac{\sum \hat{\epsilon}_i^2}{n-2}$ |
| **E[$\hat{\beta}_0$]** | $\beta_0$ (corretto) |

### 1.3 Test di Significatività Singoli Coefficienti

#### Test: $H_0: \beta_j = 0$ vs $H_1: \beta_j \neq 0$

$$T_j = \frac{\hat{\beta}_j}{\text{SE}(\hat{\beta}_j)} \sim t_{n-2}$$

**Rifiuto**: $|T_j| > t_{n-2, \alpha/2}$ oppure p-value $= 2 \times (1 - F_{t_{n-2}}(|T_j|)) < \alpha$

Intervallo confidenza: $\hat{\beta}_j \pm t_{n-2, \alpha/2} \times \text{SE}(\hat{\beta}_j)$

### 1.4 Bontà di Adattamento (Goodness-of-Fit)

| Indice | Formula | Intervallo |
|--------|---------|-----------|
| **SST** (Tot Var Y) | $\sum (Y_i - \bar{Y})^2$ | - |
| **SSR** (Var spiegata) | $\sum (\hat{Y}_i - \bar{Y})^2$ | - |
| **SSE** (Residui) | $\sum (Y_i - \hat{Y}_i)^2 = \sum \hat{\epsilon}_i^2$ | - |
| **Identità** | $SST = SSR + SSE$ | - |
| **R²** | $\frac{SSR}{SST} = 1 - \frac{SSE}{SST}$ | [0, 1] |
| **R² Adjusted** | $R^2_a = 1 - \frac{SSE/(n-k-1)}{SST/(n-1)}$ | [0, 1], penalizza regressori |

**Interpretazione R²**: proporzione varianza Y spiegata da X

### 1.5 Test Globale (ANOVA Regressione)

#### Test: $H_0: \beta_1 = 0$ vs $H_1: \beta_1 \neq 0$

$$F = \frac{SSR / 1}{SSE / (n-2)} = \frac{\text{MSR}}{\text{MSE}} \sim F_{1, n-2}$$

**Rifiuto**: $F > F_{1, n-2, \alpha}$ oppure p-value $< \alpha$

**Nota**: Equivalente a test t su $\beta_1$ in regressione semplice ($F = T^2$)

### 1.6 Intervalli di Confidenza e Previsione

#### Per media predetta $E[Y|X = x_0]$:
$$\hat{Y}_0 \pm t_{n-2, \alpha/2} \times \hat{\sigma} \sqrt{\frac{1}{n} + \frac{(x_0 - \bar{X})^2}{S_{XX}}}$$

#### Per singolo valore predetto $Y|X = x_0$:
$$\hat{Y}_0 \pm t_{n-2, \alpha/2} \times \hat{\sigma} \sqrt{1 + \frac{1}{n} + \frac{(x_0 - \bar{X})^2}{S_{XX}}}$$

**Nota**: Intervallo previsione più ampio (contiene incertezza intrinseca + stima)

---

## 2. REGRESSIONE LINEARE MULTIPLA

### 2.1 Modello Matriciale

**Modello**: $\mathbf{Y} = \mathbf{X}\boldsymbol{\beta} + \boldsymbol{\epsilon}$

$Y_i = \beta_0 + \beta_1 X_{i,1} + ... + \beta_k X_{i,k} + \epsilon_i$, con $\epsilon_i \sim N(0, \sigma^2)$

**Stimatore OLS**:
$$\hat{\boldsymbol{\beta}} = (\mathbf{X}^T \mathbf{X})^{-1} \mathbf{X}^T \mathbf{Y}$$

**Proprietà**:
- $E[\hat{\boldsymbol{\beta}}] = \boldsymbol{\beta}$ (corretto)
- $\text{Cov}(\hat{\boldsymbol{\beta}}) = \sigma^2 (\mathbf{X}^T \mathbf{X})^{-1}$
- $\text{SE}(\hat{\beta}_j) = \sqrt{\hat{\sigma}^2 \times (\mathbf{X}^T \mathbf{X})^{-1}_{jj}}$

### 2.2 Test Significatività Globale (F-Test)

#### Test: $H_0: \beta_1 = ... = \beta_k = 0$ vs $H_1: \text{almeno un } \beta_j \neq 0$

$$F = \frac{SSR / k}{SSE / (n - k - 1)} = \frac{\text{MSR}}{\text{MSE}} \sim F_{k, n-k-1}$$

**Rifiuto**: $F > F_{k, n-k-1, \alpha}$ oppure p-value $< \alpha$

**Nota**: Nullo se p-value > 0.05 suggerisce modello poco esplicativo

### 2.3 Test Significatività Singoli Coefficienti

$$T_j = \frac{\hat{\beta}_j}{\text{SE}(\hat{\beta}_j)} \sim t_{n-k-1}$$

Rifiuto se $|T_j| > t_{n-k-1, \alpha/2}$

### 2.4 Selezione Variabili

#### Forward Selection
1. Inizia con modello vuoto
2. Aggiungi regressore con miglior fit (AIC minimo o p-value massimo)
3. Ripeti fino a: nessun miglioramento significativo o criterio di arresto

#### Backward Elimination
1. Inizia con modello completo
2. Rimuovi regressore con p-value massimo (meno significativo)
3. Ripeti fino a: tutti p-value < soglia (es. 0.05)

#### Stepwise (Forward + Backward)
Combina: ogni passo add una variabile, poi verifica se rimuoverne altre migliora fit

#### Criteri Informazionali

| Criterio | Formula | Seleziona |
|----------|---------|-----------|
| **AIC** | $\text{AIC} = 2k - 2\ln(\hat{L})$ | AIC minimo |
| **BIC** | $\text{BIC} = k \ln(n) - 2\ln(\hat{L})$ | BIC minimo (penalizza k più forte) |

**Nota**: $\hat{L}$ = log-verosimiglianza massima; k = numero parametri

---

## 3. DIAGNOSTICA REGRESSIONE

### 3.1 Assunzioni Modello OLS

1. **Linearità**: Relazione lineare tra Y e X
2. **Indipendenza residui**: No autocorrelazione ($\text{Cov}(\epsilon_i, \epsilon_j) = 0$)
3. **Omoschedasticità**: Varianza costante ($\text{Var}(\epsilon_i) = \sigma^2$)
4. **Normalità**: $\epsilon_i \sim N(0, \sigma^2)$
5. **No multicollinearità**: Regressori non perfettamente correlati

### 3.2 Multicollinearità

**Problema**: Regressori altamente correlati → distorsione errori standard, instabilità stime

**Indicatori**:

| Test | Formula/Metodo | Soglia |
|------|---|---|
| **Correlazione semplice** | $|r_{X_i, X_j}|$ | > 0.8 ⚠ |
| **VIF** (Variance Inflation Factor) | $\text{VIF}_j = \frac{1}{1 - R_j^2}$ | > 10 ⚠; > 5 caution |
| **Numero di condizionamento** | $\kappa = \frac{\lambda_{\max}}{\lambda_{\min}}$ | > 30 ⚠ |

**Rimedi**:
- Aumentare n (dati)
- Standardizzare/ridimensionare regressori
- PCA o ridge regression
- Rimuovere variabili ridondanti

### 3.3 Eteroschedasticità (Non-Costanza Varianza)

**Problema**: $\text{Var}(\epsilon_i) = \sigma_i^2$ non costante → stime OLS inefficienti

**Test**:

| Test | Stat | Ipotesi Nulla |
|------|------|---------------|
| **Breusch-Pagan** | Regress $\hat{\epsilon}_i^2$ su X, calcola test F | Omoschedasticità |
| **White** | Regress $\hat{\epsilon}_i^2$ su X, X², X×X, calcola LM | Omoschedasticità |

**Rimedi**:
- Trasformazione Y (log, radice quadrata)
- Weighted Least Squares (WLS)
- Standard errors robusti (Huber-White)

### 3.4 Autocorrelazione Residui

**Problema**: $\text{Cov}(\epsilon_i, \epsilon_j) \neq 0$ per $i \neq j$ → stime inefficienti, IC errati

**Test Durbin-Watson**:
$$DW = \frac{\sum_{t=2}^n (\hat{\epsilon}_t - \hat{\epsilon}_{t-1})^2}{\sum_{t=1}^n \hat{\epsilon}_t^2}$$

| Intervallo | Interpretazione |
|-----------|-----------------|
| DW ≈ 2 | No autocorrelazione (ideale) |
| DW < 2 | Autocorrelazione positiva ⚠ |
| DW > 2 | Autocorrelazione negativa ⚠ |

**Rimedi**:
- Modelli AR(1), ARIMA per serie temporali
- Differenziazione dati
- Lag della variabile dipendente

### 3.5 Normalità Residui

**Test**:

| Test | Metodo |
|------|--------|
| **Jarque-Bera** | Stat = $n \left[ \frac{\text{Skewness}^2}{6} + \frac{(\text{Kurtosis}-3)^2}{24} \right] \sim \chi^2_2$ |
| **Q-Q Plot** | Visuale: punti devono giacere su retta 45° |
| **Shapiro-Wilk** | Per piccoli campioni |

**Rimedi**: Trasformazione Y, OLS robusto, GLM

### 3.6 Outlier e Osservazioni Influenti

| Misura | Formula | Soglia |
|--------|---------|--------|
| **Standardized residuals** | $\frac{\hat{\epsilon}_i}{\text{SE}(\hat{\epsilon}_i)}$ | > 2 ⚠; > 3 anomalo |
| **Leverage $h_{ii}$** | Diagonale matrice $(X^T X)^{-1} X^T$ | > $2k/n$ ⚠ |
| **Cook's distance** | $D_i = \frac{\hat{\epsilon}_i^2}{k \times \text{MSE}} \times \frac{h_{ii}}{1-h_{ii}}$ | > $4/n$ ⚠ |
| **DFFITS** | Cambio in previsione con/senza osserv. i | > $2\sqrt{k/n}$ ⚠ |

**Rimedi**: Rimuovere outlier, robust regression, weighted regression

---

## 4. ANOVA (Analysis of Variance)

### 4.1 ANOVA One-Way

**Setup**: Confrontare medie k gruppi indipendenti

**Modello**: $Y_{ij} = \mu + \alpha_i + \epsilon_{ij}$

- $i = 1, ..., k$ gruppi
- $j = 1, ..., n_i$ osservazioni nel gruppo i
- $\mu$ media globale
- $\alpha_i$ effetto gruppo i

**Ipotesi**: $H_0: \alpha_1 = ... = \alpha_k = 0$ (medie gruppi uguali)

#### Tavola ANOVA

| Fonte | SS | df | MS | F |
|-------|----|----|----|----|
| **Tra gruppi** | $SSB = \sum_i n_i (\bar{Y}_i - \bar{Y})^2$ | $k-1$ | $\text{MSB} = SSB/(k-1)$ | $\frac{\text{MSB}}{\text{MSW}}$ |
| **Entro gruppi** | $SSW = \sum_i \sum_j (Y_{ij} - \bar{Y}_i)^2$ | $n-k$ | $\text{MSW} = SSW/(n-k)$ | - |
| **Totale** | $SST = \sum_{ij} (Y_{ij} - \bar{Y})^2$ | $n-1$ | - | - |

**Test**:
$$F = \frac{\text{MSB}}{\text{MSW}} \sim F_{k-1, n-k} \text{ sotto } H_0$$

Rifiuto: $F > F_{k-1, n-k, \alpha}$ oppure p-value $< \alpha$

### 4.2 ANOVA Two-Way

**Setup**: Due fattori (A e B) su variabile Y

**Modello**: $Y_{ijk} = \mu + \alpha_i + \beta_j + (\alpha\beta)_{ij} + \epsilon_{ijk}$

- $\alpha_i$ effetto fattore A
- $\beta_j$ effetto fattore B
- $(\alpha\beta)_{ij}$ effetto interazione

#### Tavola ANOVA Two-Way

| Fonte | SS | df | MS | F |
|-------|----|----|----|----|
| **Fattore A** | $SSA$ | $a-1$ | $MSA$ | $\frac{MSA}{MSE}$ |
| **Fattore B** | $SSB$ | $b-1$ | $MSB$ | $\frac{MSB}{MSE}$ |
| **Interazione A×B** | $SSAB$ | $(a-1)(b-1)$ | $MSAB$ | $\frac{MSAB}{MSE}$ |
| **Errore** | $SSE$ | $ab(r-1)$ | $MSE$ | - |
| **Totale** | $SST$ | $abr-1$ | - | - |

- a = livelli fattore A
- b = livelli fattore B
- r = repliche per combinazione A-B

### 4.3 Confronti Multipli (Post-hoc)

Dopo rifiuto H₀ in ANOVA, verificare quali gruppi differiscono.

#### Tukey HSD (Honestly Significant Difference)

$$\text{HSD} = q_{\alpha}(k, n-k) \times \sqrt{\frac{\text{MSW}}{2} \left(\frac{1}{n_i} + \frac{1}{n_j}\right)}$$

Differenza significativa se $|\bar{Y}_i - \bar{Y}_j| > \text{HSD}$

#### Bonferroni Correction

Aggiusta livello significatività: $\alpha^* = \frac{\alpha}{m}$ dove m = numero confronti

---

## 5. TEST NON PARAMETRICI

### 5.1 Test Wilcoxon (Signed-Rank)

**Setup**: Confrontare mediana campione vs valore ipotizzato (o dati appaiati)

**Ipotesi**: $H_0: \text{mediana} = m_0$ vs $H_1: \text{mediana} \neq m_0$

**Procedura**:
1. Calcola $d_i = X_i - m_0$
2. Rank $|d_i|$: assegna ranks a valori assoluti
3. Somma ranks positivi: $W^+ = \sum \text{rank}(d_i > 0)$
4. Statistica: $T = \min(W^+, W^-)$

**Distribuzione**: Tabulata per piccoli n; per n > 30 approssima a Normale

### 5.2 Test Mann-Whitney-Wilcoxon (U-test)

**Setup**: Confrontare distribuzioni due campioni indipendenti

**Ipotesi**: $H_0$: distribuzioni uguali vs $H_1$: distribuzioni diverse

**Procedura**:
1. Combina campioni, rank tutti valori (1 a n₁+n₂)
2. Somma ranks gruppo 1: $R_1 = \sum_{i \in \text{gruppo 1}} \text{rank}_i$
3. Statistica Mann-Whitney:
$$U = n_1 n_2 + \frac{n_1(n_1+1)}{2} - R_1$$

**Proprietà**: $U \in [0, n_1 n_2]$; rifiuto per U piccolo (code)

### 5.3 Test Kruskal-Wallis

**Setup**: Confrontare k campioni indipendenti (non parametrico ANOVA one-way)

**Ipotesi**: $H_0$: distribuzioni k gruppi uguali

**Statistica**:
$$H = \frac{12}{n(n+1)} \sum_{i=1}^k \frac{R_i^2}{n_i} - 3(n+1)$$

dove $R_i$ = somma ranks gruppo i, $n_i$ = size gruppo i, $n = \sum n_i$

**Distribuzione**: $H \sim \chi^2_{k-1}$ sotto $H_0$ (approssimazione, n > 5)

Rifiuto: $H > \chi^2_{k-1, \alpha}$

### 5.4 Test di Indipendenza Spearman

**Setup**: Associazione monotona tra due variabili continue

**Procedura**:
1. Rank X e Y separatamente: $\text{rank}(X_i)$, $\text{rank}(Y_i)$
2. Calcola correlazione Pearson sui ranks:

$$r_s = 1 - \frac{6 \sum_i (d_i)^2}{n(n^2 - 1)}$$

dove $d_i = \text{rank}(X_i) - \text{rank}(Y_i)$

**Vantaggio**: Non assume linearità, robusto a outlier

---

## 6. FUNZIONI R CHIAVE

```r
# Regressione lineare
lm(y ~ x, data=df)
lm(y ~ x1 + x2 + x3, data=df)

summary(model)           # Stima coefficienti, test, R²
confint(model, level=0.95)  # IC coefficienti

# Diagnostica
plot(model, which=1)     # Residuals vs Fitted
plot(model, which=2)     # Q-Q plot
plot(model, which=3)     # Scale-Location (eteroschedasticità)
plot(model, which=5)     # Residuals vs Leverage

# Test specifici
lmtest::bptest(model)    # Breusch-Pagan
lmtest::dwtest(model)    # Durbin-Watson
car::vif(model)          # VIF multicollinearità

# ANOVA
aov(y ~ group, data=df)
summary(aov_model)
TukeyHSD(aov_model)      # Post-hoc Tukey

# Test non parametrici
wilcox.test(x, mu=m0)    # Wilcoxon signed-rank
wilcox.test(x1, x2)      # Mann-Whitney
kruskal.test(y ~ group, data=df)  # Kruskal-Wallis
cor.test(x, y, method='spearman')  # Spearman
```

---

**Fonte**: Formulari Bocconi (BEMACS, CLEAM, BEMACC)  
**Ultima revisione**: Aprile 2026
