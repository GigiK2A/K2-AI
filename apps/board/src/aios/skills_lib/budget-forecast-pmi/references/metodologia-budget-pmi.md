# Metodologia di budgeting per PMI italiane

## Premessa

Le PMI italiane (fino a 50M di fatturato, tipicamente 2-20M) raramente hanno un controller dedicato. Il budget viene fatto dal commercialista (che guarda al passato) o non viene fatto affatto. Questa metodologia e pensata per costruire un budget previsionale robusto partendo da dati minimi e ipotesi ragionevoli.

---

## 1. Analisi struttura costi

### Classificazione fissi vs variabili

**Costi fissi** (non variano col fatturato nel breve periodo):
- Affitto e spese condominiali
- Stipendi e contributi del personale a tempo indeterminato
- Ammortamenti immobilizzazioni
- Utenze fisse (quota fissa energia, telefonia, internet)
- Assicurazioni
- Consulenze ricorrenti (commercialista, consulente lavoro)
- Canoni software e licenze
- Leasing

**Costi variabili** (proporzionali al fatturato/volume):
- Materie prime e merci
- Lavorazioni esterne / conto terzi
- Provvigioni agenti (tipicamente 3-8% del venduto)
- Trasporti e spedizioni
- Packaging
- Energia variabile (quota consumo produzione)
- Costi di transazione (commissioni POS, marketplace)

**Costi semi-variabili** (hanno componente fissa + variabile):
- Personale interinale / stagionale
- Manutenzioni (ordinaria = fissa, straordinaria = variabile)
- Marketing (budget fisso + campagne legate a vendite)

### Come calcolare le incidenze

Per ogni voce di costo, calcolare:
- Incidenza % = Costo / Fatturato netto
- Confrontare con anno precedente e con benchmark settoriale
- Evidenziare scostamenti anomali (es. materie prime passate dal 30% al 38%)

---

## 2. Stima ricavi

### Approccio top-down

Partire dal fatturato storico e applicare un tasso di crescita:
- Fatturato previsto = Fatturato anno precedente x (1 + crescita%)
- La crescita% deve essere giustificata: nuovi clienti acquisiti, aumento listino, nuova linea prodotto
- Attenzione: crescita superiore al 15% richiede spiegazione specifica

### Approccio bottom-up (piu accurato per PMI)

Costruire il fatturato dal basso:
- Numero clienti attivi attesi x Ordine medio x Frequenza acquisto annua
- Oppure: numero pezzi venduti x Prezzo medio unitario
- Per servizi: ore vendibili x Tariffa oraria x Tasso di utilizzo

### Quale approccio usare

- Se l'azienda ha pochi clienti grandi: bottom-up per cliente
- Se ha molti clienti piccoli: top-down con aggiustamenti
- Ideale: fare entrambi e verificare la coerenza (se divergono oltre il 10%, investigare)

---

## 3. Stagionalita

### Come identificarla dai dati storici

Se sono disponibili dati mensili di almeno 2 anni:
1. Calcolare il fatturato medio mensile = Fatturato annuo / 12
2. Per ogni mese calcolare l'indice di stagionalita = Fatturato mese / Fatturato medio mensile
3. Mediare gli indici dei 2-3 anni disponibili
4. Verificare che la somma degli indici = 12 (normalizzare se necessario)

### Profili di stagionalita tipici per settore

- **Retail/commercio**: picco nov-dic (indice 1.4-1.8), calo gen-feb (indice 0.6-0.8)
- **Edilizia/costruzioni**: picco apr-ott (indice 1.1-1.3), calo nov-feb (indice 0.5-0.8)
- **Turismo/ristorazione**: picco giu-set (indice 1.5-2.0), calo gen-mar (indice 0.4-0.7)
- **B2B servizi**: abbastanza stabile, calo agosto (indice 0.5-0.7), picco set-nov (indice 1.1-1.3)
- **Alimentare**: stabile con picchi festivi (Pasqua, Natale)
- **Manifatturiero export**: dipende dai mercati di destinazione

### Distribuzione mensile del fatturato

Una volta ottenuti gli indici, il fatturato mensile previsto = (Fatturato annuo previsto / 12) x Indice stagionalita del mese.

---

## 4. Budget del personale

Il costo del personale e spesso la voce piu rilevante per le PMI di servizi (40-60% dei costi totali). Calcolo corretto del costo aziendale:

### Formula costo aziendale per dipendente

```
Retribuzione Annua Lorda (RAL)
+ Contributi INPS carico azienda (~33% della RAL)
+ TFR accantonamento annuo (RAL / 13.5 = ~7.4%)
+ IRAP sul costo del lavoro (~3.9% della base imponibile)
= Costo aziendale annuo
```

### Esempio numerico

| Voce | Importo |
|------|---------|
| RAL | 30.000 EUR |
| Contributi INPS (33%) | 9.900 EUR |
| TFR (7.4%) | 2.220 EUR |
| IRAP (3.9%) | 1.170 EUR |
| **Costo aziendale** | **43.290 EUR** |

Il moltiplicatore tipico e 1.44x la RAL (per operai/impiegati). Per dirigenti puo arrivare a 1.55x.

### Attenzione a

- Tredicesima e quattordicesima: gia incluse nella RAL ma impattano i flussi di cassa (giugno e dicembre)
- Ferie e permessi: il costo c'e ma non c'e produzione
- Nuove assunzioni: inserire il costo dal mese di ingresso, non da gennaio
- Incentivi/premi: stimare separatamente come costo variabile
- Formazione obbligatoria: costo diretto + costo opportunita

---

## 5. Budget investimenti

### Capex vs Opex

- **Capex** (investimento): acquisto macchinario, ristrutturazione, software > 516.46 EUR. Impatto CE tramite ammortamento, impatto cassa immediato (o rateizzato se finanziato).
- **Opex** (costo operativo): manutenzione, canoni, noleggi. Impatto CE e cassa nello stesso periodo.

### Piano ammortamento

Per ogni investimento:
- Costo di acquisto
- Categoria e aliquota ammortamento fiscale (es. macchinari 15%, attrezzature 25%, mobili 12%, software 33%)
- Ammortamento annuo = Costo x Aliquota
- Ammortamento mensile = Ammortamento annuo / 12
- Primo anno: ammortamento ridotto al 50% (norma fiscale)

### Impatto sul budget

- **CE**: inserire l'ammortamento mensile tra i costi fissi
- **Cash flow**: inserire l'uscita di cassa al momento del pagamento (che puo essere anticipato, alla consegna, o rateizzato)
- **Patrimoniale**: l'immobilizzazione entra nell'attivo e si riduce con gli ammortamenti

---

## 6. Budget finanziario e CCN dinamico

### Capitale Circolante Netto (CCN)

CCN = Crediti commerciali + Rimanenze - Debiti commerciali

Il CCN assorbe liquidita: se il fatturato cresce, anche il CCN cresce e serve piu cassa.

### Parametri chiave

- **DSO (Days Sales Outstanding)**: giorni medi di incasso. PMI italiane: tipicamente 60-90 giorni. PA: 30-60 giorni (migliorato con PNRR ma ancora variabile).
- **DPO (Days Payable Outstanding)**: giorni medi di pagamento ai fornitori. Tipicamente 30-60 giorni.
- **DIO (Days Inventory Outstanding)**: giorni di giacenza magazzino. Molto variabile per settore.

### Calcolo fabbisogno circolante

Fabbisogno aggiuntivo di CCN = Variazione fatturato x (DSO + DIO - DPO) / 365

Esempio: se il fatturato cresce di 500.000 EUR e il ciclo di cassa e 60gg (DSO 75 + DIO 15 - DPO 30), il fabbisogno aggiuntivo e 500.000 x 60/365 = 82.192 EUR.

### Linee di credito necessarie

Se il saldo di cassa cumulato diventa negativo in qualche mese:
- Fido di conto corrente: per scoperto temporaneo (costo: Euribor + spread 2-5%)
- Anticipo fatture/SBF: per monetizzare crediti commerciali (costo: 3-6% annuo)
- Finanziamento a medio termine: per investimenti (costo: 3-5% annuo, durata 3-7 anni)

---

## 7. Tre scenari

### Scenario base

Ipotesi realistiche, coerenti con il trend storico e le azioni pianificate:
- Crescita fatturato: in linea con piano commerciale
- Costi: variabili proporzionali, fissi come da contratti in essere
- Investimenti: come da piano approvato
- DSO/DPO: in linea con storico

### Scenario ottimistico (+20% ricavi)

- Fatturato +20% rispetto a base (nuovo cliente importante, mercato in crescita, successo nuovo prodotto)
- Costi variabili: crescono proporzionalmente
- Costi fissi: stabili (la struttura regge)
- Effetto leva operativa: l'utile cresce piu che proporzionalmente
- Attenzione: il CCN cresce e potrebbe servire piu fido

### Scenario pessimistico (-15% ricavi)

- Fatturato -15% rispetto a base (perdita cliente, crisi settoriale, ritardi progetti)
- Costi variabili: si riducono proporzionalmente
- Costi fissi: rigidi nel breve (non puoi licenziare dall'oggi al domani)
- Rischio: margine operativo si comprime o diventa negativo
- Domanda chiave: per quanti mesi l'azienda regge in perdita? Quanta cassa ha?

---

## 8. Sensitivity analysis

### Variabili chiave da testare

Le 3-4 variabili che tipicamente spostano di piu l'utile di una PMI:

1. **Fatturato (+/-10%)**: quasi sempre la variabile piu impattante. Testare: cosa succede se perdo il cliente X (che vale il 15% del fatturato)?
2. **Costo materie prime (+/-5%)**: per aziende manifatturiere/commerciali dove le materie prime pesano oltre il 30% dei ricavi.
3. **DSO (+/-15 giorni)**: non impatta l'utile ma impatta la cassa. Un allungamento di 15gg su 2M di fatturato = 82k di fabbisogno aggiuntivo.
4. **Numero dipendenti (+/-1)**: un dipendente in piu o in meno a 30k RAL = +/-43k di costo aziendale.

### Come presentare la sensitivity

Tabella a doppia entrata:
- Righe: variabile 1 (es. fatturato -10%, -5%, base, +5%, +10%)
- Colonne: variabile 2 (es. costo MP -5%, base, +5%)
- Celle: utile netto risultante

Evidenziare le combinazioni che portano in perdita (celle rosse).

---

## 9. Errori comuni nel budgeting PMI

1. **Dimenticare la stagionalita**: budget lineare su 12 mesi quando il business e stagionale porta a previsioni sbagliate mese per mese.
2. **Sottostimare il costo del personale**: usare la RAL invece del costo aziendale (errore del 44%).
3. **Confondere cassa e competenza**: un investimento da 100k impatta la cassa subito ma il CE solo tramite ammortamento.
4. **Non considerare il fabbisogno di CCN**: il fatturato cresce ma la cassa diminuisce perche i crediti commerciali crescono piu dei debiti.
5. **Budget "fotocopia"**: prendere il consuntivo dell'anno prima e aggiungere il 5%. Non e budgeting, e pigrizia.
6. **Non aggiornare il budget**: il budget va rivisto almeno ogni trimestre con i dati consuntivi (rolling forecast).
7. **Ignorare gli impegni gia presi**: contratti firmati, ordini confermati, assunzioni in corso sono certezze, non ipotesi.
