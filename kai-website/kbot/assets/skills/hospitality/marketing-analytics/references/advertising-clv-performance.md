# Advertising Strategy, CLV e Marketing Performance

## 5. Advertising Strategy e Effectiveness

### 5.1 Metriche Fondamentali

**GRP (Gross Rating Point)**:
**GRP = Reach (%) × Frequency**

- **Reach**: % del target raggiunto almeno una volta
- **Frequency**: numero medio di esposizioni per persona raggiunta
- **GRP** = somma dei rating di tutti i passaggi (es. 10 spot × 5% rating ciascuno = 50 GRP)

**CPM (Cost Per Mille)**:
**CPM = (Costo totale / Impressions) × 1.000**

**CPRP (Cost Per Rating Point)**:
**CPRP = Costo totale / GRP**

### 5.2 Curve di Risposta Pubblicitaria

**Modello a S (sigmoide)**: risposta lenta iniziale → accelerazione → saturazione

**Modello concavo (rendimenti decrescenti)**: effetto marginale positivo ma decrescente fin dal primo GRP

**Wear-in e Wear-out**:
- **Wear-in**: periodo iniziale in cui la pubblicità ha effetto crescente (costruzione awareness/recall)
- **Wear-out**: effetto decrescente dopo esposizione eccessiva (affaticamento, irritazione)
- **Soglia minima**: sotto un certo livello di GRP, l'investimento è inefficace
- **Frequency cap**: limite di esposizioni per evitare wear-out

### 5.3 Media Planning
Decisioni chiave:
- **Reach vs Frequency trade-off**: budget fisso → aumentare reach riduce frequency e viceversa
- **Continuity vs Flighting**: presenza costante vs concentrazione in periodi chiave (flight)
- **Pulsing**: combinazione di continuity + burst nei momenti chiave
- **Recency planning**: privilegiare la vicinanza all'atto d'acquisto (reach > frequency)

### 5.4 Misurazione dell'Efficacia
- **Awareness** (aided/unaided): notorietà spontanea e sollecitata
- **Ad recall**: ricordo del messaggio pubblicitario
- **Brand lift**: incremento di awareness/consideration/intent attribuibile alla campagna
- **Attribution modeling**: multi-touch (first click, last click, lineare, time decay, data-driven)
- **Marketing Mix Modeling (MMM)**: regressione che stima il contributo di ciascun canale alle vendite
- **Incrementality testing**: A/B test o geo-test per misurare il contributo causale

---

## 6. Customer Lifetime Value (CLV)

### 6.1 Formula Base (modello a margine costante)

**CLV = M × (r / (1 + i - r)) - AC**

Dove:
- **M** = margine annuo per cliente (ricavo - costo variabile)
- **r** = tasso di retention (% clienti che rimangono da un anno all'altro)
- **i** = tasso di sconto (costo del capitale o tasso di attualizzazione)
- **AC** = costo di acquisizione del cliente

### 6.2 Varianti del CLV

**CLV con orizzonte finito (T anni)**:
**CLV = Σₜ₌₁ᵀ (Mₜ × rᵗ) / (1+i)ᵗ - AC**

**CLV con margine variabile**: quando M cresce nel tempo (cross-sell, upsell):
**CLV = Σₜ₌₁∞ (M₀ × (1+g)ᵗ × rᵗ) / (1+i)ᵗ - AC**

dove g = tasso di crescita del margine per cliente.

### 6.3 Metriche Collegate

**Customer Acquisition Cost (CAC)**:
**CAC = Spesa totale marketing e vendite / Numero nuovi clienti acquisiti**

**LTV/CAC Ratio**: indica la sostenibilità dell'acquisizione
- LTV/CAC > 3 → eccellente
- LTV/CAC 1-3 → accettabile ma da monitorare
- LTV/CAC < 1 → l'acquisizione distrugge valore

**Payback Period**: mesi necessari per recuperare il CAC
**Payback = CAC / (Margine mensile per cliente)**

### 6.4 Customer Equity
Somma dei CLV di tutti i clienti attuali e futuri dell'impresa:

**Customer Equity = Σ CLVᵢ (clienti attuali) + Σ CLVⱼ (clienti futuri attesi)**

Leve per aumentare la Customer Equity:
- **Value equity**: migliorare il prodotto/servizio
- **Brand equity**: rafforzare la marca
- **Relationship equity**: programmi di loyalty, CRM

---

## 7. Marketing Performance Measurement

### 7.1 Dashboard di Marketing — KPI Essenziali

**Acquisition**:
- CAC (Customer Acquisition Cost)
- Conversion rate per canale
- Cost per lead (CPL)
- Cost per click (CPC)

**Engagement**:
- NPS (Net Promoter Score) = % Promoters − % Detractors
- CSAT (Customer Satisfaction Score)
- Engagement rate (social)
- Time on site / pages per session

**Retention**:
- Churn rate = 1 − retention rate
- Repeat purchase rate
- Customer lifetime (1 / churn rate)

**Revenue**:
- ARPU (Average Revenue Per User)
- MRR / ARR (Monthly/Annual Recurring Revenue)
- Revenue per channel
- Marketing ROI = (Revenue attribuibile − Costo marketing) / Costo marketing

### 7.2 Funnel Analysis
| Fase | Metrica | Benchmark tipico |
|------|---------|------------------|
| Awareness | Impressions, Reach | Dipende dal budget |
| Interest | CTR, engagement | 1-3% (digital) |
| Consideration | Lead generation, demo requests | 5-15% dei visitatori |
| Conversion | Purchase rate | 1-5% (e-commerce) |
| Loyalty | Retention, NPS, referral | NPS > 50 = eccellente |

### 7.3 Attribution e Incrementalità
- **Last-click attribution**: assegna tutto il merito all'ultimo touchpoint (semplice ma distorto)
- **Multi-touch attribution (MTA)**: distribuisce il merito tra tutti i touchpoint
- **Marketing Mix Modeling (MMM)**: modello aggregato top-down (regressione su dati time-series)
- **Incrementality test**: gold standard — gruppo test vs controllo per misurare l'effetto causale netto

---

## 8. AI-Applied Advertising e Pricing (Pradeep/Appel/Sthanunathan)

### 8.1 Neuroscience Copy Testing (8 Scores)
Framework di valutazione dell'efficacia creativa basato su neuroscienze. Ogni ad viene valutato su 8 dimensioni (scala 1-10):

**1. Motion Score** (Movimento):
- Il cervello è cablato per rilevare il movimento (sopravvivenza evolutiva)
- Ad con movimento ottimale: non statico ma non caotico
- Applicazione: video con transizioni fluide, animazioni mirate, movimenti direzionali verso il prodotto/logo

**2. Novelty Score** (Novità):
- La novità attiva l'attenzione involontaria (orienting response)
- Troppa novità → confusione; troppo poca → indifferenza
- Applicazione: introdurre un elemento inaspettato nei primi 3 secondi; colpo di scena narrativo

**3. Error Score** (Incongruenza):
- Il cervello processa più a fondo le incongruenze (pattern interrupt)
- Errore intenzionale = il cervello si ferma per "correggere" → maggiore encoding
- Applicazione: visual paradossi, giochi di parole, situazioni leggermente "sbagliate" che il brand risolve

**4. Ambiguity Score** (Ambiguità):
- La giusta dose stimola curiosità e engagement
- Troppa ambiguità → frustrazione e abbandono
- Sweet spot: abbastanza per incuriosire, risolta dal brand nel payoff

**5. Implicit Humanity Score** (Umanità Implicita):
- Volti, mani, espressioni attivano i neuroni specchio → empatia e connessione
- Contatto oculare con la camera → massima attivazione
- Applicazione: protagonista umano con espressioni emotive autentiche, micro-espressioni

**6. No Cortisol Score** (Assenza di Stress):
- Il cortisolo (ormone dello stress) inibisce la memorizzazione del brand
- Stimoli stressanti → il cervello ricorda lo stress, non il brand
- Applicazione: evitare paura/ansia/disagio; usare humor, calore, sorpresa positiva

**7. Voice-Over Score** (Voce Narrante):
- Il tono di voce influenza direttamente il trust e la percezione di autenticità
- Congruenza voce-brand: voce calda per brand Caregiver, voce energica per brand Connector
- Applicazione: matching voce-personalità Big Five del brand; evitare voci generiche

**8. Sound Score** (Musica e Suoni):
- Musica e sound effects attivano la memoria emotiva e il sistema limbico
- Sonic branding (jingle, audio logo) crea associazioni automatiche
- Applicazione: sound design coerente con l'archetipo narrativo; musica che evoca l'emozione target

**Uso operativo**: ciascun ad viene profilato su radar chart 8-dimensionale; il profilo aggregato predice recall (R²~0.65), brand lift e conversion rate. Score complessivo < 5 su più di 3 dimensioni → rework creativo obbligatorio.

**Extended Scores (7 aggiuntivi dal Cap 13)**:
Oltre agli 8 core scores, la valutazione neuroscientifica avanzata include 7 dimensioni aggiuntive:

9. **Music Score**: il music priming nel cervello avviene tra i 15 e i 22 anni. Lo score valuta l'appropriatezza dell'età della musica rispetto alla demografia target, specialmente nei primi secondi dell'ad
10. **Lyric Semiotic Score**: la semiotica dei testi della canzone deve connettersi con la semiotica della metafora e del creative thrust dell'ad
11. **Optical Illusions Score**: fascinazione del cervello per novità/newness inaspettate. Illusioni ottiche in cui la percezione supera o contrappone ciò che si vede → catturano attenzione (particolarmente efficaci in digital advertising e retail POS)
12. **Slow Motion Score**: il cervello è ossessionato dal movimento lento. Il tempo assoluto in un ad consumato in slow motion migliora l'effectiveness complessiva
13. **Context Score**: scoring sistematico su quanti elementi contestualmente connessi al topic nella mente non-conscia sono presenti nell'ad
14. **Metaphor Score**: scoring basato sulla semiotica e imagery della metafora emergente o dominante identificata e connessa al topic presente nell'ad
15. **Brand Semiotics Score**: scoring basato sulla presenza della semiotica della brand personality e degli attributi brand nell'ad

**Applicazione avanzata**: i 15 scores totali (8 core + 7 extended) possono essere decomposti via **factor analysis** per determinare quali fattori latenti sono meglio correlati alla performance per brand/categoria specifica. Lo score profile 15D consente di ottimizzare il creative per target specifico.

### 8.2 Algorithmic Creative Storytelling (12 Step)
Processo algoritmico per costruire storytelling pubblicitario efficace:
1. Define brand personality (Big Five)
2. Identify target segment personality
3. Match brand-to-segment personality fit
4. Select narrative archetype (eroe, mentore, sfidante, etc.)
5. Define conflict/tension (il problema del consumatore)
6. Create resolution (come il brand risolve)
7. Embed sensory cues (visual, audio, tactile triggers)
8. Optimize for format (30s TV, 15s digital, 8s bumper, 5s pre-roll, print, banner, POS, meme)
9. Test via neuroscience copy testing (8 scores)
10. A/B test varianti creative
11. Iterate based on performance data
12. Scale winning creative across channels

### 8.3 Ad Templates per Formato
| Formato | Durata/Spazio | Struttura Chiave |
|---------|---------------|-----------------|
| TV 30s | 30 secondi | Setup (5s) → Tension (10s) → Brand Resolution (10s) → CTA (5s) |
| Digital 15s | 15 secondi | Hook (3s) → Problem (4s) → Solution (5s) → CTA (3s) |
| Bumper 8s | 8 secondi | Impact visual (3s) → Brand message (3s) → Logo (2s) |
| Pre-roll 5s | 5 secondi | Brand + Key benefit + CTA |
| Print | Pagina | Hero image + Headline + Body (3 righe max) + CTA |
| Banner | 300x250 / 728x90 | Animated: 3 frame (attention → message → CTA) |
| POS | In-store | Product visual + Price/promo + Urgency trigger |
| Meme | Social | Cultural reference + Brand twist + Shareable format |

### 8.4 Programmatic Ad Purchase Logic
Logica decisionale per acquisto programmatico:
- **Real-time bidding (RTB)**: valutazione istantanea del valore dell'impression basata su: profilo utente (Big Five), contesto (sito, momento), probabilità di conversione, budget rimanente
- **Bid optimization**: algoritmo che massimizza expected ROI per impression
- **Frequency capping**: limite esposizioni per utente per evitare wear-out
- **Cross-channel orchestration**: coordinamento tra canali per sequenza ottimale di touchpoint

### 8.5 Dynamic Pricing AI-Driven (PID Controller Model)
Modello di pricing dinamico basato su controller PID (Proportional-Integral-Derivative):
- **P (Proportional)**: aggiustamento prezzo proporzionale al gap tra domanda attuale e domanda target
- **I (Integral)**: correzione basata sull'errore cumulativo nel tempo (evita drift sistematico)
- **D (Derivative)**: anticipo del trend di domanda (aggiustamento preventivo)

**~15 Euristiche di Pricing** (dal libro):
Include heuristics like: reference price anchoring, price-quality inference, odd pricing (€9.99 vs €10), bundle pricing, decoy effect, loss aversion pricing, subscription vs one-time, freemium, dynamic time-based, surge pricing, personalized pricing, loyalty pricing, competitive matching, promotional depth optimization, markdown timing.

### 8.6 Promotions AI-Driven
**7-Stage Promotion Journey**:
1. Pre-awareness (no knowledge of promotion)
2. Awareness (knows promotion exists)
3. Interest (evaluates relevance)
4. Evaluation (compares with alternatives)
5. Trial (first use of promotion)
6. Adoption (repeated use)
7. Advocacy (recommends to others)

**5-Part Promotion Template**:
1. Target definition (who)
2. Mechanic design (what — discount, BOGO, points, etc.)
3. Communication plan (how to reach)
4. Execution logistics (when, where)
5. Measurement framework (KPIs: redemption, uplift, ROI, cannibalization)

**Neurological Codes in Promotions**: le promozioni efficaci attivano codici neurologici specifici — urgency (scarcità, countdown), reward anticipation (dopamina), social proof (altri hanno usato), loss aversion (non perdere l'offerta).

**Loyalty Card Analytics**: analisi dei dati carta fedeltà per: switching algorithm (predire quando un cliente sta per cambiare brand), basket analysis (correlazioni tra prodotti), promotion sensitivity scoring (elasticità individuale alla promozione).
