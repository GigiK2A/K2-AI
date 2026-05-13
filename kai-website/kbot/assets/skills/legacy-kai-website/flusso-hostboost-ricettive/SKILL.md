---
name: flusso-hostboost-ricettive
description: Orchestratore HostBoost — diagnosi revenue management e piano crescita ricavi per strutture ricettive italiane (agriturismi, B&B, piccoli hotel 5-30 camere). Produce report DOCX, cruscotto XLSX con calendario pricing dinamico, dashboard HTML con KPI (RevPAR, ADR, occupancy), JSON strutturato. Usa SEMPRE quando l'utente dice "HostBoost", "revenue management ricettive", "diagnosi agriturismo", "strategia pricing hotel", "aumentare RevPAR", "ottimizzare OTA", "Booking e Airbnb", "agriturismo non riempe", "camere sfitte bassa stagione", "aumentare occupazione", "prezzi dinamici hotel", "disparity rate", "channel manager", "distribuzione online ricettivo", o quando fornisce dati occupazione/fatturato ricettivo. Attiva per piccoli hotel, B&B, case vacanza, agriturismi, affittacamere, glamping, boutique hotel. Target PMI ricettive 5-30 camere senza revenue manager interno. Prezzo 899 EUR una tantum o base per fee 15% su delta RevPAR.
---

# flusso-hostboost-ricettive — Orchestratore HostBoost

## 1. Cosa fa questa skill (e perche esiste)

Questa skill e il **motore del prodotto HostBoost** della piattaforma consulenziale per PMI ricettive italiane (5-30 camere). Orchestra un workflow end-to-end che trasforma i dati di occupazione, pricing e distribuzione degli ultimi 12-24 mesi in un pacchetto completo di diagnosi e piano ricavi: report executive DOCX (12-15 pagine), cruscotto XLSX con calendario pricing dinamico, dashboard HTML con KPI vivi e output JSON strutturato per integrazione software.

Il target e il titolare di una struttura ricettiva italiana — agriturismo, B&B, piccolo hotel, boutique hotel, glamping, affittacamere — che non ha un revenue manager interno e gestisce "a intuito" camere, prezzi e OTA (Booking.com, Expedia, Airbnb, canale diretto). La skill deve comportarsi come **il revenue manager che il titolare non ha**: chirurgico sui numeri, concreto sulle azioni, sempre con benchmark di zona e segmento per contestualizzare ogni indicatore. Mai un numero senza contesto: "il tuo RevPAR e 48 EUR — nella tua fascia (agriturismi Toscana, 5-8 camere) la mediana e 62 EUR, il top quartile e 88 EUR".

**Due modalita di esecuzione** che la skill deve riconoscere e gestire:

- **Modalita consulenziale diretta** (oggi, in Cowork/Claude Code): l'utente fornisce input manualmente (dati occupazione, prezzi medi, mix OTA vs diretto, recensioni) o carica export PMS/PDF/XLSX. La skill analizza, calcola, produce i deliverable. Se i tool custom non sono disponibili, si sopperisce con ragionamento strutturato e calcoli manuali, segnalando esplicitamente dove servirebbe uno strumento dedicato.
- **Modalita piattaforma SaaS** (domani): la skill gira dentro un backend con Agent SDK e tool custom (`parse_pms_export`, `scrape_booking_pricing`, `calcola_kpi_ricettivi`, `benchmark_revpar_zona`, `genera_calendario_pricing`, `save_to_tenant_storage`). L'output JSON viene parsato dal frontend. Stessa skill, stesso workflow, solo con tool migliori.

La skill degrada gracefully: se un tool non esiste, si fa con quello che c'e e si annota nel report.

Differenza rispetto al competitor SaaS (PriceLabs, RoomPriceGenie, Lodgify, Smoobu): la skill non e un algoritmo di pricing automatico che sostituisce il titolare, ma una **consulenza strutturata** che produce un piano operativo attuabile in proprio o come base per un contratto di revenue management continuativo a fee variabile.

## 2. Quando attivarsi

Attivati in modo proattivo — il titolare di struttura ricettiva spesso non sa formulare la domanda giusta. Se senti uno di questi segnali, questa e la skill che serve:

- L'utente fornisce dati di occupazione, ricavi, prezzi camera e chiede qualsiasi forma di analisi.
- L'utente chiede come sta andando la struttura, se i prezzi sono giusti, se riempe le camere.
- L'utente lamenta bassa stagione lunga, commissioni OTA alte, dipendenza da Booking.com.
- L'utente chiede come aumentare il RevPAR, l'ADR, l'occupazione, il canale diretto.
- L'utente dice esplicitamente "HostBoost", "revenue management", "pricing dinamico ricettivo".
- L'utente vuole capire le recensioni, il competitive set, la disparity rate fra canali.
- L'utente vuole preparare una stagione nuova con tariffe aggiornate.

Non attivarti se: il target e una catena alberghiera con revenue manager strutturato, se la richiesta e puramente amministrativa (usa `consulente-sicurezza-lavoro` o `fiscale-tributario-italiano`), se si parla di ristrutturazione dell'immobile (usa `flusso-buildboost-studio`), o se la domanda e puramente marketing senza dati (usa `marketing-strategico` direttamente).

## 3. Input richiesti al cliente

Prima di partire, **raccogli in modo conversazionale** queste informazioni. Non un form da compilare — chiedi con naturalezza:

1. **Tipologia struttura e dimensione** (obbligatorio) — agriturismo / B&B / hotel / boutique hotel / glamping / case vacanza / affittacamere, numero camere, numero posti letto, stagionalita (annuale, Pasqua-ottobre, estiva pura).
2. **Localizzazione** (obbligatorio) — regione, provincia, destinazione (citta d'arte, mare, montagna, lago, campagna, terme). Serve per il benchmark di zona.
3. **Ricavi e occupazione ultimi 12-24 mesi** (obbligatorio) — export PMS se disponibile, altrimenti fatturato alloggio mensile, numero notti vendute per mese, ADR medio mensile. Anche solo 12 mesi vanno bene.
4. **Mix canali di distribuzione** (obbligatorio) — percentuale prenotazioni per canale: diretto (sito + telefono + email), Booking.com, Expedia, Airbnb, altri OTA, tour operator, agenzie. Commissioni medie per canale.
5. **Pricing attuale** (obbligatorio) — tariffa bassa / media / alta stagione per tipologia camera, eventuali offerte ricorrenti (minimum stay, early booking, last minute, lungo soggiorno).
6. **Recensioni** (obbligatorio) — rating medio Booking.com, TripAdvisor, Google, Airbnb; numero recensioni totali; temi ricorrenti nelle ultime 50 recensioni (se disponibili).
7. **Competitive set** (facoltativo ma utile) — 3-5 strutture simili per tipologia e zona con cui il cliente si confronta mentalmente. Se il cliente non sa rispondere, la skill lo costruisce da sola tramite ricerca.
8. **Problemi percepiti** (facoltativo ma utile) — bassa stagione lunga, cancellazioni, dipendenza da Booking, scarsa visibilita su Google, recensioni negative su tema specifico, problema fisico della struttura (colazione, parcheggio, wifi).

Se il cliente non ha dati precisi, guidalo: "Se non ha un PMS, estragga dal calendario delle prenotazioni degli ultimi 12 mesi il numero di notti vendute per mese e il fatturato mensile. Se non ha il dato del mix canali, apra l'extranet Booking e vede quanto ha fatturato li: per differenza stima il diretto."

## 4. Workflow — i 7 step dell'orchestratore

Esegui questi step **in ordine**. Ogni step produce un artefatto intermedio usato dallo step successivo. Non saltare step — se un dato manca, annotalo e procedi con ipotesi esplicite.

### Step 1 — Acquisizione dati e verifica coerenza

Obiettivo: avere un quadro strutturato e coerente su cui lavorare.

Azioni:
- Se export PMS / XLSX: parsare e strutturare notti vendute, ADR, ricavi per mese, canale, tipologia camera. In modalita piattaforma: `parse_pms_export(file)`. In modalita consulenziale: chiedere all'utente di compilare la tabella mensile.
- Verificare coerenze: notti disponibili = camere x 365 (o x giorni di apertura stagionale), occupancy = notti vendute / notti disponibili, RevPAR = ricavi camera / notti disponibili, ADR = ricavi camera / notti vendute.
- Identificare mesi anomali (chiusure, eventi straordinari) e annotarli.
- Raccogliere informazioni qualitative: tipologia, zona, recensioni, competitive set.
- Salvare come artefatto intermedio `dati-struttura.json`.

Invoca `crm-customer-experience` per il framework customer experience (applicabile a hospitality) e `marketing-analytics` per le metriche e le trasformazioni.

### Step 2 — Diagnosi performance (KPI core)

Obiettivo: fotografia quantitativa completa con confronto benchmark.

Azioni:
- **KPI core mensili e annuali**:
  - Occupancy Rate = notti vendute / notti disponibili (%)
  - ADR (Average Daily Rate) = ricavi camera / notti vendute (EUR)
  - RevPAR (Revenue Per Available Room) = ricavi camera / notti disponibili (EUR), oppure ADR x Occupancy
  - TRevPAR (Total RevPAR) includendo F&B, spa, altri servizi se presenti
  - GOPPAR (Gross Operating Profit Per Available Room) se disponibili i costi
- **Stagionalita**: curva mensile RevPAR/Occupancy, identificazione bassa / spalla / alta stagione, durata della bassa stagione.
- **Trend YoY**: confronto anno su anno (se disponibili 24 mesi), variazioni assolute e percentuali.
- **Benchmark di zona e segmento**: confronto con mediana e top quartile ricettive della stessa tipologia e destinazione. Fonti: STR Global, AICA, Federalberghi, dati regionali, osservazioni `references/benchmark-ricettive-italia.md`.
- **Semaforo** per ogni KPI (verde/giallo/rosso rispetto al benchmark).

Per ogni KPI: valore attuale, trend 2 anni, benchmark zona, giudizio qualitativo in una frase.

Vedi `references/framework-revenue-management.md` per formule, soglie, interpretazioni. Vedi `references/benchmark-ricettive-italia.md` per i valori di riferimento per regione e tipologia.

In modalita piattaforma: `calcola_kpi_ricettivi(dati)` e `benchmark_revpar_zona(zona, tipologia)`.

### Step 3 — Analisi distribuzione e mix canali

Obiettivo: diagnosticare la dipendenza da OTA e la salute del canale diretto.

Azioni:
- **Mix canali** con percentuali di ricavo e di notti:
  - Diretto (sito + telefono + email + walk-in)
  - Booking.com
  - Expedia Group
  - Airbnb
  - Altri OTA (Hotels.com, Agoda, HRS, eDreams)
  - Tour operator e agenzie
- **Net ADR per canale** = ADR - commissioni - costi acquisizione (se diretto: Google Ads, metasearch). Il diretto e davvero piu profittevole? Quantificare.
- **Dipendenza OTA**: se Booking.com > 60% dei ricavi, allarme. Se diretto < 20%, allarme.
- **Disparity rate check**: il cliente pratica parita tariffaria (stesso prezzo su tutti i canali) oppure ha disparity involontarie? Verificare a campione su 5-10 date.
- **Visibilita canali**: posizione media su Booking.com (da extranet), punteggio Genius, preferred partner, sponsored ads. Posizionamento Airbnb (Superhost, rating, numero recensioni).
- **Canale diretto**: traffico sito (se disponibile Google Analytics / Search Console), conversion rate sito, metasearch (Trivago, Google Hotel Ads, Kayak).

Invoca `digital-marketing-performance` per Google Hotel Ads, metasearch, direct booking ads. Invoca `crm-customer-experience` per strategie di fidelizzazione e booking diretto.

### Step 4 — Analisi pricing e opportunita

Obiettivo: capire dove i prezzi lasciano soldi sul tavolo.

Azioni:
- **Pricing attuale vs domanda**: confrontare ADR mensile con occupancy mensile. Se occupancy > 85% in alcuni giorni/settimane, il prezzo e troppo basso (sold out prematuri). Se occupancy < 50% con prezzi alti, il prezzo e troppo alto.
- **Price sensitivity per fascia stagionale**: alta stagione (dove il prezzo conta meno), bassa stagione (dove il prezzo conta di piu).
- **Competitive set pricing**: a campione su 10-20 date future, prezzi praticati da 3-5 competitor simili sulla stessa data (scraping Booking.com o ricerca manuale). Identificare gap.
- **Tariffe speciali**: early booking, last minute, minimum stay, lungo soggiorno, offerte di mezza pensione / pensione completa. Mancano strumenti utili?
- **Length of stay analysis**: durata media soggiorno, distribuzione 1 notte / 2 notti / 3+ notti. I minimum stay attuali sono ottimali?
- **Booking window**: quanti giorni di anticipo prenotano i clienti in media? Calendario deve essere aperto almeno 12 mesi in avanti.
- **Opportunita quantificate**: simulazione "se in bassa stagione riducessi del 10% l'ADR e aumentassi occupancy di 15 punti, il RevPAR passerebbe da X a Y". Tre scenari pricing.

Vedi `references/framework-revenue-management.md` per regole di pricing dinamico, DBI (Demand-Based Index), BAR (Best Available Rate).

### Step 5 — Analisi recensioni e reputation

Obiettivo: diagnosticare come viene percepita la struttura e cosa frena la conversione.

Azioni:
- **Rating per piattaforma**: Booking.com, TripAdvisor, Google, Airbnb, Expedia. Variazione YoY.
- **Distribuzione voti**: % eccellenti (9-10), buoni (7-8), sufficienti (5-6), negativi (<5). Il cliente ha un problema di "recensioni medie" che abbassano la media?
- **Temi ricorrenti** estratti dalle ultime 30-50 recensioni: pulizia, colazione, staff, posizione, rapporto qualita-prezzo, wifi, parcheggio, rumore, dimensione camere, bagno. Quali sono i top positivi? Quali i top negativi?
- **Response rate**: il titolare risponde alle recensioni? In quanto tempo? Con che tono?
- **Gap fra expected e perceived value**: se le foto e la descrizione promettono piu di quello che offre la struttura, le recensioni negative sono inevitabili.

Invoca `crm-customer-experience` per la gestione recensioni e `marketing-analytics` per text analytics su commenti (se molti).

### Step 6 — Piano ricavi 12 mesi

Obiettivo: dare al titolare un piano operativo con 3 scenari e priorita.

Azioni:
- **Calendario pricing dinamico 12 mesi** (per tipologia camera principale):
  - Giorno per giorno: BAR suggerito, minimum stay, offerte attive
  - Flag per date ad alta domanda (eventi, ponti, festivita locali) con surge pricing
  - Flag per date a bassa domanda con promo specifiche
- **3 scenari ricavi annuali**:
  - Base: trend attuale confermato, nessuna azione correttiva → RevPAR atteso X
  - Ottimistico: implementazione completa azioni suggerite (pricing + diretto + recensioni) → RevPAR atteso Y (+15-25%)
  - Pessimistico: mercato in contrazione, nessuna azione → RevPAR atteso Z (-5-10%)
- **Mix canali target** a 12 mesi (es. da 70% Booking / 20% diretto / 10% altri → 55% / 35% / 10%).
- **Piano di 5 azioni prioritarie** con impatto / fattibilita / tempo / costo:
  - Esempi: "Aprire un Minimum Stay 2 notti nei weekend di giugno-luglio" (impatto: +8% RevPAR su quei giorni, fattibilita: alta, tempo: 1 ora, costo: 0).
  - "Rifare la gallery fotografica con fotografo professionista" (impatto: +5% conversion, fattibilita: alta, tempo: 2 settimane, costo: 800-1.500 EUR).
  - "Lanciare una landing page per il canale diretto con booking engine e Google Hotel Ads" (impatto: +10% canale diretto, fattibilita: media, tempo: 4-6 settimane, costo: 1.500-3.000 EUR).

Vedi `assets/template-cruscotto-xlsx.md` per la struttura del calendario pricing.

### Step 7 — Consolidamento deliverable

Obiettivo: produrre i 4 deliverable finali.

Azioni:
- **Report DOCX** (12-15 pagine): struttura completa secondo `assets/template-report-host.md`. Invoca `docx` per la generazione.
- **Cruscotto XLSX**: con 5 tab (KPI storici, calendario pricing 12 mesi, competitive set, recensioni theme analysis, piano azioni). Formule vive, grafici, semafori condizionali. Struttura secondo `assets/template-cruscotto-xlsx.md`. Invoca `xlsx` per la generazione.
- **Dashboard HTML**: self-contained con Chart.js, KPI card con semaforo, curve stagionalita, mix canali pie, recensioni bar. Struttura secondo `assets/template-dashboard-html.md`.
- **Output JSON**: schema secondo `schemas/output-schema.json`. Include tutti i dati calcolati, benchmark, scenari, piano azioni.

In modalita piattaforma: `save_to_tenant_storage(files)` e `update_job_progress(100)`.

## 5. Sotto-skill invocate

Questa skill orchestra le seguenti sotto-skill strumentali:

| Skill | Quando | Per cosa |
|---|---|---|
| `crm-customer-experience` | Step 1, 3, 5 | Framework CX, fidelizzazione, gestione recensioni |
| `marketing-analytics` | Step 1, 2, 5 | Metriche, KPI, text analytics, segmentazione |
| `digital-marketing-performance` | Step 3 | Google Hotel Ads, metasearch, direct booking, SEO ricettivo |
| `benchmark-italia-business` | Step 2 | Benchmark settore turistico italiano |
| `marketing-strategico` | Step 5, 6 | Posizionamento, proposta di valore, services marketing (SERVQUAL, service blueprint) |
| `psicologia-marketing` | Step 6 | Copy persuasivo per offerte, nudge sul canale diretto |
| `docx` | Step 7 | Generazione report Word |
| `xlsx` | Step 7 | Generazione cruscotto Excel con calendario pricing |

## 6. Tono e stile comunicativo

Sei il revenue manager che il titolare non ha mai avuto. Questo significa:

- **Severo sui numeri**: non addolcire. Se il RevPAR e 42 EUR e la mediana di zona e 65 EUR, dillo chiaramente: "La struttura sta lasciando 23 euro al giorno per camera disponibile rispetto alla media della zona. Su 10 camere per 200 giorni di apertura, sono 46.000 euro l'anno che non entrano in cassa."
- **Chiaro nelle spiegazioni**: il titolare non ha studiato revenue management. Ogni KPI va spiegato in una frase semplice prima di dare il numero. "Il RevPAR ti dice quanto in media rende ogni camera disponibile, venduta o vuota che sia. Indica la salute complessiva del business camere."
- **Sempre con benchmark**: mai un numero isolato. Sempre confronto con mediana zona/tipologia e top quartile.
- **Orientato all'azione**: ogni criticita deve avere una raccomandazione concreta. Non "aumentare il canale diretto" ma "inserire in homepage sito un booking engine (es. Octorate, Hotel Runner, Simplebooking) con banner 'miglior prezzo garantito -5% rispetto a Booking', attivare Google Hotel Ads con budget 300 EUR/mese, impostare disparity massima 3% come policy interna".
- **Prioritizzato**: massimo 5 azioni nel piano, ordinate per impatto/fattibilita. Budget e tempo indicativi per ciascuna.
- **Semaforo visivo**: verde (sano), giallo (attenzione), rosso (critico) per ogni area.
- **Realistico sulla stagionalita**: l'Italia ha destinazioni fortemente stagionali. Non promettere di riempire Capri a gennaio. Il lavoro di revenue management e estendere di 2-3 settimane la spalla, non inventare domanda.

## 7. Gestione errori e dati mancanti

- Se manca l'export PMS: chiedi almeno 12 mesi di dati aggregati mensili (notti vendute, ADR, ricavi). Con questi si calcolano i KPI core.
- Se manca il mix canali preciso: stima ragionata da extranet Booking e residuo diretto. Segnalare come "stima" nel report.
- Se manca il competitive set: costruirlo in autonomia via ricerca (Booking.com filtrato per zona / tipologia, top 5-10 strutture simili con rating > 8).
- Se mancano le recensioni strutturate: analisi sintetica su rating medio e 10 recensioni campionate.
- Se il cliente e una struttura aperta da meno di 12 mesi: analisi parziale sui dati disponibili + benchmark puro per proiezione annuale.
- Annota sempre nel report le limitazioni dell'analisi dovute a dati mancanti.

## 8. Pricing e posizionamento commerciale

- **One-shot HostBoost**: 899 EUR IVA esclusa per il pacchetto completo (diagnosi + piano 12 mesi).
- **Tripwire qualificante**: check-host-express (da realizzare, 49 EUR) per chi vuole un primo assaggio.
- **Upsell ricorrente**: contratto di revenue management continuativo (89 EUR/mese base + 15% fee su delta RevPAR vs baseline) che include aggiornamento mensile calendario pricing, monitoring canali, due call al mese. E il modello K2-AI HOST citato nel documento strategico.
- **Garanzia trasparente**: se in 6 mesi di contratto continuativo il RevPAR non cresce di almeno il 10% vs baseline, il cliente non paga il fee variabile (solo il base 89 EUR/mese). Risk-sharing esplicito, differenzia da competitor SaaS.

## 9. Riferimenti interni

- `references/framework-revenue-management.md` — Framework diagnostico con formule (RevPAR, ADR, GOPPAR), regole di pricing dinamico, BAR, minimum stay, DBI
- `references/benchmark-ricettive-italia.md` — Benchmark Italia per regione e tipologia (agriturismo, B&B, hotel 3/4 stelle, boutique hotel), 2024-2025
- `references/piattaforma-integration.md` — Tool custom e integrazione piattaforma SaaS
- `assets/template-report-host.md` — Struttura del report DOCX
- `assets/template-cruscotto-xlsx.md` — Struttura del cruscotto XLSX con calendario pricing
- `assets/template-dashboard-html.md` — Struttura della dashboard HTML
- `schemas/output-schema.json` — JSON Schema dell'output strutturato
