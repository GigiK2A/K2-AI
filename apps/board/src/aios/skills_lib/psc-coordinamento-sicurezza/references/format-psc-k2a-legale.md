# FORMAT PSC K2A TLC — Template Completo con Integrazione Legale

> **ISTRUZIONI PER L'USO**: Questo file contiene la struttura esatta e il testo standard di ogni sezione del PSC K2A TLC. Per ogni nuovo PSC:
> 1. Copia l'intera struttura
> 2. Sostituisci tutti i placeholder `[PLACEHOLDER]` con i dati del sito specifico
> 3. Adatta i rischi e le schede fase lavorativa al tipo di intervento (New Site / UP5G / Adeguamento / Dismissione)
> 4. Le sezioni marcate con 🔒 LEGALE contengono clausole difensive obbligatorie — NON rimuoverle mai
> 5. Esegui le checklist F.1 e F.3 (in fondo al documento) prima della consegna

> 6. **FORMATO DOCX**: Nella generazione del .docx, rispettare obbligatoriamente le regole di formattazione descritte nella sezione "REGOLE DI FORMATTAZIONE DOCX" in fondo a queste istruzioni

---
> ### REGOLE DI FORMATTAZIONE DOCX (OBBLIGATORIE)
>
> **A. TABELLE RISCHI (Cap. 15)** — Formato "scheda rischio singola riga":
> - Ogni rischio (15.1, 15.2, ...) è una tabella a **1 riga × 5 colonne**, SENZA riga di intestazione
> - Colonne: `Codice | Descrizione rischio | P | D | Misure DPC/DPI`
> - Larghezze: Col0 ~1.2cm, Col1 ~5cm, Col2 ~0.8cm, Col3 ~0.8cm, Col4 ~8.2cm
> - Font: tutte le celle 9pt Calibri; colonne 0-3 BOLD
> - **Sfondo colonne 0-3**: celeste `#F0F4F8`
> - **Sfondo colonna 4 (misure)**: colorata in base al livello di rischio R=P×D:
>   - R ≥ 9 (CRITICO): rosso chiaro `#FECACA`
>   - R 6-8 (ALTO): arancio chiaro `#FED7AA`
>   - R 3-5 (MEDIO): giallo chiaro `#FEF9C3`
>   - R 1-2 (BASSO): verde chiaro `#D1FAE5`
> - Le avvertenze H.x vengono inserite come tabella 1×1 con sfondo `#FFF5F5` PRIMA della tabella rischio
> - I titoli di sottosezione (15.1, 15.2, ...) sono Heading level 2
>
> **B. CARTELLONISTICA (Cap. 9.5)** — Formato "scheda pittogramma":
> - Tabella a **3 colonne**: `Pittogramma | Tipo Segnale | Esposizione nel Cantiere`
> - Riga 0 (intestazione): sfondo blu `#2F5496`, testo bianco bold 9pt
> - Colonna 0 (Pittogramma): immagine PNG del pittogramma ISO 7010 (larghezza 1.8 cm, centrata)
> - Le immagini dei pittogrammi sono conservate nella cartella `signs_ref/` e mappate nel file `mapping.json`
> - Se le immagini non sono disponibili, inserire il codice ISO (es. "M003") come testo
> - Colonna 1 (Tipo Segnale): codice + denominazione in bold + sotto in grigio piccolo il riferimento normativo
> - Colonna 2 (Esposizione): testo specifico per il cantiere
> - Larghezze: Col0 ~2.5cm, Col1 ~6cm, Col2 ~7.5cm
> - Una tabella separata per ogni categoria (Prescrizione, Pericolo, Divieto, Emergenza, Antincendio)
>
> **C. WARNING e NOTE** — Formato "box singola cella":
> - Avvertenze (⚠ H.x): tabella 1×1, sfondo `#FFF5F5`, testo 9pt, codice in bold rosso `#C00000`
> - Note (📌): tabella 1×1, sfondo `#F0F9FF`, testo 9pt
> - Clausole legali (🔒): tabella 1×1, sfondo `#EBF5FB`, titolo bold blu `#1F4E79`
>
> **D. SOTTOSCRIZIONI** — Formato "griglia 2×2":
> - Tabella 2 righe × 2 colonne (CSE | Committente / Affidataria | Subappaltatrice)
> - Con emoji ruolo (🛡, 🏢, 🏗, 🔧)
>
> **E. ALLEGATI** — Devono essere SVILUPPATI in calce al documento, non solo elencati:
> - Allegato 1: tabella completa lavorazioni (Cod. | Lavorazione | Descrizione | Impresa | Durata)
> - Allegato 2: cronoprogramma Gantt testuale (tabella con celle colorate per impresa)
> - Allegato 3: layout planimetrico in tabella descrittiva
> - Allegato 4: Fascicolo dell'Opera completo (3 Schede: I descrizione, II rischi manutenzione, III documentazione)
> - Allegato 5: checklist macchine compilabile (con caselle ☐ Sì ☐ No)
> - Allegato 6: calcolo uomini-giorno in tabella
> - Allegato 7: modulo near miss compilabile

---

## FRONTESPIZIO

```
──────────────────────────────────────────────────
STUDIO ASSOCIATO EVOLUTION | Piano di Sicurezza e Coordinamento
──────────────────────────────────────────────────

PIANO DI SICUREZZA E COORDINAMENTO
(Allegato XV e art. 100 del D.Lgs. 9 aprile 2008 n. 81 e s.m.i.)

[TIPO_INTERVENTO] di impianto tecnologico di radiotelecomunicazioni
Stazione Radio Base Iliad Italia S.p.A. — [TIPO_SITO] — [STRUTTURA_es: Palo h=30m / Roof Top]

┌─────────────────────┬──────────────────────────────────────────┐
│ CODICE SITO         │ [CODICE_SITO]                            │
│ NOME SITO           │ [NOME_SITO]                              │
│ INDIRIZZO           │ [INDIRIZZO_CANTIERE]                     │
│ COMUNE              │ [COMUNE]                                 │
│ PROVINCIA           │ [PROVINCIA] ([SIGLA])                    │
│ REGIONE             │ [REGIONE]                                │
│ TIPO SITO           │ [TIPO_SITO] — [DETTAGLIO_es: Rawland]   │
│ CONFIGURAZIONE      │ [CONFIG_es: T3 — 3 Settori — 5 tecn.]  │
│ COMMITTENTE         │ Iliad Italia S.p.A.                      │
│ IMPRESA             │ Circet Italia S.p.A.                     │
│ CSP / CSE           │ [NOME_CSE] — [STUDIO], [CITTA]          │
│ DATA DOCUMENTO      │ [DATA_DOCUMENTO]                         │
└─────────────────────┴──────────────────────────────────────────┘

┌──────┬────────────┬─────────────────┬───────────────┬──────────────┬────────────────┐
│ Rev. │ Data       │ Descrizione     │ Redatto       │ Committenza  │ Impresa        │
├──────┼────────────┼─────────────────┼───────────────┼──────────────┼────────────────┤
│ 1    │ [DATA]     │ Prima emissione │ [NOME_CSE]    │ Iliad Italia │ Circet Italia  │
└──────┴────────────┴─────────────────┴───────────────┴──────────────┴────────────────┘

IL COORDINATORE PER LA SICUREZZA (CSP/CSE)     IL COMMITTENTE
[NOME_CSE]                                      Iliad Italia S.p.A.

_______________________________                 _______________________________
Firma e Timbro                                  Firma e Timbro
```

---

## CAPITOLO 1 — PREMESSA

📋 *Riferimenti: art. 100 D.Lgs. 81/2008 e s.m.i. — Allegato XV*

Il presente Piano di Sicurezza e Coordinamento (PSC) è redatto ai sensi dell'art. 100 e dell'Allegato XV del D.Lgs. 9 aprile 2008 n. 81 e successive modificazioni (D.Lgs. 3 agosto 2009 n. 106), in relazione al cantiere di [TIPO_INTERVENTO: installazione/adeguamento/dismissione] del [nuovo/esistente] impianto di radiotelecomunicazioni Iliad Italia S.p.A. — Sito [CODICE_SITO] «[NOME_SITO]» — Comune di [COMUNE] ([SIGLA_PROV]).

### 🔒 LEGALE — Clausola specificità PSC (Cap. 1) — da `responsabilita-penale.md` sez. A.2

> **⚠ AVVERTENZA H.1** — Cass. Pen., Sez. IV, n. 27382/2021; n. 7421/2026: il presente PSC è stato redatto con specifico riferimento al cantiere in oggetto e alle sue criticità peculiari. Un PSC generico e standardizzato, non aderente alle reali criticità del sito, equivale a una totale omissione ai fini della colpa penale. Ogni sezione è calibrata sulle condizioni effettive del cantiere e dovrà essere aggiornata in caso di varianti o nuove criticità emerse in corso d'opera.

Il PSC contiene l'individuazione, l'analisi e la valutazione dei rischi, le procedure, gli apprestamenti e le attrezzature necessarie per la sicurezza dei lavoratori. L'impresa appaltatrice è tenuta a valutarne i contenuti prima della formulazione dell'offerta. Durante l'esecuzione dei lavori risulterà la presenza di più imprese (affidataria + subappaltatrici), configurando i presupposti dell'art. 90 D.Lgs. 81/2008.

Normativa di riferimento: D.Lgs. 81/2008 e s.m.i.; D.Lgs. 106/2009; D.P.R. 380/2001 art. 3; D.Lgs. 259/2003 (Codice delle Comunicazioni Elettroniche); D.M. 37/2008; D.L. 159/2025 conv. L. 198/2025 (patente a crediti); Circ. INL n. 1/2026.

### 🔒 LEGALE — Posizioni di garanzia (Cap. 1) — da `responsabilita-penale.md` sez. A, B

> **Titolari delle posizioni di garanzia nel presente cantiere:**
>
> | Soggetto | Posizione di garanzia | Riferimento normativo |
> |----------|----------------------|----------------------|
> | Committente (Iliad Italia S.p.A.) | Designazione CSP/CSE, verifica idoneità imprese, trasmissione Notifica Preliminare | Art. 90 D.Lgs. 81/08 |
> | RdL / CSP ([NOME_CSE]) | Redazione PSC conforme All. XV, Fascicolo Opera | Art. 91 D.Lgs. 81/08 |
> | CSE ([NOME_CSE]) | Vigilanza concreta applicazione PSC/POS, coordinamento imprese, sospensione in caso di pericolo grave | Art. 92 D.Lgs. 81/08 |
> | DL Impresa affidataria (Circet) | Elaborazione POS, rispetto PSC, DPI, formazione | Art. 96-97 D.Lgs. 81/08 |
> | DL Impresa subappaltatrice | POS specifico, coordinamento con affidataria | Art. 96-97 D.Lgs. 81/08 |

---

## CAPITOLO 2 — ANAGRAFICA DI CANTIERE

📋 *Riferimenti: punto 2.1.2, lettera a, punto 1, Allegato XV D.Lgs. 81/2008*

### 2.1 Caratteristiche dell'opera

| Campo | Valore |
|-------|--------|
| Natura dell'Opera | Civile / Impiantistica TLC |
| Oggetto | Piano di Sicurezza e Coordinamento (art. 100 D.Lgs. 81/08) — [CODICE_SITO] [NOME_SITO] — [TIPO_INTERVENTO] [STRUTTURA] |
| Titolo abilitativo | ✏ DA COMPILARE — SCIA/Autorizzazione n. ___ del ___ |
| Importo presunto dei lavori | € [IMPORTO] (stima Order Form) |
| Numero imprese in cantiere | [N_IMPRESE] ([ELENCO_IMPRESE]) |
| N° max lavoratori contemporanei | [N_MAX_LAV] (massimo presunto) |
| Entità presunta del lavoro | [UOMINI_GIORNO] uomini/giorno |
| Data inizio lavori | ✏ DA COMPILARE |
| Data fine lavori (presunta) | ✏ DA COMPILARE |
| Durata presunta | ~[DURATA_GG] giorni lavorativi |

### 2.2 Soggetti per la sicurezza

**🏢 COMMITTENTE**
- Ragione sociale: Iliad Italia S.p.A.
- Sede: Viale Francesco Rastelli n.1/A, 20124 Milano (MI)
- Referente: ✏ DA COMPILARE — nome e qualifica referente Iliad
- P.IVA: ✏ DA COMPILARE

**👤 RESPONSABILE DEI LAVORI / CSP / CSE**
- Nome e Cognome: [NOME_CSE]
- Studio: [NOME_STUDIO]
- Indirizzo: [INDIRIZZO_STUDIO]
- Tel./Fax: [TEL_STUDIO]
- E-mail: [EMAIL_STUDIO]
- Ordine Ingegneri: [ORDINE_PROV] — Sez. [SEZ] — n. [N_ISCRIZIONE]
- C.F.: [CF_CSE]

**🏗 IMPRESA AFFIDATARIA ED ESECUTRICE**
- Ragione sociale: CIRCET ITALIA S.P.A.
- Sede: Via Aterno, 108 — 66020 San Giovanni Teatino (CH)
- P.IVA: 01481120697
- Referente/DL: [REFERENTE_CIRCET]
- RSPP: ✏ DA COMPILARE
- RLS: ✏ DA COMPILARE
- Medico Compet.: ✏ DA COMPILARE

**🔧 IMPRESA ESECUTRICE SUBAPPALTATRICE (elettrica)**
- Ragione sociale: ✏ DA COMPILARE — impresa elettrica
- Datore di lavoro: ✏ DA COMPILARE
- P.IVA: ✏ DA COMPILARE

### 2.3 Numeri telefonici utili

| Servizio | Numero |
|----------|--------|
| Emergenza (unico europeo) | 112 |
| Pronto Soccorso / 118 | 118 |
| Carabinieri | 112 |
| Vigili del Fuoco | 115 |
| Ospedale più vicino | ✏ DA COMPILARE |
| ASL di [PROVINCIA] | [TEL_ASL] |
| CSE - [NOME_CSE] | [TEL_CSE] |
| Capocantiere Circet | ✏ DA COMPILARE |
| Referente Iliad | ✏ DA COMPILARE |

---

## CAPITOLO 3 — MODALITÀ DI GESTIONE DEL PSC

📋 *Riferimenti: artt. 92, 93 D.Lgs. 81/2008 e s.m.i.*

### 3.1 Revisione del piano

Il presente PSC è un documento dinamico. In caso di varianti in corso d'opera, modifiche organizzative, introduzione di nuove tecnologie o macchine non previste, o qualsiasi modifica che alteri il profilo di rischio, il CSE procederà all'aggiornamento tempestivo del PSC prima dell'inizio delle nuove attività (art. 92, co. 1, lett. a, D.Lgs. 81/08).

> **⚠ AVVERTENZA H.5** — Cass. Pen., Sez. IV, n. 24617/2025: la mancata tempestività nell'aggiornamento del PSC a fronte di varianti che modificano il profilo di rischio configura responsabilità penale del CSE. L'aggiornamento deve precedere l'inizio delle nuove attività.

### 🔒 LEGALE — Clausola aggiornamento PSC (Cap. 3.1) — da `tutela-patrimoniale-cse.md` sez. D.4

> Il presente PSC deve essere aggiornato a cura del CSE ogni qualvolta le condizioni di cantiere varino rispetto a quanto previsto (varianti progettuali, nuovi sub-appaltatori, modifica del cronoprogramma, eventi imprevedibili). Il committente/RdL è tenuto a comunicare tali variazioni per iscritto al CSE con congruo anticipo (minimo 5 giorni lavorativi prima dell'avvio delle nuove lavorazioni), al fine di consentire l'aggiornamento tempestivo del PSC.
>
> In assenza di comunicazione da parte del committente/RdL, il PSC si intende aggiornato alle sole informazioni disponibili alla data dell'ultima revisione.

### 3.2 Attività di coordinamento del CSE

L'attività di coordinamento del CSE comporta un obbligo di vigilanza concreto e sostanziale, non limitato al controllo formale della documentazione. Il CSE verificherà personalmente, con sopralluoghi di frequenza adeguata alla complessità delle lavorazioni in corso, che le previsioni del presente PSC siano effettivamente attuate. Di ogni sopralluogo sarà redatto verbale con le osservazioni rilevate e le eventuali prescrizioni impartite.

> **⚠ AVVERTENZA H.4** — Cass. Pen., Sez. IV, n. 24617/2025; n. 6272/2025: il CSE è tenuto a una vigilanza concreta e non meramente formale. La nomina del CSE non esonera il committente dai propri obblighi. In caso di pericolo grave e imminente il CSE dispone immediatamente la sospensione delle lavorazioni ai sensi dell'art. 92, co. 1, lett. f).

> **⚠ AVVERTENZA H.2** — Cass. Pen., Sez. IV, n. 7414/2024: il potere-dovere di sospensione è correlato a qualsiasi ipotesi di pericolo grave, a prescindere dalla verifica di specifiche violazioni normative o del rischio interferenziale. L'omessa sospensione configura responsabilità penale del CSE.

### 🔒 LEGALE — Clausola perimetro vigilanza CSE (Cap. 3.2) — da `responsabilita-penale.md` sez. A.3

> Il Coordinatore per la Sicurezza in fase di Esecuzione (CSE), nell'ambito del presente cantiere, esercita le funzioni di vigilanza e coordinamento mediante: (a) sopralluoghi periodici documentati con verbale firmato dal rappresentante dell'impresa affidataria; (b) verifica preventiva della conformità del POS ai contenuti minimi dell'Allegato XV; (c) riunioni di coordinamento all'avvio di ciascuna fase lavorativa critica; (d) sistema di segnalazione scritta delle inadempienze al committente/RdL. Eventuali varianti alle lavorazioni previste comportano obbligo di aggiornamento del PSC ai sensi dell'art. 92 co. 1 lett. b).

### 🔒 LEGALE — Clausola perimetro funzioni CSE (Cap. 3.3) — da `tutela-patrimoniale-cse.md` sez. D.2

> **3.3 PERIMETRO DELLE FUNZIONI DEL COORDINATORE PER L'ESECUZIONE**
>
> Il presente PSC è elaborato sulla base delle informazioni, dei documenti progettuali e delle condizioni di cantiere disponibili alla data di redazione. Il CSE non può garantire il rispetto del PSC da parte delle imprese al di fuori delle proprie attività di verifica periodica. La vigilanza continua e permanente sulle singole lavorazioni rimane obbligo del datore di lavoro di ciascuna impresa (art. 96 D.Lgs. 81/2008).
>
> Il CSE si riserva di aggiornare il PSC a fronte di varianti progettuali, ingresso di nuove imprese o modifiche organizzative comunicate per iscritto dal committente/RdL.

### 3.4 Consultazione RLS

Prima dell'accettazione del PSC, il datore di lavoro di ciascuna impresa esecutrice consulta il RLS e gli fornisce eventuali chiarimenti. Il RLS ha diritto di formulare proposte in merito. La consultazione viene verbalizzata.

### 3.5 Riunione di coordinamento

Prima dell'inizio dei lavori il CSE convoca una riunione di coordinamento con i datori di lavoro delle imprese esecutrici e i RLS. Ordine del giorno: illustrazione PSC, pianificazione interferenze, assegnazione responsabilità DPI, verifica documenti di ingresso. Cadenza delle riunioni successive: settimanale o al bisogno.

---

## CAPITOLO 4 — NOTIFICA PRELIMINARE

📋 *Riferimenti: art. 99 D.Lgs. 81/2008 e s.m.i.*

Il committente (Iliad Italia S.p.A.) o il Responsabile dei Lavori, prima dell'inizio dei lavori, trasmette la Notifica Preliminare all'Azienda Sanitaria Locale e alla Direzione Provinciale del Lavoro territorialmente competenti ([ASL_TERRITORIO] e DTL [PROVINCIA]), ai sensi dell'art. 99 D.Lgs. 81/2008.

> 📌 La Notifica Preliminare è obbligatoria in quanto il cantiere prevede la presenza di più imprese esecutrici. Copia firmata va affissa in cantiere per tutta la durata dei lavori.

✏ DA COMPILARE — Numero protocollo Notifica Preliminare e data invio

---

## CAPITOLO 5 — DISPOSIZIONI PER LE IMPRESE

📋 *Riferimenti: punto 2.1.2, lettera b, Allegato XV D.Lgs. 81/2008*

### 5.1 Obblighi delle imprese

Prima dell'inizio dei lavori, l'impresa affidataria trasmette il proprio POS al CSE che ne verificherà l'idoneità sostanziale, non meramente documentale.

> **⚠ AVVERTENZA H.3** — Cass. Pen. Sez. IV, n. 2845/2021; n. 4813: il CSE è tenuto alla verifica sostanziale dell'idoneità del POS. L'accettazione di un POS generico o inadeguato configura concorso di colpa del CSE in caso di infortunio. Ogni eventuale carenza dovrà essere segnalata per iscritto con richiesta formale di adeguamento.

### 5.2 Patente a crediti e badge digitale

Ai sensi dell'art. 27 D.Lgs. 81/08 come novellato dal D.L. 159/2025 (conv. L. 198/2025), tutte le imprese e i lavoratori autonomi operanti in cantiere devono essere titolari della patente a crediti con punteggio minimo di 15/30 (soglia ordinaria). È vietato l'accesso al cantiere a lavoratori privi di valida patente a crediti.

Ogni lavoratore presente in cantiere deve essere munito di tessera di riconoscimento digitale (badge) contenente: fotografia, dati anagrafici, codice fiscale, qualifica, data di assunzione, datore di lavoro. Il badge è obbligatorio anche per i lavoratori autonomi (D.Lgs. 81/08, art. 26, co. 8).

### 5.3 Contenuti minimi del POS

Il POS deve contenere almeno (Allegato XV D.Lgs. 81/08): dati identificativi dell'impresa; nominativi addetti emergenza/primo soccorso; elenco lavoratori con qualifica e formazione; descrizione lavorazioni e organizzazione del lavoro; analisi rischi specifici; elenco DPI forniti con dichiarazione di consegna; procedure lavori in quota con punti di ancoraggio; piano di manutenzione attrezzature; attestati di formazione.

### 🔒 LEGALE — 5.4 Obblighi contrattuali in materia di sicurezza — da `contratti-appalto.md` sez. F

> **5.4 OBBLIGHI CONTRATTUALI IN MATERIA DI SICUREZZA**
>
> Tutte le imprese operanti nel cantiere, ivi inclusi i sub-appaltatori e i lavoratori autonomi, sono tenute a:
>
> a) Trasmettere al CSE il POS almeno 10 giorni prima dell'inizio delle proprie lavorazioni;
> b) Non iniziare alcuna lavorazione prima della verifica di idoneità del POS da parte del CSE (art. 92 co. 1 lett. b D.Lgs. 81/08);
> c) Comunicare al CSE ogni variazione della composizione delle squadre, delle attrezzature o delle modalità operative;
> d) Partecipare alle riunioni di coordinamento convocate dal CSE;
> e) Designare un proprio referente di cantiere reperibile durante l'orario di lavoro;
> f) Rispettare le procedure di emergenza definite al Cap. 19 del PSC;
> g) Affiggere all'ingresso del cantiere la copia del PSC e del POS dell'impresa, disponibili per ispezioni ASL/ITL.
>
> La mancata osservanza delle prescrizioni del presente PSC sarà segnalata al committente/RdL per le conseguenti azioni contrattuali, ivi compresa la sospensione delle lavorazioni ai sensi dell'art. 92 co. 1 lett. f) D.Lgs. 81/2008.

### 🔒 LEGALE — 5.5 Clausole contrattuali sicurezza — da `contratti-appalto.md` sez. B

> **5.5 CLAUSOLE CONTRATTUALI APPLICABILI**
>
> **Costi della sicurezza (art. 26 co. 5 + Allegato XV punto 4):** I costi della sicurezza previsti nel presente PSC, pari a € [COSTI_SICUREZZA], sono quantificati separatamente e NON soggetti a ribasso d'asta.
>
> **Idoneità tecnico-professionale (art. 26 co. 1 + Allegato XVII):** L'appaltatore dichiara di possedere i requisiti di idoneità tecnico-professionale (iscrizione CCIAA, DURC, autocertificazione antimafia, attestati formazione, elenco attrezzature conformi CE, patente a crediti).
>
> **RC obbligatoria:** L'appaltatore dichiara di essere coperto da polizza RC verso terzi e verso i lavoratori con massimale non inferiore a € 500.000 per sinistro, in vigore per tutta la durata dei lavori.
>
> **Sub-appalto:** Il sub-appalto è consentito previa comunicazione scritta al committente/RdL e approvazione del CSE. L'impresa sub-appaltatrice è tenuta a: elaborare POS specifico; trasmettere documentazione Allegato XVII; rispettare integralmente il PSC. L'impresa affidataria rimane solidalmente responsabile (art. 97 D.Lgs. 81/2008).

---

## CAPITOLO 6 — DESCRIZIONE DELL'OPERA

📋 *Riferimenti: punto 2.1.2, lettera a, punti 2-3, Allegato XV D.Lgs. 81/2008*

### 🔒 LEGALE — Clausola informazioni fornite dal committente (Cap. 6) — da `tutela-patrimoniale-cse.md` sez. D.3

> Le informazioni riportate nella presente sezione sono state fornite dal committente/RdL e/o estratte dalla documentazione progettuale messa a disposizione del CSP. Il CSP non risponde per l'inesattezza di tali informazioni, salvo che fossero rilevabili attraverso la normale diligenza professionale.

### 6.1 Inquadramento territoriale

La Stazione Radio Base Iliad Italia S.p.A. codice sito [CODICE_SITO] «[NOME_SITO]» è ubicata nel Comune di [COMUNE] ([SIGLA_PROV]), Regione [REGIONE]. Il sito è di tipo [TIPO_SITO] ([DETTAGLIO_SITO]), in zona a destinazione d'uso ✏ DA COMPILARE (destinazione urbanistica e catastale: Foglio ___, Particella ___, Sez. ___).

Il contesto circostante è caratterizzato da: ✏ DA COMPILARE — descrivere se residenziale, agricolo, industriale, presenza di strade pubbliche, distanze da confini.

> 📌 Allegare ortofoto/immagine satellite con perimetro cantiere evidenziato — ✏ DA COMPILARE

### 6.2 Descrizione dell'infrastruttura e dell'intervento

Il presente PSC riguarda [DESCRIZIONE_INTERVENTO]. Il sito è classificato come [CLASSIFICAZIONE_SITO].

**L'intervento prevede:**
- [LAVORAZIONE_1]
- [LAVORAZIONE_2]
- [LAVORAZIONE_3]
- [LAVORAZIONE_N]
- Messa in servizio, test e collaudo funzionale dell'impianto

> 📌 ✏ DA COMPILARE: allegare foto dello stato dei luoghi ante-operam (schede foto §6.3).

### 6.3 Schede rilievo fotografico

| N° | Titolo | Data | Ora | Posizione |
|----|--------|------|-----|-----------|
| 📷 1 | ACCESSO PRINCIPALE AL CANTIERE | ___/___ | ___ | ___ |
| 📷 2 | AREA DI LAVORO — STATO DEI LUOGHI ANTE-OPERAM | ___/___ | ___ | ___ |
| 📷 3 | ZONA FONDAZIONI / COPERTURA | ___/___ | ___ | ___ |
| 📷 4 | ZONA DEPOSITO MATERIALI E ATTREZZATURE | ___/___ | ___ | ___ |
| 📷 5 | SOTTOSERVIZI E RETI ESISTENTI VISIBILI | ___/___ | ___ | ___ |
| 📷 6 | CONTESTO URBANO / EDIFICI ADIACENTI | ___/___ | ___ | ___ |
| 📷 7 | VIABILITÀ DI ACCESSO AL CANTIERE | ___/___ | ___ | ___ |
| 📷 8 | AREA ALLACCIAMENTO ELETTRICO / CAVIDOTTO | ___/___ | ___ | ___ |

*Per ogni scheda: inserire foto + didascalia descrittiva*

---

## CAPITOLO 7 — AREA DI LAVORO

📋 *Riferimenti: punto 2.1.2, lettera a, Allegato XV D.Lgs. 81/2008*

Il cantiere di [NOME_SITO] è ubicato su [TIPO_TERRENO]. La zona è classificata come ✏ DA COMPILARE. Le lavorazioni si sviluppano prevalentemente in quota ([DETTAGLIO_QUOTA]) e a terra ([DETTAGLIO_TERRA]). Il perimetro di cantiere sarà recintato per un'area minima di [RAGGIO_MIN] dal [STRUTTURA_PRINCIPALE] (zona di caduta oggetti).

Fattori ambientali: presenza di ✏ DA COMPILARE. Verificare con il gestore di rete la presenza di sottoservizi prima dello scavo (art. 100 D.Lgs. 81/08; Allegato XV pt. 2.1.3).

> **⚠ AVVERTENZA H.1** — Il presente PSC è specifico per questo sito: le caratteristiche geomorfologiche, i sottoservizi presenti e i rischi interferenziali con il contesto circostante sono analizzati nelle sezioni seguenti con riferimento esclusivo al cantiere [CODICE_SITO].

---

## CAPITOLO 8 — RISCHI INTRINSECI E FATTORI ESTERNI

📋 *Riferimenti: punto 2.2.1, Allegato XV D.Lgs. 81/2008*

### 8.1 Caratteristiche idrogeologiche

✏ DA COMPILARE — Descrivere eventuale presenza di falda, rischio allagamento, caratteristiche del terreno.

### 8.2 Fattori esterni che comportano rischi per il cantiere

| Fattore esterno | Presenza | Misure preventive |
|-----------------|----------|-------------------|
| Linee elettriche aeree | ✏ Verificare | Mantenere distanza min. 5 m; segnalare |
| Reti interrate (gas, acqua, TLC) | ✏ Verificare | Richiesta planimetrie enti gestori |
| Strade pubbliche adiacenti | ✏ Verificare | Recinzione cantiere; segnaletica D.M. 10/07/2002 |
| Edifici residenziali vicini | ✏ Verificare | Zona di caduta recintata; protezione rumore/polveri |
| Presenza altri cantieri | ✏ Verificare | Se riscontrati, coordinare con CSE |

---

## CAPITOLO 9 — ORGANIZZAZIONE DEL CANTIERE

📋 *Riferimenti: punto 2.1.2, lettera c, Allegato XV D.Lgs. 81/2008 — punto 2.2.2*

### 9.1 Recinzione, accessi, segnalazioni

Il cantiere dovrà essere completamente recintato con recinzione metallica (rete + paletti) per un'area minima di [RAGGIO_MIN] dal [STRUTTURA_PRINCIPALE], al fine di garantire la zona di caduta oggetti dall'alto. L'accesso al cantiere è consentito da un unico ingresso presidiato, munito di cancello con lucchetto. Segnaletica di accesso vietato ai non autorizzati (P006) su tutti i lati della recinzione.

### 9.2 Impianti di cantiere

IMPIANTO ELETTRICO: Quadro generale di cantiere conforme CEI 64-8, sezione 704, con interruttore generale, differenziale 30 mA e sezionatori per ogni circuito. Dichiarazione di conformità obbligatoria (D.M. 37/2008). Messa a terra secondo DPR 462/2001.

PRESIDI IGIENICI: Bagno chimico mobile certificato. Acqua potabile disponibile. Baraccamento/container per ricovero maestranze se durata > 5 giorni.

### 9.3 Aree di stoccaggio

I materiali saranno stoccati in aree dedicate, lontano dalla zona di sollevamento e dai percorsi pedonali. Rifiuti e materiali dismessi in container separato (D.Lgs. 152/2006).

### 9.4 Coordinamento lavorazioni — rischio interferenziale

Il cantiere prevede la compresenza di n. [N_IMPRESE] imprese esecutrici ([ELENCO_IMPRESE]). Le fasi di lavoro sono sequenziali per quanto possibile; quando coesistono, il CSE stabilisce le fasce orarie e i percorsi assegnati a ciascuna impresa.

> **⚠ AVVERTENZA H.6** — Cass. Pen. n. 23725/2023; n. 37214/2024: il PSC individua e analizza i rischi interferenziali derivanti dalla compresenza di più imprese. Ciascuna impresa resta responsabile dei rischi specifici propri nel suo POS. Il CSE non può ignorare situazioni di pericolo grave macroscopicamente evidente, anche se riconducibili a rischio specifico dell'impresa.

### 9.5 Segnaletica generale prevista nel cantiere

📋 *Riferimenti: artt. 161-166 e Allegati XXIV-XXXII D.Lgs. 81/2008 — UNI EN ISO 7010*

**Cartelli di PRESCRIZIONE (M — Fondo Blu, simbolo Bianco)**

| Pittogramma | Tipo Segnale | Esposizione nel Cantiere |
|-------------|-------------|--------------------------|
| [IMG_M003] | M003 — Protezione obbligatoria del capo (elmetto) [All. XXIV-XXV D.Lgs. 81/08] | [POSIZIONE_SPECIFICA] |
| [IMG_M004] | M004 — Protezione obbligatoria dei piedi (scarpe S3) [All. XXIV-XXV] | [POSIZIONE_SPECIFICA] |
| [IMG_M008] | M008 — Protezione obbligatoria delle mani (guanti EN 388) [All. XXIV-XXV] | [POSIZIONE_SPECIFICA] |
| [IMG_M014] | M014 — Giubbotto ad alta visibilità (EN ISO 20471) [All. XXIV-XXV] | [POSIZIONE_SPECIFICA] |
| [IMG_M015] | M015 — Imbracatura di sicurezza anticaduta (EN 361) [All. XXIV-XXV; art. 115 D.Lgs. 81/08] | [POSIZIONE_SPECIFICA] |

**Cartelli di PERICOLO (W — Fondo Giallo, bordo/simbolo Nero)**

| Pittogramma | Tipo Segnale | Esposizione nel Cantiere |
|-------------|-------------|--------------------------|
| [IMG_W005] | W005 — Pericolo radiazioni non ionizzanti (CEM) [art. 209 D.Lgs. 81/08; ISO 7010] | [POSIZIONE_SPECIFICA] |
| [IMG_W008] | W008 — Pericolo elettrico / tensione pericolosa [All. XXIV-XXV D.Lgs. 81/08] | [POSIZIONE_SPECIFICA] |
| [IMG_W012] | W012 — Pericolo carichi sospesi [All. XXIV-XXV D.Lgs. 81/08] | [POSIZIONE_SPECIFICA] |
| [IMG_W024] | W024 — Pericolo inciampo (cavi a terra) [ISO 7010] | [POSIZIONE_SPECIFICA] |

**Cartelli di DIVIETO (P — Fondo Bianco, bordo/barra Rossi)**

| Pittogramma | Tipo Segnale | Esposizione nel Cantiere |
|-------------|-------------|--------------------------|
| [IMG_P006] | P006 — Vietato l'accesso ai non autorizzati [art. 163 D.Lgs. 81/08; ISO 7010] | [POSIZIONE_SPECIFICA] |

**Cartelli di EVACUAZIONE / SALVATAGGIO (E — Fondo Verde, simbolo Bianco)**

| Pittogramma | Tipo Segnale | Esposizione nel Cantiere |
|-------------|-------------|--------------------------|
| [IMG_E003] | E003 — Primo soccorso [Allegati XXIV-XXV D.Lgs. 81/08] | [POSIZIONE_SPECIFICA] |

**Cartelli di ANTINCENDIO (F — Fondo Rosso, simbolo Bianco)**

| Pittogramma | Tipo Segnale | Esposizione nel Cantiere |
|-------------|-------------|--------------------------|
| [IMG_F001] | F001 — Estintore [Allegati XXIV-XXV D.Lgs. 81/08] | [POSIZIONE_SPECIFICA] |

> 📌 La segnaletica va mantenuta leggibile per tutta la durata del cantiere. Verifica settimanale integrità/leggibilità (art. 165 D.Lgs. 81/08). Cartello di cantiere obbligatorio ex D.P.R. 380/2001 (100×200 cm).

---

## CAPITOLO 10 — SOSTANZE PERICOLOSE PRESENTI

📋 *Riferimenti: artt. 222-226 D.Lgs. 81/2008 — Reg. CE 1272/2008 (CLP)*

Le sostanze pericolose che potranno essere impiegate nel cantiere includono: olio per motori, solventi per sgrassaggio, sigillanti per passanti cavi, prodotti antiossidanti per connettori. Le SDS saranno tenute in cantiere in lingua italiana.

- Quantità limitate al fabbisogno giornaliero; eccedenze ricoverate in armadio chiuso
- In caso di sversamento: assorbimento con sabbia; smaltimento come rifiuto speciale
- Vietato fumare o usare fiamme libere nelle aree di stoccaggio prodotti chimici

---

## CAPITOLO 11 — ATTREZZATURE, MACCHINE E IMPIANTI

📋 *Riferimenti: artt. 70-73, 85-88 D.Lgs. 81/2008 — Allegato V — D.Lgs. 17/2010*

| Attrezzatura | Utilizzo | Abilitazione richiesta | Verifiche |
|--------------|----------|----------------------|-----------|
| Autogrù / Autocarro con gru | Sollevamento palo, antenne | Patentino PLE/gru (All. XIV) | Check-list pre-uso; libretto |
| PLE (piattaforma aerea) | Accesso in quota | Patentino PLE (All. XIV) | Check-list pre-uso; cinture |
| Scala portatile | Accesso brevi (< 30 min, h < 5m) | Formazione (QT.5 INAIL) | Integrità piedini e pioli |
| Trapano / Avvitatore | Fissaggi carpenteria | Formazione utensili | Connettori e cavi |
| Paranco manuale/elettrico | Sollevamento antenne | Formazione paranchi | Catena/fune e ganci |
| Saldatrice MIG/MAG | Adattamenti carpenteria | Qualifica EN 1090 (se appl.) | Messa a terra; DPI |
| Generatore elettrico | Alimentazione quadro | — | Isolamento e messa a terra |

> 📌 Tutte le attrezzature con dichiarazione di conformità CE e manuale in italiano. Verifica giornaliera (INAIL — Schede macchine).

---

## CAPITOLO 12 — DISPOSITIVI DI PROTEZIONE INDIVIDUALE (DPI)

📋 *Riferimenti: artt. 74-77, 107-108 D.Lgs. 81/2008 — Reg. UE 2016/425 — QT.7 INAIL*

Gerarchia: DPC > misure organizzative > DPI (art. 15 D.Lgs. 81/08).

> **⚠ AVVERTENZA H.7** — Cass. Pen. n. 8083/2019; n. 13590/2020; n. 47015/2022: per tutti i lavori in quota (h > 2 m), il PSC prescrive in via prioritaria DPC. Solo in via residuale e motivata si ricorre a DPI anticaduta III categoria. Nel presente cantiere, la PLE costituisce la misura collettiva primaria; l'imbracatura è DPI complementare obbligatorio e non alternativo alla PLE.

Distanza di tiro d'aria: per imbracatura anticaduta (EN 361) + cordino dinamico (EN 355), la distanza minima ≈ 6 m. Verificare in corrispondenza delle piattaforme intermedie.

| DPI | Norma | Cat. | Mansione obbligata | Frequenza verifica |
|-----|-------|------|--------------------|--------------------|
| Elmetto protezione testa | EN 397 | II | Tutti | Prima uso, mensile |
| Imbracatura anticaduta | EN 361 | III | Lavori in quota > 2 m | Prima ogni uso; annuale |
| Cordino dinamico doppio | EN 355 | III | Lavori in quota su palo/PLE | Prima ogni uso |
| Dispositivo retrattile | EN 360 | III | Piattaforme < 6 m alt. | Prima ogni uso |
| Scarpe antinfort. S3 SRC | EN ISO 20345 | II | Tutti | Mensile |
| Guanti da lavoro | EN 388:2016 | II | Movimentazione materiali | Prima uso |
| Guanti isolanti elettrici | IEC 60903 Cl.0 | III | Lavori impianti elettrici | Prima uso; semestrale |
| Gilet alta visibilità | EN ISO 20471 | II | Tutti (in cantiere) | Mensile |
| Occhiali protettivi | EN 166 | II | Smerigliatura, saldatura | Prima uso |
| Cuffie/tappi antirumore | EN 352-1 | II | Uso attrezzature rumorose | Prima uso |
| Maschera FFP2 | EN 149 | III | Polveri durante scavi | Monouso |

> 📌 Per lavori in quota su palo: obbligatorio sistema di progressione verticale certificato (EN 795 tipo A2 + connettore EN 12841 tipo A) o PLE certificata. QT.1 e QT.7 INAIL.

---

## CAPITOLO 13 — VALUTAZIONE DEL RUMORE

📋 *Riferimenti: artt. 189-192 D.Lgs. 81/2008*

| Classe | Leq dB(A) | Obblighi |
|--------|-----------|----------|
| I — Sotto soglia | < 80 | Informazione generale |
| II — Tra soglie | 80–85 | Informazione/formazione; DPI disponibili |
| III — Sopra soglia | 85–87 | DPI obbligatori; sorveglianza sanitaria |
| IV — Valore limite | ≥ 87 | Divieto superamento; interventi immediati |

Principali sorgenti: [SORGENTI_RUMORE_SPECIFICHE]. Si prescrivono DPI antirumore EN 352 per lavorazioni con attrezzature rumorose.

---

## CAPITOLO 14 — SORVEGLIANZA SANITARIA

📋 *Riferimenti: artt. 41-43, 164-167 D.Lgs. 81/2008*

La sorveglianza sanitaria è obbligatoria per i lavoratori esposti a rischi specifici: rumore, vibrazioni, MMC, lavori in quota. Il Medico Competente di ciascuna impresa effettua visita preventiva, emette giudizio di idoneità alla mansione specifica (incluso lavoro in quota), e visite periodiche.

> 📌 I lavoratori addetti al lavoro in quota devono essere dichiarati idonei alla mansione con specifica nota nel giudizio di idoneità del MC.

---

## CAPITOLO 15 — RISCHI PRINCIPALI — ANALISI E PREVENZIONE

📋 *Riferimenti: punto 2.2.3, Allegato XV D.Lgs. 81/2008 — Matrice R = P × D*

Metodologia: R = P × D. P (1=Bassa, 2=Media, 3=Alta) × D (1=Lieve, 2=Grave, 3=Gravissimo). R ≥ 9: CRITICO; 6-8: ALTO; 3-5: MEDIO; 1-2: BASSO.

### 🔒 LEGALE — Posizioni di garanzia per rischio critico — da `responsabilita-penale.md` sez. D

> Per ogni rischio con R ≥ 6 (ALTO o CRITICO), il PSC indica il titolare della posizione di garanzia:
> - **Misura DPC**: Titolare → CSE (verifica presenza); DL impresa (installazione/manutenzione)
> - **DPI residuo**: Titolare → DL impresa affidataria (fornitura e addestramento)
> - **Prescrizioni operative**: Titolare → CSE (coordinamento); Preposto impresa (esecuzione)

### 15.1 Caduta dall'alto (rischio principale)

> **⚠ H.7** — Cass. Pen. n. 8083/2019: DPC prioritari. Parapetto EN 13374 / PLE come misura collettiva principale. L'imbracatura anticaduta EN 361 è DPI complementare obbligatorio, non alternativo.

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure `#FECACA` (R=9 CRITICO)

| 15.1 | Caduta dall'alto da [STRUTTURA] (quota [QUOTA]m) | 3 | 3 | DPC: [PLE certificata / parapetto EN 13374 Cl. A se muretto < 100 cm]; piattaforme di lavoro fisse con parapetto. DPI: imbracatura EN 361 + cordino dinamico doppio EN 355 + dispositivo retrattile EN 360. Linea vita verticale tipo A2 (QT.1 INAIL). Tirante d'aria verificato. Lavori in coppia obbligatori. Divieto salita senza DPI III cat. allacciati. **GARANTE DPC**: CSE (verifica) + DL impresa (installazione). **GARANTE DPI**: DL impresa. |

### 15.2 Caduta di materiale dall'alto

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure `#FECACA` (R=9 CRITICO)

| 15.2 | Caduta di oggetti/attrezzi dall'alto (quota [QUOTA]m) | 3 | 3 | Recinzione cantiere raggio min [RAGGIO_MIN] (zona caduta). Schermi orizzontali alle piattaforme. Sacchi portautensili certificati. Divieto sosta sotto carico sospeso. Paranco con fune certificata per sollevamento. **GARANTE**: CSE + DL impresa. |

### 15.3 Elettrocuzione

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure `#FED7AA` (R=6 ALTO)

| 15.3 | Contatto con circuiti elettrici attivi / apparati sotto tensione | 2 | 3 | Quadro cantiere differenziale 30 mA + messa a terra. Personale qualificato PES/PAV CEI 11-27. Sezionamento con lucchetto. Guanti IEC 60903. W008. **GARANTE**: DL impresa (elettricista qualificato). |

### 15.4 Radiazioni non ionizzanti — CEM

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure da calibrare su P e D specifici del cantiere

| 15.4 | Esposizione a CEM da SRB adiacenti eventualmente attive | [P] | [D] | Verifica preventiva: SRB adiacenti attive? Se SÌ: misura CEM (art. 210 D.Lgs. 81/08). Segnaletica W005. **GARANTE**: CSE + DL impresa. |

### 15.5 Movimentazione manuale di carichi

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure `#FEF9C3` (R=4 MEDIO)

| 15.5 | Sovraccarico biomeccanico rachide durante MMC | 2 | 2 | Uso paranchi/argani per sollevamento pezzi > 25 kg. Frazionamento carichi. Formazione MMC (D.Lgs. 81/08 Titolo VI). Rotazione compiti max 2h. |

### 15.6 Microclima sfavorevole

> **⚠ AVVERTENZA H.8** — Orientamento Cass. Pen. 2023-2025: in caso di temperatura percepita > 35°C, gelo, vento forte (> 60 km/h), pioggia o scarsa visibilità, il CSE dispone la sospensione o la rimodulazione dei lavori in quota.

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure `#FEF9C3` (R=4 MEDIO)

| 15.6 | Esposizione a condizioni climatiche avverse (vento, caldo, gelo) | 2 | 2 | Monitoraggio previsioni meteo giornaliero. Sospensione lavori in quota con vento > 6 m/s. Pause ogni 2h in estate (T > 30°C). Idratazione obbligatoria. **GARANTE**: CSE + Preposto. |

### 15.7 — 15.N [Rischi aggiuntivi specifici per cantiere]

*Adattare al cantiere specifico: vibrazioni, scivolamenti, inciampi, interferenziali, rumore ecc. Per ogni rischio:*

> **FORMATO DOCX**: tabella singola riga 5 colonne con stessa struttura e colorazione.
> Per ogni rischio con R ≥ 6 indicare il garante.
> Colori: #FECACA (R≥9), #FED7AA (R 6-8), #FEF9C3 (R 3-5), #D1FAE5 (R 1-2)


---

## CAPITOLO 16 — PROGRAMMA DEI LAVORI — CRONOPROGRAMMA

📋 *Riferimenti: punto 2.1.2, lettera d, Allegato XV*

| N° | Fase di lavoro | Durata (gg) | Op. | Note interferenziali |
|----|---------------|-------------|-----|---------------------|
| 1 | [FASE_1] | [GG] | [OP] | [NOTE] |
| 2 | [FASE_2] | [GG] | [OP] | [NOTE] |
| ... | ... | ... | ... | ... |

Durata totale stimata: [DURATA_TOTALE] — Uomini/giorno totali: [UD_TOTALI].

---

## CAPITOLO 17 — ANALISI GENERALE DEI RISCHI — METODOLOGIA

📋 *Riferimenti: punto 2.2, Allegato XV — INAIL 'La Progettazione della Sicurezza nel Cantiere'*

Matrice R = P × D:

| P / D | D=1 Lieve | D=2 Grave | D=3 Gravissimo |
|-------|-----------|-----------|----------------|
| P=1 Bassa | 1 — BASSO | 2 — BASSO | 3 — MEDIO |
| P=2 Media | 2 — BASSO | 4 — MEDIO | 6 — ALTO |
| P=3 Alta | 3 — MEDIO | 6 — ALTO | 9 — CRITICO |

Fasi critiche per interferenza: [ELENCO_FASI_CRITICHE].

---

## CAPITOLO 18 — INDIVIDUAZIONE, ANALISI E VALUTAZIONE DEI RISCHI

📋 *Riferimenti: punto 2.2.3, Allegato XV — modello INAIL schede fase lavorativa*

### 18.1 Rischi generali comuni a tutte le fasi

- Viabilità interna cantiere: accesso unico controllato con segnaletica permanente
- Disponibilità presidi sanitari e numeri emergenza visibili
- Coordinamento imprese: riunioni settimanali CSE — datori di lavoro; verbali obbligatori
- Verifica patente a crediti e badge digitale a ogni accesso
- Controllo formazione specifica: lavori in quota, macchine, impianti elettrici

### 18.2 Schede fasi lavorative (modello INAIL)

*Per ogni fase del cronoprogramma, compilare la scheda seguente:*

**18.2.N — [NOME_FASE]**

| Campo | Contenuto |
|-------|-----------|
| Descrizione attività | [DESCRIZIONE] |
| Fattori di rischio | [RISCHI_SPECIFICI] |
| DPC (misure collettive) | [DPC] |
| DPI (individuali) | [DPI] |
| Prescrizioni operative | [PRESCRIZIONI] |
| Segnaletica prevista | [SEGNALETICA] |

### 18.3 Interferenze critiche tra fasi

> **⚠ H.6** — Cass. Pen. n. 23725/2023: il PSC individua i rischi interferenziali.

| Fasi sovrapposte | Rischio interferenziale | Misura di coordinamento CSE |
|-----------------|------------------------|---------------------------|
| [FASE_A + FASE_B] | [RISCHIO] | [MISURA] |

---

## CAPITOLO 19 — GESTIONE DELLE EMERGENZE

📋 *Riferimenti: artt. 37-38, 43-45 D.Lgs. 81/2008 — D.M. 388/2003*

### 19.1 Presidi sanitari

- Cassetta pronto soccorso conforme D.M. 388/2003
- Lettino per traumatizzati e coperte isotermiche
- DAE se ospedale > 15 minuti
- Addetto Primo Soccorso: ✏ DA COMPILARE

Procedura infortunio: 1) Non spostare il ferito. 2) Valutare coscienza/respirazione. 3) Contattare 118. 4) Primo soccorso da addetto formato. 5) CSE informato immediatamente. 6) Denuncia INAIL.

> **⚠ H.2** — In caso di pericolo grave e imminente il CSE dispone sospensione immediata. Comunicazione scritta al committente.

### 19.2 Procedura specifica — [EMERGENZA_TIPICA]

[Procedura dettagliata specifica per il cantiere: es. caduta dall'alto, elettrocuzione, CEM]

### 19.3 Antincendio

- Estintori polvere ABC 6 kg: min 2 unità
- Estintore CO2 5 kg: presso quadro elettrico
- VIETATO fumare in cantiere; VIETATO accendere fuochi
- Procedura incendio: 1) Allontanamento persone 2) Chiamata 115 3) Uso estintore se sicuro

### 19.4 Condizioni meteorologiche avverse

Sospensione lavori in quota:
- Vento > 6 m/s (21,6 km/h)
- Temporali / fulmini
- Temperatura percepita > 35°C — turni ridotti, pause, idratazione
- Ghiaccio o neve su piattaforme — pulizia prima della salita
- Nebbia con visibilità < 50 m

---

## CAPITOLO 20 — STIMA DEI COSTI DELLA SICUREZZA

📋 *Riferimenti: punto 2.3 e punto 4, Allegato XV D.Lgs. 81/2008*

| Voce di costo | Qta | U.M. | Costo unit. | Totale |
|--------------|-----|------|-------------|--------|
| Imbracatura anticaduta + cordino (noleggio/dotazione) | [Q] | pz | € [CU] | € [TOT] |
| Linea vita EN 795 tipo A2 (installazione e verifica) | [Q] | cad | € [CU] | € [TOT] |
| Segnaletica di cantiere (recinzione, cartelli ISO 7010) | 1 | set | € [CU] | € [TOT] |
| Cassetta pronto soccorso D.M. 388/2003 | 1 | cad | € [CU] | € [TOT] |
| Estintori | [Q] | pz | € [CU] | € [TOT] |
| DPI generici (guanti, occhiali, FFP2, tappi) | 1 | set | € [CU] | € [TOT] |
| Misurazioni CEM preventive e finali | [Q] | rap | € [CU] | € [TOT] |
| Riunioni di coordinamento CSE | [Q] | ore | € [CU] | € [TOT] |
| Sopralluoghi CSE in cantiere | [Q] | ore | € [CU] | € [TOT] |
| **TOTALE COSTI SICUREZZA** | | | | **€ [TOTALE]** |

> 📌 Importo lavori: € [IMPORTO]. Incidenza sicurezza: [PERC]% (> 1,5% soglia minima Allegato XV). I costi della sicurezza NON sono soggetti a ribasso d'asta.

---

## CAPITOLO 21 — DOCUMENTI DA TENERE IN CANTIERE

📋 *Riferimenti: art. 107, Allegato XV D.Lgs. 81/2008*

- 21.1 — PSC e aggiornamenti
- 21.2 — POS di tutte le imprese
- 21.3 — Notifica Preliminare protocollata
- 21.4 — Nominativi e contatti: CSP, CSE, DL, RSPP, RLS, MC
- 21.5 — Patente a crediti (visura aggiornata)
- 21.6 — Registro presenze giornaliero con badge digitali
- 21.7 — SDS sostanze pericolose
- 21.8 — Dichiarazioni CE e manuali d'uso attrezzature
- 21.9 — Certificati linea vita / sistemi anticaduta
- 21.10 — Certificati taratura equipaggiamenti sollevamento
- 21.11 — Schede tecniche imbracature, cordini, moschettoni
- 21.12 — Attestati formazione (lavori in quota, PLE, impianti elettrici)
- 21.13 — Verbali riunioni di coordinamento CSE
- 21.14 — Verbali sopralluoghi CSE
- 21.15 — Relazioni misurazioni CEM preventive e finali
- 21.16 — Rapporti misurazioni rumore (se applicabile)
- 21.17 — Moduli segnalazione near miss (All. 7)
- 21.18 — DURC in corso di validità
- 21.19 — Titolo abilitativo e cartello di cantiere obbligatorio

---

## CAPITOLO 22 — ALLEGATI

- **Allegato 1** — Elenco lavorazioni (rif. Schede 18.2 e cronoprogramma Cap. 16)
- **Allegato 2** — Cronoprogramma lavori (Diagramma di Gantt)
- **Allegato 3** — Layout planimetrico del cantiere
- **Allegato 4** — Fascicolo dell'Opera (art. 91 D.Lgs. 81/08)
- **Allegato 5** — Check-list macchine e attrezzature
- **Allegato 6** — Calcolo uomini-giorno
- **Allegato 7** — Modulo segnalazione near miss

---

## SOTTOSCRIZIONI — ACCETTAZIONE DEL PIANO

[LUOGO], [DATA]

```
IL COORDINATORE PER LA SICUREZZA         IL COMMITTENTE
(CSP e CSE)                               Iliad Italia S.p.A.
[NOME_CSE]                                ✏ DA COMPILARE
[STUDIO]
Ordine Ingegneri [PROV] — n. [N_ISCR]
                                          _______________________________
_______________________________           Firma e Timbro
Firma e Timbro

L'IMPRESA AFFIDATARIA                    IMPRESA SUBAPPALTATRICE
Circet Italia S.p.A.                      ✏ DA COMPILARE
[REFERENTE_CIRCET]                        ✏ DA COMPILARE

_______________________________           _______________________________
Firma e Timbro                            Firma e Timbro
```

> 📌 Copia del PSC sottoscritta da tutte le imprese deve essere tenuta in cantiere per tutta la durata dei lavori. Il POS deve essere consegnato al CSE prima dell'inizio delle lavorazioni (art. 96, co. 1, lett. g, D.Lgs. 81/08).

---

## 🔒 APPENDICE LEGALE — CHECKLIST PRE-CONSEGNA

### Checklist F.1 — Sezioni a MASSIMO rischio sanzionatorio (da `sanzioni-conformita.md`)

Eseguire PRIMA della consegna del PSC:

- [ ] **Art. 100 + Allegato XV**: Il PSC contiene TUTTE le sezioni obbligatorie (Cap. 1-22)
- [ ] **Allegato XV punto 2.1.2**: Entità presunta espressa in uomini-giorno
- [ ] **Allegato XV punto 2.2**: Descrizione sintetica con scelte progettuali e organizzative
- [ ] **Allegato XV punto 2.3**: Area di cantiere con analisi del contesto
- [ ] **Allegato XV punto 2.4**: Organizzazione cantiere (recinzione, accessi, viabilità)
- [ ] **Allegato XV punto 4**: Stima costi sicurezza in forma ANALITICA (non forfettaria)
- [ ] **Art. 99**: Notifica Preliminare (obbligo se > 200 gg-uomo O > 1 impresa)

### Checklist F.3 — Elementi difensivi per il CSE (da `sanzioni-conformita.md`)

- [ ] PSC NON è copia-incolla di documento precedente (ogni sezione è specifica)
- [ ] Data di redazione PSC è PRECEDENTE alla data di inizio lavori
- [ ] PSC è stato consegnato all'impresa affidataria con RICEVUTA SCRITTA
- [ ] PSC versione aggiornata se le lavorazioni sono cambiate
- [ ] Verbali di sopralluogo CSE per ogni visita (con firma dell'impresa)
- [ ] Riunioni di coordinamento documentate con verbale scritto

### Checklist warning giurisprudenziali inseriti

- [ ] H.1 — PSC non standardizzato (Cap. 1, Cap. 7) — **OBBLIGATORIO**
- [ ] H.2 — Sospensione lavori (Cap. 3.2, Cap. 19) — **OBBLIGATORIO**
- [ ] H.3 — Verifica POS (Cap. 5) — **OBBLIGATORIO**
- [ ] H.4 — Alta vigilanza concreta (Cap. 3.2) — **OBBLIGATORIO**
- [ ] H.5 — Aggiornamento PSC (Cap. 3.1) — **OBBLIGATORIO**
- [ ] H.6 — Rischio interferenziale (Cap. 9.4, Cap. 18.3) — SE ≥ 2 imprese
- [ ] H.7 — DPC prima di DPI (Cap. 12, Cap. 15.1) — SE lavori in quota
- [ ] H.8 — Condizioni climatiche (Cap. 15.6, Cap. 19.4) — SE lavorazioni esterne

### Checklist clausole legali inserite

- [ ] Clausola specificità PSC (Cap. 1) — da `responsabilita-penale.md`
- [ ] Tabella posizioni di garanzia (Cap. 1) — da `responsabilita-penale.md`
- [ ] Clausola perimetro vigilanza CSE (Cap. 3.2) — da `responsabilita-penale.md`
- [ ] Clausola perimetro funzioni CSE (Cap. 3.3) — da `tutela-patrimoniale-cse.md`
- [ ] Clausola aggiornamento PSC con obbligo comunicazione scritta (Cap. 3.1) — da `tutela-patrimoniale-cse.md`
- [ ] Clausola informazioni fornite dal committente (Cap. 6) — da `tutela-patrimoniale-cse.md`
- [ ] Sezione 5.4 Obblighi contrattuali sicurezza — da `contratti-appalto.md`
- [ ] Sezione 5.5 Clausole contrattuali (costi, idoneità, RC, subappalto) — da `contratti-appalto.md`
- [ ] Garanti per ogni rischio critico (Cap. 15) — da `responsabilita-penale.md`

### 🔒 Archivio difensivo minimo (Tab. E.1 da `tutela-patrimoniale-cse.md`)

> **Segnalare all'utente al termine della consegna del PSC:**
>
> | Documento | Modalità | Conservazione |
> |-----------|----------|--------------|
> | Contratto di incarico firmato | Originale + PDF | 20 anni |
> | PSC e tutte le revisioni (con data) | PDF + backup cloud | 20 anni |
> | Notifica Preliminare (ricevuta) | PDF | 10 anni |
> | POS di ogni impresa (con data ricezione) | PDF | 10 anni |
> | Verbali sopralluogo CSE (firmati) | Originale + PDF | 20 anni |
> | Verbali riunioni coordinamento | Originale + PDF | 10 anni |
> | Segnalazioni inadempienze al committente | Email/PEC + ricevuta | 20 anni |
> | Comunicazioni imprese (in/out) | Email/PEC | 10 anni |
> | Polizza RC in vigore (ogni annualità) | PDF | Vita intera + 10 anni |
