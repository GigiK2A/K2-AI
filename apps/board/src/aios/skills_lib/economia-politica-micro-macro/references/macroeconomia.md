# MACROECONOMIA - Reference Tecnico

## CONTABILITÀ NAZIONALE

### PIL: Tre Approcci

| Approccio | Formula |
|-----------|---------|
| **Spesa** | $Y = C + I + G + NX$ |
| **Valore aggiunto** | $Y = \sum_i \text{(Valore prodotto}_{i} - \text{Costi intermedi}_{i})$ |
| **Reddito** | $Y = \text{Salari} + \text{Profitti} + \text{Rendite} + \text{Interessi}$ |

### Tasso di Crescita e Deflatore

| Grandezza | Formula |
|-----------|---------|
| **Tasso crescita PIL reale** | $g_{Y,t} = \frac{Y(t) - Y(t-1)}{Y(t-1)}$ |
| **Tasso inflazione** | $\pi(t) = \frac{P(t) - P(t-1)}{P(t-1)}$ |
| **Deflatore PIL** | $P_t = \frac{Y_{nominale}}{Y_{reale}}$ |
| **Indice Prezzi Consumo** | $\pi^{IPC}_t = \frac{IPC_t - IPC_{t-1}}{IPC_{t-1}}$ |

---

## EQUILIBRIO MERCATO BENI (Keynesiano)

### Domanda e Offerta

$$Y = C + I + G + NX$$

**Consumo**: $C^D = C_0 + c_1(Y - T)$ con $0 < c_1 < 1$ (propensione marginale al consumo)

**Investimento**: $I^D = I_0 - d \cdot i$ (dipende da output e tasso interesse)

**Spesa pubblica**: $G^D$ esogena

### Equilibrio: Modello Semplice

$$Y = C_0 + c_1(Y - T) + I + G$$

$$Y(1 - c_1) = C_0 + I + G - c_1 T$$

$$Y^* = \frac{1}{1-c_1}(C_0 - c_1 T + I + G)$$

**Moltiplicatore**: $m = \frac{1}{1-c_1} > 1$ (effetto amplificazione)

**Spesa autonoma**: $C_0 - c_1 T + I + G$

### Risparmio e Investimento

$$S = Y - T - C = \text{Privato}: S_P = Y - T - C$$
$$S_G = T - G = \text{Pubblico}$$
$$S_n = S_P + S_G = \text{Nazionale}$$

**Identità**: $S_n = I$ (il risparmio nazionale finanzia investimenti)

---

## MERCATO DELLA MONETA

### Domanda e Offerta

| Concetto | Formula |
|----------|---------|
| **Domanda moneta** | $M^D = PY \cdot L(i)$ (reddito nominale × funzione tasso) |
| **Offerta moneta** | $M^S = M$ (esogena, controllata da BC) |
| **Equilibrio** | $M^S = M^D$ |

**Tasso di interesse nominale**: $i_t = \frac{€Y_{t+1} + 100}{B_t}$ (da prezzo bond)

### Con Banche Commerciali

**Base monetaria**: $H = C + R$ (circolante + riserve)

**Moltiplicatore monetario**: $m = \frac{M}{H} = \frac{1 + c}{c + \theta(1-c)}$

con $c$ = quota circolante / depositi; $\theta$ = coefficiente riserva obbligatoria

---

## MODELLO IS-LM

### Curva IS (Investimento-Risparmio)

$$Y = C(Y-T) + I(Y, i) + G$$

Risolvi per $(Y, i)$ → **locus equilibrio mercato beni**.

- **Pendenza**: negativa (↑ $i$ → ↓ $I$ → ↓ $Y$)
- **Spostamenti**: shock a $G$, $T$, o preferenze consumo

### Curva LM (Liquidità-Moneta)

$$\frac{M}{P} = Y \cdot L(i)$$

Equilibrio **mercato moneta**:

- **Pendenza**: positiva (↑ $Y$ → ↑ $M^D$ → ↑ $i$)
- **Spostamenti**: shock a $M$ (offerta moneta)

### Equilibrio IS-LM

Intersezione → $(Y^*, i^*)$

**Politiche**:
- **Fiscale espansiva** (↑ $G$, ↓ $T$): IS destra → ↑ $Y$, ↑ $i$
- **Monetaria espansiva** (↑ $M$): LM basso → ↑ $Y$, ↓ $i$

---

## MODELLO AD-AS (Lungo Periodo)

### Domanda Aggregata (AD)

Derivata da IS-LM per livelli di prezzo variabili:

$$Y^D = \bar{A} - b \cdot P$$

con $\bar{A}$ spesa autonoma, $b$ sensibilità a prezzi.

- ↓ $P$ → ↑ domanda reale → ↑ $Y$

### Offerta Aggregata

**Breve periodo (AS)**:
$$P = P^e (1 + m)(1 - \alpha u + z)$$

con $m$ markup, $u$ disoccupazione, $z$ altri costi

- Pressione salari: ↑ $u$ → ↓ salari → giù $P$

**Lungo periodo**:
$$Y = Y_n \quad \text{(output naturale)}$$
$$U = U_n \quad \text{(tasso disoccupazione naturale)}$$

### Equilibrio AD-AS

$Y^D = Y^S$ → $(Y^*, P^*)$

---

## CURVA DI PHILLIPS

### Forma Base

$$\pi - \pi^e = -\alpha(u - u_n)$$

- **Breve periodo**: Trade-off tra inflazione e disoccupazione
- **Lungo periodo** (aspettative adattive): Curva verticale a $u_n$

### Tasso Disoccupazione Naturale

$$u_n = \frac{m + z}{\alpha}$$

- ↑ $m$ (markup), ↑ $z$ (rigidità) → ↑ $u_n$

---

## MERCATO DEL LAVORO

### Curva WS (Wage Setting)

$$\frac{W}{P^e} = F(u, z)$$

- ↑ $u$ → ↓ salario reale (minore potere contrattuale)
- ↑ $z$ → ↑ salario reale (sussidi disoccupazione, sindacati)

### Curva PS (Price Setting)

$$\frac{W}{P} = \frac{1}{1+m}$$

**Equilibrio**: $P = P^e$ → $\frac{W}{P} = F(u_n, z) = \frac{1}{1+m}$

---

## MODELLO IS-LM-PC (Breve + Medio Termine)

### Tre Equazioni

1. **IS**: $Y = C(Y-T) + I(Y, r+x) + G$ (mercato beni)
2. **LM**: $r = \bar{r}$ (tasso policy BC)
3. **PC**: $\pi = \pi^e + \frac{\alpha}{L}(Y - Y_n)$ (curva Phillips; output gap)

### Output Gap e Inflazione

$$\text{Output gap} = Y - Y_n$$

- Gap > 0 → inflazione sopra aspettative
- Gap < 0 → deflazione

### Dinamica Aspettative

**Adattive**: $\pi^e_t = \pi_{t-1}$

**Razionali**: $\pi^e_t = E[\pi_t | \Omega_t]$ (infoset agenti)

---

## POLITICA MONETARIA

### Tasso di Interesse Reale

$$r_t = i_t - \pi^e_{t+1}$$

**Zero Lower Bound**: $i_t = 0$ (vincolo importante in crisi)

### Funzione di Reazione (Taylor Rule)

$$i_t = r^* + \pi^* + \alpha(\pi_t - \pi^*) + \beta(Y_t - Y_n)$$

con $r^*$ tasso reale neutrale, $\pi^*$ target inflazione

### Strumenti BC

| Strumento | Effetto |
|-----------|---------|
| **Mercato aperto (acquisti titoli)** | ↑ $M$ → ↓ $i$ |
| **Sconto tasso ufficiale** | ↓ tassi bancari → ↑ $M$ |
| **Riserve obbligatorie** | ↑ $\theta$ → ↓ moltiplicatore |

---

## POLITICA FISCALE

### Bilancio Pubblico

$$\text{Deficit} = G + iB_{t-1} - T = (G - T) + iB_{t-1}$$

- Parte primaria: $G - T$
- Parte interessi: $iB_{t-1}$

### Vincolo Intertemporal di Bilancio

$$B_t = (1+i)B_{t-1} - PS_t$$

con $PS_t = T_t - G_t$ primario.

**Sostenibilità**: Debito non diverge → primario in avanzo oppure crescita reddito sufficiente.

### Rapporto Debito/PIL

$$\frac{B_t}{Y_t} = \frac{1+i}{1+g} \cdot \frac{B_{t-1}}{Y_{t-1}} - \frac{PS_t}{Y_t}$$

- Se $g > i$: debito stabilizzabile anche con deficit primario
- Se $i > g$: richiesto avanzo primario

---

## EFFETTI POLITICHE MACROECONOMICHE

| Policy | Breve Periodo | Lungo Periodo |
|--------|---------------|---------------|
| **Espansione fiscale** | ↑ $Y$, ↑ $i$, ↑ $\pi$ | ↑ $P$, $Y \to Y_n$, ↑ $B/Y$ |
| **Espansione monetaria** | ↑ $Y$, ↓ $i$ | ↑ $P$ proporzionale, $Y \to Y_n$ |
| **Shock stagflazionista** | ↑ $\pi$, ↓ $Y$ (trade-off) | Pressioni salari, lotta inflazione |

---

**Max 450 righe — Reference completato.**
