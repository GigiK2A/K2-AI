---
name: machine-learning
description: >
  Machine Learning teoria e pratica. Loss functions, ottimizzazione (gradient descent, SGD,
  momentum), OLS, maximum likelihood, regressione polinomiale, bias-variance tradeoff,
  regolarizzazione (Ridge L2, Lasso L1), cross-validation, classificazione (logistic
  regression, GLM), KNN, decision trees (Gini, entropia), SVM (hard/soft margin, hinge
  loss, kernel trick), Gaussian processes, ensemble (bagging, random forest, AdaBoost,
  gradient boosting), neural networks (backpropagation, ReLU, softmax, dropout), CNN
  (convolution, pooling, stride), unsupervised (K-means, GMM, EM, PCA). Basato su corso
  Bocconi BEMACS. Usa SEMPRE per: machine learning, modello predittivo, classificazione,
  regressione, overfitting, regolarizzazione, cross-validation, alberi decisione, random
  forest, boosting, reti neurali, CNN, clustering, PCA, SVM, kernel, bias variance.
  Attiva per "modello ML", "quale algoritmo usare", "overfitting", "classificare",
  "clustering", "rete neurale", "random forest", "gradient boosting".
---

# Machine Learning — Teoria e Pratica

Guida completa al Machine Learning: dai fondamenti matematici (loss functions, ottimizzazione) agli algoritmi supervisionati e non supervisionati, con enfasi su scelta del modello, regolarizzazione e valutazione. Framework operativo per data scientist, analisti e sviluppatori AI.

---

## 1. Fondamenti del Machine Learning

### 1.1 Tipi di Apprendimento
- **Supervised Learning**: dato un dataset etichettato D = {(x, t)}, trovare un'approssimazione della funzione f che generalizzi bene su dati nuovi. Richiede: loss function L, spazio delle ipotesi H, metodo di ottimizzazione.
- **Unsupervised Learning**: apprendere una rappresentazione più efficiente dei dati senza etichette.

### 1.2 Loss Functions
- **MSE (Mean Squared Error)**: MSE = (1/n) Σ(yᵢ - f̂(Xᵢ))² — per regressione
- **Categorical Log Loss**: L = -Σ yᵢ log(pᵢ) — per classificazione
- **Hinge Loss**: φ(y, w^Tx) = max(0, 1 - y·w^Tx) — per SVM

### 1.3 Bias-Variance Tradeoff
**MSE_Test = Bias² + Varianza + Errore Irriducibile (σ²)**

- **Underfitting** (alta bias, bassa varianza): modello troppo semplice, scarsa performance su training
- **Overfitting** (bassa bias, alta varianza): modello troppo complesso, cattiva generalizzazione
- **Complessità alta** → bias bassa, varianza alta
- **Complessità bassa** → bias alta, varianza bassa

---

## 2. Ottimizzazione

### 2.1 Gradient Descent
**Update rule**: x_t = x_{t-1} - η · ∇f(x_{t-1})

- **Learning rate η**: troppo grande → diverge; troppo piccolo → lento
- **Momentum**: x_t = x_{t-1} - η · ∇f(x_{t-1}) + α · Δx_{t-1}, con α ∈ [0,1]
- **Condition number** κ = max σ(A) / min σ(A): influenza la velocità di convergenza

### 2.2 Stochastic Gradient Descent (SGD)
Per dataset grandi, approssima il gradiente usando un sottoinsieme casuale dei dati. Più veloce per iterazione, convergenza più rumorosa ma spesso sufficiente.

### 2.3 Ottimizzazione Vincolata
- **Lagrangiana**: L(x, λ) = f(x) + Σ λᵢ g(x)
- **Problema duale**: utile per SVM e kernel methods

---

## 3. Regressione Lineare e Regolarizzazione

### 3.1 OLS (Ordinary Least Squares)
- **Modello**: y = Xβ + ε
- **Loss**: L(β) = (1/n) ||Xβ - y||²
- **Soluzione analitica (equazione normale)**: β̂ = (X^T X)^{-1} X^T y

### 3.2 Maximum Likelihood Estimation
Sotto assunzione di normalità degli errori: massimizzare p(y|X; β) = N(y; Xβ, σ²I) equivale a minimizzare MSE.

### 3.3 Regressione Polinomiale
y = θ₀ + θ₁x + θ₂x² + ... + θ_dx^d + ε — aumenta flessibilità ma rischio di overfitting.

### 3.4 Ridge Regression (L2)
β̂ = arg min (1/n)||Xβ - y||² + λ||β||₂²

- Riduce i coefficienti verso zero, **mai esattamente a zero**
- Interpretazione bayesiana: prior gaussiano N(0, σ²) sui coefficienti
- Contorno penalità: sferico nello spazio dei parametri

### 3.5 Lasso Regression (L1)
β̂ = arg min (1/n)||Xβ - y||² + λ||β||₁

- Può portare coefficienti **esattamente a zero** → selezione variabili (modelli sparsi)
- Interpretazione bayesiana: prior di Laplace sui coefficienti
- Contorno penalità: diamante → favorisce soluzioni sparse

### 3.6 Cross-Validation
- **Validation Set**: split casuale train/validation (instabile, potenziale bias)
- **Leave-One-Out CV (LOOCV)**: LOOCV = (1/n) Σ MSEᵢ — allena n modelli, costoso
- **k-Fold CV**: Error = (1/k) Σ MSEᵢ — bilancia efficienza e riduzione del bias (tipicamente k=5 o k=10)

---

## 4. Classificazione

### 4.1 Regressione Logistica
- **Funzione logistica**: p(X) = e^(β^T X) / (1 + e^(β^T X))
- **Logit (log-odds)**: log(p/(1-p)) = β^T X — lineare in X
- **Stima parametri**: Maximum Likelihood — L(β) = Π [p(Xᵢ)]^yᵢ · [1-p(Xᵢ)]^(1-yᵢ)

### 4.2 Regressione Logistica Multinomiale
- **Probabilità per classe k**: p(Y=k|X) = e^(β_k^T X) / Σ_j e^(β_j^T X) (softmax)
- Likelihood congiunta per tutte le categorie di risposta

### 4.3 Generalized Linear Models (GLMs)
Estendono la regressione lineare a variabili risposta non continue:
- **Componente random**: distribuzione della famiglia esponenziale (Gaussiana, Binomiale, Poisson)
- **Componente sistematica**: predittore lineare z = β₀ + β₁X₁ + ... + βₚXₚ
- **Funzione link**: collega E[y|X;θ] = φ⁻¹(z)
- La regressione logistica è un GLM con risposta Binomiale e link logit

---

## 5. Metodi Non Parametrici

### 5.1 K-Nearest Neighbours (KNN)
1. Calcolo distanze: distanza euclidea ||Xᵢ - Xⱼ||₂
2. Selezione dei k vicini più prossimi
3. Aggregazione: media (regressione) o moda (classificazione)

**Iperparametro k**: k piccolo → sensibile al rumore; k grande → smoother ma meno accurato. Ottimizzare con cross-validation. **Normalizzazione essenziale** (Min-Max scaling).

### 5.2 Decision Trees (Alberi Decisionali)
**Alberi di regressione**: funzione costante a tratti — f̂(X) = Σ f̂_ℓ · 1_{R_ℓ}(X)
**Alberi di classificazione**: predizione = moda della classe nella foglia

**Criteri di split**:
- **Misclassification Rate**: 1 - max(p_k) — semplice ma poco sensibile
- **Gini Index**: 1 - Σ p_k² — misura impurità del nodo
- **Entropia**: -Σ p_k log₂(p_k) — zero = nodo puro, seleziona la massima riduzione di entropia

---

## 6. Support Vector Machines (SVM)

### 6.1 Maximal Margin Classifier (Hard Margin)
- **Iperpiano**: w^T x = 0
- **Obiettivo**: max M soggetto a yᵢ(w^T Xᵢ) ≥ M, ||w|| = 1
- **Forma equivalente**: min (1/2)||w||² soggetto a yᵢ(w^T Xᵢ) ≥ 1

### 6.2 Support Vector Classifier (Soft Margin)
Introduce variabili slack ξᵢ per consentire alcune classificazioni errate:
- min (λ/2)||w||² + (1/n) Σ ξᵢ, soggetto a yᵢ(w^T Xᵢ) ≥ 1 - ξᵢ, ξᵢ ≥ 0

**Formulazione con Hinge Loss**: min (1/n) Σ max(0, 1 - yᵢ·w^T Xᵢ) + (λ/2)||w||²

**Tipi di support vector**:
- αᵢ = 0: non-support vector
- αᵢ ∈ (0,1): essential support vector (dal lato giusto del margine)
- αᵢ = 1: bound support vector (lato sbagliato o dentro il margine)

### 6.3 Kernel Trick
**Kernel function**: k(x, x') = φ(x)^T φ(x') — calcola prodotti interni nello spazio delle feature senza calcolare esplicitamente φ.

- **Kernel Matrix K**: K_ij = k(xᵢ, xⱼ)
- **Teorema di Mercer**: kernel valido ↔ matrice di Gram K simmetrica e semidefinita positiva
- **Representer Theorem**: f̂(x) = Σᵢ αᵢ k(xᵢ, x) — la soluzione è combinazione lineare dei kernel

**Kernel Ridge Regression**: f̂(X*) = y^T (K + nλI)^{-1} k(X*)

---

## 7. Gaussian Processes

- **Definizione**: f ~ GP(μ, κ) con media μ(x) e covarianza κ(x, x')
- **Distribuzione predittiva** per punto nuovo X*:
  - μ_pred(X*) = μ(X*) + κ(X*, X) κ(X, X)^{-1} (f(X) - μ(X))
  - σ²_pred(X*) = κ(X*, X*) - κ(X*, X) κ(X, X)^{-1} κ(X, X*)
- Forniscono stime di incertezza naturali (intervalli di confidenza predittivi)

---

## 8. Metodi Ensemble

### 8.1 Bagging (Bootstrap Aggregating)
1. Creare B campioni bootstrap dal training set
2. Allenare un modello su ciascuno
3. Aggregare: media (regressione) o voto di maggioranza (classificazione)

**Riduzione della varianza**: σ²_bagged = ((1-ρ)/B)σ² + ρσ², dove ρ = correlazione tra modelli. L'efficacia dipende dalla riduzione di ρ.

### 8.2 Random Forest
Estensione del bagging: ad ogni split, consideri solo q ≤ p variabili casuali come candidati. Riduce la correlazione tra alberi → migliore riduzione della varianza.

### 8.3 AdaBoost (Adaptive Boosting)
Allenamento sequenziale di weak learner con pesi adattivi:
1. Inizializza: D(i) = 1/n per ogni campione
2. Per t = 1,...,T:
   - Allena weak learner h_t con pesi D_t
   - Calcola errore pesato: e_t = Σ D_t(i) · 1(yᵢ ≠ h_t(x))
   - Calcola peso del learner: α_t = (1/2) log((1-e_t)/e_t)
   - Aggiorna pesi: D_{t+1}(i) = D_t(i) · exp(-α_t · yᵢ · h_t(xᵢ)) / Z_t
3. Predizione finale: H(x) = sign(Σ α_t · h_t(x))

### 8.4 Gradient Boosting
Allena modelli successivi sui **residui** dell'iterazione precedente:
1. Per t = 1,...,T:
   - Calcola residui: r_ti = -∂L(yᵢ, F(xᵢ))/∂F(xᵢ)
   - Allena learner sui residui: h_t(x) → r_t
   - Ottimizza step: γ_t = arg min Σ L(yᵢ, F_{t-1}(xᵢ) + γ · h_t(xᵢ))
   - Aggiorna: F_t(x) = F_{t-1}(x) + γ_t · h_t(x)

---

## 9. Neural Networks

### 9.1 Architettura Base
- **Singolo layer**: f̂(x) = h(W^T x + b), dove h è la funzione di attivazione
- **Multi-layer**: q^(l) = h(W^(l) · q^(l-1) + b^(l))

**Funzioni di attivazione**:
- **Logistic (Sigmoid)**: h(x) = 1/(1+e^{-x}) — output in (0,1)
- **ReLU**: h(x) = max(0, x) — efficiente, evita vanishing gradient
- **Softmax** (output layer classificazione): h(x)ᵢ = e^{xᵢ} / Σ_j e^{x_j}

### 9.2 Backpropagation
Algoritmo per calcolare i gradienti della loss rispetto ai pesi di ogni layer, propagando l'errore dall'output all'input.
- **Ottimizzazione**: θ* = arg min J(θ) = arg min (1/n) Σ L(xᵢ, yᵢ, θ)
- **Cost functions**: MSE (regressione), Cross-entropy (classificazione multiclasse)

### 9.3 Convolutional Neural Networks (CNN)
**Operazione di convoluzione**: q_ij = h(ΣΣ x_{i+k-1, j+l-1} · W_{kl})
- **Sparse interactions**: ogni neurone dipende solo da una piccola regione dell'input
- **Parameter sharing**: lo stesso filtro W è usato su tutta l'immagine

**Strided convolution**: salto di s pixel per ridurre le dimensioni spaziali
**Pooling**: average pooling o max pooling per ridurre dimensionalità e creare invarianza

### 9.4 Dropout (Regolarizzazione)
- Durante il training: maschera casuale m con probabilità r di essere attivo
- q̃^(l-1) = m^(l-1) ⊙ q^(l-1)
- Durante il test: tutti i neuroni attivi
- Previene la co-adattazione dei neuroni, agisce come regolarizzazione implicita

---

## 10. Apprendimento Non Supervisionato

### 10.1 K-Means Clustering
**Obiettivo**: min Σ_{ℓ=1}^K (1/|R_ℓ|) Σ_{x∈R_ℓ} ||x - μ_ℓ||²

Algoritmo iterativo:
1. Inizializzazione casuale dei centroidi
2. Assegnazione di ogni punto al centroide più vicino
3. Ricalcolo dei centroidi: μ_ℓ = media dei punti assegnati al cluster ℓ
4. Ripetere fino a convergenza

**Non convesso** → converge a minimi locali. Usare il **metodo del gomito** (elbow) per scegliere k. **Normalizzazione essenziale**.

### 10.2 Gaussian Mixture Model (GMM)
Soft clustering: ogni punto ha una probabilità di appartenere a ciascun cluster.
- f(x) = Σ_{j=1}^M π(j) · N(x | μ_j, Σ_j)
- Responsabilità: w_i(j) = π(j)N(x|μ_j,Σ_j) / Σ_v π(v)N(x|μ_v,Σ_v)

### 10.3 Expectation-Maximization (EM)
1. **E-Step**: calcola le responsabilità w_i(j) con i parametri correnti
2. **M-Step**: aggiorna i parametri massimizzando la verosimiglianza attesa
   - π(j) = (1/N) Σ w_i(j)
   - μ_j = Σ w_i(j)xᵢ / Σ w_i(j)
   - Σ_j = Σ w_i(j)(xᵢ-μ_j)(xᵢ-μ_j)^T / Σ w_i(j)
3. Ripetere fino a convergenza

### 10.4 PCA (Principal Component Analysis)
Riduzione della dimensionalità da d a k (k < d):
- Trova le direzioni di massima varianza nei dati
- Base ortonormale {u_j}_{j=1}^k che approssima i dati d-dimensionali
- Utile come preprocessing e per visualizzazione

---

## 11. Guida alla Scelta dell'Algoritmo

### Problemi di Regressione
| Situazione | Algoritmo consigliato |
|---|---|
| Relazione lineare, pochi predittori | OLS |
| Molti predittori, rischio overfitting | Ridge/Lasso |
| Relazione non lineare | Random Forest, Gradient Boosting |
| Dati molto grandi, relazioni complesse | Neural Network |
| Serve incertezza sulla predizione | Gaussian Process |

### Problemi di Classificazione
| Situazione | Algoritmo consigliato |
|---|---|
| Classificazione binaria, interpretabilità | Logistic Regression |
| Boundary non lineare, pochi dati | SVM con kernel |
| Molte feature, interpretabilità | Decision Tree |
| Massima accuratezza, dati tabulari | Gradient Boosting (XGBoost) |
| Immagini, dati sequenziali | CNN, Neural Network |

### Problemi di Clustering
| Situazione | Algoritmo consigliato |
|---|---|
| Cluster sferici, k noto | K-Means |
| Cluster ellittici, soft assignment | GMM + EM |
| Riduzione dimensionalità | PCA |
