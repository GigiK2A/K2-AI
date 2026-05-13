# FORMAT PSC K2A TLC ROOF TOP — Template Completo con Integrazione Legale

> **ISTRUZIONI PER L'USO**: Questo file contiene la struttura esatta e il testo standard di ogni sezione del PSC K2A per cantieri TLC Roof Top (installazione/adeguamento SRB su copertura di edifici). Per ogni nuovo PSC:
> 1. Copia l'intera struttura
> 2. Sostituisci tutti i placeholder `[PLACEHOLDER]` con i dati del sito specifico
> 3. Adatta i rischi e le schede fase lavorativa al tipo di intervento (New Site / UP5G / Adeguamento / Dismissione / Transfer)
> 4. Le sezioni marcate con 🔒 LEGALE contengono clausole difensive obbligatorie — NON rimuoverle mai
> 5. Le sezioni marcate con ⚠ AVVERTENZA H.x contengono warning giurisprudenziali Cassazione Penale — NON rimuoverle mai
> 6. Esegui le checklist F.1 e F.3 (in fondo al documento) prima della consegna
>
> **VARIANTE**: Questo format è specifico per cantieri **TLC Roof Top** (installazione/adeguamento SRB su copertura edificio). Per cantieri TLC Raw Land usare variante con fondazioni. Per cantieri civili/residenziali usare `format-psc-evo-appartamento.md`.

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
> **B. CARTELLONISTICA (TAVOLA SEPARATA dopo sottoscrizioni)** — Formato "scheda pittogramma":
> - Tabella a **3 colonne**: `Pittogramma | Tipo Segnale | Esposizione nel Cantiere`
> - Riga 0 (intestazione): sfondo blu `#2F5496`, testo bianco bold 9pt
> - Colonna 0 (Pittogramma): immagine PNG del pittogramma ISO 7010 (larghezza 1.8 cm, centrata)
> - Le immagini dei pittogrammi sono conservate nella cartella `signs_ref/` e mappate nel file `mapping.json`
> - Se le immagini non sono disponibili, inserire il codice ISO (es. "M003") come testo
> - Colonna 1 (Tipo Segnale): codice + denominazione in bold + sotto in grigio piccolo il riferimento normativo
> - Colonna 2 (Esposizione): testo specifico per il cantiere
> - Larghezze: Col0 ~2.5cm, Col1 ~6cm, Col2 ~7.5cm
> - Una tabella separata per ogni categoria (Prescrizione, Pericolo, Divieto, Emergenza, Antincendio)
> - **NOTA**: Nel format TLC Roof Top la cartellonistica è una **TAVOLA SEPARATA** posizionata DOPO le sottoscrizioni e PRIMA degli allegati
>
> **C. WARNING, NOTE e CLAUSOLE LEGALI** — Formato "box singola cella":
> - Avvertenze (⚠ H.x): tabella 1×1, sfondo `#FFF5F5`, testo 9pt, codice in bold rosso `#C00000`
> - Note (📌): tabella 1×1, sfondo `#F0F9FF`, testo 9pt
> - Clausole legali (🔒): tabella 1×1, sfondo `#EBF5FB`, titolo bold blu `#1F4E79`
>
> **D. ORGANIGRAMMA** — Formato "tabella grafica colorata":
> - Tabella 7 righe × 4 colonne con celle colorate per ruolo
> - Colori: `#1F4E79` (CSE, intestazione), `#2E75B6` (Committente), `#C00000` (Impresa appaltatrice)
> - Sfondo box: `#FFF2CC` (Committente/Iliad), `#FFEB9C` (Affidataria/Circet), `#C6EFCE` (Subappaltatori), `#BDD7EE` (CSE)
> - Testo centrato in ogni cella, nomi in bold
>
> **E. SOTTOSCRIZIONI** — Formato "griglia 2×2":
> - Tabella 2 righe × 2 colonne (CSE | Committente / Affidataria | Subappaltatrice)
> - Con emoji ruolo (🛡, 🏢, 🏗, 🔧)
>
> **F. ALLEGATI** — Devono essere SVILUPPATI in calce al documento, non solo elencati:
> - Allegato 1: tabella completa lavorazioni (Cod. | Lavorazione | Descrizione | Impresa | Durata)
> - Allegato 2: cronoprogramma Gantt testuale (tabella con celle colorate per impresa)
> - Allegato 3: layout planimetrico (descrizione testuale con riferimento tavole PE)
> - Allegato 4: Fascicolo dell'Opera completo (3 Schede: I descrizione, II rischi manutenzione, III documentazione)
> - Allegato 5: check-list macchine compilabile (10×8, caselle ☐ Sì ☐ No)
> - Allegato 6: calcolo uomini-giorno in tabella
> - Allegato 7: modulo near miss compilabile
>
> **G. GESTIONE IMMAGINI**:
> 
> Le immagini nel PSC si dividono in due categorie:
> 
> **IMMAGINI FISSE (da template — NON sostituire mai):**
> - Segnaletica PRESCRIZIONE ISO 7010 (TAVOLA CARTELLONISTICA)
> - Segnaletica PERICOLO ISO 7010 (TAVOLA CARTELLONISTICA)
> - Segnaletica DIVIETO ISO 7010 (TAVOLA CARTELLONISTICA)
> - Segnaletica EMERGENZA ISO 7010 (TAVOLA CARTELLONISTICA)
> - Segnaletica ANTINCENDIO ISO 7010 (TAVOLA CARTELLONISTICA)
> - Tavola attrezzature e DPI (Cap. 11 e Cap. 12)
> - Tavola DPI antirumore (Cap. 13)
> 
> **FOTO SITO (placeholder — da inserire per ogni progetto):**
> - Cap. 6.3: minimo 8 foto ante-operam del sito + planimetria copertura
> - Layout: **almeno 2 foto per pagina**, disposte su 2 colonne affiancate (7 cm ciascuna)
> - Usare tabella invisibile (no border) 2 colonne per il layout
> - Planimetria copertura: larghezza piena (14 cm), celle unite
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
> - Interruzione di pagina: prima di ogni capitolo principale (1–22), prima della TAVOLA CARTELLONISTICA e prima degli allegati

---

## STRUTTURA DOCUMENTO — 22 CAPITOLI + TAVOLA CARTELLONISTICA + 7 ALLEGATI

```
FRONTESPIZIO (T0 — 10×2)
⚠ BOX H.1 (T1 — 1×1)
🔒 BOX LEGALE POSIZIONI DI GARANZIA (T2 — 1×1)
SOMMARIO
CAPITOLO 1 — PREMESSA
CAPITOLO 2 — ANAGRAFICA DI CANTIERE
  2.1 Caratteristiche dell'opera (T3 — 11×2)
  2.2 Soggetti per la sicurezza (T4 — 7×2)
  2.3 Numeri telefonici utili (T5 — 9×2)
CAPITOLO 3 — MODALITÀ DI GESTIONE DEL PSC
  3.1 Revisione del piano
  ⚠ BOX H.2 (T6 — 1×1)
  ⚠ BOX H.5 (T7 — 1×1)
  3.2 Attività di coordinamento del CSE
  ⚠ BOX H.4 (T8 — 1×1)
  3.3 Perimetro delle funzioni del CSE
  🔒 BOX PERIMETRO GARANZIA CSE (T9 — 1×1)
  3.4 Consultazione RLS
  3.5 Riunione di coordinamento
CAPITOLO 4 — NOTIFICA PRELIMINARE
  📌 BOX NOTA (T10 — 1×1)
CAPITOLO 5 — DISPOSIZIONI PER LE IMPRESE
  5.1 Obblighi delle imprese
  ⚠ BOX H.3 (T11 — 1×1)
  5.2 Patente a crediti e badge digitale
  5.3 Contenuti minimi del POS
  5.4 Obblighi contrattuali di sicurezza
  🔒 BOX CLAUSOLE CONTRATTUALI (T12 — 1×1)
CAPITOLO 6 — DESCRIZIONE DELL'OPERA
  🔒 BOX INFORMAZIONI COMMITTENTE (T13 — 1×1)
  6.1 Inquadramento territoriale
  6.2 Descrizione dell'infrastruttura e dell'intervento
  6.3 Schede rilievo fotografico (foto ante-operam sito + planimetria copertura)
CAPITOLO 7 — AREA DI LAVORO
CAPITOLO 8 — RISCHI INTRINSECI E FATTORI ESTERNI
  8.1 Caratteristiche idrogeologiche
  8.2 Fattori esterni (T14 — 6×3)
CAPITOLO 9 — ORGANIZZAZIONE DEL CANTIERE
  9.1 Recinzione, accessi, segnalazioni
  9.2 Impianti di cantiere
  9.3 Aree di stoccaggio
  9.4 Coordinamento lavorazioni — rischio interferenziale
      ORGANIGRAMMA DI CANTIERE (tabella grafica 7×4)
  ⚠ BOX H.6 INTERFERENZIALE (T15 — 1×1)
  9.5 Segnaletica di sicurezza (📌 BOX T16 — 1×1)
CAPITOLO 10 — SOSTANZE PERICOLOSE
CAPITOLO 11 — ATTREZZATURE, MACCHINE E IMPIANTI (T17 — 9×4)
CAPITOLO 12 — DPI (T18 — 14×5)
  ⚠ BOX H.7 DPC > DPI (T19 — 1×1)
CAPITOLO 13 — VALUTAZIONE DEL RUMORE (T20 — 5×3)
CAPITOLO 14 — SORVEGLIANZA SANITARIA
CAPITOLO 15 — RISCHI PRINCIPALI — ANALISI E PREVENZIONE
  15.1–15.9 Schede rischio (T21–T30, ciascuna 1×5)
  ⚠ BOX H.8 MICROCLIMA (prima di 15.6)
CAPITOLO 16 — CRONOPROGRAMMA (T31 — 13×5)
CAPITOLO 17 — MATRICE R = P × D (T32 — 4×4)
CAPITOLO 18 — RISCHI PER FASE
  18.1 Procedure di emergenza e coordinamento
  18.2 Schede di fase lavorativa (T33–T37, ciascuna 7×2)
      TABELLA INTERFERENZE (T38 — 6×3) con ⚠ H.6 in riga 0
CAPITOLO 19 — GESTIONE DELLE EMERGENZE
CAPITOLO 20 — STIMA COSTI SICUREZZA (T39 — 10×5)
CAPITOLO 21 — DOCUMENTI DA TENERE IN CANTIERE
CAPITOLO 22 — ALLEGATI (elenco)
SOTTOSCRIZIONI (T40 — 2×2)
📌 BOX NOTA PSC (T41 — 1×1)
─── TAVOLA CARTELLONISTICA (sezione separata) ───
  Cartelli PRESCRIZIONE (T42 — pittogrammi 3 colonne)
  Cartelli PERICOLO (T43 — pittogrammi 3 colonne)
  Cartelli DIVIETO (T44 — pittogrammi 3 colonne)
  Cartelli EMERGENZA (T45 — pittogrammi 3 colonne)
─── ALLEGATI SVILUPPATI ───
ALLEGATO 1 — ELENCO LAVORAZIONI (T46 — 13×5)
ALLEGATO 2 — CRONOPROGRAMMA GANTT (T47 — 13×11)
ALLEGATO 3 — LAYOUT PLANIMETRICO
ALLEGATO 4 — FASCICOLO DELL'OPERA
  Scheda I  — Descrizione (T48 — 9×3)
  Scheda II — Rischi manutenzione (T49 — 8×2 + T50 — 7×4)
  Scheda III — Documentazione (T51 — 8×3)
ALLEGATO 5 — CHECK-LIST MACCHINE (T52 — 10×8)
ALLEGATO 6 — CALCOLO UOMINI-GIORNO (T53 — 14×5)
ALLEGATO 7 — MODULO NEAR MISS (T54 — 12×2)
```

---

## FRONTESPIZIO

```
──────────────────────────────────────────────────
STUDIO ASSOCIATO EVOLUTION | Piano di Sicurezza e Coordinamento
──────────────────────────────────────────────────

PIANO DI SICUREZZA E COORDINAMENTO
(Allegato XV e art. 100 del D.Lgs. 9 aprile 2008 n. 81 e s.m.i.)

[TIPO_INTERVENTO] di impianto tecnologico di radiotelecomunicazioni
Stazione Radio Base Iliad Italia S.p.A. — Roof Top — [STRUTTURA_es: Palina h=6m su lastrico]

┌─────────────────────┬──────────────────────────────────────────┐
│ Codice Sito         │ [CODICE_SITO]                            │
│ Nome Sito           │ [NOME_SITO]                              │
│ Tipologia           │ Roof Top — [TIPO_INTERVENTO]             │
│ Committente         │ Iliad Italia S.p.A.                      │
│ Indirizzo           │ [INDIRIZZO_CANTIERE] — [CAP] [COMUNE] ([PROVINCIA]) │
│ Coordinate          │ Lat [LAT]° N — Long [LONG]° E            │
│ Tecnologie          │ [TECNOLOGIE_es: 5G700/UMTS900/LTE1800/LTE2100/LTE2600] │
│ Progetto Esecutivo  │ PE Rif. [RIF_PE] — Rev. [REV_PE]         │
│ Rev. PSC            │ 00 — Emissione del [DATA_EMISSIONE]      │
│ CSP / CSE           │ [NOME_CSE] — Ordine Ingegneri [PROV] n. [N_ORDINE] │
└─────────────────────┴──────────────────────────────────────────┘
```

**Tabella T0**: 10 righe × 2 colonne. Colonna 0 = etichetta (bold, sfondo `#2F5496`, testo bianco). Colonna 1 = valore.

**Tabella revisioni** (sotto T0):

```
┌──────┬────────────┬─────────────────┬───────────────┬──────────────┬────────────────┐
│ Rev. │ Data       │ Descrizione     │ Redatto       │ Committenza  │ Impresa        │
├──────┼────────────┼─────────────────┼───────────────┼──────────────┼────────────────┤
│ 1    │ [DATA]     │ Prima emissione │ [NOME_CSE]    │ Iliad Italia │ Circet Italia  │
└──────┴────────────┴─────────────────┴───────────────┴──────────────┴────────────────┘
```

**Firme** (sotto tabella revisioni):

```
IL COORDINATORE PER LA SICUREZZA (CSP/CSE)     IL COMMITTENTE
[NOME_CSE]                                      Iliad Italia S.p.A.

_______________________________                 _______________________________
Firma e Timbro                                  Firma e Timbro
```

---

## ⚠ BOX H.1 (T1 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.1 — Cass. Pen., Sez. IV, n. 27382/2021; n. 7421/2026: il presente PSC è
stato redatto con specifico riferimento al cantiere in oggetto e alle sue criticità peculiari.
Un PSC generico e standardizzato, non aderente alle reali criticità del sito, equivale a una
totale omissione ai fini della colpa penale. Ogni sezione è calibrata sulle condizioni effettive
del cantiere e dovrà essere aggiornata in caso di varianti o nuove criticità emerse in corso d'opera.
```

---

## 🔒 BOX LEGALE — POSIZIONI DI GARANZIA (T2 — 1×1, sfondo `#EBF5FB`)

```
🔒 Posizioni di garanzia
Art. 89-100 D.Lgs. 81/2008. I soggetti titolari di posizione di garanzia nel presente cantiere sono:
(a) Committente — Iliad Italia S.p.A.;
(b) CSP e CSE — [NOME_CSE];
(c) Impresa affidataria ex art. 89 co.1 lett. i) — Circet Italia S.p.A.;
(d) Subappaltatori esecutori: [ELENCO_SUBAPPALTATORI].
Ciascun soggetto risponde, entro il perimetro della propria posizione di garanzia, della tutela della
sicurezza dei lavoratori presenti in cantiere. La violazione degli obblighi di coordinamento e vigilanza
è sanzionata penalmente (artt. 92, 93, 157, 158, 159 D.Lgs. 81/2008).
```

---

## CAPITOLO 1 — PREMESSA

📋 *Riferimenti: art. 100 D.Lgs. 81/2008 e s.m.i. — Allegato XV*

```
Il presente Piano di Sicurezza e Coordinamento (PSC) è redatto ai sensi dell'art. 100 e
dell'Allegato XV del D.Lgs. 9 aprile 2008 n. 81 e successive modificazioni (D.Lgs. 3 agosto
2009 n. 106), in relazione al cantiere di [TIPO_INTERVENTO: installazione/adeguamento/dismissione]
dell'impianto di radiotelecomunicazioni Iliad Italia S.p.A. — Sito [CODICE_SITO] «[NOME_SITO]» —
Comune di [COMUNE] ([SIGLA_PROV]).
```

```
Il PSC contiene l'individuazione, l'analisi e la valutazione dei rischi, le procedure, gli
apprestamenti e le attrezzature necessarie per la sicurezza dei lavoratori. L'impresa appaltatrice
è tenuta a valutarne i contenuti prima della formulazione dell'offerta. Durante l'esecuzione dei
lavori risulterà la presenza di più imprese (affidataria + subappaltatrici), configurando i
presupposti dell'art. 90 D.Lgs. 81/2008.
```

```
Il PSC è documento specifico del cantiere in oggetto: ogni sezione è calibrata sui rischi,
sulle caratteristiche dell'opera (copertura a quota [QUOTA_LASTRICO]m — palina h [ALTEZZA_PALINA]m
— quota max [QUOTA_MAX]m), sulla conformazione del sito e sulle interferenze tra le imprese
presenti. Nessuna parte è ripresa da modelli standard non contestualizzati
(⚠ H.1 — Cass. Pen. n. 7421/2026: PSC standardizzato = omissione).
```

```
Normativa di riferimento: D.Lgs. 81/2008 e s.m.i.; D.Lgs. 106/2009; D.P.R. 380/2001 art. 3;
D.Lgs. 259/2003 (Codice delle Comunicazioni Elettroniche); D.M. 37/2008; D.L. 159/2025 conv.
L. 198/2025 (patente a crediti); Circ. INL n. 1/2026.
```

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

### 2.1 Caratteristiche dell'opera (T3 — 11×2)

| Campo | Valore |
|-------|--------|
| Natura dell'Opera | Civile / Impiantistica TLC |
| Oggetto | PSC (art. 100 D.Lgs. 81/08) — [CODICE_SITO] [NOME_SITO] — [TIPO_INTERVENTO] impianto SRB Roof Top |
| Titolo abilitativo | ✏ DA COMPILARE — SCIA/Autorizzazione n. ___ del ___ |
| Importo presunto dei lavori | € [IMPORTO] (stima Order Form) |
| Quota lastrico/copertura | [QUOTA_LASTRICO] m s.l. |
| Quota max palina | [QUOTA_MAX_PALINA] m s.l. (palina h = [ALTEZZA_PALINA] m) |
| Numero imprese in cantiere | [N_IMPRESE] ([ELENCO_IMPRESE]) |
| N° max lavoratori contemporanei | [N_MAX_LAV] (massimo presunto) |
| Entità presunta del lavoro | [UOMINI_GIORNO] uomini/giorno |
| Data inizio lavori | ✏ DA COMPILARE |
| Durata presunta | ~[DURATA_GG] giorni lavorativi |

**Nota**: Riga intestazione sfondo blu `#2F5496` testo bianco.

### 2.2 Soggetti per la sicurezza (T4 — 7×2)

| Ruolo | Dati |
|-------|------|
| 🏢 Committente | Iliad Italia S.p.A. — Viale Francesco Rastelli n.1/A, 20124 Milano (MI) — Referente: ✏ DA COMPILARE |
| 👤 CSP e CSE | [NOME_CSE] — [NOME_STUDIO] — [INDIRIZZO_STUDIO] — Tel. [TEL_CSE] — Ordine Ingegneri [PROV] n. [N_ORDINE] — C.F. [CF_CSE] |
| 🏗 Impresa affidataria | Circet Italia S.p.A. — Via Aterno, 108 — 66020 San Giovanni Teatino (CH) — P.IVA 01481120697 — Referente: [REFERENTE_CIRCET] |
| 🔧 Subappaltatore 1 — [SPECIALIZZAZIONE_1] | [NOME_SUB_1] — [DATI_SUB_1] |
| 🔧 Subappaltatore 2 — [SPECIALIZZAZIONE_2] | [NOME_SUB_2] — [DATI_SUB_2] |

**Nota**: Il numero di subappaltatori è variabile (tipicamente: elettrica, civile). Aggiungere/rimuovere righe in base al cantiere.

### 2.3 Numeri telefonici utili (T5 — 9×2)

| Servizio | Numero |
|----------|--------|
| Emergenza (unico europeo) | 112 |
| Pronto Soccorso / 118 | 118 |
| Carabinieri | 112 |
| Vigili del Fuoco | 115 |
| Ospedale più vicino | ✏ DA COMPILARE — [NOME_OSPEDALE] — [DISTANZA] km |
| ASL di [PROVINCIA] | [TEL_ASL] |
| CSE - [NOME_CSE] | [TEL_CSE] |
| Capocantiere Circet | ✏ DA COMPILARE |
| Referente Iliad | ✏ DA COMPILARE |

---

## CAPITOLO 3 — MODALITÀ DI GESTIONE DEL PSC

📋 *Riferimenti: artt. 92, 93 D.Lgs. 81/2008 e s.m.i.*

### 3.1 Revisione del piano

```
Il presente PSC è un documento dinamico. In caso di varianti in corso d'opera, modifiche
organizzative, introduzione di nuove tecnologie o macchine non previste, o qualsiasi modifica
che alteri il profilo di rischio, il CSE procederà all'aggiornamento tempestivo del PSC prima
dell'inizio delle nuove attività (art. 92, co. 1, lett. a, D.Lgs. 81/08).
```

### ⚠ BOX H.5 (T7 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.5 — Cass. Pen., Sez. IV, n. 24617/2025: la mancata tempestività
nell'aggiornamento del PSC a fronte di varianti che modificano il profilo di rischio configura
responsabilità penale del CSE. L'aggiornamento deve precedere l'inizio delle nuove attività.
```

### 🔒 LEGALE — Clausola aggiornamento PSC (Cap. 3.1) — da `tutela-patrimoniale-cse.md` sez. D.4

> Il presente PSC deve essere aggiornato a cura del CSE ogni qualvolta le condizioni di cantiere varino rispetto a quanto previsto (varianti progettuali, nuovi sub-appaltatori, modifica del cronoprogramma, eventi imprevedibili). Il committente/RdL è tenuto a comunicare tali variazioni per iscritto al CSE con congruo anticipo (minimo 5 giorni lavorativi prima dell'avvio delle nuove lavorazioni), al fine di consentire l'aggiornamento tempestivo del PSC.
>
> In assenza di comunicazione da parte del committente/RdL, il PSC si intende aggiornato alle sole informazioni disponibili alla data dell'ultima revisione.

### 3.2 Attività di coordinamento del CSE

```
L'attività di coordinamento del CSE comporta un obbligo di vigilanza concreto e sostanziale,
non limitato al controllo formale della documentazione. Il CSE verificherà personalmente, con
sopralluoghi di frequenza adeguata alla complessità delle lavorazioni in corso, che le previsioni
del presente PSC siano effettivamente attuate. Di ogni sopralluogo sarà redatto verbale con le
osservazioni rilevate e le eventuali prescrizioni impartite.
```

### ⚠ BOX H.4 (T8 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.4 — Cass. Pen., Sez. IV, n. 24617/2025; n. 6272/2025: il CSE è tenuto a una
vigilanza concreta e non meramente formale. La nomina del CSE non esonera il committente dai
propri obblighi. In caso di pericolo grave e imminente il CSE dispone immediatamente la
sospensione delle lavorazioni ai sensi dell'art. 92, co. 1, lett. f).
```

### ⚠ BOX H.2 (T6 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.2 — Cass. Pen., Sez. IV, n. 7414/2024: il potere-dovere di sospensione è
correlato a qualsiasi ipotesi di pericolo grave, a prescindere dalla verifica di specifiche
violazioni normative o del rischio interferenziale. L'omessa sospensione configura responsabilità
penale del CSE.
```

### 3.3 Perimetro delle funzioni del CSE

### 🔒 BOX PERIMETRO GARANZIA CSE (T9 — 1×1, sfondo `#EBF5FB`)

```
🔒 Perimetro di garanzia CSE
Il CSE esercita funzioni di alta vigilanza (non sostituisce il datore di lavoro dell'impresa).
I poteri sono: adeguamento PSC, verifica POS, riunioni coordinamento, sospensione lavori per
pericolo grave. La responsabilità per l'attuazione delle misure di sicurezza ricade sull'impresa
esecutrice e sul suo datore di lavoro (art. 96 D.Lgs. 81/2008). Il CSE non ha potere diretto
di controllo moment-by-moment sui singoli lavoratori.
```

### 3.4 Consultazione RLS

```
Prima dell'accettazione del PSC, il datore di lavoro di ciascuna impresa esecutrice consulta
il RLS e gli fornisce eventuali chiarimenti. Il RLS ha diritto di formulare proposte in merito.
La consultazione viene verbalizzata.
```

### 3.5 Riunione di coordinamento

```
Prima dell'inizio dei lavori il CSE convoca una riunione di coordinamento con i datori di lavoro
delle imprese esecutrici e i RLS. Ordine del giorno: illustrazione PSC, pianificazione
interferenze, assegnazione responsabilità DPI, verifica documenti di ingresso. Cadenza delle
riunioni successive: settimanale o al bisogno.
```

---

## CAPITOLO 4 — NOTIFICA PRELIMINARE

📋 *Riferimenti: art. 99 D.Lgs. 81/2008 e s.m.i.*

```
Il committente (Iliad Italia S.p.A.) o il Responsabile dei Lavori, prima dell'inizio dei lavori,
trasmette la Notifica Preliminare all'Azienda Sanitaria Locale e alla Direzione Provinciale del
Lavoro territorialmente competenti ([ASL_TERRITORIO] e DTL [PROVINCIA]), ai sensi dell'art. 99
D.Lgs. 81/2008.
```

### 📌 BOX NOTA (T10 — 1×1, sfondo `#F0F9FF`)

```
📌 La Notifica Preliminare è obbligatoria in quanto il cantiere prevede la presenza di più
imprese esecutrici. Copia firmata va affissa in cantiere per tutta la durata dei lavori.
```

✏ DA COMPILARE — Numero protocollo Notifica Preliminare e data invio

---

## CAPITOLO 5 — DISPOSIZIONI PER LE IMPRESE

📋 *Riferimenti: punto 2.1.2, lettera b, Allegato XV D.Lgs. 81/2008*

### 5.1 Obblighi delle imprese

```
Prima dell'inizio dei lavori, l'impresa affidataria (Circet Italia S.p.A.) trasmette il proprio
POS al CSE che ne verificherà l'idoneità sostanziale, non meramente documentale.
```

### ⚠ BOX H.3 (T11 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.3 — Cass. Pen. Sez. IV, n. 2845/2021; n. 4813: il CSE è tenuto alla verifica
sostanziale dell'idoneità del POS. L'accettazione di un POS generico o inadeguato configura
concorso di colpa del CSE in caso di infortunio. Ogni eventuale carenza dovrà essere segnalata
per iscritto con richiesta formale di adeguamento.
```

### 5.2 Patente a crediti e badge digitale

```
Ai sensi dell'art. 27 D.Lgs. 81/08 come novellato dal D.L. 159/2025 (conv. L. 198/2025),
tutte le imprese e i lavoratori autonomi operanti in cantiere devono essere titolari della
patente a crediti con punteggio minimo di 15/30 (soglia ordinaria). È vietato l'accesso al
cantiere a lavoratori privi di valida patente a crediti.

Ogni lavoratore presente in cantiere deve essere munito di tessera di riconoscimento digitale
(badge) contenente: fotografia, dati anagrafici, codice fiscale, qualifica, data di assunzione,
datore di lavoro. Il badge è obbligatorio anche per i lavoratori autonomi (D.Lgs. 81/08,
art. 26, co. 8).
```

### 5.3 Contenuti minimi del POS

```
Il POS deve contenere almeno (Allegato XV D.Lgs. 81/08): dati identificativi dell'impresa;
nominativi addetti emergenza/primo soccorso; elenco lavoratori con qualifica e formazione;
descrizione lavorazioni e organizzazione del lavoro; analisi rischi specifici; elenco DPI
forniti con dichiarazione di consegna; procedure lavori in quota con punti di ancoraggio;
piano di manutenzione attrezzature; attestati di formazione.
```

### 🔒 LEGALE — 5.4 Obblighi contrattuali in materia di sicurezza — da `contratti-appalto.md` sez. F

```
Tutte le imprese operanti nel cantiere, ivi inclusi i sub-appaltatori e i lavoratori autonomi,
sono tenute a:

a) Trasmettere al CSE il POS almeno 10 giorni prima dell'inizio delle proprie lavorazioni;
b) Non iniziare alcuna lavorazione prima della verifica di idoneità del POS da parte del CSE;
c) Comunicare al CSE ogni variazione della composizione delle squadre, delle attrezzature o
   delle modalità operative;
d) Partecipare alle riunioni di coordinamento convocate dal CSE;
e) Designare un proprio referente di cantiere reperibile durante l'orario di lavoro;
f) Rispettare le procedure di emergenza definite al Cap. 19 del PSC;
g) Affiggere all'ingresso del cantiere copia del PSC e del POS dell'impresa.
```

### 🔒 LEGALE — 5.5 Clausole contrattuali sicurezza — da `contratti-appalto.md` sez. B

> **Costi della sicurezza (art. 26 co. 5 + Allegato XV punto 4):** I costi della sicurezza previsti nel presente PSC, pari a € [COSTI_SICUREZZA], sono quantificati separatamente e NON soggetti a ribasso d'asta.
>
> **Idoneità tecnico-professionale (art. 26 co. 1 + Allegato XVII):** L'appaltatore dichiara di possedere i requisiti di idoneità tecnico-professionale.
>
> **RC obbligatoria:** L'appaltatore dichiara di essere coperto da polizza RC verso terzi e verso i lavoratori con massimale non inferiore a € 500.000 per sinistro.
>
> **Sub-appalto:** Il sub-appalto è consentito previa comunicazione scritta al committente/RdL e approvazione del CSE. L'impresa affidataria rimane solidalmente responsabile (art. 97 D.Lgs. 81/2008).

---

## CAPITOLO 6 — DESCRIZIONE DELL'OPERA

📋 *Riferimenti: punto 2.1.2, lettera a, punti 2-3, Allegato XV D.Lgs. 81/2008*

### 🔒 LEGALE — Clausola informazioni fornite dal committente (Cap. 6) — da `tutela-patrimoniale-cse.md` sez. D.3

> Le informazioni riportate nella presente sezione sono state fornite dal committente/RdL e/o estratte dalla documentazione progettuale messa a disposizione del CSP. Il CSP non risponde per l'inesattezza di tali informazioni, salvo che fossero rilevabili attraverso la normale diligenza professionale.

### 6.1 Inquadramento territoriale

```
La Stazione Radio Base Iliad Italia S.p.A. codice sito [CODICE_SITO] «[NOME_SITO]» è ubicata
nel Comune di [COMUNE] ([SIGLA_PROV]), Regione [REGIONE]. Il sito è di tipo Roof Top, su
copertura dell'edificio sito in [INDIRIZZO_CANTIERE], in zona a destinazione d'uso ✏ DA COMPILARE
(Foglio ___, Particella ___, Sez. ___).

L'edificio ospitante è [DESCRIZIONE_EDIFICIO: es. fabbricato di civile abitazione di N piani f.t.,
struttura in c.a., copertura piana praticabile con lastrico solare a quota [QUOTA_LASTRICO] m s.l.m.].

Il contesto circostante è caratterizzato da: ✏ DA COMPILARE — zona residenziale/commerciale/industriale,
vicinanza strade, distanze da edifici adiacenti, panorama verso [DIREZIONI].
```

### 6.2 Descrizione dell'infrastruttura e dell'intervento

```
Il presente PSC riguarda la [TIPO_INTERVENTO: installazione di nuovo impianto / adeguamento
dell'impianto esistente / dismissione] della SRB Iliad cod. [CODICE_SITO] in configurazione
[CONFIGURAZIONE_es: T3 — 3 Settori — 5 tecnologie]. L'impianto è collocato sulla copertura
dell'edificio a quota lastrico [QUOTA_LASTRICO] m.

L'intervento prevede:
- Allestimento cantiere in copertura e predisposizione accesso in quota
- Trasporto materiali in copertura tramite autogrù / PLE
- Realizzazione basamenti e baggioli in cls per supporto apparati
- Montaggio palina porta-antenne h [ALTEZZA_PALINA] m su baggioli
- Installazione apparati radio (RRH, FCOB, antenne settoriali)
- Posa cavi RF, fibra ottica e alimentazione
- Collegamento al quadro elettrico di sito e impianto di terra
- Collaudo funzionale e messa in servizio
- Misurazioni CEM conformi art. 210 D.Lgs. 81/08
- Finiture e smontaggio cantiere
```

### 6.3 Schede rilievo fotografico

```
Le foto seguenti documentano lo stato dei luoghi al momento del sopralluogo ([DATA_SOPRALLUOGO]).
```

> **LAYOUT FOTO**: minimo 2 foto per pagina. Ogni foto ha larghezza **7 cm** (2.76 in), disposta su 2 colonne affiancate. Didascalia sotto ciascuna foto in Calibri 8pt corsivo. Se la foto è panoramica o una planimetria, può occupare l'intera larghezza (14 cm) ma comunque max 1/2 pagina.

**Griglia foto — 2 per riga, layout a tabella invisibile 2 colonne:**

```
┌──────────────────────────┬──────────────────────────┐
│  [FOTO DA INSERIRE]      │  [FOTO DA INSERIRE]      │
│  7 cm × auto             │  7 cm × auto             │
│  Foto 1 — Vista ortofoto │  Foto 2 — Facciata edif. │
├──────────────────────────┼──────────────────────────┤
│  [FOTO DA INSERIRE]      │  [FOTO DA INSERIRE]      │
│  7 cm × auto             │  7 cm × auto             │
│  Foto 3 — Accesso copertura │  Foto 4 — Lastrico    │
├──────────────────────────┼──────────────────────────┤
│  [FOTO DA INSERIRE]      │  [FOTO DA INSERIRE]      │
│  7 cm × auto             │  7 cm × auto             │
│  Foto 5 — Area install.  │  Foto 6 — Muretto perim. │
├──────────────────────────┼──────────────────────────┤
│  [FOTO DA INSERIRE]      │  [FOTO DA INSERIRE]      │
│  7 cm × auto             │  7 cm × auto             │
│  Foto 7 — Viabilità      │  Foto 8 — Allacciamento  │
├──────────────────────────┴──────────────────────────┤
│       [FOTO DA INSERIRE — PLANIMETRIA COPERTURA]    │
│       14 cm × auto (larghezza piena)                │
│  Foto 9 — Planimetria copertura con posizionamento  │
└─────────────────────────────────────────────────────┘
```

**Implementazione .docx**: usare una tabella a **2 colonne con bordi invisibili** (no border). Ogni cella contiene l'immagine centrata + didascalia sotto. Per la planimetria (ultima riga), unire le 2 celle (merge).

**Foto obbligatorie** (minimo 8, adattare al cantiere):
1. Vista ortofoto/aerea edificio con posizionamento SRB
2. Facciata edificio e contesto urbano
3. Accesso copertura (scala, botola, torrino scala)
4. Lastrico/copertura — stato ante-operam
5. Area prevista per installazione apparati
6. Muretto perimetrale / parapetto copertura (rilievo altezza)
7. Viabilità di accesso al cantiere (strade, mezzi pesanti)
8. Punto allacciamento elettrico / cavidotto
9. Planimetria copertura con posizionamento impianto (dal PE)

> **NOTA**: le foto sono specifiche del sito e vanno inserite dall'utente o estratte dai documenti PE. Nel template .docx i placeholder grigi `[FOTO DA INSERIRE]` vengono sostituiti con le foto reali.

---

## CAPITOLO 7 — AREA DI LAVORO

📋 *Riferimenti: punto 2.1.2, lettera a, Allegato XV D.Lgs. 81/2008*

```
Il cantiere del sito [CODICE_SITO] si sviluppa su due livelli:

LIVELLO 1 — A TERRA: area di carico/scarico materiali, stazionamento autogrù/PLE, zona
deposito temporaneo. Superficie delimitata ≈ [SUPERFICIE_TERRA] mq, recintata con rete
metallica (h ≥ 200 cm) + teli ombreggianti.

LIVELLO 2 — IN COPERTURA: lastrico solare a quota [QUOTA_LASTRICO] m. Area di installazione
apparati, baggioli, palina, quadro elettrico. Accesso tramite [TIPO_ACCESSO: scala interna/
scala esterna/PLE].

La zona di caduta oggetti dall'alto (raggio min [RAGGIO_MIN] m dalla verticale del bordo
copertura) è interamente recintata a terra. Divieto di transito pedonale e veicolare nella
zona di caduta durante i lavori in quota.
```

```
Fattori ambientali: [DESCRIZIONE_FATTORI: es. zona costiera — vento prevalente da
[DIREZIONE] — velocità media [VELOCITA] m/s; presenza di SRB di altri operatori su edifici
adiacenti]. Verificare con il gestore di rete la presenza di sottoservizi prima dello scavo
(art. 100 D.Lgs. 81/08; Allegato XV pt. 2.1.3).
```

---

## CAPITOLO 8 — RISCHI INTRINSECI E FATTORI ESTERNI

📋 *Riferimenti: punto 2.2.1, Allegato XV D.Lgs. 81/2008*

### 8.1 Caratteristiche idrogeologiche

✏ DA COMPILARE — Descrivere eventuale rischio idrogeologico, caratteristiche della copertura (infiltrazioni, guaina, pendenze), portata strutturale del solaio.

### 8.2 Fattori esterni che comportano rischi per il cantiere (T14 — 6×3)

| Fattore esterno | Presenza | Misure preventive |
|-----------------|----------|-------------------|
| Linee elettriche aeree | ✏ Verificare | Mantenere distanza min. 5 m da PLE e autogrù; segnalare |
| Reti interrate (gas, acqua, TLC) | ✏ Verificare | Richiesta planimetrie enti gestori prima scavi cavidotto |
| Strade pubbliche adiacenti | ✏ Verificare | Recinzione cantiere; segnaletica D.M. 10/07/2002; OSA se necessario |
| Edifici residenziali adiacenti | ✏ Verificare | Zona di caduta recintata; protezione rumore; informativa condomini |
| Vento — zona [ZONA_VENTO] | SÌ — [DESCRIZIONE_es: zona costiera, velocità media X m/s] | Anemometro in copertura; sospensione lavori in quota con v > 6 m/s (21,6 km/h) |
| SRB adiacenti altri operatori | ✏ Verificare — [OPERATORI_ADIACENTI] | Misura CEM preventiva; segnaletica W005; coordinamento con operatori |

**Nota**: Per siti Roof Top la riga "Vento" è SEMPRE presente. Adattare intensità e direzione in base alla localizzazione geografica. La riga "SRB adiacenti" è obbligatoria per siti in co-locazione o edifici con altre SRB.

---

## CAPITOLO 9 — ORGANIZZAZIONE DEL CANTIERE

📋 *Riferimenti: punto 2.1.2, lettera c, Allegato XV D.Lgs. 81/2008 — punto 2.2.2*

### 9.1 Recinzione, accessi, segnalazioni

```
A TERRA: il cantiere sarà completamente recintato con recinzione metallica (rete + paletti,
h ≥ 200 cm) per un'area minima pari alla zona di caduta oggetti + area manovra autogrù.
L'accesso al cantiere è consentito da un unico ingresso presidiato, munito di cancello con
lucchetto. Segnaletica di accesso vietato ai non autorizzati (P006) su tutti i lati.

IN COPERTURA: accesso tramite [TIPO_ACCESSO]. Parapetto perimetrale: se muretto < 100 cm,
integrare con parapetto provvisorio EN 13374 Classe A (montanti + corrente superiore a 100 cm
+ corrente intermedio a 50 cm + tavola fermapiede h 20 cm). Segnaletica di obbligo DPI (M003,
M004, M008, M014, M015) all'uscita torrino/botola.
```

### 9.2 Impianti di cantiere

```
IMPIANTO ELETTRICO: Quadro generale di cantiere conforme CEI 64-8, sezione 704, con
interruttore generale, differenziale 30 mA e sezionatori per ogni circuito. Dichiarazione
di conformità obbligatoria (D.M. 37/2008). Messa a terra secondo DPR 462/2001.

PRESIDI IGIENICI: Bagno chimico mobile a terra. Acqua potabile disponibile.
Baraccamento/container per ricovero maestranze se durata > 5 giorni.
```

### 9.3 Aree di stoccaggio

```
I materiali saranno stoccati a terra nell'area recintata, lontano dalla zona di sollevamento.
In copertura: solo materiali necessari alla lavorazione in corso, posizionati lontano dal bordo
e ancorati contro il vento. Rifiuti e materiali dismessi in container separato (D.Lgs. 152/2006).
```

### 9.4 Coordinamento lavorazioni — rischio interferenziale

```
Il cantiere prevede la compresenza di n. [N_IMPRESE] imprese esecutrici ([ELENCO_IMPRESE]).
Le fasi di lavoro sono sequenziali per quanto possibile; quando coesistono, il CSE stabilisce
le fasce orarie e i percorsi assegnati a ciascuna impresa.
```

### ORGANIGRAMMA DI CANTIERE (tabella grafica 7×4)

```
┌───────────────────────────────────────────────────────┐
│   ORGANIGRAMMA DI CANTIERE (intestazione #1F4E79)     │
├───────────────────────────────────────────────────────┤
│  COMMITTENTE: Iliad Italia S.p.A. (sfondo #FFF2CC)    │
│  CSP/CSE: [NOME_CSE] (sfondo #BDD7EE)                │
├───────────────────────────────────────────────────────┤
│  IMPRESA AFFIDATARIA: Circet Italia S.p.A.            │
│  (sfondo #FFEB9C)                                     │
├──────────────┬────────────────────────────────────────┤
│  SUB 1       │   SUB 2                                │
│  [NOME_SUB]  │   [NOME_SUB]                           │
│ (sfondo      │  (sfondo                               │
│ #C6EFCE)     │  #C6EFCE)                              │
└──────────────┴────────────────────────────────────────┘
```

### ⚠ BOX H.6 INTERFERENZIALE (T15 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.6 — Cass. Pen. n. 23725/2023; n. 37214/2024: il PSC individua e analizza i
rischi interferenziali derivanti dalla compresenza di più imprese. Ciascuna impresa resta
responsabile dei rischi specifici propri nel suo POS. Il CSE non può ignorare situazioni di
pericolo grave macroscopicamente evidente, anche se riconducibili a rischio specifico dell'impresa.
```

### 9.5 Segnaletica di sicurezza prevista nel cantiere

📋 *Riferimenti: artt. 161-166 e Allegati XXIV-XXXII D.Lgs. 81/2008 — UNI EN ISO 7010*

### 📌 BOX NOTA SEGNALETICA (T16 — 1×1, sfondo `#F0F9FF`)

```
📌 La segnaletica va mantenuta leggibile per tutta la durata del cantiere. Verifica settimanale
integrità/leggibilità (art. 165 D.Lgs. 81/08). Cartello di cantiere obbligatorio ex D.P.R.
380/2001 (100×200 cm). La tavola cartellonistica completa è riportata in sezione dedicata dopo
le sottoscrizioni.
```

**Segnaletica tipica per cantiere TLC Roof Top (riepilogo):**

| Categoria | Segnali tipici |
|-----------|----------------|
| Prescrizione | M003 Elmetto, M004 Scarpe S3, M008 Guanti, M014 Giubbotto AV, M015 Imbracatura anticaduta |
| Pericolo | W005 CEM/radiazioni non ionizzanti, W008 Tensione elettrica, W012 Carichi sospesi, W024 Inciampo cavi |
| Divieto | P006 Vietato accesso non autorizzati, P007 Vietato veicoli non autorizzati |
| Emergenza | E003 Primo soccorso, E007 Punto raccolta |
| Antincendio | F001 Estintore |

---

## CAPITOLO 10 — SOSTANZE PERICOLOSE PRESENTI

📋 *Riferimenti: artt. 222-226 D.Lgs. 81/2008 — Reg. CE 1272/2008 (CLP)*

```
Le sostanze pericolose che potranno essere impiegate nel cantiere includono: olio per motori,
solventi per sgrassaggio, sigillanti per passanti cavi, prodotti antiossidanti per connettori,
malta cementizia per baggioli. Le SDS saranno tenute in cantiere in lingua italiana.

- Quantità limitate al fabbisogno giornaliero; eccedenze ricoverate in armadio chiuso
- In caso di sversamento: assorbimento con sabbia; smaltimento come rifiuto speciale
- Vietato fumare o usare fiamme libere nelle aree di stoccaggio prodotti chimici
```

---

## CAPITOLO 11 — ATTREZZATURE, MACCHINE E IMPIANTI

📋 *Riferimenti: artt. 70-73, 85-88 D.Lgs. 81/2008 — Allegato V — D.Lgs. 17/2010*

> **🖼️ IMMAGINE FISSA — TAVOLA ATTREZZATURE**: inserire l'immagine riepilogativa delle attrezzature di cantiere (presente nel template .docx). Questa immagine è FISSA e NON va sostituita — mostra le attrezzature tipiche con pittogrammi di sicurezza.

### Tabella attrezzature (T17 — 9×4)

| Attrezzatura | Utilizzo | Abilitazione richiesta | Verifiche |
|--------------|----------|----------------------|-----------|
| Autogrù / Autocarro con gru | Sollevamento palo, antenne, materiali | Patentino gru (All. XIV D.Lgs. 81/08) | Check-list pre-uso; libretto; verifica periodica |
| PLE (piattaforma aerea) | Accesso in quota, montaggio apparati | Patentino PLE (All. XIV) | Check-list pre-uso; cinture; portata max |
| Scala portatile | Accesso brevi (< 30 min, h < 5m) | Formazione (QT.5 INAIL) | Integrità piedini e pioli; vincolo superiore |
| Trapano / Avvitatore | Fissaggi carpenteria, tassellature | Formazione utensili | Connettori e cavi integri |
| Paranco manuale/elettrico | Sollevamento antenne e apparati | Formazione paranchi | Catena/fune e ganci; portata max |
| Saldatrice MIG/MAG | Adattamenti carpenteria metallica | Qualifica EN 1090 (se appl.) | Messa a terra; DPI saldatura |
| Generatore elettrico | Alimentazione quadro cantiere | — | Isolamento e messa a terra |
| Smerigliatrice angolare | Taglio/smerigliatura carpenteria | Formazione utensili | Disco integro; carter protezione |
| Betoniera (se baggioli in opera) | Confezionamento cls per baggioli | — | Protezione organi rotanti |

> 📌 Tutte le attrezzature con dichiarazione di conformità CE e manuale in italiano. Verifica giornaliera (INAIL — Schede macchine).

---

## CAPITOLO 12 — DISPOSITIVI DI PROTEZIONE INDIVIDUALE (DPI)

📋 *Riferimenti: artt. 74-77, 107-108 D.Lgs. 81/2008 — Reg. UE 2016/425 — QT.7 INAIL*

> **🖼️ IMMAGINE FISSA — TAVOLA DPI**: inserire l'immagine riepilogativa dei DPI obbligatori (presente nel template .docx). Questa immagine è FISSA e NON va sostituita — mostra i DPI tipici con norme EN di riferimento.

### ⚠ BOX H.7 (T19 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.7 — Cass. Pen. n. 8083/2019; n. 13590/2020; n. 47015/2022: per tutti i
lavori in quota (h > 2 m), il PSC prescrive in via prioritaria DPC. Solo in via residuale e
motivata si ricorre a DPI anticaduta III categoria. Nel presente cantiere, la PLE e il parapetto
EN 13374 costituiscono le misure collettive primarie; l'imbracatura è DPI complementare
obbligatorio e non alternativo alla PLE/parapetto.
```

```
Distanza di tiro d'aria: per imbracatura anticaduta (EN 361) + cordino dinamico (EN 355),
la distanza minima ≈ 6 m. Verificare in corrispondenza delle piattaforme intermedie e del
bordo copertura.
```

### Tabella DPI (T18 — 14×5)

| DPI | Norma | Cat. | Mansione obbligata | Frequenza verifica |
|-----|-------|------|--------------------|--------------------|
| Elmetto protezione testa | EN 397 | II | Tutti | Prima uso, mensile |
| Imbracatura anticaduta | EN 361 | III | Lavori in quota > 2 m | Prima ogni uso; annuale |
| Cordino dinamico doppio | EN 355 | III | Lavori in quota su palo/PLE/copertura | Prima ogni uso |
| Dispositivo retrattile | EN 360 | III | Piattaforme e bordo copertura | Prima ogni uso |
| Scarpe antinfort. S3 SRC | EN ISO 20345 | II | Tutti | Mensile |
| Guanti da lavoro | EN 388:2016 | II | Movimentazione materiali | Prima uso |
| Guanti isolanti elettrici | IEC 60903 Cl.0 | III | Lavori impianti elettrici | Prima uso; semestrale |
| Gilet alta visibilità | EN ISO 20471 | II | Tutti (in cantiere) | Mensile |
| Occhiali protettivi | EN 166 | II | Smerigliatura, saldatura, forature | Prima uso |
| Cuffie/tappi antirumore | EN 352-1 | II | Uso attrezzature rumorose | Prima uso |
| Maschera FFP2 | EN 149 | III | Polveri durante forature/tagli | Monouso |
| Guanti anticalore | EN 407 | II | Saldatura, taglio ossiacetilenico | Prima uso |
| Visiera saldatura | EN 175 | II | Saldatura MIG/MAG | Prima uso |
| Linea vita / Punto ancoraggio | EN 795 tipo A2 | — | Palo / struttura fissa | Annuale (certificazione) |

> 📌 Per lavori in quota su palo: obbligatorio sistema di progressione verticale certificato (EN 795 tipo A2 + connettore EN 12841 tipo A) o PLE certificata. QT.1 e QT.7 INAIL.

---

## CAPITOLO 13 — VALUTAZIONE DEL RUMORE

📋 *Riferimenti: artt. 189-192 D.Lgs. 81/2008*

> **🖼️ IMMAGINE FISSA — TAVOLA DPI ANTIRUMORE**: inserire l'immagine riepilogativa dei DPI antirumore (presente nel template .docx). Questa immagine è FISSA e NON va sostituita.

### Tabella classi esposizione (T20 — 5×3)

| Classe | Leq dB(A) | Obblighi |
|--------|-----------|----------|
| I — Sotto soglia | < 80 | Informazione generale |
| II — Tra soglie | 80–85 | Informazione/formazione; DPI disponibili |
| III — Sopra soglia | 85–87 | DPI obbligatori; sorveglianza sanitaria |
| IV — Valore limite | ≥ 87 | Divieto superamento; interventi immediati |

```
Principali sorgenti: [SORGENTI_RUMORE: es. smerigliatrice angolare (~100 dB), trapano a
percussione (~95 dB), autogrù (~80 dB)]. DPI antirumore EN 352 per lavorazioni con
attrezzature rumorose. L'impresa dovrà fornire la valutazione specifica nel POS.
```

---

## CAPITOLO 14 — SORVEGLIANZA SANITARIA

📋 *Riferimenti: artt. 41-43, 164-167 D.Lgs. 81/2008*

```
La sorveglianza sanitaria è obbligatoria per i lavoratori esposti a rischi specifici: rumore,
vibrazioni, MMC, lavori in quota, CEM. Il Medico Competente di ciascuna impresa effettua visita
preventiva, emette giudizio di idoneità alla mansione specifica (incluso lavoro in quota), e
visite periodiche.
```

> 📌 I lavoratori addetti al lavoro in quota devono essere dichiarati idonei alla mansione con specifica nota nel giudizio di idoneità del MC. Per lavori in copertura a quota > [QUOTA_LASTRICO] m: idoneità specifica per lavori in quota e assenza di controindicazioni (vertigini, patologie cardiocircolatorie).

---

## CAPITOLO 15 — RISCHI PRINCIPALI — ANALISI E PREVENZIONE

📋 *Riferimenti: punto 2.2.3, Allegato XV D.Lgs. 81/2008 — Matrice R = P × D*

```
Metodologia: R = P × D. P (Probabilità): 1=Bassa, 2=Media, 3=Alta.
D (Danno): 1=Lieve (< 15 gg), 2=Grave (> 40 gg), 3=Gravissimo (morte).
R ≥ 9: CRITICO (rosso); 6-8: ALTO (arancio); 3-5: MEDIO (giallo); 1-2: BASSO (verde).
```

### 🔒 LEGALE — Posizioni di garanzia per rischio critico — da `responsabilita-penale.md` sez. D

> Per ogni rischio con R ≥ 6 (ALTO o CRITICO), il PSC indica il titolare della posizione di garanzia:
> - **Misura DPC**: Titolare → CSE (verifica presenza); DL impresa (installazione/manutenzione)
> - **DPI residuo**: Titolare → DL impresa affidataria (fornitura e addestramento)
> - **Prescrizioni operative**: Titolare → CSE (coordinamento); Preposto impresa (esecuzione)

### RISCHI SPECIFICI TLC ROOF TOP

#### 15.1 Caduta dall'alto (rischio principale)

> **⚠ H.7** — DPC prioritari. Parapetto EN 13374 / PLE come misura collettiva principale.

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure `#FECACA` (R=9 CRITICO)

| 15.1 | Caduta dall'alto da copertura (quota [QUOTA_LASTRICO]m) e da palina (quota max [QUOTA_MAX]m) | 3 | 3 | DPC: PLE certificata per accesso in quota; parapetto EN 13374 Cl. A su bordi copertura privi di muretto ≥ 100 cm; piattaforme di lavoro fisse con parapetto su palina. DPI: imbracatura EN 361 + cordino dinamico doppio EN 355 + dispositivo retrattile EN 360. Linea vita verticale tipo A2 (QT.1 INAIL). Tirante d'aria verificato ≥ 6 m. Lavori in coppia obbligatori. Divieto salita su palina senza DPI III cat. allacciati. **GARANTE DPC**: CSE (verifica) + DL Circet (installazione). **GARANTE DPI**: DL Circet. |

#### 15.2 Caduta di materiale dall'alto

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure `#FECACA` (R=9 CRITICO)

| 15.2 | Caduta di oggetti/attrezzi/antenne dall'alto (quota [QUOTA_MAX]m) su area sottostante | 3 | 3 | Recinzione cantiere a terra raggio min [RAGGIO_MIN] m (zona caduta). Schermi orizzontali alle piattaforme. Sacchi portautensili certificati. Divieto sosta sotto carico sospeso. Paranco con fune certificata per sollevamento antenne e apparati. Segnaletica W012. **GARANTE**: CSE + DL Circet. |

#### 15.3 Elettrocuzione

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure `#FED7AA` (R=6 ALTO)

| 15.3 | Contatto con circuiti elettrici attivi / apparati sotto tensione — quadro sito | 2 | 3 | Quadro cantiere differenziale 30 mA + messa a terra (DPR 462/2001). Personale qualificato PES/PAV CEI 11-27 per lavori su quadro. Sezionamento con lucchetto. Guanti IEC 60903. Segnaletica W008 presso quadro e cavidotto. **GARANTE**: DL Circet (elettricista qualificato). |

#### 15.4 Radiazioni non ionizzanti — CEM

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure da calibrare su P e D specifici

| 15.4 | Esposizione a CEM da SRB adiacenti attive e/o durante collaudo impianto | [P] | [D] | Verifica preventiva: SRB adiacenti attive? Se SÌ: misura CEM ante-operam (art. 210 D.Lgs. 81/08). Limitare permanenza in zone con E > 20 V/m. Segnaletica W005 in copertura. Spegnimento impianti adiacenti durante lavori ravvicinati (coordinamento con operatori). Misura CEM post-attivazione per verifica limiti. **GARANTE**: CSE + DL Circet. |

#### 15.5 Movimentazione manuale di carichi

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure `#FEF9C3` (R=4 MEDIO)

| 15.5 | Sovraccarico biomeccanico rachide durante MMC (antenne, RRH, baggioli, carpenteria) | 2 | 2 | Uso autogrù/paranchi/argani per sollevamento pezzi > 25 kg. Frazionamento carichi. Formazione MMC (D.Lgs. 81/08 Titolo VI). Rotazione compiti max 2h. Antenne e RRH movimentati con ausili meccanici fino al punto di installazione. |

#### 15.6 Microclima sfavorevole — Vento

### ⚠ BOX H.8 (sfondo `#FFF5F5`, PRIMA della tabella 15.6)

```
⚠ AVVERTENZA H.8 — Orientamento Cass. Pen. 2023-2025: in caso di temperatura percepita
> 35 °C, gelo, vento forte (> 60 km/h), pioggia o scarsa visibilità, il CSE dispone la
sospensione o la rimodulazione dei lavori in quota.
```

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure `#FEF9C3` (R=4 MEDIO tipico, elevare per zone costiere/ventose)

| 15.6 | Microclima sfavorevole — vento [ZONA_es: zona costiera] — caldo/gelo | 2 | 2 | Monitoraggio previsioni meteo giornaliero. Anemometro in copertura. Sospensione lavori in quota con vento > 6 m/s (21,6 km/h). Pause ogni 2h in estate (T > 30°C). Idratazione obbligatoria. Sospensione per gelo (T < 0°C con ghiaccio). Divieto sollevamento carichi con vento > 40 km/h. **GARANTE**: CSE + Preposto Circet. |

#### 15.7 Vibrazioni

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure `#FEF9C3` (R=3 MEDIO)

| 15.7 | Vibrazioni al sistema mano-braccio (HAV) da utensili portatili | 1 | 3 | Utilizzo utensili con sistema antivibrante. Rotazione compiti. Pausa ogni 60 min. Valutazione specifica nel POS impresa. Sorveglianza sanitaria per esposizione HAV. |

#### 15.8 Scivolamenti, cadute in piano, urti

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure `#FEF9C3` (R=4 MEDIO)

| 15.8 | Scivolamento su copertura bagnata/ghiacciata; caduta in piano su cavi; urti contro strutture | 2 | 2 | Pulizia percorsi. Scarpe S3 antiscivolo. Cavi incanalati o segnalati (W024). Illuminazione notturna se necessaria. Verifica guaina copertura prima dell'accesso (umidità, ghiaccio). |

#### 15.9 Rischi interferenziali

> **FORMATO DOCX**: tabella singola riga 5 colonne, sfondo info `#F0F4F8`, sfondo misure da calibrare

| 15.9 | Interferenza tra imprese — sollevamento + lavori in quota simultanei — compresenza a terra e in copertura | [P] | [D] | Fasce orarie dedicate per impresa. Divieto compresenza sotto carico sospeso. Comunicazione radio tra terra e copertura. Riunione di coordinamento prima di ogni fase critica. Segnaletica mobile per zone temporaneamente interdette. **GARANTE**: CSE. |

> **Nota**: P e D devono essere calibrate sul cantiere specifico, MAI generiche. Motivare il valore assegnato con riferimento al PE, alle foto, alle condizioni del sito. Aggiungere rischi aggiuntivi specifici se pertinenti (es. amianto in copertura, rumore prolungato, ecc.).

---

## CAPITOLO 16 — PROGRAMMA DEI LAVORI — CRONOPROGRAMMA

📋 *Riferimenti: punto 2.1.2, lettera d, Allegato XV*

```
Durata complessiva stimata: [DURATA_GG] giorni lavorativi. Entità presunta: [UOMINI_GIORNO] uomini-giorno.
```

### Tabella cronoprogramma TLC Roof Top (T31 — 13×5)

| N° | Fase di lavoro | Durata (gg) | Op. | Note interferenziali |
|----|---------------|-------------|-----|---------------------|
| L.01 | Allestimento cantiere — recinzione, segnaletica, impianto elettrico | [GG] | [OP] | — |
| L.02 | Trasporto e sollevamento materiali in copertura (autogrù) | [GG] | [OP] | ⚠ Interferenza L.01/L.03 |
| L.03 | Realizzazione baggioli in cls e basamenti | [GG] | [OP] | — |
| L.04 | Montaggio palina porta-antenne | [GG] | [OP] | ⚠ Interferenza L.02 (autogrù) |
| L.05 | Installazione apparati radio (RRH, antenne settoriali) | [GG] | [OP] | — |
| L.06 | Posa cavi RF (jumper/feeder) | [GG] | [OP] | — |
| L.07 | Installazione FCOB e cablaggio indoor | [GG] | [OP] | — |
| L.08 | Posa fibra ottica e connettorizzazione | [GG] | [OP] | — |
| L.09 | Collaudo funzionale e messa in servizio | [GG] | [OP] | — |
| L.10 | Finiture e ripristini | [GG] | [OP] | — |
| L.11 | Smontaggio cantiere | [GG] | [OP] | — |
| L.12 | Misurazioni CEM (post-attivazione) | [GG] | [OP] | — |

```
Durata totale stimata: [DURATA_TOTALE] giorni — Uomini/giorno totali: [UD_TOTALI].
```

---

## CAPITOLO 17 — ANALISI GENERALE DEI RISCHI — MATRICE R = P × D

📋 *Riferimenti: punto 2.2, Allegato XV — INAIL 'La Progettazione della Sicurezza nel Cantiere'*

### Tabella matrice (T32 — 4×4)

| P / D | D=1 Lieve | D=2 Grave | D=3 Gravissimo |
|-------|-----------|-----------|----------------|
| P=1 Bassa | 1 — BASSO | 2 — BASSO | 3 — MEDIO |
| P=2 Media | 2 — BASSO | 4 — MEDIO | 6 — ALTO |
| P=3 Alta | 3 — MEDIO | 6 — ALTO | 9 — CRITICO |

**Colorazione**: BASSO verde `#D1FAE5`, MEDIO giallo `#FEF9C3`, ALTO arancio `#FED7AA`, CRITICO rosso `#FECACA`.

```
Fasi critiche per interferenza: L.02 (sollevamento) + L.04 (montaggio palina) + L.05 (apparati in quota).
```

---

## CAPITOLO 18 — INDIVIDUAZIONE, ANALISI E VALUTAZIONE DEI RISCHI PER FASE

📋 *Riferimenti: punto 2.2.3, Allegato XV — modello INAIL schede fase lavorativa*

### 18.1 Procedure di emergenza e coordinamento

- Viabilità interna cantiere: accesso unico controllato con segnaletica permanente
- Disponibilità presidi sanitari e numeri emergenza visibili (a terra e in copertura)
- Coordinamento imprese: riunioni settimanali CSE — datori di lavoro; verbali obbligatori
- Verifica patente a crediti e badge digitale a ogni accesso
- Controllo formazione specifica: lavori in quota, macchine, impianti elettrici, CEM
- Comunicazione terra-copertura: radio ricetrasmittenti o telefono cellulare

### 18.2 Schede fasi lavorative TLC Roof Top (T33–T37, ciascuna 7×2)

**Schede tipiche** (compilare per ogni fase del cronoprogramma):

**18.2.1 — Allestimento cantiere e accesso in copertura**

| Campo | Contenuto |
|-------|-----------|
| Descrizione attività | Recinzione area a terra, segnaletica, installazione quadro cantiere, predisposizione accesso copertura |
| Fattori di rischio | Caduta dall'alto (accesso copertura), elettrocuzione (collegamento quadro), movimentazione materiali |
| DPC | Recinzione metallica h ≥ 200 cm; parapetto EN 13374 su bordi copertura |
| DPI | Elmetto EN 397, scarpe S3, guanti EN 388, giubbotto AV EN 20471 |
| Prescrizioni operative | Accesso copertura solo con scala fissa e protezione botola; verifica quadro cantiere |
| Interferenze | Con fase L.02 (sollevamento): vietata compresenza in zona autogrù |
| Sorveglianza CSE | Sopralluogo iniziale; verifica DPC e accesso |

**18.2.2 — Sollevamento e trasporto materiali**

| Campo | Contenuto |
|-------|-----------|
| Descrizione attività | Sollevamento palo/antenne/materiali con autogrù; trasporto in copertura |
| Fattori di rischio | Caduta carichi (zona caduta), urti, ribaltamento autogrù, vento |
| DPC | Recinzione zona caduta; segnaletica W012; verifica portata autogrù |
| DPI | Elmetto, scarpe S3, guanti, giubbotto AV, imbracatura EN 361 (in copertura) |
| Prescrizioni operative | Divieto sosta sotto carico sospeso; sospensione con vento > 40 km/h; segnalatore a terra |
| Interferenze | ⚠ CRITICA: divieto compresenza fase L.03/L.04 durante sollevamento |
| Sorveglianza CSE | Presenza CSE durante sollevamento palina e antenne |

**18.2.3 — Montaggio palina e apparati radio**

| Campo | Contenuto |
|-------|-----------|
| Descrizione attività | Montaggio palina su baggioli, installazione antenne settoriali, RRH, FCOB |
| Fattori di rischio | Caduta dall'alto (palina h [ALTEZZA_PALINA]m), caduta oggetti, CEM, vento |
| DPC | PLE per montaggio; parapetto bordo copertura; ancoraggio palina |
| DPI | Imbracatura EN 361 + cordino doppio EN 355 + retrattile EN 360; elmetto; scarpe S3 |
| Prescrizioni operative | Lavoro in coppia; tirante d'aria verificato; divieto salita con vento > 6 m/s; verifica CEM se SRB adiacenti attive |
| Interferenze | Con fase L.06/L.07 (cablaggio): sequenzialità obbligatoria |
| Sorveglianza CSE | Verifica DPI III cat.; verifica ancoraggio; verbale pre-salita |

**18.2.4 — Posa cavi e fibra ottica**

| Campo | Contenuto |
|-------|-----------|
| Descrizione attività | Posa cavi RF, jumper, alimentazione, fibra ottica dal quadro alla palina |
| Fattori di rischio | Inciampo cavi, elettrocuzione (allacciamento), CEM, lavori in quota |
| DPC | Canalette e passacavi per percorso cavi; sezionamento quadro durante allacciamento |
| DPI | Guanti isolanti IEC 60903 (per allacciamento); elmetto; scarpe S3 |
| Prescrizioni operative | PES/PAV per allacciamento; cavi fissati lungo il percorso; no cavi volanti in copertura |
| Interferenze | Con fase L.05 se contemporanee: coordinamento posizioni |
| Sorveglianza CSE | Verifica qualificazione elettrica; verifica percorso cavi |

**18.2.5 — Collaudo, misurazioni CEM e smontaggio**

| Campo | Contenuto |
|-------|-----------|
| Descrizione attività | Collaudo funzionale impianto, misurazioni CEM, smontaggio cantiere, ripristini |
| Fattori di rischio | CEM (impianto in funzione), caduta dall'alto (smontaggio), traffico veicolare |
| DPC | Delimitazione area durante misurazioni CEM; segnaletica W005 |
| DPI | Elmetto, scarpe S3, guanti, giubbotto AV |
| Prescrizioni operative | Misurazioni CEM da personale qualificato; verifica limiti artt. 209-210 D.Lgs. 81/08 |
| Interferenze | — |
| Sorveglianza CSE | Verifica rapporto misurazioni CEM; verbale fine lavori |

### TABELLA INTERFERENZE (T38 — N×3, con ⚠ H.6 in riga header unificata)

Riga 0: cella unificata con ⚠ H.6 (sfondo `#FFF5F5`)

| Fasi sovrapposte | Rischio interferenziale | Misura di coordinamento CSE |
|-----------------|------------------------|---------------------------|
| L.02 + L.03 (sollevamento + baggioli) | Caduta carichi su operai a terra | Divieto compresenza; sospensione baggioli durante sollevamento |
| L.02 + L.04 (sollevamento + montaggio palina) | Caduta carichi; collisione braccio autogrù | Sequenzialità obbligatoria; segnalatore dedicato |
| L.05 + L.06 (apparati + cavi) | Caduta attrezzi; ingombro area lavoro | Fasce orarie dedicate; comunicazione radio |
| L.04 + L.12 (montaggio + CEM) | CEM su operai in quota durante attivazione | Verifica spegnimento prima dell'accesso in copertura |

---

## CAPITOLO 19 — GESTIONE DELLE EMERGENZE

📋 *Riferimenti: artt. 37-38, 43-45 D.Lgs. 81/2008 — D.M. 388/2003*

### 19.1 Presidi sanitari

- Cassetta pronto soccorso conforme D.M. 388/2003 (a terra + in copertura se > 5 operai)
- Lettino per traumatizzati e coperte isotermiche (a terra)
- DAE se ospedale > 15 minuti
- Addetto Primo Soccorso: ✏ DA COMPILARE

```
Procedura infortunio: 1) Non spostare il ferito. 2) Valutare coscienza/respirazione. 3) Contattare
118. 4) Primo soccorso da addetto formato. 5) CSE informato immediatamente. 6) Denuncia INAIL.
```

> **⚠ H.2** — In caso di pericolo grave e imminente il CSE dispone sospensione immediata.

### 19.2 Procedure specifiche TLC Roof Top

**Caduta dall'alto**: attivare 118; non spostare il ferito; comunicare posizione esatta (copertura, quota [QUOTA_LASTRICO]m); predisporre accesso VVF/118 in copertura.

**Elettrocuzione**: sezionare alimentazione dal quadro sito; non toccare l'infortunato; chiamare 118; rianimazione solo se formati BLS.

**Esposizione CEM**: allontanare immediatamente il lavoratore dalla zona di irradiazione; verifica immediata stato apparati (se accidentalmente attivati); sorveglianza sanitaria d'urgenza.

**Incendio**: usare estintore ABC/CO2; evacuare la copertura; chiamare 115; punto di raccolta a terra.

### 19.3 Condizioni meteorologiche avverse

```
Sospensione lavori in quota:
- Vento > 6 m/s (21,6 km/h) — rilevato da anemometro in copertura
- Temporali / fulmini — cessare immediatamente lavori su palina metallica
- Temperatura percepita > 35°C — turni ridotti, pause, idratazione
- Ghiaccio o neve su copertura — pulizia e verifica aderenza prima dell'accesso
- Pioggia intensa — sospensione per rischio scivolamento
- Nebbia con visibilità < 50 m
```

---

## CAPITOLO 20 — STIMA DEI COSTI DELLA SICUREZZA

📋 *Riferimenti: punto 2.3 e punto 4, Allegato XV D.Lgs. 81/2008*

### Tabella costi (T39 — 10×5)

| Voce di costo | Qta | U.M. | Costo unit. | Totale |
|--------------|-----|------|-------------|--------|
| Parapetto provvisorio EN 13374 Cl. A (noleggio/installazione bordo copertura) | [Q] | ml | € [CU] | € [TOT] |
| Imbracatura anticaduta + cordino (noleggio/dotazione) | [Q] | pz | € [CU] | € [TOT] |
| Linea vita EN 795 tipo A2 (installazione e verifica) | [Q] | cad | € [CU] | € [TOT] |
| Recinzione cantiere a terra (rete metallica h 200 cm) | [Q] | ml | € [CU] | € [TOT] |
| Segnaletica di cantiere (cartelli ISO 7010 + cartello cantiere) | 1 | set | € [CU] | € [TOT] |
| Cassetta pronto soccorso D.M. 388/2003 | 1 | cad | € [CU] | € [TOT] |
| Estintori (ABC 6 kg + CO2 5 kg) | [Q] | pz | € [CU] | € [TOT] |
| Misurazioni CEM preventive e finali | [Q] | rap | € [CU] | € [TOT] |
| Riunioni di coordinamento CSE | [Q] | ore | € [CU] | € [TOT] |
| Sopralluoghi CSE in cantiere | [Q] | ore | € [CU] | € [TOT] |
| | | | **TOTALE** | **€ [TOTALE_COSTI]** |

> 📌 Importo lavori: € [IMPORTO]. Incidenza sicurezza: [PERC]% (> 1,5% soglia minima Allegato XV). I costi della sicurezza NON sono soggetti a ribasso d'asta.

---

## CAPITOLO 21 — DOCUMENTI DA TENERE IN CANTIERE

📋 *Riferimenti: art. 107, Allegato XV D.Lgs. 81/2008*

- 21.1 — PSC e aggiornamenti
- 21.2 — POS di tutte le imprese (Circet + subappaltatori)
- 21.3 — Notifica Preliminare protocollata
- 21.4 — Nominativi e contatti: CSP, CSE, DL, RSPP, RLS, MC
- 21.5 — Patente a crediti (visura aggiornata)
- 21.6 — Registro presenze giornaliero con badge digitali
- 21.7 — SDS sostanze pericolose
- 21.8 — Dichiarazioni CE e manuali d'uso attrezzature
- 21.9 — Certificati linea vita / sistemi anticaduta (EN 795)
- 21.10 — Certificati taratura equipaggiamenti sollevamento (autogrù, PLE)
- 21.11 — Schede tecniche imbracature, cordini, moschettoni
- 21.12 — Attestati formazione (lavori in quota, PLE, impianti elettrici, CEM)
- 21.13 — Verbali riunioni di coordinamento CSE
- 21.14 — Verbali sopralluoghi CSE
- 21.15 — Relazioni misurazioni CEM preventive e finali
- 21.16 — Rapporti misurazioni rumore (se applicabile)
- 21.17 — Moduli segnalazione near miss (All. 7)
- 21.18 — DURC in corso di validità di tutte le imprese
- 21.19 — Titolo abilitativo e cartello di cantiere obbligatorio
- 21.20 — Progetto Esecutivo (PE) con elaborati grafici e strutturali

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

## SOTTOSCRIZIONI — ACCETTAZIONE DEL PIANO (T40 — 2×2)

| 🛡 IL COORDINATORE PER LA SICUREZZA (CSP e CSE) | 🏢 IL COMMITTENTE |
|---|---|
| [NOME_CSE] | Iliad Italia S.p.A. |
| [NOME_STUDIO] | ✏ DA COMPILARE: referente Iliad |
| Ordine Ingegneri [PROV] Sez. A n. [N_ORDINE] | |
| _______________________________ | _______________________________ |
| Firma e Timbro | Firma e Timbro |

| 🏗 L'IMPRESA AFFIDATARIA | 🔧 IMPRESA SUBAPPALTATRICE |
|---|---|
| Circet Italia S.p.A. | [ELENCO_SUBAPPALTATORI] |
| [REFERENTE_CIRCET] | ✏ DA COMPILARE: nome referente |
| _______________________________ | _______________________________ |
| Firma e Timbro | Firma e Timbro |

### 📌 BOX NOTA PSC (T41 — 1×1, sfondo `#F0F9FF`)

```
📌 Copia del presente PSC, debitamente sottoscritta da tutte le imprese, deve essere tenuta in
cantiere per tutta la durata dei lavori. Il POS deve essere consegnato al CSE prima dell'inizio
delle lavorazioni di ciascuna impresa (art. 96, co. 1, lett. g, D.Lgs. 81/08).
```

---

## ─── TAVOLA CARTELLONISTICA ───

**Heading 1**: `TAVOLA CARTELLONISTICA`

📋 *Riferimenti: artt. 161-166 e Allegati XXIV-XXXII D.Lgs. 81/2008 — UNI EN ISO 7010*

> **🖼️ IMMAGINI FISSE — SEGNALETICA ISO 7010**: per ogni categoria è presente nel template .docx un'immagine riepilogativa dei pittogrammi pertinenti. Queste immagini sono FISSE nel template e NON vanno sostituite. Sono le tavole visive di riferimento per la segnaletica di cantiere.

### Cartelli di PRESCRIZIONE (M — Fondo Blu, simbolo Bianco) (T42)

> 🖼️ immagine fissa pittogrammi Prescrizione

| Pittogramma | Tipo Segnale | Esposizione nel Cantiere |
|-------------|-------------|--------------------------|
| [IMG_M003] | M003 — Protezione obbligatoria del capo (elmetto) [All. XXIV-XXV D.Lgs. 81/08] | Ingresso cantiere, accesso copertura, zona palina |
| [IMG_M004] | M004 — Protezione obbligatoria dei piedi (scarpe S3) [All. XXIV-XXV] | Ingresso cantiere |
| [IMG_M008] | M008 — Protezione obbligatoria delle mani (guanti EN 388) [All. XXIV-XXV] | Zona movimentazione materiali |
| [IMG_M014] | M014 — Giubbotto ad alta visibilità (EN ISO 20471) [All. XXIV-XXV] | Area cantiere a terra, zona autogrù |
| [IMG_M015] | M015 — Imbracatura di sicurezza anticaduta (EN 361) [All. XXIV-XXV; art. 115 D.Lgs. 81/08] | Accesso copertura, palina, bordi copertura |

### Cartelli di PERICOLO (W — Fondo Giallo, bordo/simbolo Nero) (T43)

> 🖼️ immagine fissa pittogrammi Pericolo

| Pittogramma | Tipo Segnale | Esposizione nel Cantiere |
|-------------|-------------|--------------------------|
| [IMG_W005] | W005 — Pericolo radiazioni non ionizzanti (CEM) [art. 209 D.Lgs. 81/08; ISO 7010] | Copertura, in prossimità antenne SRB adiacenti attive |
| [IMG_W008] | W008 — Pericolo elettrico / tensione pericolosa [All. XXIV-XXV D.Lgs. 81/08] | Quadro elettrico sito, cavidotto |
| [IMG_W012] | W012 — Pericolo carichi sospesi [All. XXIV-XXV D.Lgs. 81/08] | Zona sottostante autogrù, zona sollevamento |
| [IMG_W024] | W024 — Pericolo inciampo (cavi a terra) [ISO 7010] | Copertura lungo percorso cavi, area cantiere |

### Cartelli di DIVIETO (P — Fondo Bianco, bordo/barra Rossi) (T44)

> 🖼️ immagine fissa pittogrammi Divieto

| Pittogramma | Tipo Segnale | Esposizione nel Cantiere |
|-------------|-------------|--------------------------|
| [IMG_P006] | P006 — Vietato l'accesso ai non autorizzati [art. 163 D.Lgs. 81/08; ISO 7010] | Ingresso cantiere a terra, accesso copertura |
| [IMG_P007] | P007 — Vietato ai veicoli di movimentazione merci [ISO 7010] | Area pedonale cantiere |

### Cartelli di EVACUAZIONE / SALVATAGGIO (E — Fondo Verde, simbolo Bianco) (T45)

> 🖼️ immagine fissa pittogrammi Emergenza

| Pittogramma | Tipo Segnale | Esposizione nel Cantiere |
|-------------|-------------|--------------------------|
| [IMG_E003] | E003 — Primo soccorso [Allegati XXIV-XXV D.Lgs. 81/08] | Baraccamento cantiere, copertura |
| [IMG_E007] | E007 — Punto di raccolta [ISO 7010] | Area a terra, lontano da zona caduta |

### Cartelli di ANTINCENDIO (F — Fondo Rosso, simbolo Bianco)

| Pittogramma | Tipo Segnale | Esposizione nel Cantiere |
|-------------|-------------|--------------------------|
| [IMG_F001] | F001 — Estintore [Allegati XXIV-XXV D.Lgs. 81/08] | Baraccamento, quadro elettrico, copertura |

---

## ALLEGATO 1 — ELENCO LAVORAZIONI (T46 — 13×5)

**Heading 1**: `ALLEGATO 1 — ELENCO LAVORAZIONI`

📋 *Rif.: punto 2.1.2, Allegato XV D.Lgs. 81/2008 — cronoprogramma Cap. 16 e schede 18.2*

| Cod. | Lavorazione | Descrizione sintetica | Impresa | Durata |
|------|-------------|----------------------|---------|--------|
| L.01 | Allestimento cantiere | Recinzione, segnaletica, quadro cantiere, accesso copertura | Circet | [DURATA] gg |
| L.02 | Trasporto e sollevamento | Sollevamento materiali con autogrù in copertura | Circet | [DURATA] gg |
| L.03 | Baggioli e basamenti | Realizzazione baggioli in cls per supporto palina e apparati | Circet / [SUB] | [DURATA] gg |
| L.04 | Montaggio palina | Assemblaggio e innalzamento palina h [ALTEZZA_PALINA] m | Circet | [DURATA] gg |
| L.05 | Installazione apparati | Montaggio antenne settoriali, RRH, [APPARATI_SPECIFICI] | Circet | [DURATA] gg |
| L.06 | Posa cavi RF | Jumper, feeder, cavi alimentazione | Circet | [DURATA] gg |
| L.07 | FCOB e cablaggio indoor | Installazione FCOB, NodeBox, cablaggio interno | Circet | [DURATA] gg |
| L.08 | Fibra ottica | Posa FO, connettorizzazione, test OTDR | Circet / [SUB] | [DURATA] gg |
| L.09 | Collaudo | Test funzionale, messa in servizio | Circet | [DURATA] gg |
| L.10 | Finiture | Ripristini copertura, pulizia | Circet | [DURATA] gg |
| L.11 | Smontaggio cantiere | Rimozione recinzione, segnaletica, pulizia area | Circet | [DURATA] gg |
| L.12 | Misurazioni CEM | Misure campo elettromagnetico post-attivazione | [TECNICO_CEM] | [DURATA] gg |

---

## ALLEGATO 2 — CRONOPROGRAMMA DEI LAVORI (T47 — 13×11)

**Heading 1**: `ALLEGATO 2 — CRONOPROGRAMMA DEI LAVORI`

📋 *Rif.: punto 2.1.2, lettera d, Allegato XV — Diagramma di Gantt*

Tabella Gantt con colonne: `Fase | Impresa | G1 | G2 | G3 | G4 | G5 | G6 | G7 | G8 | G9`

Dove Gn = giornata lavorativa. Celle colorate per impresa:
- `#FFEB9C` (giallo) = Circet Italia (affidataria)
- `#C6EFCE` (verde) = Subappaltatore 1 (es. elettrica)
- `#BDD7EE` (azzurro) = Subappaltatore 2 (es. civile)
- `#D6DCE4` (grigio) = Tecnico misure CEM

```
Legenda: ▓ giallo = Circet — ▓ verde = [SUB_1] — ▓ azzurro = [SUB_2] — ▓ grigio = CEM

Fasi critiche per interferenza: L.02+L.03 (sollevamento+baggioli); L.02+L.04 (sollevamento+palina).
```

---

## ALLEGATO 3 — LAYOUT PLANIMETRICO DEL CANTIERE

**Heading 1**: `ALLEGATO 3 — LAYOUT PLANIMETRICO DEL CANTIERE`

```
Il layout planimetrico del cantiere è rappresentato negli elaborati grafici del PE
(rif. [RIF_PE] — tavola planimetria copertura e sezione). Di seguito si descrivono gli
elementi di cantiere con il relativo posizionamento:

A TERRA:
- Area recinzione: perimetro [DIMENSIONI] m, altezza rete 200 cm
- Ingresso cantiere: lato [LATO], cancello con lucchetto
- Stazionamento autogrù: posizione [POSIZIONE]
- Area stoccaggio materiali: [POSIZIONE]
- Bagno chimico: [POSIZIONE]
- Cassetta PS + estintore: [POSIZIONE]

IN COPERTURA:
- Accesso: [TIPO_ACCESSO] — [POSIZIONE]
- Palina: posizione [POSIZIONE], orientamento [ORIENTAMENTO]
- Baggioli: n. [N_BAGGIOLI], posizioni [POSIZIONI]
- Quadro elettrico sito: [POSIZIONE]
- Percorso cavi: [DESCRIZIONE_PERCORSO]
- Parapetto provvisorio EN 13374: lati [LATI] (dove muretto < 100 cm)
```

---

## ALLEGATO 4 — FASCICOLO DELL'OPERA

**Heading 1**: `ALLEGATO 4 — FASCICOLO DELL'OPERA`

```
(ai sensi dell'art. 91, comma 1, lett. b, D.Lgs. 81/2008 — Allegato XVI)
Il presente Fascicolo dell'Opera contiene le informazioni utili ai fini della prevenzione e della
protezione dai rischi cui sono esposti i lavoratori che interverranno successivamente sull'opera
per lavori di manutenzione o adeguamento della SRB.
```

### Scheda I — Descrizione sintetica dell'opera (T48 — 9×3)

| Elemento | Descrizione | Note |
|----------|-------------|------|
| Ubicazione | [INDIRIZZO] — [COMUNE] ([PROV]) | Copertura edificio — Foglio [F] Part. [P] |
| Tipo intervento | [TIPO_INTERVENTO] SRB Iliad [CODICE_SITO] | Configurazione [CONFIG] |
| Struttura ospitante | Edificio [TIPO_EDIFICIO], [N_PIANI] piani f.t. | Copertura piana a quota [QUOTA]m |
| Struttura SRB | Palina h [ALTEZZA_PALINA]m su baggioli cls | Quota max [QUOTA_MAX]m |
| Apparati installati | [ELENCO_APPARATI: antenne, RRH, FCOB, NodeBox] | Tecnologie: [TECNOLOGIE] |
| Impianti | Elettrico (quadro sito) + terra + FO | D.M. 37/2008 |
| Durata lavori | [DURATA] giorni | [DATA_INIZIO] – [DATA_FINE] |
| Imprese | Circet Italia S.p.A. + [SUBAPPALTATORI] | |
| Note | [NOTE_PARTICOLARI] | |

### Scheda II — Rischi manutenzione (T49 — 8×2 + T50 — 7×4)

**T49** (descrittiva):

| Voce | Descrizione |
|------|-------------|
| Tipologia interventi futuri | Manutenzione ordinaria (sostituzione apparati, antenne), adeguamento tecnologico (UP5G), dismissione |
| Rischi principali | Caduta dall'alto (copertura e palina), CEM (impianto attivo), elettrocuzione (quadro), vento |
| Accesso ai luoghi | [TIPO_ACCESSO] — scala interna/esterna edificio + botola/porta copertura |
| Misure preventive in dotazione | Parapetto perimetrale (se installato fisso); punti ancoraggio EN 795 su palina |
| Attrezzature necessarie | PLE o scala + imbracatura; attrezzi manuali; strumenti misura CEM |
| DPI necessari | Imbracatura EN 361, cordino EN 355, elmetto EN 397, scarpe S3, guanti |
| Frequenza interventi prevista | Ordinaria: semestrale; Straordinaria: al bisogno |

**T50** (matrice rischi manutenzione 7×4):

| Rischio da manutenzione | Misura preventiva | Dotazione opera | Frequenza intervento |
|------------------------|-------------------|----------------|---------------------|
| Caduta dall'alto da copertura | Parapetto perimetrale (se fisso) | Punti ancoraggio EN 795 su palina | Ogni intervento |
| Caduta dall'alto da palina | Imbracatura + linea vita verticale | Linea vita EN 795 tipo A2 | Ogni intervento |
| Esposizione CEM | Spegnimento settori interessati | Procedure operative Iliad | Ogni intervento |
| Elettrocuzione | Sezionamento quadro | Interruttore generale con lucchetto | Ogni intervento |
| Caduta materiali dall'alto | Delimitazione area sottostante | Recinzione fissa (se presente) | Ogni intervento |
| Vento | Verifica meteo + anemometro | Anemometro in copertura (se installato) | Ogni intervento |

### Scheda III — Documentazione (T51 — 8×3)

| Documento | Ubicazione/Archivio | Contenuto rilevante |
|-----------|--------------------|--------------------|
| Progetto Esecutivo (PE) | Iliad / Circet | Planimetrie, carpenteria, schema elettrico |
| DdC impianto elettrico D.M. 37/08 | Circet / Iliad | Conformità quadro sito |
| DdC impianto di terra | Circet / Iliad | Rete di terra + dispersori |
| Relazione misurazioni CEM | Iliad | Valori campo EM post-attivazione |
| PSC (presente documento) | CSE / Iliad | Rischi e prescrizioni cantiere |
| POS imprese | CSE / Iliad | Piani operativi |
| Certificato strutturale palina | Fornitore | Verifica statica + idoneità |
| Fascicolo manutenzione palina | CSE / Iliad | Piano manutenzione struttura |

```
Il Fascicolo dell'Opera deve essere aggiornato dal committente (Iliad) in occasione di ogni
intervento di manutenzione o adeguamento successivo.
```

---

## ALLEGATO 5 — CHECK-LIST MACCHINE E ATTREZZATURE (T52 — 10×8)

**Heading 1**: `ALLEGATO 5 — CHECK-LIST MACCHINE E ATTREZZATURE`

📋 *Rif.: artt. 70-73 D.Lgs. 81/2008 — Allegato V — D.Lgs. 17/2010 (Direttiva Macchine)*

```
La seguente check-list deve essere compilata dall'impresa affidataria prima dell'utilizzo di
ciascuna attrezzatura in cantiere e conservata per tutta la durata dei lavori.
```

| Attrezzatura | Marca/Modello | Matr./ID | Marcatura CE | Libretto uso | Manutenz. in corso | Operatore formato | Conforme |
|---|---|---|---|---|---|---|---|
| Autogrù | | | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| PLE | | | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| Trapano / Avvitatore | | | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| Smerigliatrice | | | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| Paranco | | | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| Saldatrice | | | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| Generatore | | | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| Betoniera | | | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| [ALTRA_ATTREZZATURA] | | | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |

```
Compilata da: ________________________________  Data: ___/___/______  Firma: ________________________________
Verificata dal CSE: ________________________________  Data: ___/___/______  Firma: ________________________________
```

---

## ALLEGATO 6 — CALCOLO UOMINI-GIORNO (T53 — 14×5)

**Heading 1**: `ALLEGATO 6 — CALCOLO UOMINI-GIORNO`

📋 *Rif.: art. 89, comma 1, lett. g, D.Lgs. 81/2008 — punto 2.1.2, Allegato XV*

```
L'entità presunta del cantiere è espressa in uomini-giorno ed è calcolata come somma delle
giornate lavorative prestate dai lavoratori, anche autonomi, previste per la realizzazione
dell'opera.
```

| Fase | Lavorazione | N° operai | Durata (gg) | Uomini-giorno |
|------|-------------|-----------|-------------|---------------|
| L.01 | Allestimento cantiere | [N] | [GG] | [UG] |
| L.02 | Trasporto e sollevamento | [N] | [GG] | [UG] |
| L.03 | Baggioli e basamenti | [N] | [GG] | [UG] |
| L.04 | Montaggio palina | [N] | [GG] | [UG] |
| L.05 | Installazione apparati | [N] | [GG] | [UG] |
| L.06 | Posa cavi RF | [N] | [GG] | [UG] |
| L.07 | FCOB e cablaggio indoor | [N] | [GG] | [UG] |
| L.08 | Fibra ottica | [N] | [GG] | [UG] |
| L.09 | Collaudo | [N] | [GG] | [UG] |
| L.10 | Finiture | [N] | [GG] | [UG] |
| L.11 | Smontaggio cantiere | [N] | [GG] | [UG] |
| L.12 | Misurazioni CEM | [N] | [GG] | [UG] |
| | **TOTALE** | | | **[TOTALE_UG]** |

```
Entità presunta del cantiere: [TOTALE_UG] uomini-giorno.
Valore [< / ≥] 200 uomini-giorno → [NOTA_NOTIFICA_PRELIMINARE].
```

---

## ALLEGATO 7 — MODULO SEGNALAZIONE NEAR MISS / MANCATO INFORTUNIO (T54 — 12×2)

**Heading 1**: `ALLEGATO 7 — MODULO SEGNALAZIONE NEAR MISS / MANCATO INFORTUNIO`

📋 *Rif.: art. 20 D.Lgs. 81/2008 — Linea Guida INAIL 'Gestione dei near miss'*

```
Il presente modulo deve essere compilato da qualsiasi lavoratore presente in cantiere in caso
di evento che, pur non avendo causato lesioni, avrebbe potuto provocarle (near miss / mancato
infortunio). La segnalazione è anonimizzabile su richiesta.
```

| Campo | Compilazione |
|-------|-------------|
| Data e ora evento | ___/___/______ ore ___:___ |
| Luogo esatto | ☐ Area a terra ☐ Copertura ☐ Scale accesso ☐ Zona palina ☐ Zona autogrù ☐ Altro: ____________ |
| Fase lavorativa in corso | |
| Descrizione sintetica dell'evento | |
| Persone coinvolte (nomi e impresa) | |
| Persone testimoni | |
| Possibili cause | ☐ Caduta oggetti ☐ Scivolamento ☐ Caduta dall'alto ☐ Contatto elettrico ☐ CEM ☐ Vento ☐ Urto ☐ Altro: ____________ |
| DPI indossati al momento | ☐ Elmetto ☐ Imbracatura ☐ Scarpe S3 ☐ Guanti ☐ Giubbotto AV ☐ Altro: ____________ |
| Gravità potenziale | ☐ Lieve ☐ Moderata ☐ Grave ☐ Molto grave |
| Azioni immediate intraprese | |
| Azioni correttive proposte | |

```
Segnalante: ________________________________  Qualifica: ________________________________
Impresa: ________________________________  Data compilazione: ___/___/______
Firma: ________________________________

RICEZIONE CSE
Data ricezione: ___/___/______  Protocollo n.: ____________
Azioni disposte dal CSE: ________________________________
Firma CSE: ________________________________  Data: ___/___/______
```

---

## 🔒 APPENDICE LEGALE — CHECKLIST PRE-CONSEGNA

### Checklist F.1 — Completezza documentale

- [ ] Frontespizio compilato con tutti i dati (codice sito, tecnologie, PE, revisione)
- [ ] Box ⚠ H.1 (specificità PSC) presente dopo frontespizio
- [ ] Box 🔒 Posizioni di garanzia con nomi corretti
- [ ] Tabella caratteristiche opera (T3) completa con quota lastrico e palina
- [ ] Tabella soggetti sicurezza (T4) completa con DURC verificato
- [ ] Numeri telefonici utili aggiornati e localizzati (ospedale, ASL, CSE)
- [ ] Foto ante-operam inserite (min. 8 foto: ortofoto, edificio, accesso copertura, lastrico, area installazione, muretto, viabilità, allacciamento + planimetria)
- [ ] Tutti i rischi con P e D motivate dal cantiere specifico (NON generici)
- [ ] Rischio CEM calibrato sulla presenza/assenza SRB adiacenti
- [ ] Rischio vento calibrato sulla zona geografica
- [ ] Cronoprogramma coerente con elenco lavorazioni (12 fasi TLC)
- [ ] Schede fase lavorativa compilate per ogni fase
- [ ] Tabella interferenze compilata con misure specifiche
- [ ] Costi sicurezza calcolati e coerenti (parapetto EN 13374, imbracature, misurazioni CEM)
- [ ] Tutti i 7 allegati sviluppati (non solo elencati)
- [ ] TAVOLA CARTELLONISTICA con pittogrammi (dopo sottoscrizioni)
- [ ] Sottoscrizioni con tutti i soggetti (CSE, Iliad, Circet, subappaltatori)
- [ ] Fascicolo dell'Opera completo (3 schede)

### Checklist F.3 — Conformità normativa e difensiva

- [ ] ⚠ H.1 (PSC specifico) → dopo frontespizio
- [ ] ⚠ H.2 (sospensione lavori) → integrato in Cap. 3
- [ ] ⚠ H.3 (verifica POS) → integrato in Cap. 5
- [ ] ⚠ H.4 (alta vigilanza) → integrato in Cap. 3.2
- [ ] ⚠ H.5 (aggiornamento PSC) → integrato in Cap. 3.1
- [ ] ⚠ H.6 (interferenziale) → integrato in Cap. 9.4 e Cap. 18
- [ ] ⚠ H.7 (DPC > DPI) → integrato in Cap. 12
- [ ] ⚠ H.8 (microclima/vento) → integrato in Cap. 15.6
- [ ] 🔒 Posizioni di garanzia → T2
- [ ] 🔒 Perimetro CSE → T9
- [ ] 🔒 Clausole contrattuali → T12
- [ ] 🔒 Informazioni committente → T13
- [ ] Nessun placeholder `[DA COMPILARE]` residuo non intenzionale
