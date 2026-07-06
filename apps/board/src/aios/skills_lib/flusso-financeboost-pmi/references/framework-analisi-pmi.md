# Framework di Analisi Finanziaria per PMI Italiane

Questo documento definisce il framework diagnostico utilizzato dalla skill `flusso-financeboost-pmi` per analizzare lo stato di salute finanziaria di una PMI italiana (5-50 dipendenti). Ogni KPI include formula, significato, soglie di alert e modalita di calcolo dal bilancio civilistico italiano.

---

## 1. AREA REDDITIVITA

### 1.1 ROE — Return on Equity

- **Formula**: `Utile netto / Patrimonio netto x 100`
- **Dal bilancio civilistico**: Utile (perdita) d'esercizio (voce 21 CE) / Totale Patrimonio netto (voce A SP passivo)
- **Significato**: rendimento del capitale proprio investito dai soci. E il KPI piu importante per il titolare perche risponde alla domanda "quanto rende il mio investimento?"
- **Sano**: > 10% (superiore al rendimento di un investimento alternativo risk-free + premio rischio)
- **Alert**: 5-10% (rendimento modesto, valutare se il rischio imprenditoriale e adeguatamente remunerato)
- **Critico**: < 5% o negativo (il titolare guadagnerebbe di piu con un BTP)

### 1.2 ROI — Return on Investment

- **Formula**: `Reddito operativo (EBIT) / Capitale investito netto x 100`
- **Dal bilancio civilistico**: Differenza tra valore e costi della produzione (A-B CE) / Totale Attivo - Debiti commerciali a breve
- **Significato**: rendimento del capitale investito nell'attivita operativa, indipendentemente da come e finanziato
- **Sano**: > 8%
- **Alert**: 4-8%
- **Critico**: < 4% o negativo

### 1.3 ROS — Return on Sales

- **Formula**: `Reddito operativo (EBIT) / Ricavi netti x 100`
- **Dal bilancio civilistico**: (A-B CE) / Ricavi delle vendite e prestazioni (voce A.1 CE)
- **Significato**: quanti centesimi di utile operativo per ogni euro di fatturato
- **Sano**: > 8% (variabile per settore — manifatturiero 5-8%, servizi 10-15%, commercio 2-5%)
- **Alert**: 3-8%
- **Critico**: < 3% o negativo

### 1.4 EBITDA Margin

- **Formula**: `EBITDA / Ricavi netti x 100`
- **Dal bilancio civilistico**: (A-B CE + Ammortamenti voce B.10 + Svalutazioni voce B.12) / A.1 CE
- **Significato**: marginalita operativa lorda, prima di ammortamenti e politiche contabili
- **Sano**: > 12%
- **Alert**: 6-12%
- **Critico**: < 6%

### 1.5 Utile netto / Fatturato

- **Formula**: `Utile netto / Ricavi netti x 100`
- **Dal bilancio civilistico**: voce 21 CE / voce A.1 CE
- **Significato**: margine netto finale dopo tutte le componenti (operative, finanziarie, straordinarie, fiscali)
- **Sano**: > 5%
- **Alert**: 1-5%
- **Critico**: < 1% o negativo

---

## 2. AREA LIQUIDITA

### 2.1 Current Ratio (Indice di liquidita corrente)

- **Formula**: `Attivo circolante / Passivita correnti`
- **Dal bilancio civilistico**: Totale attivo circolante (voce C SP attivo) / Debiti esigibili entro l'esercizio successivo (voce D SP passivo, quota entro)
- **Significato**: capacita di far fronte ai debiti a breve con le risorse a breve
- **Sano**: > 1.5
- **Alert**: 1.0 - 1.5
- **Critico**: < 1.0 (l'azienda non riesce a coprire i debiti a breve con l'attivo circolante)

### 2.2 Quick Ratio (Indice di liquidita immediata / Acid Test)

- **Formula**: `(Attivo circolante - Rimanenze) / Passivita correnti`
- **Dal bilancio civilistico**: (C SP - C.I Rimanenze) / Debiti entro
- **Significato**: come il current ratio ma esclude le rimanenze (meno liquide)
- **Sano**: > 1.0
- **Alert**: 0.5 - 1.0
- **Critico**: < 0.5

### 2.3 CCN — Capitale Circolante Netto

- **Formula**: `Attivo circolante - Passivita correnti`
- **Dal bilancio civilistico**: C SP attivo - Debiti entro esercizio (voce D entro)
- **Significato**: margine di sicurezza finanziaria a breve termine, in valore assoluto
- **Sano**: positivo e crescente
- **Alert**: positivo ma in calo
- **Critico**: negativo (deficit finanziario a breve)

### 2.4 CCC — Cash Conversion Cycle (Ciclo di conversione del contante)

- **Formula**: `Giorni crediti + Giorni magazzino - Giorni debiti`
- **Significato**: quanti giorni passano dal pagamento ai fornitori all'incasso dai clienti. Piu e basso, meglio e.
- **Sano**: < 60 giorni
- **Alert**: 60-120 giorni
- **Critico**: > 120 giorni

### 2.5 Giorni medi incasso crediti (DSO)

- **Formula**: `Crediti commerciali / Ricavi netti x 365`
- **Dal bilancio civilistico**: Crediti verso clienti (voce C.II.1 SP) / A.1 CE x 365
- **Sano**: < 60 giorni (Italia ha media alta: 67 giorni nel 2024)
- **Alert**: 60-90 giorni
- **Critico**: > 90 giorni

### 2.6 Giorni medi pagamento debiti (DPO)

- **Formula**: `Debiti commerciali / Acquisti x 365`
- **Dal bilancio civilistico**: Debiti verso fornitori (voce D.7 SP) / (B.6 + B.7 CE) x 365
- **Sano**: 30-60 giorni (equilibrato)
- **Alert**: > 90 giorni (potrebbe indicare tensione di cassa) o < 15 giorni (si paga troppo presto)
- **Critico**: > 120 giorni (rischio tensione con fornitori)

### 2.7 Giorni medi giacenza magazzino (DIO)

- **Formula**: `Rimanenze / Costo del venduto x 365`
- **Dal bilancio civilistico**: C.I SP / (B.6 + B.7 + B.11 variazione rimanenze CE) x 365
- **Sano**: < 45 giorni (variabile per settore)
- **Alert**: 45-90 giorni
- **Critico**: > 90 giorni (capitale immobilizzato, rischio obsolescenza)

---

## 3. AREA SOLIDITA

### 3.1 D/E — Debt to Equity

- **Formula**: `Debiti finanziari / Patrimonio netto`
- **Dal bilancio civilistico**: (Debiti verso banche voce D.4 + Obbligazioni D.1 + D.2) / Totale A SP passivo
- **Significato**: quanto debito finanziario per ogni euro di patrimonio netto
- **Sano**: < 1.5
- **Alert**: 1.5 - 3.0
- **Critico**: > 3.0 (sovra-indebitamento)

### 3.2 Leverage finanziario

- **Formula**: `Totale Attivo / Patrimonio netto`
- **Dal bilancio civilistico**: Totale attivo SP / Totale A SP passivo
- **Significato**: moltiplicatore del capitale proprio. Nella scomposizione Du Pont, amplifica ROI in ROE.
- **Sano**: < 3.0
- **Alert**: 3.0 - 5.0
- **Critico**: > 5.0

### 3.3 Autonomia finanziaria

- **Formula**: `Patrimonio netto / Totale fonti x 100`
- **Dal bilancio civilistico**: A SP passivo / Totale SP passivo x 100
- **Significato**: percentuale di finanziamento con mezzi propri
- **Sano**: > 30%
- **Alert**: 15-30%
- **Critico**: < 15%

### 3.4 Copertura oneri finanziari

- **Formula**: `EBIT / Oneri finanziari`
- **Dal bilancio civilistico**: (A-B CE) / C.17 CE (interessi e altri oneri finanziari)
- **Significato**: quante volte il reddito operativo copre gli interessi passivi (Interest Coverage Ratio)
- **Sano**: > 3.0
- **Alert**: 1.5 - 3.0
- **Critico**: < 1.5 (l'azienda fatica a pagare gli interessi col reddito operativo)

---

## 4. AREA EFFICIENZA

### 4.1 Rotazione capitale investito (Asset Turnover)

- **Formula**: `Ricavi netti / Capitale investito netto`
- **Dal bilancio civilistico**: A.1 CE / (Totale attivo - Debiti commerciali)
- **Significato**: quanti euro di fatturato genera ogni euro investito. Nella scomposizione Du Pont: ROI = ROS x Rotazione.
- **Sano**: > 1.5 (servizi) o > 0.8 (manifatturiero capital-intensive)
- **Alert**: 0.5 - 1.0
- **Critico**: < 0.5

### 4.2 Produttivita per addetto

- **Formula**: `Valore Aggiunto / Numero dipendenti`
- **Dal bilancio civilistico**: (Valore produzione A CE - Costi materie B.6 - Costi servizi B.7 - Godimento beni terzi B.8) / N. dipendenti medio
- **Significato**: quanto valore crea ciascun dipendente
- **Sano**: > 60.000 EUR/anno (PMI italiana media)
- **Alert**: 40.000 - 60.000 EUR/anno
- **Critico**: < 40.000 EUR/anno

### 4.3 Incidenza costo del lavoro su VA

- **Formula**: `Costo del personale / Valore Aggiunto x 100`
- **Dal bilancio civilistico**: B.9 CE / Valore Aggiunto x 100
- **Significato**: quanto del valore creato viene assorbito dal costo del lavoro
- **Sano**: < 60%
- **Alert**: 60-75%
- **Critico**: > 75% (il lavoro assorbe quasi tutto il valore aggiunto, non resta margine per ammortamenti, oneri finanziari e utile)

---

## 5. AREA CRESCITA

### 5.1 CAGR Fatturato

- **Formula**: `(Fatturato anno N / Fatturato anno N-2)^(1/2) - 1` (su 3 anni)
- **Significato**: tasso di crescita annuo composto del fatturato
- **Sano**: > inflazione + 2-3% (crescita reale)
- **Alert**: 0% - inflazione (crescita nominale ma non reale)
- **Critico**: negativo (fatturato in calo)

### 5.2 Trend margini

- **Significato**: evoluzione dei margini (EBITDA margin, ROS, utile netto/fatturato) nel triennio
- **Sano**: margini stabili o in crescita
- **Alert**: margini in lieve calo (< 2 punti percentuali in 3 anni)
- **Critico**: margini in forte calo (> 2 punti in 3 anni)

### 5.3 Rapporto Investimenti / Ammortamenti

- **Formula**: `Incrementi immobilizzazioni / Ammortamenti dell'esercizio`
- **Dal bilancio civilistico**: variazione immobilizzazioni (da nota integrativa o differenza SP + B.10 CE) / B.10 CE
- **Significato**: se > 1, l'azienda investe piu di quanto ammortizza (rinnovo). Se < 1, il patrimonio produttivo si sta deteriorando.
- **Sano**: > 1.2
- **Alert**: 0.8 - 1.2
- **Critico**: < 0.8 (sotto-investimento cronico)

---

## Scomposizione Du Pont del ROE

La scomposizione Du Pont e il cuore dell'analisi perche collega tutte le aree:

```
ROE = ROS x Rotazione x Leverage

dove:
  ROS = EBIT / Ricavi netti                    (redditivita delle vendite)
  Rotazione = Ricavi netti / Capitale investito (efficienza degli investimenti)
  Leverage = Capitale investito / PN            (struttura finanziaria)
```

### Interpretazione pratica per il titolare PMI

- **ROE basso per ROS basso**: "Guadagni poco su ogni vendita. Il problema e nei margini: costi troppo alti o prezzi troppo bassi."
- **ROE basso per Rotazione bassa**: "Hai troppo capitale investito rispetto al fatturato che generi. Magazzino gonfio? Crediti troppo lunghi? Immobilizzazioni sottoutilizzate?"
- **ROE basso per Leverage basso**: "L'azienda e poco indebitata — il che e sano, ma significa che non stai usando la leva finanziaria per amplificare il rendimento. Ha senso solo se ROI > costo del debito."
- **ROE alto per Leverage alto**: "ATTENZIONE: il ROE sembra buono, ma e gonfiato dal debito. Se il ROI scende sotto il costo del debito, il leverage diventa distruttivo."

### Esempio numerico

```
Azienda: fatturato 2M, EBIT 160K, Attivo 1.5M, PN 500K, Utile 80K

ROS = 160K / 2M = 8%
Rotazione = 2M / 1.5M = 1.33
Leverage = 1.5M / 500K = 3.0

ROE (approssimato) = 8% x 1.33 x 3.0 = 32% (lordo, prima di imposte e gestione finanziaria)
ROE (effettivo) = 80K / 500K = 16% (netto)

Differenza: oneri finanziari e imposte erodono meta del rendimento operativo.
```

---

## CCN e CCC: Calcolo e Leve di Miglioramento

### Calcolo da bilancio italiano

```
CCN = Attivo circolante (C SP) - Debiti a breve (D entro SP)

CCC = DSO + DIO - DPO
    = (Crediti clienti / Ricavi x 365)
    + (Rimanenze / Costo venduto x 365)
    - (Debiti fornitori / Acquisti x 365)
```

### Leve di miglioramento del CCC

1. **Ridurre DSO** (giorni crediti):
   - Fatturare immediatamente alla consegna/prestazione
   - Offrire sconto per pagamento anticipato (es. 2% a 10 giorni)
   - Sollecito sistematico a 30-60-90 giorni
   - Valutare factoring pro-soluto per clienti piu lenti

2. **Ridurre DIO** (giorni magazzino):
   - Analisi ABC delle giacenze: eliminare slow-movers
   - Ridurre lotti di acquisto, aumentare frequenza ordini
   - Just-in-time dove possibile
   - Svalutare/liquidare obsoleti

3. **Aumentare DPO** (giorni debiti) — con cautela:
   - Negoziare termini piu lunghi coi fornitori principali
   - NON ritardare i pagamenti unilateralmente (rischio forniture e reputazione)
   - Valutare reverse factoring/supply chain finance

### Impatto: ogni giorno di CCC in meno libera

```
Liquidita liberata = Fatturato giornaliero x giorni CCC ridotti
Es. Fatturato 2M → fatturato giornaliero ~5.500 EUR
    Riduzione CCC di 15 giorni → ~82.500 EUR liberati
```
