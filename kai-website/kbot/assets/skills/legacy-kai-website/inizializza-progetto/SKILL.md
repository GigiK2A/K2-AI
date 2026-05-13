---
name: inizializza-progetto
description: >
  Crea il file Excel tracker per project management cantieri TLC (Iliad, Cellnex). Genera un
  foglio di lavoro con tutte le fasi dal PE alla consegna BEF, un foglio per operatore, e
  formattazione condizionale per lo stato avanzamento. Usa per: "crea tracker cantieri",
  "nuovo progetto TLC", "inizializza Excel cantieri", "aggiungi sito al tracker",
  "nuovo sito Iliad", "nuovo sito Cellnex", "crea foglio di lavoro cantiere",
  "project management antenne", "tracker fasi lavorative", "file Excel cantieri TLC",
  "nuovo cantiere da tracciare", "aggiungi riga sito".
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
---

# Inizializza Progetto — Tracker Excel Cantieri TLC

Questa skill crea e gestisce il file Excel master di project management per i cantieri TLC di K2A Studio.

## Comportamento

Quando l'utente chiede di creare un tracker o aggiungere siti:

### 1. Se il file NON esiste ancora

Genera il file Excel `tracker_cantieri_tlc.xlsx` nella cartella di lavoro dell'utente usando lo script Python descritto sotto. Il file contiene:

- **Foglio "Dashboard"** — riepilogo con conteggi per operatore e per stato
- **Foglio "Tutti i Siti"** — tabella master con tutti i siti e tutte le fasi
- **Foglio per operatore** (es. "Iliad", "Cellnex") — vista filtrata per operatore

### 2. Se il file ESISTE già

Carica il file esistente con openpyxl e aggiungi la nuova riga sito senza perdere i dati.

## Struttura Excel

### Colonne del foglio "Tutti i Siti"

| Colonna | Contenuto |
|---------|-----------|
| A | N. progressivo |
| B | Operatore (Iliad / Cellnex / Altro) |
| C | Codice Sito (es. MI00234_001) |
| D | Indirizzo / Comune |
| E | Tipo (Raw Land / Roof Top / Transfer / Colocation) |
| F | DL (Luca / Jessica) |
| G | CSE (Luca / Jessica) |
| H | Assegnazione Figure |
| I | Verifica Progetto Esecutivo |
| J | Verifica Autorizzazioni |
| K | PSC e CME Sicurezza |
| L | Verifica POS Impresa |
| M | Cronoprogramma Lavori |
| N | Apertura Cantiere |
| O | Sopralluogo Apertura Lavori (1° obbligatorio) |
| P | Sopralluogo Verifica in Cantiere (2° obbligatorio) |
| Q | Sopralluogo Chiusura Lavori (3° obbligatorio) |
| R | Gestione Direzione Lavori |
| S | Prove Materiali e Genio Civile |
| T | Commissioning e Collaudo |
| U | Raccolta Certificazioni |
| V | Certificato Fine Lavori |
| W | Consegna BEF Portale Cliente |
| X | % Avanzamento (formula) |
| Y | Note |

### Valori ammessi per le colonne fase (H-W)

- **(vuoto)** = Non iniziata
- **data (DD/MM/YYYY)** = Completata — la data indica QUANDO è stata eseguita
- `IN CORSO` = In lavorazione
- `NC` = Non conforme / bloccata
- `N/A` = Non applicabile

### Formattazione condizionale

- **Data** → sfondo verde chiaro (C6EFCE), testo verde scuro (006100)
- `IN CORSO` → sfondo giallo (FFD966), testo nero
- `NC` → sfondo rosso (FF0000), testo bianco
- `N/A` → sfondo grigio (D9D9D9), testo grigio scuro

### Sopralluoghi CSE — Minimi Obbligatori

I sopralluoghi sono divisi in 3 colonne separate (O, P, Q), tutti obbligatori:
- **Sopralluogo Apertura Lavori** (col O) — all'avvio del cantiere
- **Sopralluogo Verifica in Cantiere** (col P) — durante l'esecuzione
- **Sopralluogo Chiusura Lavori** (col Q) — prima della chiusura

Ciascuno viene vidimato con la DATA del sopralluogo.

### Formula % Avanzamento (colonna X)

Conta le celle con data (fasi completate) su quelle applicabili (16 fasi totali meno N/A):
```
=IFERROR(SUMPRODUCT((ISNUMBER(H{r}:W{r}))*1)/(16-COUNTIF(H{r}:W{r},"N/A")),0)
```
Formattata come percentuale 0%.

### Foglio Dashboard

Contiene:
- Conteggio siti per operatore
- Conteggio siti per stato (completati, in corso, bloccati)
- Avanzamento medio per operatore
- Data ultimo aggiornamento

## Script Python da eseguire

Leggi il file `references/fasi-cantiere.md` per l'elenco completo delle fasi e i codici.

Usa **openpyxl** per creare il file con formule e formattazione. Dopo la creazione, esegui:
```bash
python /sessions/sleepy-amazing-knuth/mnt/.claude/skills/xlsx/scripts/recalc.py <percorso_file>
```

## Raccolta Dati Nuovo Sito — Flusso Domande Obbligatorio

**REGOLA FONDAMENTALE:** Quando l'utente vuole aggiungere un nuovo sito, DEVI raccogliere i dati facendo domande interattive usando il tool `AskUserQuestion` con opzioni a scelta multipla. NON procedere finché non hai tutti i dati. Fai UNA domanda alla volta, nell'ordine seguente.

### Domanda 1 — Operatore
Chiedi: "Per quale operatore è il sito?"
Opzioni: `Iliad` / `Cellnex` / `Altro (specificare)`

### Domanda 2 — Codice Sito
Chiedi: "Qual è il codice sito?" (campo libero)
Formato atteso: 2 lettere + 5 cifre + underscore + 3 cifre (es. MI00234_001, RM00126_003)
Se l'utente inserisce un formato diverso, accettalo comunque ma segnala il formato standard.

### Domanda 3 — Indirizzo
Chiedi: "Indirizzo e Comune del sito?" (campo libero)
Formato atteso: Via/Piazza + civico, Comune (Provincia) — es. "Via Roma 15, Milano (MI)"

### Domanda 4 — Tipo Sito
Chiedi: "Che tipo di sito è?"
Opzioni: `Raw Land` / `Roof Top` / `Transfer` / `Colocation`

### Domanda 5 — Figure Responsabili (DL e CSE)
Applica le regole automatiche e chiedi conferma:

**Regole automatiche:**
- Raw Land → proponi Luca (Ing.) come DL e CSE
- Roof Top → proponi Jessica (Arch.) come DL e CSE
- Transfer → proponi Luca se strutturale, Jessica se architettonico
- Colocation → proponi in base al tipo di struttura ospitante

Chiedi: "In base al tipo sito, propongo [Luca/Jessica] come DL e CSE. Confermi?"
Opzioni: `Sì, confermo` / `No, DL: Luca e CSE: Jessica` / `No, DL: Jessica e CSE: Luca` / `Entrambi su DL e CSE`

### Domanda 6 — Fasi già completate (opzionale)
Chiedi: "Il sito parte da zero o ci sono fasi già completate?"
Opzioni: `Parte da zero (F00)` / `Alcune fasi già fatte (specificare)`

Se l'utente indica fasi già completate, segna quelle fasi come "OK" direttamente nell'inserimento.

### Domanda 7 — Note iniziali (opzionale)
Chiedi: "Vuoi aggiungere note iniziali?" (campo libero, facoltativo)
Opzioni: `Nessuna nota` / `Sì (specificare)`

### Dopo aver raccolto tutti i dati
1. Mostra un riepilogo completo dei dati raccolti e chiedi conferma finale
2. Solo dopo la conferma, esegui lo script Python per inserire la riga nel tracker
3. Ricalcola le formule
4. Conferma l'inserimento mostrando la % avanzamento iniziale

### Inserimento Multiplo
Se l'utente vuole inserire più siti in serie, dopo il primo chiedi: "Vuoi aggiungere un altro sito?"
e ripeti il flusso domande.

## Posizione File

Salva sempre in: `[cartella lavoro utente]/tracker_cantieri_tlc.xlsx`

Se il file esiste già, chiedi prima se aggiungere righe o sovrascrivere.
