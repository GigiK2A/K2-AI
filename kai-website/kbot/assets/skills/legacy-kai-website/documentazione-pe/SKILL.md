---
name: documentazione-pe
description: >
  Skill per la redazione della documentazione testuale del PE iliad: frontespizio, relazione
  tecnica descrittiva, documentazione fotografica ante-operam, schede radio di progetto.
  Usa SEMPRE questa skill quando l'utente dice "frontespizio PE iliad", "relazione tecnica
  descrittiva iliad", "relazione tecnica sito radio", "documentazione fotografica sito iliad",
  "schede radio di progetto", "scheda radio PE", "compilare scheda radio progetto",
  "redigere relazione tecnica PE", "intestazione PE iliad", "copertina PE iliad",
  "checklist elaborati frontespizio", "anagrafica sito PE", "dati sito PE iliad".
metadata:
  version: "0.1.0"
  author: "Luca Rossi"
  riferimento: "Linea Guida PE iliad v.1.1 — FRONTESPIZIO.docx"
---

# Documentazione PE iliad — Frontespizio, Relazione Tecnica, Foto, Schede Radio

Questa skill guida la redazione degli elaborati documentali del PE iliad.

---

## 1. Frontespizio del PE

### Intestazione Obbligatoria

Il frontespizio deve riportare il seguente titolo standard:

> **Progetto per la realizzazione di un impianto tecnologico di radiotelecomunicazioni per telefonia cellulare**
> **Sistema UMTS900/LTE1800/UMTS2100/LTE2600/LTE2100**
> **"PROGETTO ESECUTIVO"**

### Checklist Elaborati in Frontespizio

Il frontespizio include una checklist con caselle da barrare, indicando gli elaborati inclusi nel PE:

```
☐ Progetto architettonico presentato al comune
☐ Relazione tecnica descrittiva
☐ Documentazione fotografica ante-operam
☐ Schede radio di progetto
☐ Relazione Palo / Verifica statica Palo
☐ Relazione di calcolo sulle fondazioni / Verifica statica
☐ Relazione Geotecnica
☐ Relazione Geologica
☐ Elaborati grafici esecutivi
☐ Relazioni e Tavole Impianti
☐ Verifica scariche atmosferiche
```

### Dati Identificativi Sito

```
Codice Sito:    _______________
Nome Sito:      _______________
Tipologia Sito: _______________  (NS-RL / NS-RT / TC-RL / TC-RT)
Indirizzo:      _______________
Comune:         _______________
Provincia:      _______________
Data documento: _______________
Versione doc.:  _______________
```

### Blocco Firme

```
Il richiedente          Il Fornitore            Il Progettista
[Logo iliad]            _______________         _______________
iliad Italia S.p.A.     _______________         _______________
```

### Redazione del Frontespizio

Per generare il frontespizio come documento Word (.docx):
1. Attivare la skill **docx**
2. Utilizzare il template FRONTESPIZIO.docx come riferimento
3. Compilare tutti i campi con i dati del sito specifico
4. Barrare le caselle degli elaborati inclusi nel PE

---

## 2. Relazione Tecnica Descrittiva

### Struttura Standard

**Sezione 1 — Premessa e Oggetto**

Descrivere:
- Il soggetto richiedente (iliad Italia S.p.A.)
- L'oggetto dell'intervento (installazione impianto radioelettrico per telefonia mobile)
- Il sistema di tecnologie previste (UMTS900/LTE1800/UMTS2100/LTE2600/LTE2100)
- Il riferimento normativo principale (D.Lgs. 259/2003, art. 86-87)

**Sezione 2 — Descrizione del Sito**

- Codice sito e nome sito
- Indirizzo, Comune, Provincia, CAP
- Coordinate GPS (latitudine e longitudine WGS84 in gradi decimali)
- Quota altimetrica sul livello del mare [m s.l.m.]
- Accessibilità (strade adiacenti, accesso carrabile, ecc.)
- Proprietà dell'area/edificio (pubblica, privata, contratto d'uso)
- Destinazione urbanistica dell'area (da PRG/PUC)
- Eventuale presenza di vincoli

**Sezione 3 — Descrizione dell'Intervento**

Per **NS-RL**:
- Tipologia e altezza della struttura porta antenne da installare (palo poligonale H = [m])
- Dimensioni e caratteristiche della platea di fondazione
- Dimensioni dell'area recintata (L × B m²)
- Tipo e altezza della recinzione
- Tipologia del cancello di accesso
- Posizione e tipo del quadro elettrico
- Tipologia di armadio stradale/contatore

Per **NS-RT**:
- Descrizione dell'edificio esistente (uso, altezza, tipologia strutturale)
- Tipo di struttura porta antenne su roof (palina, sbraccio, ecc.)
- Numero e tipo di baggioli
- Percorso cavi in copertura

Per **TC-RL / TC-RT**:
- Descrizione del sito esistente e degli operatori già presenti
- Descrizione degli apparati da aggiungere
- Eventuali modifiche alla struttura portante esistente

**Sezione 4 — Apparati Radio**

Tabella apparati:

| Apparato | Marca | Modello | Banda [MHz] | Settore | H installazione [m] | N° |
|----------|-------|---------|-------------|---------|---------------------|----|
| Antenna | | | UMTS900 | A | | |
| Antenna | | | LTE1800 | A | | |
| Antenna | | | UMTS2100 | A | | |
| ... | | | | | | |
| RRU | | | | | | |
| BTS/BBU | | | — | — | — | |

**Sezione 5 — Impianto Elettrico**

- Tipo di fornitura elettrica (monofase 230V / trifase 400V)
- Potenza contrattuale richiesta
- Gestore di rete e modalità di allacciamento
- Tipo di quadro principale (ICA / MiniTD / QPL)
- Impianto di terra: tipo dispersori, resistenza target

**Sezione 6 — Conformità Normativa**

- Conformità alle emissioni elettromagnetiche (DPCM 8/7/2003 e s.m.i.)
- Limiti di esposizione ai CEM rispettati (valutazione ICNIRP)
- Conformità urbanistica e autorizzativa
- Rispetto del Codice delle Comunicazioni Elettroniche (D.Lgs. 259/2003)

---

## 3. Documentazione Fotografica Ante-Operam

### Linee Guida per la Documentazione Fotografica

La documentazione fotografica ante-operam deve testimoniare lo stato dei luoghi PRIMA dell'installazione dell'impianto iliad.

**Fotografie obbligatorie:**

| N° | Soggetto | Note |
|----|---------|------|
| 1 | Vista generale dell'area da Est o Nord-Est | Contesto territoriale |
| 2 | Vista generale dell'area da Ovest o Sud-Ovest | Contesto territoriale |
| 3 | Dettaglio dell'area dove sarà installato il palo | Con metro o riferimento di scala |
| 4 | Posizione prevista del cilindretto/armadio stradale | Con strada/marciapiede |
| 5 | Accesso al sito (ingresso/cancello/percorso) | |
| 6 | Vista verso i punti cardinali principali (N, S, E, O) | Per analisi paesaggistica |
| 7-n | Eventuali elementi particolari del sito | Anomalie, preesistenze, ecc. |

**Formato scheda fotografica:**

Per ogni fotografia riportare:
```
Foto n°: [numero]
Data scatto: [gg/mm/aaaa]
Ora: [hh:mm]
Posizione fotografo: [coordinate GPS o descrizione]
Direzione di ripresa: [N/S/E/O/NE/...]
Descrizione: [soggetto e contenuto]
```

**Per NS-RT aggiungere:**
- Fotografie della copertura esistente con tutti gli impianti già presenti
- Fotografie dei punti di accesso al tetto
- Fotografie degli elementi strutturali della copertura (solaio, travi, parapetti)

---

## 4. Schede Radio di Progetto

Le Schede Radio di Progetto sono diverse dalle Schede Radio di sopralluogo (TSSR/B40):

- Le **Schede Radio di sopralluogo** (TSSR/B40) documentano la situazione rilevata durante il sopralluogo (usare la skill **tssr-b40-filler:scheda-radio-reader**)
- Le **Schede Radio di Progetto** riportano i dati DEFINITIVI di progetto, verificati e approvati

### Dati da riportare nelle Schede Radio di Progetto

| Campo | Fonte dati |
|-------|-----------|
| Codice sito | Scheda Radio + confermato da iliad |
| Nome sito | Scheda Radio + confermato da iliad |
| Coordinate GPS | Misurate in sito (sopralluogo) |
| Indirizzo | Verificato da sopralluogo |
| Struttura portante | Definita da progetto strutturale |
| Altezza struttura | Da progetto (per NS) o da rilievo (per TC) |
| Apparati radio | Da Site Scenario / Order Form definitivo |
| Altezza base antenne | Da progetto definitivo |
| Altezza centro elettrico | Da progetto definitivo |
| Settori e azimut | Da Site Scenario |
| Tecnologie | UMTS900/LTE1800/UMTS2100/LTE2600/LTE2100 |

### Differenze Rispetto al TSSR/B40

| Voce | TSSR/B40 (sopralluogo) | Scheda Radio PE (progetto) |
|------|------------------------|---------------------------|
| Stato | Rilevato in sito | Definitivo di progetto |
| Apparati | Esistenti o da sopralluogo | Definitivi da Order Form |
| Altezze | Misurate | Da progetto strutturale |
| Firma | Tecnico sopralluogo | Progettista |

---

## Note sulla Versioning degli Elaborati

Tutti gli elaborati del PE devono seguire la numerazione delle revisioni:

| Revisione | Codice | Significato |
|-----------|--------|-------------|
| Prima emissione | 00 | Prima versione del PE |
| Prima revisione | 01 | Correzioni richieste da iliad |
| Seconda revisione | 02 | Ulteriori correzioni |

Il frontespizio e tutti gli elaborati devono riportare la stessa data e revisione del PE.

## Attivare Skill Complementari

- **docx** — per generare la relazione tecnica come file Word (.docx)
- **pdf** — per assemblare/unire gli elaborati in un unico PDF
- **tssr-b40-filler:scheda-radio-reader** — per leggere e interpretare le Schede Radio di sopralluogo
- **tssr-b40-filler:compila-tssr** — per compilare il B40 dal PDF della Scheda Radio
