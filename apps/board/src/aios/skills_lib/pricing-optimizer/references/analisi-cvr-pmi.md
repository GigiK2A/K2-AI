# Framework Costi-Volumi-Risultati (CVR) per PMI

Riferimento tecnico per l'analisi CVR applicata alle piccole e medie imprese italiane.

---

## 1. Classificazione dei Costi

### Costi Fissi (CF)
Restano costanti al variare del volume di attivita entro il range rilevante.
- Affitto locali
- Stipendi personale fisso (non legati alla produzione)
- Ammortamenti impianti e attrezzature
- Assicurazioni
- Utenze quota fissa
- Canoni software e licenze
- Commercialista, consulenze fisse
- Rate mutui e leasing

**Per PMI**: i costi fissi sono spesso sottostimati. Il titolare dimentica di includere il proprio compenso, l'ammortamento del furgone, il costo del magazzino. Regola: se lo paghi anche quando non vendi niente, e un costo fisso.

### Costi Variabili (CV)
Variano in proporzione diretta al volume di attivita.
- Materie prime e materiali diretti
- Provvigioni agenti (% sul venduto)
- Costi di spedizione per unita
- Packaging
- Commissioni pagamento (POS, PayPal)
- Energia di processo (quota variabile)
- Subforniture legate alla commessa

**Per PMI di servizi**: il costo variabile principale e spesso il tempo del professionista. Se un'ora di consulenza viene venduta a 100 EUR e il consulente junior costa 30 EUR/ora (lordo azienda), il costo variabile e 30 EUR.

### Costi Semi-variabili
Contengono una componente fissa e una variabile.
- Utenze (canone fisso + consumo)
- Telefonia (fisso + traffico)
- Personale con straordinari (stipendio base + ore extra)
- Manutenzione (programmata + a consumo)

**Come trattarli**: separare le due componenti. Metodo dei minimi-massimi:
```
CV unitario = (Costo al volume max - Costo al volume min) / (Volume max - Volume min)
CF = Costo totale - (CV unitario x Volume)
```

In alternativa, per semplicita, assegnare interamente a fissi o variabili in base alla componente prevalente.

---

## 2. Margine di Contribuzione (MdC)

### Definizioni

**MdC unitario** = Prezzo di vendita unitario (p) - Costo variabile unitario (cv)
```
MCu = p - cv
```
Rappresenta quanto ogni unita venduta contribuisce a coprire i costi fissi e generare utile.

**MdC percentuale** = MCu / p x 100
```
MC% = MCu / p x 100
```
Indica la percentuale del prezzo che resta dopo aver coperto i costi variabili.

**MdC totale** = MCu x Quantita venduta (Q)
```
MC totale = MCu x Q = (p - cv) x Q
```
Oppure: MC totale = Ricavi totali - Costi variabili totali.

### Interpretazione per PMI

| MC% | Interpretazione | Tipico di |
|---|---|---|
| Sopra 70% | Eccellente — servizi ad alto valore | Consulenza, formazione, SaaS |
| 50-70% | Buono — margine sano | Servizi professionali, artigianato specializzato |
| 30-50% | Medio — attenzione ai volumi | Commercio specializzato, ristorazione |
| 15-30% | Basso — serve volume alto | Commercio tradizionale, commodity |
| Sotto 15% | Critico — verificare sostenibilita | GDO, commodity a basso margine |

---

## 3. Break-Even Point (BEP)

### BEP in Quantita
```
BEP(q) = CF / MCu
```
Numero minimo di unita da vendere per coprire tutti i costi.

### BEP in Valore (Fatturato)
```
BEP(v) = CF / MC%
```
Fatturato minimo per raggiungere il pareggio.

### BEP per Prodotto in Mix

Quando l'impresa vende piu prodotti, il BEP si calcola sul mix ponderato.

1. Definire il mix di vendita (% di ciascun prodotto sul totale unita)
2. Calcolare il MCu medio ponderato:
```
MCu medio = SUM(MCu_i x peso_i)
```
dove peso_i = Q_i / Q_totale

3. BEP totale in unita:
```
BEP mix = CF / MCu medio
```

4. BEP per singolo prodotto:
```
BEP_i = BEP mix x peso_i
```

**Attenzione**: il BEP in mix e valido solo se il mix resta costante. Se cambia la proporzione tra prodotti, cambia il BEP.

### BEP Target (con utile obiettivo)
```
Q target = (CF + Utile obiettivo) / MCu
```
Quanto vendere per ottenere un utile specifico.

Con le tasse:
```
Q target post-tax = (CF + Utile obiettivo / (1 - aliquota)) / MCu
```

---

## 4. Margine di Sicurezza

```
Margine di sicurezza = (Vendite attuali - Vendite BEP) / Vendite attuali x 100
```

Misura quanto possono calare le vendite prima di entrare in perdita.

| Margine | Valutazione | Azione |
|---|---|---|
| Sopra 40% | Molto sicuro | Margine per investimenti |
| 25-40% | Buono | Situazione sana |
| 15-25% | Attenzione | Monitorare da vicino |
| Sotto 15% | Critico | Azioni immediate necessarie |

---

## 5. Leva Operativa

```
Leva operativa = MC totale / Utile operativo
```

Oppure, in termini di variazione:
```
Leva operativa = % variazione Utile / % variazione Fatturato
```

### Significato per il Rischio d'Impresa

La leva operativa misura la sensibilita dell'utile a variazioni del fatturato.

- **Leva alta** (sopra 4): struttura di costi prevalentemente fissi. Piccole variazioni di volume producono grandi variazioni di utile. Alto rischio ma alto potenziale.
  - Tipica di: studi professionali, SaaS, attivita capital-intensive
  - Esempio: leva 5 significa che +10% fatturato = +50% utile, ma -10% fatturato = -50% utile

- **Leva bassa** (sotto 2.5): struttura di costi prevalentemente variabili. L'utile segue linearmente il volume. Basso rischio ma minore potenziale.
  - Tipica di: commercio, servizi a basso valore aggiunto, subforniture
  - Esempio: leva 1.5 significa che +10% fatturato = +15% utile

- **Leva intermedia** (2.5-4): equilibrio tra fissi e variabili.

**Nota**: la leva operativa tende a infinito quando ci si avvicina al BEP (perche l'utile tende a zero). Viceversa, lontano dal BEP la leva si riduce.

---

## 6. Analisi What-If

### Variazione del Prezzo
Un aumento di prezzo del Delta% con elasticita e:
```
Nuova Q = Q x (1 - e x Delta%)
Nuovo MCu = (p x (1 + Delta%)) - cv
Nuovo MC totale = Nuovo MCu x Nuova Q
Nuovo Utile = Nuovo MC totale - CF
```

### Variazione del Costo Variabile
```
Nuovo MCu = p - (cv x (1 + Delta%))
Nuovo Utile = Nuovo MCu x Q - CF
```
(Il volume resta costante perche il prezzo non cambia.)

### Variazione dei Costi Fissi
```
Nuovo Utile = MC totale - CF x (1 + Delta%)
Nuovo BEP = CF x (1 + Delta%) / MCu
```

### Variazione del Mix
Ricalcolare MCu medio ponderato con i nuovi pesi e aggiornare BEP e utile.

---

## 7. Esempi Numerici PMI Italiana

### Esempio 1: Studio Professionale (Commercialista)

| Servizio | Prezzo | CV | MCu | MC% | Volume/mese | MC totale |
|---|---|---|---|---|---|---|
| Dichiarazione redditi | 150 EUR | 25 EUR | 125 EUR | 83% | 40 | 5.000 EUR |
| Consulenza oraria | 100 EUR | 15 EUR | 85 EUR | 85% | 60 | 5.100 EUR |
| Tenuta contabilita | 300 EUR/mese | 80 EUR | 220 EUR | 73% | 25 | 5.500 EUR |
| Pratiche societarie | 500 EUR | 100 EUR | 400 EUR | 80% | 8 | 3.200 EUR |

CF mensili: 12.000 EUR (affitto 2.500, stipendi 7.000, utenze/sw 1.500, altro 1.000)
MC totale: 18.800 EUR
Utile: 6.800 EUR
Leva operativa: 18.800 / 6.800 = 2.76
Margine sicurezza: (vendite - BEP) / vendite. Vendite totali = 26.400 EUR. BEP(v) = 12.000 / (18.800/26.400) = 16.851 EUR. MdS = (26.400-16.851)/26.400 = 36%

### Esempio 2: Ristorante (30 coperti)

| Voce | Prezzo medio | CV | MCu | MC% | Volume/mese | MC totale |
|---|---|---|---|---|---|---|
| Pranzo | 15 EUR | 5.50 EUR | 9.50 EUR | 63% | 450 | 4.275 EUR |
| Cena | 30 EUR | 11 EUR | 19 EUR | 63% | 350 | 6.650 EUR |
| Aperitivo | 8 EUR | 2 EUR | 6 EUR | 75% | 200 | 1.200 EUR |
| Asporto | 12 EUR | 5 EUR | 7 EUR | 58% | 150 | 1.050 EUR |

CF mensili: 9.500 EUR
MC totale: 13.175 EUR
Utile: 3.675 EUR
Leva operativa: 13.175 / 3.675 = 3.59
Margine sicurezza: ~28%

### Esempio 3: Negozio Abbigliamento

| Categoria | Prezzo medio | CV (acquisto) | MCu | MC% | Volume/mese | MC totale |
|---|---|---|---|---|---|---|
| Abbigliamento donna | 65 EUR | 30 EUR | 35 EUR | 54% | 80 | 2.800 EUR |
| Accessori | 25 EUR | 8 EUR | 17 EUR | 68% | 120 | 2.040 EUR |
| Calzature | 90 EUR | 45 EUR | 45 EUR | 50% | 30 | 1.350 EUR |

CF mensili: 4.500 EUR
MC totale: 6.190 EUR
Utile: 1.690 EUR
Leva operativa: 6.190 / 1.690 = 3.66

### Esempio 4: Artigiano (Falegname)

| Prodotto | Prezzo | CV (materiali+subf) | MCu | MC% | Volume/mese | MC totale |
|---|---|---|---|---|---|---|
| Mobile su misura | 2.500 EUR | 900 EUR | 1.600 EUR | 64% | 3 | 4.800 EUR |
| Restauro | 800 EUR | 200 EUR | 600 EUR | 75% | 5 | 3.000 EUR |
| Piccoli lavori | 200 EUR | 50 EUR | 150 EUR | 75% | 15 | 2.250 EUR |

CF mensili: 6.000 EUR (laboratorio, attrezzature, assicurazione, furgone)
MC totale: 10.050 EUR
Utile: 4.050 EUR
Leva operativa: 10.050 / 4.050 = 2.48
