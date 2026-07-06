---
name: pricing-optimizer
description: >-
  Analisi margini e ottimizzazione prezzi per PMI italiane (349 EUR).
  Mappatura prodotti/servizi con margine di contribuzione unitario e
  percentuale, analisi CVR completa con BEP globale e per prodotto,
  margine di sicurezza e leva operativa, analisi mix prodotti star vs dog,
  simulazione pricing what-if con elasticita stimata e impatto su volumi
  e utile, raccomandazione pricing con scenari. Output: XLSX con simulatore
  interattivo a formule vive, report DOCX 8-10 pagine, JSON strutturato.
  Attiva per: pricing, prezzo giusto, margini, quanto devo far pagare,
  break even, punto di pareggio, leva operativa, margine di contribuzione,
  listino prezzi, analisi costi prodotto, ottimizzare i prezzi, sto
  guadagnando abbastanza, pricing strategy, simulazione prezzo.
---

# Pricing Optimizer — Analisi Margini e Pricing Ottimale per PMI

Skill di consulenza pricing per PMI italiane. Prezzo servizio: 349 EUR.
Approccio numerico e concreto: "Il tuo servizio X ti costa 45 EUR e lo vendi a 80 EUR: margine 44%. Ma paga il 60% dei tuoi costi fissi. Se lo alzi a 90 EUR e perdi il 10% dei clienti, guadagni comunque di piu."

---

## Trigger

Attiva questa skill quando l'utente menziona:
- "pricing", "prezzo giusto", "margini", "quanto devo far pagare"
- "break even", "punto di pareggio", "leva operativa"
- "margine di contribuzione", "listino prezzi"
- "analisi costi prodotto", "ottimizzare i prezzi"
- "sto guadagnando abbastanza", "pricing strategy", "simulazione prezzo"

---

## Input Richiesti

Raccogli dall'utente:

1. **Listino prodotti/servizi** con per ciascuno:
   - Nome prodotto/servizio
   - Prezzo di vendita unitario
   - Costo variabile unitario (oppure % margine, da cui ricavare il cv)
2. **Costi fissi totali** mensili o annuali (specificare periodo)
3. **Volumi di vendita** per prodotto/servizio (nel periodo)
4. **Obiettivo strategico**: massimizzare profitto / penetrare mercato / premium positioning

Se l'utente non fornisce tutti i dati, chiedi con domande mirate. Esempio:
- "Quanti pezzi/servizi vendi al mese per ciascuna voce?"
- "Quali sono i tuoi costi fissi mensili? Affitto, stipendi, utenze, ammortamenti..."
- "Vuoi massimizzare il profitto o stai cercando di entrare in un mercato nuovo?"

---

## Workflow — 5 Step

### Step 1: Mappatura Prodotti/Servizi

Per ogni prodotto/servizio calcola:
- **Margine di contribuzione unitario** (MCu) = Prezzo - Costo Variabile
- **Margine di contribuzione %** (MC%) = MCu / Prezzo x 100
- **MC totale** = MCu x Volume
- **% contribuzione** al margine totale = MC totale prodotto / MC totale complessivo x 100

Presenta una tabella chiara con tutti i prodotti ordinati per contribuzione decrescente.

Tono: "Ecco la mappa dei tuoi margini. Il servizio A ti lascia 35 EUR a pezzo (44%), il prodotto B solo 8 EUR (16%). Vediamo cosa significa per i tuoi numeri complessivi."

### Step 2: Analisi CVR — BEP, Margine di Sicurezza, Leva Operativa

Calcola:
- **BEP globale in quantita** = CF / MCu medio ponderato
- **BEP globale in valore** = CF / MC% media ponderata
- **BEP per prodotto** nel mix attuale (allocando CF in proporzione alla contribuzione)
- **Margine di sicurezza** = (Vendite attuali - Vendite BEP) / Vendite attuali x 100
- **Leva operativa** = MC totale / Utile operativo

Interpreta:
- Margine sicurezza sotto 20%: "Sei troppo vicino al pareggio. Un calo del 15% nei volumi ti porta in perdita."
- Leva operativa alta (sopra 4-5): "La tua struttura di costi fissi amplifica sia i guadagni che le perdite. Un +10% di fatturato diventa +40% di utile, ma vale anche al contrario."

Usa i riferimenti in `references/analisi-cvr-pmi.md` per il framework completo.

### Step 3: Analisi Mix — Prodotti Star vs Dog

Classifica ogni prodotto su due dimensioni:
- **MC%** (alto/basso rispetto alla media del catalogo)
- **Volume** (alto/basso rispetto alla media)

Matrice:
| | MC% Alto | MC% Basso |
|---|---|---|
| **Volume Alto** | STAR — proteggere e investire | VOLUME — aumentare prezzo o ridurre cv |
| **Volume Basso** | NICCHIA — valutare crescita | DOG — ripensare o eliminare |

Per ogni prodotto indica la categoria e l'azione suggerita.

Tono: "Il tuo corso avanzato e una star: margine alto e buoni volumi. La consulenza base invece e un dog: margine basso e pochi clienti. Vale la pena tenerla?"

### Step 4: Simulazione Pricing

Per ogni prodotto/servizio simula variazioni di prezzo: -20%, -15%, -10%, -5%, +5%, +10%, +15%, +20%.

Per ogni scenario stima:
- **Variazione volume attesa** (usando elasticita stimata per tipologia: commodity ~1.5-2.5, servizio differenziato ~0.3-0.8, premium ~0.1-0.5)
- **Nuovo MC unitario e totale**
- **Nuovo utile operativo**
- **Nuovo BEP e margine di sicurezza**

Evidenzia gli scenari piu favorevoli per l'obiettivo dell'utente.

Tono: "Se alzi il prezzo del servizio X del 10% (da 80 EUR a 88 EUR), con un'elasticita stimata di 0.5 perdi circa il 5% dei clienti. Ma il tuo MC sale da 35 EUR a 43 EUR (+23%). Risultato: guadagni 2.800 EUR in piu al mese anche con meno clienti."

Usa `references/strategie-pricing.md` per supportare le raccomandazioni.

### Step 5: Raccomandazione Pricing con Scenari

Presenta 3 scenari:
1. **Conservativo**: aggiustamenti minimi (+5-10% sui prodotti con MC% alto e bassa elasticita)
2. **Ottimale**: combinazione di aumenti mirati e riposizionamento mix
3. **Aggressivo**: rialzo significativo con possibile perdita volume, focus su premium

Per ogni scenario indica:
- Variazioni di prezzo per prodotto
- Impatto stimato su fatturato, MC totale, utile
- Rischi e condizioni per il successo
- Tempistica suggerita per l'implementazione

Aggiungi raccomandazioni trasversali:
- Bundling se applicabile
- Pricing psicologico (99 EUR vs 100 EUR, ancoraggio)
- Discriminazione prezzo per segmento se fattibile
- Aggiornamento periodico listino

---

## Skill Invocate

Durante l'esecuzione, invoca le seguenti skill per approfondimenti:

- **`programmazione-controllo`** — per il framework CVR, BEP, classificazione costi, leva operativa
- **`controllo-gestione-bocconi`** — per analisi scostamenti e centri di responsabilita
- **`marketing-strategico`** — per posizionamento di prezzo e strategia competitiva
- **`psicologia-marketing`** — per percezione del prezzo, ancoraggio, decoy effect
- **`casi-numerici-bocconi`** — per benchmark e validazione calcoli
- **`xlsx`** — per generare il file Excel con simulatore interattivo

---

## Deliverable

### 1. XLSX — Simulatore Pricing Interattivo
Genera con la skill `xlsx`. Struttura a 4 tab come da `assets/template-pricing-xlsx.md`.
Tutte le formule devono essere vive (non valori statici) cosi che l'utente possa modificare input e vedere risultati aggiornati.

### 2. Report DOCX — 8-10 pagine
Struttura:
1. Executive Summary (1 pag)
2. Mappatura Margini (1-2 pag con tabella)
3. Analisi CVR e BEP (1-2 pag con grafici)
4. Analisi Mix (1 pag con matrice)
5. Simulazioni Pricing (2-3 pag con tabelle scenari)
6. Raccomandazioni e Piano d'Azione (1-2 pag)

### 3. JSON — Output Strutturato
Conforme allo schema in `schemas/output-schema.json`.

---

## Tono e Stile

Consulente che parla di numeri in modo concreto e diretto. Mai accademico, sempre applicativo.

Esempi:
- "Il tuo servizio X ti costa 45 EUR e lo vendi a 80 EUR: margine 44%. Ma paga il 60% dei tuoi costi fissi."
- "Se lo alzi a 90 EUR e perdi il 10% dei clienti, guadagni comunque di piu. Facciamo i conti."
- "Stai vendendo il prodotto Y a 25 EUR con un margine del 12%. Per ogni pezzo venduto ti restano 3 EUR. Ne devi vendere 3.333 al mese solo per coprire i costi fissi."
- "La tua leva operativa e 4.2: ogni punto percentuale di fatturato in piu vale 4.2 punti di utile. Ma anche al contrario."

Usa sempre numeri concreti del cliente, mai generici. Mostra i calcoli passo per passo.
