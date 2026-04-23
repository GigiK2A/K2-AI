---
name: aggiorna-stato
description: >
  Aggiorna lo stato delle fasi lavorative nel tracker Excel cantieri TLC. Vidima le fasi
  completate, segna NC, aggiorna note. Usa SEMPRE per: "vidima fase", "aggiorna stato sito",
  "segna OK la fase", "fase completata", "marca come completato", "aggiorna il tracker",
  "il POS è approvato", "abbiamo aperto il cantiere", "sopralluogo fatto", "CFL firmato",
  "commissioning completato", "BEF caricato", "sito completato", "segna NC",
  "aggiorna avanzamento", "stato cantiere", "check fase", "prossima fase sito".
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
---

# Aggiorna Stato — Vidimazione Fasi Cantiere TLC

Questa skill aggiorna il file `tracker_cantieri_tlc.xlsx` vidimando lo stato delle fasi lavorative per ciascun sito.

## Comportamento

### 1. Trova il file tracker

Cerca `tracker_cantieri_tlc.xlsx` nella cartella di lavoro dell'utente. Se non esiste, suggerisci di usare `inizializza-progetto` prima.

### 2. Identifica il sito — Flusso Interattivo

Se l'utente NON specifica chiaramente il sito, usa `AskUserQuestion` per chiedere:

**Domanda:** "Quale sito vuoi aggiornare?"
Leggi il tracker e mostra come opzioni i siti presenti con codice + operatore + % avanzamento:
- es. `MI00234_001 (Iliad) — 50%`
- es. `RM00126_003 (Iliad) — 14%`
- es. `TO00089_002 (Cellnex) — 93%`
- Aggiungi opzione `Altro (inserisci codice)`

Se l'utente specifica già il codice sito nel messaggio (es. "aggiorna MI00234_001"), salta questa domanda.

Carica il file con openpyxl e trova la riga corrispondente nel foglio "Tutti i Siti".

### 3. Aggiorna la fase — Flusso Interattivo

Se l'utente indica chiaramente la fase e lo stato (es. "POS approvato per MI00234_001"), procedi direttamente.

Se l'utente è generico (es. "aggiorna il sito", "prossima fase"), usa `AskUserQuestion`:

**Domanda 1 — Quale fase?**
Leggi lo stato corrente del sito dal tracker e mostra SOLO le fasi rilevanti (prossime da fare):
- es. se F00-F06 sono OK, mostra: `F07 — Sopralluoghi CSE` / `F08 — Gestione DL` / `Altra fase`

**Domanda 2 — Quale stato?**
Opzioni: `Completata (inserisce data odierna)` / `Completata in altra data (specificare)` / `IN CORSO` / `NC (non conforme)` / `N/A (non applicabile)`

**REGOLA FONDAMENTALE:** Quando una fase è completata, nel tracker si scrive la DATA (dd/mm/yyyy), MAI "OK". La data può essere quella odierna o una data specifica indicata dall'utente.

**Domanda 3 — Note? (solo se NC o se utile)**
Se lo stato è NC, chiedi: "Descrivi brevemente il motivo della NC"

L'utente può anche dire cose in linguaggio naturale e il plugin le interpreta:
- **"Segna OK la fase F04"** → imposta cella = "OK"
- **"POS approvato per MI00234_001"** → riconosci che si tratta di F04, imposta "OK"
- **"Segna NC la fase autorizzazioni"** → riconosci F02, imposta "NC"
- **"Sopralluogo fatto"** → riconosci F07, imposta "OK" (o "IN CORSO" se sono sopralluoghi periodici)
- **"Prossima fase"** → mostra la prima fase non ancora OK e chiedi conferma

### Mappatura linguaggio naturale → fase

| L'utente dice | Colonna | Fase nel tracker |
|---------------|---------|------------------|
| chi firma / figure / responsabili | H | Assegnazione Figure |
| PE / progetto esecutivo / elaborati ricevuti | I | Verifica Progetto Esecutivo |
| autorizzazioni / permessi / art.87 / SCIA / PDC | J | Verifica Autorizzazioni |
| PSC / CME / sicurezza pre-cantiere | K | PSC e CME Sicurezza |
| POS / piano operativo / impresa | L | Verifica POS Impresa |
| cronoprogramma / planning / tempistica | M | Cronoprogramma Lavori |
| apertura / consegna area / verbale consegna / notifica | N | Apertura Cantiere |
| primo sopralluogo / sopralluogo apertura | O | Sopralluogo Apertura Lavori |
| sopralluogo verifica / sopralluogo in cantiere | P | Sopralluogo Verifica in Cantiere |
| sopralluogo chiusura / ultimo sopralluogo | Q | Sopralluogo Chiusura Lavori |
| DL / ordine servizio / SAL / variante | R | Gestione Direzione Lavori |
| prove / campioni / cls / GC / Genio Civile / RSU | S | Prove Materiali e Genio Civile |
| commissioning / collaudo / misure terra | T | Commissioning e Collaudo |
| certificazioni / DiCo / DM 37 / dichiarazioni | U | Raccolta Certificazioni |
| CFL / fine lavori / ultimazione | V | Certificato Fine Lavori |
| BEF / portale / consegna cliente / chiusura | W | Consegna BEF Portale Cliente |

### 4. Salva e ricalcola

Dopo ogni modifica:
1. Salva il file con openpyxl
2. Esegui `python /sessions/sleepy-amazing-knuth/mnt/.claude/skills/xlsx/scripts/recalc.py <file>` per aggiornare le formule (% avanzamento)
3. Conferma all'utente cosa è stato aggiornato

## Aggiornamento Multiplo

L'utente può aggiornare più fasi in una volta:
- "Per MI00234_001: POS OK, cronoprogramma OK, cantiere aperto"
- → Imposta F04=OK, F05=OK, F06=OK

## Verifica Pre-Vidimazione

**REGOLA CRITICA:** Prima di segnare una fase come "OK", verifica DUE cose:

### 1. Propedeuticità (sequenza fasi)
Verifica che le fasi precedenti siano tutte OK o N/A. Se non lo sono:
- "Attenzione: la fase F02 (Autorizzazioni) non risulta ancora completata. Vuoi procedere comunque?"

### 2. Lavoro tecnico eseguito
Chiedi conferma che il lavoro della fase sia stato effettivamente svolto:
- F01 → "La verifica PE è stata eseguita con la skill dedicata? Checklist completa?"
- F02 → "Tutte le autorizzazioni sono state verificate con la skill architettura/beni monumentali?"
- F03 → "Il PSC è stato redatto/aggiornato con la skill PSC?"
- F04 → "Il POS è stato verificato con la skill CSE?"
- F06 → "Verbale, notifica e giornale lavori sono stati generati con la skill DL?"
- F09 → "RSU e deposito GC sono stati completati con la skill strutturale?"
- F10 → "Commissioning e misure verificati con la skill impianti elettrici?"
- F11 → "Tutte le DiCo D.M. 37/2008 raccolte e verificate?"
- F12 → "CFL redatto con la skill direzione lavori?"
- F13 → "BEF caricato su portale e email inviata?"

Se l'utente non ha ancora fatto il lavoro tecnico, suggerisci:
"Prima di vidimare, ti consiglio di usare la skill **esegui-fase** per eseguire il lavoro sulla fase F[XX]. Vuoi procedere con l'esecuzione?"

Questo garantisce che la vidimazione corrisponda a lavoro reale, non a un semplice check manuale.

## Aggiunta Note

L'utente può aggiungere note alla colonna W:
- "Aggiungi nota: in attesa autorizzazione paesaggistica dal 15/03"
- → Scrivi nella cella W della riga corrispondente

## Visualizzazione Stato Corrente

Se l'utente chiede "a che punto siamo con [sito]" oppure "stato [codice]":
1. Leggi la riga dal tracker
2. Mostra una tabella riepilogativa con tutte le fasi e il loro stato
3. Evidenzia la prossima fase da completare
4. Mostra la % avanzamento

## Codice Python Tipo

```python
from openpyxl import load_workbook

wb = load_workbook('tracker_cantieri_tlc.xlsx')
ws = wb['Tutti i Siti']

# Trova riga per codice sito
codice = 'MI00234_001'
target_row = None
for row in ws.iter_rows(min_row=2, max_col=3, values_only=False):
    if row[2].value == codice:
        target_row = row[0].row
        break

# Mappatura fase → colonna (H=8 ... W=23)
fase_col = {
    'Assegnazione Figure': 'H',
    'Verifica Progetto Esecutivo': 'I',
    'Verifica Autorizzazioni': 'J',
    'PSC e CME Sicurezza': 'K',
    'Verifica POS Impresa': 'L',
    'Cronoprogramma Lavori': 'M',
    'Apertura Cantiere': 'N',
    'Sopralluogo Apertura Lavori': 'O',
    'Sopralluogo Verifica in Cantiere': 'P',
    'Sopralluogo Chiusura Lavori': 'Q',
    'Gestione Direzione Lavori': 'R',
    'Prove Materiali e Genio Civile': 'S',
    'Commissioning e Collaudo': 'T',
    'Raccolta Certificazioni': 'U',
    'Certificato Fine Lavori': 'V',
    'Consegna BEF Portale Cliente': 'W',
}

# IMPORTANTE: le fasi completate si vidimano con la DATA, non con "OK"
import datetime
ws[f'{fase_col["Verifica POS Impresa"]}{target_row}'] = datetime.date.today()
ws[f'{fase_col["Verifica POS Impresa"]}{target_row}'].number_format = 'DD/MM/YYYY'
wb.save('tracker_cantieri_tlc.xlsx')
```
