# ECONOMIA INTERNAZIONALE E MONETARIA - Reference Tecnico

## TASSI DI CAMBIO E BOND

### Relazione Prezzo-Tasso Bond

$$B_t (1 + i_t) = 100 \quad \Rightarrow \quad B_t = \frac{100}{1 + i_t}$$

Tasso interesse nominal implicitO: ↑ $i$ → ↓ prezzo bond

### Struttura per Scadenza (Term Structure)

Tasso a 2 anni dalla media di tassi spot 1 anno corrente ed atteso:

$$(1 + i_{t,2})^2 = (1 + i_t)(1 + i^e_{t+1})$$

$$i_{t,2} = \frac{i_t + i^e_{t+1}}{2}$$

Se aspettative di rialzo tassi → curva yield positiva.

---

## TASSI NOMINALI VS REALI

### Relazione Fisher

$$1 + i_t = (1 + r_t)(1 + \pi^e_{t+1})$$

Approssimazione: $i_t \approx r_t + \pi^e_{t+1}$ (Fisher equation)

| Grandezza | Formula |
|-----------|---------|
| **Tasso reale** | $r_t = i_t - \pi^e_{t+1}$ |
| **Inflazione attesa** | $\pi^e_{t+1} = \frac{P^e_{t+1}}{P_t} - 1$ |

---

## PARITÀ DEI POTERI D'ACQUISTO (PPP)

### Legge del Prezzo Unico

Bene $i$ identico, no trasporti: $E_{$/€} \times P_i^€ = P_i^{\$}$

### PPP Assoluta

$$E_{$/€} = \frac{P^{\$}}{P^€}$$

Tasso cambio = rapporto livelli prezzi.

**Fallimenti**: Beni non-tradabili (lavoro, real estate), costi trasporto, non perfetta sostituzione.

### PPP Relativa

Variazioni di cambio = differenza variazioni prezzi:

$$\frac{E_t - E_{t-1}}{E_{t-1}} = \pi^{\$}_t - \pi^€_t$$

Meno restrittiva di assoluta; più supportata empiricamente.

### Parità Interesse Scoperta (UIP)

$$\frac{E^e - E}{E} = R - R^*$$

Rendimento atteso valuta domestica = differenziale tassi. Fallisce empiricamente (forward premium puzzle).

### Fisher Effect Internazionale

Unione UIP + PPP relativa:

$$\pi^e - \pi^{e*} = R - R^*$$

↑ inflazione domestica → ↑ tasso nominale domestico (lungo periodo).

---

## MODELLO MUNDELL-FLEMING

Economía aperta, beni e moneta, tasso cambio flessibile.

### Tre Equazioni

1. **IS**: $Y = C(Y-T) + I(Y, r) + G + NX(Y, Y^*, E)$
   - $NX$ dipende: output domestico ($Y$), estero ($Y^*$), cambio reale ($E$)

2. **LM**: $\frac{M}{P} = L(Y, i)$

3. **Parità Interesse Scoperta**: $\frac{E^e - E}{E} = i - i^*$

### Equilibrio

$(Y^*, i^*)$ da IS-LM; poi $E^*$ da UIP.

### Politiche in Regime Tassi Flessibili

| Policy | Effetto |
|--------|---------|
| **Espansione fiscale** | ↑ $i$ → apprezzamento $E$ → ↓ $NX$ → poco/niente effetto $Y$ (crowding out estero) |
| **Espansione monetaria** | ↓ $i$ → deprezzamento $E$ → ↑ $NX$ → ↑ $Y$ (efficace) |
| **Shock reputazione** | ↑ $E$ (apprezzamento) → ↓ $NX$ → ↓ $Y$ |

---

## TASSO DI CAMBIO REALE E BILANCIA COMMERCIALE

### Tasso Cambio Reale

$$E^r = E \times \frac{P^*}{P}$$

(potere d'acquisto relativo, aggiustato per inflazione estera)

### Elasticità Commerciale

$$NX = NX(E^r, Y, Y^*)$$

- ↑ $E^r$ (deprezzamento reale) → ↑ esportazioni, ↓ importazioni → ↑ $NX$
- ↑ $Y$ → ↑ importazioni → ↓ $NX$

---

## ENFASI INTERTEMPORALE: TASSI LUNGHI

### Aspettative Tasso Cambio Futuro

Se annuncio espansione monetaria permanente:

$$i \uparrow \not\Rightarrow E \downarrow \text{ (verso equilibrio lungo termine)}$$

Invece: ↑ inflazione attesa → ↓ tasso reale → deprezzamento atteso futuro

→ **Overshooting di Dornbusch**: cambio si muove più di quanto in LP.

---

## BILANCIA DEI PAGAMENTI

### Componenti

| Conto | Descrizione |
|-------|------------|
| **Corrente (CA)** | Commercio beni, servizi, redditi primari, trasferimenti |
| **Capitale** | Movimenti capitali, investimenti |
| **Finanziaria** | Investimenti diretti, portafoglio, derivati |

**Identità**: $CA + KA \approx 0$ (deficit corrente → afflusso capitali).

---

## APPROCCIO MONETARIO AL CAMBIO

### Equilibrio Lungo Termine

Domanda e offerta moneta determinano prezzo (livello prezzi):

$$P = \frac{M}{L(r, Y)}$$

PPP + monetario → tasso cambio determinato da:

$$E_{$/€} = \frac{M^{\$}}{M^€} \times \frac{L(r^€, Y^€)}{L(r^{\$}, Y^{\$})}$$

**Effetto**: ↑ $M^{\$}$ → proporzionale ↑ $E_{$/€}$ (deprezzamento) LP.

### Neutralità Monetaria LP

Aumento permanente offerta moneta non altera output, occupazione, tassi reali.

---

## ELEMENTI DI AREE VALUTARIE OTTIMALI

### Criteri Mundell

**Adesione unione monetaria efficiente se**:

1. **Mobilità fattori produttivi** alta (L, K tra paesi)
2. **Correlazione shocks** alta (muovono insieme)
3. **Integrazione commerciale** alta (rischi diversificabili)
4. **Automatic stabilizers fiscali** forti (trasferimenti tra paesi)

### Trade-off

- **Pro unione**: Eliminazione rischio cambio, integrazione finanziaria, spillover politici
- **Contro**: Perdita strumento politica monetaria indipendente; shocks asimmetrici problematici

### Eurozona: Caso Reale

Elevata integrazione commerciale, mobilità L limitata, shocks asimmetrici (es. crisi 2010-15).

→ Richiede automatismi fiscali europei o politica redistributiva (ancora incomplete).

---

## FENOMENO OVERSHOOTING (Dornbusch)

### Meccanica

1. ↑ $M$ annunciato → prezzo salta a $P^* > P$ (mercato anticipa)
2. $r \downarrow$ immediato, ma prezzi sticky (breve termine)
3. Real $\frac{M}{P}$ ↑ → ↓ tassi → deprezzamento atteso futuro
4. **Cambio salta a deprezzamento iniziale > deprezzamento LP** (overshooting)
5. Nel tempo: $P \uparrow$ gradualmente → $r$ ritorna, cambio converge LP

### Implicazione

Spiega volatilità elevata tassi cambio nominali (daily jumps) vs. smooth LP alignment.

---

## INFLAZIONE INTERNAZIONALE

### Relazione Moneta-Prezzi LP

Empirica (1980-2014): forte correlazione tra $g_M$ e $\pi$

$$\frac{\Delta P}{P} = \frac{\Delta M^s}{M^s} - \frac{\Delta L}{L}$$

- Variazioni tasso cambio concordi con differenziali inflazione (supporta PPP relativa)
- Deviazioni: dovute a shocks domanda moneta, output, bassissime

---

## PRICING DELLE MERCI SCAMBIATE

### Tipologie

| Modello | Descrizione |
|---------|------------|
| **PCP (Producer Currency Pricing)** | Esportatore fissa prezzo in valuta domestica |
| **LCP (Local Currency Pricing)** | Prezzo in valuta acquirente; impresa assorbe variazioni cambio |
| **DCP (Dominant Currency)** | Prezzo in valuta dominante (es. $\$ per commodities) |

**Effetto**: PCP → pass-through cambio alto; LCP → scarso (discriminazione prezzo).

---

**Max 350 righe — Reference internazionale e monetaria completato.**
