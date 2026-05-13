# Modelli di Regressione e Segmentazione Quantitativa

## 1. Fondamenti di Model Building

### 1.1 Regressione Lineare per il Marketing
La regressione è lo strumento base per quantificare le relazioni tra variabili di marketing:

**Y = β₀ + β₁X₁ + β₂X₂ + ... + βₖXₖ + ε**

Dove:
- **Y** = variabile dipendente (vendite, quota di mercato, awareness)
- **Xᵢ** = variabili indipendenti (prezzo, investimento adv, distribuzione)
- **βᵢ** = coefficienti (effetto marginale di Xᵢ su Y)
- **ε** = errore casuale

**Interpretazione dei coefficienti**:
- β₁ = variazione di Y per un incremento unitario di X₁, a parità di tutte le altre variabili
- Segno: positivo → relazione diretta; negativo → relazione inversa
- Significatività: p-value < 0.05 → l'effetto è statisticamente significativo

**Metriche di bontà del modello**:
- **R²**: quota di varianza di Y spiegata dal modello (0-1, più alto = migliore)
- **R² adjusted**: corretto per il numero di variabili (preferito quando si confrontano modelli)
- **F-test**: significatività complessiva del modello
- **RMSE**: errore medio di previsione (in unità di Y)

### 1.2 Dummy Variables (Variabili Indicatrici)
Per includere variabili qualitative (categoriche) nel modello di regressione:

**Regola**: k categorie → k-1 dummy variables

Esempio: stagionalità (4 trimestri → 3 dummy):
- D₁ = 1 se Q1, 0 altrimenti
- D₂ = 1 se Q2, 0 altrimenti
- D₃ = 1 se Q3, 0 altrimenti
- Q4 = categoria di riferimento (quando tutte le dummy = 0)

**Interpretazione**: βᵈ = differenza media di Y rispetto alla categoria di riferimento.

### 1.3 Interazioni tra Variabili
Per catturare effetti sinergici o antagonisti:

**Y = β₀ + β₁X₁ + β₂X₂ + β₃(X₁ × X₂) + ε**

- β₃ > 0 → sinergia (l'effetto combinato è maggiore della somma)
- β₃ < 0 → antagonismo (l'effetto combinato è minore della somma)

Esempio: interazione prezzo × promozione — una promozione può amplificare l'effetto di un taglio prezzo.

### 1.4 Effetti Non Lineari
Trasformazioni comuni nel marketing:
- **Log-lineare**: ln(Y) = β₀ + β₁X → β₁ = elasticità (variazione % di Y per unità di X)
- **Log-log**: ln(Y) = β₀ + β₁ln(X) → β₁ = elasticità costante
- **Quadratica**: Y = β₀ + β₁X + β₂X² → rendimenti decrescenti (β₂ < 0) o crescenti (β₂ > 0)

**Elasticità della domanda al prezzo**: tipicamente tra -1 e -3 per beni di largo consumo.

---

## 2. Segmentazione Quantitativa

### 2.1 Cluster Analysis
Tecnica statistica per identificare segmenti naturali nei dati:

**Processo**:
1. Selezionare le variabili di segmentazione (comportamentali, psicografiche, di valore)
2. Standardizzare le variabili (z-score)
3. Applicare l'algoritmo di clustering (k-means, hierarchical)
4. Determinare il numero ottimale di cluster (elbow method, silhouette)
5. Profilare e interpretare i segmenti
6. Validare la stabilità dei segmenti

**K-Means**: minimizza la varianza intra-cluster. Iterativamente assegna ogni osservazione al centroide più vicino e ricalcola i centroidi.

### 2.2 RFM Analysis (Recency, Frequency, Monetary)
Segmentazione dei clienti basata su tre dimensioni comportamentali:

- **Recency** (R): quanto tempo fa l'ultimo acquisto (più recente → migliore)
- **Frequency** (F): quante volte ha acquistato nel periodo (più frequente → migliore)
- **Monetary** (M): quanto ha speso in totale (più alto → migliore)

**Scoring**: assegnare un punteggio 1-5 a ciascuna dimensione → 125 celle possibili.

**Segmenti tipici RFM**:
| Segmento | R | F | M | Azione |
|----------|---|---|---|--------|
| Champions | 5 | 5 | 5 | Premiare, programmi VIP |
| Loyal | 3-4 | 4-5 | 4-5 | Upsell, cross-sell |
| At Risk | 1-2 | 3-4 | 3-4 | Campagne di retention |
| Lost | 1 | 1-2 | 1-2 | Win-back o lasciare |
| New Customers | 5 | 1 | 1-2 | Nurturing, onboarding |

---

## 3. AI-Driven Customer Segmentation (Pradeep/Appel/Sthanunathan)

### 3.1 Processo di Segmentazione AI-Driven (5 Step)
1. **Data Collection & PCA**: raccolta di 7 tipologie di dati (behavioral, contextual, demographic, geographic, psychographic, lifestyle/cultural, social); riduzione dimensionale via Principal Component Analysis
2. **Clustering avanzato**: applicazione K-means o hierarchical su componenti principali; determinazione ottimale cluster
3. **Metaphor-Based Segmentation**: assegnazione di metafore evocative a ciascun segmento (es. "Explorer", "Guardian") per facilitare comprensione e comunicazione interna — va oltre le etichette demografiche
4. **Facet-Based Segmentation**: per ciascun segmento, identificazione di "sfaccettature" (facets) multiple — motivazionali, comportamentali, attitudinali — che danno profondità al profilo
5. **Segment Fusion**: fusione di output da diverse fonti analitiche (survey, behavioral data, social data) in un profilo unificato per segmento; collegamento a offerte specifiche (segment-specific offerings)

### 3.2 Le 7 Tipologie di Dati per Segmentazione
| Tipologia | Descrizione | Esempio |
|-----------|-------------|---------|
| Behavioral | Azioni di acquisto, usage, navigazione | Frequenza acquisto, basket size, click patterns |
| Contextual | Contesto situazionale dell'interazione | Momento della giornata, device, location al momento dell'acquisto |
| Demographic | Caratteristiche socio-demografiche | Età, genere, reddito, istruzione |
| Geographic | Localizzazione e caratteristiche territoriali | Regione, densità urbana, clima |
| Psychographic | Valori, atteggiamenti, opinioni | Stili di vita, orientamento al rischio, valori |
| Lifestyle/Cultural | Stili di vita e preferenze culturali | Interessi, hobby, consumi culturali |
| Social | Reti sociali e influenza | Social network connections, influencer following, community membership |

### 3.3 Criteri di Validità dei Segmenti AI
5 criteri di validità specifici per segmentazione AI-driven:

1. **Stabilità temporale**: i segmenti devono persistere nel tempo (test-retest)
2. **Actionability**: ogni segmento deve suggerire azioni marketing distinte
3. **Discriminazione**: i segmenti devono essere sufficientemente diversi tra loro (inter-cluster distance)
4. **Coerenza interna**: le unità all'interno dello stesso segmento devono essere simili (intra-cluster variance bassa)
5. **Prevedibilità**: il segmento deve predire comportamenti futuri (churn, upsell, response to promotion)

### 3.4 Personality Extraction via Five-Factor Model (Big Five)
L'AI consente di estrarre il profilo di personalità del consumatore dai dati comportamentali (testo, social, navigazione) usando il modello Five-Factor (OCEAN):

- **Openness** (Apertura): curiosità, creatività, ricerca di novità
- **Conscientiousness** (Coscienziosità): disciplina, organizzazione, affidabilità
- **Extraversion** (Estroversione): socievolezza, assertività, energia
- **Agreeableness** (Amicalità): cooperatività, fiducia, altruismo
- **Neuroticism** (Nevroticismo): instabilità emotiva, ansia, vulnerabilità

**Applicazioni marketing**: personalizzazione del tono comunicativo, matching consumatore-brand personality, predizione di preferenze di prodotto, segmentazione psicografica scalabile (vs. survey tradizionali limitate dalla dimensione campione).

### 3.5 Inverse Hierarchy of Needs
Modello alternativo alla piramide di Maslow per segmentazione: le preferenze di consumo seguono una gerarchia inversa dove i bisogni di auto-espressione e appartenenza (top Maslow) possono guidare le scelte prima dei bisogni funzionali. Applicazione: i segmenti possono essere definiti dal livello della gerarchia a cui il consumatore opera per una data categoria di prodotto.

---

## 4. Fondamenti Matematici per Segmentazione Marketing (Pradeep/Appel/Sthanunathan, Cap 3-5)

Concetti fondamentali di AI/ML applicati alla segmentazione e all'analisi di mercato, dal libro "AI for Marketing and Product Innovation" (Wiley 2019).

### 4.1 Metriche di Distanza per Segmentazione Clienti
La scelta della metrica di distanza influenza direttamente la forma dei segmenti identificati:

**Distanza Euclidea** (la più comune):
- d(A,B) = √(Σᵢ (aᵢ - bᵢ)²)
- Misura la distanza "in linea d'aria" nello spazio multidimensionale
- **Uso marketing**: segmentazione basata su variabili continue standardizzate (spesa, frequenza, recency)
- **Limite**: sensibile a scale diverse → richiede standardizzazione (z-score) prima dell'uso

**Distanza Taxicab (Manhattan)**:
- d(A,B) = Σᵢ |aᵢ - bᵢ|
- Somma delle distanze assolute lungo ogni asse
- **Uso marketing**: utile quando le dimensioni di segmentazione sono indipendenti e non compensabili (es. un cliente non "compensa" bassa frequenza con alta spesa — sono dimensioni distinte)

**Distanza Max (Chebyshev)**:
- d(A,B) = maxᵢ |aᵢ - bᵢ|
- Distanza determinata dalla dimensione con maggiore differenza
- **Uso marketing**: identificare clienti che deviano fortemente anche su una sola dimensione (outlier detection, identificazione di clienti "estremi" su un singolo KPI)

**Implicazione pratica**: la scelta della metrica non è tecnica ma strategica — definisce cosa significa "similarità" tra clienti nel contesto specifico del business.

### 4.2 K-Centers Clustering per Partizione di Mercato
Algoritmo di clustering partitivo per identificare segmenti naturali nei dati:

**Processo** (analogia con celle di Voronoi):
1. Selezionare K centri iniziali (casualmente o con euristica)
2. Assegnare ogni cliente al centro più vicino (secondo la metrica scelta)
3. Ricalcolare il centro di ciascun cluster (centroide = media delle coordinate)
4. Ripetere 2-3 finché i centri si stabilizzano (convergenza)
5. I confini tra cluster formano **celle di Voronoi**: regioni dello spazio in cui ogni punto è più vicino al proprio centro che a qualsiasi altro

**Applicazione marketing**:
- Ogni cluster = un segmento di mercato con caratteristiche omogenee
- I centroidi rappresentano il "cliente tipo" di ciascun segmento
- La distanza tra centroidi misura quanto i segmenti sono distinti tra loro

**3 Approcci al Clustering** (dal libro):
1. **Gerarchico**: approccio "soap bubble" — cluster vicini si fondono progressivamente (agglomerativo, bottom-up) o si dividono (divisivo, top-down). Produce un dendrogramma
2. **Partitivo**: K-means/K-centers — determina i cluster in un colpo solo, poi raffina iterativamente
3. **Bayesiano**: utilizza probabilità a priori e a posteriori per determinare l'appartenenza al cluster; più sofisticato ma computazionalmente più costoso

**Criticità operative**:
- Sensibile agli outlier (un data point anomalo può distorcere il centroide)
- Sensibile al punto di partenza (inizializzazione diversa → cluster diversi)
- La conoscenza a priori dei dati aiuta a scegliere K e i punti iniziali appropriati
- Difficile quantificare la "bontà" di un clustering (silhouette score, elbow method)

### 4.3 Classificazione Bayesiana per Profiling Consumatori
Applicazione del teorema di Bayes per classificare consumatori in segmenti predefiniti:

**Logica**: dato un insieme di caratteristiche osservate (comportamento, demografia, preferenze), qual è la probabilità che il consumatore appartenga a ciascun segmento?

**P(Segmento|Dati) = P(Dati|Segmento) × P(Segmento) / P(Dati)**

- **P(Segmento)**: probabilità a priori (es. 30% dei clienti sono "Champions", 20% "At Risk")
- **P(Dati|Segmento)**: verosimiglianza — quanto è probabile osservare quei dati in quel segmento
- **P(Segmento|Dati)**: probabilità a posteriori — classificazione aggiornata con l'evidenza

**Uso marketing**: 
- Assegnare nuovi clienti a segmenti esistenti basandosi sul loro comportamento iniziale
- Aggiornare la classificazione man mano che arrivano nuovi dati (approccio dinamico)
- Classificazione probabilistica (non deterministica): un cliente può avere 60% probabilità "Loyal" e 40% "At Risk" → azioni calibrate

**Attenzione**: la probabilità è controintuitiva — il libro cita il caso del California murder case dove l'errore probabilistico del prosecutor ha portato a conclusioni sbagliate. Nel marketing, errori analoghi portano a targeting sbagliato.

### 4.4 PCA (Principal Component Analysis) per Brand Perception
Tecnica di riduzione dimensionale che trova le "variabili migliori" — combinazioni lineari delle variabili originali che massimizzano la varianza spiegata.

**Intuizione** (analogia baseball del libro):
- Date 15+ statistiche di un giocatore (battuta, basi rubate, fuoricampo, errori, etc.), molte sono ridondanti
- PCA trova la prima componente principale che spiega la massima varianza → "quanto è bravo il giocatore"
- La seconda componente spiega la massima varianza residua, ed è per costruzione non correlata con la prima → "tipo di giocatore" (slugger vs speedster)
- Ogni componente successiva cattura varianza residua decrescente

**Meccanismo matematico**:
- Si calcola la **matrice di covarianza** tra tutte le variabili
- Si trovano gli **autovettori** (eigenvectors) della matrice → le direzioni delle componenti principali
- Gli **autovalori** (eigenvalues) associati → la quantità di varianza spiegata da ciascuna componente
- Equazione: AX = vX, dove A è la matrice, X il vettore, v lo scalare (autovalore)

**Applicazione alla Brand Perception**:
- Date 20+ variabili di percezione di un brand (innovativo, affidabile, economico, lussuoso, etc.), PCA riduce a 3-5 componenti principali interpretabili
- **PC1** potrebbe essere "qualità percepita complessiva" (correla con affidabile, premium, innovativo)
- **PC2** potrebbe essere "personalità" (asse Explorer vs Sentinel)
- Le perceptual maps (mappe percettive) sono proiezioni dei brand sulle prime 2 componenti principali

**Prerequisiti critici**:
- **Normalizzazione**: PCA è sensibile alla scala → tutti i dati devono essere standardizzati (z-score) prima dell'analisi
- **Standardizzazione**: ogni variabile deve avere media 0 e deviazione standard 1
- Nessuna variabile originale viene "eliminata": ogni componente è una combinazione lineare di TUTTE le variabili originali

### 4.5 Factor Analysis per Dimensioni di Brand
Tecnica complementare alla PCA ma concettualmente diversa:

**PCA vs Factor Analysis**:
| Aspetto | PCA | Factor Analysis |
|---------|-----|-----------------|
| Tipo | Non supervisionata | Supervisionata (il modellatore sceglie i fattori) |
| Obiettivo | Massimizzare varianza spiegata | Identificare fattori latenti sottostanti |
| Componenti | Combinazioni lineari costruite automaticamente | Fattori interpretabili scelti dal ricercatore |
| Indipendenza | Componenti ortogonali (non correlate) | Fattori possono essere correlati tra loro |
| Analogia baseball | "Quanto è bravo" (automatico) | "Forza, velocità, coordinazione" (teorizzati) |

**Applicazione marketing**: 
- Factor Analysis per identificare le dimensioni latenti della percezione di brand (le "qualità invisibili" che guidano le valutazioni osservabili)
- Es.: le valutazioni su 20 attributi di un brand possono essere spiegate da 4 fattori latenti: qualità, innovazione, valore, fiducia
- I fattori non saranno necessariamente indipendenti: qualità e fiducia possono correlare positivamente (come forza e velocità sono entrambe influenzate dal fitness generale)
- Il modellatore decide quanti fattori e come interpretarli → richiede expertise di dominio marketing

### 4.6 Pipeline PCA → Clustering per Segmentazione Marketing
Il processo completo PCA+Clustering per segmentazione AI-driven (collegamento con sezione 3.1):

1. **Raccolta dati**: 7 tipologie (behavioral, contextual, demographic, geographic, psychographic, lifestyle/cultural, social)
2. **Preprocessing**: normalizzazione, standardizzazione, trattamento missing values, anomaly detection
3. **PCA**: riduzione da N variabili a K componenti principali (K << N, tipicamente 3-8) — preserva 70-85% della varianza
4. **Clustering su componenti**: applicare K-means/gerarchico sulle K componenti (non sulle variabili originali) — riduce il rumore e la curse of dimensionality
5. **Interpretazione**: profilare i cluster usando le variabili originali e assegnare metafore (sezione 3.3) e facets (sezione 3.4)
6. **Validazione**: stabilità temporale, actionability, discriminazione, coerenza interna, prevedibilità (sezione 3.3)
7. **Segment Fusion**: fusione con dati da altre fonti per profilo unificato (sezione 3.5)

Questa pipeline è il cuore operativo della segmentazione AI-driven descritta nel libro.
