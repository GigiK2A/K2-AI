# Imposte sul Reddito e Fiscalità Differita

## 1. IRES — Imposta sul Reddito delle Società

### 1.1 Aliquota e Base Imponibile

**IRES**: aliquota **24%** sul reddito imponibile delle società di capitali (SRL, SPA, SAPA).

Il reddito imponibile fiscale (RI) NON coincide con il reddito ante imposte civilistico (RAI):
```
RAI (Reddito Ante Imposte) → risulta dal Conto Economico civilistico
RI (Reddito Imponibile)   → risulta dalla dichiarazione dei redditi (Modello SC)
```

### 1.2 Dal RAI al RI: Variazioni Fiscali

Il passaggio dal RAI al RI avviene attraverso **variazioni in aumento** e **variazioni in diminuzione**:

```
RAI (utile ante imposte da CE)
+ Variazioni in aumento (costi non deducibili fiscalmente)
- Variazioni in diminuzione (ricavi non tassabili o deduzioni extra)
= RI (Reddito Imponibile fiscale)
```

Le variazioni nascono da **differenze** tra norme civilistiche e norme fiscali (TUIR - D.P.R. 917/1986).

---

## 2. Differenze Permanenti e Temporanee

### 2.1 Differenze Permanenti

Sono differenze tra RAI e RI che **non si riverseranno** mai negli esercizi futuri. Nascono da costi civilistici mai deducibili o da ricavi civilistici mai tassabili.

**Esempi di differenze permanenti in aumento (costi non deducibili):**
- Ammende, sanzioni e penalità (art. 99, comma 1, TUIR)
- Liberalità eccedenti i limiti di deducibilità
- 50% spese di rappresentanza eccedenti i limiti
- Imposte sul reddito (IRES/IRPEF stessa)

**Esempi di differenze permanenti in diminuzione (ricavi non tassabili):**
- Dividendi esenti al 95% (PEX — art. 89, comma 2, TUIR)
- Plusvalenze esenti (PEX — art. 87 TUIR, 95% esente)
- Sopravvenienze attive non tassabili

**Effetto**: le differenze permanenti modificano l'aliquota fiscale effettiva rispetto al 24% nominale, ma NON generano imposte anticipate o differite.

### 2.2 Differenze Temporanee

Sono differenze tra RAI e RI che **si riverseranno** negli esercizi futuri. Il costo o il ricavo è riconosciuto sia civilisticamente sia fiscalmente, ma in **esercizi diversi**.

#### Differenze temporanee positive (RAI > RI nell'esercizio corrente)

Il reddito imponibile è **minore** del RAI oggi → l'imposta è rinviata al futuro → nasce un **Fondo imposte differite** (passività).

**Esempio tipico — Plusvalenza rateizzata (art. 86, comma 4, TUIR):**
- Plusvalenza civilistica: rileva interamente nell'esercizio di realizzo
- Plusvalenza fiscale: può essere rateizzata in max 5 esercizi (se il bene è posseduto da almeno 3 anni)

#### Differenze temporanee negative (RAI < RI nell'esercizio corrente)

Il reddito imponibile è **maggiore** del RAI oggi → l'imposta è anticipata → nascono **Imposte anticipate** (attività).

**Esempio tipico — Ammortamento civilistico > ammortamento fiscale:**
- Quota ammortamento civilistico: determinata dalla vita utile effettiva
- Quota ammortamento fiscale: limitata dai coefficienti ministeriali (D.M. 31/12/1988)
- Se l'ammortamento civilistico eccede quello fiscale, la differenza è una variazione in aumento oggi che si riverserà in diminuzione quando l'ammortamento civilistico sarà inferiore al fiscale (o il bene sarà completamente ammortizzato civilisticamente ma non fiscalmente)

---

## 3. Imposte Differite e Anticipate

### 3.1 Formula delle Imposte di Competenza

```
Imposte di competenza = Imposte correnti
                       + Imposte differite (accantonamento)
                       - Imposte anticipate (iscrizione)
                       ± Riversamenti di imposte differite/anticipate di esercizi precedenti
```

Dove:
- **Imposte correnti** = RI × aliquota IRES (24%) → debito verso Erario
- **Imposte differite** = Differenze temporanee positive × aliquota → fondo imposte differite (SP passivo B.2)
- **Imposte anticipate** = Differenze temporanee negative × aliquota → crediti per imposte anticipate (SP attivo C.II.5-ter)

### 3.2 Posizionamento in Bilancio

**Stato Patrimoniale — Attivo:**
- C.II.5-ter) Imposte anticipate (crediti per imposte anticipate)

**Stato Patrimoniale — Passivo:**
- B.2) Fondi per imposte, anche differite

**Conto Economico:**
- 20) Imposte sul reddito d'esercizio, correnti, differite e anticipate
  - a) Imposte correnti
  - b) Imposte differite
  - c) Imposte anticipate
  - d) Proventi (oneri) da adesione al regime di consolidato/trasparenza fiscale

### 3.3 Riversamenti

Negli esercizi successivi, quando le differenze temporanee si riassorbono:

**Riversamento imposte differite** (la passività si riduce):
```
Fondo imposte differite        XXX | Imposte differite (CE, segno +)  XXX
```
Effetto: riduce le imposte di competenza dell'esercizio di riversamento.

**Riversamento imposte anticipate** (il credito si riduce):
```
Imposte anticipate (CE, segno -)  XXX | Crediti per imposte anticipate  XXX
```
Effetto: aumenta le imposte di competenza dell'esercizio di riversamento.

---

## 4. Esempio Completo — Plusvalenza Rateizzata

### Dati
- Anno 1: cessione immobile posseduto da 5 anni. Plusvalenza civilistica: €100.000
- L'impresa opta per la rateizzazione fiscale in 5 esercizi (art. 86, comma 4, TUIR)
- Quota annua fiscale: 100.000 / 5 = €20.000
- Aliquota IRES: 24%
- RAI (senza altre differenze): €200.000

### Anno 1 — Origine della differenza temporanea positiva

```
RAI:                            200.000
Variazione in diminuzione:      -80.000  (plusvalenza civilistica 100.000 - quota fiscale 20.000)
RI:                             120.000
```

**Imposte correnti:** 120.000 × 24% = **€28.800**
**Imposte differite:** 80.000 × 24% = **€19.200** (su plusvalenza rinviata fiscalmente)
**Imposte di competenza:** 28.800 + 19.200 = **€48.000** (= 200.000 × 24% ✓)

**Scritture:**
```
Imposte correnti IRES          28.800 | Debiti tributari (Erario)   28.800
Imposte differite              19.200 | Fondo imposte differite     19.200
```

### Anni 2-5 — Riversamento

Ogni anno diventa tassabile una quota di €20.000 della plusvalenza (già contabilizzata nell'anno 1).

```
RAI anno 2 (ipotesi):          180.000
Variazione in aumento:          +20.000  (quota plusvalenza che diventa tassabile)
RI:                             200.000
```

**Imposte correnti:** 200.000 × 24% = **€48.000**
**Riversamento imposte differite:** 20.000 × 24% = **€4.800**
**Imposte di competenza:** 48.000 - 4.800 = **€43.200** (= 180.000 × 24% ✓)

**Scritture:**
```
Imposte correnti IRES          48.000 | Debiti tributari (Erario)   48.000
Fondo imposte differite         4.800 | Imposte differite (CE)       4.800
```

---

## 5. Esempio Completo — Ammortamento Civilistico vs Fiscale

### Dati
- Macchinario acquistato per €60.000
- Vita utile civilistica: 3 anni → quota annua civilistica: €20.000
- Coefficiente ministeriale fiscale: 15,5% → quota annua fiscale: €9.300
- Primo esercizio fiscale: dimezzamento → quota anno 1: €4.650
- Aliquota IRES: 24%

### Tavola di Confronto (6 esercizi)

| Anno | Amm. Civilistico | Amm. Fiscale | Differenza | Tipo | Var. Fiscale |
|------|------------------|-------------|------------|------|-------------|
| 1 | 20.000 | 4.650 | +15.350 | In aumento | Imp. Anticipate |
| 2 | 20.000 | 9.300 | +10.700 | In aumento | Imp. Anticipate |
| 3 | 20.000 | 9.300 | +10.700 | In aumento | Imp. Anticipate |
| 4 | 0 | 9.300 | -9.300 | In diminuzione | Riversamento |
| 5 | 0 | 9.300 | -9.300 | In diminuzione | Riversamento |
| 6 | 0 | 18.150 | -18.150 | In diminuzione | Riversamento |
| **Tot** | **60.000** | **60.000** | **0** | | |

Nota anno 6: il residuo fiscale (60.000 - 4.650 - 9.300×4 = 18.150) viene dedotto interamente.

### Anno 1 — Iscrizione imposte anticipate

L'ammortamento civilistico (€20.000) eccede il fiscale (€4.650) di €15.350. Questo genera una variazione in aumento (maggior reddito imponibile oggi) e imposte anticipate.

**Imposte anticipate:** 15.350 × 24% = **€3.684**

```
Crediti per imposte anticipate  3.684 | Imposte anticipate (CE)     3.684
```

### Anno 4 — Riversamento imposte anticipate

L'ammortamento fiscale (€9.300) eccede il civilistico (€0): variazione in diminuzione.

**Riversamento:** 9.300 × 24% = **€2.232**

```
Imposte anticipate (CE)         2.232 | Crediti per imposte anticipate 2.232
```

---

## 6. Riepilogo dei 6 Casi

| Caso | Diff. Temporanea | Oggi (origine) | Futuro (riverso) |
|------|-----------------|----------------|-------------------|
| **1. Plusvalenza rateizzata** | Positiva (RAI > RI) | Imposte differite (passivo) | Riversamento → riduce imposte CE |
| **2. Amm. civile > fiscale** | Negativa (RAI < RI) | Imposte anticipate (attivo) | Riversamento → aumenta imposte CE |
| **3. Fondo rischi non deducibile** | Negativa (RAI < RI) | Imposte anticipate (attivo) | Riversamento all'utilizzo del fondo |
| **4. Svalutazione crediti eccedente** | Negativa (RAI < RI) | Imposte anticipate (attivo) | Riversamento alla perdita effettiva |
| **5. Dividendi PEX (95% esente)** | Permanente | Nessuna fiscalità differita | Mai — differenza permanente |
| **6. Sanzioni indeducibili** | Permanente | Nessuna fiscalità differita | Mai — differenza permanente |

---

## 7. Esercizio Tipo Esame

### Dati — Emerson SpA
- RAI: €26.000
- Tax Rate: 30%
- Differenze:
  - Ammende indeducibili: +€4.000 (permanente)
  - Dividendi esenti 95%: -€10.000 × 95% = -€9.500 (permanente)
  - Plusvalenza rateizzata 5 anni: -€15.000 × 4/5 = -€12.000 (temporanea positiva)
  - Fondo garanzia non deducibile: +€6.000 (temporanea negativa)

### Calcolo RI
```
RAI:                            26.000
+ Ammende:                      +4.000
- Dividendi esenti (95%):       -9.500
- Plusvalenza differita (4/5):  -12.000
+ Fondo garanzia:               +6.000
= RI:                           14.500
```

### Calcolo Imposte
```
Imposte correnti:   14.500 × 30% =  4.350
Imposte differite:  12.000 × 30% =  3.600  (plusvalenza rinviata → passivo)
Imposte anticipate:  6.000 × 30% = -1.800  (fondo garanzia → attivo)
= Imposte competenza:              6.150
```

**Verifica**: RAI rettificato per sole permanenti: 26.000 + 4.000 - 9.500 = 20.500
20.500 × 30% = 6.150 ✓

### Scritture
```
Imposte correnti IRES           4.350 | Debiti tributari              4.350
Imposte differite               3.600 | Fondo imposte differite       3.600
Crediti per imposte anticipate  1.800 | Imposte anticipate (CE)       1.800
```

**Voce CE "20) Imposte sul reddito":** 4.350 + 3.600 - 1.800 = **€6.150**
