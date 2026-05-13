---
name: elaborati-architettonici
description: >
  Skill per la redazione degli elaborati architettonici del Progetto Esecutivo iliad.
  Usa SEMPRE questa skill quando l'utente dice "progetto architettonico iliad",
  "tavole architettoniche PE", "stato di fatto", "stato di progetto", "comparazione",
  "planimetria sito iliad", "prospetti architettonici", "cartografia sito",
  "inquadramento urbanistico", "elaborati grafici architettonici antenna iliad",
  "DWG architettonico", "disegni architettonici PE", "pianta e prospetto sito TLC".
metadata:
  version: "0.1.0"
  author: "Luca Rossi"
  riferimento: "Linea Guida Progetti Esecutivi iliad v.1.1 — Progetto Architettonico"
---

# Elaborati Architettonici — PE iliad

Questa skill guida la redazione del Progetto Architettonico del PE iliad, obbligatorio per tutte le tipologie di sito (NS-RL, NS-RT, TC-RL, TC-RT).

## Composizione del Progetto Architettonico

Il Progetto Architettonico per iliad comprende le seguenti tavole/sezioni:

1. **Cartografia** (inquadramento territoriale)
2. **Inquadramento stato di fatto** (estratto catastale e urbanistico)
3. **Stato di Fatto** (pianta e prospetto)
4. **Stato di Progetto** (pianta e prospetto)
5. **Comparazione** (pianta e prospetto)

---

## Tavola 1 — Cartografia e Inquadramento

Predisporre:
- Estratto di mappa catastale con individuazione del lotto/edificio
- Estratto di cartografia CTR o IGM in scala adeguata (1:10.000 o 1:25.000)
- Estratto PRG/PUC con destinazione urbanistica dell'area
- Cerchiare/evidenziare la posizione del sito

Dati da riportare in cartiglio:
- Comune, Foglio, Mappale/i
- Destinazione urbanistica
- Eventuale presenza vincoli (paesaggistico, idrogeologico, ecc.)

---

## Tavola 2 — Stato di Fatto (pianta + prospetto)

### Pianta Stato di Fatto

Riportare fedelmente la situazione preesistente:

**Per NS-RL (terreno libero):**
- Perimetro dell'area disponibile con dimensioni
- Accessi esistenti
- Eventuali manufatti presenti
- Vegetazione significativa
- Recinzioni o muretti esistenti
- Quota altimetrica del terreno
- Punti cardinali e nord geografico

**Per NS-RT (edificio esistente):**
- Pianta della copertura con tutti gli elementi esistenti
- Antenne/impianti di altri operatori già presenti
- Vani scala, locali tecnici, parapetti
- Servizi esistenti (quadri elettrici, ecc.)
- Accessi al tetto

**Per TC-RL / TC-RT:**
- Come sopra con tutti gli apparati degli operatori già presenti
- Posizione e tipo delle strutture esistenti (palo, traliccio, ecc.)

### Prospetti Stato di Fatto

- Prospetto principale del sito (fronte strada o lato più rappresentativo)
- Eventuale prospetto secondario
- Quotatura altezze edificio/strutture esistenti
- Indicazione strutture portanti esistenti

---

## Tavola 3 — Stato di Progetto (pianta + prospetto)

### Pianta Stato di Progetto

Riportare il progetto dell'impianto radioelettrico con:

**Elementi comuni a tutte le tipologie:**
- Posizione e tipo di struttura porta antenne (palo, palina, traliccio)
- Posizione degli apparati radio (shelter, basamenti, baggioli)
- Posizione del quadro elettrico (QPL, MiniTD, ICA)
- Percorso dei cavidotti dal punto di consegna energia agli apparati
- Percorso delle fibre ottiche
- Posizione del cilindretto/armadio stradale
- Quote significative

**Per NS-RL aggiungere:**
- Platea di fondazione con dimensioni
- Recinzione perimetrale con dimensioni e tipo
- Cancello di ingresso con dimensioni e apertura
- Accesso carrabile se presente

**Per NS-RT aggiungere:**
- Posizione e dimensioni baggioli
- Tipologia di ancoraggio (resine, tasselli)
- Percorso cavi su copertura

### Prospetti Stato di Progetto

- Prospetto con struttura porta antenne a progetto
- Quota di installazione delle antenne
- Altezza struttura portante
- Antenne previste (numero, tipologia, orientamento indicativo)
- Apparati previsti in quota

---

## Tavola 4 — Comparazione (Stato di Fatto vs Stato di Progetto)

Presentare affiancati o sovrapposti (con colori differenti) lo stato di fatto e lo stato di progetto per evidenziare:
- **Rosso / tratteggio**: elementi da demolire (se TC con modifiche)
- **Verde / solido**: nuovi elementi da installare
- **Nero**: elementi esistenti da mantenere

**Comparazione pianta:**
- Sovrapposizione piante con legenda colori
- Dimensioni principali

**Comparazione prospetto:**
- Confronto altezze prima e dopo
- Ingombro visivo dell'impianto

---

## Scale di Rappresentazione Consigliate

| Tavola | Scala raccomandata |
|--------|--------------------|
| Cartografia IGM/CTR | 1:10.000 o 1:25.000 |
| Estratto catastale | 1:2.000 o 1:1.000 |
| Estratto PRG | 1:2.000 o 1:5.000 |
| Pianta stato fatto/progetto NS-RL | 1:200 o 1:100 |
| Pianta stato fatto/progetto NS-RT | 1:100 o 1:50 |
| Prospetti | 1:100 o 1:50 |
| Dettagli | 1:20 o 1:10 |

---

## Conformità Urbanistica e Autorizzativa

La progettazione architettonica deve tenere conto di:

- **D.Lgs. 259/2003** (Codice delle Comunicazioni Elettroniche) — art. 86-87: procedura autorizzativa impianti TLC
- **L.R. regionale** di riferimento per gli impianti radiobase
- **PRG/PUC** del Comune: verificare destinazione d'uso e ammissibilità impianti TLC
- **Regolamento comunale** per impianti di telefonia mobile (se esistente)
- Eventuale presenza di **vincoli paesaggistici** (D.Lgs. 42/2004): in tal caso attivare skill **architetto-beni-monumentali**
- Eventuale presenza di **beni culturali** nelle vicinanze

## Attivare Skill Complementari

- **progettazione-architettonica** — per calcolo superfici, verifiche normative DPR 380/2001
- **architetto-beni-monumentali** — se il sito è in area vincolata (Soprintendenza)
- **diritto-italiano** — per verifiche normative specifiche regionali/comunali
