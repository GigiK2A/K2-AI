# FORMAT PSC B40 — Modifica Impianto SRB Roof Top Esistente — Template Completo con Integrazione Legale

> **ISTRUZIONI PER L'USO**: Questo file contiene la struttura esatta e il testo standard di ogni sezione del PSC B40 per cantieri di **modifica/adeguamento di impianto SRB esistente su Roof Top** (aggiunta RRH, combiner, moduli, cavi su palina e quadro esistenti — NO nuova struttura, NO baggioli, NO fondazioni). Per ogni nuovo PSC:
> 1. Copia l'intera struttura
> 2. Sostituisci tutti i placeholder `[PLACEHOLDER]` con i dati del sito specifico
> 3. Adatta i rischi e le schede fase lavorativa al tipo di intervento (UP5G / Adeguamento / Integrazione apparati)
> 4. Le sezioni marcate con 🔒 LEGALE contengono clausole difensive obbligatorie — NON rimuoverle mai
> 5. Le sezioni marcate con ⚠ AVVERTENZA H.x contengono warning giurisprudenziali Cassazione Penale — NON rimuoverle mai
> 6. Esegui le checklist F.1 e F.3 (in fondo al documento) prima della consegna
>
> **VARIANTE**: Questo format è specifico per **modifiche su SRB Roof Top esistente** (palina, quadro, cavidotti già presenti — intervento limitato ad aggiunta apparati, cavi, interruttori). Per nuovi siti Roof Top con struttura da realizzare usare `format-psc-k2a-rooftop.md`. Per cantieri civili/residenziali usare `format-psc-evo-appartamento.md`.
>
> **DIFFERENZE CHIAVE rispetto a K2A Roof Top (nuovo sito)**:
> - 7 fasi (L.01–L.07) anziché 12 — niente baggioli, montaggio palina, fibra, CEM post-attivazione
> - No autogrù / PLE (materiali portati a mano o con paranco su palina esistente)
> - Durata breve: tipicamente 5 giorni, 2 operatori
> - Singola impresa (Circet), senza subappalti nella configurazione standard
> - Rischi calibrati su lavorazioni in quota su palina esistente e quadro DC -48V
> - 8 rischi principali (15.1–15.8) anziché 9

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
> **B. CARTELLONISTICA** — Nel format B40, la segnaletica è integrata nel Cap. 9.5 con immagini fisse (non tavola separata):
> - Cartelli di PRESCRIZIONE (M — Fondo Blu)
> - Cartelli di PERICOLO (W — Fondo Giallo)
> - Cartelli di DIVIETO (P — Fondo Bianco/Rosso)
> - Cartelli di EVACUAZIONE (E — Fondo Verde) e ANTINCENDIO (F — Fondo Rosso)
> - Immagini fisse ISO 7010 dal template — NON sostituire
>
> **C. WARNING, NOTE e CLAUSOLE LEGALI** — Formato "box singola cella":
> - Avvertenze (⚠ H.x): tabella 1×1, sfondo `#FFF5F5`, testo 9pt, codice in bold rosso `#C00000`
> - Note (📌): tabella 1×1, sfondo `#F0F9FF`, testo 9pt
> - Clausole legali (🔒): tabella 1×1, sfondo `#EBF5FB`, titolo bold blu `#1F4E79`
>
> **D. ORGANIGRAMMA** — Formato "tabella grafica colorata":
> - Tabella 6 righe × 4 colonne (senza riga subappalto nella config. standard)
> - Colori: `#1F4E79` (CSE, intestazione), `#2E75B6` (Committente), `#C00000` (Impresa appaltatrice)
> - Sfondo box: `#FFF2CC` (Committente/Iliad), `#FFEB9C` (Affidataria/Circet), `#BDD7EE` (CSE)
>
> **E. SOTTOSCRIZIONI** — Formato "griglia 2×2":
> - Tabella 2 righe × 2 colonne (CSE | Committente / Affidataria | Subappaltatrice)
> - Con emoji ruolo (🛡, 🏢, 🏗, 🔧)
>
> **F. ALLEGATI** — Devono essere SVILUPPATI in calce al documento, non solo elencati:
> - Allegato 1: tabella lavorazioni (7+1 righe × 5 col)
> - Allegato 2: cronoprogramma Gantt testuale (celle colorate, mezze giornate)
> - Allegato 3: layout planimetrico (descrizione elementi in copertura)
> - Allegato 4: Fascicolo dell'Opera (3 Schede: I descrizione, II rischi manutenzione, III documentazione)
> - Allegato 5: check-list macchine compilabile (7×6 caselle ☐ Sì ☐ No)
> - Allegato 6: calcolo uomini-giorno in tabella (7+1 righe × 4 col)
> - Allegato 7: modulo near miss compilabile (12×2)
>
> **G. GESTIONE IMMAGINI**:
>
> **IMMAGINI FISSE (da template — NON sostituire mai):**
> - Segnaletica PRESCRIZIONE ISO 7010 (Cap. 9.5)
> - Segnaletica PERICOLO ISO 7010 (Cap. 9.5)
> - Segnaletica DIVIETO ISO 7010 (Cap. 9.5)
> - Segnaletica EVACUAZIONE/ANTINCENDIO ISO 7010 (Cap. 9.5)
> - Tavola attrezzature e DPI (Cap. 11 e Cap. 12)
> - Tavola DPI antirumore (Cap. 13)
>
> **FOTO SITO (placeholder — da inserire per ogni progetto):**
> - Cap. 6.3: minimo 8 foto ante-operam del sito + planimetria di progetto
> - Layout: **2 foto per pagina**, disposte su 2 colonne affiancate (7 cm ciascuna) in tabella invisibile
> - Planimetria di progetto: larghezza piena (14 cm), celle unite
> - Didascalia sotto ogni foto: Calibri 8pt corsivo
> - Placeholder nel template: `[FOTO DA INSERIRE]` con box grigio chiaro `#F2F2F2`
>
> **H. IMPOSTAZIONI GENERALI DOCX**:
> - Margini: 2.5 cm per tutti i lati
> - Font corpo testo: Calibri 11pt, interlinea 1.15, colore `#333333`
> - Font titoli capitolo (Heading 1): Calibri Bold 14pt, colore blu `#2F5496`
> - Font sottotitoli (Heading 2): Calibri Bold 12pt, colore blu `#2F5496`
> - Font tabelle: Calibri 9pt
> - Piè di pagina: "PSC — [CODICE_SITO] [NOME_SITO] — [NOME_STUDIO] — [NOME_CSE]", centrato, Calibri 7pt grigio `#808080`
> - Interruzione di pagina: prima di ogni capitolo principale (1–22) e prima degli allegati
> - **Stile tabella**: "Normal Table" con bordi aggiunti via XML (non "Table Grid")

---

## STRUTTURA DOCUMENTO — 22 CAPITOLI + 7 ALLEGATI

```
FRONTESPIZIO (T0 — 21×2)
⚠ BOX H.1 (T1 — 1×1)
🔒 BOX LEGALE SPECIFICITÀ PSC (T2 — 1×1)
SOMMARIO (se previsto)
CAPITOLO 1 — PREMESSA E QUADRO NORMATIVO
  1.1 Quadro normativo di riferimento (T3 — 12×2)
  1.2 Posizioni di garanzia (T4 — 6×3)
CAPITOLO 2 — ANAGRAFICA DEL CANTIERE (T5 — 23×2)
CAPITOLO 3 — GESTIONE DEL PSC E ATTIVITÀ DEL CSE
  3.1 Revisione del piano
  ⚠ BOX H.5 (T6 — 1×1)
  🔒 CLAUSOLA AGGIORNAMENTO PSC (T7 — 1×1)
  3.2 Attività di coordinamento del CSE
  ⚠ BOX H.4 (T8 — 1×1)
  ⚠ BOX H.2 (T9 — 1×1)
  🔒 CLAUSOLA PERIMETRO VIGILANZA CSE (T10 — 1×1)
  3.3 Perimetro delle funzioni del CSE
  🔒 BOX PERIMETRO FUNZIONI CSE (T11 — 1×1)
  ⚠ BOX H.3 (T12 — 1×1)
  3.4 Consultazione RLS
  3.5 Riunione di coordinamento
CAPITOLO 4 — NOTIFICA PRELIMINARE
CAPITOLO 5 — DISPOSIZIONI PER LE IMPRESE
  5.1 Obblighi delle imprese
  5.2 Patente a crediti e badge digitale
  5.3 Contenuti minimi del POS
  5.4 Obblighi contrattuali di sicurezza
  🔒 CLAUSOLE CONTRATTUALI (T13 — 1×1)
  🔒 CLAUSOLE APPLICABILI (T14 — 1×1)
CAPITOLO 6 — DESCRIZIONE DELL'OPERA
  🔒 BOX INFORMAZIONI COMMITTENTE (T15 — 1×1)
  6.1 Inquadramento territoriale
  6.2 Descrizione dell'intervento
  6.3 Rilievo fotografico ante-operam (T16–T23 — foto 2 per pagina)
CAPITOLO 7 — AREA DI LAVORO
  ⚠ BOX H.1 (T24 — 1×1)
  7.1 Zone operative (T25 — 8×3)
CAPITOLO 8 — RISCHI INTRINSECI E FATTORI ESTERNI
  8.1 Caratteristiche del sito
  8.2 Fattori esterni (T26 — 7×3)
CAPITOLO 9 — ORGANIZZAZIONE DEL CANTIERE
  9.1 Recinzione, accessi, segnalazioni
  9.2 Impianti di cantiere
  9.3 Aree di stoccaggio
  9.4 Coordinamento lavorazioni
  ⚠ BOX H.6 INTERFERENZIALE (T27 — 1×1)
  9.5 Segnaletica (con immagini fisse ISO 7010: T28–T31)
CAPITOLO 10 — SOSTANZE PERICOLOSE PRESENTI
CAPITOLO 11 — ATTREZZATURE, MACCHINE E IMPIANTI (T32 — 6×4)
CAPITOLO 12 — DPI (T33 — 1×1 H.7 + T34 — 11×5)
CAPITOLO 13 — VALUTAZIONE DEL RUMORE (T35 — 5×3)
CAPITOLO 14 — SORVEGLIANZA SANITARIA
CAPITOLO 15 — RISCHI PRINCIPALI — ANALISI E PREVENZIONE
  🔒 BOX GARANTI RISCHIO CRITICO (T36 — 1×1)
  ⚠ BOX H.7 DPC > DPI (T37 — 1×1)
  15.1 Caduta dall'alto (T38 — 1×5, R=9)
  15.2 Caduta di materiale dall'alto (T39 — 1×5, R=9)
  15.3 Elettrocuzione (T40 — 1×5, R=6)
  15.4 Radiazioni non ionizzanti — CEM (T41 — 1×5)
  15.5 Movimentazione manuale carichi (T42 — 1×5, R=4)
  ⚠ BOX H.8 MICROCLIMA (T43 — 1×1)
  15.6 Microclima sfavorevole (T44 — 1×5, R=4)
  15.7 Scivolamento su copertura (T45 — 1×5, R=4)
  15.8 Caduta dal bordo della copertura (T47 — 1×5)
  DIAGRAMMA GANTT CAP. 16 (T46 — 9×7, inserito dopo 15.7)
CAPITOLO 16 — PROGRAMMA DEI LAVORI — CRONOPROGRAMMA
CAPITOLO 17 — ANALISI GENERALE DEI RISCHI — METODOLOGIA (T48 — 8×5 fasi + T49 — 4×4 matrice)
CAPITOLO 18 — INDIVIDUAZIONE, ANALISI E VALUTAZIONE DEI RISCHI
  18.1 Rischi generali comuni a tutte le fasi
  18.2 Schede fasi lavorative (T50–T55 — 6 schede 7×2)
  18.3 Interferenze critiche (T56 — 1×1 H.2 + T57 — 17×2)
CAPITOLO 19 — GESTIONE DELLE EMERGENZE
  19.1 Presidi sanitari
  19.2 Procedura — Caduta dall'alto
  19.3 Procedura — Elettrocuzione DC -48V
  19.4 Antincendio
  19.5 Condizioni meteorologiche avverse
CAPITOLO 20 — STIMA COSTI SICUREZZA (T58 — 6×5)
CAPITOLO 21 — DOCUMENTI DA TENERE IN CANTIERE (T59 — 18×2)
CAPITOLO 22 — ALLEGATI (T60 — 8×2)
SOTTOSCRIZIONI (T61 — 2×2)
─── ALLEGATI SVILUPPATI ───
ALLEGATO 1 — ELENCO LAVORAZIONI (T62 — 8×5)
ALLEGATO 2 — CRONOPROGRAMMA GANTT (T63 — 9×12)
ALLEGATO 3 — LAYOUT PLANIMETRICO (T64 — 10×3)
ALLEGATO 4 — FASCICOLO DELL'OPERA
  Scheda I  — Descrizione (T65 — 10×2)
  Scheda II — Rischi manutenzione (T66 — 6×5)
  Scheda III — Documentazione (T67 — 8×2)
ALLEGATO 5 — CHECK-LIST MACCHINE (T68 — 8×6)
ALLEGATO 6 — CALCOLO UOMINI-GIORNO (T69 — 9×4)
ALLEGATO 7 — MODULO NEAR MISS (T70 — 13×2)
```

---

## FRONTESPIZIO

```
──────────────────────────────────────────────────
STUDIO ASSOCIATO EVOLUTION | Piano di Sicurezza e Coordinamento
──────────────────────────────────────────────────

PIANO DI SICUREZZA E COORDINAMENTO
(art. 100, D.Lgs. 81/2008 e s.m.i. — Allegato XV)

STAZIONE RADIO BASE ILIAD ITALIA S.p.A.

┌──────────────────────────┬──────────────────────────────────────┐
│ COMMITTENTE              │ Iliad Italia S.p.A.                  │
│ IMPRESA AFFIDATARIA      │ Circet Italia S.p.A.                 │
│ Codice Sito              │ [CODICE_SITO]                        │
│ Nome Sito                │ «[NOME_SITO]»                        │
│ Tipologia                │ Roof Top — Modifica impianto esistente│
│ Tecnologie               │ [TECNOLOGIE]                         │
│ Indirizzo                │ [INDIRIZZO] — [CAP] [COMUNE] ([PROV])│
│ Coordinate               │ Lat [LAT]° N — Long [LONG]° E        │
│ Progetto Esecutivo       │ PE Rif. [RIF_PE] — Rev. [REV_PE]     │
│ Intervento               │ [DESCRIZIONE_BREVE_INTERVENTO]       │
│ Struttura portante       │ Palina h [ALTEZZA_PALINA] m su [SUPPORTO]│
│ Quota lastrico           │ [QUOTA_LASTRICO] m s.l.m.            │
│ Quota max impianto       │ [QUOTA_MAX] m s.l.m.                 │
│ N° imprese               │ [N_IMPRESE]                          │
│ N° max lavoratori        │ [N_MAX_LAV]                          │
│ Durata presunta          │ ~[DURATA_GG] giorni lavorativi       │
│ Entità presunta          │ [UOMINI_GIORNO] uomini/giorno       │
│ Data inizio lavori       │ ✏ DA COMPILARE                      │
│ Rev. PSC                 │ 00 — Emissione del [DATA_EMISSIONE]  │
│ CSP / CSE                │ [NOME_CSE] — Ordine [CAT] [PROV] n. [N_ORDINE]│
│ Studio                   │ [NOME_STUDIO] — [INDIRIZZO_STUDIO]   │
└──────────────────────────┴──────────────────────────────────────┘
```

**Tabella T0**: 21 righe × 2 colonne. Colonna 0 = etichetta (bold, sfondo `#2F5496`, testo bianco). Colonna 1 = valore.

---

## ⚠ BOX H.1 (T1 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.1
Cass. Pen., Sez. IV, n. 7421/2026: il PSC deve essere specifico e calibrato sulle reali
criticità del cantiere in oggetto. Un PSC generico e standardizzato, non aderente alle
reali criticità del sito, equivale a una totale omissione ai fini della colpa penale.
```

---

## 🔒 BOX LEGALE — SPECIFICITÀ PSC (T2 — 1×1, sfondo `#EBF5FB`)

```
🔒 CLAUSOLA LEGALE — Specificità del PSC (Cap. 1)
Il presente PSC è stato elaborato con specifico riferimento al cantiere del sito
[CODICE_SITO] «[NOME_SITO]» e alle sue criticità peculiari: lavori in quota su palina
esistente a quota [QUOTA_MAX] m, rischio elettrico DC -48V, accesso in copertura,
microclima. Ogni sezione è calibrata sulle condizioni effettive del cantiere.
```

---

## CAPITOLO 1 — PREMESSA E QUADRO NORMATIVO

📋 *Riferimenti: art. 100 D.Lgs. 81/2008 e s.m.i. — Allegato XV*

```
Il presente Piano di Sicurezza e Coordinamento (PSC) è redatto ai sensi dell'art. 100
del D.Lgs. 81/2008 e s.m.i. e dell'Allegato XV, in conformità al D.Lgs. 106/2009 e alla
normativa vigente, per il cantiere di modifica dell'impianto di radiotelecomunicazioni
Iliad Italia S.p.A. — Sito [CODICE_SITO] «[NOME_SITO]» — Roof Top nel Comune di
[COMUNE] ([SIGLA_PROV]).

Il PSC è elaborato dal Coordinatore per la Sicurezza in fase di Progettazione (CSP),
[NOME_CSE], che assume altresì le funzioni di Coordinatore per la Sicurezza in fase di
Esecuzione (CSE).
```

### 1.1 Quadro normativo di riferimento (T3 — 12×2)

| Norma | Oggetto |
|-------|---------|
| D.Lgs. 81/2008 e s.m.i. | Testo Unico Sicurezza sul Lavoro |
| D.Lgs. 106/2009 | Disposizioni integrative e correttive al D.Lgs. 81/2008 |
| D.P.R. 380/2001 | Testo Unico Edilizia |
| D.Lgs. 259/2003 | Codice delle Comunicazioni Elettroniche |
| D.M. 37/2008 | Impianti all'interno degli edifici |
| D.L. 159/2025 conv. L. 198/2025 | Patente a crediti e badge digitale |
| Circ. INL n. 1/2026 | Indicazioni operative patente a crediti |
| NTC 2018 (D.M. 17/01/2018) | Norme Tecniche per le Costruzioni |
| Circ. n. 7/2019 | Istruzioni applicative NTC 2018 |
| D.P.R. 462/2001 | Verifiche impianti di messa a terra |
| D.M. 388/2003 | Pronto soccorso aziendale |
| Reg. UE 2016/425 | DPI — Regolamento dispositivi di protezione individuale |

### 1.2 Posizioni di garanzia (T4 — 6×3)

| Soggetto | Posizione di garanzia | Riferimento |
|----------|----------------------|-------------|
| Committente (Iliad Italia S.p.A.) | Designazione CSP/CSE, verifica idoneità imprese, Notifica Preliminare | Art. 90 D.Lgs. 81/08 |
| CSP ([NOME_CSE]) | Redazione PSC conforme All. XV, Fascicolo Opera | Art. 91 D.Lgs. 81/08 |
| CSE ([NOME_CSE]) | Vigilanza concreta PSC/POS, coordinamento imprese, sospensione pericolo grave | Art. 92 D.Lgs. 81/08 |
| DL Impresa affidataria (Circet) | POS, rispetto PSC, DPI, formazione | Art. 96-97 D.Lgs. 81/08 |
| DL Impresa subappaltatrice | POS specifico, coordinamento con affidataria | Art. 96-97 D.Lgs. 81/08 |

---

## CAPITOLO 2 — ANAGRAFICA DEL CANTIERE

📋 *Riferimenti: punto 2.1.2, lettera a, punto 1, Allegato XV D.Lgs. 81/2008*

### Tabella anagrafica (T5 — 23×2)

```
Contiene i seguenti campi (23 righe × 2 colonne, intestazione blu #2F5496):

SEZIONE OPERA:
- Natura dell'opera: Civile / Impiantistica TLC
- Oggetto: PSC art. 100 D.Lgs. 81/08 — [CODICE_SITO] [NOME_SITO] — Modifica impianto SRB Roof Top
- Titolo abilitativo: ✏ DA COMPILARE
- Importo presunto: € [IMPORTO]
- N° imprese: [N_IMPRESE]
- N° max lavoratori: [N_MAX_LAV]
- Entità presunta: [UOMINI_GIORNO] uomini/giorno
- Data inizio lavori: ✏ DA COMPILARE
- Durata presunta: ~[DURATA_GG] giorni lavorativi

SEZIONE SOGGETTI:
- Committente: Iliad Italia S.p.A. — Viale F. Rastelli n.1/A, 20124 Milano
- CSP e CSE: [NOME_CSE] — [NOME_STUDIO] — [INDIRIZZO_STUDIO]
- Impresa affidataria: Circet Italia S.p.A. — Via Aterno 108, San Giovanni Teatino (CH)
- Subappaltatore: [NOME_SUB] oppure "Non previsti"

SEZIONE NUMERI UTILI:
- 112, 118, 115
- Ospedale più vicino: ✏ DA COMPILARE
- ASL: ✏ DA COMPILARE
- CSE: [TEL_CSE]
- Capocantiere Circet: ✏ DA COMPILARE
- Referente Iliad: ✏ DA COMPILARE
```

---

## CAPITOLO 3 — GESTIONE DEL PSC E ATTIVITÀ DEL CSE

📋 *Riferimenti: artt. 92, 93 D.Lgs. 81/2008 e s.m.i.*

### 3.1 Revisione del piano

```
Il presente PSC è un documento dinamico. In caso di varianti in corso d'opera, modifiche
organizzative, introduzione di nuove tecnologie o macchine non previste, o qualsiasi modifica
che alteri il profilo di rischio, il CSE procederà all'aggiornamento tempestivo del PSC prima
dell'inizio delle nuove attività (art. 92, co. 1, lett. a, D.Lgs. 81/08).
```

### ⚠ BOX H.5 (T6 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.5 — Cass. Pen., Sez. IV, n. 24617/2025: la mancata tempestività
nell'aggiornamento del PSC a fronte di varianti che modificano il profilo di rischio configura
responsabilità penale del CSE. L'aggiornamento deve precedere l'inizio delle nuove attività.
```

### 🔒 LEGALE — Clausola aggiornamento PSC (T7 — 1×1, sfondo `#EBF5FB`)

> Il presente PSC deve essere aggiornato a cura del CSE ogni qualvolta le condizioni di cantiere varino. Il committente/RdL è tenuto a comunicare tali variazioni per iscritto al CSE con congruo anticipo (minimo 5 giorni lavorativi). In assenza di comunicazione, il PSC si intende aggiornato alle sole informazioni disponibili alla data dell'ultima revisione.

### 3.2 Attività di coordinamento del CSE

```
L'attività di coordinamento del CSE comporta un obbligo di vigilanza concreto e sostanziale,
non limitato al controllo formale della documentazione. Il CSE verificherà personalmente, con
sopralluoghi di frequenza adeguata alla complessità delle lavorazioni in corso, che le previsioni
del presente PSC siano effettivamente attuate.
```

### ⚠ BOX H.4 (T8 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.4 — Cass. Pen., Sez. IV, n. 24617/2025; n. 6272/2025: il CSE è tenuto a una
vigilanza concreta e non meramente formale. In caso di pericolo grave e imminente il CSE
dispone immediatamente la sospensione delle lavorazioni ai sensi dell'art. 92, co. 1, lett. f).
```

### ⚠ BOX H.2 (T9 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.2 — Cass. Pen., Sez. IV, n. 7414/2024: il potere-dovere di sospensione è
correlato a qualsiasi ipotesi di pericolo grave, a prescindere dalla verifica di specifiche
violazioni normative o del rischio interferenziale.
```

### 🔒 CLAUSOLA PERIMETRO VIGILANZA CSE (T10 — 1×1, sfondo `#EBF5FB`)

> Il Coordinatore per la Sicurezza in fase di Esecuzione esercita le funzioni di alta vigilanza previste dall'art. 92 D.Lgs. 81/2008. I poteri del CSE non sostituiscono gli obblighi di vigilanza del datore di lavoro dell'impresa esecutrice.

### 3.3 Perimetro delle funzioni del CSE

### 🔒 BOX PERIMETRO FUNZIONI CSE (T11 — 1×1, sfondo `#EBF5FB`)

```
🔒 Perimetro di garanzia CSE
Il CSE esercita funzioni di alta vigilanza (non sostituisce il datore di lavoro dell'impresa).
I poteri sono: adeguamento PSC, verifica POS, riunioni coordinamento, sospensione lavori per
pericolo grave. La responsabilità per l'attuazione delle misure ricade sull'impresa esecutrice
(art. 96 D.Lgs. 81/2008).
```

### ⚠ BOX H.3 (T12 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.3 — Cass. Pen. Sez. IV, n. 2845/2021; n. 4813: il CSE è tenuto alla verifica
sostanziale dell'idoneità del POS. L'accettazione di un POS generico configura concorso di
colpa del CSE in caso di infortunio.
```

### 3.4 Consultazione RLS

```
Prima dell'accettazione del PSC, il datore di lavoro di ciascuna impresa esecutrice consulta
il RLS e gli fornisce eventuali chiarimenti. La consultazione viene verbalizzata.
```

### 3.5 Riunione di coordinamento

```
Prima dell'inizio dei lavori il CSE convoca una riunione di coordinamento con i datori di lavoro
delle imprese esecutrici e i RLS. O.d.G.: illustrazione PSC, pianificazione interferenze,
assegnazione responsabilità DPI, verifica documenti. Cadenza successive: settimanale o al bisogno.
```

---

## CAPITOLO 4 — NOTIFICA PRELIMINARE

📋 *Riferimenti: art. 99 D.Lgs. 81/2008 e s.m.i.*

```
Il committente (Iliad Italia S.p.A.) o il Responsabile dei Lavori, prima dell'inizio dei lavori,
trasmette la Notifica Preliminare all'ASL e alla Direzione Provinciale del Lavoro competenti,
ai sensi dell'art. 99 D.Lgs. 81/2008.

Numero protocollo Notifica Preliminare e data invio: ✏ DA COMPILARE.
Copia firmata della Notifica Preliminare va affissa in cantiere per tutta la durata dei lavori.
```

---

## CAPITOLO 5 — DISPOSIZIONI PER LE IMPRESE

📋 *Riferimenti: punto 2.1.2, lettera b, Allegato XV D.Lgs. 81/2008*

### 5.1 Obblighi delle imprese

```
Prima dell'inizio dei lavori, l'impresa affidataria Circet Italia S.p.A. trasmette il proprio
POS al CSE che ne verificherà l'idoneità sostanziale, non meramente documentale.
```

### 5.2 Patente a crediti e badge digitale

```
Ai sensi dell'art. 27 D.Lgs. 81/08 come novellato dal D.L. 159/2025 (conv. L. 198/2025),
tutte le imprese e i lavoratori autonomi operanti in cantiere devono essere titolari della
patente a crediti con punteggio minimo di 15/30. È vietato l'accesso al cantiere a lavoratori
privi di patente a crediti valida.

Ogni lavoratore deve essere munito di tessera di riconoscimento digitale (badge) contenente:
fotografia, dati anagrafici, codice fiscale, qualifica, data di assunzione, datore di lavoro.
```

### 5.3 Contenuti minimi del POS

```
Il POS deve contenere almeno (Allegato XV D.Lgs. 81/08): dati identificativi dell'impresa;
nominativi addetti emergenza/primo soccorso; elenco lavoratori con qualifica e formazione;
descrizione lavorazioni; analisi rischi specifici; elenco DPI con dichiarazione di consegna;
procedure lavori in quota con punti di ancoraggio; piano di manutenzione attrezzature;
attestati di formazione.
```

### 🔒 LEGALE — 5.4 Obblighi contrattuali (T13 — 1×1, sfondo `#EBF5FB`)

```
Tutte le imprese sono tenute a:
a) Trasmettere al CSE il POS almeno 10 giorni prima dell'inizio delle proprie lavorazioni;
b) Non iniziare alcuna lavorazione prima della verifica di idoneità del POS;
c) Comunicare al CSE ogni variazione delle squadre, attrezzature o modalità operative;
d) Partecipare alle riunioni di coordinamento;
e) Designare un referente di cantiere reperibile durante l'orario di lavoro;
f) Rispettare le procedure di emergenza del Cap. 19;
g) Affiggere copia del PSC e del POS all'ingresso del cantiere.
```

### 🔒 LEGALE — 5.5 Clausole contrattuali applicabili (T14 — 1×1, sfondo `#EBF5FB`)

> **Costi della sicurezza**: € [COSTI_SICUREZZA], NON soggetti a ribasso d'asta (art. 26 co. 5 + All. XV pt. 4).
> **Idoneità tecnico-professionale**: L'appaltatore dichiara i requisiti ex art. 26 co. 1 + All. XVII.
> **RC obbligatoria**: Polizza RC verso terzi e lavoratori, massimale ≥ € 500.000/sinistro.
> **Sub-appalto**: consentito previa comunicazione scritta e approvazione CSE.

---

## CAPITOLO 6 — DESCRIZIONE DELL'OPERA

📋 *Riferimenti: punto 2.1.2, lettera a, punti 2-3, Allegato XV D.Lgs. 81/2008*

### 🔒 CLAUSOLA INFORMAZIONI COMMITTENTE (T15 — 1×1, sfondo `#EBF5FB`)

> Le informazioni riportate nella presente sezione sono state fornite dal committente/RdL e/o estratte dalla documentazione progettuale. Il CSP non risponde per l'inesattezza di tali informazioni, salvo che fossero rilevabili con la normale diligenza professionale.

### 6.1 Inquadramento territoriale

```
La Stazione Radio Base Iliad Italia S.p.A. codice sito [CODICE_SITO] «[NOME_SITO]» è ubicata
nel Comune di [COMUNE] ([SIGLA_PROV]), Regione [REGIONE], Municipio/Circoscrizione [MUNICIPIO].
Il sito è di tipo Roof Top, su copertura dell'edificio sito in [INDIRIZZO_CANTIERE].

L'edificio è [DESCRIZIONE_EDIFICIO: es. fabbricato residenziale di N piani f.t., struttura
in c.a., copertura piana praticabile a quota [QUOTA_LASTRICO] m s.l.m.].

Il contesto è caratterizzato da: [DESCRIZIONE_CONTESTO: zona residenziale/mista, strade
principali, distanze da edifici adiacenti].
```

### 6.2 Descrizione dell'intervento

```
Il presente PSC riguarda l'intervento di modifica dell'impianto radio esistente sul sito
[CODICE_SITO] «[NOME_SITO]». Il sito è classificato come Roof Top, con palina h [ALTEZZA_PALINA] m
su [SUPPORTO: es. basamento/baggioli cls] esistente, a quota massima [QUOTA_MAX] m s.l.m.

L'intervento prevede le seguenti lavorazioni:
1. Installazione di n. [N_RRH] moduli RRH (Remote Radio Head) [POSIZIONE_es: dietro le antenne
   esistenti sulla palina]
2. Installazione di n. [N_COMBINER] combiner [POSIZIONE]
3. Posa cavi di alimentazione DC -48V dai moduli RRH al quadro elettrico esistente
4. Installazione di n. [N_INTERRUTTORI] interruttori magnetotermici nel quadro DC -48V esistente
5. Posa jumper coassiali dalle antenne ai nuovi moduli RRH
6. Collaudo funzionale e messa in servizio

Tutte le lavorazioni si svolgono sulla copertura dell'edificio e sulla palina esistente. Non
è prevista la realizzazione di nuove strutture portanti, fondazioni o baggioli. L'accesso
avviene tramite [TIPO_ACCESSO: scala interna + porta/botola copertura].

Dati di progetto:
- Quota lastrico: [QUOTA_LASTRICO] m s.l.m.
- Palina: h [ALTEZZA_PALINA] m ([TIPO_PALINA: poligonale/tubolare]), quota max [QUOTA_MAX] m
- Operatori previsti: [N_OPERATORI] contemporanei
- Durata stimata: [DURATA_GG] giorni lavorativi
- Impresa esecutrice: Circet Italia S.p.A.
```

### 6.3 Rilievo fotografico ante-operam

```
Si riporta il rilievo fotografico eseguito nel corso del sopralluogo preliminare del
[DATA_SOPRALLUOGO]. Le foto documentano lo stato dei luoghi ante-operam.
```

**Layout foto**: tabella invisibile 2 colonne, ogni foto 7 cm × auto. 2 per pagina.

```
┌──────────────────────────┬──────────────────────────┐
│  [FOTO DA INSERIRE]      │  [FOTO DA INSERIRE]      │
│  Fig. 6.1 — Vista aerea  │  Fig. 6.2 — Contesto     │
├──────────────────────────┼──────────────────────────┤
│  [FOTO DA INSERIRE]      │  [FOTO DA INSERIRE]      │
│  Fig. 6.3 — Facciata     │  Fig. 6.4 — Ingresso     │
├──────────────────────────┼──────────────────────────┤
│  [FOTO DA INSERIRE]      │  [FOTO DA INSERIRE]      │
│  Fig. 6.5 — Palina e     │  Fig. 6.6 — Dettaglio    │
│       antenne             │       RRH esistenti      │
├──────────────────────────┼──────────────────────────┤
│  [FOTO DA INSERIRE]      │  [FOTO DA INSERIRE]      │
│  Fig. 6.7 — Scala/accesso│  Fig. 6.8 — Area apparati│
├──────────────────────────┴──────────────────────────┤
│       [FOTO DA INSERIRE — PLANIMETRIA DI PROGETTO]  │
│       14 cm × auto (larghezza piena)                │
│  Fig. 6.9 — Planimetria (stato di progetto dal PE)  │
└─────────────────────────────────────────────────────┘
```

**Foto obbligatorie** (minimo 8, adattare al cantiere):
1. Vista aerea/ortofoto edificio con posizionamento SRB
2. Contesto urbano circostante
3. Facciata edificio
4. Ingresso/porta accesso copertura
5. Palina esistente con array antenne
6. Dettaglio apparati esistenti (RRH, parabole, cablaggio)
7. Scala/accesso palina (protezione a gabbia se presente)
8. Area apparati e quadro elettrico
9. Planimetria di progetto (stato di progetto dal PE)

---

## CAPITOLO 7 — AREA DI LAVORO

📋 *Riferimenti: punto 2.1.2, lettera a, Allegato XV D.Lgs. 81/2008*

```
Il cantiere del sito [CODICE_SITO] «[NOME_SITO]» è ubicato sulla copertura
[TIPO_COPERTURA: piana/inclinata] dell'edificio [TIPO_EDIFICIO] sito in [INDIRIZZO],
[COMUNE]. Le lavorazioni si svolgono interamente in copertura e sulla palina esistente.

L'accesso al sito avviene dall'ingresso [condominiale/principale] su [VIA], attraverso le
scale interne fino al lastrico solare. Non è previsto stazionamento di mezzi pesanti al
piano strada. I materiali vengono trasportati a mano fino alla copertura.
```

### ⚠ BOX H.1 specifico sito (T24 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.1
Il presente PSC è specifico per il sito [CODICE_SITO]: le caratteristiche del sito, i
rischi individuati e le misure prescritte sono calibrate sulle condizioni effettive
verificate nel sopralluogo del [DATA_SOPRALLUOGO].
```

### 7.1 Descrizione delle zone operative (T25 — 8×3)

| Zona | Descrizione | Prescrizioni |
|------|-------------|-------------|
| **A — Copertura** | Lastrico solare a quota [QUOTA_LASTRICO] m. Superficie utile ≈ [SUPERFICIE] mq | Accesso solo autorizzati con DPI; muretto perimetrale h [ALTEZZA_MURETTO] cm |
| **A1 — Punto installazione** | Area palina esistente h [ALTEZZA_PALINA] m: installazione RRH e combiner | Lavoro in quota con imbracatura EN 361; lavoro in coppia obbligatorio |
| **A2 — Percorso cavi** | Tragitto dalla palina al quadro elettrico per posa cavi DC -48V | Cavi fissati con fascette lungo percorso; no cavi volanti |
| **B — Accesso/scala** | Scala interna edificio + porta/botola copertura | Illuminazione adeguata; segnaletica M003, M004 |
| **C — Deposito temporaneo** | Area apparati/shelter per stoccaggio temporaneo materiali | Materiali lontano dal bordo copertura |
| **D — Quadro elettrico** | Posizione quadro DC -48V esistente | Sezionamento con lucchetto; segnaletica W008 |
| **E — Bordo copertura** | Perimetro del lastrico con muretto h [ALTEZZA_MURETTO] cm | Se muretto < 100 cm: parapetto provvisorio EN 13374 |

---

## CAPITOLO 8 — RISCHI INTRINSECI E FATTORI ESTERNI

📋 *Riferimenti: punto 2.2.1, Allegato XV D.Lgs. 81/2008*

### 8.1 Caratteristiche del sito

```
Trattandosi di intervento su Roof Top (copertura di edificio esistente), non si rilevano
rischi di natura idrogeologica. La copertura è [TIPO: piana e praticabile / inclinata], con
guaina impermeabilizzante [STATO: in buono/discreto/cattivo stato]. [NOTA_STRUTTURALE:
es. portata solaio verificata nel PE].
```

### 8.2 Fattori esterni (T26 — 7×3)

| Fattore esterno | Presenza | Misure preventive |
|-----------------|----------|-------------------|
| Linee elettriche aeree | ✏ Verificare | Distanza min. 5 m; segnalare |
| SRB adiacenti attivi (altri operatori) | ✏ Verificare — [OPERATORI] | Misura CEM preventiva; segnaletica W005 |
| Vento — zona [ZONA_VENTO] | SÌ | Anemometro; sospensione lavori quota con v > 6 m/s |
| Edifici residenziali adiacenti | ✏ Verificare | Zona caduta; informativa condomini |
| Traffico veicolare | ✏ Verificare | Segnaletica stradale se necessaria |
| Condizioni meteo estreme | SÌ — [DESCRIZIONE] | Monitoraggio previsioni; sospensione per temporali/gelo |

---

## CAPITOLO 9 — ORGANIZZAZIONE DEL CANTIERE

📋 *Riferimenti: punto 2.1.2, lettera c, Allegato XV D.Lgs. 81/2008 — punto 2.2.2*

### 9.1 Recinzione, accessi, segnalazioni

```
L'area di cantiere è confinata al lastrico solare dell'edificio, accessibile esclusivamente
tramite la scala interna condominiale e la porta/botola di accesso al lastrico. L'accesso è
controllato tramite lucchetto/serratura. Segnaletica di cantiere all'ingresso del vano scala
e in copertura: P006 (vietato accesso non autorizzati), M003 (elmetto), M004 (scarpe S3),
M015 (imbracatura).
```

### 9.2 Impianti di cantiere

```
IMPIANTO ELETTRICO: L'alimentazione di cantiere sarà prelevata dal quadro elettrico esistente
del sito, dotato di interruttore generale, differenziale 30 mA e sezionatori per circuiti.
Dichiarazione di conformità D.M. 37/2008. Messa a terra secondo DPR 462/2001.
```

### 9.3 Aree di stoccaggio

```
I materiali ([ELENCO_MATERIALI: moduli RRH, combiner, cavi, interruttori]) saranno stoccati
nell'area apparati del lastrico solare, lontano dal bordo della copertura e dalla zona di
lavoro attiva. Rifiuti e materiali dismessi in appositi contenitori (D.Lgs. 152/2006).
```

### 9.4 Coordinamento lavorazioni

```
Il cantiere prevede la presenza di n. [N_IMPRESE] impresa/e esecutrice/i: [ELENCO_IMPRESE].
[SE 1 SOLA IMPRESA]: Il rischio interferenziale tra imprese diverse è escluso. Permane il
rischio interferenziale interno tra fasi lavorative diverse della stessa impresa, gestito
attraverso la sequenzialità delle fasi (cfr. cronoprogramma Cap. 16).
```

### ⚠ BOX H.6 INTERFERENZIALE (T27 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.6 — Cass. Pen. n. 23725/2023; n. 37214/2024: benché nel presente cantiere
[sia prevista una sola impresa / siano previste N imprese], il CSE non può ignorare situazioni
di pericolo grave macroscopicamente evidente, anche se riconducibili a rischio specifico
dell'impresa. Il PSC individua e analizza i rischi interferenziali.
```

### 9.5 Segnaletica di sicurezza

📋 *Riferimenti: artt. 161-166 e Allegati XXIV-XXXII D.Lgs. 81/2008 — UNI EN ISO 7010*

> **🖼️ IMMAGINI FISSE** — Per ogni categoria è presente nel template .docx un'immagine dei pittogrammi ISO 7010. Queste immagini sono FISSE e NON vanno sostituite.

**Categorie** (con immagini fisse T28–T31):
- Cartelli di PRESCRIZIONE (M — Fondo Blu): M003, M004, M008, M014, M015
- Cartelli di PERICOLO (W — Fondo Giallo): W005, W008, W024
- Cartelli di DIVIETO (P — Fondo Bianco/Rosso): P006
- Cartelli di EVACUAZIONE (E — Fondo Verde) e ANTINCENDIO (F — Fondo Rosso): E003, E007, F001

```
La segnaletica va mantenuta leggibile per tutta la durata del cantiere. Verifica settimanale
integrità/leggibilità (art. 165 D.Lgs. 81/08).
```

---

## CAPITOLO 10 — SOSTANZE PERICOLOSE PRESENTI

📋 *Riferimenti: artt. 222-226 D.Lgs. 81/2008 — Reg. CE 1272/2008 (CLP)*

```
Le sostanze pericolose che potranno essere impiegate: sigillanti per passanti cavi, prodotti
antiossidanti per connettori RF, grassi dielettrici. SDS in cantiere in italiano.
Quantità limitate al fabbisogno giornaliero. Vietato fumare nelle aree stoccaggio.
```

---

## CAPITOLO 11 — ATTREZZATURE, MACCHINE E IMPIANTI

📋 *Riferimenti: artt. 70-73, 85-88 D.Lgs. 81/2008 — Allegato V*

> **🖼️ IMMAGINE FISSA — TAVOLA ATTREZZATURE**: presente nel template .docx, NON va sostituita.

### Tabella attrezzature B40 (T32 — 6×4)

| Attrezzatura | Utilizzo | Abilitazione | Verifiche |
|---|---|---|---|
| Trapano / Avvitatore a batteria | Fissaggi staffe RRH/combiner, tassellature | Formazione utensili | Integrità connettori; batteria carica |
| Chiave dinamometrica | Serraggio bulloni staffe e connettori RF | — | Taratura verificata |
| Paranco/carrucola | Sollevamento RRH e combiner sulla palina | Formazione | Fune/catena e gancio integri; portata |
| Crimpatrice cavi | Connettorizzazione jumper coassiali | Formazione specifica | Matrici e punzoni corretti |
| Multimetro / Pinza amperometrica | Verifiche circuito DC -48V | PES/PAV CEI 11-27 | Taratura; puntali integri |
| Cassetta attrezzi manuali | Montaggio generale | — | Integrità; isolamento impugnature |

> 📌 Tutte le attrezzature con dichiarazione di conformità CE e manuale in italiano. Verifica giornaliera pre-uso. Non è previsto l'utilizzo di autogrù, PLE o mezzi pesanti.

---

## CAPITOLO 12 — DISPOSITIVI DI PROTEZIONE INDIVIDUALE (DPI)

📋 *Riferimenti: artt. 74-77, 107-108 D.Lgs. 81/2008 — Reg. UE 2016/425*

> **🖼️ IMMAGINE FISSA — TAVOLA DPI**: presente nel template .docx, NON va sostituita.

### ⚠ BOX H.7 (T33 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.7 — Cass. Pen. n. 8083/2019; n. 13590/2020; n. 47015/2022: per tutti i
lavori in quota (h > 2 m), il PSC prescrive in via prioritaria DPC. Solo in via residuale
e motivata si ricorre a DPI anticaduta III categoria. Nel presente cantiere, la scala alla
marinara con protezione a gabbia e la linea vita EN 795 costituiscono i DPC primari.
```

### Tabella DPI B40 (T34 — 11×5)

| DPI | Norma | Cat. | Mansione | Verifica |
|-----|-------|------|----------|----------|
| Elmetto | EN 397 | II | Tutti | Prima uso, mensile |
| Imbracatura anticaduta | EN 361 | III | Lavori in quota > 2 m | Prima ogni uso; annuale |
| Cordino dinamico doppio | EN 355 | III | Salita palina | Prima ogni uso |
| Dispositivo retrattile | EN 360 | III | Bordo copertura | Prima ogni uso |
| Scarpe S3 SRC | EN ISO 20345 | II | Tutti | Mensile |
| Guanti da lavoro | EN 388:2016 | II | Movimentazione materiali | Prima uso |
| Guanti isolanti | IEC 60903 Cl.0 | III | Lavori quadro DC | Prima uso; semestrale |
| Gilet alta visibilità | EN ISO 20471 | II | Tutti | Mensile |
| Occhiali protettivi | EN 166 | II | Forature, tagli | Prima uso |
| Cuffie/tappi antirumore | EN 352-1 | II | Attrezzature rumorose | Prima uso |

---

## CAPITOLO 13 — VALUTAZIONE DEL RUMORE

📋 *Riferimenti: artt. 189-192 D.Lgs. 81/2008*

> **🖼️ IMMAGINE FISSA — TAVOLA DPI ANTIRUMORE**: presente nel template, NON va sostituita.

### Tabella classi (T35 — 5×3)

| Classe | Leq dB(A) | Obblighi |
|--------|-----------|----------|
| I — Sotto soglia | < 80 | Informazione generale |
| II — Tra soglie | 80–85 | Informazione/formazione; DPI disponibili |
| III — Sopra soglia | 85–87 | DPI obbligatori; sorveglianza sanitaria |
| IV — Valore limite | ≥ 87 | Divieto; interventi immediati |

```
Principali sorgenti: trapano/avvitatore a batteria (Leq 75-85 dB(A)), paranco elettrico
(Leq 70-80 dB(A)). DPI antirumore EN 352 per lavorazioni con attrezzature rumorose.
```

---

## CAPITOLO 14 — SORVEGLIANZA SANITARIA

📋 *Riferimenti: artt. 41-43 D.Lgs. 81/2008*

```
La sorveglianza sanitaria è obbligatoria per i lavoratori esposti a rischi specifici: lavori
in quota, rumore, movimentazione manuale carichi, esposizione CEM. Il Medico Competente
emette giudizio di idoneità alla mansione specifica, incluso lavoro in quota.

I lavoratori addetti al lavoro sulla palina a quota [QUOTA_MAX] m devono essere dichiarati
idonei con specifica nota (assenza controindicazioni: vertigini, patologie cardiocircolatorie).
```

---

## CAPITOLO 15 — RISCHI PRINCIPALI — ANALISI E PREVENZIONE

📋 *Riferimenti: punto 2.2.3, Allegato XV D.Lgs. 81/2008 — Matrice R = P × D*

```
Metodologia: R = P × D. P (1=Bassa, 2=Media, 3=Alta) × D (1=Lieve, 2=Grave, 3=Gravissimo).
R ≥ 9: CRITICO (rosso); 6-8: ALTO (arancio); 3-5: MEDIO (giallo); 1-2: BASSO (verde).
```

### 🔒 LEGALE — Garanti rischio critico (T36 — 1×1, sfondo `#EBF5FB`)

> Per ogni rischio con R ≥ 6, il PSC indica il titolare della posizione di garanzia:
> - **DPC**: CSE (verifica) + DL impresa (installazione/manutenzione)
> - **DPI**: DL impresa affidataria (fornitura e addestramento)
> - **Prescrizioni operative**: CSE (coordinamento) + Preposto (esecuzione)

### ⚠ BOX H.7 DPC > DPI (T37 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.7 — Cass. Pen. n. 8083/2019: DPC prioritari. La scala alla marinara con
protezione a gabbia e la linea vita EN 795 tipo A2 costituiscono i DPC primari per l'accesso
alla palina; l'imbracatura è DPI complementare obbligatorio.
```

### 15.1 Caduta dall'alto — Rischio principale

| 15.1 | Caduta dall'alto dalla palina (quota max [QUOTA_MAX] m) durante installazione RRH/combiner | 3 | 3 | DPC: scala alla marinara con protezione a gabbia; linea vita verticale EN 795 tipo A2 su palina; piattaforme di lavoro fisse. DPI: imbracatura EN 361 + cordino dinamico doppio EN 355. Tirante d'aria verificato ≥ 6 m. Lavori in coppia obbligatori. Divieto salita senza DPI III cat. allacciati. **GARANTE DPC**: CSE (verifica) + DL Circet (manutenzione). **GARANTE DPI**: DL Circet. |

> Sfondo misure: `#FECACA` (R=9 CRITICO)

### 15.2 Caduta di materiale dall'alto

| 15.2 | Caduta di RRH/attrezzi/cavi dall'alto della palina (quota [QUOTA_MAX] m) | 3 | 3 | Recinzione area sottostante palina. Sacchi portautensili certificati. Divieto sosta sotto operatori in quota. Corde di servizio per sollevamento controllato materiali. Segnaletica W012. **GARANTE**: CSE + DL Circet. |

> Sfondo misure: `#FECACA` (R=9 CRITICO)

### 15.3 Elettrocuzione

| 15.3 | Contatto con circuiti DC -48V attivi nel quadro elettrico | 2 | 3 | Sezionamento circuito con lucchetto prima dell'intervento. Personale qualificato PES/PAV CEI 11-27. Guanti isolanti IEC 60903. Segnaletica W008. Verifica assenza tensione con multimetro prima di ogni collegamento. **GARANTE**: DL Circet (elettricista qualificato). |

> Sfondo misure: `#FED7AA` (R=6 ALTO)

### 15.4 Radiazioni non ionizzanti — CEM

| 15.4 | Esposizione a CEM da SRB esistente attiva durante lavori sulla palina | [P] | [D] | Verifica preventiva: impianto esistente attivo? Se SÌ: misura CEM ante-operam (art. 210 D.Lgs. 81/08). Limitare permanenza in zone con E > 20 V/m. Segnaletica W005 in copertura. Coordinamento con operatore per spegnimento settori durante lavori ravvicinati. **GARANTE**: CSE + DL Circet. |

> P e D da calibrare sul cantiere specifico (verificare se impianto è attivo)

### 15.5 Movimentazione manuale di carichi

| 15.5 | Sovraccarico biomeccanico durante trasporto RRH, combiner, cavi in copertura e sulla palina | 2 | 2 | Frazionamento carichi. Uso paranco/carrucola per sollevamento pezzi > 25 kg sulla palina. Formazione MMC (D.Lgs. 81/08 Titolo VI). Rotazione compiti. |

> Sfondo misure: `#FEF9C3` (R=4 MEDIO)

### ⚠ BOX H.8 MICROCLIMA (T43 — 1×1, sfondo `#FFF5F5`, PRIMA della tabella 15.6)

```
⚠ AVVERTENZA H.8 — Orientamento Cass. Pen. 2023-2025: in caso di temperatura percepita
> 35°C, gelo, vento forte, pioggia o scarsa visibilità, il CSE dispone la sospensione o la
rimodulazione dei lavori in quota.
```

### 15.6 Microclima sfavorevole

| 15.6 | Microclima sfavorevole: vento, temperatura estrema, pioggia su copertura esposta | 2 | 2 | Monitoraggio previsioni meteo giornaliero. Sospensione lavori in quota con vento > 6 m/s (21,6 km/h). Pause ogni 2h in estate (T > 30°C). Idratazione obbligatoria. Sospensione per gelo o pioggia intensa. **GARANTE**: CSE + Preposto Circet. |

> Sfondo misure: `#FEF9C3` (R=4 MEDIO)

### 15.7 Scivolamento e inciampo su copertura

| 15.7 | Scivolamento su guaina bagnata/ghiacciata; inciampo su cavi, attrezzi, ostacoli in copertura | 2 | 2 | Pulizia percorsi. Scarpe S3 antiscivolo SRC. Cavi incanalati o segnalati. Illuminazione adeguata. Verifica guaina copertura prima dell'accesso. Segnaletica W024 lungo percorso cavi. |

> Sfondo misure: `#FEF9C3` (R=4 MEDIO)

### 15.8 Caduta dal bordo della copertura

| 15.8 | Caduta dal bordo della copertura (quota lastrico [QUOTA_LASTRICO] m) | [P] | [D] | Muretto perimetrale h [ALTEZZA_MURETTO] cm. Se muretto < 100 cm: parapetto provvisorio EN 13374 Classe A (montanti + corrente 100 cm + intermedio 50 cm + fermapiede 20 cm). Divieto avvicinamento bordo senza DPI. Segnaletica perimetrale. **GARANTE**: CSE (verifica DPC) + DL Circet. |

> P e D da calibrare in base all'altezza del muretto esistente

---

## CAPITOLO 16 — PROGRAMMA DEI LAVORI — CRONOPROGRAMMA

📋 *Riferimenti: punto 2.1.2, lettera d, Allegato XV*

```
Durata totale stimata: [DURATA_GG] giorni lavorativi (con sovrapposizione fasi ove possibile).
Uomini/giorno totali: [UOMINI_GIORNO] u/g ([N_OPERATORI] operatori × [DURATA_GG] giorni).
Data inizio lavori: ✏ DA DEFINIRE.
```

### Diagramma di Gantt B40 (T46 — 9×7)

| Fase | Impresa | G1 | G2 | G3 | G4 | G5 |
|------|---------|----|----|----|----|-----|
| L.01 — Allestimento cantiere | Circet | ▓ | | | | |
| L.02 — Installazione staffe RRH/combiner | Circet | ▓ | ▓ | | | |
| L.03 — Montaggio RRH e combiner | Circet | | ▓ | ▓ | | |
| L.04 — Posa cavi DC -48V | Circet | | | ▓ | ▓ | |
| L.05 — Collegamento quadro DC | Circet | | | | ▓ | |
| L.06 — Posa jumper e collaudo | Circet | | | | ▓ | ▓ |
| L.07 — Smontaggio cantiere e ripristini | Circet | | | | | ▓ |

Colorazione Gantt:
- `#FFC000` (giallo) = Circet Italia (affidataria)
- Celle vuote = non attiva

---

## CAPITOLO 17 — ANALISI GENERALE DEI RISCHI — METODOLOGIA

📋 *Riferimenti: punto 2.2, Allegato XV*

### Tabella riepilogo fasi e rischi (T48 — 8×5)

| Fase | Rischi | P | D | R |
|------|--------|---|---|---|
| L.01 — Allestimento cantiere | Caduta, scivolamento, MMC | 2 | 2 | 4 |
| L.02 — Installazione staffe | Caduta dall'alto, caduta materiale | 3 | 3 | 9 |
| L.03 — Montaggio RRH/combiner | Caduta dall'alto, MMC, CEM | 3 | 3 | 9 |
| L.04 — Posa cavi DC -48V | Caduta dall'alto, inciampo | 2 | 2 | 4 |
| L.05 — Collegamento quadro DC | Elettrocuzione, CEM | 2 | 3 | 6 |
| L.06 — Posa jumper e collaudo | Caduta dall'alto, CEM | 2 | 3 | 6 |
| L.07 — Smontaggio cantiere | Caduta, scivolamento | 2 | 2 | 4 |

### Matrice R = P × D (T49 — 4×4)

| P / D | D=1 Lieve | D=2 Grave | D=3 Gravissimo |
|-------|-----------|-----------|----------------|
| P=1 Bassa | 1 — BASSO | 2 — BASSO | 3 — MEDIO |
| P=2 Media | 2 — BASSO | 4 — MEDIO | 6 — ALTO |
| P=3 Alta | 3 — MEDIO | 6 — ALTO | 9 — CRITICO |

Colorazione: BASSO `#D1FAE5`, MEDIO `#FEF9C3`, ALTO `#FED7AA`, CRITICO `#FECACA`.

---

## CAPITOLO 18 — INDIVIDUAZIONE, ANALISI E VALUTAZIONE DEI RISCHI PER FASE

📋 *Riferimenti: punto 2.2.3, Allegato XV — modello INAIL schede fase lavorativa*

### 18.1 Rischi generali comuni a tutte le fasi

- Viabilità: accesso unico controllato con segnaletica permanente
- Presidi sanitari e numeri emergenza visibili
- Verifica patente a crediti e badge digitale a ogni accesso
- Formazione specifica: lavori in quota, impianti elettrici, CEM
- Comunicazione copertura-terra: telefono cellulare

### 18.2 Schede fasi lavorative B40 (T50–T55, ciascuna 7×2)

**18.2.1 — Allestimento cantiere e trasporto materiali**

| Campo | Contenuto |
|-------|-----------|
| Descrizione attività | Segnaletica, delimitazione zona lavoro, trasporto RRH/combiner/cavi in copertura |
| Fattori di rischio | Caduta in piano, MMC (trasporto scale), scivolamento |
| DPC | Segnaletica P006, M003, M004, M015 all'accesso copertura |
| DPI | Elmetto EN 397, scarpe S3, guanti EN 388, giubbotto AV |
| Prescrizioni | Materiali portati a mano; max 25 kg per persona; percorso illuminato |
| Interferenze | — |
| Sorveglianza CSE | Sopralluogo iniziale; verifica accesso e segnaletica |

**18.2.2 — Installazione staffe e supporti RRH/combiner sulla palina**

| Campo | Contenuto |
|-------|-----------|
| Descrizione attività | Fissaggio staffe metalliche sulla palina per RRH e combiner |
| Fattori di rischio | Caduta dall'alto (palina h [ALTEZZA_PALINA] m), caduta attrezzi |
| DPC | Linea vita verticale EN 795 tipo A2; protezione a gabbia scala |
| DPI | Imbracatura EN 361 + cordino doppio EN 355; elmetto; scarpe S3 |
| Prescrizioni | Lavoro in coppia; sacchi portautensili; divieto sosta sotto palina |
| Interferenze | Non contemporanea a L.04 (posa cavi al quadro) |
| Sorveglianza CSE | Verifica DPI III cat.; verifica ancoraggio; verbale pre-salita |

**18.2.3 — Montaggio RRH e combiner sulla palina**

| Campo | Contenuto |
|-------|-----------|
| Descrizione attività | Sollevamento con paranco e fissaggio RRH e combiner sulle staffe |
| Fattori di rischio | Caduta dall'alto, caduta apparati, CEM (se impianto parzialmente attivo) |
| DPC | Linea vita; paranco con fune certificata |
| DPI | Imbracatura EN 361 + cordino EN 355; elmetto; guanti EN 388 |
| Prescrizioni | Verifica CEM se impianto attivo; coordinamento spegnimento settori |
| Interferenze | Sequenziale dopo L.02 |
| Sorveglianza CSE | Presenza durante sollevamento apparati; verifica CEM |

**18.2.4 — Posa cavi DC -48V dalla palina al quadro elettrico**

| Campo | Contenuto |
|-------|-----------|
| Descrizione attività | Posa cavi alimentazione DC -48V lungo percorso palina → quadro |
| Fattori di rischio | Inciampo cavi, caduta dall'alto (tratti in quota), elettrocuzione |
| DPC | Canalette per percorso cavi; fissaggio con fascette |
| DPI | Elmetto; scarpe S3; guanti isolanti se vicino al quadro |
| Prescrizioni | Cavi fissati lungo percorso; no cavi volanti in copertura |
| Interferenze | Non contemporanea a L.02/L.03 (lavori in quota su palina) |
| Sorveglianza CSE | Verifica percorso cavi; verifica fissaggi |

**18.2.5 — Collegamento quadro DC -48V e installazione interruttori**

| Campo | Contenuto |
|-------|-----------|
| Descrizione attività | Installazione interruttori MT nel quadro DC e collegamento cavi |
| Fattori di rischio | Elettrocuzione DC -48V, arco elettrico |
| DPC | Sezionamento generale con lucchetto; cartello "lavori in corso" |
| DPI | Guanti isolanti IEC 60903 Cl.0; occhiali EN 166; scarpe S3 |
| Prescrizioni | Solo personale PES/PAV CEI 11-27; verifica assenza tensione; lavoro fuori tensione |
| Interferenze | Non contemporanea a L.06 (collaudo con impianto attivo) |
| Sorveglianza CSE | Verifica qualificazione elettrica; verifica sezionamento |

**18.2.6 — Posa jumper coassiali e collaudo**

| Campo | Contenuto |
|-------|-----------|
| Descrizione attività | Connessione jumper RF da antenne a RRH, collaudo funzionale |
| Fattori di rischio | Caduta dall'alto (lavori su palina), CEM (durante collaudo) |
| DPC | Linea vita; delimitazione area durante collaudo |
| DPI | Imbracatura EN 361; elmetto; guanti |
| Prescrizioni | Collaudo con personale qualificato; verifica limiti CEM post-attivazione |
| Interferenze | — |
| Sorveglianza CSE | Verifica rapporto collaudo; verbale fine lavori |

### 18.3 Interferenze critiche tra fasi

```
[SE SINGOLA IMPRESA]: Considerata la presenza di una sola impresa esecutrice e l'assenza di
subappalti, non si prevedono interferenze tra imprese. Le fasi sono organizzate in sequenza
con sovrapposizioni controllate (cfr. Gantt Cap. 16). Le principali sovrapposizioni critiche:
```

| Fasi sovrapposte | Rischio | Misura |
|---|---|---|
| L.02 + L.04 | Lavori in quota su palina + posa cavi al quadro: caduta attrezzi | Sequenzialità per tratti verticali |
| L.03 + L.05 | Montaggio apparati + collegamento elettrico | Sezionamento obbligatorio durante L.05 |
| L.06 collaudo + qualsiasi fase in quota | CEM durante attivazione impianto | Nessun operatore su palina durante collaudo RF |

### ⚠ BOX H.2 (T56 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.2
In caso di pericolo grave e imminente il CSE dispone sospensione immediata delle lavorazioni
(art. 92, co. 1, lett. f, D.Lgs. 81/08).
```

---

## CAPITOLO 19 — GESTIONE DELLE EMERGENZE

📋 *Riferimenti: artt. 37-38, 43-45 D.Lgs. 81/2008 — D.M. 388/2003*

### 19.1 Presidi sanitari

```
Cassetta pronto soccorso conforme D.M. 388/2003 presente nell'area apparati sul lastrico.
Coperte isotermiche. Addetto Primo Soccorso designato dall'impresa Circet.

Procedura infortunio: 1) Non spostare il ferito. 2) Valutare coscienza/respirazione.
3) Contattare 118. 4) Primo soccorso da addetto formato. 5) CSE informato immediatamente.
6) Denuncia INAIL.
```

### 19.2 Procedura — Caduta dall'alto

```
In caso di caduta dall'alto dalla palina: 1) Allertare immediatamente il 118 comunicando la
quota. 2) Non tentare di spostare l'infortunato. 3) Predisporre accesso rapido VVF/118 alla
copertura. 4) CSE informato immediatamente. 5) Sospensione lavori.
```

### 19.3 Procedura — Elettrocuzione DC -48V

```
In caso di elettrocuzione: 1) Sezionare immediatamente il circuito (interruttore generale).
2) Non toccare l'infortunato finché il circuito non è sezionato. 3) Chiamare 118.
4) Rianimazione BLS solo se formati. 5) CSE informato immediatamente.
```

### 19.4 Antincendio

```
Estintori: min. 1 polvere ABC 6 kg nell'area apparati + 1 CO2 5 kg presso quadro elettrico.
VIETATO fumare sul lastrico solare. Procedura incendio: 1) Allontanare personale. 2) Tentare
spegnimento se sicuro. 3) Chiamare 115. 4) Evacuare copertura. 5) Punto raccolta a terra.
```

### 19.5 Condizioni meteorologiche avverse

```
Sospensione immediata dei lavori in quota:
- Vento > 6 m/s (21,6 km/h)
- Temporali / fulmini (cessare immediatamente lavori su palina metallica!)
- Temperatura percepita > 35°C (turni ridotti, pause, idratazione)
- Ghiaccio o neve su copertura
- Pioggia intensa
- Nebbia con visibilità < 50 m
```

---

## CAPITOLO 20 — STIMA DEI COSTI DELLA SICUREZZA

📋 *Riferimenti: punto 2.3 e punto 4, Allegato XV D.Lgs. 81/2008*

### Tabella costi B40 (T58 — 6×5)

| Voce di costo | Qta | U.M. | C. unit. | Totale |
|---|---|---|---|---|
| Segnaletica di cantiere (cartelli ISO 7010 + cartello cantiere) | 1 | set | € [CU] | € [TOT] |
| Cassetta pronto soccorso D.M. 388/2003 | 1 | cad | € [CU] | € [TOT] |
| Estintori (ABC 6 kg + CO2 5 kg) | 2 | pz | € [CU] | € [TOT] |
| Sopralluoghi CSE in cantiere | [Q] | ore | € [CU] | € [TOT] |
| Riunione di coordinamento CSE | [Q] | ore | € [CU] | € [TOT] |
| | | | **TOTALE** | **€ [TOTALE_COSTI]** |

> 📌 I costi della sicurezza NON sono soggetti a ribasso d'asta (art. 26 co. 5 D.Lgs. 81/08 e Allegato XV punto 4).

---

## CAPITOLO 21 — DOCUMENTI DA TENERE IN CANTIERE (T59 — 18×2)

| Rif. | Documento |
|------|-----------|
| 21.1 | PSC e aggiornamenti |
| 21.2 | POS di tutte le imprese |
| 21.3 | Notifica Preliminare protocollata |
| 21.4 | Nominativi: CSP, CSE, DL, RSPP, RLS, MC |
| 21.5 | Patente a crediti (visura aggiornata) |
| 21.6 | Registro presenze giornaliero con badge |
| 21.7 | SDS sostanze pericolose |
| 21.8 | Dichiarazioni CE attrezzature |
| 21.9 | Certificati linea vita / sistemi anticaduta EN 795 |
| 21.10 | Schede imbracature, cordini, moschettoni |
| 21.11 | Attestati formazione (lavori in quota, impianti elettrici) |
| 21.12 | Verbali riunioni coordinamento CSE |
| 21.13 | Verbali sopralluoghi CSE |
| 21.14 | DdC impianto elettrico D.M. 37/2008 |
| 21.15 | DURC in corso di validità |
| 21.16 | Titolo abilitativo e cartello cantiere |
| 21.17 | Progetto Esecutivo (PE) |

---

## CAPITOLO 22 — ALLEGATI (T60 — 8×2)

| Allegato | Titolo |
|----------|--------|
| 1 | Elenco lavorazioni |
| 2 | Cronoprogramma lavori (Diagramma di Gantt) |
| 3 | Layout planimetrico del cantiere |
| 4 | Fascicolo dell'Opera |
| 5 | Check-list macchine e attrezzature |
| 6 | Calcolo uomini-giorno |
| 7 | Modulo segnalazione near miss |

---

## SOTTOSCRIZIONI — ACCETTAZIONE DEL PIANO (T61 — 2×2)

| 🛡 IL COORDINATORE PER LA SICUREZZA (CSP e CSE) | 🏢 IL COMMITTENTE |
|---|---|
| [NOME_CSE] | Iliad Italia S.p.A. |
| [NOME_STUDIO] | ✏ DA COMPILARE: referente Iliad |
| Ordine [CAT] [PROV] Sez. A n. [N_ORDINE] | |
| _______________________________ | _______________________________ |
| Firma e Timbro | Firma e Timbro |

| 🏗 L'IMPRESA AFFIDATARIA | 🔧 IMPRESA SUBAPPALTATRICE |
|---|---|
| Circet Italia S.p.A. | [ELENCO_SUBAPPALTATORI] |
| ✏ DA COMPILARE | ✏ DA COMPILARE |
| _______________________________ | _______________________________ |
| Firma e Timbro | Firma e Timbro |

```
Copia del PSC sottoscritta da tutte le imprese deve essere tenuta in cantiere per tutta la
durata dei lavori. Il POS deve essere consegnato al CSE prima dell'inizio delle lavorazioni.
```

---

## ALLEGATO 1 — ELENCO LAVORAZIONI (T62 — 8×5)

**Heading 1**: `ALLEGATO 1 — ELENCO LAVORAZIONI`

| Cod. | Lavorazione | Descrizione sintetica | Impresa | Durata |
|------|-------------|----------------------|---------|--------|
| L.01 | Allestimento cantiere | Segnaletica, delimitazione area, trasporto materiali in copertura | Circet | [GG] gg |
| L.02 | Installazione staffe | Fissaggio staffe metalliche su palina per RRH e combiner | Circet | [GG] gg |
| L.03 | Montaggio RRH e combiner | Sollevamento e fissaggio apparati sulle staffe | Circet | [GG] gg |
| L.04 | Posa cavi DC -48V | Posa cavi alimentazione dalla palina al quadro elettrico | Circet | [GG] gg |
| L.05 | Collegamento quadro DC | Installazione interruttori MT e collegamento cavi al quadro | Circet | [GG] gg |
| L.06 | Posa jumper e collaudo | Connessione jumper coassiali e collaudo funzionale | Circet | [GG] gg |
| L.07 | Smontaggio cantiere | Ripristini, pulizia, rimozione segnaletica | Circet | [GG] gg |

---

## ALLEGATO 2 — CRONOPROGRAMMA GANTT (T63 — 9×12)

**Heading 1**: `ALLEGATO 2 — CRONOPROGRAMMA DEI LAVORI`

Tabella Gantt a mezze giornate: colonne `Fase | Impresa | G1M | G1P | G2M | G2P | G3M | G3P | G4M | G4P | G5M | G5P`

Dove M = mattina, P = pomeriggio. Celle colorate `#FFC000` = attiva Circet.

```
Legenda: ▓ giallo FFC000 = Circet Italia — M = mattina — P = pomeriggio
```

---

## ALLEGATO 3 — LAYOUT PLANIMETRICO (T64 — 10×3)

**Heading 1**: `ALLEGATO 3 — LAYOUT PLANIMETRICO DEL CANTIERE`

```
Il layout è rappresentato negli elaborati grafici del PE. Di seguito gli elementi:
```

| Elemento | Posizione | Note |
|----------|-----------|------|
| Accesso copertura | [POSIZIONE: es. scala interna, lato nord] | Porta/botola con segnaletica |
| Palina esistente | [POSIZIONE] | h [ALTEZZA_PALINA] m, orientamento [DIR] |
| Punto installazione RRH | [POSIZIONE: es. settori 1, 2, 3 sulla palina] | Quota installazione: [QUOTA] m |
| Percorso cavi DC | [DESCRIZIONE: es. da palina a quadro, lungo muretto perimetrale] | Fissaggio con fascette ogni [X] cm |
| Quadro elettrico DC -48V | [POSIZIONE] | Sezionamento con lucchetto |
| Area deposito materiali | [POSIZIONE: es. area apparati esistente] | Lontano dal bordo copertura |
| Cassetta PS + estintore | [POSIZIONE] | Visibili e accessibili |
| Segnaletica accesso | [POSIZIONE: ingresso vano scala + porta copertura] | P006, M003, M004, M015 |
| Punto raccolta emergenza | [POSIZIONE: es. ingresso edificio piano terra] | Segnaletica E007 |

---

## ALLEGATO 4 — FASCICOLO DELL'OPERA

**Heading 1**: `ALLEGATO 4 — FASCICOLO DELL'OPERA`

```
(ai sensi dell'art. 91, comma 1, lett. b, D.Lgs. 81/2008 — Allegato XVI)
Informazioni utili per la prevenzione dei rischi in occasione di futuri lavori di
manutenzione o adeguamento della SRB.
```

### Scheda I — Descrizione dell'opera (T65 — 10×2)

| Campo | Valore |
|-------|--------|
| Ubicazione | [INDIRIZZO] — [COMUNE] ([PROV]) |
| Tipo intervento | Modifica SRB Iliad [CODICE_SITO] — aggiunta RRH/combiner |
| Struttura ospitante | [TIPO_EDIFICIO], [N_PIANI] piani, copertura piana a quota [QUOTA_LASTRICO] m |
| Struttura SRB | Palina h [ALTEZZA_PALINA] m su [SUPPORTO] — quota max [QUOTA_MAX] m |
| Apparati installati | [ELENCO_APPARATI] |
| Impianti | Elettrico DC -48V + terra + coassiali RF |
| Durata lavori | [DURATA_GG] giorni |
| Imprese | Circet Italia S.p.A. |
| CSP/CSE | [NOME_CSE] |

### Scheda II — Rischi manutenzione futura (T66 — 6×5)

| Intervento futuro | Rischio principale | Misura preventiva | Dotazione opera | Frequenza |
|---|---|---|---|---|
| Sostituzione RRH/combiner | Caduta dall'alto dalla palina | Imbracatura + linea vita | Linea vita EN 795 su palina | Al bisogno |
| Manutenzione quadro DC | Elettrocuzione | Sezionamento + lucchetto | Interruttore generale | Semestrale |
| Sostituzione antenne | Caduta apparati dall'alto | Paranco + delimitazione area | Punto ancoraggio su palina | Al bisogno |
| Adeguamento tecnologico (UP5G) | Caduta + CEM + elettrocuzione | DPI III cat. + spegnimento | Dispositivi anticaduta | Al bisogno |
| Ispezione periodica struttura | Caduta dall'alto | Imbracatura anticaduta | Linea vita su palina | Annuale |

### Scheda III — Documentazione (T67 — 8×2)

| Documento | Archivio |
|-----------|----------|
| Progetto Esecutivo (PE) | Iliad / Circet |
| DdC impianto elettrico D.M. 37/08 | Circet / Iliad |
| DdC impianto di terra | Circet / Iliad |
| PSC (presente documento) | CSE / Iliad |
| POS imprese | CSE / Iliad |
| Certificato strutturale palina | Fornitore / Iliad |
| Fascicolo manutenzione palina | CSE / Iliad |

---

## ALLEGATO 5 — CHECK-LIST MACCHINE E ATTREZZATURE (T68 — 8×6)

**Heading 1**: `ALLEGATO 5 — CHECK-LIST MACCHINE E ATTREZZATURE`

| Attrezzatura | Marcatura CE | Libretto uso | Manutenz. | Operatore formato | Conforme |
|---|---|---|---|---|---|
| Trapano/avvitatore | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| Chiave dinamometrica | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| Paranco/carrucola | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| Crimpatrice cavi | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| Multimetro | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| Pinza amperometrica | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| [ALTRA] | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |

```
Compilata da: ________________________________  Data: ___/___/______
Verificata dal CSE: ________________________________  Data: ___/___/______
```

---

## ALLEGATO 6 — CALCOLO UOMINI-GIORNO (T69 — 9×4)

**Heading 1**: `ALLEGATO 6 — CALCOLO UOMINI-GIORNO`

| Fase | Lavorazione | N° operai × Durata | Uomini-giorno |
|------|-------------|---------------------|---------------|
| L.01 | Allestimento cantiere | [N] × [GG] | [UG] |
| L.02 | Installazione staffe | [N] × [GG] | [UG] |
| L.03 | Montaggio RRH e combiner | [N] × [GG] | [UG] |
| L.04 | Posa cavi DC -48V | [N] × [GG] | [UG] |
| L.05 | Collegamento quadro DC | [N] × [GG] | [UG] |
| L.06 | Posa jumper e collaudo | [N] × [GG] | [UG] |
| L.07 | Smontaggio cantiere | [N] × [GG] | [UG] |
| | **TOTALE** | | **[TOTALE_UG]** |

---

## ALLEGATO 7 — MODULO SEGNALAZIONE NEAR MISS (T70 — 13×2)

**Heading 1**: `ALLEGATO 7 — MODULO SEGNALAZIONE NEAR MISS / MANCATO INFORTUNIO`

| Campo | Compilazione |
|-------|-------------|
| Data e ora evento | ___/___/______ ore ___:___ |
| Luogo esatto | ☐ Copertura ☐ Palina ☐ Scale accesso ☐ Quadro elettrico ☐ Altro: ________ |
| Fase lavorativa in corso | |
| Descrizione sintetica evento | |
| Persone coinvolte | |
| Persone testimoni | |
| Possibili cause | ☐ Caduta oggetti ☐ Scivolamento ☐ Caduta dall'alto ☐ Contatto elettrico ☐ CEM ☐ Vento ☐ Altro: ________ |
| DPI indossati | ☐ Elmetto ☐ Imbracatura ☐ Scarpe S3 ☐ Guanti ☐ Giubbotto AV ☐ Altro: ________ |
| Gravità potenziale | ☐ Lieve ☐ Moderata ☐ Grave ☐ Molto grave |
| Azioni immediate intraprese | |
| Azioni correttive proposte | |

```
Segnalante: ________________________________  Impresa: ________________________________
Data: ___/___/______  Firma: ________________________________

RICEZIONE CSE
Data: ___/___/______  Protocollo n.: ____________
Azioni disposte: ________________________________
Firma CSE: ________________________________
```

---

## 🔒 APPENDICE — CHECKLIST PRE-CONSEGNA

### Checklist F.1 — Completezza documentale

- [ ] Frontespizio compilato (21 righe: codice sito, tecnologie, quote, PE, CSE)
- [ ] Box ⚠ H.1 presente dopo frontespizio
- [ ] Box 🔒 Specificità PSC presente
- [ ] Tabella normativa (T3) completa
- [ ] Tabella posizioni garanzia (T4) con nomi corretti
- [ ] Anagrafica cantiere (T5) completa: 23 righe, numeri utili aggiornati
- [ ] Foto ante-operam inserite (min. 8 + planimetria di progetto)
- [ ] Zone operative (T25) calibrate sul sito specifico
- [ ] Tutti i rischi 15.1–15.8 con P e D motivate (NON generici)
- [ ] Rischio CEM calibrato su stato impianto (attivo/spento)
- [ ] Cronoprogramma Gantt coerente con 7 fasi
- [ ] 6 schede fase lavorativa compilate
- [ ] Costi sicurezza calcolati
- [ ] 7 allegati sviluppati (non solo elencati)
- [ ] Fascicolo dell'Opera (3 schede)
- [ ] Sottoscrizioni con tutti i soggetti

### Checklist F.3 — Conformità normativa e difensiva

- [ ] ⚠ H.1 (PSC specifico) → dopo frontespizio + Cap. 7
- [ ] ⚠ H.2 (sospensione lavori) → Cap. 3 + Cap. 18
- [ ] ⚠ H.3 (verifica POS) → Cap. 3.3
- [ ] ⚠ H.4 (alta vigilanza) → Cap. 3.2
- [ ] ⚠ H.5 (aggiornamento PSC) → Cap. 3.1
- [ ] ⚠ H.6 (interferenziale) → Cap. 9.4
- [ ] ⚠ H.7 (DPC > DPI) → Cap. 12 + Cap. 15
- [ ] ⚠ H.8 (microclima) → Cap. 15.6
- [ ] 🔒 Specificità PSC → T2
- [ ] 🔒 Clausola aggiornamento → T7
- [ ] 🔒 Perimetro vigilanza CSE → T10
- [ ] 🔒 Perimetro funzioni CSE → T11
- [ ] 🔒 Clausole contrattuali → T13 + T14
- [ ] 🔒 Informazioni committente → T15
- [ ] 🔒 Garanti rischio critico → T36
- [ ] Nessun placeholder residuo non intenzionale
