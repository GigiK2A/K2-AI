---
name: redazione-pacchetto
description: >
  Questa skill deve essere usata quando l'utente vuole "redigere il pacchetto", "creare il
  pacchetto autorizzativo", "fare la SCIA per iliad", "preparare i documenti del sito",
  "compilare il pacchetto per il comune", "redigi la SCIA art. 45", "crea i documenti per
  l'autorizzazione iliad", "fai il pacchetto per [codice sito]", oppure quando fornisce dati
  di un sito iliad (codice sito, indirizzo, scheda radio, progetto architettonico) chiedendo
  la redazione completa dei documenti.
metadata:
  version: "0.5.0"
  author: "K2A s.r.l.s."
---

# Redazione Pacchetto Autorizzativo Iliad (SCIA art. 45) — v0.5.0

Redigi il pacchetto autorizzativo completo per una Stazione Radio Base Iliad Italia S.p.A. mediante procedura SCIA ai sensi dell'art. 45 D.Lgs. 259/2003.

---

## FASE 0-BIS — Letture OBBLIGATORIE (non saltare MAI)

Prima di Fase 0 (ricerche web) e di qualsiasi altra operazione, **leggere tassativamente e nell'ordine**:

1. `references/lezioni-apprese.md` — catalogo errori + soluzioni canoniche (L1–L13). Qualsiasi errore già visto in sessioni precedenti è qui. **Se lo ripeti, è una tua responsabilità.**
2. `references/annotazioni-template.md` — classificazione INLINE vs STANDALONE delle annotazioni rosse presenti nei template (evita di cancellare interi paragrafi utili, es. procura Longari)
3. `references/valori-sample-template.md` — valori sample realistici nei template che **vanno sempre sostituiti** (preesistenze SCIA/ARPA/VAP, PRG T4 default, foto sito, ecc.)
4. `references/post-processing.md` — procedure tecniche di pulizia finale dei `.docx` (red-color stripping, sostituzione foto via zipfile, cancellazione aeroporti non pertinenti, rimozione VAP, sanity-check finale)
5. `references/domande-obbligatorie.md` — checklist di domande da porre all'utente con `AskUserQuestion` prima di toccare qualsiasi file

**Se NON si leggono questi 5 file, fermarsi e leggerli.** È il modo in cui la skill mantiene memoria tra sessioni.

---

## FASE 0-TER — Diagnostica Template

Appena l'utente carica i template `.docx`, eseguire diagnostica PRIMA di scrivere qualsiasi `edit_*.py`:

1. Lanciare lo script `trova_annotazioni_rosse` descritto in `annotazioni-template.md` su **tutti** i template caricati, per elencare tutti i pattern rossi presenti
2. Listare `word/media/*` di ogni template per identificare foto sample da sostituire (criterio: `.jpeg` > 100KB probabile foto sito; < 20KB probabile logo)
3. Confrontare le annotazioni trovate con quelle catalogate in `annotazioni-template.md`:
   - Se una annotazione è **già catalogata** → applicare la soluzione canonica (INLINE → `replacements`; STANDALONE → `annotation_markers`)
   - Se una annotazione è **nuova** → chiedere all'utente come gestirla e **aggiornare immediatamente `annotazioni-template.md`** con la nuova voce

---

## FASE 0-QUATER — Checklist Q&A (bloccante)

Prima di scrivere qualsiasi `edit_*.py`, porre le domande dei blocchi 1–10 di `references/domande-obbligatorie.md` usando il tool `AskUserQuestion`.

**NON procedere** finché:
- Tutti i campi critici (Blocchi 1, 2, 3, 6) sono valorizzati
- L'utente ha confermato esplicitamente la checklist compilata
- Sono stati raccolti tutti i protocolli delle preesistenze (SCIA DPU, ARPA, VAP se applicabile)
- È stata scelta esplicitamente la figura Progettista e, se diverso, il Direttore dei Lavori
- È stato identificato il reference site Alpha24 leggendolo dalla Scheda Radio (mai assumere)

---

## REGOLA ANTI-MEMORIA-CORTA

Se l'utente dice frasi tipo:
- "te lo avevo detto"
- "l'avevamo già risolto"
- "hai dimenticato"
- "ci abbiamo lavorato troppo"
- "ogni volta ripeti gli stessi errori"

→ è un **segnale CHIARO** che `references/lezioni-apprese.md` va AGGIORNATO **ORA**. Aggiungere una nuova voce L-next che cattura il problema, la causa, la regola canonica. Questo è il **ciclo di auto-miglioramento** del plugin. Non rispondere con scuse: apri il file e aggiungi la voce.

---

## ORDINE DI REDAZIONE DOCUMENTI (VINCOLANTE — vedi L13)

I documenti del pacchetto NON sono indipendenti. Esiste un ordine obbligatorio di redazione perché alcuni documenti **derivano** da altri:

```
1. SCIA art. 45            (doc 1)
2. Delega                  (doc 2)
3. RELAZIONE TECNICA (RT)  (doc 4)  ← DOCUMENTO MASTER
4. ASSEVERAZIONI           (doc 6)  ← DERIVA DALLA RT (L13)
5. Atto d'obbligo          (doc 10)
6. Dich. Sostitutiva α24h  (doc 9)
7. Impegno ARPA            (doc 8)
8. B40/RELAIE              (doc 7)
```

**Regola L13 — Asseverazioni derivano dalla RT:**
- La RT è il documento **master**: contiene PRG, PTPR, vincoli, ENAC, preesistenze, descrizione intervento nella loro forma canonica.
- Le Asseverazioni **riprendono** questi stessi valori (cella "relazione precisazioni" C0 P31 + tabella PRG/PTPR/ENAC).
- **MAI compilare `edit_asseverazioni.py` prima di aver completato e validato `edit_rt.py`.**
- Implementazione: `edit_asseverazioni.py` deve usare **lo stesso dizionario `SITO`** di `edit_rt.py` (o rileggere l'output di RT per estrarne i valori canonici).
- **Sanity-check incrociato obbligatorio** dopo aver generato entrambi: PRG, PTPR, ENAC, vincoli, preesistenze devono essere **identici stringa per stringa** tra RT e ASSEV. Se c'è una discrepanza → non consegnare il pacchetto.

---

## PRINCIPI FONDAMENTALI (leggere PRIMA di qualsiasi operazione)

### Principio 1 — Template Immodificabili

I documenti base del pacchetto (SCIA, Delega, RT, Asseverazioni, Impegno ARPA, Dich. Sostitutiva, Atto d'obbligo) sono **template preesistenti** che vanno **SOLO compilati nelle parti variabili**, MAI ricreati da zero.

**Regole operative:**
- Se l'utente fornisce un file `.docx` come template base, quel file va **editato**, non riscritto
- Per editare un `.docx` senza alterare formattazione, stili, intestazioni e piè di pagina, usare il metodo **zipfile + XML raw**:
  1. Aprire il `.docx` con `zipfile` in Python
  2. Leggere `word/document.xml`
  3. Cercare i placeholder o i testi da sostituire con `xml.etree.ElementTree` o regex
  4. Sostituire SOLO le parti variabili (codice sito, nome, indirizzo, catasto, coordinate, ecc.)
  5. Riscrivere il `.docx` con il contenuto XML aggiornato
- **NON usare python-docx** per riscrivere il documento intero: distrugge la formattazione originale
- Se non è disponibile un template `.docx`, generare il documento seguendo fedelmente la struttura in `references/struttura-documenti.md`

### Principio 2 — Checklist Obbligatoria Prima della Compilazione

Prima di toccare qualsiasi template o generare qualsiasi documento, DEVI:

1. **Identificare tutte le sorgenti dati** disponibili:
   - Preesistenza (pacchetto già presentato in precedenza per lo stesso sito)
   - Scheda Radio (B40/TSSR PDF o FILETX.xlsx)
   - Progetto Esecutivo (PE) / Progetto Architettonico
   - Input diretto dell'utente
2. **Compilare la checklist dati** (vedi `references/checklist-compilazione-rt.md`) verificando per ciascun dato:
   - ✅ Trovato → indicare sorgente e valore
   - ❌ Non trovato → segnare come `[DA COMPILARE — richiede: descrizione]`
   - ⚠️ Discordanza tra sorgenti → chiedere all'utente quale valore adottare
3. **Presentare la checklist compilata all'utente** e ottenere conferma PRIMA di procedere alla redazione

### Principio 3 — Gerarchia di Prevalenza Dati

Quando lo stesso dato compare in più sorgenti, applicare questa gerarchia:

| Dato | Sorgente prevalente | Fallback |
|------|---------------------|----------|
| Codice sito e nome sito | Scheda Radio | Preesistenza |
| Indirizzo completo | Preesistenza (se corretta) | PE → Scheda Radio |
| Dati catastali (Foglio, P.lla, Sez.) | Preesistenza | PE |
| Coordinate WGS84 | Scheda Radio | PE |
| Municipio (Roma) | Preesistenza | Verifica web |
| Zona sismica | PE (relazione strutturale) | Preesistenza |
| Destinazione PRG (Tav. 3, 4, G1) | Verifica web PRG Roma | Preesistenza (**attenzione**: le tavole PRG variano per zona!) |
| Destinazione PTPR (Tav. A, B, C) | Verifica web PTPR Lazio | Preesistenza |
| Vincoli paesaggistici/monumentali | Preesistenza (SOLO da questa sorgente) | — |
| Wording legittimità impianto | Preesistenza (copiare ESATTAMENTE) | — |
| Sistema radiomobile | Scheda Radio | FILETX.xlsx |
| Quota s.l.m. | PE | Scheda Radio |
| Proprietà infrastruttura | Preesistenza | Utente |
| Tipo sito (RT/RL/Palo su edificio) | PE | Preesistenza |
| Tecnico incaricato | Utente | — |

**In caso di dubbio su qualsiasi dato → CHIEDERE SEMPRE all'utente.**

### Principio 4 — La RT è il Documento Master

La **Relazione Tecnica (RT)** è il documento più completo del pacchetto: contiene tutti i dati identificativi, urbanistici, catastali, tecnici e procedurali del sito. Se la RT è compilata correttamente, tutti gli altri documenti del pacchetto ne derivano senza necessità di richiedere dati aggiuntivi all'utente.

**Regole operative:**
- Se l'utente fornisce una RT già compilata (anche parzialmente), **estraila per prima** come sorgente dati primaria per tutti gli altri documenti
- I dati presenti nella RT hanno priorità rispetto all'input diretto dell'utente, tranne in caso di evidente errore
- Quando si completa la RT, automaticamente si hanno i dati per compilare: SCIA, Delega, Asseverazioni, Impegno ARPA, DICH. SOSTITUTIVA, Atto d'obbligo
- Usa la RT anche come checklist di completezza: i campi `[DA COMPILARE]` nella RT indicano le lacune da colmare per il pacchetto completo

---

## Fase 0 — Ricerche Web Obbligatorie (SEMPRE all'avvio)

Prima di iniziare la raccolta dati, eseguire ricerche web per aggiornare i componenti variabili del pacchetto. Consultare `references/componenti-variabili.md` per le query specifiche.

**Ricerche obbligatorie:**
1. **PEC destinatari** — DPU Roma Capitale, SUAP, Poteri Sostitutivi, Municipio specifico, ARPA Lazio; per comuni fuori Roma: SUAP del comune
2. **Aggiornamenti normativi** — art. 45 D.Lgs. 259/2003, DPCM attuativi L. 214/2023 limiti EM, D.M. 2014 α24h
3. **Tariffe ARPA Lazio** aggiornate per impegno al pagamento
4. **PRG/PTPR del sito** tramite WebGIS Roma o ricerca online (se indirizzo disponibile)
5. **Validità procura Iliad** (Longari, 10/04/2024) — segnalare se prossima alla scadenza
6. **Nulla Osta Cellnex** (se sito in ospitalità) — versione aggiornata
7. **Regolamento Roma** — consultare `references/regolamento-roma.md` per verificare: aree preferenziali (Art. 3), divieto siti sensibili (Art. 4), obbligo VAP (Art. 5 co. 5) in base alla zona PRG del sito

Se una ricerca non restituisce risultati certi: usare il valore noto più recente e segnare ⚠️ **verifica manuale consigliata**.

---

## Fase 1 — Raccolta Dati di Base

Chiedi (o estrai dai file forniti) i seguenti dati minimi obbligatori per iniziare:

1. **Codice sito** (es. `RM00168_005`)
2. **Nome sito** (es. `VIA DI TORREVECCHIA`)
3. **Indirizzo** (via, numero civico)
4. **Comune** e **Municipio** (se Roma)
5. **Dati catastali** (Foglio, Particella, Sezione)
6. **Coordinate WGS84** (Lat N, Long E)
7. **Data redazione** (gg/mm/aaaa)
8. **Tecnico incaricato** (Ing. Luca Rossi o Ing. Jessica Romanelli)
9. **Sistema radiomobile** (es. `5G700/UMTS900/LTE1800/LTE2100/LTE2300/LTE2600/5G3700`)
10. **Quota s.l.m.** (quota dell'impianto in metri)
11. **Tipo sito** (Rooftop su edificio / Raw Land / Palo su edificio)
12. **Proprietà infrastruttura** (Cellnex Italia S.p.A. / altro)

Se l'utente fornisce la scheda radio (B40/TSSR PDF o file FILETX.xlsx), estrai da lì i dati tecnici radio (vedi `references/dati-sito.md`).

Se l'utente fornisce il progetto architettonico (PE), estrai da lì l'indirizzo, i dati catastali, la quota e le coordinate.

Se l'utente fornisce una **preesistenza** (pacchetto precedente), estrai i dati identificativi, vincoli, wording legittimità e destinazione PRG/PTPR. **ATTENZIONE**: i vincoli e il wording legittimità vanno presi SOLO dalla preesistenza.

**Dopo aver raccolto i dati: compilare e presentare la checklist** (`references/checklist-compilazione-rt.md`) all'utente per conferma.

---

## Fase 2 — Redazione Documenti

Redigi i documenti nell'ordine seguente, usando i template in `references/struttura-documenti.md`. Per ogni documento:
- Se è disponibile un template `.docx` dell'utente: **editalo** con zipfile/XML (Principio 1)
- Se non è disponibile: genera il file `.docx` usando lo skill `docx`
- Salva ogni file nella cartella di lavoro con la nomenclatura corretta

**Ordine di redazione (VINCOLANTE — vedi L13 per la regola RT → ASSEV):**

1. **SCIA art. 45** (doc 1) — documento principale
2. **Delega alla presentazione** (doc 2)
3. **RT — Relazione Tecnica** (doc 4) — **DOCUMENTO MASTER**: PRG, PTPR, ENAC, vincoli, preesistenze, descrizione intervento nella loro forma canonica. DEVE essere finalizzato prima di procedere alla ASSEV.
4. **ASSEVERAZIONI** (doc 6) — **DERIVATO dalla RT**: i valori PRG/PTPR/ENAC/vincoli/preesistenze devono coincidere stringa per stringa con la RT. `edit_asseverazioni.py` deve usare lo stesso dizionario `SITO` di `edit_rt.py` o rileggere l'output della RT.
5. **Atto d'obbligo** (doc 10)
6. **DICH. SOSTITUTIVA ALPHA24** (doc 9) — reference site SEMPRE da Scheda Radio, mai assumere
7. **Impegno pagamento ARPA** (doc 8)
8. **B40/RELAIE** (doc 7) — richiede dati tecnici radio completi

**Sanity-check incrociato RT ↔ ASSEV (obbligatorio):** dopo aver generato entrambi i documenti, confrontare PRG, PTPR, ENAC, elenco vincoli, preesistenze SCIA/ARPA/VAP. Se c'è una sola discrepanza → il pacchetto NON è consegnabile.

I documenti 3 (MISE-PROCURA), 5 (PDM) e 13 (Nulla Osta Cellnex) sono **file fissi** già in formato PDF — non vanno redatti ma solo inclusi nel pacchetto.

---

## Fase 3 — Integrazione Dati Progressiva

Man mano che l'utente fornisce materiali aggiuntivi, aggiorna i documenti:

- **Scheda Radio (B40/TSSR PDF)** → aggiorna la scheda radio nel B40, le frequenze nella SCIA e nella RT
- **FILETX.xlsx** → estrai i parametri EM per il B40 (potenze, azimuth, tilt, coordinate punti)
- **Progetto Architettonico (PE)** → estrai foto del sito, planimetrie, quote edifici per il B40 (sezione 4 e 7.2)
- **PDM (Piano di Misurazione ARPA)** → includi nel pacchetto come doc 5 senza modifiche
- **Misure di campo EM** (se fornite) → integra nella sezione 7.2 del B40
- **Preesistenza** → estrai vincoli, wording legittimità, destinazione PRG/PTPR, dati catastali

---

## Fase 4 — Nomenclatura File

Usa sempre la nomenclatura standard:

```
[N].[CODICE_SITO]_[NOME_SITO]_[TipoDocumento].docx
```

Esempi:
- `1.RM00168_005_VIA DI TORREVECCHIA_Scia art. 45.docx`
- `2.RM00168_005_VIA DI TORREVECCHIA_Delega alla presentazione.docx`
- `4.RM00168_005_VIA DI TORREVECCHIA_RT.docx`
- `6.RM00168_005_VIA DI TORREVECCHIA_ASSEVERAZIONI.docx`
- `7.RM00168_005_VIA DI TORREVECCHIA_B40_RELAIE.docx`
- `8.RM00168_005_VIA DI TORREVECCHIA_Impegno al pagamento art. 45 singolo operatore_Arpa Roma.doc`
- `9.RM00168_005_VIA DI TORREVECCHIA_DICH. SOSTITUTIVA ALPHA24.docx`
- `10.RM00168_005_VIA DI TORREVECCHIA_Atto d'obbligo.docx`

---

## Fase 5 — Verifica Finale

Al termine della redazione, prima di consegnare il pacchetto:
1. Esegui una verifica incrociata dei dati identificativi tra tutti i documenti generati
2. Controlla che tutti i campi `[DA COMPILARE]` siano stati risolti
3. Verifica la coerenza dei dati con la checklist compilata in Fase 1
4. Segnala eventuali dati mancanti che impediscono la finalizzazione
5. Verifica che i PEC e i riferimenti normativi siano quelli aggiornati dalla Fase 0

---

## Regole Importanti

- **Non inventare dati**: se un campo non è disponibile, scrivi `[DA COMPILARE — richiede: descrizione del dato]`
- **Dati fissi Iliad**: usa sempre i dati aziendali fissi in `references/dati-sito.md` (CF, sede legale, procura, ecc.)
- **Municipio Roma**: ricava il Municipio dall'indirizzo o dal codice sito — non assumere; per i comuni fuori Roma omettere il Municipio
- **Progettista**: usa i dati corretti del tecnico incaricato (Luca Rossi o Jessica Romanelli) da `references/dati-sito.md`
- **Stralci PRG/PTPR**: nella RT sono presenti tabelle PRG/PTPR — le tavole variano per zona della città, verificare sempre con la Fase 0
- **Vincoli**: i vincoli paesaggistici e monumentali vanno presi ESCLUSIVAMENTE dalla preesistenza
- **Wording legittimità**: il testo che descrive la legittimità dell'impianto va copiato ESATTAMENTE dalla preesistenza
- **Documentazione fotografica**: richiede immagini reali del sito — segna come `[INSERIRE FOTO]` se non disponibili
- **Misure di campo EM**: i valori numerici nel B40 (sezione 7.2 e 8) richiedono dati reali delle misure o del software di simulazione
- **Template .docx**: MAI ricreare da zero un template fornito dall'utente — editare SOLO le parti variabili
- **Regolamento Roma**: applicare sempre le regole di `references/regolamento-roma.md` per siti nel Comune di Roma — verificare aree preferenziali, siti sensibili e necessità VAP
- **RT come sorgente dati**: se l'utente fornisce una RT, estraila PRIMA di qualsiasi altra operazione e usala come base per tutti gli altri documenti
- **RT prima di ASSEV** (L13): le Asseverazioni sono un derivato della Relazione Tecnica — mai compilarle prima che la RT sia completa e validata. Vedi `lezioni-apprese.md` § L13
- **Red stripping obbligatorio** nei template RT e ASSEV dopo le sostituzioni — vedi `post-processing.md`
- **Sostituzione foto sito** obbligatoria nel template RT — vedi `post-processing.md` § "Sostituzione Foto Sito"
- **Reference aeroporto** da leggere SEMPRE dal PDM (tavole 7.x), mai assumere — vedi `lezioni-apprese.md` § L4
- **VAP applicabilità** da verificare SEMPRE prima di lasciare riferimenti VAP nei documenti — vedi `lezioni-apprese.md` § L10
- **Alpha24 reference site** da leggere SEMPRE dalla Scheda Radio, mai copiare tra sessioni — vedi `lezioni-apprese.md` § L8
- **Progettista vs DL** da chiedere esplicitamente all'inizio — vedi `domande-obbligatorie.md` Blocco 3
- **Sanity-check incrociato RT ↔ ASSEV** obbligatorio — vedi L13 e `post-processing.md` § "Sanity-Check Finale"
- **Aggiornamento `lezioni-apprese.md`**: ogni volta che un bug emerge in sessione, aggiungere una nuova voce L-next. Se l'utente dice "te lo avevo detto" → aggiorna subito il file.
