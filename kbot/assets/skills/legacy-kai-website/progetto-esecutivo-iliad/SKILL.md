---
name: progetto-esecutivo-iliad
description: >
  Skill principale per la redazione del Progetto Esecutivo (PE) iliad Italia S.p.A.
  Usa SEMPRE questa skill quando l'utente dice "fare il PE", "redigere il progetto esecutivo",
  "progetto esecutivo iliad", "PE new site", "PE rawland", "PE rooftop", "PE transfer",
  "PE colocation", "cosa serve per il PE", "elenco elaborati PE", "frontespizio PE",
  "lista documenti iliad", "checklist progetto esecutivo". Attivala anche per qualsiasi
  richiesta di supporto alla redazione di un PE per siti iliad di qualsiasi tipologia.
metadata:
  version: "0.1.0"
  author: "Luca Rossi"
  riferimento: "Linea Guida Progetti Esecutivi iliad v.1.1"
---

# Progetto Esecutivo iliad — Skill Principale

Questa skill guida la redazione completa del Progetto Esecutivo (PE) per siti iliad Italia S.p.A. secondo la "Linea Guida Progetti Esecutivi v.1.1".

## Identificazione Tipologia Sito

Prima di procedere, identificare la tipologia del sito tra:

- **New Site RawLand (NS-RL)** — nuovo sito a terra
- **New Site RoofTop (NS-RT)** — nuovo sito su edificio esistente
- **Transfer/Colocation RawLand (TC-RL)** — colocazione su sito esistente a terra
- **Transfer/Colocation RoofTop (TC-RT)** — colocazione su edificio esistente

Se non specificato, chiedere: codice sito, nome sito, comune, provincia, tipologia.

## Matrice Elaborati Obbligatori

Consultare `references/matrice-elaborati.md` per l'elenco completo per ciascuna tipologia.

**Schema rapido:**

| Elaborato | NS-RL | NS-RT | TC-RL | TC-RT |
|-----------|:-----:|:-----:|:-----:|:-----:|
| Progetto Architettonico | ✓ | ✓ | ✓ | ✓ |
| Relazione tecnica descrittiva | ✓ | ✓ | ✓ | ✓ |
| Documentazione fotografica ante-operam | ✓ | ✓ | ✓ | ✓ |
| Schede Radio di progetto | ✓ | ✓ | ✓ | ✓ |
| Relazione di calcolo del Palo (nuova) | ✓ | ✓ | — | — |
| Verifica/Asseverazione palo esistente | — | — | ✓ | ✓ |
| Relazione di calcolo fondazione (nuova) | ✓ | — | — | — |
| Verifica statica fondazione esistente | — | — | ✓ | — |
| Relazione Geotecnica | ✓ | — | ✓ | — |
| Relazione Geologica | ✓ | — | se nec. | — |
| Elaborati Grafici Costruttivi | ✓ | ✓ | ✓ | ✓ |
| Relazione calcolo impianto elettrico | ✓ | ✓ | ✓ | ✓ |
| Elaborati Grafici Impianti | ✓ | ✓ | ✓ | ✓ |
| Verifica scariche atmosferiche | ✓ | ✓ | se nec. | se nec. |

## Workflow di Redazione PE

### Step 1 — Raccolta dati sito

Acquisire dalla Scheda Radio / Site Scenario:
- Codice sito (formato: XX00000_000)
- Nome sito
- Indirizzo completo
- Comune e Provincia
- Coordinate GPS (WGS84)
- Tipologia sito
- Tecnologie radio (UMTS900/LTE1800/UMTS2100/LTE2600/LTE2100)
- Struttura portante (tipo palo, altezza)
- Apparati previsti

### Step 2 — Frontespizio e indice elaborati

Redigere il frontespizio con:
- Dati identificativi sito (Codice, Nome, Tipologia, Indirizzo, Comune, Provincia)
- Data documento e versione
- Checklist elaborati previsti per la tipologia

Attivare la skill **documentazione-pe** per la redazione del frontespizio.

### Step 3 — Progetto Architettonico

Attivare la skill **elaborati-architettonici** per:
- Cartografia con inquadramento territoriale
- Stato di fatto (pianta e prospetto)
- Stato di progetto (pianta e prospetto)
- Comparazione (pianta e prospetto)

### Step 4 — Relazione Tecnica Descrittiva

Attivare la skill **documentazione-pe** per la relazione tecnica.

### Step 5 — Schede Radio

Attivare la skill **documentazione-pe** per la compilazione delle Schede Radio di progetto (con dati definitivi di progetto, non da sopralluogo).

### Step 6 — Relazioni Strutturali

Attivare la skill **relazioni-strutturali** per:
- Relazione di calcolo del palo (NS-RL, NS-RT)
- Verifica/asseverazione palo esistente (TC-RL, TC-RT)
- Relazione di calcolo fondazione (NS-RL)
- Verifica statica fondazione (TC-RL)
- Relazione Geotecnica (NS-RL, TC-RL)
- Relazione Geologica (NS-RL, TC-RL se necessario)

### Step 7 — Elaborati Grafici Costruttivi

Attivare la skill **elaborati-civili** per tutte le tavole costruttive differenziate per tipologia sito.

### Step 8 — Relazione e Grafici Impianti

Attivare la skill **elaborati-impianti** per:
- Relazione di calcolo impianto elettrico
- Elaborati grafici impianti
- Verifica scariche atmosferiche (LPS)

### Step 9 — PSC

Per i cantieri che lo richiedono (NS-RL, NS-RT), attivare la skill **psc-coordinamento-sicurezza**.

### Step 10 — Verifica finale e consegna

Eseguire il controllo finale con la skill **verifica-pe-terzi** applicata al proprio elaborato (autocontrollo).

## Dati da Riportare nel Frontespizio

```
Codice Sito:    [XX00000_000]
Nome Sito:      [Nome]
Tipologia Sito: [NS-RL / NS-RT / TC-RL / TC-RT]
Indirizzo:      [Via, n. civico]
Comune:         [Comune]
Provincia:      [Sigla]
Data documento: [gg/mm/aaaa]
Versione doc.:  [1.0]
```

## Note Operative

- Il richiedente è sempre **iliad Italia S.p.A.**
- Il sistema radio è: **UMTS900/LTE1800/UMTS2100/LTE2600/LTE2100**
- Per i calcoli strutturali mantenere una marginalità del **15-20%** sugli sfruttamenti
- L'incidenza di bulloni e zincatura sulla carpenteria non deve superare il **10%**
- Tutti gli elaborati devono riportare in cartiglio: Codice Sito, Nome Sito, Fornitore, Progettista
