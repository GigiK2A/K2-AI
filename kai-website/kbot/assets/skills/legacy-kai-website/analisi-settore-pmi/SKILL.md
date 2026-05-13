---
name: analisi-settore-pmi
description: >-
  Analisi settore con 5 forze Porter per PMI italiane (349 EUR).
  Definizione confini settore e sotto-settore, analisi 5 forze con scoring 1-5
  per rivalita, minaccia entranti, minaccia sostituti, potere fornitori, potere
  clienti, con variabili specifiche ed evidenze. Dinamiche settoriali: fase
  lifecycle, trend digitalizzazione/ESG/PNRR, disruption, regolamentazione.
  Raggruppamenti strategici con mappa 2D su variabili chiave. Sintesi
  attrattivita settore e implicazioni strategiche per il cliente.
  Output: report DOCX 10-12 pagine con radar chart, JSON strutturato.
  Attiva per: analisi settore, 5 forze Porter, il mio settore, analisi
  competitiva, barriere all ingresso, come sta il settore, analisi di mercato,
  struttura settore, competitor analysis, raggruppamenti strategici,
  dinamiche settore.
---

# Analisi Settore PMI — 5 Forze Porter, Dinamiche e Raggruppamenti Strategici

Skill di analisi settoriale per PMI italiane. Prezzo servizio: 349 EUR.
Approccio analitico con esempi italiani concreti del settore specifico del cliente.

---

## Trigger

Attiva questa skill quando l'utente menziona:
- "analisi settore", "5 forze Porter", "il mio settore"
- "analisi competitiva", "barriere all'ingresso"
- "come sta il settore", "analisi di mercato"
- "struttura settore", "competitor analysis"
- "raggruppamenti strategici", "dinamiche settore"

---

## Input Richiesti

Raccogli dall'utente:

1. **Settore** di appartenenza (es. "alimentare", "meccanica di precisione", "servizi IT")
2. **Sotto-settore** specifico (es. "pasta fresca artigianale", "torneria conto terzi", "cybersecurity per PMI")
3. **Area geografica di riferimento** — mercato locale/regionale/nazionale/export (specificare)
4. **Competitor noti** (2-5) — i principali concorrenti che il cliente riconosce come diretti
5. **Prodotti/servizi principali** — cosa offre il cliente e in quali segmenti compete

Se l'utente non fornisce tutti i dati, chiedi con domande mirate. Esempio:
- "In quale settore operi esattamente? E qual e il sotto-settore specifico?"
- "Il tuo mercato e locale, regionale, nazionale o esporti?"
- "Chi sono i tuoi 2-5 concorrenti principali?"
- "Quali sono i prodotti o servizi principali che offri?"

---

## Workflow — 5 Step

### Step 1: Definizione Confini Settore e Sotto-settore

Definisci con precisione:
- **Confini del settore**: quali attivita rientrano, quali no
- **Sotto-settore specifico**: nicchia in cui opera il cliente
- **Mercato di riferimento**: delimitazione geografica e dimensionale
- **Catena del valore**: posizionamento del cliente nella filiera (monte/valle)

Usa dati ISTAT (codici ATECO), Cerved, report Mediobanca, dati Confindustria per dimensionare il settore. Specifica il codice ATECO di riferimento.

Tono: "Il tuo settore, pasta fresca artigianale (ATECO 10.73.0), in Italia vale circa 1,2 miliardi di EUR con oltre 2.000 imprese attive. Il sotto-settore premium/artigianale rappresenta il 15-20% del mercato. Vediamo come si muovono le forze competitive."

### Step 2: Analisi 5 Forze di Porter (Scoring 1-5)

Per ciascuna delle 5 forze, analizza le variabili specifiche, assegna uno score 1-5 (1=forza debole, favorevole all'impresa; 5=forza forte, sfavorevole) e fornisci evidenze concrete dal settore italiano.

Consulta `references/guida-5-forze-pmi.md` per le variabili dettagliate di ciascuna forza.

#### 2.1 Rivalita tra concorrenti esistenti
Variabili: numero concorrenti, concentrazione (CR4/CR8), tasso crescita settore, differenziazione, incidenza costi fissi, barriere all'uscita.

#### 2.2 Minaccia di nuovi entranti
Variabili: economie di scala, capitale richiesto, accesso ai canali distributivi, regolamentazione/licenze, forza brand incumbent, switching costs per i clienti.

#### 2.3 Minaccia di prodotti/servizi sostituti
Variabili: propensione alla sostituzione, rapporto prezzo/prestazione dell'alternativa, costi di switching verso il sostituto.

#### 2.4 Potere contrattuale dei fornitori
Variabili: concentrazione fornitori, importanza dell'input, costi di switching fornitore, minaccia di integrazione a valle, disponibilita di input sostitutivi.

#### 2.5 Potere contrattuale dei clienti
Variabili: concentrazione clienti, volumi di acquisto, standardizzazione del prodotto, costi di switching per il cliente, minaccia di integrazione a monte.

**Attrattivita complessiva**: media delle 5 forze.
- 1.0-2.0: settore molto attrattivo
- 2.1-3.0: settore attrattivo
- 3.1-4.0: settore moderatamente attrattivo
- 4.1-5.0: settore poco attrattivo

Tono: "La rivalita nel tuo settore e alta (4/5): ci sono molti operatori, il prodotto e poco differenziato e i margini sono compressi. Pero la minaccia di nuovi entranti e bassa (2/5) grazie alle competenze tecniche necessarie. Questo significa che chi e dentro, e protetto — ma deve lottare con chi c'e gia."

### Step 3: Dinamiche Settoriali

Analizza:
- **Fase del ciclo di vita del settore**: introduzione / crescita / maturita / declino — e relative caratteristiche, KSF (Key Success Factor), strategie consigliate per PMI
- **Trend in corso**: digitalizzazione, sostenibilita/ESG, reshoring, Silver economy, impatti PNRR
- **Segnali di disruption**: nuove tecnologie, nuovi modelli di business, cambiamenti normativi
- **Regolamentazione**: normative chiave che impattano il settore (cenni)

Consulta `references/dinamiche-settoriali.md` per il framework completo.

Tono: "Il tuo settore e in fase di maturita avanzata: crescita sotto il 2% annuo, consolidamento in corso, margini in calo. Ma c'e un trend di reshoring dalla Cina che sta riaprendo spazi per chi investe in qualita e tempi di consegna rapidi."

### Step 4: Raggruppamenti Strategici (Mappa 2D)

Costruisci una mappa dei raggruppamenti strategici:
1. **Identifica le 2 variabili chiave** che differenziano i competitor nel settore (es. ampiezza gamma vs. livello prezzo; specializzazione vs. copertura geografica; innovazione vs. costo)
2. **Posiziona i competitor** sulla mappa 2D (inclusi quelli forniti dal cliente + altri rilevanti)
3. **Identifica i gruppi**: cluster di aziende con strategie simili
4. **Analizza le distanze**: barriere alla mobilita tra gruppi, direzioni di migrazione

Tono: "Nel tuo settore vedo 3 gruppi strategici: (1) i generalisti ad alto volume/basso prezzo — pensa a [Competitor A]; (2) gli specialisti di nicchia/alto valore — dove sei tu e [Competitor B]; (3) i nuovi player digitali. Spostarsi dal gruppo 2 al gruppo 1 richiederebbe investimenti in capacita produttiva che per una PMI non hanno senso. Meglio rafforzare la posizione nel gruppo 2."

### Step 5: Sintesi Attrattivita e Implicazioni per il Cliente

Produci:
- **Score attrattivita settore** (1-5) con giustificazione
- **Forza dominante**: quale delle 5 forze condiziona di piu la redditivita
- **Implicazioni strategiche**: cosa fare concretamente, dato il profilo delle forze
- **Opportunita**: dove si aprono spazi nel settore
- **Minacce principali**: i rischi piu concreti nei prossimi 2-3 anni
- **Raccomandazioni** specifiche per il posizionamento del cliente

Tono: "Il tuo settore ha un'attrattivita moderata (3.2/5). La forza dominante e il potere dei clienti — i tuoi 3 clienti principali fanno il 60% del fatturato e ti comprimono i margini. La raccomandazione principale: diversifica la base clienti e investi in differenziazione per ridurre la sostituibilita."

---

## Skill Invocate

- **`strategia-competitiva`**: per approfondire il posizionamento competitivo e le strategie generiche
- **`benchmark-italia-business`**: per dati di benchmark settoriali italiani (margini, KPI di settore)
- **`economia-politica-micro-macro`**: per le strutture di mercato (concorrenza perfetta, oligopolio, monopolistica) e i modelli microeconomici applicati
- **`docx`**: per generare il report DOCX finale 10-12 pagine

---

## Deliverable

1. **Report DOCX** (10-12 pagine) — strutturato secondo `assets/template-report-settore.md`
2. **JSON strutturato** — conforme a `schemas/output-schema.json`

---

## Tono e Stile

- **Analitico ma accessibile**: dati e framework accademici, spiegati in modo comprensibile per un imprenditore PMI
- **Esempi italiani concreti**: ogni forza illustrata con nomi di aziende, settori, dinamiche reali del contesto italiano
- **Orientato all'azione**: ogni analisi si chiude con "e quindi per te significa..."
- **Numerico quando possibile**: score, percentuali, dati di mercato — non solo descrizioni qualitative
