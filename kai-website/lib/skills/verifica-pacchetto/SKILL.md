---
name: verifica-pacchetto
description: >
  Questa skill deve essere usata quando l'utente vuole "verificare il pacchetto", "controllare il
  pacchetto autorizzativo", "check del pacchetto iliad", "revisionare la SCIA", "controllare i
  documenti del sito", "verificare la completezza del pacchetto", "controllare la coerenza dei
  dati", "trovare errori nel pacchetto", "audit del pacchetto autorizzativo", "verifica RT vs
  Asseverazioni", "controllo residui template", "check preesistenze fittizie", "verifica ENAC
  Ciampino", oppure quando carica documenti di un pacchetto SCIA art. 45 per impianti iliad e
  chiede una verifica sistematica secondo la checklist aggiornata v0.5.0 (aree A-H, lezioni L1-L22).
metadata:
  version: "0.5.0"
  author: "K2A s.r.l.s."
---

# Verifica Pacchetto Autorizzativo Iliad (SCIA art. 45) — v0.5.0

Esegui una verifica sistematica e completa di un pacchetto autorizzativo iliad già redatto. Produci un report strutturato di conformità con esito per ogni punto.

## Flusso di Verifica

### Step -1 — Letture OBBLIGATORIE (memoria persistente del plugin)

Prima di qualsiasi operazione, leggere:

1. `references/lezioni-apprese.md` — catalogo anti-pattern (L1–L13) da cercare attivamente nei pacchetti in verifica
2. `references/annotazioni-template.md` — residui tipici di annotazioni template non rimosse (es. "VERIFICARE CHE", "INSERIRE", "SE PRESENTE") da segnalare come NC
3. `references/valori-sample-template.md` — valori sample dei template (es. `QF/2025/0126488`, `19436.U del 20/03/2023`, `Città storica … T4`) che se presenti in un pacchetto finale sono **NC BLOCCANTE**
4. `references/post-processing.md` — sanity-check finale da eseguire in fase di verifica: residui rossi, foto sample, aeroporti non pertinenti, riferimenti VAP disallineati

**Regola speciale di verifica (L13):** confrontare PRG/PTPR/ENAC/vincoli/preesistenze tra `4.*_RT.docx` e `6.*_ASSEVERAZIONI.docx`. Se c'è **anche una sola discrepanza** stringa per stringa → NC BLOCCANTE perché le Asseverazioni devono derivare dalla RT.

---

### Step 0 — Ricerche Web Obbligatorie (SEMPRE all'avvio)

Prima di iniziare la verifica, eseguire ricerche web per disporre dei riferimenti aggiornati. Consultare il file `references/componenti-variabili.md` (nella skill gemella `redazione-pacchetto`) per le query specifiche.

**Ricerche obbligatorie:**
1. **PEC destinatari aggiornate** — DPU Roma Capitale, SUAP, Poteri Sostitutivi, Municipio specifico, ARPA Lazio; per comuni fuori Roma: SUAP del comune
2. **Aggiornamenti normativi** — verificare se ci sono modifiche all'art. 45 D.Lgs. 259/2003, nuovi DPCM attuativi L. 214/2023 limiti EM, aggiornamenti D.M. 2014 α24h
3. **Tariffe ARPA Lazio** — verificare importi aggiornati per l'impegno al pagamento
4. **Validità procura Iliad** (Longari, 10/04/2024) — segnalare se prossima alla scadenza o sostituita

Se una ricerca non restituisce risultati certi: usare il valore noto più recente (da `references/documenti-richiesti.md`) e aggiungere ⚠️ **verifica manuale consigliata** nel report.

---

### Step 1 — Raccolta documenti

Prima di iniziare, verifica quali documenti sono disponibili. Chiedi all'utente di fornire (o indicare il percorso de) i file del pacchetto da verificare. I documenti attesi sono elencati in `references/documenti-richiesti.md`.

Se l'utente ha già caricato i file o indicato la cartella, procedi direttamente.

### Step 2 — Lettura documenti

Leggi il contenuto di ciascun documento disponibile. Per i file `.docx` usa Python con `zipfile` + `xml.etree.ElementTree` per estrarre il testo da `word/document.xml`. Per i `.pdf` usa strumenti PDF disponibili.

Estrai e annota per ogni documento:
- Codice sito (es. RM00168_005)
- Nome sito (es. VIA DI TORREVECCHIA)
- Indirizzo (via, numero civico)
- Comune e Municipio (se Roma)
- Dati catastali (Foglio, Particella, Sezione)
- Coordinate WGS84 (Lat, Long)
- Data documento
- Progettista incaricato
- Sistema radiomobile dichiarato
- PEC destinatari utilizzate

### Step 3 — Verifica per aree

Esegui la verifica secondo le **otto aree** della checklist in `references/checklist-verifica.md`:

1. **A. COMPLETEZZA** — tutti i documenti obbligatori sono presenti?
2. **B. COERENZA DATI** — i dati identificativi del sito sono identici in tutti i documenti?
3. **C. CORRETTEZZA TECNICA** — il B40/RELAIE è strutturato correttamente? Le sezioni sono tutte presenti e compilate?
4. **D. CONFORMITÀ NORMATIVA** — i riferimenti normativi sono corretti e aggiornati? (confrontare con i risultati dello Step 0)
5. **E. PEC E DESTINATARI** — le PEC dei destinatari nella SCIA corrispondono a quelle aggiornate dallo Step 0?
6. **F. RESIDUI TEMPLATE** (v0.3.0) — cercare nel pacchetto le stringhe canoniche di annotazioni rimaste (`VERIFICARE CHE`, `INSERIRE`, `SOLO SE`, `SE PRESENTE`, `DA VERIFICARE`, `XXXXX`) e i valori sample catalogati in `valori-sample-template.md` (`QF/2025/0126488`, `19436.U del 20/03/2023`, `Città storica … T4`, ecc.). Se presenti → NC BLOCCANTE.
7. **G. COERENZA RT ↔ ASSEV** (v0.3.0, L13) — confronto stringa per stringa di PRG, PTPR, ENAC, elenco vincoli, preesistenze SCIA/ARPA/VAP tra `4.*_RT.docx` e `6.*_ASSEVERAZIONI.docx`. Ogni discrepanza → NC BLOCCANTE.
8. **H. VERIFICHE v0.5.0** (L14–L22) — Permit Coordinator identico in SCIA/DICH/Atto (L14), codice reversale presente in SCIA (L15), foto non deformata in RT (L16), proprietà infrastruttura corretta (L17), codici tavole PRG corrispondenti ai PDF allegati (L18), didascalia PRG coerente (L19), zona sismica corretta (L20), descrizione area personalizzata (L21), tabella parabole compilata (L22).

### Step 4 — Report di verifica

Produci un report strutturato in formato markdown con:

```
# REPORT DI VERIFICA PACCHETTO AUTORIZZATIVO
## Sito: [CODICE] – [NOME SITO]
## Data verifica: [DATA]
## Versione skill: v0.5.0

### A. COMPLETEZZA DOCUMENTI
| # | Documento | Presente | Note |
|---|-----------|----------|------|
...

### B. COERENZA DATI IDENTIFICATIVI
| Campo | Doc 1 | Doc 2 | ... | Esito |
|-------|-------|-------|-----|-------|
...

### C. CORRETTEZZA TECNICA (B40/RELAIE)
| Sezione | Presente/Compilata | Note |
...

### D. CONFORMITÀ NORMATIVA
| Riferimento | Verificato | Note |
...

### E. PEC E DESTINATARI
| Destinatario | PEC nel pacchetto | PEC aggiornata (web) | Esito |
...

### F. RESIDUI TEMPLATE (v0.3.0 — controllo lezioni L1-L12)
| Check | File | Stringa trovata | Priorità | Esito |
|-------|------|-----------------|----------|-------|
| F1 Annotazioni rosse residue | | | | |
| F2 Valori sample preesistenze | | | | |
| F3 PRG T4 sample | | | | |
| F4 Foto sito sample | | | | |
| F5 Red color residuo | | | | |
| F6 Aeroporto non pertinente | | | | |
| F7 VAP presente ma non applicabile | | | | |
| F8 Alpha24 reference generico | | | | |

### G. COERENZA RT ↔ ASSEVERAZIONI (v0.3.0 — L13 BLOCCANTE)
| Check | RT | ASSEV | Esito |
|-------|-----|-------|-------|
| G1 PRG (tavola + zona) | | | |
| G2 PTPR (tavola + ambito) | | | |
| G3 Elenco vincoli | | | |
| G4 ENAC (aeroporto + area int./non int.) | | | |
| G5 Preesistenze SCIA/ARPA/VAP | | | |
| G6 Cella "relazione precisazioni" coerente con RT | | | |

### H. VERIFICHE v0.5.0 (L14-L22)
| Check | Verifica | Esito |
|-------|----------|-------|
| H1 Permit Coordinator identico in SCIA/DICH/Atto | | |
| H2 Codice reversale presente in SCIA | | |
| H3 Foto non deformata in RT | | |
| H4 Proprietà infrastruttura corretta | | |
| H5 Codici tavole PRG = PDF allegati | | |
| H6 Didascalia PRG coerente con zona | | |
| H7 Zona sismica corretta | | |
| H8 Descrizione area personalizzata | | |
| H9 Tabella parabole compilata | | |

## ESITO COMPLESSIVO
[CONFORME / NON CONFORME / CONFORME CON RILIEVI]

## RILIEVI E AZIONI CORRETTIVE
[Elenco prioritizzato di criticità da correggere — 🔴 BLOCCANTE / 🟠 IMPORTANTE / 🟡 MINORE]
```

### Step 5 — Salvataggio report

Salva il report come file `.md` nella cartella del pacchetto verificato (o nella cartella di lavoro se non specificata), con nome `VERIFICA_[CODICE SITO]_[DATA].md`.

Indica all'utente dove è stato salvato il file.

## Note operative

- Se mancano documenti, segnalalo come NC (Non Conforme) nella sezione COMPLETEZZA.
- Se un documento non è leggibile (es. PDF firmato p7m, file .doc vecchio formato), segnalalo come "non verificabile" e prosegui.
- Priorità dei rilievi: **BLOCCANTE** (impedisce la presentazione), **IMPORTANTE** (richiede correzione prima della presentazione), **MINORE** (migliorativo).
- Per i siti nel Comune di Roma, verifica la correttezza del Municipio destinatario in tutti i documenti (vedi `references/documenti-richiesti.md`).
- Consulta `references/normativa-riferimento.md` per i riferimenti normativi da verificare.
- **Confronta sempre le PEC e i dati normativi con quelli aggiornati nello Step 0** — segnalare come ⚠️ IMPORTANTE se le PEC nel pacchetto non corrispondono a quelle attuali.
