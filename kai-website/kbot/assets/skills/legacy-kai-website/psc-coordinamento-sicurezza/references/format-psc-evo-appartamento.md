# FORMAT PSC EVO APPARTAMENTO — Template Completo con Integrazione Legale

> **ISTRUZIONI PER L'USO**: Questo file contiene la struttura esatta e il testo standard di ogni sezione del PSC EVO per ristrutturazione interna di appartamento (CILA/SCIA). Per ogni nuovo PSC:
> 1. Copia l'intera struttura
> 2. Sostituisci tutti i placeholder `[PLACEHOLDER]` con i dati del cantiere specifico
> 3. Adatta i rischi e le schede fase lavorativa al tipo di intervento (ristrutturazione interna, bagni, cucina, impianti, infissi, ecc.)
> 4. Le sezioni marcate con 🔒 LEGALE contengono clausole difensive obbligatorie — NON rimuoverle mai
> 5. Le sezioni marcate con ⚠ AVVERTENZA H.x contengono warning giurisprudenziali Cassazione Penale — NON rimuoverle mai
> 6. Esegui le checklist F.1 e F.3 (in fondo al documento) prima della consegna
>
> **VARIANTE**: Questo format è specifico per cantieri di **ristrutturazione interna appartamento** in condominio (CILA art. 6-bis DPR 380/2001 o SCIA). Per cantieri TLC/SRB usare `format-psc-k2a-legale.md`.

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
> **B. WARNING, NOTE e CLAUSOLE LEGALI** — Formato "box singola cella":
> - Avvertenze (⚠ H.x): tabella 1×1, sfondo `#FFF5F5`, testo 9pt, codice in bold rosso `#C00000`
> - Note (📌): tabella 1×1, sfondo `#F0F9FF`, testo 9pt
> - Clausole legali (🔒): tabella 1×1, sfondo `#EBF5FB`, titolo bold blu `#1F4E79`
>
> **C. ORGANIGRAMMA** — Formato "tabella grafica colorata":
> - Tabella 7 righe × 4 colonne con celle colorate per ruolo
> - Colori: `#1F4E79` (CSE, intestazione), `#2E75B6` (Committente), `#C00000` (Impresa appaltatrice)
> - Sfondo box: `#FFF2CC` (Committente), `#FFEB9C` (Appaltatrice), `#C6EFCE` (Subappaltatori), `#BDD7EE` (CSE)
> - Testo centrato in ogni cella, nomi in bold
>
> **D. SOTTOSCRIZIONI** — Formato "griglia 2×2":
> - Tabella 2 righe × 2 colonne (CSE | Committente / Affidataria | Subappaltatrice)
> - Con emoji ruolo (🛡, 🏢, 🏗, 🔧)
>
> **E. ALLEGATI** — Devono essere SVILUPPATI in calce al documento, non solo elencati:
> - Allegato 1: tabella completa lavorazioni 13×5 (Cod. | Lavorazione | Descrizione | Impresa | Durata)
> - Allegato 2: cronoprogramma Gantt testuale (tabella con celle colorate per impresa)
> - Allegato 3: layout planimetrico (descrizione testuale con riferimento tavole CILA)
> - Allegato 4: Fascicolo dell'Opera completo (3 Schede: I descrizione, II rischi manutenzione, III documentazione)
> - Allegato 5: check-list macchine compilabile (10×8, caselle ☐ Sì ☐ No)
> - Allegato 6: calcolo uomini-giorno in tabella (14×5)
> - Allegato 7: modulo near miss compilabile (12×2)
>
> **F. GESTIONE IMMAGINI**:
> 
> Le immagini nel PSC si dividono in due categorie:
> 
> **IMMAGINI FISSE (da template — NON sostituire mai):**
> - `image15.png` → Cartello di cantiere tipo (Cap. 9.1)
> - `image17` → Segnaletica PRESCRIZIONE ISO 7010 (Cap. 9.5)
> - `image18` → Segnaletica PERICOLO ISO 7010 (Cap. 9.5)
> - `image19` → Segnaletica DIVIETO ISO 7010 (Cap. 9.5)
> - `image20` → Segnaletica EMERGENZA ISO 7010 (Cap. 9.5)
> - `image21` → Segnaletica ANTINCENDIO ISO 7010 (Cap. 9.5)
> - `image22` → Tavola attrezzature e DPI (Cap. 11 e Cap. 12)
> - `image23` → Tavola DPI antirumore (Cap. 13)
> 
> **FOTO CANTIERE (placeholder — da inserire per ogni progetto):**
> - Cap. 6.3: minimo 7 foto ante-operam + pianta
> - Layout: **almeno 2 foto per pagina**, disposte su 2 colonne affiancate (7 cm ciascuna)
> - Usare tabella invisibile (no border) 2 colonne per il layout
> - Pianta/planimetria: larghezza piena (14 cm), celle unite
> - Didascalia sotto ogni foto: Calibri 8pt corsivo
> - Placeholder nel template: `[FOTO DA INSERIRE]` con box grigio chiaro `#F2F2F2`
>
> **G. IMPOSTAZIONI GENERALI DOCX**:
> - Margini: 2.5 cm per tutti i lati
> - Font corpo testo: Calibri 11pt, interlinea 1.15, colore `#333333`
> - Font titoli capitolo (Heading 1): Calibri Bold 14pt, colore blu `#2F5496`
> - Font sottotitoli (Heading 2): Calibri Bold 12pt, colore blu `#2F5496`
> - Font tabelle: Calibri 9pt
> - Piè di pagina: "PSC — [INDIRIZZO_CANTIERE] — [NOME_STUDIO] — [NOME_CSE]", centrato, Calibri 7pt grigio `#808080`
> - Interruzione di pagina: prima di ogni capitolo principale (1–22) e prima degli allegati

---

## STRUTTURA DOCUMENTO — 22 CAPITOLI + 7 ALLEGATI

```
FRONTESPIZIO (T0 — 10×2)
BOX LEGALE POSIZIONI DI GARANZIA (T1 — 1×1)
SOMMARIO
CAPITOLO 1 — PREMESSA
CAPITOLO 2 — ANAGRAFICA DI CANTIERE
  2.1 Caratteristiche dell'opera (T2 — 11×2)
  2.2 Soggetti per la sicurezza (T3 — 7×2)
  2.3 Numeri telefonici utili (T4 — 9×2)
CAPITOLO 3 — MODALITÀ DI GESTIONE DEL PSC
  3.1 Revisione del piano
  ⚠ BOX H.2 (T5 — 1×1)
  3.2 Attività di coordinamento del CSE
  3.3 Perimetro delle funzioni del CSE
  🔒 BOX PERIMETRO GARANZIA CSE (T6 — 1×1)
  3.4 Consultazione RLS
  3.5 Riunione di coordinamento
CAPITOLO 4 — NOTIFICA PRELIMINARE
  📌 BOX NOTA (T7 — 1×1)
CAPITOLO 5 — DISPOSIZIONI PER LE IMPRESE
  5.1 Obblighi delle imprese
  5.2 Patente a crediti e badge digitale
  5.3 Contenuti minimi del POS
  5.4 Obblighi contrattuali di sicurezza
CAPITOLO 6 — DESCRIZIONE DELL'OPERA
  6.1 Inquadramento territoriale
  6.2 Descrizione dell'intervento
  6.3 Schede rilievo fotografico (foto ante-operam + piante)
CAPITOLO 7 — AREA DI LAVORO
CAPITOLO 8 — RISCHI INTRINSECI E FATTORI ESTERNI
  8.1 Caratteristiche idrogeologiche
  8.2 Fattori esterni (T8 — 6×3)
CAPITOLO 9 — ORGANIZZAZIONE DEL CANTIERE
  9.1 Recinzione, accessi, segnalazioni
  ⚠ BOX H.6 INTERFERENZIALE (T9 — 1×1)
  9.2 Impianti di cantiere
  9.3 Aree di stoccaggio
  9.4 Coordinamento lavorazioni — rischio interferenziale
      ORGANIGRAMMA DI CANTIERE (tabella grafica 7×4)
  9.5 Segnaletica di sicurezza (📌 BOX T10 — 1×1)
      Tabelle segnaletica per categoria (Prescrizione, Pericolo, Divieto, Emergenza, Antincendio)
CAPITOLO 10 — SOSTANZE PERICOLOSE
CAPITOLO 11 — ATTREZZATURE, MACCHINE E IMPIANTI
CAPITOLO 12 — DPI
  ⚠ BOX H.7 DPC > DPI (T11 — 1×1)
CAPITOLO 13 — VALUTAZIONE DEL RUMORE (T12 — 5×3)
CAPITOLO 14 — SORVEGLIANZA SANITARIA
CAPITOLO 15 — RISCHI PRINCIPALI — ANALISI E PREVENZIONE
  15.1–15.9 Schede rischio (T13–T22, ciascuna 1×5)
  ⚠ BOX H.8 MICROCLIMA (T18 — 1×1, prima di 15.6)
CAPITOLO 16 — CRONOPROGRAMMA (T23 — 13×5)
CAPITOLO 17 — MATRICE R = P × D (T24 — 4×4)
CAPITOLO 18 — RISCHI PER FASE
  18.1 Procedure di emergenza e coordinamento
  18.2 Schede di fase lavorativa (T25–T29, ciascuna 7×2)
      TABELLA INTERFERENZE (T30 — 6×3) con ⚠ H.6 in riga 0
CAPITOLO 19 — GESTIONE DELLE EMERGENZE
CAPITOLO 20 — STIMA COSTI SICUREZZA (T31 — 10×5)
CAPITOLO 21 — DOCUMENTI DA TENERE IN CANTIERE
CAPITOLO 22 — ALLEGATI (elenco)
SOTTOSCRIZIONI (T32 — 2×2)
📌 BOX NOTA PSC (T33 — 1×1)
─── ALLEGATI SVILUPPATI ───
ALLEGATO 1 — ELENCO LAVORAZIONI (T34 — 13×5)
ALLEGATO 2 — CRONOPROGRAMMA GANTT (T35 — 13×11)
ALLEGATO 3 — LAYOUT PLANIMETRICO
ALLEGATO 4 — FASCICOLO DELL'OPERA
  Scheda I  — Descrizione (T36 — 9×3)
  Scheda II — Rischi manutenzione (T37 — 8×2 + T38 — 7×4)
  Scheda III — Documentazione (T39 — 8×3)
ALLEGATO 5 — CHECK-LIST MACCHINE (T40 — 10×8)
ALLEGATO 6 — CALCOLO UOMINI-GIORNO (T41 — 14×5)
ALLEGATO 7 — MODULO NEAR MISS (T42 — 12×2)
```

---

## FRONTESPIZIO

```
──────────────────────────────────────────────────
STUDIO ASSOCIATO EVOLUTION | Piano di Sicurezza e Coordinamento
──────────────────────────────────────────────────

PIANO DI SICUREZZA E COORDINAMENTO
(Allegato XV e art. 100 del D.Lgs. 9 aprile 2008 n. 81 e s.m.i.)

┌─────────────────────┬──────────────────────────────────────────┐
│ Codice Sito         │ —                                        │
│ Nome Sito           │ [INDIRIZZO_BREVE] — [COMUNE]             │
│ Tipologia           │ Ristrutturazione interna appartamento — [TITOLO_ABILITATIVO] │
│ Committente         │ [NOME_COMMITTENTE]                       │
│ Indirizzo           │ [INDIRIZZO_CANTIERE] — [CAP] [COMUNE] ([PROVINCIA]) │
│ Coordinate          │ Lat [LAT]° N — Long [LONG]° E            │
│ Tecnologie          │ N/A — Opere edili e impiantistiche residenziali │
│ Progetto Esecutivo  │ [TITOLO_ABILITATIVO] prot. n. [PROT] del [DATA_PROT] │
│ Rev. PSC            │ 00 — Emissione del [DATA_EMISSIONE]      │
│ CSP / CSE           │ [NOME_CSE] — Ordine Ingegneri [PROV] n. [N_ORDINE] │
└─────────────────────┴──────────────────────────────────────────┘
```

**Tabella T0**: 10 righe × 2 colonne. Colonna 0 = etichetta (bold, sfondo `#2F5496`, testo bianco). Colonna 1 = valore.

---

## BOX LEGALE — POSIZIONI DI GARANZIA (T1)

Tabella 1×1, sfondo `#EBF5FB`, titolo bold blu `#1F4E79`.

```
🔒 Posizioni di garanzia
Art. 89-100 D.Lgs. 81/2008. I soggetti titolari di posizione di garanzia nel presente cantiere sono:
(a) Committente — [NOME_COMMITTENTE];
(b) CSP e CSE — [NOME_CSE];
(c) Impresa appaltatrice (affidataria ex art. 89 co.1 lett. i) — [NOME_IMPRESA_APPALTATRICE];
(d) Subappaltatori esecutori: [ELENCO_SUBAPPALTATORI].
Ciascun soggetto risponde, entro il perimetro della propria posizione di garanzia, della tutela della
sicurezza dei lavoratori presenti in cantiere. La violazione degli obblighi di coordinamento e vigilanza
è sanzionata penalmente (artt. 92, 93, 157, 158, 159 D.Lgs. 81/2008).
```

---

## CAPITOLO 1 — PREMESSA

**Heading 1**: `CAPITOLO 1 — PREMESSA`

**Rif. normativi**: `Rif. normativi: art. 100 D.Lgs. 81/2008 e s.m.i. — Allegato XV`

**Testo standard**:

```
Il presente Piano di Sicurezza e Coordinamento (PSC) è redatto ai sensi dell'art. 100 e
dell'Allegato XV del D.Lgs. 9 aprile 2008 n. 81 e successive modificazioni e integrazioni
(D.Lgs. 3 agosto 2009 n. 106). Il documento contiene l'individuazione, l'analisi e la
valutazione dei rischi e le conseguenti procedure, gli apprestamenti e le attrezzature atti a
garantire, per tutta la durata dei lavori, il rispetto delle norme per la prevenzione degli
infortuni e la tutela della salute dei lavoratori nonché la stima dei relativi costi (punto 2.1.1
Allegato XV). Il PSC è parte integrante del contratto di appalto (art. 100, comma 2).
```

```
L'opera consiste nella [DESCRIZIONE_SINTETICA_INTERVENTO] all'interno di un
appartamento al [PIANO] di un edificio condominiale in [INDIRIZZO_CANTIERE].
L'intervento è assoggettato a [TITOLO_ABILITATIVO] (art. [ARTICOLO_RIFERIMENTO]
DPR 380/2001).
```

```
Il PSC è documento specifico del cantiere in oggetto: ogni sezione è calibrata sui rischi,
sulle caratteristiche dell'opera, sulla conformazione dell'area e sulle interferenze tra le
imprese presenti. Nessuna parte è ripresa da modelli standard non contestualizzati
(⚠ H.1 — Cass. Pen. n. 7421/2026: PSC standardizzato = omissione).
```

> ⚠ **WARNING H.1**: Integrare nel testo della premessa il richiamo alla specificità del PSC rispetto al cantiere in oggetto.

---

## CAPITOLO 2 — ANAGRAFICA DI CANTIERE

**Heading 1**: `CAPITOLO 2 — ANAGRAFICA DI CANTIERE`

`Rif.: punto 2.1.2, lettera a, punto 1, Allegato XV D.Lgs. 81/2008`

### 2.1 Caratteristiche dell'opera (T2 — 11×2)

| Voce | Dati |
|---|---|
| Natura dell'Opera | Civile / Edilizia residenziale — Impiantistica |
| Tipologia cantiere | Ristrutturazione interna appartamento — [TITOLO_ABILITATIVO] art. [ART] DPR 380/2001 |
| Indirizzo | [INDIRIZZO_CANTIERE] — [CAP] [COMUNE] ([PROVINCIA]) |
| Dati catastali | Foglio [FOGLIO] — Part. [PART] — Sub. [SUB] |
| Coordinate WGS84 | [LAT]° N — [LONG]° E |
| Piano appartamento | [PIANO] — edificio condominiale |
| Composizione alloggio | [ELENCO_LOCALI] |
| Durata presunta | [N_GIORNI] giorni lavorativi |
| Entità presunta | [N_UG] uomini-giorno |
| Importo lavori | € [IMPORTO] + IVA (prev. [IMPRESA_FORNITORE] n. [N_PREV] del [DATA_PREV]) |

**Nota**: Riga intestazione sfondo blu `#2F5496` testo bianco.

### 2.2 Soggetti per la sicurezza (T3 — 7×2)

| Ruolo | Dati |
|---|---|
| Committente | [NOME_COMMITTENTE] — CF [CF_COMMITTENTE] — [INDIRIZZO_COMMITTENTE] |
| CSP e CSE | [NOME_CSE] — [NOME_STUDIO] — [INDIRIZZO_STUDIO] — Tel. [TEL_CSE] — Ordine Ing. [PROV] n. [N_ORDINE] |
| Impresa appaltatrice | [NOME_IMPRESA_APPALTATRICE] — [INDIRIZZO_IMPRESA] — Impresa appaltatrice ex art. 89 co.1 lett. i) D.Lgs. 81/08 — Responsabile art. 97 |
| Subappaltatore 1 — [SPECIALIZZAZIONE_1] | [NOME_SUB_1] — CF [CF_SUB_1] |
| Subappaltatore 2 — [SPECIALIZZAZIONE_2] | [NOME_SUB_2] — [DATI_SUB_2] — D.M. 37/2008 lett. [LETTERE] |
| Subappaltatore 3 — [SPECIALIZZAZIONE_3] | [NOME_SUB_3] — P.IVA [PIVA_SUB_3] — D.M. 37/08 lett. [LETTERE] — ⚠ [NOTE_DURC] |

**Nota**: Il numero di subappaltatori è variabile. Aggiungere/rimuovere righe in base al cantiere. Segnalare sempre DURC in scadenza/scaduto.

### 2.3 Numeri telefonici utili (T4 — 9×2)

| Servizio | Numero |
|---|---|
| Emergenza unica | 112 |
| Pronto soccorso | 118 |
| Vigili del Fuoco | 115 |
| Carabinieri | 112 |
| Polizia | 113 |
| USL [NOME_ASL] — [COMUNE] | [TEL_ASL] |
| Ospedale [NOME_OSPEDALE] — [COMUNE] | [TEL_OSPEDALE] |
| Comune di [COMUNE] — Ufficio Tecnico | [TEL_COMUNE] |

---

## CAPITOLO 3 — MODALITÀ DI GESTIONE DEL PSC

**Heading 1**: `CAPITOLO 3 — MODALITÀ DI GESTIONE DEL PSC`

### 3.1 Revisione del piano

```
Il presente PSC è documento dinamico. Deve essere aggiornato tempestivamente dal CSE ogni
qualvolta intervengano modifiche significative alle lavorazioni, alle imprese presenti, ai rischi
rilevati o alle condizioni del cantiere (⚠ H.5 — Cass. Pen. n. 3809/2024).
```

### ⚠ BOX H.2 (T5 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.2 — Cass. Pen. n. 7414/2024: in caso di pericolo grave e imminente, il CSE
dispone la sospensione immediata dei lavori, con comunicazione scritta al committente, dandone
motivazione. Il CSE che non sospende i lavori in caso di pericolo grave è penalmente responsabile
anche per l'omissione (Cass. Pen. n. 7414/2024; n. 27165/2023). Verbale di sospensione:
rif. modello V.3 in references/verbali-cse.md.
```

### 3.2 Attività di coordinamento del CSE

```
Il CSE effettua sopralluoghi periodici e verbalizzati, verifica l'attuazione del PSC e dei POS,
adotta provvedimenti di propria competenza (diffida, sospensione) e informa il committente in caso
di inadempienza delle imprese. L'attività di coordinamento è documentata con verbali numerati e
firmati (⚠ H.4 — alta vigilanza concreta).
```

### 3.3 Perimetro delle funzioni del CSE

### 🔒 BOX PERIMETRO GARANZIA CSE (T6 — 1×1, sfondo `#EBF5FB`)

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
Prima dell'inizio dei lavori, il RLS di ciascuna impresa è consultato ai sensi dell'art. 102
D.Lgs. 81/2008. Il verbale di consultazione è conservato nell'archivio di cantiere.
```

### 3.5 Riunione di coordinamento

```
Prima dell'inizio dei lavori si terrà la riunione di coordinamento di cui all'art. 92 D.Lgs.
81/2008, alla quale partecipano: CSE, referenti delle imprese, eventuali lavoratori autonomi.
Oggetto: illustrazione del PSC, cronoprogramma, interferenze, procedure di emergenza, obblighi
delle imprese. Verbale firmato da tutti i presenti.
```

---

## CAPITOLO 4 — NOTIFICA PRELIMINARE

**Heading 1**: `CAPITOLO 4 — NOTIFICA PRELIMINARE`

```
Il CSP verifica l'avvenuta trasmissione e ne conserva copia nell'archivio di cantiere. Copia
della Notifica deve essere affissa in modo visibile presso il cantiere (portone ingresso
appartamento). La Notifica è trasmessa alla ASL competente ([NOME_ASL]) e alla Direzione
Provinciale del Lavoro di [PROVINCIA].
```

### 📌 BOX NOTA (T7 — 1×1, sfondo `#F0F9FF`)

```
📌 La Notifica Preliminare è obbligatoria ai sensi dell'art. 99 D.Lgs. 81/2008 in quanto il
cantiere prevede la presenza di più imprese esecutrici ([NOME_IMPRESA_APPALTATRICE] +
subappaltatori). La Notifica è trasmessa alla ASL e alla DPL competenti per territorio prima
dell'inizio dei lavori.
```

---

## CAPITOLO 5 — DISPOSIZIONI PER LE IMPRESE

**Heading 1**: `CAPITOLO 5 — DISPOSIZIONI PER LE IMPRESE`

`Rif.: punto 2.1.2, lettera b, Allegato XV D.Lgs. 81/2008`

### 5.1 Obblighi delle imprese

```
[NOME_IMPRESA_APPALTATRICE] riveste il ruolo di IMPRESA APPALTATRICE ai sensi dell'art. 89
comma 1 lett. i) del D.Lgs. 81/2008. In quanto impresa affidataria, [NOME_IMPRESA_APPALTATRICE]
è responsabile della verifica delle condizioni di sicurezza dei lavori affidati e dell'applicazione
delle disposizioni e delle prescrizioni del PSC (art. 97 D.Lgs. 81/2008). Il subappalto integrale
delle lavorazioni a [ELENCO_SUBAPPALTATORI] non esonera [NOME_IMPRESA_APPALTATRICE] dagli obblighi
di coordinamento e vigilanza propri dell'impresa affidataria.
```

```
Ciascuna impresa esecutrice, prima dell'inizio dei lavori, deve: redigere e trasmettere al CSE il
proprio Piano Operativo di Sicurezza (POS); fornire copia del DURC in corso di validità; fornire
elenco nominativo dei lavoratori e attestati di formazione e idoneità sanitaria; comunicare i
nominativi degli addetti emergenza, primo soccorso e antincendio (⚠ H.3 — Cass. Pen.: il CSE
deve verificare i POS prima dell'inizio dei lavori).
```

### 5.2 Patente a crediti e badge digitale

```
A decorrere dal 01/10/2024, le imprese e i lavoratori autonomi che operano in cantiere devono
essere in possesso della patente a crediti di cui all'art. 27 D.Lgs. 81/2008 (come modificato
dal D.L. 19/2024, conv. L. 56/2024). Il badge digitale è verificato dal CSE prima dell'accesso
in cantiere.
```

### 5.3 Contenuti minimi del POS

```
Il POS deve contenere almeno (Allegato XV D.Lgs. 81/08): dati identificativi dell'impresa;
nominativi addetti emergenza/primo soccorso; elenco lavoratori con attestati formazione;
idoneità sanitaria dei lavoratori; valutazione rumore, vibrazioni, MMC; elenco attrezzature
con certificazioni CE; sostanze/preparati pericolosi (SDS); misure preventive integrative.
```

### 5.4 Obblighi contrattuali di sicurezza

```
Costi della sicurezza (art. 26 co. 5 + Allegato XV punto 4): i costi della sicurezza previsti
nel presente PSC, pari a € [IMPORTO_COSTI_SICUREZZA] (stima preventivo [IMPRESA_FORNITORE]
n. [N_PREV] del [DATA_PREV]) sono compresi nell'importo contrattuale, NON soggetti a ribasso
d'asta e devono essere specificamente indicati nel contratto di appalto.
```

---

## CAPITOLO 6 — DESCRIZIONE DELL'OPERA

**Heading 1**: `CAPITOLO 6 — DESCRIZIONE DELL'OPERA`

`Rif.: punto 2.1.2, lettera a, punti 2-3, Allegato XV D.Lgs. 81/2008`

### 6.1 Inquadramento territoriale

```
Il sito oggetto dell'intervento è ubicato in [INDIRIZZO_CANTIERE], nel Comune di [COMUNE]
([PROVINCIA]), [DESCRIZIONE_POSIZIONE_RISPETTO_CENTRO]. L'edificio ospitante è un [DESCRIZIONE_EDIFICIO]
di [N_PIANI] piani fuori terra, con [DESCRIZIONE_STRUTTURA].
```

```
Il contesto circostante è caratterizzato da [DESCRIZIONE_CONTESTO: tessuto urbano, strade,
edifici adiacenti, traffico, ecc.].
```

### 6.2 Descrizione dell'intervento

```
L'intervento prevede [DESCRIZIONE_DETTAGLIATA_LAVORI: elenco delle lavorazioni principali,
locali coinvolti, riferimenti ai locali come INT.1, INT.2, ecc., materiali previsti,
riferimenti al preventivo/progetto].
```

### 6.3 Schede rilievo fotografico

```
Le foto seguenti documentano lo stato dei luoghi al momento del sopralluogo ([DATA_SOPRALLUOGO]).
```

> **LAYOUT FOTO**: minimo 2 foto per pagina. Ogni foto ha larghezza **7 cm** (2.76 in), disposta su 2 colonne affiancate. Didascalia sotto ciascuna foto in Calibri 8pt corsivo. Se la foto è panoramica o una pianta, può occupare l'intera larghezza (14 cm) ma comunque max 1/2 pagina.

**Griglia foto — 2 per riga, layout a tabella invisibile 2 colonne:**

```
┌──────────────────────────┬──────────────────────────┐
│  [FOTO DA INSERIRE]      │  [FOTO DA INSERIRE]      │
│  7 cm × auto             │  7 cm × auto             │
│  Foto 1 — Vista ortofoto │  Foto 2 — Ingresso edif. │
├──────────────────────────┼──────────────────────────┤
│  [FOTO DA INSERIRE]      │  [FOTO DA INSERIRE]      │
│  7 cm × auto             │  7 cm × auto             │
│  Foto 3 — Dett. portone  │  Foto 4 — Sala (ante-op) │
├──────────────────────────┼──────────────────────────┤
│  [FOTO DA INSERIRE]      │  [FOTO DA INSERIRE]      │
│  7 cm × auto             │  7 cm × auto             │
│  Foto 5 — Area cucina    │  Foto 6 — Bagno          │
├──────────────────────────┴──────────────────────────┤
│           [FOTO DA INSERIRE — PIANTA]               │
│           14 cm × auto (larghezza piena)            │
│  Foto 7 — Pianta appartamento e dettaglio interventi│
└─────────────────────────────────────────────────────┘
```

**Implementazione .docx**: usare una tabella a **2 colonne con bordi invisibili** (no border). Ogni cella contiene l'immagine centrata + didascalia sotto. Per la pianta (ultima riga), unire le 2 celle (merge).

**Foto obbligatorie** (minimo 7, adattare al cantiere):
1. Vista ortofoto/aerea edificio
2. Ingresso edificio / portone condominiale
3. Dettaglio ingresso / scala condominiale
4. Locale principale stato ante-operam (es. sala)
5. Area prevista per intervento specifico (es. cucina)
6. Bagno/i
7. Pianta appartamento con dettaglio interventi (da elaborati grafici CILA)

> **NOTA**: le foto sono specifiche del cantiere e vanno inserite dall'utente o estratte dai documenti forniti (CILA, sopralluogo). Nel template .docx i placeholder grigi `[FOTO DA INSERIRE]` vengono sostituiti con le foto reali.

---

## CAPITOLO 7 — AREA DI LAVORO

**Heading 1**: `CAPITOLO 7 — AREA DI LAVORO`

`Rif.: punto 2.1.2, lettera a, Allegato XV D.Lgs. 81/2008`

```
L'area di lavoro principale è l'appartamento (q. [PIANO]) e i locali interni dell'appartamento.
Accesso tramite [DESCRIZIONE_ACCESSO: scala condominiale interna, n. piani, ascensore, ecc.].
L'area esterna interessata è limitata a [DESCRIZIONE_AREA_ESTERNA: carico/scarico materiali,
zona a terra per stoccaggio temporaneo, ecc.]. Nei locali comuni non si svolgono lavorazioni:
il transito è limitato al trasporto materiali.
```

---

## CAPITOLO 8 — RISCHI INTRINSECI E FATTORI ESTERNI

**Heading 1**: `CAPITOLO 8 — RISCHI INTRINSECI E FATTORI ESTERNI`

`Rif.: punto 2.2.1, Allegato XV D.Lgs. 81/2008`

### 8.1 Caratteristiche idrogeologiche

```
[DESCRIZIONE_IDROGEOLOGICA: es. L'area non presenta rischi idrogeologici significativi
(consultato PAI Autorità Bacino Distrettuale [NOME_BACINO]). Non si rilevano sottoservizi
interferenti essendo lavorazioni interamente interne al [PIANO].]
```

### 8.2 Fattori esterni (T8 — 6×3)

| Fattore esterno | Presenza | Misure preventive |
|---|---|---|
| Linee elettriche aeree | [SÌ/NO] | [MISURE o N/A] |
| Sottoservizi interrati | [SÌ/NO — motivazione] | [MISURE o N/A] |
| Traffico veicolare | [SÌ/NO — dettaglio] | [MISURE: segnaletica temporanea, ecc.] |
| Condominio abitato | SÌ — appartamenti adiacenti e sottostanti occupati | Rispetto orari condominiali; protezione scale comuni; avviso ai condomini |
| Presenza eternit (cisterna/copertura) | [SÌ/NO — specificare se oggetto di intervento] | [MISURE: nessun contatto/disturbo; segnalazione; divieto manipolazione] |

**Nota**: Per ristrutturazione in condominio, la riga "Condominio abitato" è SEMPRE presente con SÌ. Adattare la riga eternit in base al sopralluogo.

---

## CAPITOLO 9 — ORGANIZZAZIONE DEL CANTIERE

**Heading 1**: `CAPITOLO 9 — ORGANIZZAZIONE DEL CANTIERE`

`Rif.: punto 2.1.2, lettera c, Allegato XV D.Lgs. 81/2008 — punto 2.2.2`

### 9.1 Recinzione, accessi, segnalazioni

```
Area a terra: delimitazione con nastro bianco/rosso e rete arancione plastificata (h ≥ 120 cm).
Cartello P006 'Vietato l'accesso ai non autorizzati' sul portone ingresso.

Accesso: portone condominiale con chiave (fornito dal committente). Percorso verticale: scala
condominiale interna con protezione gradini (teli antipolvere, nastro). Piano cantiere: porta
appartamento con cartello cantiere (committente, CSE, imprese, numeri emergenza).
```

> **🖼️ IMMAGINE FISSA — CARTELLO DI CANTIERE**: inserire l'immagine del cartello di cantiere tipo (presente nel template .docx come `image15.png`). Questa immagine è FISSA nel template e non va sostituita — mostra il layout standard del cartello informativo di cantiere con i dati da compilare.

```
Il cartello deve essere messo sul portone dell'ingresso dell'appartamento in posizione
facilmente visibile.
```

### 9.2 Impianti di cantiere

```
Impianto elettrico: alimentazione dall'utenza condominiale o da generatore. Quadro cantiere con
protezione differenziale 30 mA, magnetotermico, messa a terra. Illuminazione integrativa per
locali ciechi (proiettori LED 50W su treppiede).
```

### 9.3 Aree di stoccaggio

```
Materiali depositati nell'appartamento nella area stoccaggio interna. Carico massimo
nell'appartamento ≤ [CARICO_MAX] kg/mq (da verificare con relazione strutturale se necessario).
Accatastamento: max [ALTEZZA_MAX] m. Materiali pesanti ([MATERIALI_PESANTI]) in prossimità
muri perimetrali/portanti. Prodotti chimici (colle, sigillanti): stoccaggio separato, lontano
da fonti di calore.
```

### 9.4 Coordinamento lavorazioni — rischio interferenziale

```
Il cantiere prevede la compresenza di n. [N_IMPRESE] imprese esecutrici ([ELENCO_IMPRESE]).
Le fasi interferenti sono gestite come segue: [DESCRIZIONE_GESTIONE_INTERFERENZE].
```

### ORGANIGRAMMA DI CANTIERE (tabella grafica 7×4)

Inserire l'organigramma come tabella colorata:

```
┌───────────────────────────────────────────────────────┐
│   ORGANIGRAMMA DI CANTIERE (intestazione #1F4E79)     │
├───────────────────────────────────────────────────────┤
│  COMMITTENTE: [NOME_COMMITTENTE]  (sfondo #FFF2CC)    │
│  CSP/CSE: [NOME_CSE] (sfondo #BDD7EE)                │
├───────────────────────────────────────────────────────┤
│  IMPRESA APPALTATRICE: [NOME_APPALTATRICE]            │
│  (sfondo #FFEB9C)                                     │
├──────────┬──────────────┬────────────────────────────┤
│  SUB 1   │   SUB 2      │   SUB 3                    │
│ (sfondo  │  (sfondo     │  (sfondo                   │
│ #C6EFCE) │  #C6EFCE)    │  #C6EFCE)                  │
└──────────┴──────────────┴────────────────────────────┘
```

```
Ciascun subappaltatore risponde direttamente all'impresa appaltatrice [NOME_IMPRESA_APPALTATRICE]
ai sensi dell'art. 97 D.Lgs. 81/2008. L'impresa appaltatrice verifica che ciascun subappaltatore
sia in possesso dei requisiti tecnico-professionali e della documentazione di sicurezza prevista.
```

### ⚠ BOX H.6 INTERFERENZIALE (T9 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.6 — Cass. Pen. n. 23725/2023; n. 37214/2024: il PSC individua i rischi
interferenziali tra le lavorazioni e prescrive le misure di coordinamento specifiche. La mancata
gestione delle interferenze è causa autonoma di responsabilità del CSE.
```

### 9.5 Segnaletica di sicurezza prevista nel cantiere

`Rif.: artt. 161-166 e Allegati XXIV-XXXII D.Lgs. 81/2008 — UNI EN ISO 7010`

### 📌 BOX NOTA SEGNALETICA (T10 — 1×1, sfondo `#F0F9FF`)

```
📌 La segnaletica va mantenuta integra, leggibile e in posizione corretta per tutta la durata
dei lavori. L'impresa appaltatrice verifica settimanalmente lo stato della segnaletica.
```

**Tabelle segnaletica** — una per ciascuna categoria, ciascuna con immagine riepilogativa:

> **🖼️ IMMAGINI FISSE — SEGNALETICA ISO 7010**: per ogni categoria è presente nel template .docx un'immagine riepilogativa dei cartelli pertinenti. Queste immagini sono FISSE nel template e NON vanno sostituite. Sono le tavole visive di riferimento per la segnaletica di cantiere.

1. **Cartelli di PRESCRIZIONE (M — Fondo Blu)** + 🖼️ immagine fissa `image17` — elencare segnali obbligatori
2. **Cartelli di PERICOLO (W — Fondo Giallo)** + 🖼️ immagine fissa `image18` — elencare segnali pertinenti
3. **Cartelli di DIVIETO (P — Fondo Rosso/Bianco)** + 🖼️ immagine fissa `image19` — elencare divieti
4. **Cartelli di EMERGENZA (E — Fondo Verde)** + 🖼️ immagine fissa `image20` — uscita emergenza, punto raccolta
5. **Cartelli di ANTINCENDIO (F — Fondo Rosso)** + 🖼️ immagine fissa `image21` — estintore, ecc.

**Segnaletica tipica per ristrutturazione appartamento in condominio:**

| Categoria | Segnali tipici |
|---|---|
| Prescrizione | M003 Protezione orecchie, M004 Protezione occhi, M008 Scarpe sicurezza, M014 Elmetto, M009 Guanti |
| Pericolo | W001 Pericolo generico, W012 Tensione elettrica, W015 Caduta materiali, W016 Rischio biologico (se demolizione), W026 Caduta in piano |
| Divieto | P001 Divieto generico, P002 Vietato fumare, P006 Vietato accesso non autorizzati, P007 Vietato veicoli movimentazione merci |
| Emergenza | E001 Uscita emergenza, E003 Primo soccorso, E007 Punto raccolta |
| Antincendio | F001 Estintore, F003 Scala antincendio (se presente) |

---

## CAPITOLO 10 — SOSTANZE PERICOLOSE PRESENTI

**Heading 1**: `CAPITOLO 10 — SOSTANZE PERICOLOSE PRESENTI`

`Rif.: artt. 222-232 D.Lgs. 81/2008 — Regolamento CLP (1272/2008)`

```
Nel cantiere in oggetto non si prevede l'utilizzo di sostanze chimiche pericolose in quantità
significativa. In caso di utilizzo di prodotti per l'impiantistica (colle, solventi, sigillanti),
le relative Schede Dati di Sicurezza (SDS) devono essere presenti in cantiere e consultate prima
dell'uso. I lavoratori devono essere informati sui rischi e sulle misure di protezione.
```

> **Nota**: adattare se il cantiere prevede rimozione di materiali contenenti amianto, verniciatura, utilizzo di resine epossidiche, ecc.

---

## CAPITOLO 11 — ATTREZZATURE, MACCHINE E IMPIANTI

**Heading 1**: `CAPITOLO 11 — ATTREZZATURE, MACCHINE E IMPIANTI`

`Rif.: artt. 70-73, 85-88 D.Lgs. 81/2008 — Allegato V — D.Lgs. 17/2010`

> **🖼️ IMMAGINE FISSA — TAVOLA ATTREZZATURE**: inserire l'immagine riepilogativa delle attrezzature di cantiere (presente nel template .docx come `image22`). Questa immagine è FISSA e NON va sostituita — mostra le attrezzature tipiche con pittogrammi di sicurezza.

Elencare le attrezzature previste nel cantiere. Per ristrutturazione interna tipica:

- Trapano a percussione
- Smerigliatrice angolare (flessibile)
- Avvitatore a impulsi
- Saldatrice (eventuale)
- Paranco manuale a catena (per sollevamento materiali pesanti)
- Scala portatile (EN 131)
- Trabattello (EN 1004) — se lavori a soffitto
- Strumenti di misura
- Gruppo elettrogeno (eventuale)

---

## CAPITOLO 12 — DISPOSITIVI DI PROTEZIONE INDIVIDUALE (DPI)

**Heading 1**: `CAPITOLO 12 — DISPOSITIVI DI PROTEZIONE INDIVIDUALE (DPI)`

`Rif.: artt. 74-79 D.Lgs. 81/2008 — Allegato VIII`

> **🖼️ IMMAGINE FISSA — TAVOLA DPI**: inserire l'immagine riepilogativa dei DPI obbligatori (presente nel template .docx come `image22` — stessa tavola del Cap. 11, ripetuta). Questa immagine è FISSA e NON va sostituita — mostra i DPI tipici con norme EN di riferimento.

### ⚠ BOX H.7 (T11 — 1×1, sfondo `#FFF5F5`)

```
⚠ AVVERTENZA H.7 — Cass. Pen. n. 8083/2019: la protezione collettiva (DPC: parapetti,
reti, segregazione) ha la PRIORITÀ sui dispositivi di protezione individuale (DPI). I DPI
sono integrativi dei DPC, mai sostitutivi. La scelta di un DPI in luogo di un DPC
disponibile integra violazione dell'art. 15 D.Lgs. 81/2008.
```

Elencare DPI obbligatori per il cantiere: elmetto EN 397, scarpe S3, guanti EN 388/374,
occhiali EN 166, maschere FFP2/FFP3 EN 149, cuffie/inserti EN 352, giubbotto AV EN ISO 20471.

---

## CAPITOLO 13 — VALUTAZIONE DEL RUMORE

**Heading 1**: `CAPITOLO 13 — VALUTAZIONE DEL RUMORE`

`Rif.: artt. 189-192 D.Lgs. 81/2008`

> **🖼️ IMMAGINE FISSA — TAVOLA RUMORE/DPI ANTIRUMORE**: inserire l'immagine riepilogativa dei DPI antirumore (presente nel template .docx come `image23`). Questa immagine è FISSA e NON va sostituita.

### Tabella classi esposizione (T12 — 5×3)

| Classe di esposizione | Leq dB(A) | Obblighi del datore di lavoro |
|---|---|---|
| I — Sotto soglia inferiore | < 80 | Informazione generale |
| II — Tra soglie | 80-85 | Informazione/formazione; DPI disponibili |
| III — Sopra soglia superiore | 85-87 | DPI obbligatori; sorveglianza sanitaria |
| IV — Valore limite | ≥ 87 | Divieto superamento; interventi immediati |

```
Principali sorgenti: [ELENCO_SORGENTI_RUMORE]. DPI antirumore EN 352 obbligatori durante
[LAVORAZIONI_RUMOROSE]. L'impresa dovrà fornire la valutazione specifica del rischio rumore
nel proprio POS.
```

---

## CAPITOLO 14 — SORVEGLIANZA SANITARIA

**Heading 1**: `CAPITOLO 14 — SORVEGLIANZA SANITARIA`

`Rif.: artt. 41-43, 164-167 D.Lgs. 81/2008`

```
La sorveglianza sanitaria è obbligatoria per i lavoratori esposti a rischi specifici: rumore,
vibrazioni, MMC, lavori in quota. Il Medico Competente di ciascuna impresa rilascia il giudizio
di idoneità alla mansione specifica, che deve essere presente in cantiere e consultabile dal CSE.
```

---

## CAPITOLO 15 — RISCHI PRINCIPALI — ANALISI E PREVENZIONE

**Heading 1**: `CAPITOLO 15 — RISCHI PRINCIPALI — ANALISI E PREVENZIONE`

`Rif.: punto 2.2.3, Allegato XV D.Lgs. 81/2008 — Matrice R = P × D`

```
Metodologia: R = P × D. P (Probabilità): 1=Bassa, 2=Media, 3=Alta.
D (Danno): 1=Lieve (< 15 gg), 2=Grave (> 40 gg), 3=Gravissimo (morte).
R ≥ 9: CRITICO (rosso); 6-8: ALTO (arancio); 3-5: MEDIO (giallo); 1-2: BASSO (verde).
```

### RISCHI TIPICI PER RISTRUTTURAZIONE INTERNA APPARTAMENTO

Selezionare i rischi pertinenti. Elenco tipico:

#### 15.1 Caduta materiali (rischio principale)
Tabella 1×5: `15.1 | Caduta materiali dall'alto durante demolizioni e trasporto | P | D | Misure`

#### 15.2 Inalazione polveri
Tabella 1×5: `15.2 | Inalazione polveri e fibre durante demolizioni/forature | P | D | Misure`

#### 15.3 Elettrocuzione
Tabella 1×5: `15.3 | Contatto con parti in tensione | P | D | Misure`

#### 15.4 Rumore e vibrazioni
Tabella 1×5: `15.4 | Esposizione a rumore > 85 dB(A) e vibrazioni HAV | P | D | Misure`

#### 15.5 Movimentazione manuale carichi
Tabella 1×5: `15.5 | Sollevamento/trasporto manuale carichi pesanti | P | D | Misure`

#### 15.6 Microclima sfavorevole

### ⚠ BOX H.8 (T18 — 1×1, sfondo `#FFF5F5`, PRIMA della tabella 15.6)

```
⚠ AVVERTENZA H.8 — Orientamento Cass. Pen. 2023-2025: in caso di temperatura percepita
> 35 °C o < 0 °C, sospendere le lavorazioni fino al rientro nei limiti. Il CSE dispone la
sospensione per condizioni climatiche estreme anche in assenza di richiesta delle imprese.
```

Tabella 1×5: `15.6 | Microclima sfavorevole (caldo/freddo estremo) | P | D | Misure`

#### 15.7 Proiezione schegge e frammenti
Tabella 1×5: `15.7 | Proiezione schegge durante taglio/molatura | P | D | Misure`

#### 15.8 Contatto con sostanze chimiche
Tabella 1×5: `15.8 | Contatto cutaneo/inalazione prodotti chimici | P | D | Misure`

#### 15.9 Rischi interferenziali
Tabella 1×5: `15.9 | Compresenza imprese — interferenza spaziale e temporale | P | D | Misure`

Aggiungere sottosezione 15.9.1 con tabella 1×5 per dettaglio interferenze specifiche.

> **Nota**: P e D devono essere calibrate sul cantiere specifico, MAI generiche. Motivare il valore assegnato con riferimento al progetto, alle foto, alle condizioni del sito.

---

## CAPITOLO 16 — PROGRAMMA DEI LAVORI — CRONOPROGRAMMA

**Heading 1**: `CAPITOLO 16 — PROGRAMMA DEI LAVORI — CRONOPROGRAMMA`

`Rif.: punto 2.1.2, lettera d, Allegato XV`

```
Durata complessiva stimata: [N_GIORNI] giorni lavorativi. Entità presunta: [N_UG] uomini-giorno.
```

### Tabella cronoprogramma (T23 — N×5)

| N° | Fase di lavoro | Durata (gg) | Op. | Note interferenziali |
|---|---|---|---|---|
| 1 | [FASE_1] | [DURATA] | [N_OP] | [NOTE] |
| 2 | [FASE_2] | [DURATA] | [N_OP] | [NOTE] |
| ... | ... | ... | ... | ... |

Evidenziare le fasi con INTERFERENZA in colonna "Note interferenziali".

---

## CAPITOLO 17 — ANALISI GENERALE DEI RISCHI — MATRICE R = P × D

**Heading 1**: `CAPITOLO 17 — ANALISI GENERALE DEI RISCHI — MATRICE R = P × D`

`Rif.: punto 2.2, Allegato XV — INAIL 'La Progettazione della Sicurezza nel Cantiere'`

### Tabella matrice (T24 — 4×4)

| P / D | D=1 Lieve | D=2 Grave | D=3 Gravissimo |
|---|---|---|---|
| P=1 Bassa | 1 — BASSO | 2 — BASSO | 3 — MEDIO |
| P=2 Media | 2 — BASSO | 4 — MEDIO | 6 — ALTO |
| P=3 Alta | 3 — MEDIO | 6 — ALTO | 9 — CRITICO |

**Colorazione**: BASSO verde `#D1FAE5`, MEDIO giallo `#FEF9C3`, ALTO arancio `#FED7AA`, CRITICO rosso `#FECACA`.

---

## CAPITOLO 18 — INDIVIDUAZIONE, ANALISI E VALUTAZIONE DEI RISCHI PER FASE

**Heading 1**: `CAPITOLO 18 — INDIVIDUAZIONE, ANALISI E VALUTAZIONE DEI RISCHI PER FASE`

`Rif.: punto 2.2.3, Allegato XV — modello INAIL schede fase lavorativa`

### 18.1 Procedure di emergenza e coordinamento

Elenco puntato:
- Viabilità interna cantiere: accesso unico controllato con segnaletica permanente
- Area stoccaggio: [POSIZIONE], max [CARICO] kg/mq
- Cassetta PS conforme DM 388/2003 (Gruppo C) nell'appartamento
- Estintore ABC 6 kg (polvere) nell'appartamento
- Numeri emergenza affissi in cantiere (112, 118, 115)

### 18.2 Schede di fase lavorativa (T25–T29, ciascuna 7×2)

Ogni scheda ha questa struttura:

| Campo | Contenuto |
|---|---|
| Descrizione attività | [DESCRIZIONE_FASE] |
| Rischi principali | [RISCHI_FASE] |
| DPC | [DISPOSITIVI_PROTEZIONE_COLLETTIVA] |
| DPI | [DPI_PREVISTI con norme EN] |
| Prescrizioni operative | [PRESCRIZIONI] |
| Interferenze | [INTERFERENZE_CON_ALTRE_FASI] |
| Sorveglianza CSE | [AZIONI_CSE] |

**Schede tipiche per ristrutturazione appartamento:**
1. Allestimento cantiere
2. Demolizioni e rimozioni
3. Massetti e sottofondi
4. Posa pavimenti/rivestimenti e sanitari
5. Completamento impianti elettrici/idraulici

### TABELLA INTERFERENZE (T30 — N×3, con ⚠ H.6 in riga header unificata)

Riga 0: cella unificata con ⚠ H.6 (sfondo `#FFF5F5`)

| Fasi sovrapposte | Rischio interferenziale | Misura di coordinamento CSE |
|---|---|---|
| [FASE_A + FASE_B] | [RISCHIO] | [MISURA: fasce orarie, percorsi separati, ecc.] |

---

## CAPITOLO 19 — GESTIONE DELLE EMERGENZE

**Heading 1**: `CAPITOLO 19 — GESTIONE DELLE EMERGENZE`

Procedure di emergenza previste (elenco puntato):
- **Caduta materiali**: attivare 118, non spostare l'infortunato, attendere soccorsi. Comunicare posizione esatta (piano, locale).
- **Incendio**: usare estintore ABC 6 kg; evacuare l'appartamento; chiamare 115; punto di raccolta a terra.
- **Folgorazione**: sezionare alimentazione dal quadro; non toccare l'infortunato; chiamare 118.
- **Condizioni meteo avverse**: sospendere lavorazioni; mettere in sicurezza attrezzature; CSE dispone ripresa.
- **Evento sismico**: evacuazione ordinata verso punto di raccolta esterno; verifica strutturale prima della ripresa.

---

## CAPITOLO 20 — STIMA DEI COSTI DELLA SICUREZZA

**Heading 1**: `CAPITOLO 20 — STIMA DEI COSTI DELLA SICUREZZA`

`Rif.: punto 2.3 e punto 4, Allegato XV D.Lgs. 81/2008`

### Tabella costi (T31 — N×5)

| Voce di costo | Qta | U.M. | Costo unit. | Totale |
|---|---|---|---|---|
| Riunione di coordinamento iniziale | 1 | cad | € 70,00 | € 70,00 |
| Delimitazione area cantiere interna (teli, nastri) | 1 | cad | € 45,00 | € 45,00 |
| Cassetta PS DM 388/2003 Gruppo C | 1 | cad | € 25,00 | € 25,00 |
| Estintore polvere ABC 6 kg | 1 | cad | € 15,00 | € 15,00 |
| Segnaletica ISO 7010 (kit cantiere) | 1 | cad | € 60,00 | € 60,00 |
| Teli protezione pavimenti e scale condominiali | 1 | cad | € 85,00 | € 85,00 |
| Riunioni di coordinamento in corso d'opera | 1 | cad | € 150,00 | € 150,00 |
| | | | **TOTALE** | **€ [TOTALE_COSTI]** |

> **Nota**: adattare le voci di costo al cantiere specifico. Aggiungere: noleggio ponteggio/trabattello, DPI aggiuntivi, misurazioni fonometriche, ecc. se pertinenti.

---

## CAPITOLO 21 — DOCUMENTI DA TENERE IN CANTIERE

**Heading 1**: `CAPITOLO 21 — DOCUMENTI DA TENERE IN CANTIERE`

`Rif.: art. 107, Allegato XV D.Lgs. 81/2008`

Elenco puntato (14 voci standard):
- Copia del presente PSC (ultima revisione) con sottoscrizioni
- Notifica Preliminare (art. 99 D.Lgs. 81/08)
- POS di ciascuna impresa esecutrice ([ELENCO_IMPRESE])
- DURC in corso di validità di ogni impresa
- Patente a crediti (badge digitale) di ogni impresa e lavoratore autonomo
- Attestati formazione dei lavoratori (art. 37 D.Lgs. 81/08, Acc. Stato-Regioni)
- Giudizi di idoneità alla mansione specifica
- Libretti macchine e attrezzature (marcatura CE, manutenzione)
- Dichiarazione di conformità impianto elettrico (DM 37/2008)
- Verbali sopralluogo CSE (firmati dalle imprese)
- Verbali riunioni di coordinamento
- Registro presenze giornaliero
- Schede dati di sicurezza sostanze (SDS) — se presenti
- Dichiarazione di conformità impianti (D.M. 37/2008)

---

## CAPITOLO 22 — ALLEGATI

**Heading 1**: `CAPITOLO 22 — ALLEGATI`

Elenco puntato:
- Allegato 1 — Elenco lavorazioni (rif. Schede 18.2 e cronoprogramma Cap. 16)
- Allegato 2 — Cronoprogramma lavori (Diagramma di Gantt)
- Allegato 3 — Layout planimetrico del cantiere (estratto da Tav. [TAVOLE] degli Elaborati Grafici [TITOLO_ABILITATIVO])
- Allegato 4 — Fascicolo dell'Opera (art. 91 D.Lgs. 81/08 — Allegato XVI)
- Allegato 5 — Check-list macchine e attrezzature
- Allegato 6 — Calcolo uomini-giorno
- Allegato 7 — Modulo segnalazione near miss

---

## SOTTOSCRIZIONI — ACCETTAZIONE DEL PIANO (T32 — 2×2)

| 🛡 IL COORDINATORE PER LA SICUREZZA (CSP e CSE) | 🏢 IL COMMITTENTE |
|---|---|
| [NOME_CSE] | [NOME_COMMITTENTE] |
| [NOME_STUDIO] | |
| Ordine Ingegneri [PROV] Sez. A n. [N_ORDINE] | ✏ DA COMPILARE |
| _______________________________ | _______________________________ |
| Firma e Timbro | Firma e Timbro |

| 🏗 L'IMPRESA AFFIDATARIA | 🔧 IMPRESA SUBAPPALTATRICE |
|---|---|
| [NOME_IMPRESA_APPALTATRICE] | [ELENCO_SUBAPPALTATORI] |
| ✏ DA COMPILARE: nome referente | ✏ DA COMPILARE: nome referente |
| _______________________________ | _______________________________ |
| Firma e Timbro | Firma e Timbro |

### 📌 BOX NOTA PSC (T33 — 1×1, sfondo `#F0F9FF`)

```
📌 Copia del presente PSC, debitamente sottoscritta da tutte le imprese, deve essere tenuta in
cantiere per tutta la durata dei lavori. Il POS deve essere consegnato al CSE prima dell'inizio
delle lavorazioni di ciascuna impresa.
```

---

## ALLEGATO 1 — ELENCO LAVORAZIONI (T34 — N×5)

**Heading 1**: `ALLEGATO 1 — ELENCO LAVORAZIONI`

`Rif.: punto 2.1.2, Allegato XV D.Lgs. 81/2008 — cronoprogramma Cap. 16 e schede 18.2`

| Cod. | Lavorazione | Descrizione sintetica | Impresa | Durata |
|---|---|---|---|---|
| L.01 | [LAVORAZIONE_1] | [DESCRIZIONE] | [IMPRESA] | [DURATA] gg |
| L.02 | [LAVORAZIONE_2] | [DESCRIZIONE] | [IMPRESA] | [DURATA] gg |
| ... | ... | ... | ... | ... |

---

## ALLEGATO 2 — CRONOPROGRAMMA DEI LAVORI (T35 — N×11)

**Heading 1**: `ALLEGATO 2 — CRONOPROGRAMMA DEI LAVORI`

`Rif.: punto 2.1.2, lettera d, Allegato XV — Diagramma di Gantt`

Tabella Gantt con colonne: `Fase | Impresa | G1 | G2 | G3 | G4 | G5 | G6 | G7 | G8 | G9`

Dove Gn = giornata lavorativa (raggruppata per settimane). Celle colorate per impresa:
- `#FEF9C3` (giallo) = Impresa fornitore principale
- `#C6EFCE` (verde) = Subappaltatore 1 (muratura)
- `#BDD7EE` (azzurro) = Subappaltatore 2 (elettrico)
- `#D6DCE4` (blu/grigio) = Subappaltatore 3 (idraulico)

```
Legenda: ▓ giallo = [IMPRESA_1] — ▓ verde = [SUB_1] — ▓ azzurro = [SUB_2] — ▓ blu = [SUB_3]

Fasi critiche per interferenza: [DESCRIZIONE_FASI_CRITICHE_CON_MISURE]
```

---

## ALLEGATO 3 — LAYOUT PLANIMETRICO DEL CANTIERE

**Heading 1**: `ALLEGATO 3 — LAYOUT PLANIMETRICO DEL CANTIERE`

```
Il layout planimetrico del cantiere è rappresentato nella Tav. [TAVOLE] [TITOLO_ABILITATIVO]
[NOME_PROGETTISTA] (rif. [TITOLO_ABILITATIVO] del [DATA_TITOLO]). Di seguito si descrivono gli
elementi di cantiere con il relativo posizionamento nell'appartamento:
[DESCRIZIONE_POSIZIONAMENTO: area stoccaggio, cassetta PS, estintore, quadro cantiere, percorsi, ecc.]
```

---

## ALLEGATO 4 — FASCICOLO DELL'OPERA

**Heading 1**: `ALLEGATO 4 — FASCICOLO DELL'OPERA`

```
(ai sensi dell'art. 91, comma 1, lett. b, D.Lgs. 81/2008 — Allegato XVI)
Il presente Fascicolo dell'Opera contiene le informazioni utili ai fini della prevenzione e della
protezione dai rischi cui sono esposti i lavoratori che interverranno successivamente sull'opera
per lavori di manutenzione.
```

### Scheda I — Descrizione sintetica dell'opera (T36 — 9×3)

| Elemento | Descrizione | Note |
|---|---|---|
| Ubicazione | [INDIRIZZO] | [DATI_CATASTALI] |
| Tipo intervento | [DESCRIZIONE_INTERVENTO] | [TITOLO_ABILITATIVO] |
| Struttura | [TIPO_STRUTTURA] | [N_PIANI], [ANNO_COSTRUZIONE] |
| Copertura | [TIPO_COPERTURA] | [ACCESSO_COPERTURA] |
| Impianti realizzati | [ELENCO_IMPIANTI] | [CONFORMITÀ_DM_37_2008] |
| Piano cantiere | [PIANO] | [ACCESSO] |
| Durata lavori | [DURATA] | [DATA_INIZIO] – [DATA_FINE] |
| Imprese | [ELENCO_IMPRESE] | |
| Note | [NOTE_PARTICOLARI] | |

### Scheda II — Rischi manutenzione (T37 — 8×2 + T38 — 7×4)

**T37** (descrittiva):
| Voce | Descrizione |
|---|---|
| Tipologia interventi futuri | [MANUTENZIONE_ORDINARIA_STRAORDINARIA] |
| Rischi principali | [ELENCO_RISCHI_MANUTENZIONE] |
| Accesso ai luoghi | [DESCRIZIONE_ACCESSO] |
| Misure preventive in dotazione | [MISURE_DOTAZIONE_OPERA] |
| Attrezzature necessarie | [ATTREZZATURE_MANUTENZIONE] |
| DPI necessari | [DPI_MANUTENZIONE] |
| Frequenza interventi prevista | [FREQUENZA] |

**T38** (matrice rischi manutenzione 7×4):
| Rischio da manutenzione | Misura preventiva | Dotazione opera | Frequenza intervento |
|---|---|---|---|
| [RISCHIO_1] | [MISURA_1] | [DOTAZIONE_1] | [FREQUENZA_1] |
| ... | ... | ... | ... |

### Scheda III — Documentazione (T39 — 8×3)

| Documento | Ubicazione/Archivio | Contenuto rilevante |
|---|---|---|
| Progetto architettonico ([TITOLO_ABILITATIVO]) | [POSIZIONE] | Planimetrie, sezioni |
| DdC impianto elettrico D.M. 37/08 | [POSIZIONE] | Conformità impianto elettrico |
| DdC impianto idraulico D.M. 37/08 | [POSIZIONE] | Conformità impianto idrico-sanitario |
| PSC (presente documento) | Committente | Rischi e prescrizioni cantiere |
| POS imprese | Committente | Piani operativi imprese |
| Verbali CSE | Committente/CSE | Sopralluoghi e prescrizioni |
| Certificato agibilità | Comune | [SE_PRESENTE] |
| [ALTRO_DOCUMENTO] | [POSIZIONE] | [CONTENUTO] |

```
Il Fascicolo dell'Opera deve essere aggiornato dal committente in occasione di ogni intervento
di manutenzione successivo, a cura del Coordinatore per la Sicurezza eventualmente nominato.
```

---

## ALLEGATO 5 — CHECK-LIST MACCHINE E ATTREZZATURE (T40 — 10×8)

**Heading 1**: `ALLEGATO 5 — CHECK-LIST MACCHINE E ATTREZZATURE`

`Rif.: artt. 70-73 D.Lgs. 81/2008 — Allegato V — D.Lgs. 17/2010 (Direttiva Macchine)`

```
La seguente check-list deve essere compilata dall'impresa affidataria prima dell'utilizzo di
ciascuna attrezzatura in cantiere e conservata per tutta la durata dei lavori.
```

| Attrezzatura | Marca/Modello | Matr./ID | Marcatura CE | Libretto uso | Manutenz. in corso | Operatore formato | Conforme |
|---|---|---|---|---|---|---|---|
| [ATTREZZATURA_1] | | | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| [ATTREZZATURA_2] | | | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No | ☐ Sì ☐ No |
| ... | | | ... | ... | ... | ... | ... |

```
Compilata da: ________________________________  Data: ___/___/______  Firma: ________________________________
Verificata dal CSE: ________________________________  Data: ___/___/______  Firma: ________________________________
```

---

## ALLEGATO 6 — CALCOLO UOMINI-GIORNO (T41 — N×5)

**Heading 1**: `ALLEGATO 6 — CALCOLO UOMINI-GIORNO`

`Rif.: art. 89, comma 1, lett. g, D.Lgs. 81/2008 — punto 2.1.2, Allegato XV`

```
L'entità presunta del cantiere è espressa in uomini-giorno ed è calcolata come somma delle
giornate lavorative prestate dai lavoratori, anche autonomi, previste per la realizzazione
dell'opera.
```

| Fase | Lavorazione | N° operai | Durata (gg) | Uomini-giorno |
|---|---|---|---|---|
| L.01 | [LAVORAZIONE_1] | [N] | [GG] | [UG] |
| L.02 | [LAVORAZIONE_2] | [N] | [GG] | [UG] |
| ... | ... | ... | ... | ... |
| | **TOTALE** | | | **[TOTALE_UG]** |

```
Entità presunta del cantiere: [TOTALE_UG] uomini-giorno.
Valore [< / ≥] 200 uomini-giorno → [NOTA_NOTIFICA_PRELIMINARE].
```

---

## ALLEGATO 7 — MODULO SEGNALAZIONE NEAR MISS / MANCATO INFORTUNIO (T42 — 12×2)

**Heading 1**: `ALLEGATO 7 — MODULO SEGNALAZIONE NEAR MISS / MANCATO INFORTUNIO`

`Rif.: art. 20 D.Lgs. 81/2008 — Linea Guida INAIL 'Gestione dei near miss'`

```
Il presente modulo deve essere compilato da qualsiasi lavoratore presente in cantiere in caso
di evento che, pur non avendo causato lesioni, avrebbe potuto provocarle (near miss / mancato
infortunio). La segnalazione è anonimizzabile su richiesta.
```

| Campo | Compilazione |
|---|---|
| Data e ora evento | ___/___/______ ore ___:___ |
| Luogo esatto | ☐ Area a terra ☐ Scale condominiali ☐ Appartamento ☐ Locali interni ☐ Altro: ____________ |
| Fase lavorativa in corso | |
| Descrizione sintetica dell'evento | |
| Persone coinvolte (nomi e impresa) | |
| Persone testimoni | |
| Possibili cause | ☐ Caduta oggetti ☐ Scivolamento ☐ Caduta materiali ☐ Contatto elettrico ☐ Proiezione schegge ☐ Urto ☐ Altro: ____________ |
| DPI indossati al momento | ☐ Elmetto ☐ Scarpe S3 ☐ Guanti ☐ Imbracatura ☐ Giubbotto AV ☐ Altro: ____________ |
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

## CHECKLIST PRE-CONSEGNA

### F.1 — Completezza documentale

- [ ] Frontespizio compilato con tutti i dati
- [ ] Box 🔒 Posizioni di garanzia con nomi corretti
- [ ] Tabella caratteristiche opera (T2) completa
- [ ] Tabella soggetti sicurezza (T3) completa con DURC verificato
- [ ] Numeri telefonici utili aggiornati e localizzati
- [ ] Foto ante-operam inserite (min. 5 foto: edificio, ingresso, locali, pianta)
- [ ] Tutti i rischi con P e D motivate dal cantiere specifico
- [ ] Cronoprogramma coerente con elenco lavorazioni
- [ ] Schede fase lavorativa compilate per ogni fase
- [ ] Tabella interferenze compilata con misure specifiche
- [ ] Costi sicurezza calcolati e coerenti con il cantiere
- [ ] Tutti i 7 allegati sviluppati (non solo elencati)
- [ ] Sottoscrizioni con tutti i soggetti
- [ ] Fascicolo dell'Opera completo (3 schede)

### F.3 — Conformità normativa e difensiva

- [ ] ⚠ H.1 (PSC specifico) → integrato in Cap. 1
- [ ] ⚠ H.2 (sospensione lavori) → integrato in Cap. 3
- [ ] ⚠ H.3 (verifica POS) → integrato in Cap. 5
- [ ] ⚠ H.4 (alta vigilanza) → integrato in Cap. 3.2
- [ ] ⚠ H.5 (aggiornamento PSC) → integrato in Cap. 3.1
- [ ] ⚠ H.6 (interferenziale) → integrato in Cap. 9.4 e Cap. 18
- [ ] ⚠ H.7 (DPC > DPI) → integrato in Cap. 12
- [ ] ⚠ H.8 (microclima) → integrato in Cap. 15.6
- [ ] 🔒 Posizioni di garanzia → T1
- [ ] 🔒 Perimetro CSE → T6
- [ ] Nessun placeholder `[DA COMPILARE]` residuo non intenzionale
- [ ] Nessun riferimento a cantieri diversi (residui da template)
- [ ] Tutti i riferimenti normativi presenti e corretti
