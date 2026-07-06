---
name: verifica-requisiti-simest
description: >-
  Skill foglia AgevolazioniBoost K2-AI per la verifica dei requisiti e l'analisi
  delle opportunità di finanziamento SIMEST Fondo 394 (D.Lgs. 143/1998).
  Supporta PMI italiane nell'accesso ai finanziamenti agevolati per
  l'internazionalizzazione — fiere estere, e-commerce internazionale, apertura
  mercati esteri, certificazioni, transizione digitale e verde, studi di
  fattibilità. Verifica la sussistenza dei requisiti soggettivi (PMI, bilanci,
  sede, assenza procedure concorsuali), identifica la linea di finanziamento
  più adatta, calcola la quota a fondo perduto applicabile (incluse maggiorazioni
  Mezzogiorno, startup innovative, PMI innovative), guida nella preparazione
  della documentazione pre-domanda e segnala lo stato di apertura dello sportello.
  Usata dall'orchestratore AgevolazioniBoost come step 3/4 oppure in modalità
  standalone. Restituisce JSON strutturato per il flusso orchestrato.
---








<!-- LEGAL-EVIDENCE-BLOCK-V7 -->
## Tools Normattiva + Giurisprudenza (CCost + CGUE + CEDU + CdS/TAR + Cassazione) — verifica obbligatoria

Hai 5 toolkit locali + 1 lookup live per consulenza legale evidence-based:
- **Normattiva** — ~42.000 norme italiane (DB FTS5)
- **Corte Costituzionale** — 22.258 pronunce + 46.154 massime (1956→2026)
- **Corte di Giustizia UE + Tribunale UE** — ~38.000 cause (2005→2026)
- **Corte EDU (Strasburgo)** — 10.000 casi contro l'Italia (2001→2026), con traduzioni ufficiali Min. Giustizia
- **Giustizia Amministrativa** — Consiglio di Stato + TAR + CGARS (2024→2025, in espansione)
- **Cassazione (LIVE pubblica)** — SentenzeWeb italgiure, accesso pubblico zero-setup (~188k civ + ~236k pen, testo integrale)

### Workflow obbligatorio

**A. Norme italiane**
```bash
python3 ~/normattiva_ai/tools/cita.py "<es. D.Lgs 81/2008>"
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --materia bilancio_finanza_pubblica --limit 5
```

**B. Corte Costituzionale**
```bash
python3 ~/giurisprudenza_ai/tools/cross_norma_sentenza.py "art. 32 Cost." --limit 10
python3 ~/giurisprudenza_ai/tools/rag_giurisprudenza.py "<query>" --anno-da 2018
python3 ~/giurisprudenza_ai/tools/cita_sentenza.py "Corte cost. N/AAAA"
```

**C. CGUE (diritto UE / GDPR / appalti / antitrust / privacy / dogana)**
```bash
python3 ~/cgue_ai/tools/cross_norma_cgue.py "art. 101 TFUE" --limit 10
python3 ~/cgue_ai/tools/cross_norma_cgue.py "Reg. UE 679/2016"        # GDPR
python3 ~/cgue_ai/tools/rag_cgue.py "<query>" --anno-da 2018
python3 ~/cgue_ai/tools/cita_cgue.py "C-16/05"
```

**D. CEDU (diritti fondamentali / equo processo art. 6 / detenzione art. 3 / proprietà P1-1 / vita privata art. 8)**
```bash
python3 ~/cedu_ai/tools/cross_articolo_cedu.py "art. 6" --solo-importanti --limit 10
python3 ~/cedu_ai/tools/rag_cedu.py "<query>" --anno-da 2015
python3 ~/cedu_ai/tools/cita_cedu.py "63386/16"      # numero di ricorso
```

**E. Giustizia Amministrativa — CdS/TAR (appalti, edilizia, accesso atti, SCIA, silenzio, espropri, PA)**
```bash
python3 ~/gad_ai/tools/cross_norma_gad.py "D.Lgs 36/2023" --limit 10   # appalti
python3 ~/gad_ai/tools/cross_norma_gad.py "Legge 241/1990"             # procedimento
python3 ~/gad_ai/tools/rag_gad.py "<query>" --sede cds --anno-da 2024
```

**F. Cassazione (LIVE pubblica — civile/penale, legittimità) — zero setup**
```bash
# Verifica/recupera un precedente di Cassazione (SentenzeWeb pubblico, nessun login)
python3 ~/cassazione_ai/tools/cassazione_lookup.py --cit "Cass. civ. 12345/2023"
python3 ~/cassazione_ai/tools/cassazione_lookup.py --q "licenziamento giusta causa" --sezione civ --rows 5
python3 ~/cassazione_ai/tools/cassazione_lookup.py --cit "Cass. civ. 12345/2023" --full   # testo integrale
python3 ~/cassazione_ai/tools/check_cassazione.py --file <output.md>                        # verifica citazioni
```
Copre la finestra pubblica (~ultimi 5 anni + storico parziale). Se una citazione MANCA può essere fuori finestra; dillo, non inventare la massima.

**G. Verifica finale (prima del deliverable, su ogni file MD prodotto)**
```bash
python3 ~/normattiva_ai/tools/check_citazioni.py --file <output.md> --strict
python3 ~/giurisprudenza_ai/tools/check_sentenze.py --file <output.md> --strict
python3 ~/cgue_ai/tools/check_cgue.py --file <output.md> --strict
python3 ~/cedu_ai/tools/check_cedu.py --file <output.md> --strict
python3 ~/gad_ai/tools/check_gad.py --file <output.md> --strict
```

Knowledge pack norme: `~/normattiva_ai/knowledge_packs/bilancio_finanza_pubblica/`

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# Skill — verifica-requisiti-simest
## AgevolazioniBoost K2-AI | Skill Foglia

---

## Identità e scopo

Questa skill foglia fa parte del sistema **AgevolazioniBoost K2-AI** ed è dedicata
all'analisi e alla verifica dei requisiti per i finanziamenti **SIMEST Fondo 394**.

Viene attivata dall'orchestratore AgevolazioniBoost come **Step 3/4** (dopo la
profilazione aziendale e l'identificazione degli strumenti agevolativi) oppure
direttamente in modalità **standalone** quando l'utente menziona esplicitamente
SIMEST, Fondo 394, internazionalizzazione PMI o strumenti correlati.

**SIMEST** è la società del Gruppo CDP/SACE dedicata al sostegno finanziario
dell'internazionalizzazione delle PMI italiane. Eroga finanziamenti agevolati
a tasso zero o ridotto, spesso abbinati a una quota a fondo perduto non
rimborsabile, tramite un portale online a sportello periodicamente aperto.

---

## SEZIONE 1 — Panoramica SIMEST Fondo 394

### Riferimento normativo e struttura

| Voce | Dettaglio |
|---|---|
| Base normativa | D.Lgs. 143/1998, art. 6 e seguenti |
| Gestore | SIMEST S.p.A. (controllata SACE, Gruppo CDP) |
| Tipo strumento | Finanziamento agevolato + quota a fondo perduto (stessa domanda) |
| Tasso finanziamento | Zero o ridotto (tasso di riferimento UE ridotto) |
| Accesso | Portale online simest.it — modalità a sportello |
| Target | PMI italiane con proiezione internazionale |

### Requisiti soggettivi base

Per accedere al Fondo 394, l'azienda richiedente deve soddisfare **tutti** i
seguenti requisiti:

- [ ] **Dimensione PMI**: non più di 250 dipendenti E fatturato annuo non
  superiore a 50 milioni di EUR (oppure totale di bilancio non superiore a
  43 milioni di EUR)
- [ ] **Bilanci depositati**: almeno 2 bilanci approvati e depositati presso il
  Registro Imprese
- [ ] **Sede legale e operativa in Italia**
- [ ] **Assenza procedure concorsuali**: nessuna procedura di fallimento,
  liquidazione, concordato preventivo, amministrazione straordinaria in corso
- [ ] **Regolarità fiscale e contributiva**: DURC regolare, nessun debito
  tributario iscritto a ruolo non rateizzato
- [ ] **Partecipazione societaria**: SIMEST può acquisire una quota temporanea
  di minoranza (opzionale, non obbligatoria per tutte le linee)

### Avvertenza critica — sportello a esaurimento plafond

> **ATTENZIONE**: Le finestre di apertura del Fondo 394 sono imprevedibili e
> i plafond si chiudono in tempi molto rapidi — a volte in pochi giorni o
> poche ore dall'apertura. E' indispensabile prepararsi prima e presentare
> la domanda il primo giorno utile.

---

## SEZIONE 2 — Le 6 linee di finanziamento principali

### Linea 1 — Fiere e mostre internazionali

| Parametro | Valore |
|---|---|
| Spese ammissibili | Quota di partecipazione, allestimento stand, trasporto merci e materiali, personale dedicato, comunicazione e promozione in loco |
| Importo massimo | 300.000 EUR per domanda |
| Tasso finanziamento | 0% (tasso zero) |
| Quota fondo perduto standard | 25% dell'importo finanziato |
| Quota FP Mezzogiorno | 40% dell'importo finanziato |
| Durata | 4 anni (di cui 1 preammortamento) |
| Note | Ammesse fiere fisiche e virtuali; spese retroattive fino a 6 mesi prima della domanda in alcuni casi |

### Linea 2 — E-commerce internazionale

| Parametro | Valore |
|---|---|
| Spese ammissibili | Sviluppo/adattamento piattaforma e-commerce, integrazione marketplace internazionali (Amazon, Alibaba, ecc.), localizzazione (traduzione, adattamento UX), digital marketing per mercati esteri, consulenze specialistiche |
| Importo massimo | 500.000 EUR per domanda |
| Tasso finanziamento | 0% (tasso zero) |
| Quota fondo perduto standard | 25% dell'importo finanziato |
| Quota FP Mezzogiorno | 40% dell'importo finanziato |
| Durata | 6 anni (di cui 2 preammortamento) |
| Note | Richiede piano export digitale dettagliato; target minimo di fatturato estero da piano |

### Linea 3 — Transizione digitale e verde

| Parametro | Valore |
|---|---|
| Spese ammissibili | Investimenti tecnologici per migliorare la competitivita' internazionale (ERP, automazione, Industry 4.0), certificazioni ambientali, efficienza energetica, riduzione emissioni per accesso a mercati ESG-oriented |
| Importo massimo | 300.000 EUR per domanda |
| Tasso finanziamento | 0% (tasso zero) |
| Quota fondo perduto standard | 25% dell'importo finanziato |
| Quota FP Mezzogiorno | 40% dell'importo finanziato |
| Durata | 6 anni (di cui 2 preammortamento) |
| Note | Investimento deve avere nesso causale dimostrabile con l'internazionalizzazione |

### Linea 4 — Inserimento in mercati esteri

| Parametro | Valore |
|---|---|
| Spese ammissibili | Apertura uffici di rappresentanza, showroom, magazzini o punti vendita all'estero; affitti, allestimenti, personale locale, consulenze legali e fiscali estero |
| Importo massimo | 1.500.000 EUR per domanda |
| Tasso finanziamento | Tasso agevolato (riferimento UE ridotto) |
| Quota fondo perduto standard | 25% dell'importo finanziato |
| Quota FP Mezzogiorno | 40% dell'importo finanziato |
| Durata | 8 anni (di cui 2 preammortamento) |
| Note | Linea con importi piu' elevati; richiede business plan internazionalizzazione solido e proiezioni finanziarie estero |

### Linea 5 — Certificazioni e consulenze

| Parametro | Valore |
|---|---|
| Spese ammissibili | Certificazioni di prodotto per mercati esteri (CE, FDA, ISO per export, ecc.), consulenze legali e fiscali per operativita' in mercati stranieri, consulenze contrattualistiche internazionali |
| Importo massimo | 200.000 EUR per domanda |
| Tasso finanziamento | 0% (tasso zero) |
| Quota fondo perduto standard | 25% dell'importo finanziato |
| Quota FP Mezzogiorno | 40% dell'importo finanziato |
| Durata | 4 anni (di cui 1 preammortamento) |
| Note | Spese retroattive ammesse; certificazione deve essere funzionale all'export verso mercati specifici |

### Linea 6 — Studi di fattibilita'

| Parametro | Valore |
|---|---|
| Spese ammissibili | Analisi per nuovi mercati esteri, ricerche di mercato internazionali, due diligence su partner esteri, studi legali/normativi su paesi target |
| Importo massimo | 100.000 EUR per domanda |
| Tasso finanziamento | 0% (tasso zero) |
| Quota fondo perduto standard | 25% dell'importo finanziato |
| Quota FP Mezzogiorno | 40% dell'importo finanziato |
| Durata | 4 anni (di cui 1 preammortamento) |
| Note | Linea con iter istruttorio piu' snello; utile come primo accesso al Fondo 394 |

---

## SEZIONE 3 — La quota a fondo perduto

### Meccanismo base

La quota a **fondo perduto (FP)** e' una percentuale del finanziamento concesso
che **non deve essere restituita**. Non si tratta di un contributo separato ma
di una componente integrata nella stessa delibera di finanziamento:

1. SIMEST delibera il finanziamento totale (es. 200.000 EUR)
2. Una quota (es. 25% = 50.000 EUR) viene erogata a fondo perduto
3. La quota residua (es. 75% = 150.000 EUR) e' finanziamento agevolato da rimborsare
4. L'erogazione avviene in un'unica soluzione o per stati avanzamento lavori

### Maggiorazioni disponibili

| Categoria | Maggiorazione FP | Note |
|---|---|---|
| PMI standard | Standard (25%) | Requisito base |
| PMI localizzate nel Mezzogiorno | +15% (fino a 40%) | Calabria, Campania, Basilicata, Puglia, Sicilia, Sardegna, Molise, Abruzzo |
| Startup innovative (ex art. 25 D.L. 179/2012) | Ulteriore maggiorazione | Cumulabile con Mezzogiorno fino a soglia massima |
| PMI innovative (ex art. 4 D.L. 3/2015) | Ulteriore maggiorazione | Cumulabile con Mezzogiorno fino a soglia massima |

### Tabella riepilogativa quota FP per linea

| Linea | Quota FP Standard | Quota FP Mezzogiorno | Importo max FP (standard, max domanda) |
|---|---|---|---|
| Fiere internazionali | 25% | 40% | 75.000 EUR |
| E-commerce internazionale | 25% | 40% | 125.000 EUR |
| Transizione digitale e verde | 25% | 40% | 75.000 EUR |
| Inserimento mercati esteri | 25% | 40% | 375.000 EUR |
| Certificazioni e consulenze | 25% | 40% | 50.000 EUR |
| Studi di fattibilita' | 25% | 40% | 25.000 EUR |

> I valori sopra riportati si basano sull'applicazione della percentuale
> all'importo massimo della linea. L'importo effettivo dipende dal progetto
> presentato. Verificare sempre le condizioni aggiornate su simest.it.

---

## SEZIONE 4 — Procedura online step by step

### Step 1 — Verifica apertura sportello
**Timing stimato**: attivita' continuativa (pre-apertura)

- Monitorare quotidianamente la sezione "Sportello" su **simest.it**
- Iscriversi alla **newsletter SIMEST** e alla newsletter **SACE**
- Seguire i canali Unioncamere, CNA, Confindustria, associazioni di categoria
- Configurare Google Alert per "SIMEST sportello aperto Fondo 394"
- Verificare con il proprio consulente/intermediario finanziario eventuali
  preavvisi non ufficiali

### Step 2 — Preparazione documentazione pre-domanda
**Timing stimato**: 2-4 settimane prima dell'apertura attesa

- Raccogliere e aggiornare tutti i documenti (vedi Sezione 5)
- Redigere o aggiornare il business plan internazionalizzazione
- Preparare il piano export con proiezioni fatturato estero
- Raccogliere preventivi per le spese previste (almeno 2 per voce significativa)
- Verificare visura camerale aggiornata e DURC
- Registrarsi/verificare accesso al portale SIMEST con credenziali aggiornate

### Step 3 — Compilazione domanda su portale SIMEST
**Timing stimato**: 1-3 giorni lavorativi (da fare il primo giorno di apertura)

- Accedere al portale **simest.it** con credenziali aziendali
- Selezionare la linea di finanziamento appropriata
- Caricare tutti i documenti obbligatori nella sezione dedicata
- Compilare i moduli di autocertificazione richiesti
- Indicare importo richiesto e piano di utilizzo fondi
- Inviare la domanda e salvare il numero di protocollo

> **CRITICO**: La domanda va inviata il primo giorno di apertura dello
> sportello, preferibilmente nelle prime ore. I plafond si esauriscono
> rapidamente.

### Step 4 — Istruttoria SIMEST
**Timing stimato**: 30-90 giorni lavorativi dalla ricezione domanda completa

- SIMEST verifica la completezza documentale (richiesta integrazioni se necessario)
- Analisi del merito creditizio e della solidita' del progetto
- Eventuale richiesta di chiarimenti o documentazione aggiuntiva
- Valutazione del piano export e delle proiezioni

### Step 5 — Delibera e firma contratto
**Timing stimato**: 15-30 giorni dalla conclusione istruttoria

- Notifica della delibera positiva (o diniego motivato)
- Invio contratto di finanziamento in formato digitale
- Firma digitale del contratto da parte del legale rappresentante
- Eventuale costituzione garanzie (se richieste per importi elevati)

### Step 6 — Erogazione e rendicontazione
**Timing stimato**: erogazione entro 30 giorni dalla firma; rendicontazione
entro scadenza contrattuale

- Erogazione dell'importo deliberato (unica soluzione o SAL)
- Avvio del progetto e sostenimento delle spese ammissibili
- Raccolta documentazione di spesa (fatture, bonifici, contratti)
- Rendicontazione finale entro i termini contrattuali
- Eventuale visita ispettiva SIMEST (per importi rilevanti)
- Avvio rimborso rate secondo piano di ammortamento

---

## SEZIONE 5 — Documenti necessari

### Documenti aziendali (sempre obbligatori)

- [ ] Visura camerale aggiornata (non oltre 3 mesi)
- [ ] Ultimi 2 bilanci approvati e depositati (Stato patrimoniale, Conto
  economico, Nota integrativa)
- [ ] Statuto aggiornato e atto costitutivo
- [ ] Documento d'identita' in corso di validita' del legale rappresentante
- [ ] DURC in corso di validita'
- [ ] Autocertificazione antimafia (per importi sopra soglia)
- [ ] Dichiarazione de minimis (se applicabile)
- [ ] Eventuale certificazione PMI innovativa o startup innovativa (se si
  richiede maggiorazione FP)

### Documenti tecnici di progetto

- [ ] **Business plan internazionalizzazione** (struttura: analisi mercati
  target, strategia export, piano operativo, proiezioni finanziarie 3-5 anni)
- [ ] **Piano export dettagliato** con obiettivi di fatturato estero,
  mercati target, canali distributivi
- [ ] Descrizione dettagliata del progetto per cui si richiede il finanziamento
- [ ] Cronoprogramma delle attivita' e delle spese

### Documenti specifici per linea

**Fiere internazionali**
- [ ] Conferma iscrizione/invito alla fiera con indicazione date e location
- [ ] Preventivi per stand, trasporto, comunicazione

**E-commerce internazionale**
- [ ] Preventivi sviluppo piattaforma o integrazione marketplace
- [ ] Piano di digital marketing internazionale con KPI
- [ ] Eventuale contratto con agenzia specializzata

**Transizione digitale e verde**
- [ ] Analisi del gap tecnologico attuale vs. obiettivo
- [ ] Preventivi forniture hardware/software
- [ ] Collegamento esplicito tra investimento e obiettivo export

**Inserimento mercati esteri**
- [ ] Contratto di locazione o lettera di intenti per sede estera
- [ ] Preventivi allestimento
- [ ] Documentazione su normativa locale (visto, permessi)

**Certificazioni e consulenze**
- [ ] Preventivo ente certificatore o consulente
- [ ] Specifiche del mercato estero target e requisiti di certificazione

**Studi di fattibilita'**
- [ ] Offerta della societa' di ricerche/consulenza
- [ ] Descrizione del mercato/paese da analizzare

---

## SEZIONE 6 — Cumulabilita'

### Con altre linee SIMEST

Non e' generalmente ammessa la cumulabilita' di piu' linee Fondo 394 per le
**stesse spese**. E' pero' possibile:

- Presentare domande su linee diverse per **spese diverse** (es. Fiera + E-commerce
  per spese distinte)
- Presentare domande in **annualita' diverse** per attivita' distinte
- Verificare sempre le condizioni aggiornate nel bando vigente al momento
  della domanda

### Con agevolazioni nazionali

| Strumento | Cumulabilita' | Note |
|---|---|---|
| Credito d'imposta R&S/Innovazione | Da verificare | Dipende dalla natura delle spese |
| Nuova Sabatini | Da verificare | Se spese distinte, possibile |
| Contratti di sviluppo | Da verificare caso per caso | Notificare entrambi i gestori |
| PNRR — bandi specifici | Da verificare | Regole de minimis e aiuti di stato |

### Con bandi regionali export

I bandi regionali per l'internazionalizzazione (es. voucher export, contributi
fiera, fondi FESR per internazionalizzazione) sono **spesso cumulabili** con
il Fondo 394, a condizione che:

- Le spese non siano le stesse oggetto di doppio finanziamento pubblico al 100%
- Si rispettino i massimali de minimis (200.000 EUR su 3 esercizi fiscali)
- Si dichiarino correttamente tutti gli aiuti ricevuti

**Opportunita' da segnalare**: molte Regioni hanno fondi dedicati all'export
attivabili in parallelo (es. Fondo export Lombardia, voucher internazionalizzazione
Veneto, bandi FESR Campania per export). Verificare il catalogo regionale
specifico.

---

## SEZIONE 7 — Strategia per le finestre a sportello

### Preparazione pre-apertura (checklist operativa)

La preparazione va completata **prima** che lo sportello apra. Lista documenti
da tenere pronti:

- [ ] Visura camerale aggiornata (aggiornare ogni 3 mesi)
- [ ] Bilanci depositati (verificare che l'ultimo sia disponibile)
- [ ] DURC valido (rinnovare se in scadenza entro 30 giorni)
- [ ] Credenziali portale SIMEST attive e testate
- [ ] Business plan internazionalizzazione completato e revisionato
- [ ] Piano export con proiezioni aggiornate
- [ ] Preventivi raccolti per tutte le voci di spesa previste
- [ ] Moduli di autocertificazione compilati (anche se da aggiornare alla data)
- [ ] Delibera del CdA o del titolare per la richiesta di finanziamento
- [ ] Firma digitale del legale rappresentante funzionante

### Fonti di alert per l'apertura dello sportello

| Fonte | Tipo alert | Affidabilita' |
|---|---|---|
| Newsletter SIMEST (simest.it/newsletter) | Email ufficiale | Alta — fonte primaria |
| Newsletter SACE (sace.it) | Email ufficiale | Alta |
| Unioncamere e Camere di Commercio locali | Comunicati, email | Media-Alta |
| CNA / Confindustria / Confcommercio | Newsletter associative | Media |
| Google Alert "SIMEST sportello" | Automatico | Media |
| Consulente/intermediario finanziario | Preavviso informale | Variabile |
| LinkedIn (profilo ufficiale SIMEST) | Post social | Media — utile per conferma |

### Timing operativo il giorno dell'apertura

1. **Ore 8:00-9:00**: verificare apertura su simest.it e newsletter
2. **Ore 9:00-10:00**: accesso al portale e avvio compilazione domanda
3. **Ore 10:00-12:00**: caricamento documenti e completamento form
4. **Entro le 13:00**: invio domanda e salvataggio protocollo
5. **Entro le 24 ore**: conferma ricezione e verifica completezza

### Piano B — se lo sportello e' chiuso o il plafond e' esaurito

| Scenario | Azione alternativa |
|---|---|
| Sportello SIMEST chiuso | Monitorare apertura successiva; nel frattempo attivare linee regionali export |
| Plafond esaurito prima dell'invio | Verificare riapertura straordinaria; attivare bandi regionali cumulabili |
| Domanda non ammissibile per requisiti | Lavorare sui requisiti mancanti (es. depositare bilanci, regolarizzare DURC) |
| PMI non in target (dimensioni) | Valutare strumenti alternativi (ICE, SIMEST partecipazioni, bandi MISE) |

**Strumenti alternativi da considerare**:
- Bandi ICE per fiere e promozione estero
- Voucher internazionalizzazione regionali (FESR)
- SIMEST — partecipazione al capitale (linea distinta dal Fondo 394)
- Garanzie SACE per export
- Bandi MISE/MIMIT per internazionalizzazione PMI

---

## SEZIONE 8 — 5 errori da evitare

### Errore 1 — Presentare domanda senza documentazione completa

**Conseguenza**: la domanda viene sospesa per richiesta integrazioni, perdendo
priorita' nella coda; in alcuni casi puo' essere rigettata d'ufficio se le
integrazioni non arrivano nei termini.

**Azione correttiva**: usare la checklist della Sezione 5 come lista di
controllo pre-invio; simulare la compilazione sul portale SIMEST prima
dell'apertura dello sportello (senza inviare).

---

### Errore 2 — Inviare la domanda dopo i primi giorni dall'apertura

**Conseguenza**: il plafond si esaurisce rapidamente; chi invia tardi trova lo
sportello gia' chiuso oppure ottiene una posizione in graduatoria sfavorevole.

**Azione correttiva**: configurare tutti gli alert (Sezione 7) e bloccare
in agenda le prime 4 ore del giorno di apertura per dedicarle esclusivamente
alla compilazione e invio della domanda.

---

### Errore 3 — Sottostimare le spese o presentare preventivi non congrui

**Conseguenza**: SIMEST puo' ridurre l'importo finanziabile o rigettare la
domanda per incoerenza tra progetto e costi indicati; in rendicontazione si
rischia di non poter dimostrare la spesa effettiva.

**Azione correttiva**: raccogliere almeno 2 preventivi per ogni voce di spesa
significativa; verificare che i preventivi siano intestati all'azienda
richiedente e datati; fare riferimento a listini ufficiali per fiere e
marketplace.

---

### Errore 4 — Non dichiarare altri aiuti di stato ricevuti

**Conseguenza**: violazione della normativa de minimis con obbligo di
restituzione di tutti gli aiuti ricevuti, potenziali sanzioni e iscrizione
nel Registro Nazionale Aiuti di Stato come soggetto inadempiente.

**Azione correttiva**: verificare il registro RNA (Registro Nazionale Aiuti —
rna.gov.it) prima di presentare domanda; dichiarare tutti gli aiuti ricevuti
negli ultimi 3 esercizi fiscali; consultare il commercialista per il calcolo
del massimale residuo disponibile.

---

### Errore 5 — Rendicontare spese non ammissibili o fuori periodo

**Conseguenza**: decadenza parziale o totale del beneficio con obbligo di
restituzione del fondo perduto e possibile risoluzione del contratto di
finanziamento.

**Azione correttiva**: conservare tutta la documentazione di spesa (fatture,
bonifici, estratti conto) dal primo giorno; verificare la data di avvio
progetto contrattualmente prevista; non anticipare spese prima della delibera
salvo specifiche deroghe contrattuali; far eseguire la rendicontazione da
un professionista esperto di agevolazioni.

---

## Output per orchestratore

Al termine dell'analisi, la skill restituisce il seguente JSON strutturato
per l'orchestratore AgevolazioniBoost:

```json
{
  "skill": "verifica-requisiti-simest",
  "timestamp": "<ISO8601>",
  "azienda": {
    "ragione_sociale": "<string>",
    "settore": "<string>",
    "regione": "<string>",
    "fatturato_eur": "<number>",
    "dipendenti": "<number>"
  },
  "esito_verifica": {
    "requisiti_soddisfatti": true,
    "requisiti_mancanti": [],
    "note_requisiti": "<string>"
  },
  "raccomandazione": {
    "linea_consigliata": "<Fiere|E-commerce|Digitale-Verde|Mercati-Esteri|Certificazioni|Studi-Fattibilita>",
    "motivazione": "<string>",
    "importo_richiedibile_eur": "<number>",
    "quota_fp_pct": "<number>",
    "beneficio_stimato_eur": "<number>",
    "maggiorazione_mezzogiorno": false,
    "maggiorazione_startup_innovativa": false,
    "maggiorazione_pmi_innovativa": false
  },
  "stato_sportello": {
    "sportello_aperto": false,
    "fonte_verifica": "WebSearch — verificare su simest.it",
    "data_verifica": "<ISO8601>",
    "prossima_apertura_attesa": "da monitorare"
  },
  "azione_immediata": "<string descrittiva dell'azione prioritaria consigliata>",
  "piano_b": "<string — azione alternativa se sportello chiuso>",
  "cumulabilita": {
    "bandi_regionali_export": true,
    "altri_strumenti_simest": false,
    "note": "<string>"
  }
}
```

### Note per l'orchestratore

- Il campo `sportello_aperto` richiede sempre una verifica live tramite
  **WebSearch** su simest.it — non puo' essere compilato in modo statico
- Il campo `beneficio_stimato_eur` corrisponde alla quota a fondo perduto
  applicabile (quota_fp_pct x importo_richiedibile_eur)
- Se `requisiti_soddisfatti` e' `false`, il campo `azione_immediata` deve
  descrivere come colmare il requisito mancante prima di riaprire il flusso
- In caso di PMI del Mezzogiorno, aggiornare `quota_fp_pct` al 40% e
  impostare `maggiorazione_mezzogiorno: true`

---

*Skill foglia AgevolazioniBoost K2-AI — verifica-requisiti-simest*
*Riferimento normativo: D.Lgs. 143/1998 | Gestito da SIMEST S.p.A. (Gruppo CDP/SACE)*
*Verificare sempre le condizioni aggiornate su simest.it prima di presentare domanda*
