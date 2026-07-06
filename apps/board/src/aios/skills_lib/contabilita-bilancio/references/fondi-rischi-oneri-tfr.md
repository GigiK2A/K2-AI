# Fondi per Rischi e Oneri, TFR e Scritture di Assestamento

## 1. Fondi per Rischi e Oneri (art. 2424-bis, comma 3, c.c.; OIC 31)

### 1.1 Definizione e Natura

I fondi per rischi e oneri rappresentano passività di natura determinata, certe o probabili, con data di sopravvenienza o ammontare indeterminati. Sono iscritti nella macro-classe B del passivo dello Stato Patrimoniale.

### 1.2 Classificazione secondo 4 Criteri

Per distinguere fondi rischi, fondi oneri e debiti, si analizzano 4 variabili:

| Criterio | Fondi Rischi | Fondi Oneri | Debiti |
|---|---|---|---|
| **1. Natura** | Determinata | Determinata | Determinata |
| **2. Esistenza** | **Probabile** | **Certa** | **Certa** |
| **3. Ammontare** | Stimato | **Stimato** | Determinato |
| **4. Data sopravvenienza** | Indeterminata | Indeterminata | Determinata |

**Fondi Rischi**: passività la cui esistenza stessa è incerta (probabile ma non certa). Es.: fondo cause legali in corso, fondo garanzia prodotti.

**Fondi Oneri**: passività la cui esistenza è certa, ma l'ammontare o la data di manifestazione sono incerti. Es.: fondo manutenzione ciclica, fondo per ristrutturazione deliberata.

**Debiti**: passività certe nell'esistenza, nell'ammontare e nella data di scadenza. Non sono fondi.

### 1.3 Condizioni per l'Iscrizione (OIC 31)

Un fondo va iscritto quando sussistono **tutte** le seguenti condizioni:
1. Esiste un'obbligazione attuale (legale o implicita) derivante da un evento passato
2. È **probabile** che si verificherà un'uscita di risorse economiche
3. L'ammontare è stimabile in modo **attendibile**

Se l'evento è solo **possibile** (non probabile): nessuna iscrizione, solo informativa in Nota Integrativa.
Se l'evento è **remoto**: nessuna iscrizione né informativa.

### 1.4 Schema SP — Posizionamento

**Passivo — B) Fondi per rischi e oneri:**
- B.1) Per trattamento di quiescenza e obblighi simili
- B.2) Per imposte, anche differite
- B.3) Strumenti finanziari derivati passivi
- B.4) Altri

**Passivo — C) Trattamento di fine rapporto di lavoro subordinato** (voce autonoma, non dentro i fondi)

### 1.5 Scritture Contabili dei Fondi

**Accantonamento a fondo rischi per causa legale (€30.000 stimati):**
```
Accantonamento per rischi      30.000 | Fondo rischi cause legali    30.000
```
(Il costo va in CE, voce B.12 o B.13; il fondo in SP passivo B.4)

**Utilizzo del fondo al verificarsi dell'evento (pagamento sentenza €28.000):**
```
Fondo rischi cause legali      28.000 | Banca c/c                  28.000
```

**Se l'esborso eccede il fondo (sentenza €35.000, fondo €30.000):**
```
Fondo rischi cause legali      30.000 | Banca c/c                  35.000
Sopravvenienze passive          5.000 |
```

**Se il fondo eccede l'esborso (sentenza €22.000, fondo €30.000):**
```
Fondo rischi cause legali      22.000 | Banca c/c                  22.000
Fondo rischi cause legali       8.000 | Sopravvenienze attive        8.000
```

**Se il rischio viene meno (causa vinta):**
```
Fondo rischi cause legali      30.000 | Sopravvenienze attive       30.000
```

---

## 2. TFR — Trattamento di Fine Rapporto (art. 2120 c.c.)

### 2.1 Natura Giuridica

Il TFR è una forma di **retribuzione differita** che spetta al lavoratore dipendente alla cessazione del rapporto di lavoro, qualunque ne sia la causa. In bilancio è classificato come voce autonoma del passivo (SP — C) Trattamento di fine rapporto di lavoro subordinato).

Non è un fondo rischi/oneri perché il debito è **certo** nell'esistenza; è solo incerto nella data di erogazione e nell'ammontare finale (dipende dalla retribuzione futura e dalla rivalutazione ISTAT).

### 2.2 Calcolo Annuale

**Quota capitale annua:**
```
Quota TFR = Retribuzione annua utile / 13,5
```
La retribuzione utile comprende tutte le somme corrisposte a titolo non occasionale (compresi straordinari abituali, mensilità aggiuntive), escluse le somme occasionali.

**Rivalutazione del fondo preesistente:**
```
Rivalutazione = Fondo TFR al 31/12 precedente × Coefficiente di rivalutazione
Coefficiente = 1,5% fisso + 75% × variazione indice ISTAT prezzi al consumo
```

**Imposta sostitutiva sulla rivalutazione:**
```
Imposta sostitutiva = Rivalutazione × 17%
```
L'imposta sostitutiva riduce il fondo TFR (non il costo dell'esercizio).

### 2.3 Esempio Numerico Completo

**Dati:**
- Retribuzione annua lorda: €36.000
- Fondo TFR al 31/12 anno precedente: €50.000
- Variazione indice ISTAT: 1,8%

**Calcoli:**
- Quota capitale: 36.000 / 13,5 = **€2.666,67**
- Coefficiente rivalutazione: 1,5% + 75% × 1,8% = 1,5% + 1,35% = **2,85%**
- Rivalutazione: 50.000 × 2,85% = **€1.425,00**
- Imposta sostitutiva: 1.425 × 17% = **€242,25**

**Scritture:**
```
31/12 TFR (costo del personale)    2.666,67 | Fondo TFR                2.666,67
31/12 Rivalutazione TFR (on. fin.)  1.425,00 | Fondo TFR                1.425,00
31/12 Fondo TFR                       242,25 | Erario c/imp. sost. TFR    242,25
```

**Fondo TFR a fine esercizio:** 50.000 + 2.666,67 + 1.425 - 242,25 = **€53.849,42**

### 2.4 Destinazione del TFR (post Riforma 2007)

Per le imprese con **almeno 50 dipendenti**, il TFR maturando (dal 2007) va versato al fondo pensione scelto dal lavoratore oppure al **Fondo di Tesoreria INPS**.

In tal caso, la scrittura cambia:
```
TFR (costo del personale)      2.667 | Debiti v/fondo pensione      2.667
```
oppure:
```
TFR (costo del personale)      2.667 | Debiti v/INPS Fondo Tesoreria 2.667
```

Il fondo TFR in bilancio contiene solo la quota maturata ante-riforma (o per imprese < 50 dipendenti).

---

## 3. Scritture di Assestamento — Panoramica Completa

### 3.1 Ammortamenti

**Principio**: ripartizione del costo di un'immobilizzazione lungo la sua vita utile stimata.

**Ammortamento impianto (costo €100.000, vita utile 10 anni, aliquota 10%):**
```
31/12 Ammortamento impianti   10.000 | Fondo amm.to impianti      10.000
```

Il **fondo ammortamento** è un conto rettificativo dell'attivo (SP attivo, in deduzione della voce di immobilizzazione).

**Ammortamento primo esercizio** (prassi fiscale: dimezzamento aliquota): 10% / 2 = 5%
```
31/12 Ammortamento impianti    5.000 | Fondo amm.to impianti       5.000
```

### 3.2 Svalutazione Crediti

**Accantonamento al fondo svalutazione crediti (stima insolvenza 3% su crediti €500.000):**
```
31/12 Svalutazione crediti    15.000 | Fondo svalutazione crediti  15.000
```

**Perdita su crediti conclamata (cliente fallito, credito €8.000, coperto da fondo per €5.000):**
```
Fondo svalutazione crediti     5.000 | Crediti v/clienti            8.000
Perdite su crediti             3.000 |
```

### 3.3 Ratei

**Rateo attivo** — provento di competenza dell'esercizio non ancora incassato/fatturato:

Es.: interessi attivi su titoli (cedola semestrale €6.000 incassata il 1° aprile; quota di competenza 1° luglio - 31 dicembre = 6 mesi su 12 = €3.000):
```
31/12 Ratei attivi             3.000 | Interessi attivi su titoli   3.000
```

**Rateo passivo** — costo di competenza dell'esercizio non ancora pagato/fatturato:

Es.: interessi passivi su mutuo (rata semestrale €4.000 pagata il 1° marzo; quota di competenza 1° settembre - 31 dicembre = 4 mesi su 6 = €2.667):
```
31/12 Interessi passivi        2.667 | Ratei passivi                2.667
```

### 3.4 Risconti

**Risconto attivo** — costo già pagato/fatturato ma di competenza futura:

Es.: assicurazione annuale €12.000 pagata il 1° ottobre (competenza: 3 mesi esercizio in corso, 9 mesi esercizio successivo):
```
31/12 Risconti attivi          9.000 | Premi di assicurazione       9.000
```
(Si storna dal costo la quota non di competenza: 9/12 × 12.000 = 9.000)

**Risconto passivo** — ricavo già incassato/fatturato ma di competenza futura:

Es.: canone di locazione attivo annuale €24.000 incassato il 1° novembre (competenza: 2 mesi esercizio in corso, 10 mesi esercizio successivo):
```
31/12 Fitti attivi            20.000 | Risconti passivi            20.000
```
(Si storna dal ricavo la quota non di competenza: 10/12 × 24.000 = 20.000)

### 3.5 Rimanenze di Magazzino

**Rilevazione finale rimanenze (inventario fisico al 31/12: €80.000):**
```
31/12 Rimanenze finali merci  80.000 | Merci c/rimanenze finali    80.000
```
(Le rimanenze finali riducono il costo del venduto nel CE e figurano nell'attivo circolante dello SP)

**All'apertura dell'esercizio successivo, le rimanenze iniziali diventano costo:**
```
01/01 Merci c/rimanenze iniziali 80.000 | Rimanenze iniziali merci  80.000
```

### 3.6 Riepilogo Tipologie Assestamento

| Tipo | Operazione | Effetto su CE | Effetto su SP |
|---|---|---|---|
| Ammortamento | Congettura | + Costo | + Fondo (rettifica attivo) |
| Svalutazione crediti | Stima | + Costo | + Fondo (rettifica attivo) |
| Accantonamento fondi | Stima | + Costo | + Fondo rischi/oneri (passivo) |
| TFR | Calcolo | + Costo personale | + Fondo TFR (passivo) |
| Rateo attivo | Integrazione | + Ricavo | + Rateo attivo (attivo) |
| Rateo passivo | Integrazione | + Costo | + Rateo passivo (passivo) |
| Risconto attivo | Rettifica | - Costo | + Risconto attivo (attivo) |
| Risconto passivo | Rettifica | - Ricavo | + Risconto passivo (passivo) |
| Rimanenze finali | Rettifica | - Costo venduto | + Rimanenze (attivo circolante) |
