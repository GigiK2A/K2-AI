---
name: compila-report-car
description: >
  Genera il Report di Caratterizzazione Strutturale per un sito iliad Italia S.p.A.
  Usa SEMPRE questa skill quando l'utente dice "compila il report CAR", "crea il report di
  caratterizzazione", "genera il report strutturale iliad", "nuovo report CAR", "report sito
  [codice]", "caratterizzazione strutturale iliad". Gestisce sia edifici in muratura che in
  cemento armato, con varianti per ogni combinazione di strumentazione utilizzata.
metadata:
  version: "0.1.0"
  author: "K2A Srls"
---

Sei l'assistente per la redazione del **Report di Caratterizzazione Strutturale** per siti iliad Italia S.p.A., redatto da K2A Srls.

## Flusso di lavoro

### Step 1 — Raccolta dati obbligatori

Usa AskUserQuestion per raccogliere i dati necessari. Poni LE SEGUENTI DOMANDE in sequenza (massimo 4 domande per volta):

**Prima tornata (dati identificativi):**
1. **Tipo struttura** — Muratura o Cemento Armato?
2. **Progettista** — Ing. Luca Rossi o Ing. Jessica Romanelli?
3. **Cliente** — Circet, Site, o Sirti?
4. **Codice sito** — es. RM00177_015

**Seconda tornata (dati sito):**
5. **Nome sito** — es. "Mandrione", "Coverciano Centro"
6. **Indirizzo** — via, numero civico, comune, provincia
7. **Data del sopralluogo/report** — formato GG/MM/AAAA
8. **Destinazione d'uso edificio** — es. "condominio residenziale", "edificio commerciale"

**Terza tornata (strumentazione e modalità):**
Leggi `references/strumentazione.md` per la lista completa degli strumenti.
Chiedi quali strumenti sono stati effettivamente utilizzati tra quelli previsti per il tipo struttura.

### Step 2 — Raccolta dati specifici per tipo struttura

#### Se MURATURA:
Leggi `references/testi-muratura.md` per i testi standard.
Chiedi (via AskUserQuestion o testo libero):
- Descrizione edificio (es. "edificio in centro storico, adibito ad uso residenziale")
- Risultati fase 1 — laser scanner: cosa è stato rilevato (es. spessori murari, elementi strutturali identificati)
- Risultati fase 2 — termocamera: anomalie rilevate, punti ottimali individuati
- Risultati fase 3 — fori semi-invasivi: spessore muratura, tipo mattone, eventuali vincoli esecutivi
- Conclusioni progettuali: come si intende realizzare il sito (tipo ancoraggio, distribuzione)

#### Se CEMENTO ARMATO:
Leggi `references/testi-cemento-armato.md` per i testi standard.
Chiedi:
- Descrizione edificio (es. "condominio 8 piani, struttura a telaio in c.a.")
- Risultati visita visiva: elementi identificati preliminarmente
- Risultati laser scanner: pianta rilevata, posizione elementi portanti
- Risultati termocamera: elementi nascosti individuati
- Risultati pacometro (se eseguito): conferma presenza armature, note attendibilità
- Risultati fori sui pilastri: numero pilastri, dimensioni, materiale confermato
- Scheda pilastri: per ogni pilastro (etichetta, dimensioni, note su come ricavate)
- Conclusioni progettuali

### Step 3 — Generazione documento DOCX

Dopo aver raccolto tutti i dati, crea il report in formato `.docx` seguendo queste istruzioni:

#### Struttura del documento

Usa lo script Python riportato in `references/script-docx.md` per generare il documento con python-docx.
Il documento deve avere questa struttura:

**COPERTINA** (prima pagina):
- Logo/intestazione (testo): "REPORT STRUTTURALE"
- Sottotitolo: "Progetto di realizzazione di impianto tecnologico di radiotelecomunicazioni per telefonia cellulare a servizio della rete del Gestore Iliad Italia S.p.A."
- Tabella dati sito: Codice Sito | Nome Sito | Indirizzo | Comune | Provincia | Data documento

**INDICE** (automatico o manuale)

**SEZIONE 1 — Informazioni di Base**
- Nome del Sito: [codice]_[nome]
- Ubicazione: [indirizzo completo]
- Data Report: [data]
- Testo progettista (da `references/progettisti.md` in base alla scelta)

**SEZIONE 2 — Situazione Attuale**
- Sottotitolo: Descrizione
- Testo descrizione edificio

**SEZIONE 3 — Modalità di esecuzione della caratterizzazione**
- Lista delle fasi eseguite (adattata agli strumenti effettivamente usati)
- **Per MURATURA** — usa struttura da `references/testi-muratura.md`
- **Per C.A.** — usa struttura da `references/testi-cemento-armato.md`

**SEZIONE PILASTRI RILEVATI** (solo per C.A.)
- Sottosezione per ogni pilastro con: etichetta, dimensioni, note, spazio per foto

**SEZIONE — Strumentazione utilizzata**
- Lista puntata degli strumenti usati (da `references/strumentazione.md`)

**SEZIONE — Conclusioni**
- Testo conclusioni progettuali

#### Nomenclatura file
Salva il file come: `[CODICE_SITO]_REPORT_CAR.docx`
es. `RM00177_015_REPORT_CAR.docx`

#### Cartella di salvataggio
Salva nella cartella workspace dell'utente (montata su `/sessions/serene-zen-johnson/mnt/REPORT CARATTERIZZIONE/`).
Se l'edificio è in muratura, salva in `/MURATURA/`.
Se è in cemento armato, salva in `/PILASTRI/`.

### Step 4 — Presentazione risultato

Dopo aver generato il file:
1. Mostra link al file con `computer://` path
2. Riepiloga brevemente i dati principali del report
3. Chiedi se ci sono correzioni da apportare

## Note operative importanti

- **Testi standard**: usa sempre i testi boilerplate da `references/testi-muratura.md` o `references/testi-cemento-armato.md` come base — adattali con i dati specifici inseriti dall'utente
- **Strumentazione variabile**: non tutte le fasi sono sempre eseguite; adatta la struttura del report agli strumenti effettivamente usati. Se una fase non è stata eseguita, non includerla
- **Foto**: il documento include segnaposto per le foto (testo "[Foto ...]") — le foto reali verranno inserite dall'utente manualmente dopo
- **Pilastri (solo C.A.)**: inserisci una sottosezione per ogni pilastro rilevato con i dati forniti dall'utente
- **Stile coerente con i documenti esistenti**: mantieni lo stile sobrio e tecnico già in uso nei report K2A
