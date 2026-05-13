# Corporate Finance — Contenuto Bocconi Distintivo

## Matematica finanziaria

### Regimi di capitalizzazione e sconto

**Capitalizzazione semplice (retta)**
- Montante: $M(t) = C(1 + it)$
- Fattore montante: $f(t) = 1 + it$
- Fattore sconto: $\varphi(t) = \frac{1}{1+it}$
- Tasso unitario di interesse: $i = f(1) - 1$

**Capitalizzazione composta (annuale)**
- Montante: $M(t) = C(1+i)^t$
- Fattore montante: $f(t) = (1+i)^t$
- Fattore sconto: $\varphi(t) = \frac{1}{(1+i)^t}$

**Capitalizzazione composta istantanea (regime esponenziale)**
- $f(t) = e^{\delta t}$, dove $\delta = \ln(1+i)$ è l'intensità istantanea d'interesse
- $\varphi(t) = e^{-\delta t}$
- Legame: $1 + i = e^{\delta}$

### Tassi equivalenti e TAEG

Due tassi relativi a periodi di capitalizzazione diversi sono equivalenti se producono montanti uguali:
- Da periodale ad annuale: $i = (1+i_m)^m - 1$
- Da annuale a periodale: $i_m = \sqrt[m]{1+i} - 1$

**Tasso Annuo Nominale (TAN)**: tasso nominale riferito ad anno, usato in contratti finanziari.
- Se il tasso mensile è $i_m$, allora TAN $= m \cdot i_m$

**Tasso Annuo Effettivo Globale (TAEG)**: tasso equivalente che considera tutti i costi finanziamenti.
- Eguaglia il valore attuale della somma ricevuta al valore attuale delle rate erogate

### Ammortamenti

**Piano di ammortamento graduale**: serie di pagamenti $R_t$ (rate) che estinguono un debito $S$ con interesse al tasso $i$.

**Legge di ammortamento (variabile)**
- Condizione di chiusura elementare: $S = \sum_{t=1}^{n} C_t$ (somma quote capitali = debito)
- Condizione di chiusura finanziaria (iniziale): $S = \sum_{t=1}^{n} R_t \varphi(t_s)$
- Condizione di chiusura finanziaria (finale): $S \cdot f(T_n) = \sum_{t=1}^{n} R_t f(T_n - t_s)$

Donde: $R_t = C_t + I_t$ (rata = quota capitale + quota interessi)

**Ammortamento all'italiana (francese adattato)**
- Quote capitali costanti: $C_t = \frac{S}{n}$
- Interessi decrescenti: $I_t = (S - \sum_{k=1}^{t-1} C_k) \cdot i$
- Rata: $R_t = C_t + I_t$ (decrescente nel tempo)

**Ammortamento alla francese (annualità costante)**
- Rata costante: $R = S \cdot \frac{i(1+i)^n}{(1+i)^n - 1} = S \cdot a_{n|i}^{-1}$
- Quote capitali crescenti: $C_t = R \cdot \varphi(n-t+1)^{-1}$
- Debito residuo: $D_t = R \cdot a_{n-t|i}$

### Duration e Convexity di un bond

**Duration di Macaulay** (scadenza media ponderata):
$$D = \frac{\sum_{t=1}^{n} t \cdot CF_t \cdot \varphi(t)}{\sum_{t=1}^{n} CF_t \cdot \varphi(t)} = \frac{\sum_{t=1}^{n} t \cdot CF_t \cdot (1+y)^{-t}}{P}$$

dove $CF_t$ sono i flussi di cassa, $y$ il yield to maturity, $P$ il prezzo del bond.

**Durata modificata** (sensibilità prezzo-rendimento):
$$D^* = \frac{D}{1+y}$$

Approssimazione variazione prezzo:
$$\Delta P \approx -D^* \cdot P \cdot \Delta y + \frac{1}{2} \cdot \text{Convexity} \cdot P \cdot (\Delta y)^2$$

**Convexity**:
$$\text{Convexity} = \frac{\sum_{t=1}^{n} t(t+1) \cdot CF_t \cdot (1+y)^{-t-2}}{P}$$

---

## Teoria del portafoglio (Markowitz, CAPM, APT)

### Markowitz: Varianza-media e frontiera efficiente

**Varianza e covarianza di un portafoglio** (N asset):
$$\sigma_p^2 = \sum_{i=1}^{N} w_i^2 \sigma_i^2 + 2\sum_{i=1}^{N}\sum_{j>i} w_i w_j \rho_{ij} \sigma_i \sigma_j$$

dove $w_i$ sono i pesi, $\rho_{ij}$ le correlazioni, $\sigma_i$ le volatilità.

**Diversificazione**: con asset equalmente ponderati e $N \to \infty$:
$$\sigma_p^2 = \frac{1}{N}(\text{Average Variance}) + (1 - \frac{1}{N})(\text{Average Covariance})$$

La varianza non eliminabile è il **rischio sistematico** (covariance risk).

**Frontiera efficiente**: insieme di portafogli che massimizzano il rendimento atteso per ogni livello di rischio.

**Portafoglio a varianza minima (MVP)**: portafoglio sulla frontiera con volatilità più bassa.

**Tangency portfolio**: portafoglio di asset rischiosi con il massimo Sharpe Ratio, tangente alla capital allocation line (CAL).

### Capital Allocation Line e Sharpe Ratio

Con asset privo di rischio ($R_f$) e portafoglio rischioso ($R_p$):

$$E(R_p) = R_f + \omega [E(R) - R_f]$$
$$\sigma_p = |\omega| \sigma$$

**Sharpe Ratio del portafoglio rischioso**:
$$SR = \frac{E(R) - R_f}{\sigma} = \frac{E[R_p] - R_f}{\sigma_p}$$

La CAL ha pendenza pari al Sharpe Ratio; il tangency portfolio lo massimizza.

### CAPM: Capital Asset Pricing Model

**Assunzioni**:
1. Mercato competitivo in equilibrio
2. Orizzonte temporale unico
3. Tutti gli asset sono negoziabili
4. Nessun attrito (no tasse, no costi transazione)
5. Investitori razionali, mean-variance optimizer, aspettative omogenee

**Modello a un fattore**:
$$r_i = E(r_i) + \beta_i m + e_i$$

dove:
- $m$ è il fattore di rischio sistematico (eccesso rendimento di mercato)
- $\beta_i = \frac{\text{Cov}(r_i, r_m)}{\text{Var}(r_m)}$ è il beta sistematico dell'asset
- $e_i$ è il rischio specifico (idiosincratico), $\text{Cov}(m, e_i) = 0$

**Varianza dell'asset**:
$$\sigma_i^2 = \beta_i^2 \sigma_m^2 + \sigma_{e_i}^2$$

**Security Market Line (SML)**:
$$E(R_i) = R_f + \beta_i [E(R_m) - R_f]$$

- **Intercept** ($\alpha_i$): è il rendimento quando $\beta=0$. In equilibrio CAPM, $\alpha_i = 0$ per tutti gli asset
- **Slope**: è il premio per rischio sistematico (market risk premium)
- Se $\alpha_i > 0$: asset sottovalutato (buy)
- Se $\alpha_i < 0$: asset sopravvalutato (sell)

**Capital Market Line (CML)** (tangency portfolio = portafoglio di mercato):
$$E(R_p) = R_f + \frac{E(R_m) - R_f}{\sigma_m} \sigma_p$$

La CML è valida solo per portafogli efficienti (sulla frontiera).

### APT: Arbitrage Pricing Theory (Ross)

Modello multifattore senza ipotesi su preferenze investitori:

$$E(R_i) = R_f + \lambda_1 \beta_{i1} + \lambda_2 \beta_{i2} + \cdots + \lambda_k \beta_{ik}$$

dove:
- $\beta_{ij}$ è la sensibilità dell'asset al fattore $j$
- $\lambda_j$ è il premio per rischio del fattore $j$ (analogo al market risk premium)

**Assenza di opportunità di arbitraggio**: se non esistono portafogli "zero-cost" con return garantito positivo, vale la relazione lineare con i fattori.

---

## Derivati formalizzati

### Opzioni: Payoff e strategie

**Call option (opzione di acquisto)**:
- Payoff a scadenza: $\max(S_T - K, 0)$
- $S_T$ prezzo spot a scadenza, $K$ strike price
- Valore: massimo tra la differenza (S - K) e zero

**Put option (opzione di vendita)**:
- Payoff: $\max(K - S_T, 0)$

**Parità put-call**:
$$C_t - P_t = S_t - K e^{-r(T-t)}$$

### Black-Scholes: Pricing e Greeks

**Prezzo call option** (asset non dividend-paying):
$$C_t = S_t N(d_1) - K e^{-r(T-t)} N(d_2)$$

dove:
$$d_1 = \frac{\ln(S_t/K) + (r + \frac{\sigma^2}{2})(T-t)}{\sigma\sqrt{T-t}}$$
$$d_2 = d_1 - \sigma\sqrt{T-t}$$

e $N(\cdot)$ è la CDF della normale standard.

**Delta** ($\Delta$): sensibilità del prezzo all'asset sottostante
$$\Delta_C = N(d_1), \quad \Delta_P = N(d_1) - 1$$

**Gamma** ($\Gamma$): sensibilità della delta al prezzo dell'asset (convexity)
$$\Gamma = \frac{N'(d_1)}{S_t \sigma \sqrt{T-t}}$$

**Vega** ($\nu$): sensibilità alla volatilità
$$\nu = S_t N'(d_1) \sqrt{T-t}$$

**Theta** ($\Theta$): sensibilità al passaggio del tempo (decay)
$$\Theta = -\frac{S_t N'(d_1) \sigma}{2\sqrt{T-t}} - r K e^{-r(T-t)} N(d_2)$$

**Rho** ($\rho$): sensibilità ai tassi di interesse
$$\rho = K(T-t) e^{-r(T-t)} N(d_2)$$

### Swap: IRS (Interest Rate Swap) e CDS (Credit Default Swap)

**Interest Rate Swap (IRS)**
- Contratto in cui le parti scambiano flussi di interessi a tasso fisso vs tasso variabile su uno stesso capitale nozionale
- Valore fisso (fixed leg): $\sum_{i=1}^{n} c \cdot \Delta t_i \cdot B_i(0)$, dove $c$ è la cedola fissa, $B_i(0)$ il fattore di sconto
- Valore variabile (floating leg): pagamenti legati a tassi forward
- In equilibrio, il valore netto dello swap è zero all'inizio ($V_{\text{swap}} = 0$)

**Credit Default Swap (CDS)**
- Protezione contro il default di un emittente obbligazionario
- Venditore del CDS incassa premi periodici; se evento di credito, paga al compratore (nominal - recovery value)
- Spread CDS: premio annuale pagato dal compratore di protezione
- Relazione con bond: $\text{Spread CDS} \approx (1 - \text{Recovery Rate}) \times \text{Probability of Default}$

---

## Valutazione di Financial Institutions (Banche e Assicurazioni)

### Modelli DDM per banche

**Dividend Discount Model applicato alle banche**:
$$V_{\text{bank}} = \sum_{t=1}^{\infty} \frac{D_t}{(1+r_e)^t}$$

dove $D_t$ sono i dividendi attesi, $r_e$ il costo del capitale proprio.

**Franchise value**: valore generato da attività di financial intermediation.
- Misura la capacità della banca di generare profitti in eccesso rispetto al costo del capitale
- $\text{Franchise Value} = V_{\text{bank}} - \text{Replacement Value}$

### Indicatori di solidità bancaria (Basilea III)

**CET1 (Common Equity Tier 1 Ratio)**:
$$\text{CET1} = \frac{\text{Core Tier 1 Capital}}{\text{Risk-Weighted Assets}} \geq 4.5\%$$

Include: capitale azionario, utili non distribuiti (al netto dei filtri regulatori).

**Tier 1 Ratio**:
$$\text{Tier 1} = \frac{\text{Tier 1 Capital}}{\text{RWA}} \geq 6\%$$

Tier 1 = CET1 + Additional Tier 1 (strumenti ibridi, subordinati).

**Total Capital Ratio**:
$$\text{Total Capital} = \frac{\text{Tier 1 + Tier 2}}{\text{RWA}} \geq 8\%$$

**Liquidity Coverage Ratio (LCR)**:
$$\text{LCR} = \frac{\text{High-Quality Liquid Assets (HQLA)}}{\text{Total Net Cash Outflows over 30 days}} \geq 100\%$$

Garantisce che la banca possa sopravvivere a scenario di stress di liquidità.

**Net Stable Funding Ratio (NSFR)**:
$$\text{NSFR} = \frac{\text{Available Stable Funding}}{\text{Required Stable Funding}} \geq 100\%$$

Misura la stabilità di finanziamento su orizzonte di un anno.

### Embedded Value (per assicurazioni)

$$\text{EV} = \text{NAV (Net Asset Value)} + \text{PVFP (Present Value of Future Profits)}$$

dove:
- **NAV**: valore netto della società (patrimonio + riserve matematiche aggiustate)
- **PVFP**: valore attuale dei profitti futuri da polizze in essere
  - Scontati al costo del capitale assicurativo (tasso di sconto risk-adjusted)
  - Depurati da future uscite per sinistri e costi amministrativi

$$\text{EV} = \text{Equity} + \text{PV}[\text{Futuro Profitti Netti}]$$

---

## Sistema finanziario italiano ed europeo

### Struttura del sistema finanziario italiano

**Funzione monetaria**: creazione di moneta (base monetaria, moneta scripturale) e strumenti di pagamento.

**Funzione allocativa**: trasferimento risorse da unit in surplus a unit in deficit.
- **Intermediari specializzati**: banche (credito), intermediari finanziari (titoli), assicurazioni (protezione rischi)

**Funzione di gestione del rischio**: trasferimento di rischi mediante contratti finanziari e polizze.

### Autorità di vigilanza

**Banca d'Italia** (per la struttura):
- Autorità monetaria e di vigilanza prudenziale per banche, intermediari finanziari, mercati monetari
- Responsabile della stabilità del sistema finanziario italiano
- Vigilanza su: liquidità, solvibilità, riserve obbligatorie, trasparenza

**CONSOB** (Commissione Nazionale per le Società e la Borsa):
- Vigilanza su mercati mobiliari, società quotate, intermediari (SIM, gestori patrimoni)
- Enforce compliance a norme sulla trasparenza pre e post-scambio
- Controllo su insider trading, manipolazione mercati

**IVASS** (Istituto per la Vigilanza sulle Assicurazioni):
- Autorità di vigilanza su imprese assicuratrici e riassicurative
- Tutela dei consumatori assicurativi

### MiFID II: Impatti operativi

**Markets in Financial Instruments Directive II** (2018):
- **Best Execution**: intermediari devono eseguire ordini ai migliori prezzi e condizioni disponibili
- **Transparent pre-trade**: pubblicazione quotazioni (bid/ask) in modo continuativo per strumenti liquid
- **Transparent post-trade**: divulgazione operazioni eseguite (prezzi, volumi, tempi)
- **Trading Obligations**: strumenti finanziari devono essere negoziati su venue regolate (MTF/OTF) se liquid
- **Position Limits**: limiti di concentrazione su strumenti derivati (es: commodity derivatives)

### Mercati regolamentati vs Multilateral Trading Facilities (MTF)

**Mercati regolamentati**:
- Soggetti a vigilanza stringente, clearing obbligatorio, regole di listing

**MTF** (mercati privati, over-the-counter):
- Meno regolati, costi di transazione più bassi
- Clearing e settlement negoziali (tra controparte)
- Usati per strumenti non liquid (corporate bonds, derivati OTC)

### Tassazione strumenti finanziari

**Italia**:
- **Plusvalenze da titoli** (capital gains): aliquota ordinaria 26% (irpef con cedolare secca opzionale)
- **Cedole e cedole**:ire fino al 26% aliquota ordinaria
- **Tobin tax**: imposta sulle transazioni finanziarie (0.1% azioni, 0.01% derivati)
- **Imposta sui depositi** (per banche): tassa sui depositi in eccesso a soglie

---

## Note di integrazione

### Connessioni DCF-CAPM-WACC (già in skill, ricordare)

DCF usa WACC come tasso di sconto:
$$\text{WACC} = w_E r_E + w_D r_D (1 - \tau_c)$$

dove $r_E = R_f + \beta_E (E[R_m] - R_f)$ (CAPM) e $w_E, w_D$ sono i pesi di equity e debt.

### Valutazione M&A: sinergies e earnout

**Earnout**: parte del prezzo differito e condizionato al raggiungimento di target (EBITDA, revenue).

**Earnout value**:
$$\text{Earnout} = \sum_t \frac{\text{Contingent Payment}_t}{(1 + \text{WACC discount})^t}$$

Riduce rischio post-acquisizione per l'acquirente; allinea incentivi tra venditori e acquirenti.

### Relazione duration e tassi (per portfolio management)

Aumento dei tassi → diminuzione dell'obbligazionario (duration risk).

Un fondo con duration media 5 anni subirà una perdita di ~5% per ogni rialzo di 100 bp nei tassi.

Gestione: immunizzazione (match duration dell'attivo e passivo) o hedging con futures su tassi.

---

**Compilazione**: Dispense Matteo Cordaro (Bocconi 2022-23) e riferimenti CAPM, APT, Markowitz.
Ricordare che questa skill integra **DCF, WACC, capital budgeting, M&A, LBO, valutazione a multipli, struttura capitale** (già presenti); questo file aggiunge matematica finanziaria, teoria portafoglio formalizzata, derivati, banche, sistema italiano.
