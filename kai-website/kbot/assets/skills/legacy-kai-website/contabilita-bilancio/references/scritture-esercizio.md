# Scritture di Esercizio: IVA, Ciclo Acquisti/Vendite, Personale, Finanziamenti

## 1. IVA — Imposta sul Valore Aggiunto

### 1.1 Meccanismo dell'IVA

L'IVA è un'imposta **indiretta** sui consumi, **neutra** per le imprese. Il soggetto IVA funge da **sostituto d'imposta**: riscuote l'IVA dai clienti (IVA a debito) e la versa all'Erario, detraendo l'IVA pagata ai fornitori (IVA a credito).

**Formula liquidazione periodica:**
```
IVA a debito (su vendite) - IVA a credito (su acquisti) = IVA da versare (o credito IVA)
```

### 1.2 Aliquote IVA (principali)
- **22%**: aliquota ordinaria (beni e servizi non agevolati)
- **10%**: aliquota ridotta (alimentari trasformati, ristoranti, ristrutturazioni edilizie, energia)
- **5%**: aliquota super-ridotta (basilico, origano, rosmarino, prestazioni socio-sanitarie)
- **4%**: aliquota minima (alimentari di prima necessità: pane, latte, frutta, verdura; libri; prima casa)

### 1.3 Operazioni ai fini IVA
- **Imponibili**: soggette a IVA (vendite nazionali ordinarie)
- **Non imponibili**: senza IVA ma con obbligo di fatturazione (esportazioni, cessioni intra-UE)
- **Esenti**: senza IVA per legge (servizi sanitari, finanziari, assicurativi, locazioni)
- **Escluse/fuori campo**: non rientrano nel campo IVA (interessi di mora, risarcimenti)

### 1.4 Conti IVA e Liquidazione

**Conti utilizzati:**
- **IVA a credito** (conto patrimoniale attivo): IVA pagata sugli acquisti
- **IVA a debito** (conto patrimoniale passivo): IVA addebitata sulle vendite
- **Erario c/IVA**: saldo della liquidazione periodica

**Liquidazione mensile/trimestrale (es. liquidazione con IVA a debito > IVA a credito):**
```
IVA a debito                   15.000 | IVA a credito              10.000
                                      | Erario c/IVA                5.000
```

**Versamento:**
```
Erario c/IVA                    5.000 | Banca c/c                   5.000
```

---

## 2. Ciclo Acquisti

### 2.1 Acquisto Ordinario di Merci

**Acquisto merci per €20.000 + IVA 22%:**
```
Merci c/acquisti               20.000 |
IVA a credito                   4.400 |
                                      | Debiti v/fornitori          24.400
```

**Pagamento fornitore:**
```
Debiti v/fornitori             24.400 | Banca c/c                  24.400
```

### 2.2 Anticipi a Fornitori (3 momenti contabili)

**Momento 1 — Versamento anticipo (es. €5.000 + IVA 22%):**
```
Anticipi a fornitori            5.000 |
IVA a credito                   1.100 |
                                      | Banca c/c                   6.100
```

**Momento 2 — Ricevimento fattura definitiva (merce €20.000 + IVA 22% = €24.400, meno anticipo):**
```
Merci c/acquisti               20.000 |
IVA a credito                   3.300 |
                                      | Anticipi a fornitori         5.000
                                      | IVA a credito (storno)       1.100
                                      | Debiti v/fornitori          17.200
```
Nota: l'IVA già versata sull'anticipo viene stornata perché la fattura definitiva contiene l'IVA sull'intero importo. Il saldo IVA a credito netto è €4.400 (3.300 + 1.100 iniziale - 1.100 storno = 3.300, ma complessivamente 1.100 + 3.300 = 4.400 totale).

**Momento 3 — Pagamento saldo:**
```
Debiti v/fornitori             17.200 | Banca c/c                  17.200
```

### 2.3 Resi su Acquisti

**Reso merce per difetto, nota di credito €2.000 + IVA 22%:**
```
Debiti v/fornitori              2.440 | Resi su acquisti             2.000
                                      | IVA a credito (storno)         440
```

### 2.4 Abbuoni su Acquisti

**Abbuono per difformità qualitativa €500 + IVA 22%:**
```
Debiti v/fornitori                610 | Abbuoni attivi                 500
                                      | IVA a credito (storno)         110
```

### 2.5 Sconti

**Sconti incondizionati**: inseriti direttamente in fattura, riducono la base imponibile → non richiedono scrittura separata (il costo è già al netto).

**Sconti condizionati (es. per raggiungimento volume):**
```
Debiti v/fornitori              1.220 | Sconti attivi su acquisti    1.000
                                      | IVA a credito (storno)         220
```

**Sconti cassa (per pagamento anticipato) — senza IVA:**
```
Debiti v/fornitori             24.400 | Banca c/c                  23.900
                                      | Sconti di cassa attivi         500
```
Nota: lo sconto cassa **non** rileva ai fini IVA (non emessa nota di variazione), perché è un provento finanziario.

---

## 3. Ciclo Vendite

### 3.1 Vendita Ordinaria

**Vendita merci per €30.000 + IVA 22%:**
```
Crediti v/clienti              36.600 | Ricavi di vendita           30.000
                                      | IVA a debito                 6.600
```

**Incasso:**
```
Banca c/c                     36.600 | Crediti v/clienti           36.600
```

### 3.2 Anticipi da Clienti (3 momenti contabili)

**Momento 1 — Incasso anticipo (€8.000 + IVA 22%):**
```
Banca c/c                      9.760 | Anticipi da clienti          8.000
                                      | IVA a debito                 1.760
```

**Momento 2 — Emissione fattura definitiva (€30.000 + IVA 22%, meno anticipo):**
```
Crediti v/clienti              24.640 | Ricavi di vendita           30.000
Anticipi da clienti             8.000 |
IVA a debito (storno)           1.760 | IVA a debito                 6.600
```
(Saldo IVA a debito netto: 6.600 - 1.760 + 1.760 iniziale = 6.600 totale)

**Momento 3 — Incasso saldo:**
```
Banca c/c                     24.640 | Crediti v/clienti           24.640
```

### 3.3 Resi su Vendite

**Nota di credito per reso €3.000 + IVA 22%:**
```
Resi su vendite                 3.000 | Crediti v/clienti            3.660
IVA a debito (storno)             660 |
```

### 3.4 Abbuoni e Sconti su Vendite

**Abbuono passivo €1.000 + IVA 22%:**
```
Abbuoni passivi                 1.000 | Crediti v/clienti            1.220
IVA a debito (storno)             220 |
```

**Sconto cassa concesso (senza nota di variazione IVA):**
```
Sconti di cassa passivi           500 | Crediti v/clienti              500
```

---

## 4. Costo del Lavoro Dipendente

### 4.1 Le 5 Componenti del Costo del Lavoro

Il costo del lavoro per l'impresa comprende:
1. **Retribuzione lorda**: salario/stipendio base + indennità + straordinari + premi
2. **Contributi previdenziali a carico del datore** (INPS, INAIL): circa 30-32% della retribuzione lorda
3. **TFR** (Trattamento di Fine Rapporto): accantonamento annuo
4. **Altri costi**: mensa, benefit, formazione obbligatoria
5. **IRAP** (quota lavoro): componente regionale

### 4.2 Busta Paga — Struttura e Scritture

**Schema sintetico:**
```
Retribuzione lorda                           €3.000
- Contributi INPS a carico lavoratore (9,19%)  -€276
= Imponibile fiscale                         €2.724
- IRPEF lorda                                 -€XXX
+ Detrazioni                                  +€XXX
= IRPEF netta (ritenuta)                      -€450
= Retribuzione netta                         €1.998
```

### 4.3 Scritture del Personale

**Rilevazione retribuzioni mensili (es. retribuzione lorda €100.000 per tutti i dipendenti):**
```
Salari e stipendi             100.000 | Debiti v/dipendenti         69.000
                                      | INPS c/contributi lavoratore  9.190
                                      | Erario c/ritenute IRPEF     21.810
```

**Contributi previdenziali a carico dell'azienda (es. 31%):**
```
Contributi previdenziali       31.000 | INPS c/contributi azienda   31.000
```

**Pagamento stipendi netti:**
```
Debiti v/dipendenti            69.000 | Banca c/c                  69.000
```

**Versamento contributi INPS (lavoratore + azienda):**
```
INPS c/contributi lavoratore    9.190 | Banca c/c                  40.190
INPS c/contributi azienda      31.000 |
```

**Versamento ritenute IRPEF:**
```
Erario c/ritenute IRPEF        21.810 | Banca c/c                  21.810
```

### 4.4 TFR — Trattamento di Fine Rapporto (art. 2120 c.c.)

**Calcolo annuale TFR:**
```
Quota capitale = Retribuzione annua lorda / 13,5
Rivalutazione fondo TFR = Fondo TFR al 31/12 precedente × (1,5% + 75% × indice ISTAT)
Imposta sostitutiva rivalutazione = Rivalutazione × 17%
```

**Esempio con retribuzione lorda annua €39.000 e fondo TFR precedente €40.000, indice ISTAT 2%:**

Quota capitale: 39.000 / 13,5 = €2.888,89
Rivalutazione: 40.000 × (0,015 + 0,75 × 0,02) = 40.000 × 0,03 = €1.200
Imposta sostitutiva: 1.200 × 17% = €204

**Accantonamento quota capitale:**
```
TFR (costo)                    2.889 | Fondo TFR                    2.889
```

**Rivalutazione fondo TFR:**
```
Rivalutazione TFR (onere fin.)  1.200 | Fondo TFR                    1.200
```

**Imposta sostitutiva 17% sulla rivalutazione:**
```
Fondo TFR                        204 | Erario c/imposta sost. TFR      204
```

**Saldo fondo TFR a fine esercizio:** 40.000 + 2.889 + 1.200 - 204 = **€43.885**

**Erogazione TFR al dipendente cessato (es. €15.000):**
```
Fondo TFR                     15.000 | Banca c/c                  15.000
```

---

## 5. Finanziamento Corrente

### 5.1 Conto Corrente Bancario

**Interessi passivi su c/c (liquidazione trimestrale):**
```
Interessi passivi               1.200 | Banca c/c                   1.200
```

**Interessi attivi su c/c:**
```
Banca c/c                        150 | Interessi attivi                150
```

### 5.2 Apertura di Credito in Conto Corrente (Fido)

Non genera scritture specifiche all'atto della concessione. Gli utilizzi si rilevano come normali movimenti bancari. Gli interessi passivi si calcolano solo sulle somme effettivamente utilizzate.

**Commissione sul fido non utilizzato:**
```
Oneri bancari                     500 | Banca c/c                     500
```

### 5.3 Cambiali

**Emissione di cambiale (pagherò) a estinzione debito fornitore:**
```
Debiti v/fornitori             10.000 | Cambiali passive             10.000
```

**Pagamento cambiale alla scadenza:**
```
Cambiali passive               10.000 | Banca c/c                  10.000
```

**Ricezione cambiale da cliente:**
```
Cambiali attive                10.000 | Crediti v/clienti           10.000
```

### 5.4 Sconto Cambiario

L'impresa anticipa l'incasso di una cambiale non ancora scaduta presentandola alla banca, che anticipa l'importo al netto degli interessi di sconto.

**Sconto pro-solvendo** (l'impresa resta garante; se il debitore non paga, la banca si rivale sull'impresa):

Presentazione allo sconto (cambiale €10.000, sconto €300):
```
Banca c/c                      9.700 | Cambiali allo sconto        10.000
Oneri finanziari di sconto        300 |
```
Il conto **Cambiali allo sconto** è un conto d'ordine (o un conto patrimoniale transitorio) che evidenzia il rischio di regresso.

All'incasso da parte della banca (buon fine):
```
Cambiali allo sconto           10.000 | Cambiali attive             10.000
```

In caso di insoluto (mancato pagamento del debitore):
```
Cambiali allo sconto           10.000 | Banca c/c                  10.000
Crediti v/clienti              10.000 | Cambiali attive             10.000
```
(La banca addebita l'importo; il credito torna verso il cliente originario)

**Sconto pro-soluto** (la banca assume il rischio di insolvenza; l'impresa è liberata):

Presentazione allo sconto (cambiale €10.000, sconto €500 — più alto per il rischio assunto dalla banca):
```
Banca c/c                      9.500 | Cambiali attive             10.000
Oneri finanziari di sconto        500 |
```
Il credito è definitivamente trasferito: nessun rischio di regresso, nessun conto d'ordine.

---

## 6. Acquisto e Cessione di Immobilizzazioni

### 6.1 Acquisto Immobilizzazione

**Acquisto macchinario €50.000 + IVA 22%:**
```
Macchinari                     50.000 |
IVA a credito                  11.000 |
                                      | Debiti v/fornitori          61.000
```

### 6.2 Cessione Immobilizzazione

**Cessione macchinario (costo storico €50.000, fondo ammortamento €35.000, prezzo vendita €20.000 + IVA):**

Valore netto contabile: 50.000 - 35.000 = €15.000
Prezzo di vendita: €20.000 → **Plusvalenza** = 20.000 - 15.000 = €5.000

```
Crediti v/clienti              24.400 | Macchinari                  50.000
Fondo ammortamento macchinari  35.000 | IVA a debito                 4.400
                                      | Plusvalenza da alienazione    5.000
```

Se il prezzo fosse stato €12.000 → **Minusvalenza** = 15.000 - 12.000 = €3.000
```
Crediti v/clienti              14.640 | Macchinari                  50.000
Fondo ammortamento macchinari  35.000 | IVA a debito                 2.640
Minusvalenza da alienazione     3.000 |
```
