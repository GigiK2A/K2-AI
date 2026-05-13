---
name: flusso-advisorboost-pmi
description: Orchestratore AdvisorBoost — diagnosi strategico-finanziaria integrata PMI italiane 5-50 dipendenti con riclassificazione bilancio, 5 forze Porter, VRIO, piano 12-36 mesi, cruscotto KPI. Trigger "AdvisorBoost", "diagnosi strategica e finanziaria", "advisor PMI", "consulenza integrata PMI", "business advisor", "il commercialista non mi basta", "dove va la mia azienda", "piano strategico e finanziario", "consulenza imprenditoriale", "diagnosi completa PMI", "revisione strategica", "consulente generalista", "CFO esterno", "temporary manager finanziario", "piano crescita e risanamento", "business plan e bilancio". Servizio 1.999-3.999 EUR one-shot + 299 EUR/mese retainer. Integra bilancio 3 anni, settore, posizionamento, KPI operativi, proiezione 36 mesi con scenari, azioni prioritarie. Core vendita diretta dal titolare o dal commercialista. Attivala quando la PMI chiede advisor a 360 gradi.
---

# flusso-advisorboost-pmi

Orchestratore AdvisorBoost. Consulenza strategico-finanziaria integrata per PMI italiane 5-50 dipendenti. Il titolare riceve una diagnosi completa che fonde analisi di bilancio, posizionamento competitivo, benchmark settore e piano operativo 12-36 mesi. E il verticale che sostituisce il "business advisor umano" per le PMI che non hanno un CFO interno.

## Panoramica

AdvisorBoost e il secondo livello premium del funnel:
- **Primo livello (tripwire)**: `check-pmi-express` — pagellino 0-100 gratuito o 49 EUR.
- **Core (questo)**: `flusso-advisorboost-pmi` — diagnosi completa 1.999-3.999 EUR + 299 EUR/mese opzionale.
- **Upsell**: retainer mensile 299 EUR per aggiornamento cruscotto KPI, call trimestrale, supporto decisionale su richiesta.

Il cliente tipo e un titolare di PMI manifatturiera / servizi B2B / retail specializzato / studio professionale che:
1. Non ha un controller o CFO interno.
2. Il commercialista fa solo compliance fiscale.
3. Sente il bisogno di una direzione strategica integrata (non solo bilancio, non solo marketing).
4. Vuole decidere se investire, acquisire, cedere, crescere, cambiare posizionamento.

AdvisorBoost combina quello che oggi richiederebbe 3 consulenti separati (commercialista analitico + strategy consultant + business coach) in un deliverable integrato.

## Input

### Obbligatori
- **Bilanci ultimi 3 anni** (PDF, XLSX, bilancio XBRL da camerale, o dati grezzi in chat).
- **Nome azienda, settore ATECO, numero dipendenti, fatturato**.
- **Descrizione cliente tipo** (chi sono, cosa acquistano, perche scelgono noi).
- **3-5 competitor principali** (nomi, zona geografica).
- **Obiettivi a 36 mesi** (crescita fatturato? marginalita? cessione? successione? internazionalizzazione? turnaround?).

### Raccomandati
- **Ultimi 2 scostamenti budget vs actual** (se esistono).
- **Mix ricavi per linea di prodotto/servizio** (se disponibile).
- **KPI operativi attuali** (LTV, CAC, churn, ticket medio, ore fatturate, ecc.).
- **Organigramma** o breve descrizione ruoli chiave.
- **Fonti di vantaggio competitivo percepite** (rispondere con 3 punti).

### Opzionali
- Ricerche di mercato fatte.
- Questionari clienti recenti.
- Business plan vecchi.
- Contratti chiave (supply, clienti top, finanziamenti).

## Workflow 7-step

### Step 1 — Analisi bilancio storico (3 anni)
Invoca `analisi-bilancio-pmi` e `bilancio-consolidato-analisi`. Produce:
- Riclassificazione SP (a liquidita/esigibilita + funzionale) e CE (a valore aggiunto + a costo del venduto).
- Calcolo 25+ indici: redditualita (ROE, ROI, ROS, Du Pont scomposto), solidita (D/E, copertura immobilizzazioni, quoziente di struttura), liquidita (current, quick, CCC), efficienza (rotazione attivo, giorni crediti/debiti/magazzino).
- Trend 3 anni con CAGR fatturato, margini, EBITDA, PFN.
- Rendiconto finanziario metodo indiretto con quadratura.
- Alert automatici su crisi d'impresa (indici allerta CCII).

### Step 2 — Analisi settore e competitivo
Invoca `analisi-settore-pmi`, `strategia-competitiva`, `posizionamento-strategico`, `check-competitivo-express`. Produce:
- 5 forze Porter scorate 1-5 con variabili ed evidenze.
- Dinamiche settoriali (life-cycle, PNRR, digitalizzazione, ESG).
- Raggruppamenti strategici con mappa 2D.
- Posizionamento cliente: catena valore Porter, fonti vantaggio competitivo, test difendibilita.
- Competitive Index 0-100 vs 3-5 competitor nominati.

### Step 3 — Analisi risorse e competenze (VRIO)
Invoca `strategia-grant-bocconi`. Produce:
- Elenco risorse tangibili e intangibili.
- Test VRIO per ognuna (Valore, Rarita, Inimitabilita, Organizzazione).
- Core competencies identificate.
- Capacita dinamiche: sensing, seizing, reconfiguring.
- Gap di competenze da colmare per obiettivi 36 mesi.

### Step 4 — Benchmark integrato
Invoca `benchmark-italia-business` + tabelle locali in `references/benchmark-pmi-integrato.md`. Produce:
- Confronto 10 KPI chiave vs settore ATECO e vs fascia dimensionale.
- Identificazione aree "sotto mediana" e "sopra top quartile".
- Gap-analysis quantitativa con targeting 3 anni.

### Step 5 — Scenario strategico e opzioni
Invoca `piano-crescita-pmi`, `teoria-dei-giochi-decisioni`. Produce:
- Matrice Ansoff applicata: 4 opzioni (penetrazione, sviluppo prodotto, sviluppo mercato, diversificazione).
- Per ogni opzione: scoring attrattivita × fattibilita × rischio.
- Test gioco competitivo: reazione probabile dei 3 competitor principali per ogni opzione scelta.
- Raccomandazione 1 opzione primaria + 1 di riserva.

### Step 6 — Piano economico-finanziario 36 mesi
Invoca `budget-forecast-pmi`, `casi-numerici-bocconi`. Produce:
- Budget economico mensilizzato 36 mesi (ricavi per linea, costi fissi/variabili, EBITDA, utile netto).
- Budget finanziario: cash flow, fabbisogno circolante, piano incassi/pagamenti.
- 3 scenari: base, ottimistico (+15% ricavi, +2pp margine), pessimistico (-10% ricavi, -2pp margine, +20gg incassi).
- Sensitivity analysis su 3 variabili chiave.
- Calcolo enterprise value con 3 metodi (multipli EBITDA, DCF, patrimoniale), valore finale raccomandato.

### Step 7 — Piano azioni prioritarie
Selezione 5-8 azioni ad alto impatto strutturate come mini-progetti:
- Titolo, descrizione, categoria (Strategia/Marketing/Operation/Finance/HR/Sistemi).
- Impatto stimato su EBITDA e/o fatturato.
- Fattibilita (alta/media/bassa).
- Costo una tantum + ricorrente mensile.
- Tempi implementazione (settimane).
- Responsabile interno consigliato.
- KPI per misurare avanzamento.
- Milestone 30-60-90 giorni.

## Output

### 1. Report DOCX executive (30-40 pagine)
Template in `assets/template-report-advisor.md`. Sezioni:
1. Executive summary 1 pagina (score globale, top 3 temi, 3 decisioni suggerite).
2. Chi siamo oggi (snapshot azienda, storia, mercato).
3. Analisi di bilancio 3 anni (riclassificazione, indici, trend, rendiconto).
4. Analisi settore (Porter, dinamiche, benchmark).
5. Posizionamento competitivo (catena valore, VRIO, mappa).
6. Opzioni strategiche e raccomandazione.
7. Piano economico-finanziario 36 mesi (3 scenari, sensitivity).
8. Piano azioni prioritarie (5-8 mini-progetti).
9. Cruscotto KPI mensile proposto.
10. Disclaimer + metodologia + fonti.

### 2. Cruscotto XLSX operativo
Template in `assets/template-cruscotto-advisor-xlsx.md`. 7 tab:
- Tab 1 — Bilancio riclassificato 3 anni + proiezione 3 anni.
- Tab 2 — Indici di bilancio + benchmark + semaforo.
- Tab 3 — Budget mensile 36 mesi (economico + finanziario).
- Tab 4 — Scenari (base/ottimistico/pessimistico).
- Tab 5 — KPI operativi mensili (input utente + grafici).
- Tab 6 — Piano azioni con GANTT.
- Tab 7 — Enterprise value (multipli, DCF, patrimoniale).

Formule vive ovunque. Validazioni, formattazione condizionale, grafici embedded.

### 3. Dashboard HTML single-page
Template in `assets/template-dashboard-advisor-html.md`. Self-contained, Chart.js, sezioni:
- Hero score strategico 0-100 + giudizio + percentile settore.
- KPI cards 4 (EBITDA, ROI, D/E, Crescita).
- Grafici: trend 3 anni + proiezione 3 anni, scenari, mix ricavi, mappa Porter radar.
- Tabella azioni prioritarie.
- CTA retainer 299 EUR/mese.

### 4. JSON strutturato
Schema in `schemas/output-schema.json`. Output programmatico per integrazioni future (CRM cliente, portale K2-AI).

## Pricing

| Modalita | Prezzo | Contenuto |
|---|---|---|
| AdvisorBoost Light | 1.999 EUR | Report DOCX + JSON, senza cruscotto XLSX ne dashboard HTML. Base per PMI < 500k fatturato. |
| AdvisorBoost Standard | 2.999 EUR | Pacchetto completo (DOCX + XLSX + HTML + JSON). Base per PMI 500k-5M fatturato. |
| AdvisorBoost Pro | 3.999 EUR | Pacchetto Standard + 2 call da 90 min (kick-off + presentazione risultati) + revisione a 30 giorni. PMI > 2M fatturato. |
| Retainer mensile | 299 EUR/mese | Aggiornamento cruscotto, 1 call 60 min/mese, supporto asincrono email. Minimo 6 mesi. |

## Tono di comunicazione

- **Diretto come il commercialista esperto, ma con visione strategica che il commercialista non ha**.
- Mai jargon consulenziale vuoto ("sinergie", "best practice", "leverage strategico"). Sempre numeri e decisioni.
- Sempre benchmark di settore come contesto.
- Quando si dice "fa questa mossa", dire anche "se non funziona, questo e il piano B".
- Il titolare deve chiudere il report con **3 decisioni chiare da prendere entro 30 giorni**. Non 50 spunti generici.

## Regole operative

1. **Riservatezza assoluta**: i dati di bilancio non escono mai da Cowork in formato elaborato con nomi. File con dati sensibili sempre con slug anonimo.
2. **Fonte dichiarata per ogni benchmark**: citare sempre `scoring-model-host.md 2025-Q4` o `benchmark-italia-business` con riferimento alla sezione.
3. **Disclaimer obbligatorio**: "La presente diagnosi e un supporto decisionale. Non costituisce servizio di revisione contabile ne consulenza fiscale. Le proiezioni sono stime."
4. **Non sostituire il commercialista**: per atti fiscali, dichiarazioni, valutazioni giurate rimandare sempre al professionista abilitato.
5. **Se l'azienda e in crisi conclamata** (DSCR < 1, PFN/EBITDA > 6, perdite > 1/3 del capitale): segnalare esplicitamente la soglia di allerta CCII e consigliare consulenza specialistica di composizione negoziata.

## Collegamenti con altre skill

Invoca in sequenza:
- `analisi-bilancio-pmi`, `bilancio-consolidato-analisi`, `contabilita-bilancio`
- `analisi-settore-pmi`, `strategia-competitiva`, `strategia-grant-bocconi`, `posizionamento-strategico`
- `budget-forecast-pmi`, `corporate-finance`, `casi-numerici-bocconi`
- `piano-crescita-pmi`, `teoria-dei-giochi-decisioni`
- `check-salute-finanziaria`, `check-competitivo-express` (per screening rapido)
- `benchmark-italia-business`, `programmazione-controllo`, `controllo-gestione-bocconi`

Deriva lead da:
- `check-pmi-express` (tripwire 49 EUR)
- `check-salute-finanziaria`, `check-competitivo-express` (pagellini verticali)
- Campagne LinkedIn K2-AI B2B

Redirige verso upselling:
- Verticali specifici: `flusso-financeboost-pmi`, `flusso-strategyboost-pmi`, `flusso-webboost-pmi` se il cliente vuole deep dive tematico.

## Errori comuni da evitare

- **Non confondere con analisi di bilancio singola**: AdvisorBoost e integrato strategia + finanza, non un semplice bilancio analitico.
- **Non proporre interventi giganteschi non implementabili**: la PMI ha 5-50 dipendenti, non una BU di 500. Tutte le azioni devono essere realizzabili dal titolare con le risorse attuali o con un'assunzione/consulenza incrementale.
- **Non fare forecast a 5-10 anni**: il PMI italiano non ha visibilita oltre 36 mesi. Stop.
- **Non dimenticare il retainer**: il modello economico K2-AI si basa sul ricorrente. Il report finale deve rendere evidente il valore del retainer 299 EUR/mese.
- **Non ignorare il commercialista del cliente**: AdvisorBoost e complementare, non sostitutivo. Dedicare 1 paragrafo a "come questo si integra con il tuo commercialista e il tuo consulente del lavoro".

## Esempio use-case

> Titolare di uno studio di progettazione TLC (proprio profilo K2-AI). 7 dipendenti, 900k fatturato, cliente principale Iliad Italia. Vuole capire se cercare nuovi clienti, acquisire uno studio piccolo, diversificare in TIM, o uscire dal mercato in 5 anni. AdvisorBoost produce: diagnosi finanziaria 3 anni (margini sani ma concentrazione cliente al 78%), analisi settore (Iliad rallenta investimenti 2026, Cellnex stabile, TIM-WindTre consolidando fornitori), posizionamento (studio specialistico con forte reputazione iliad ma debole brand), piano 36 mesi con 3 scenari e raccomandazione "diversificazione Cellnex + acquisizione studio lombardo entro 18 mesi", piano azioni 6 punti con costi e ROI. Risultato pagato 2.999 EUR, retainer 299 EUR/mese attivo per 12 mesi. Valore percepito > 20k EUR.
