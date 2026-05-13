# Sistema Alert — Semafori e Notifiche Automatiche

## 1. Sistema semafori a 3 livelli

### Verde — In target o migliore
- **Condizione:** Scostamento dal target <= 10% (in positivo o entro soglia accettabile)
- **Significato:** KPI sotto controllo, nessuna azione richiesta
- **Visualizzazione:** Cerchio verde #22C55E, nessun commento automatico
- **Icona dashboard:** cerchio pieno verde

### Giallo — Attenzione
- **Condizione:** Scostamento dal target tra 10% e 20% (in negativo)
- **Significato:** KPI in zona di attenzione, monitorare con piu frequenza
- **Visualizzazione:** Cerchio giallo #EAB308, commento breve di attenzione
- **Icona dashboard:** triangolo giallo con punto esclamativo
- **Azione:** Verificare la causa, pianificare intervento se il trend non migliora

### Rosso — Azione richiesta
- **Condizione:** Scostamento dal target > 20% (in negativo)
- **Significato:** KPI critico, richiede intervento immediato
- **Visualizzazione:** Cerchio rosso #EF4444, commento dettagliato con cause e azioni
- **Icona dashboard:** cerchio rosso con X
- **Azione:** Intervento immediato richiesto

### Calcolo scostamento

```
Scostamento % = ((Valore attuale - Target) / Target) x 100
```

**Nota sulla direzione:** Per KPI dove "meno e meglio" (es. GG incasso, scarti, reclami, turnover), invertire il segno:
```
Scostamento % = ((Target - Valore attuale) / Target) x 100
```

Se il risultato e negativo, il KPI e peggiorato rispetto al target.

### Soglie personalizzabili

Le soglie 10%/20% sono valori di default. Il titolare puo personalizzarle per KPI:
- KPI molto sensibili (es. posizione di cassa): soglie piu strette (5%/10%)
- KPI con alta variabilita naturale (es. nuovi clienti per PMI piccola): soglie piu larghe (15%/30%)

---

## 2. Alert automatici per KPI rossi

Per ogni KPI che entra in zona rossa, generare automaticamente una scheda alert con 3 elementi:

### 2.1 Descrizione deviazione
Frase sintetica che descrive il problema in linguaggio non tecnico.

**Esempio:**
> "Il fatturato di marzo (85.000 euro) e inferiore del 25% rispetto al target (113.000 euro) e del 18% rispetto a marzo dello scorso anno (104.000 euro)."

### 2.2 Possibili cause (2-3 ipotesi)
Ipotesi generate in base al tipo di KPI e ai dati disponibili.

**Tabella cause tipiche per KPI:**

| KPI | Cause probabili |
|---|---|
| **Fatturato sotto target** | (1) Perdita di 1-2 clienti importanti, (2) Ritardo nella fatturazione, (3) Stagionalita non prevista nel budget |
| **EBITDA in calo** | (1) Aumento costi non pianificato (materie prime, personale), (2) Fatturato in calo senza riduzione costi proporzionale, (3) Mix prodotto/servizio meno redditizio |
| **Cash flow negativo** | (1) Ritardo incassi clienti, (2) Pagamenti anticipati a fornitori, (3) Investimento non pianificato |
| **GG incasso in aumento** | (1) Clienti in difficolta finanziaria, (2) Contestazioni/reclami bloccano pagamenti, (3) Processo di sollecito insufficiente |
| **Posizione cassa bassa** | (1) Cash flow negativo prolungato, (2) Investimento recente, (3) Mancato rinnovo linea di credito |
| **Clienti persi (churn alto)** | (1) Problema qualita prodotto/servizio, (2) Concorrente con offerta migliore, (3) Prezzo non competitivo |
| **Concentrazione alta** | (1) Crescita organica sbilanciata, (2) Perdita clienti piccoli, (3) Eccessiva dipendenza da commesse grandi |
| **Ore fatturabili basse** | (1) Troppo tempo su attivita interne non remunerative, (2) Sotto-organico che obbliga tutti a fare admin, (3) Progetto in perdita che assorbe risorse |
| **Scarti/resi alti** | (1) Problema qualita materia prima, (2) Macchinario da manutenere, (3) Personale nuovo non ancora formato |
| **Turnover alto** | (1) Retribuzioni sotto mercato, (2) Clima aziendale deteriorato, (3) Mancanza di prospettive di crescita |

### 2.3 Azione suggerita
Azione concreta, specifica, fattibile per una PMI.

**Formato standard:**
> **Azione:** [Cosa fare] entro [quando] — [chi dovrebbe farlo]

**Esempi:**
> **Azione:** Contattare i 3 clienti principali questa settimana per verificare pipeline ordini prossimo trimestre — Titolare/Commerciale

> **Azione:** Sollecitare i crediti scaduti oltre 60 giorni (elenco allegato) e valutare l'invio di una diffida formale per i crediti oltre 90 giorni — Amministrazione

> **Azione:** Analizzare il dettaglio costi del mese per identificare le voci aumentate e negoziare con i fornitori principali — Titolare/Responsabile acquisti

---

## 3. Trend alert

### KPI in peggioramento costante
- **Condizione:** KPI che peggiora per 3 mesi consecutivi, anche se ancora in zona verde
- **Logica:** Confrontare valore mese corrente vs mese-1 vs mese-2 vs mese-3. Se la direzione e costantemente negativa per 3 periodi, attivare alert
- **Visualizzazione:** Icona freccia in discesa accanto al semaforo verde, con nota "Trend in peggioramento da 3 mesi"
- **Livello:** Giallo (attenzione) anche se il valore assoluto e ancora verde

### Calcolo trend
```
Trend negativo = (Valore_M > Valore_M-1 > Valore_M-2 > Valore_M-3)
dove M e il mese corrente, per KPI "meno e meglio"

Trend negativo = (Valore_M < Valore_M-1 < Valore_M-2 < Valore_M-3)
per KPI "piu e meglio"
```

### Eccezioni
- Non attivare trend alert se il peggioramento totale sui 3 mesi e < 5% (fluttuazione normale)
- Non attivare trend alert per KPI con stagionalita nota (es. fatturato in agosto per settore vacanze)

---

## 4. Alert di concentrazione

### Concentrazione fatturato clienti
- **Soglia critica:** Top 3 clienti rappresentano > 40% del fatturato
- **Soglia di attenzione:** Top 3 clienti rappresentano 30-40% del fatturato
- **Calcolo:** (Fatturato cliente 1 + cliente 2 + cliente 3) / Fatturato totale x 100

### Perche e importante per le PMI
La perdita di un singolo cliente che pesa il 15-20% del fatturato puo mettere a rischio la sopravvivenza dell'azienda. Questo alert e specifico per PMI dove la base clienti e naturalmente ridotta.

### Azione suggerita standard
> **Concentrazione > 50%:** "RISCHIO ALTO. Il fatturato dipende eccessivamente da pochi clienti. Priorita assoluta: diversificare la base clienti. Definire un piano commerciale per acquisire almeno 3-5 nuovi clienti nei prossimi 6 mesi."

> **Concentrazione 40-50%:** "ATTENZIONE. La dipendenza dai clienti principali e significativa. Intensificare le attivita commerciali verso nuovi segmenti di mercato."

> **Concentrazione 30-40%:** "MONITORARE. Livello nella norma per una PMI ma da tenere sotto controllo. Verificare la solidita dei clienti principali."

---

## 5. Priorita degli alert

Quando ci sono piu alert attivi, ordinarli per gravita:

1. **Priorita 1 — Sopravvivenza:** Posizione cassa critica, cash flow negativo persistente
2. **Priorita 2 — Redditivita:** EBITDA negativo o in forte calo, fatturato sotto target
3. **Priorita 3 — Sostenibilita:** Churn alto, concentrazione clienti, GG incasso in aumento
4. **Priorita 4 — Sviluppo:** Trend negativi su KPI crescita, processi in peggioramento

Nella dashboard, mostrare gli alert in questo ordine. Il titolare deve vedere per primi i problemi che possono compromettere l'azienda nel breve termine.

---

## 6. Formato visualizzazione alert nella dashboard

Ogni alert nella sezione dedicata deve avere questa struttura:

```
[SEMAFORO]  [NOME KPI]  [VALORE] vs [TARGET]  ([SCOSTAMENTO %])
Cosa sta succedendo: [descrizione in linguaggio chiaro]
Possibili cause:
  1. [causa 1]
  2. [causa 2]
  3. [causa 3]
Azione suggerita: [azione concreta con tempistica]
```

Colore card:
- Rosso: sfondo #FEF2F2, bordo sinistro 4px #EF4444
- Giallo: sfondo #FFFBEB, bordo sinistro 4px #EAB308
