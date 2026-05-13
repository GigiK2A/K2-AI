---
name: scheda-radio-reader
description: >
  This skill should be used when the user mentions "Scheda Radio", "TSSR", "B40",
  "iliad", "TDC", "sito radio", "antenna", "sopralluogo radio", or asks to
  "compilare il TSSR", "estrarre dati dal PDF", "leggere la scheda radio",
  "compilare il B40". Also triggers on mentions of codice sito (pattern like
  RM00126_003), Scheda Tecnica Sito Radio, or any telecom site documentation workflow.
version: 0.1.0
---

# Scheda Radio Reader — iliad / TDC

Questo skill fornisce le istruzioni per estrarre dati da Schede Radio PDF in formato iliad/TDC e compilare il file Excel TSSR_B40.

## Struttura del documento Scheda Radio

Le Schede Radio iliad/TDC sono documenti tecnici PDF che documentano un sito di trasmissione radio. Il documento segue tipicamente questa struttura:

1. **Intestazione** — Logo iliad/TDC, titolo "Scheda Radio" o "Scheda Tecnica Sito Radio", data
2. **Anagrafica sito** — Codice sito, nome, indirizzo, comune, provincia, coordinate GPS
3. **Dati tecnici impianto** — Altezze, struttura portante, tipo palo
4. **Apparati radio** — Produttore, modello antenna, settori, frequenze
5. **Note e firme** — Data sopralluogo, tecnico, validazione

## Regole di estrazione campi

Consulta `references/field-mappings.md` per i pattern regex completi e gli esempi di varianti di layout.

### Codice Sito

Formato canonico: `[A-Z]{2}\d{5}_\d{3}` (es. `RM00126_003`, `MI00342_001`, `TO00789_002`)

- Cercare prima in testata documento, poi in box "Codice Sito" o "Site ID"
- Può apparire anche come `RM 00126_003` (con spazio) — rimuovere lo spazio
- Alternativa senza underscore: `RM00126003` → normalizzare a `RM00126_003`

### Nome Sito

- Solitamente su riga separata dopo il codice sito, o in campo "Nome Sito" / "Site Name"
- Formato tipico: `Città-Quartiere` o `Comune-Localita` (es. `Acilia-Monti San Paolo`)
- Può contenere trattini, spazi, caratteri accentati

### Coordinate GPS (WGS84)

- Latitudine: compresa tra 35.0 e 47.5 per l'Italia
- Longitudine: compresa tra 6.5 e 18.5 per l'Italia
- Formati accettati: decimale (`41.823456`), gradi-minuti-secondi (`41°49'24.44"N`)
- Etichette: "Lat", "Latitudine", "N:", "LAT", "φ"
- Se in DMS, convertire in decimale: `gradi + minuti/60 + secondi/3600`

### Comune e Provincia

- Comune: nome intero senza abbreviazioni (es. `Roma`, `Milano`, `Fiumicino`)
- Provincia: sigla 2 lettere maiuscole (es. `RM`, `MI`, `TO`)
- Spesso compaiono insieme: `Roma (RM)` o `Roma - RM` o in righe separate

### Data Sopralluogo

- Formati accettati: `gg/mm/aaaa`, `gg-mm-aaaa`, `gg.mm.aaaa`
- Etichette: "Data", "Data sopralluogo", "Data visita", "Del"
- Normalizzare sempre a formato `gg/mm/aaaa`

### Indirizzo

- Riga completa con via/piazza/strada, numero civico, eventuale CAP
- Etichette: "Indirizzo", "Via", "Indirizzo sito", "Ubicazione"
- Includere tutto tranne comune e provincia (già in celle separate)

### Produttore Antenna

- Valori tipici: `Huawei`, `Nokia`, `Ericsson`, `Kathrein`, `CommScope`, `RFS`, `Andrew`
- Etichette: "Produttore", "Fornitore", "Manufacturer", "Brand"
- Estrarre solo il nome del produttore, non il modello

### Modello Antenna

- Codice alfanumerico (es. `APXVAAA4X4D65R`, `742265`, `BSTA4518BM`)
- Etichette: "Modello", "Tipo antenna", "Model", "Part number"

### Base Antenna (m)

- Altezza base dell'antenna dal suolo, in metri
- Etichette: "Base Antenna", "Base ant.", "H base", "Altezza base", "Quota base"
- Estrarre solo il numero (es. `24.5`, `30`)

### Altezza Centro Elettrico (m)

- Altezza del centro elettrico / centro radiante dal suolo, in metri
- Etichette: "Centro Elettrico", "H el.", "ACE", "Altezza CE", "Centro Radiante", "H centro"
- Estrarre solo il numero (es. `27.5`, `33.2`)

## Mappatura celle Excel — Foglio1

| Cella | Campo sorgente | Formato atteso |
|-------|---------------|----------------|
| F6 | Nome sito | Testo libero (es. "Acilia-Monti San Paolo") |
| F7 | Codice sito | Codice normalizzato (es. "RM00126_003") |
| E5 | Comune + Provincia | "Comune (SiglaProv)" (es. "Roma (RM)") |
| E8 | Data sopralluogo | "gg/mm/aaaa" |
| F16 | Comune | Solo nome comune |
| F17 | Indirizzo completo | Via, numero, eventuale CAP |
| N16 | Sigla provincia | 2 lettere maiuscole (es. "RM") |
| C34 | Nota tecnica | Stringa formattata (vedi sotto) |

### Formato nota tecnica C34

```
Lat: XX.XXXXXX - Lon: XX.XXXXXX | Produttore: XXXX | Modello: XXXX | Base ant.: XX m | H el.: XX m
```

Esempio reale:
```
Lat: 41.823456 - Lon: 12.345678 | Produttore: Huawei | Modello: APXVAAA4X4D65R | Base ant.: 24.5 m | H el.: 27.5 m
```

## Gestione celle mergiate in Excel

Il file TSSR_B40 contiene spesso celle mergiate. Se `ws["F6"] = valore` non funziona:

```python
# Approccio alternativo per celle mergiate
from openpyxl.utils import get_column_letter

def set_merged_cell(ws, cell_ref, value):
    """Scrive in una cella anche se è mergiate."""
    cell = ws[cell_ref]
    # Trovare la cella master del merge range
    for merge_range in ws.merged_cells.ranges:
        if cell.coordinate in merge_range:
            # Scrivi nella cella in alto a sinistra del range
            ws.cell(row=merge_range.min_row,
                   column=merge_range.min_col).value = value
            return
    # Cella non mergiate: scrittura diretta
    ws[cell_ref] = value
```

## Dipendenze Python richieste

```bash
pip install pdfplumber openpyxl --break-system-packages -q
```

Alternativa per PDF problematici:
```bash
pip install pypdf --break-system-packages -q
```
