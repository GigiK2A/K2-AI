---
name: piano-crescita-pmi
description: >-
  Piano di crescita strategico per PMI italiane con matrice Ansoff, valutazione opzioni e business plan semplificato.
  Trigger: "piano di crescita", "come crescere", "espandermi", "nuovo mercato", "nuovo prodotto", "diversificare",
  "Ansoff", "internazionalizzazione", "acquisizione", "business plan", "piano strategico", "aprire una nuova sede",
  "fare rete", "alleanza strategica". Input: azienda (settore, fatturato, dipendenti, prodotti/servizi), obiettivo
  crescita (fatturato target, mercato, orizzonte), risorse disponibili, vincoli. Workflow 5 step: analisi posizione
  attuale, mappatura opzioni Ansoff con make/buy/ally, scoring attrattivita x fattibilita x rischio, business plan
  con proiezione 3 anni BEP/ROI, piano azione con milestone. Invoca strategia-grant-bocconi,
  strategia-competitiva, corporate-finance, teoria-dei-giochi-decisioni, casi-numerici-bocconi,
  benchmark-italia-business. Output: DOCX 12-15 pagine, XLSX proiezioni, JSON. Prezzo 599 euro.
---

# piano-crescita-pmi

Piano di crescita strategico per PMI italiane: matrice Ansoff, valutazione opzioni, business plan semplificato con proiezioni finanziarie a 3 anni.

## Panoramica

Questa skill genera un piano di crescita completo per PMI italiane (5-250 dipendenti, fatturato 500k-50M). Il titolare o il management descrive la propria azienda, l'obiettivo di crescita e le risorse disponibili; riceve un report strategico con 4 opzioni Ansoff valutate, una raccomandazione motivata, un business plan semplificato con numeri concreti e un piano d'azione con milestone.

## Input

### Obbligatori
- **Settore**: manifatturiero, servizi, commercio, ristorazione, edilizia, IT, trasporti, professionisti, altro
- **Fatturato attuale**: ricavi netti annui (ultimo esercizio)
- **Numero dipendenti**: organico attuale
- **Prodotti/servizi attuali**: descrizione sintetica dell'offerta corrente
- **Obiettivo di crescita**: fatturato target o percentuale di crescita desiderata
- **Orizzonte temporale**: entro quando (tipicamente 1-5 anni)

### Opzionali (migliorano la qualita dell'analisi)
- **Mercato target**: area geografica o segmento desiderato
- **Budget disponibile per investimento**: quanto si puo investire nella crescita
- **Competenze distintive**: cosa sa fare bene l'azienda rispetto ai concorrenti
- **Capacita produttiva residua**: se c'e margine per produrre di piu senza investire
- **Vincoli**: limiti finanziari, organizzativi, normativi, geografici
- **Trend settore**: il mercato sta crescendo, stabile o in calo
- **Margine operativo attuale**: EBITDA o margine netto percentuale
- **Clienti principali**: concentrazione clienti, tipologia (B2B/B2C)

## Workflow

### Step 1 - Analisi posizione attuale

Analizza la posizione competitiva dell'azienda partendo dai dati forniti:
- Fatturato, trend ultimi anni, margini
- Competenze distintive e risorse chiave
- SWOT sintetica (4-6 punti per quadrante)
- Posizionamento nel settore rispetto ai benchmark

**Skill invocata**: `strategia-grant-bocconi` per framework di analisi delle risorse e competenze distintive.

**Skill invocata**: `benchmark-italia-business` per confronto con mediane di settore.

### Step 2 - Mappatura opzioni crescita su matrice Ansoff

Per ciascuno dei 4 quadranti Ansoff, genera un'opzione concreta e specifica per l'azienda:

1. **Penetrazione mercato**: come aumentare quota sul mercato attuale (pricing, promozioni, CRM, forza vendita, fidelizzazione)
2. **Sviluppo prodotto**: quali nuovi prodotti/servizi offrire ai clienti attuali (R&D, partnership, licenze, servizi accessori)
3. **Sviluppo mercato**: come portare i prodotti attuali in nuovi mercati (export, nuove aree geografiche, nuovi segmenti, e-commerce, nuovi canali)
4. **Diversificazione**: nuovi prodotti per nuovi mercati (correlata con sinergie vs conglomerata)

Per ogni opzione, valuta la modalita di esecuzione:
- **Make** (crescita interna/organica): sviluppo con risorse proprie
- **Buy** (crescita esterna/M&A): acquisizione di azienda, ramo d'azienda, brevetti
- **Ally** (crescita collaborativa): alleanze, reti d'impresa, consorzi, franchising, joint venture

Usa il framework di `references/opzioni-crescita-pmi.md` come guida.

**Skill invocata**: `strategia-competitiva` per analisi delle dinamiche competitive e posizionamento.

**Skill invocata**: `teoria-dei-giochi-decisioni` per valutare scenari di reazione competitiva e scelte make/buy/ally.

### Step 3 - Valutazione opzioni con scoring

Per ogni opzione, assegna un punteggio 1-5 su tre dimensioni:
- **Attrattivita** (1-5): dimensione opportunita, crescita attesa, marginalita potenziale
- **Fattibilita** (1-5): coerenza con risorse, competenze, tempi, complessita esecutiva
- **Rischio** (1-5 invertito: 5=rischio basso, 1=rischio alto): rischio finanziario, operativo, di mercato

**Score composito** = Attrattivita x 0.35 + Fattibilita x 0.40 + Rischio x 0.25

Presenta una tabella comparativa e raccomanda l'opzione con score piu alto, motivando la scelta. Se due opzioni hanno score simili, discuti i trade-off.

### Step 4 - Business plan semplificato

Per l'opzione raccomandata (e eventualmente la seconda classificata), elabora un business plan semplificato seguendo il template di `references/business-plan-semplificato.md`:

- **Opportunita**: cosa, per chi, perche ora
- **Modello economico**: ricavi previsti, costi variabili, costi fissi incrementali, margine di contribuzione
- **Investimento richiesto**: quanto serve, per cosa, fonti di finanziamento possibili
- **Proiezione 3 anni**: P&L sintetico anno per anno, cash flow cumulato
- **BEP**: break-even point in mesi
- **ROI**: ritorno sull'investimento al terzo anno
- **Top 3 rischi**: con probabilita, impatto e piano di mitigazione

**Skill invocata**: `corporate-finance` per modelli di valutazione finanziaria, calcolo BEP, ROI, analisi di sensitivita.

**Skill invocata**: `casi-numerici-bocconi` per rigore nei calcoli e impostazione delle proiezioni finanziarie.

### Step 5 - Piano d'azione con milestone

Definisci un piano d'azione operativo con:
- **6-8 milestone** distribuite sull'orizzonte temporale (tipicamente 18-36 mesi)
- Per ogni milestone: attivita chiave, responsabile suggerito, investimento cumulato, KPI di verifica
- **Gantt semplificato**: rappresentazione temporale delle attivita principali
- **Quick win**: 2-3 azioni da avviare entro 30 giorni
- **Checkpoint di revisione**: ogni 3-6 mesi con criteri go/no-go

## Regole di comunicazione

- **Tono pragmatico e numerico**: ogni raccomandazione deve avere un numero attaccato. "L'opzione B (sviluppo di mercato nel triveneto) richiede 80k euro di investimento, raggiunge il BEP in 14 mesi, e ha un ROI atteso del 35% al terzo anno. E la scelta migliore dato il tuo profilo di rischio."
- **Mai teoria senza applicazione**: ogni concetto strategico (Ansoff, make/buy/ally) deve essere tradotto in azione concreta per quella specifica azienda
- **Confronto chiaro**: le opzioni devono essere comparabili con numeri e tabelle, non con descrizioni vaghe
- **Linguaggio da imprenditore**: evitare gergo accademico. "Penetrazione mercato" diventa "vendere di piu ai clienti che gia hai e rubare clienti ai concorrenti"
- **Onesta sui rischi**: non vendere illusioni. Se un'opzione e rischiosa, dirlo chiaramente con numeri
- **Orientamento alla decisione**: il deliverable deve portare il titolare a dire "ok, facciamo questa, partiamo lunedi"

## Skill invocate

- `strategia-grant-bocconi`: analisi risorse, competenze distintive, framework strategico
- `strategia-competitiva`: dinamiche competitive, posizionamento, barriere
- `corporate-finance`: valutazione finanziaria, BEP, ROI, analisi sensitivita
- `teoria-dei-giochi-decisioni`: scenari competitivi, decisioni make/buy/ally
- `casi-numerici-bocconi`: rigore numerico nelle proiezioni finanziarie
- `benchmark-italia-business`: benchmark settoriali italiani per confronto
- `docx`: generazione report DOCX formattato
- `xlsx`: generazione foglio Excel con proiezioni finanziarie

## Output

Tre file consegnati:

1. **Report DOCX** (`piano-crescita-[azienda].docx`): report 12-15 pagine secondo il template in `assets/template-piano-crescita.md`
2. **Foglio XLSX** (`proiezioni-crescita-[azienda].xlsx`): proiezioni finanziarie a 3 anni con P&L, cash flow, BEP, ROI, analisi sensitivita
3. **JSON strutturato** (`piano-crescita-[azienda].json`): dati machine-readable secondo lo schema in `schemas/output-schema.json`

## Pricing

599 euro per PMI italiane. Include report DOCX, foglio XLSX con proiezioni e JSON strutturato.
