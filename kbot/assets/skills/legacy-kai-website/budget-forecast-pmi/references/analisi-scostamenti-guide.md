# Guida all'analisi degli scostamenti per PMI

## Introduzione

L'analisi degli scostamenti (variance analysis) e lo strumento che trasforma il budget da esercizio statico a strumento di gestione dinamico. Ogni mese si confronta il consuntivo con il budget e si indaga il perche delle differenze, per prendere decisioni correttive.

Per le PMI senza controller, il processo deve essere semplice, rapido (30 minuti al mese) e orientato all'azione.

---

## 1. Framework scostamenti ricavi

### Scomposizione dello scostamento ricavi totale

```
Scostamento ricavi = Ricavi effettivi - Ricavi budget
```

Si scompone in:

**Scostamento di prezzo**:
```
= (Prezzo effettivo - Prezzo budget) x Quantita effettiva
```
Misura: abbiamo venduto a un prezzo diverso da quello previsto?

**Scostamento di quantita (volume)**:
```
= (Quantita effettiva - Quantita budget) x Prezzo budget
```
Misura: abbiamo venduto piu o meno unita del previsto?

### Esempio pratico

Budget: 1.000 pezzi a 50 EUR = 50.000 EUR
Consuntivo: 1.100 pezzi a 47 EUR = 51.700 EUR

- Scostamento totale: +1.700 EUR (favorevole)
- Scostamento prezzo: (47 - 50) x 1.100 = -3.300 EUR (sfavorevole: abbiamo abbassato il prezzo)
- Scostamento quantita: (1.100 - 1.000) x 50 = +5.000 EUR (favorevole: abbiamo venduto di piu)

Interpretazione: abbiamo venduto di piu perche abbiamo fatto sconti. Il fatturato e cresciuto, ma il margine unitario e calato. Bisogna verificare se conviene.

---

## 2. Framework scostamenti costi

### Scomposizione scostamento costi variabili

**Scostamento di prezzo (spesa)**:
```
= (Prezzo unitario effettivo - Prezzo unitario budget) x Quantita effettiva
```
Misura: abbiamo pagato di piu o di meno per le risorse?

**Scostamento di efficienza (impiego)**:
```
= (Quantita effettiva - Quantita standard per output effettivo) x Prezzo budget
```
Misura: abbiamo usato piu o meno risorse del previsto per produrre?

### Esempio pratico — Materie prime

Budget: 500 kg a 10 EUR/kg per produrre 1.000 pezzi (standard: 0.5 kg/pezzo)
Consuntivo: 580 kg a 10.50 EUR/kg per produrre 1.100 pezzi

- Quantita standard per output effettivo: 1.100 x 0.5 = 550 kg
- Scostamento prezzo: (10.50 - 10.00) x 580 = +290 EUR (sfavorevole: MP piu cara)
- Scostamento efficienza: (580 - 550) x 10.00 = +300 EUR (sfavorevole: piu scarti)
- Scostamento totale costi: +590 EUR (sfavorevole: abbiamo speso di piu)

### Scostamento costi fissi

Per i costi fissi lo scostamento e piu semplice:
```
Scostamento costi fissi = Costi fissi effettivi - Costi fissi budget
```

Cause tipiche:
- Aumento imprevisto affitto
- Assunzione non pianificata
- Spesa straordinaria di manutenzione
- Consulenza non prevista

---

## 3. Scostamento margine complessivo

### Scomposizione in 4 effetti

Lo scostamento del margine totale si scompone in:

**1. Effetto volume**:
```
= (Volume totale effettivo - Volume totale budget) x Margine medio budget
```
Abbiamo venduto piu/meno pezzi in totale?

**2. Effetto mix**:
```
= Volume totale effettivo x (Mix effettivo - Mix budget) x Margine unitario budget per prodotto
```
Abbiamo venduto una combinazione di prodotti diversa? (Es. piu prodotti a basso margine)

**3. Effetto prezzo**:
```
= Quantita effettiva per prodotto x (Prezzo effettivo - Prezzo budget)
```
Abbiamo venduto a prezzi diversi?

**4. Effetto efficienza**:
```
= Variazione costi unitari x Quantita effettiva
```
Abbiamo prodotto/erogato in modo piu o meno efficiente?

### Per PMI: semplificazione pratica

Se l'azienda ha pochi prodotti/servizi, fare la scomposizione completa. Se ha molti prodotti, concentrarsi su:
- Effetto volume (quanto abbiamo venduto)
- Effetto margine medio (a che margine abbiamo venduto)

---

## 4. Budget flessibile vs budget statico

### Concetto

- **Budget statico**: quello costruito a inizio anno con le ipotesi originali
- **Budget flessibile**: il budget statico ricalcolato ai volumi effettivi

Il confronto budget flessibile vs consuntivo isola gli scostamenti di efficienza e prezzo, eliminando l'effetto volume.

### Esempio

| Voce | Budget statico (1.000 pz) | Budget flessibile (1.100 pz) | Consuntivo (1.100 pz) |
|------|---------------------------|-------------------------------|------------------------|
| Ricavi | 50.000 | 55.000 | 51.700 |
| Costi variabili | 25.000 | 27.500 | 29.200 |
| Margine contribuzione | 25.000 | 27.500 | 22.500 |
| Costi fissi | 15.000 | 15.000 | 15.800 |
| Utile | 10.000 | 12.500 | 6.700 |

Analisi:
- Scostamento volume (budget flessibile vs statico): +2.500 EUR (favorevole, abbiamo venduto di piu)
- Scostamento efficienza/prezzo (consuntivo vs flessibile): -5.800 EUR (sfavorevole, margini peggiori)
- Scostamento totale: -3.300 EUR (sfavorevole)

Conclusione: il volume in piu non ha compensato il peggioramento dei margini. Investigare perche.

---

## 5. Template mensile per analisi scostamenti

### Struttura della tabella

| Voce | Budget mese | Consuntivo mese | Scostamento | % | Causa | Azione correttiva |
|------|-------------|-----------------|-------------|---|-------|--------------------|
| Ricavi linea A | | | | | | |
| Ricavi linea B | | | | | | |
| **Totale ricavi** | | | | | | |
| Materie prime | | | | | | |
| Provvigioni | | | | | | |
| Trasporti | | | | | | |
| **Totale costi variabili** | | | | | | |
| **Margine contribuzione** | | | | | | |
| Personale | | | | | | |
| Affitto | | | | | | |
| Utenze | | | | | | |
| Ammortamenti | | | | | | |
| Altro fisso | | | | | | |
| **Totale costi fissi** | | | | | | |
| **EBITDA** | | | | | | |
| **Utile operativo** | | | | | | |

### Soglie di attenzione

- **Verde** (scostamento 0-5%): nella norma, nessuna azione
- **Giallo** (scostamento 5-10%): monitorare, capire se e trend o evento isolato
- **Rosso** (scostamento oltre 10%): azione correttiva necessaria, investigare causa

### Frequenza e processo

**Mensile** (entro il 15 del mese successivo):
1. Il commercialista/gestionale fornisce i dati consuntivi
2. Compilare la tabella scostamenti (15 minuti)
3. Per ogni voce rossa: identificare causa e azione (15 minuti)
4. Aggiornare previsione a finire (se necessario)

**Trimestrale** (entro fine mese successivo al trimestre):
1. Revisione cumulata dei 3 mesi
2. Aggiornamento scenari se le ipotesi base sono cambiate
3. Decisione: il budget annuale e ancora valido o serve revisione?

---

## 6. Usare gli scostamenti per decidere

### Non solo reporting

L'errore piu comune e trattare l'analisi scostamenti come un esercizio di reporting: "abbiamo speso il 7% in piu di materie prime". E poi? Cosa facciamo?

### Dalla varianza alla decisione

Per ogni scostamento significativo, rispondere a 3 domande:

1. **E' controllabile?** Lo scostamento dipende da noi (inefficienza, errore di previsione) o da fattori esterni (aumento prezzo MP, cliente perso)?

2. **E' temporaneo o strutturale?** Un ritardo di consegna e temporaneo. Un aumento dei prezzi delle materie prime e strutturale. Le risposte sono diverse.

3. **Cosa facciamo?**
   - Se controllabile e temporaneo: monitorare, dovrebbe rientrare
   - Se controllabile e strutturale: cambiare processo, rinegoziare, ottimizzare
   - Se non controllabile e temporaneo: assorbire, usare riserve
   - Se non controllabile e strutturale: rivedere il budget, adeguare i prezzi, ripensare il modello

### Esempi di azioni correttive per PMI

| Scostamento | Causa | Azione |
|-------------|-------|--------|
| Ricavi -12% | Perdita cliente X | Azione commerciale su nuovi prospect, ridurre costi discrezionali |
| MP +8% | Aumento prezzo acciaio | Rinegoziare con fornitore, cercare alternativo, rivedere listino |
| Personale +15% | Straordinari non previsti | Analizzare carichi di lavoro, valutare assunzione vs straordinari |
| Utenze +20% | Aumento energia | Valutare contratto a prezzo fisso, efficientamento energetico |
| DSO +15gg | Clienti pagano in ritardo | Solleciti, sconto per pagamento anticipato, factoring |

### Il ciclo virtuoso

```
Budget → Consuntivo → Scostamento → Analisi causa → Azione → Risultato → Nuovo budget
```

Ogni ciclo migliora la qualita delle previsioni (le ipotesi si affinano) e la capacita di reazione dell'azienda.

---

## 7. KPI da monitorare mensilmente

Oltre agli scostamenti puntuali, monitorare questi indicatori sintetici:

| KPI | Formula | Soglia attenzione |
|-----|---------|-------------------|
| Margine contribuzione % | MdC / Ricavi | Calo di 2+ punti % |
| EBITDA % | EBITDA / Ricavi | Sotto il 10% (servizi) o 8% (manifattura) |
| Break-even mensile | Costi fissi / MdC% | Se il BEP supera i ricavi medi mensili |
| DSO effettivo | Crediti / (Ricavi/365) | Oltre 90 giorni |
| Cash runway | Cassa disponibile / Uscite mensili medie | Sotto 3 mesi |
| Scostamento cumulato ricavi | Ricavi YTD effettivi vs budget | Oltre -10% |
