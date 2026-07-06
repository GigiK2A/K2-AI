# Checklist di Verifica — Pacchetto Autorizzativo Iliad SCIA art. 45

## A. COMPLETEZZA DOCUMENTI

Per ogni documento, verifica la presenza del file e assegna: ✅ PRESENTE | ⚠️ MANCANTE | ❌ NC BLOCCANTE

| N. | Documento | Verifica | Priorità se mancante |
|----|-----------|----------|---------------------|
| 1 | SCIA art. 45 | | BLOCCANTE |
| 2 | Delega alla presentazione | | BLOCCANTE |
| 3 | MISE-PROCURA Longari-Rossi | | BLOCCANTE |
| 4 | RT — Relazione Tecnica | | BLOCCANTE |
| 5 | PDM — Piano di Misurazione | | IMPORTANTE |
| 6 | ASSEVERAZIONI | | BLOCCANTE |
| 7 | B40/RELAIE | | BLOCCANTE |
| 8 | Impegno pagamento ARPA | | IMPORTANTE |
| 9 | DICH. SOSTITUTIVA ALPHA24 | | IMPORTANTE |
| 10 | Atto d'obbligo | | IMPORTANTE |
| 11 | Diagrammi Angolari | | MINORE (se previsti) |
| 13 | Nulla Osta Cellnex | | BLOCCANTE (se sito Cellnex) |
| — | FILETX.xlsx | | MINORE (dati interni) |

---

## B. COERENZA DATI IDENTIFICATIVI

Verifica che i seguenti campi siano **identici** in tutti i documenti del pacchetto.

### B1 — Codice Sito
- Formato atteso: `RM[5cifre]_[3cifre]` (es. `RM00168_005`)
- Verifica in: SCIA, RT, Asseverazioni, B40, Atto d'obbligo, DICH. SOSTITUTIVA

**Esito:**
- ✅ Identico in tutti i documenti
- ❌ Difformità: [indicare dove e quale valore]

### B2 — Nome Sito
- Verifica coerenza del nome breve (es. "VIA DI TORREVECCHIA")
- Può avere capitalizzazione diversa (tutto maiuscolo vs mixed) — accettabile
- Non deve cambiare la via/toponomastica

**Esito:** ✅ / ❌

### B3 — Indirizzo Completo
- Via, numero civico, Comune, Municipio (se Roma)
- Verifica in: SCIA (oggetto e corpo), RT, Asseverazioni (asseverazione indirizzo), B40, Atto d'obbligo

**Esito:** ✅ / ❌ — Difformità: [dove]

### B4 — Dati Catastali (Foglio, Particella, Sezione)
- Formato: `N.C.E.U. di [Comune] Foglio [N], P.lla n. [N], Sez. [X]`
- Verifica in: SCIA, RT, Asseverazioni (asseverazione catasto), B40

**Esito:** ✅ / ❌

### B5 — Coordinate WGS84
- Formato: `Lat. [gradi] N; Long. [gradi] E` oppure tabella UTMX/UTMY
- Verifica in: RT, Asseverazioni, B40 (Anagrafe Impianto)
- Tolleranza: valori identici fino alla sesta cifra decimale

**Esito:** ✅ / ❌

### B6 — Data Documento
- Tutti i documenti redatti lo stesso giorno (o in sequenza logica breve)
- L'Atto d'obbligo può avere una data leggermente diversa
- Attenzione a errori di digitazione dell'anno (es. "20256" invece di "2026")

**Esito:** ✅ / ❌ — Note: [eventuali date anomale]

### B7 — Municipio (solo per Roma Capitale)
- Il numero del Municipio deve corrispondere all'indirizzo del sito
- Verificare la coerenza tra numero municipio e indirizzo PEC nella SCIA
- Nota: i Municipi romani hanno numerazioni sia nuove che vecchie (es. XIV ex XIX)

**Esito:** ✅ / ❌

### B8 — Progettista Incaricato
- Deve essere uno dei tecnici K2A (Luca Rossi o Jessica Romanelli)
- CF, numero ordine e ordine di appartenenza devono essere corretti
- Verifica in: SCIA (nomina progettista), Asseverazioni (firma), B40 (curriculum allegato)

**Esito:** ✅ / ❌

### B9 — Sistema Radiomobile
- Formato atteso (tipico): `5G700/UMTS900/LTE1800/LTE2100/LTE2300/LTE2600/5G3700`
- Deve essere identico in: titolo RT, intestazione B40, SCIA (tipologia impianto)

**Esito:** ✅ / ❌

---

## C. CORRETTEZZA TECNICA — B40/RELAIE

Verifica che il documento B40 sia strutturato correttamente con tutte le sezioni richieste.

### C1 — Struttura e Indice

| Sezione | Titolo atteso | Presente |
|---------|--------------|----------|
| 1 | Anagrafe Impianto (1.1 Identificazione, 1.2 Gestore) | |
| 2 | Premessa | |
| 3 | Normativa (3.1 Riferimenti, 3.2 Legislazione Italiana DPCM 8/7/2003) | |
| 4 | Descrizione area e punto installazione (4.1-4.4) | |
| 5 | Caratteristiche radioelettiche SRB (5.1-5.4) | |
| 6 | Scheda radio impianto | |
| 7 | Valutazione impatto EM (7.1-7.2 con sottosezioni) | |
| 8 | Valutazione intensità campi elettrici (8.1-8.4) | |
| 9 | Conclusioni e attestazione conformità | |
| 10 | Allegati (cartografia, datasheet, curriculum, calibrazioni) | |

### C2 — Anagrafe Impianto (Sezione 1)

| Campo | Presente e compilato |
|-------|---------------------|
| Codice impianto | |
| Nome impianto | |
| Indirizzo | |
| Comune, Provincia, Regione | |
| Quota s.l.m. | |
| Coordinate WGS84 + UTMX/UTMY | |
| Denominazione gestore (Iliad Italia S.p.A.) | |
| Indirizzo sede legale gestore | |

### C3 — Scheda Radio (Sezione 6)

| Campo | Presente e compilato |
|-------|---------------------|
| Frequenze operative per ogni settore | |
| Potenze (EIRP per frequenza) | |
| Azimuth per settore | |
| Tilt meccanico/elettrico | |
| Tipo antenna | |
| Altezza antenna | |
| Guadagno antenna | |

### C4 — Punti Significativi e Misure (Sezione 7.2)

| Elemento | Presente |
|----------|----------|
| Sopralluogo documentato | |
| Metodologia di misura descritta | |
| Tabella punti di misura/stima con coordinate | |
| Planimetria con indicazione dei punti | |
| Documentazione fotografica dei punti | |
| Valori di campo EM preesistente misurato | |

### C5 — Calcoli EM e Volumi di Rispetto (Sezione 8)

| Elemento | Presente |
|----------|----------|
| Calcolo per frequenze 3 < f < 3000 MHz | |
| Calcolo per frequenze mmWave (se presenti antenne 5G mmWave) | |
| Volumi di rispetto calcolati (SLU 20 V/m, SLA 6 V/m, OQ 6 V/m) | |
| Isolinee orizzontali 6-15-20-40 V/m su planimetria 1:2000 | |
| Sezioni verticali con curve isocampo (una per settore) | |

### C6 — Allegati (Sezione 10)

| Allegato | Presente |
|----------|----------|
| Cartografia con settori e altre emittenti area | |
| Datasheet antenne | |
| Curriculum tecnico incaricato | |
| Copia certificati di calibrazione strumenti | |

### C7 — Conclusioni (Sezione 9)

- La sezione deve contenere: attestazione di conformità ai limiti di legge (DPCM 8/7/2003)
- Deve esplicitare che i valori calcolati sono inferiori a 6 V/m (valore di attenzione/obiettivo di qualità)
- Deve essere firmata dal tecnico incaricato

---

## D. CONFORMITÀ NORMATIVA

### D1 — Riferimenti normativi nella SCIA

| Norma | Da citare in | Verifica |
|-------|-------------|----------|
| D.Lgs. 259/2003 art. 43 (urbanizzazione primaria) | SCIA premessa | |
| D.Lgs. 259/2003 art. 45 (SCIA) | SCIA oggetto e titolo | |
| L. 36/2001 (legge quadro EM) | SCIA premessa | |
| D.P.R. 380/2001 art. 16, comma 7 | SCIA premessa | |
| Autorizzazione Generale MISE 25.07.2016 | SCIA premessa | |
| Procura Notaio Amato 10/04/2024, Rep. 63403/18598 | SCIA, Delega, Atto, DICH. | |

### D2 — Riferimenti nel B40/RELAIE

| Norma | Da citare | Verifica |
|-------|-----------|----------|
| L. 36/2001 | Sez. 3.1 | |
| DPCM 8 luglio 2003 | Sez. 3.1 e 3.2 | |
| D.Lgs. 259/2003 | Sez. 3.1 | |
| D.M. 2 dicembre 2014 (α24h) | Sez. 3.1 | |
| Raccomandazione CEE 1999/519/CE | Sez. 3.1 | |
| Direttiva 2004/40/CE | Sez. 3.1 | |

### D3 — Limiti di esposizione (DPCM 8/7/2003)

| Limite | Valore | Applicazione |
|--------|--------|-------------|
| Limite di esposizione | 20 V/m | Luoghi frequentati ≤ 4h/die |
| Valore di attenzione | 6 V/m | Luoghi frequentati ≥ 4h/die (interni) |
| Obiettivo di qualità | 6 V/m | Edifici adibiti a permanenza > 4h |

I valori sopra devono essere citati correttamente nel B40. Verifica che non siano riportati valori obsoleti (es. 61 V/m, 28 V/m o altri valori pre-L.214/2023).

### D4 — Dichiarazione Sostitutiva ALPHA24

| Elemento | Corretto |
|----------|---------|
| Richiamo D.M. 2 dicembre 2014 (MATTM) | |
| Richiamo L. 214/2023 art. 10 (modifica limiti EM) | |
| Entrata in vigore L. 214/2023 al 31/12/2023 | |
| Firma Andrea Longari con riferimento alla procura | |

### D5 — Atto d'obbligo

| Elemento | Corretto |
|----------|---------|
| Impegno a dismettere entro 3 mesi dalla fine utilizzazione | |
| Codice e nome sito corretti | |
| Data corretta (senza errori tipografici, es. "20256" al posto di "2026") | |
| Firma Andrea Longari con riferimento alla procura | |
| Contatti Permit Coordinator Iliad | |

---

## F. RESIDUI TEMPLATE (v0.3.0 — basato su lezioni-apprese L1-L12)

Cercare attivamente nel testo estratto da OGNI `.docx` del pacchetto le seguenti **stringhe-sonda**. Se una di queste compare nel pacchetto finale, è **NC BLOCCANTE** perché significa che il template non è stato pulito.

### F1 — Annotazioni rosse residue (stringhe letterali)

| Stringa | Tipo | Dove cercare | Priorità |
|---------|------|--------------|----------|
| `VERIFICARE CHE LA PROCURA SIA SEMPRE QUELLA DEL 04/2024` | inline | SCIA, Delega, Atto d'obbligo | 🔴 BLOCCANTE |
| `INSERIRE` | standalone/inline | Tutti | 🔴 BLOCCANTE |
| `DA VERIFICARE` | inline | Tutti | 🔴 BLOCCANTE |
| `SE PRESENTE` | inline | RT, ASSEV | 🔴 BLOCCANTE |
| `SOLO SE` | inline | RT, ASSEV | 🔴 BLOCCANTE |
| `O INFRASTRUTTURA SE PALO` | inline (L11) | RT | 🔴 BLOCCANTE |
| `[DA COMPILARE]` | placeholder | Tutti | 🔴 BLOCCANTE |
| `XXXXX` / `XXXX` / `XXX` | placeholder | Tutti | 🔴 BLOCCANTE |
| `yyyyy` | placeholder | Tutti | 🔴 BLOCCANTE |

### F2 — Valori sample da template (preesistenze fittizie — L2)

Questi valori **sample realistici** sono presenti nei template di origine e vanno sempre sostituiti. Se compaiono in un pacchetto finale, sono preesistenze FITTIZIE che non appartengono al sito reale.

| Stringa | Template origine | Priorità |
|---------|------------------|----------|
| `QF/2025/0126488` | 4.*_RT.docx (T3 R0 C1), 6.*_ASSEVERAZIONI.docx | 🔴 BLOCCANTE |
| `QF/2025/0126488 del 26/09/2025` | idem | 🔴 BLOCCANTE |
| `24/09/2025` (come data invio SCIA preesistente) | idem | 🔴 BLOCCANTE |
| `19436.U del 20/03/2023` (protocollo ARPA sample) | idem | 🔴 BLOCCANTE |
| `NA/13029 del 12/06/2023` (protocollo VAP sample) | idem | 🔴 BLOCCANTE |

### F3 — PRG T4 sample nel template (L3)

| Stringa | Dove | Priorità |
|---------|------|----------|
| `Città storica: Tessuti di espansione otto-novecentesca ad isolato – T4` | RT, ASSEV | 🟠 IMPORTANTE (verificare se corretta per la zona del sito) |

Se il sito è in periferia novecentesca (Tuscolana, Prenestina, ecc.) → la dicitura corretta è `T3 Città consolidata — Tessuti di espansione novecentesca a tipologia edilizia libera`. Segnalare come 🔴 BLOCCANTE se il sito è chiaramente in T3 e il pacchetto dice T4.

### F4 — Foto sito sample (L6)

Nel template `4.*_RT.docx` sono presenti `word/media/image1.jpeg` e `word/media/image2.jpeg` che sono foto di cantieri di altri siti. Verifica che:

1. Aprendo il `.docx` come zip, le foto `image1.jpeg` e `image2.jpeg` siano diverse da quelle del template originale
2. Le foto siano effettivamente del sito reale

Metodo operativo: estrarre le foto dal template ricevuto, confrontarle visivamente con le foto note del sito (se disponibili dalla Scheda Radio / PE / utente). Se identiche a quelle del template default → 🔴 BLOCCANTE.

### F5 — Red-color stripping non eseguito (L7)

Se aprendo il `.docx` si vede ancora testo in **rosso** (color `FF0000`) → il red-stripping finale non è stato eseguito. Anche se il testo non contiene annotazioni residue, il colore rosso è un indicatore visivo che il lavoro non è stato completato. 🟠 IMPORTANTE.

Metodo: cercare nel `word/document.xml` il pattern `<w:color w:val="FF0000"/>` — deve essere zero occorrenze.

### F6 — Aeroporto non pertinente (L4)

Nella RT e nelle Asseverazioni è presente una lista aeroporti (Fiumicino, Ciampino, Urbe, Pratica di Mare). Deve essere tenuto **SOLO** l'aeroporto di riferimento che compare nelle tavole del PDM (sezione 7.x del PDM — OLS / superficie di rispetto). Se compaiono più aeroporti simultaneamente → 🟠 IMPORTANTE.

### F7 — VAP non applicabile ma presente (L10)

Se il sito NON rientra nell'art. 5 co. 5 Delib. 78/2024 Roma, TUTTI i riferimenti VAP devono essere rimossi dal pacchetto:

- Riga vincoli `V.A.P. – ininfluente ai fini dell'intervento;`
- Preesistenza `Parere favorevole del Dipartimento Ciclo dei Rifiuti...`
- Allegato VAP nella SCIA (se presente)

Se il sito non è in VAP-zone e compaiono questi riferimenti → 🟠 IMPORTANTE.

### F8 — Alpha24 reference site generico (L8)

Nella `DICH. SOSTITUTIVA ALPHA24`, il reference site indicato deve essere quello definito nella **Scheda Radio** del sito in esame (sezione "Tecnica Antenna"), **NON** il codice sito stesso e **NON** un reference copiato da un altro pacchetto. Se il reference site = codice sito dichiarante → 🟠 IMPORTANTE (probabile errore).

---

## G. COERENZA RT ↔ ASSEVERAZIONI (v0.3.0 — L13 BLOCCANTE)

**Regola L13:** le Asseverazioni derivano dalla Relazione Tecnica. I dati urbanistici, paesaggistici, aeroportuali e le preesistenze devono essere **identici stringa per stringa** tra i due documenti.

Metodo operativo: estrarre il testo di `4.*_RT.docx` e `6.*_ASSEVERAZIONI.docx` e confrontare i seguenti elementi.

### G1 — Destinazione PRG

| Elemento | RT | ASSEV | Esito |
|----------|-----|-------|-------|
| Tavola PRG indicata (es. Tav. 3 - Sistemi e regole) | | | |
| Zona/tessuto (es. "T3 Città consolidata — Tessuti di espansione novecentesca") | | | |

Discrepanza → 🔴 BLOCCANTE

### G2 — Destinazione PTPR

| Elemento | RT | ASSEV | Esito |
|----------|-----|-------|-------|
| Tavola PTPR (A/B/C) | | | |
| Ambito (es. "Paesaggio degli insediamenti urbani") | | | |

Discrepanza → 🔴 BLOCCANTE

### G3 — Elenco vincoli

Confrontare voce per voce l'elenco vincoli di RT e ASSEV. Deve essere identico stringa per stringa (ordine, presenza/assenza di VAP, wording esatto).

Discrepanza → 🔴 BLOCCANTE

### G4 — ENAC Area interessata / non interessata

| Elemento | RT | ASSEV | Esito |
|----------|-----|-------|-------|
| Aeroporto di riferimento (Fiumicino / Ciampino / Urbe / Pratica di Mare) | | | |
| Area interessata / non interessata | | | |

Discrepanza → 🔴 BLOCCANTE (pattern che abbiamo visto: RT dice "interessata" perché corretto da PDM, ASSEV dice "non interessata" perché valore sample mai sostituito)

### G5 — Preesistenze SCIA/ARPA/VAP

| Preesistenza | RT | ASSEV | Esito |
|--------------|-----|-------|-------|
| SCIA precedente (protocollo DPU) | | | |
| Pagamento ARPA precedente (protocollo) | | | |
| VAP precedente (protocollo, se applicabile) | | | |

Discrepanza → 🔴 BLOCCANTE

### G6 — Cella "relazione precisazioni" ASSEV

Nella cella C0 P31 delle Asseverazioni deve essere presente un riassunto coerente della RT, NON il placeholder sample del template. Contenuti minimi attesi:

- Tipo intervento dichiarato nella RT
- Preesistenze citate in RT (con gli stessi protocolli)
- Conformità urbanistica come dichiarata in RT
- Eventuale esclusione VAP ex art. 5 co. 5 Delib. 78/2024 (se applicabile in RT)

Se la cella è vuota, contiene placeholder o contiene testo incoerente con la RT → 🔴 BLOCCANTE

---

## Griglia di Priorità Rilievi

| Priorità | Definizione |
|----------|-------------|
| 🔴 BLOCCANTE | Impedisce la presentazione della pratica. Correggi prima di qualsiasi invio. |
| 🟠 IMPORTANTE | Deve essere corretto prima della presentazione. |
| 🟡 MINORE | Migliorativo o non critico. Da correggere se possibile. |

---

## Procedura di verifica automatizzata RT ↔ ASSEV (consigliata)

Per eseguire le verifiche G1–G6 in modo sistematico, lo script suggerito è:

```python
import docx2txt, re

rt_text = docx2txt.process("4.<CODE>_<NAME>_RT.docx")
assev_text = docx2txt.process("6.<CODE>_<NAME>_ASSEVERAZIONI.docx")

# Estrazione canonica PRG
prg_rt = re.search(r"(T\d\s*(?:Città\s+(?:storica|consolidata|da\s+ristrutturare))[^\n.]+)", rt_text)
prg_as = re.search(r"(T\d\s*(?:Città\s+(?:storica|consolidata|da\s+ristrutturare))[^\n.]+)", assev_text)
assert prg_rt and prg_as and prg_rt.group(1).strip() == prg_as.group(1).strip(), "G1 FAIL"

# ENAC
enac_rt = "non interessata" in rt_text
enac_as = "non interessata" in assev_text
assert enac_rt == enac_as, "G4 FAIL"

# Preesistenze SCIA
scia_rt = re.findall(r"QF/\d{4}/\d{7}", rt_text)
scia_as = re.findall(r"QF/\d{4}/\d{7}", assev_text)
assert set(scia_rt) == set(scia_as), "G5 FAIL (SCIA)"

# ARPA
arpa_rt = re.findall(r"\d{4,6}\.U\s+del\s+\d{2}/\d{2}/\d{4}", rt_text)
arpa_as = re.findall(r"\d{4,6}\.U\s+del\s+\d{2}/\d{2}/\d{4}", assev_text)
assert set(arpa_rt) == set(arpa_as), "G5 FAIL (ARPA)"

print("RT ↔ ASSEV OK")
```

Lo script produce uscita ESITO OK se tutti i check passano, altrimenti solleva l'asserzione fallita che identifica il punto della checklist G non conforme.

---

## H. VERIFICHE AGGIUNTIVE v0.4.0 (L14–L22)

### H1 — Permit Coordinator (L14)

Verificare che il Permit Coordinator sia **identico** in doc 1 (SCIA), doc 9 (DICH. SOSTITUTIVA α24), doc 10 (Atto d'obbligo). Confrontare con il valore presente nella **preesistenza** (se disponibile).

| Documento | Permit indicato | Da preesistenza | Esito |
|-----------|----------------|-----------------|-------|
| SCIA (doc 1) | | | |
| DICH. SOSTITUTIVA (doc 9) | | | |
| Atto d'obbligo (doc 10) | | | |

Discrepanza tra documenti → 🔴 BLOCCANTE
Discrepanza con preesistenza → 🟠 IMPORTANTE

### H2 — Codice reversale nella SCIA (L15)

La SCIA deve contenere il codice reversale del pagamento dei diritti. Se assente o placeholder → 🟠 IMPORTANTE.

### H3 — Foto non deformata nella RT (L16)

Aprire il `.docx` della RT e verificare visivamente che le foto (copertina + ultima pagina) non siano deformate (stirate/compresse). Metodo: confrontare aspect ratio dell'immagine nel zip con le dimensioni `<wp:extent>` nel XML.

Foto deformata → 🟠 IMPORTANTE

### H4 — Proprietà infrastruttura corretta nella RT (L17)

Nella tabella "1. Dati identificativi dell'immobile" della RT, verificare che il campo proprietà corrisponda al proprietario reale dell'infrastruttura (da preesistenza).

| RT dice | Preesistenza dice | Esito |
|---------|-------------------|-------|
| | | |

Discrepanza → 🔴 BLOCCANTE (es. "SITE S.p.A." quando il sito è Cellnex)

### H5 — Codici tavole PRG corrispondono alla cartografia PDF (L18)

Confrontare i codici tavola citati nel testo della RT (es. "Tav. 3_18") con i nomi/titoli dei PDF cartografici allegati al pacchetto.

| Tavola citata in RT | PDF allegato | Esito |
|---------------------|-------------|-------|
| | | |

Discrepanza → 🔴 BLOCCANTE

### H6 — Didascalia PRG coerente con zona reale (L19)

La didascalia sotto lo stralcio PRG nella RT deve riportare la zona corretta del sito, NON il testo sample del template. Confrontare con la verifica WebGIS o con la preesistenza.

Testo sample del template ancora presente → 🔴 BLOCCANTE

### H7 — Zona sismica corretta (L20)

| RT dice | Valore corretto (PE/INGV/Regione Lazio) | Esito |
|---------|------------------------------------------|-------|
| | Roma = Zona 2B (DGR 387/2009) | |

Discrepanza → 🔴 BLOCCANTE

### H8 — Descrizione area di intervento personalizzata (L21)

La sezione 2 della RT deve descrivere l'area reale del sito (quartiere, contesto edilizio, tipo infrastruttura), NON il testo sample del template.

Indicatori di testo sample: se il quartiere descritto non corrisponde all'indirizzo del sito, o se la descrizione è identica a quella del template originale → 🔴 BLOCCANTE.

### H9 — Tabella parabole compilata (L22)

Se il sito ha parabole/ponti radio → la tabella deve essere compilata con dati reali dalla Scheda Radio.
Se il sito NON ha parabole → la tabella deve riportare "Nessuna parabola" o essere vuota con nota.
Se la tabella è vuota senza nota OPPURE contiene dati sample → 🟠 IMPORTANTE.
