# Framework Diagnostica Strutturale

## Quadro Normativo di Riferimento (al 2026)

### Norme cogenti

| Norma | Ruolo |
|-------|-------|
| D.M. 17/01/2018 (NTC 2018) | Norma tecnica cogente per tutte le costruzioni |
| Circolare 21/01/2019 n.7 C.S.LL.PP. | Istruzioni applicative NTC 2018 |
| D.P.R. 380/2001 art. 65 | Denuncia lavori c.a./acciaio |
| D.P.R. 380/2001 art. 67 | Collaudo statico |
| D.P.R. 380/2001 artt. 93-94 | Autorizzazione/deposito sismico |

### Norme scadute/storiche da citare solo per contesto

| Norma | Stato |
|-------|-------|
| D.M. 09/03/2023 | Scaduto 22/03/2025 (sospendeva §11.4.2 e §11.5.2 NTC 2018). Rilevante solo per progetti 2023-2025. |
| D.M. 14/01/2008 (NTC 2008) | Storico, applicabile a edifici esistenti 2008-2018 |
| D.M. 16/01/1996 | Storico, per edifici esistenti 1996-2008 |

### Linee Guida e strumenti complementari

| Norma | Ruolo |
|-------|-------|
| D.M. 58/2017 + D.M. 65/2017 | Sismabonus, classi rischio sismico A+÷G |
| OPCM 3274/2003 | Classificazione sismica Comuni (zone 1-2-3-4) |
| CNR-DT 200/2012 | Rinforzo FRP |
| CNR-DT 207/2008 | Azioni vento strutture snelle |

---

## Livelli di Conoscenza (NTC 2018 cap. 8 e Circolare 2019 C8)

| Livello | Geometria | Dettagli costruttivi | Proprieta materiali | FC |
|---------|-----------|---------------------|---------------------|-----|
| LC1 - Limitato | Rilievo completo | Progetto originale o rilievo limitato | Valori da normativa epoca | 1.35 |
| LC2 - Adeguato | Rilievo completo | Rilievo esteso o progetto + verifica | Prove limitate in situ | 1.20 |
| LC3 - Accurato | Rilievo completo | Rilievo esaustivo | Prove estese in situ | 1.00 |

## Proprieta materiali per epoca (c.a.)

| Epoca | Classe calcestruzzo presunta | fcm (MPa) | fym acciaio (MPa) |
|-------|----------------------------|-----------|--------------------|
| < 1950 | Rck 15-20 | 12-16 | 220-320 (liscio) |
| 1950-1970 | Rck 20-25 | 16-21 | 320-380 (FeB32k) |
| 1971-1990 | Rck 25-30 | 21-25 | 380-430 (FeB38k/44k) |
| > 1990 | C25/30 - C30/37 | 25-33 | 430-540 (B450C) |

## Indice di Sicurezza Sismica

IS-V = PGA_capacita / PGA_domanda (ag * S * ST)

| IS-V | Classificazione | Azione |
|------|----------------|--------|
| > 1.0 | Adeguato | Nessun intervento obbligatorio |
| 0.8-1.0 | Quasi adeguato | Miglioramento consigliato |
| 0.6-0.8 | Moderatamente vulnerabile | Miglioramento sismico raccomandato |
| 0.3-0.6 | Vulnerabile | Miglioramento sismico urgente |
| < 0.3 | Molto vulnerabile | Adeguamento/demolizione da valutare |

## Classi di Rischio Sismico (DM 58/2017 e s.m.i.)

| Classe | PAM (%) | IS-V indicativo |
|--------|---------|-----------------|
| A+ | < 0.50 | > 1.2 |
| A | 0.50-1.0 | 1.0-1.2 |
| B | 1.0-1.5 | 0.8-1.0 |
| C | 1.5-2.5 | 0.6-0.8 |
| D | 2.5-3.5 | 0.4-0.6 |
| E | 3.5-4.5 | 0.2-0.4 |
| F | 4.5-7.5 | 0.1-0.2 |
| G | > 7.5 | < 0.1 |

## Verifiche SLU principali

### Flessione semplice c.a.
MRd = As * fyd * (d - 0.4x)  con x = As * fyd / (0.8 * b * fcd)
Verifica: MRd >= MEd → D/C = MEd/MRd

### Taglio c.a.
VRd = min(VRd,c ; VRd,s) con VRd,c per elementi senza armatura a taglio
VRd,s = Asw/s * 0.9d * fyd * (cotθ + cotα) * sinα
Verifica: VRd >= VEd

### Pressoflessione c.a.
Diagramma di interazione N-M: calcolo per punti con fibra compressa/tesa
Verifica: punto (NEd, MEd) interno al dominio di resistenza

### Muratura - Pressoflessione nel piano
MRd = (l^2 * t * σ0 / 2) * (1 - σ0 / (0.85 * fd))
Dove l = lunghezza parete, t = spessore, σ0 = tensione verticale media

### Muratura - Taglio per fessurazione diagonale
VRd = l * t * (1.5 * τ0d / b) * sqrt(1 + σ0 / (1.5 * τ0d))
Dove τ0d = resistenza a taglio di riferimento della muratura / FC

---

## Combinazioni di Carico (§2.5.3 NTC 2018)

### SLU fondamentale
γG1·G1 + γG2·G2 + γP·P + γQ1·Qk1 + Σ(γQi·ψ0i·Qki)

### SLU eccezionale
G1 + G2 + P + Ad + Σ(ψ2i·Qki)

### SLU sismica
E + G1 + G2 + P + Σ(ψ2i·Qki)

### SLE rara
G1 + G2 + P + Qk1 + Σ(ψ0i·Qki)

### SLE frequente
G1 + G2 + P + ψ11·Qk1 + Σ(ψ2i·Qki)

### SLE quasi-permanente
G1 + G2 + P + Σ(ψ2i·Qki)

### Coefficienti parziali (Tab. 2.6.I NTC)

| Azione | γF favorevole | γF sfavorevole |
|--------|---------------|----------------|
| G1 permanente strutturale | 1.0 | 1.3 |
| G2 permanente non strutturale | 0.8 (o 0) | 1.5 |
| Qk variabile | 0.0 | 1.5 |
| P precompressione | 0.9 | 1.1 |

### Coefficienti di combinazione ψ (Tab. 2.5.I NTC)

| Categoria | ψ0 | ψ1 | ψ2 |
|-----------|----|----|----|
| A - Abitazioni/uffici | 0.7 | 0.5 | 0.3 |
| B - Uffici | 0.7 | 0.5 | 0.3 |
| C - Ambienti affollati | 0.7 | 0.7 | 0.6 |
| D - Ambienti commerciali | 0.7 | 0.7 | 0.6 |
| E - Magazzini | 1.0 | 0.9 | 0.8 |
| F - Autorimesse < 30 kN | 0.7 | 0.7 | 0.6 |
| G - Autorimesse > 30 kN | 0.7 | 0.5 | 0.3 |
| H - Coperture | 0.0 | 0.0 | 0.0 |
| Neve z ≤ 1000 m | 0.5 | 0.2 | 0.0 |
| Neve z > 1000 m | 0.7 | 0.5 | 0.2 |
| Vento | 0.6 | 0.2 | 0.0 |
| Temperatura | 0.6 | 0.5 | 0.0 |

### Approcci geotecnici (§6.2.3 NTC)

**Approccio 1 - Due combinazioni**:
- Combinazione 1 (A1+M1+R1) — dimensionamento strutturale degli elementi
- Combinazione 2 (A2+M2+R2) — dimensionamento geotecnico (capacita portante)

**Approccio 2 - Unica combinazione**:
- (A1+M1+R3) — sia strutturale che geotecnico, con γR specifici per verifica
