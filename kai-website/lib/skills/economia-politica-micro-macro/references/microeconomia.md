# MICROECONOMIA - Reference Tecnico

## TEORIA DEL CONSUMATORE

### Curve di Domanda e Offerta

| Formula | Descrizione |
|---------|------------|
| $Q_d = a - b \cdot P_x$ | Curva di domanda |
| $P_x = \frac{a}{b} - \frac{Q_d}{b}$ | Inversa domanda |
| $Q_s = a + b \cdot P_x$ | Curva di offerta |
| $P_x = -\frac{a}{b} + \frac{Q_s}{b}$ | Inversa offerta |

### Elasticità della Domanda

| Tipo | Formula | Interpretazione |
|------|---------|-----------------|
| **Prezzo** | $E_{Qd,p} = \frac{\partial Q_d}{\partial P} \cdot \frac{P_0}{Q_0}$ | \|$E$\| > 1: elastica; = 1: unitaria; < 1: inelastica |
| **Reddito** | $E_{Qd,M} = \frac{\partial Q_d}{\partial M} \cdot \frac{M_0}{Q_0}$ | > 0: bene normale; < 0: bene inferiore |
| **Incrociata** | $E_{Qx,Py} = \frac{\partial Q_x}{\partial P_y} \cdot \frac{P_y}{Q_x}$ | > 0: sostituti; < 0: complementi |

**Spesa totale**: $TE = P \cdot Q$ → $\%TE = \%P + \%Q$

### Utilità e Saggio di Sostituzione

| Concetto | Formula |
|----------|---------|
| **Utilità marginale** | $MU_x = \frac{\partial U(x,y)}{\partial x}$, $MU_y = \frac{\partial U(x,y)}{\partial y}$ |
| **MRS (saggio marginale di sostituzione)** | $MRS_{x,y} = \frac{MU_x}{MU_y}$ |
| **Ottimo consumatore** | $MRS_{x,y} = \frac{P_x}{P_y}$ |

### Funzioni di Utilità Canoniche

#### Beni Standard (Cobb-Douglas)
$$U(x,y) = x^a y^b \quad \Rightarrow \quad MRS = \frac{a}{b} \cdot \frac{y}{x}$$

#### Beni Perfetti Sostituti
$$U(x,y) = ax + by \quad \Rightarrow \quad MRS = \frac{a}{b} \text{ (costante)}$$

#### Beni Perfetti Complementi
$$U(x,y) = \min(ax, by) \quad \Rightarrow \quad \text{Ottimo: } y = \frac{a}{b}x$$

### Vincolo di Bilancio
$$P_x X + P_y Y = M$$
$$Y = \frac{M}{P_y} - \frac{P_x}{P_y}X \quad \text{(retta con inclinazione } -\frac{P_x}{P_y}\text{)}$$

### Effetto Reddito e Sostituzione (Slutsky)
Variazione di quantità domandata da shock di prezzo:
$$\Delta Q = \underbrace{\frac{\partial Q}{\partial P}|_{MRS=P/P}}_{\text{Sostituzione}} + \underbrace{\frac{\partial Q}{\partial M} \cdot P \cdot Q/M}_{\text{Reddito}}$$

- **Bene normale**: Effetto reddito < 0 (stesso segno di sostituzione)
- **Bene inferiore**: Effetto reddito > 0 (opposto a sostituzione); se > sostituzione → **bene Giffen**

---

## TEORIA DELLA PRODUZIONE

### Funzione di Produzione e Prodotti

| Concetto | Formula |
|----------|---------|
| **Prodotto medio lavoro** | $APL = \frac{Q}{L}$ |
| **Prodotto marginale lavoro** | $MPL = \frac{\partial f(L,K)}{\partial L}$ |
| **Prodotto medio capitale** | $APK = \frac{Q}{K}$ |
| **Prodotto marginale capitale** | $MPK = \frac{\partial f(L,K)}{\partial K}$ |

**Regola**: Se $MP > AP$ allora $AP$ cresce; se $MP < AP$ allora $AP$ cala; se $MP = AP$ allora $AP$ flat.

### Funzione di Produzione Cobb-Douglas
$$f(L,K) = A \cdot L^\alpha K^\beta$$

- Se $\alpha > 1$: $MPL$ crescente
- Se $\alpha < 1$: $MPL$ decrescente
- Se $\alpha = 1$: $MPL$ costante (analogamente per $\beta$ e $K$)

### Saggio Marginale di Sostituzione Tecnica (MRTS)
$$MRTS_{L,K} = \frac{MPL}{MPK}$$

**Isoquanto**: luogo dei punti $(L, K)$ che producono $Q$ costante.

#### MRTS Canonici
- **Input standard (Cobb-Douglas)**: $MRTS_{L,K} = \frac{\alpha}{β} \cdot \frac{K}{L}$
- **Input perfetti sostituti**: $f(L,K) = aL + bK$ → $MRTS = \frac{a}{b}$ (costante)

### Rendimenti di Scala

| Tipo | Condizione | Significato |
|------|-----------|------------|
| **IRS** (Increasing) | $f(\lambda L, \lambda K) > \lambda f(L,K)$ | Output cresce più che proporzionalmente |
| **CRS** (Constant) | $f(\lambda L, \lambda K) = \lambda f(L,K)$ | Output cresce proporzionalmente |
| **DRS** (Decreasing) | $f(\lambda L, \lambda K) < \lambda f(L,K)$ | Output cresce meno che proporzionalmente |

**Cobb-Douglas**: Se $\alpha + \beta > 1$ → IRS; = 1 → CRS; < 1 → DRS

### Costi di Produzione

| Costo | Formula | Breve Periodo | Lungo Periodo |
|------|---------|--------------|--------------|
| **Totale** | $TC(Q) = wL + rK$ | $FC + VC$ | Tutti variabili |
| **Medio** | $AC = \frac{TC}{Q}$ | $AFC + AVC$ | $\frac{VC}{Q}$ |
| **Marginale** | $MC = \frac{\partial TC}{\partial Q}$ | Variabili solo | Tutti input |

**Isocosto**: $wL + rK = TC$ → inclinazione: $-\frac{w}{r}$

**Ottimo produttivo**: $MRTS_{L,K} = \frac{w}{r}$ + vincolo $f(L,K) = Q$

**Relazione AC-MC**: 
- Se $AC$ decresce → $AC > MC$ (economie di scala)
- Se $AC$ cresce → $AC < MC$ (diseconomie di scala)

---

## FORME DI MERCATO

### Concorrenza Perfetta

**Curva di offerta**: $P = MC$ se $P \geq \min(AC)$

**Quantità**: $Q_i^* = \frac{Q_{market}^*}{N}$ (divisione equa fra $N$ imprese)

**Profitti**: $\Pi = P \cdot Q_i - TC(Q_i)$; in equilibrio: $\Pi = 0$ (in LP)

**Surplus consumatore**: $\frac{(P_{max} - P) \cdot Q}{2}$

**Surplus produttore**: $\Pi + FC$ (breve); $\Pi$ (lungo periodo)

### Monopolio

**Massimizzazione**: $MR = MC$ → $Q_m$, poi $P_m$ da curva domanda

**Markup**: $\frac{P - MC}{P} = -\frac{1}{E_{Qd,p}}$ (potere di mercato)

**Discriminazione di prezzo**:
- **Perfetta**: $P = MC$, DWL = 0, surplus consumatori → produttore
- **Due tariffe**: Fisso $P=MC$, variabile = surplus
- **Terzo tipo**: $MR_1 = MC$ → $(Q_1, P_1)$; $MR_2 = MC$ → $(Q_2, P_2)$ (domande diverse)

### Oligopolio: Modello di Bertrand

**Competizione su prezzo simultanea**

- **Costi identici**: $P_A = P_B = MC$ → $\Pi = 0$ (efficienza)
- **Costi diversi** ($MC_A > MC_B$): $P_A = MC_A$, $P_B = MC_A - \varepsilon$ → B prende tutto

**Con $n > 2$ imprese**:
1. Se $MC_1 > MC_2 > MC_3$: $P_1 = MC_1$; $P_2 = MC_2$; $P_3 = MC_2 - \varepsilon$ (la 3ª vince)

### Oligopolio: Modello di Cournot

**Competizione su quantità simultanea**

$$Q = Q_1 + Q_2, \quad P = a - (Q_1 + Q_2)$$

**Revenue marginale**: $MR_i = a - (Q_i + Q_j)$

**Funzioni di reazione ottima**:
$$MR_1 = MC_1 \quad \Rightarrow \quad Q_1 = f(Q_2)$$
$$MR_2 = MC_2 \quad \Rightarrow \quad Q_2 = f(Q_1)$$

**Nash Equilibrio**: Risolvere il sistema → $(Q_1^*, Q_2^*)$

### Oligopolio: Modello di Stackelberg

**Competizione sequenziale** (Leader-Follower)

1. Follower (impresa 2) sceglie: $Q_2 = f(Q_1)$
2. Leader (impresa 1) anticipa e massimizza:
   $$\Pi_1 = [a - Q_1 - f(Q_1) - MC] \cdot Q_1$$
3. Derivare rispetto $Q_1$ → $Q_1^*$ → $Q_2^* = f(Q_1^*)$ → $Q^* = Q_1^* + Q_2^*$ → $P^*$

---

## SCELTA IN CONDIZIONE DI INCERTEZZA

| Concetto | Formula |
|----------|---------|
| **Valore atteso** | $EV = \sum_i p_i \cdot V_i$ |
| **Utilità attesa** | $EU = \sum_i p_i \cdot U(V_i)$ |
| **Equivalente certo** | $U(CE) = EU$ |
| **Premio al rischio** | $RP = EV - CE$ |

**Avverse al rischio**: $U$ concava, $CE < EV$, $RP > 0$
**Propensi al rischio**: $U$ convessa, $CE > EV$, $RP < 0$
**Neutrali**: $U$ lineare, $CE = EV$, $RP = 0$

---

## ESTERNALITÀ

### Esternalità Negativa

**Mercato privato**: $P = MC$ (inefficiente)

**Social optimum**: $P = MC + MEC$ (marginal external cost)

→ Spostamento offerta verso l'alto di $MEC$; quantità → giù

**Correzione**: Tassa pari a $MEC \cdot Q$ (Pigouviana)

### Esternalità Positiva

**Mercato privato**: $P = MB$ (sottoconsumo)

**Social optimum**: $P = MB + MEB$ (marginal external benefit)

→ Spostamento domanda verso l'alto di $MEB$; quantità → su

**Correzione**: Sussidio pari a $MEB \cdot Q$

---

## ASIMMETRIE INFORMATIVE

### Selezione Avversa (Market for Lemons - Akerlof)

**Setup**: Auto buona (qualità alta, $MC_{good}$) e cattiva ($MC_{bad}$).

Se qualità non osservabile:
- Consumatori neutrali al rischio: $P^e = 0.5 \cdot P_d^{good} + 0.5 \cdot P_d^{bad}$
- Se $P^e < MC_{good}$ → venditori buoni escono
- Equilibrio: solo auto cattive scambiate a $P = P_d^{bad}$

**Segnalazione**: Bene di alta qualità emette segnale credibile se:
$$\pi_{good|signal} \geq \pi_{good|no signal} \quad \text{e} \quad \pi_{bad|signal} < \pi_{bad|no signal}$$
→ Separazione in due mercati (bene + segnale vs. senza segnale)

### Moral Hazard

**Vincoli su sforzo $e$ dell'agente**:
1. **Compatibilità incentivi**: $EU(e=1) \geq EU(e=0)$
2. **Partecipazione**: $EU(e=1) \geq \bar{U}$

---

## TEORIA DEI GIOCHI (Base)

### Forme Normali e Strategie

**Equilibrio di Nash**: Profilo di strategie tali che nessun giocatore vuole deviare unilateralmente.

**Gioco di coordinamento**: Beneficio da coordinazione (es.: standard tecnologici).

**Gioco di competizione pura**: Zero-sum; interessi opposti.

---

**Max 450 righe — Reference tecnico completato.**
