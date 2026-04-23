---
name: budget-forecast-pmi
description: >-
  Costruzione budget previsionale 12 mesi per PMI italiane con analisi scostamenti e scenari.
  Partendo dal bilancio storico e dalle ipotesi del titolare (crescita fatturato, nuovi costi,
  investimenti), produce un budget economico mensile (ricavi per linea, costi fissi e variabili,
  margini, EBITDA, utile netto), un budget finanziario (flussi di cassa, fabbisogno circolante,
  piano incassi e pagamenti), tre scenari (base, ottimistico, pessimistico) con sensitivity
  analysis sulle variabili chiave, e un template per analisi scostamenti a consuntivo.
  Deliverable: XLSX con formule vive modificabili dal titolare, report DOCX sintetico, JSON
  strutturato. Tono pratico orientato alla decisione per imprenditori senza controller.
  Prezzo 399 EUR.
---

# budget-forecast-pmi

Budget previsionale 12 mesi con analisi scostamenti e scenari per PMI italiane.

## Trigger

Questa skill si attiva quando l'utente menziona:

- "budget", "previsionale", "forecast"
- "pianificazione finanziaria", "budget aziendale"
- "quanto guadagnerò", "previsione costi ricavi"
- "budget 12 mesi", "piano economico"
- "scostamenti budget", "analisi varianze"

## Input richiesti

1. **Bilancio ultimo anno** (o dati principali: fatturato, costi, utile, struttura patrimoniale)
2. **Ipotesi di crescita fatturato** (percentuale attesa, nuove linee di ricavo)
3. **Costi previsti nuovi** (assunzioni, affitti, servizi aggiuntivi)
4. **Investimenti pianificati** (macchinari, tecnologia, capex)
5. **Settore** di appartenenza (per benchmark e stagionalità tipica)

## Workflow — 5 step

### Step 1: Analisi struttura costi/ricavi storica

Analizzare il bilancio storico per identificare:

- **Costi fissi vs variabili**: classificare ogni voce di costo. Fissi = affitto, stipendi base, ammortamenti, utenze fisse. Variabili = materie prime, provvigioni, trasporti, lavorazioni esterne.
- **Incidenza percentuale**: calcolare il peso di ogni voce sul fatturato (es. materie prime 35%, personale 28%).
- **Stagionalità**: dai dati mensili storici (se disponibili) o da benchmark settoriali, costruire il profilo di distribuzione mensile del fatturato (es. picco novembre-dicembre per retail).
- **Trend**: variazioni anno su anno, margini in miglioramento o peggioramento.

Invocare `programmazione-controllo` per la classificazione costi e `controllo-gestione-bocconi` per i framework analitici.

### Step 2: Costruzione budget economico 12 mesi

Costruire il Conto Economico previsionale mese per mese:

- **Ricavi per linea**: scomporre il fatturato per linea di business/prodotto, applicare crescita differenziata e curva di stagionalità.
- **Costi variabili**: legati ai ricavi con % storiche (aggiustate per ipotesi).
- **Margine di contribuzione**: ricavi - costi variabili, per linea e totale.
- **Costi fissi**: distribuiti sui 12 mesi (attenzione a tredicesima/quattordicesima, rinnovi contrattuali).
- **Budget personale**: retribuzione lorda + contributi INPS 33% + TFR 7.4% + IRAP 3.9% = costo aziendale completo.
- **Ammortamenti**: piano ammortamento investimenti nuovi ed esistenti.
- **EBITDA, EBIT, utile ante imposte, utile netto**: con aliquota IRES 24% + IRAP 3.9%.

Invocare `casi-numerici-bocconi` per la risoluzione dei calcoli e le verifiche di coerenza.

### Step 3: Budget finanziario

Costruire il piano dei flussi di cassa mensili:

- **Incassi**: ricavi sfasati per giorni medi di incasso (DSO). Se DSO = 60gg, il fatturato di gennaio si incassa a marzo.
- **Pagamenti**: costi sfasati per giorni medi di pagamento (DPO). Fornitori a 30/60/90gg.
- **IVA**: debito/credito IVA mensile, liquidazioni trimestrali o mensili.
- **Imposte**: acconti e saldi IRES/IRAP secondo scadenze fiscali.
- **Investimenti**: uscite di cassa per capex (non ammortamento).
- **Saldo mensile e saldo cumulato**: evidenziare mesi di fabbisogno finanziario.
- **Fabbisogno di linee di credito**: se il saldo cumulato diventa negativo, quantificare l'affidamento necessario.

Invocare `corporate-finance` per la modellazione dei flussi e la stima del fabbisogno.

### Step 4: Analisi scenari

Costruire 3 scenari con riepilogo annuo:

- **Scenario base**: ipotesi realistiche fornite dal titolare.
- **Scenario ottimistico**: ricavi +20% rispetto a base, costi variabili proporzionali, costi fissi stabili. Ipotesi: mercato favorevole, nuovo cliente grande, stagione forte.
- **Scenario pessimistico**: ricavi -15% rispetto a base, costi fissi rigidi (non riducibili nel breve), costi variabili proporzionali ridotti. Ipotesi: perdita cliente, crisi settoriale, ritardi pagamenti.

Per ogni scenario calcolare: fatturato, margine contribuzione, EBITDA, utile netto, cash flow cumulato, mese di break-even temporale.

**Sensitivity analysis**: identificare le 3-4 variabili che spostano di piu l'utile:
- Variazione fatturato (+/-10%)
- Variazione costo materie prime (+/-5%)
- Variazione DSO (+/-15 giorni)
- Variazione numero dipendenti (+/-1)

Mostrare impatto su utile e cash flow per ogni variazione.

### Step 5: Template per analisi scostamenti a consuntivo

Fornire il framework per il monitoraggio mensile:

- **Scostamento ricavi** = scostamento prezzo + scostamento quantita (scomposto).
- **Scostamento costi** = scostamento prezzo + scostamento efficienza.
- **Scostamento margine** = effetto volume + effetto mix + effetto prezzo + effetto efficienza.
- **Budget flessibile vs budget statico**: ricalcolare il budget ai volumi effettivi per isolare la componente volume.
- **Template mensile**: colonne Budget | Consuntivo | Scostamento | Causa | Azione correttiva.
- **Soglie di attenzione**: scostamento oltre 5% = giallo (monitorare), oltre 10% = rosso (intervenire).

Invocare `controllo-gestione-bocconi` per il framework teorico degli scostamenti.

## Skill invocate

- `programmazione-controllo` — classificazione costi, centri di responsabilita, budget per centri
- `controllo-gestione-bocconi` — framework analitico scostamenti, reporting direzionale
- `casi-numerici-bocconi` — calcoli numerici, verifiche di coerenza, esercizi applicativi
- `corporate-finance` — modellazione flussi di cassa, valutazione fabbisogno, analisi investimenti
- `xlsx` — generazione file Excel con formule vive, grafici, tab strutturate

## Deliverable

### 1. XLSX — Budget completo con formule vive

File Excel con 6 tab (vedi `assets/template-budget-xlsx.md`):
- Tab Ipotesi: tutte le variabili modificabili dal titolare
- Tab Budget Economico: CE previsionale 12 mesi con formule collegate a Ipotesi
- Tab Budget Finanziario: flussi di cassa mensili
- Tab Scenari: riepilogo annuo base/ottimistico/pessimistico
- Tab Scostamenti: template pronto per inserire il consuntivo
- Tab Dashboard: grafici riassuntivi

Il titolare modifica le ipotesi e tutto ricalcola automaticamente.

Generare tramite skill `xlsx`.

### 2. DOCX — Report sintetico

Documento di 4-6 pagine con:
- Executive summary (1 pagina): numeri chiave, rischi, opportunita
- Ipotesi utilizzate e fonti
- Commento ai 3 scenari con raccomandazioni
- Piano d'azione: cosa monitorare mensilmente, quando rivedere il budget

### 3. JSON — Output strutturato

Conforme a `schemas/output-schema.json`: tutti i dati numerici del budget in formato machine-readable per integrazioni con gestionali o dashboard BI.

## Tono e stile

Pratico, diretto, orientato alla decisione. Il destinatario e un titolare di PMI, non un CFO di multinazionale.

Esempi di comunicazione:
- "Se il fatturato cresce del 10% e assumi 2 persone, ecco cosa succede al tuo utile."
- "Con questi numeri, a luglio ti servono 45.000 EUR di fido bancario. Meglio parlarne con la banca adesso."
- "Il tuo margine regge fino a un calo del 12% del fatturato. Oltre, vai in perdita."

Non usare gergo tecnico senza spiegarlo. Ogni numero deve avere un "e quindi?" — cosa significa per l'imprenditore.
