---
name: report-avanzamento
description: >
  Genera report avanzamento cantieri TLC dal tracker Excel. Report per operatore, per fase,
  per stato. Identifica siti bloccati (NC) e prossime azioni. Usa SEMPRE per: "report cantieri",
  "stato avanzamento", "quanti siti completati", "siti bloccati", "riepilogo Iliad",
  "riepilogo Cellnex", "dashboard cantieri", "avanzamento per operatore", "siti in ritardo",
  "prossime azioni cantieri", "report settimanale", "overview cantieri",
  "quanti cantieri aperti", "stato generale TLC".
tools:
  - Read
  - Write
  - Bash
  - Glob
---

# Report Avanzamento — Dashboard Cantieri TLC

Questa skill legge il file `tracker_cantieri_tlc.xlsx` e produce report di avanzamento in diversi formati.

## Comportamento

### 1. Carica il tracker

Trova e leggi `tracker_cantieri_tlc.xlsx` con pandas. Se non esiste, suggerisci `inizializza-progetto`.

### 2. Tipo di report

In base alla richiesta dell'utente, genera uno dei seguenti:

---

### Report Generale

Mostra:
- Totale siti nel tracker
- Siti completati (tutte le fasi OK o N/A)
- Siti in corso (almeno una fase IN CORSO)
- Siti bloccati (almeno una fase NC)
- % avanzamento medio globale
- % avanzamento medio per operatore

### Report per Operatore

Filtra per Iliad / Cellnex / altro e mostra:
- Lista siti dell'operatore con % avanzamento
- Fase corrente (ultima fase OK + 1) per ogni sito
- Siti con NC da risolvere
- Ordinamento per % avanzamento (dal più indietro)

### Report Siti Bloccati

Lista di tutti i siti con almeno una fase in stato NC:
- Codice sito + operatore
- Fase bloccata
- Note associate
- Suggerimento azione da intraprendere

### Report per Fase

Analisi trasversale: per una specifica fase, mostra quanti siti sono:
- OK (completata)
- IN CORSO
- NC (bloccata)
- Non ancora iniziata
- N/A

Utile per capire i colli di bottiglia (es. "quanti siti sono bloccati sulle autorizzazioni?")

### Report Settimanale

Riepilogo per invio al PM o al cliente:
- Siti che hanno avanzato nell'ultima settimana (confronto con note/date)
- Siti fermi
- Prossime milestone previste
- Azioni pendenti

---

## Formato Output

I report possono essere prodotti come:

1. **Testo in conversazione** — per consultazione rapida
2. **File Excel separato** — `report_avanzamento_[data].xlsx` con grafici
3. **File HTML** — dashboard visuale con tabelle colorate

Default: testo in conversazione. Se l'utente chiede "esporta" o "file" → genera Excel o HTML.

## Script Python Tipo per Report Generale

```python
import pandas as pd
from openpyxl import load_workbook

wb = load_workbook('tracker_cantieri_tlc.xlsx', data_only=True)
ws = wb['Tutti i Siti']

data = []
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0] is None:
        break
    data.append(row)

headers = [cell.value for cell in ws[1]]
df = pd.DataFrame(data, columns=headers)

# Fasi columns
fasi_cols = [c for c in df.columns if c and c.startswith('F')]

totale = len(df)
completati = len(df[df[fasi_cols].apply(
    lambda r: all(v in ('OK', 'N/A') for v in r if v), axis=1
)])
bloccati = len(df[df[fasi_cols].apply(
    lambda r: any(v == 'NC' for v in r if v), axis=1
)])
in_corso = totale - completati - bloccati

print(f"Totale siti: {totale}")
print(f"Completati: {completati}")
print(f"In corso: {in_corso}")
print(f"Bloccati: {bloccati}")
```

## Integrazione con Altre Skill

Quando il report evidenzia criticità, suggerisci le skill appropriate:
- NC su F02 (Autorizzazioni) → "Verifica con skill `architetto-beni-monumentali` se serve autorizzazione paesaggistica"
- NC su F03 (PSC) → "Aggiorna il PSC con skill `psc-coordinamento-sicurezza`"
- NC su F09 (Prove GC) → "Controlla deposito strutturale con skill `progettista-strutturale`"
- NC su F11 (Certificazioni) → "Verifica conformità con skill `impianti-elettrici` o `agibilita`"
