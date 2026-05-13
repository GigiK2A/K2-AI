# Policy Evaluation — Metodi Causali

Riferimento tecnico completo dalla Dispensa Bocconi 2y-2s General (Policy Evaluation).

---

## Framework Causale: Contraffattuale e Selezione

### Il Problema Causale Fondamentale

**Osservazione vs. Contraffattuale:**
- Osserviamo il risultato quando il trattamento è somministrato → Y_i(T_i = 1)
- NON osserviamo il risultato potenziale assente il trattamento → Y_i(T_i = 0) [contraffattuale]
- Identification problem: per ogni unità, osserviamo solo 1 outcome su 2 possibili

**Differenza ingenua (naive difference):**
$$E(Y_i | T_i = 1) - E(Y_i | T_i = 0) = \underbrace{E(Y_i^1 | T_i = 1) - E(Y_i^0 | T_i = 1)}_{\text{ATT}} + \underbrace{E(Y_i^0 | T_i = 1) - E(Y_i^0 | T_i = 0)}_{\text{SELECTION BIAS}}$$

Quando SB < 0: sottostimiamo l'effetto; quando SB > 0: sovrastimiamo.

### Definizioni di Effetto Causale

**Average Treatment Effect (ATE):**
$$ATE = E(Y_i^1 - Y_i^0) = E(Y_i^1) - E(Y_i^0)$$
Effetto medio su tutta la popolazione (trattati + non trattati).

**Average Treatment Effect on the Treated (ATT):**
$$ATT = E(Y_i^1 - Y_i^0 | T_i = 1) = E(Y_i^1 | T_i = 1) - E(Y_i^0 | T_i = 1)$$
Effetto medio sulla sottopopolazione che riceve il trattamento.

**Local Average Treatment Effect (LATE):**
$$LATE = E(Y_i^1 - Y_i^0 | \text{compliers})$$
Effetto causale per gli individui i cui comportamenti sono influenzati da uno strumento (IV). Identificato in presenza di non-compliance.

### Fonti di Correlazione (4 Meccanismi)

1. **Causalità diretta**: A causa B
2. **Causalità inversa**: B causa A (reverse causality)
3. **Variabile omessa**: C causa sia A che B
4. **Caso**: Correlazione spuria

---

## Randomized Controlled Trials (RCT)

### Principio Fondamentale

**Random assignment** bilancia le caratteristiche potenziali (osservate e non) tra trattamento e controllo in expectation:
$$E[Y_i^0 | T_i = 1] = E[Y_i^0 | T_i = 0]$$

Elimina la selezione bias, rendendo la differenza semplice identificatrice di ATE.

### Validità

**Internal validity:** Validità rigorosa della relazione causale all'interno dello studio. RCT ben condotti hanno validità interna molto alta.

**External validity:** Generalizzabilità dei risultati fuori dal contesto dello studio. Limitata quando:
- Campioni non rappresentativi
- Effetti di Hawthorne (comportamento alterato per consapevolezza di being studied)
- John Henry effect (controlli reattivi che contrastano il trattamento)

### Implementazione

- **Design robusto e pre-specificato**
- **Dimensione campionaria** calcolata ex-ante per potenza statistica
- **Matching vs. stratificazione** per balance su caratteristiche baseline
- **Analisi intention-to-treat (ITT)** per mantenere randomizzazione

### Criticità Pratiche

1. **Compliance imperfetta**: non tutti i trattati ricevono il trattamento; non tutti i controlli rimangono untreated
2. **Attrition**: drop-out differenziale tra bracci
3. **Spillover/contamination**: controlli esposti al trattamento indirettamente
4. **Costi elevati** e questioni etiche

---

## Difference-in-Differences (DiD)

### Logica Fondamentale

Confrontiamo la **variazione nel tempo** del gruppo trattato vs. controllo. La variazione nel controllo fornisce il **contraffattuale** per il trattato assente il trattamento.

$$DD = [Y_{T,\text{post}} - Y_{T,\text{pre}}] - [Y_{C,\text{post}} - Y_{C,\text{pre}}]$$

Equivalentemente, regressione con interazione tempo × trattamento:
$$Y_{it} = \beta_0 + \beta_1 T_i + \beta_2 \text{Post}_t + \beta_3 (T_i \times \text{Post}_t) + u_{it}$$

dove $\beta_3 = $ effetto DiD.

### Assunzione Identificante: Parallel Trends

**Assunzione cruciale**: In assenza del trattamento, il gruppo trattato e controllo avrebbero seguito lo stesso trend temporale.

Testabile usando:
- **Placebo test**: Verifichiamo parallel trends nel pre-periodo (almeno 2 periodi pre-trattamento)
- **Event study**: Tracciamo dinamica degli effetti nel tempo, verificando che coefficienti pre-trattamento ≈ 0

### Two-Way Fixed Effects

$$Y_{it} = \beta_1 T_i \times \text{Post}_t + \alpha_i + \gamma_t + u_{it}$$

- $\alpha_i$ = fixed effect individuale (elimina OVB da variabili time-invariant)
- $\gamma_t$ = fixed effect temporale (elimina trend temporali comuni)

### Assunzioni Aggiuntive

1. **No spillover**: Il controllo non è influenzato dal trattamento del gruppo trattato
2. **No change in composition**: Gli individui non si muovono tra gruppi per il trattamento

### Trattamento Staggered (Staggered DiD)

Quando diverse unità ricevono il trattamento in tempi diversi. Event study a horizonte dinamico:
$$Y_{it} = \sum_{\tau = -K}^{L} \beta_{\tau} \mathbb{1}(\text{time to treatment} = \tau) + \alpha_i + \gamma_t + u_{it}$$

Fornisce profilo completo dell'effetto nel tempo.

---

## Instrumental Variables (IV)

### Problema di Base

Correlazione tra regressore endogeno e termine d'errore dovuta a:
- Omitted variable bias
- Simultaneità (reverse causality)
- Errore di misurazione

OLS produce stime distorte e inconsistenti.

### Condizioni di Validità di uno Strumento Z

1. **Random assignment**: Z è esogenamente assegnato
2. **First stage**: Z influenza il trattamento T (testabile)
3. **Exclusion restriction**: Z influenza Y solo attraverso T (non testabile direttamente)

Formalmente, strumento Z è valido se:
$$\text{Cov}(Z, Y) \neq 0 \text{ ma} \text{Cov}(Z, u) = 0$$

### Wald Estimator

Forma più semplice di IV (uno strumento, una variabile endogena):
$$\hat{\beta}_{IV} = \frac{\text{Reduced form}}{\text{First stage}} = \frac{\Delta Y}{\Delta T} = \frac{E(Y | Z = 1) - E(Y | Z = 0)}{E(T | Z = 1) - E(T | Z = 0)}$$

Stima l'effetto medio della variazione di T indotta da Z.

### Two-Stage Least Squares (2SLS)

**First stage:**
$$T_i = \alpha_0 + \alpha Z_i + v_i$$
Stimiamo $\hat{T}_i = \hat{\alpha}_0 + \hat{\alpha} Z_i$

**Second stage:**
$$Y_i = \beta_0 + \beta \hat{T}_i + e_i$$

L'uso di $\hat{T}_i$ (che è correlato con Z per ipotesi) elimina l'endogeneità di T.

Con **multipli strumenti** o **controlli aggiuntivi**, il modello diventa:
- FS: $T_i = \alpha_0 + \alpha_Z Z_i + \alpha_W W_i + v_i$
- RF: $Y_i = \gamma_0 + \gamma_Z Z_i + \gamma_W W_i + u_i$
- 2SLS: $Y_i = \beta_0 + \beta \hat{T}_i + \beta_W W_i + e_i$

### Local Average Treatment Effect (LATE)

IV identifica il LATE: l'effetto per gli individui i cui comportamenti sono influenzati dallo strumento (compliers).

$$LATE = \frac{E(Y | Z = 1) - E(Y | Z = 0)}{E(T | Z = 1) - E(T | Z = 0)}$$

Non identifica ATE, a meno che l'effetto sia omogeneo.

### Weak Instruments

Se lo strumento ha bassa correlazione con T (weak first stage), gli estimatori IV:
- Sono distorto verso OLS anche in grandi campioni
- Hanno varianza elevata
- Test e IC sono inaffidabili

**Diagnostica**: Verifichiamo F-statistica della first stage. Regola empirica: F > 10.

---

## Regression Discontinuity (RD)

### Idea Fondamentale

Un'assegnazione di trattamento basata su una regola deterministica di una variabile di soglia (running variable) crea un **esperimento naturale**: individui poco sopra/sotto il cutoff sono simili in tutto tranne il trattamento.

$$T_i = \begin{cases} 1 & \text{se } x_i \geq x_0 \\ 0 & \text{se } x_i < x_0 \end{cases}$$

### Sharp RD

Il trattamento è una **funzione deterministica** del cutoff:
$$Y_i = \alpha + \beta x_i + \gamma T_i + \delta (x_i - x_0) \mathbb{1}(x_i \geq x_0) + u_i$$

**Assunzioni di identificazione:**
1. $f(x)$ (la funzione baseline) è smooth al cutoff
2. Nessuna manipolazione del running variable al cutoff (testabile con McCrary test)

Lo stimatore cattura il **local effect** al cutoff: $\gamma = \lim_{x \to x_0^+} E(Y | x) - \lim_{x \to x_0^-} E(Y | x)$

### Fuzzy RD

Il trattamento è una **funzione probabilistica** della soglia:
$$\text{Pr}(T_i = 1 | x_i) \text{ presenta un salto al cutoff}$$

Questa è una IV naturale:
- Z = indicatore cutoff (Z = 1 se $x_i \geq x_0$)
- T = effettivo trattamento ricevuto
- LATE stimato via 2SLS

### Scelta della Bandwidth

Bandwidth atto: equilibrio tra bias (funzionale form) e varianza (pochi obs vicino cutoff).

- **Troppo larga**: bias da curvatura della funzione
- **Troppo stretta**: pochi obs, varianza alta

Metodi: leave-one-out cross-validation, optimal bandwidth (Imbens-Kalyanaraman).

### McCrary Test

Verifica se la **densità del running variable è continua al cutoff**. Se discontinuità nella densità → possibile manipolazione del cutoff, viola assunzioni RD.

---

## Propensity Score Matching (PSM)

### Idea

Se condizioniamo sulla **propensity score** $p(X_i) = \text{Pr}(T_i = 1 | X_i)$ (probabilità di trattamento dato X), il trattamento diventa "as good as randomly assigned" condizionatamente:

$$(Y_i^0, Y_i^1) \perp T_i | p(X_i)$$

Questo riduce dimensionalità: invece di matchare su tutti gli X, matchiamo su uno scalar.

### Procedure

1. **Stima della propensity score**: Regressione logit/probit di $T_i$ su X
2. **Imposizione della common support**: Rimuoviamo unità che hanno $p(X_i) < \min(p | T=1)$ o $p(X_i) > \max(p | T=0)$
3. **Matching**: Per ogni trattato, troviamo un (o più) controlli con propensity score simile

### Algoritmi di Matching

- **Nearest neighbor**: Seleziona il controllo con propensity score più vicino
- **Caliper matching**: Seleziona controlli entro una tolleranza prestabilita
- **Stratification**: Divide il supporto della propensity score in strati, confronta trattati e controlli entro strato
- **Kernel matching**: Media ponderata di tutti i controlli, con pesi inversamente proporzionali alla distanza

### Criticità

1. **Common support imperfetto**: Rimane selezione bias per caratteristiche non osservate
2. **Sensibilità alla specificazione** della propensity score
3. **Perdita di osservazioni** fuori dal common support
4. Meno affidabile di RCT o quasi-sperimenti (DiD, RD)

---

## Synthetic Control Method

### Logica

Costruiamo un **controllo sintetico ponderato** dai controlli disponibili per replicare il pre-trend dell'unità trattata, poi osserviamo la divergenza post-trattamento.

Utile quando **una sola unità riceve il trattamento** (o poche unità), e i controlli sono molteplici.

### Formulazione

Sia $j = 1, \ldots, J$ le unità di controllo potenziali. Cerchiamo pesi $w_j \geq 0$, $\sum w_j = 1$ che minimizzino:
$$\sum_t (Y_{1t} - \sum_{j=2}^{J+1} w_j Y_{jt})^2$$
nel pre-periodo.

Il controllo sintetico è: $\hat{Y}_{1,\text{synthetic}} = \sum_{j=2}^{J+1} w_j^* Y_{jt}$

L'effetto è: $\tau_t = Y_{1t} - \hat{Y}_{1,\text{synthetic},t}$ nel post-periodo.

### Inference: Placebo Tests

In assenza di distribuzione nota, usiamo **placebo test**: applichiamo iterativamente il metodo ai controlli (come se fossero trattati), ottenendo la distribuzione nulla degli effetti pseudo-trattativi.

Se l'effetto vero è maggiore della distribuzione placebo, concludiamo causalità.

---

## Diagnostica, Robustness e Sensitivity

### Placebo Test

Regrediamo il trattamento su **outcome nel pre-periodo** (prima del trattamento stesso). Coefficiente dovrebbe essere vicino a 0.

Per DiD con staggered treatment, ogni lag pre-trattamento dovrebbe avere effetto ≈ 0.

### Sensitivity Analysis

Valutiamo robustezza a:
- **Specificazione funzionale**: Aggiungiamo polinomi, trasformazioni del running variable (in RD)
- **Sottocampioni**: Escludiamo osservazioni ai margini
- **Variabili di controllo alternative**: Includiamo/escludiamo covariate

Se risultati robusti, confidenza aumenta.

### Standard Error Clustering

Quando osservazioni sono correlate (es. studenti nella stessa scuola, individui nello stesso comune), la formula standard di SE sottostima la vera varianza.

**Soluzioni:**
- Clustered SE: regress with `cluster(cluster_var)`
- Due-way clustering: se nesting multi-livello
- Block bootstrap se clusters molto pochi

### Esternalità di Policy (Spillover Effects)

Quando il controllo è esposto indirettamente al trattamento:
- Stima dell'effetto è **attenuata** (contaffattuale contaminato)
- Estimatore fornisce **effetto netto** (trattato vs. controllo contaminato), non effetto puro

Soluzioni:
- Aumentare distanza geografica/sociale tra trattati e controlli
- Modelizzare spillover strutturalmente
- Usare **treatment saturation design** (varia il grado di esposizione)

### Eterogeneità negli Effetti

Effetti di trattamento variano per sottogruppi. Stimiamo:
- **Interazioni**: $Y_i = \beta T_i + \beta_{\text{het}} T_i \times X_i + ...$
- **Subgroup analysis**: Dividiamo il campione e stimiamo effetti separatamente
- **Machine learning**: Conditional average treatment effects (CATE) usando random forests, lasso

---

## Tavola Sinottica dei Metodi

| Metodo | Assunzione Chiave | Quando Usare | Validità |
|--------|------------------|-------------|---------|
| **RCT** | Random assignment | Possibile randomizzare | Massima |
| **DiD** | Parallel trends | Shock esogeno su alcuni gruppi | Alta se trends verificati |
| **RD** | Continuità al cutoff | Soglia amministrativa del trattamento | Alta (local, non externa) |
| **IV** | Exclusion restriction | Strumento esogeno disponibile | Media (sensibile weak instruments) |
| **PSM** | Unconfoundedness | Osservate tutte le variabili di confondimento | Bassa (selezione su non osservate) |
| **Synthetic Control** | No anticipation | Poche unità trattate, molti controlli | Media-alta |

---

## Terminologia Tecnica (Inglese-Italiano)

- **Causal inference**: Inferenza causale
- **Counterfactual**: Contraffattuale (scenario assente trattamento)
- **Selection bias**: Selezione bias (confondimento da selezione nel trattamento)
- **Endogeneity**: Endogeneità (correlazione regressore-errore)
- **Omitted variable bias (OVB)**: Bias da variabile omessa
- **First stage, reduced form, IV estimator**: Primo stadio, forma ridotta, stimatore IV
- **Fuzzy assignment**: Assegnazione fuzzy (probabilistica vs. deterministica)
- **Common support**: Supporto comune (overlap nella propensity score)
- **Compliance**: Compliance (aderenza al trattamento assegnato)
- **Spillover / Contamination**: Spillover/contaminazione (effetto del trattamento sui controlli)
- **External validity**: Validità esterna (generalizzabilità)
- **Internal validity**: Validità interna (causalità rigorosa nel campione)

---

## Riferimenti Applicativi (Italia/UE)

- **PNRR**: Progetti finanziati da programmi Next Generation EU richiedono valutazione ex-post. Metodi quasi-sperimentali (DiD, RD, PSM) frequentemente impiegati.
- **Politiche pubbliche UE**: ESC (European Structural Funds), programmi Erasmus+, politiche ambientali. Spesso DiD con country-time variation per sfruttare variabilità normativa.
- **Politiche occupazionali**: Training programs, sussidi all'impiego. RCT frequente per le valutazioni; IV (lotterie, cutoff amministrativi) quando RCT infeasible.
- **Valutazione investimenti pubblici**: ACB integrata con tecniche quasi-sperimentali per correggere distorsioni nella selezione dei progetti.

---

**Ultima revisione**: Dispensa ASTRA Bocconi 2y-2s (Policy Evaluation) — 13 pagine, 2025.
