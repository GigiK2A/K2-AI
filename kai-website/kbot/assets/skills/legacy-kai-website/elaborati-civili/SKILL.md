---
name: elaborati-civili
description: >
  Skill per la redazione degli elaborati grafici costruttivi delle opere civili del PE iliad.
  Usa SEMPRE questa skill quando l'utente dice "elaborati civili iliad", "tavole costruttive",
  "sviluppo fondazione", "sviluppo platea", "plinto di fondazione iliad", "platea di fondazione",
  "recinzione sito iliad", "cancello sito", "carpenteria rawland", "carpenteria rooftop",
  "baggioli rooftop", "tavole costruttive rawland", "tavole costruttive rooftop",
  "tracciamento sito", "sezioni di sito", "mc di scavo", "lista pezzi carpenteria",
  "distinta carpenteria", "peso carpenteria", "bulloni zincatura incidenza",
  "linee guida civili iliad", "realizzazioni civili rawland", "realizzazioni civili rooftop".
metadata:
  version: "0.1.0"
  author: "Luca Rossi"
  riferimento: "Linea Guida PE iliad v.1.1 + Linee guida realizzazioni civili Rawland v.1.2 + Rooftop v.1.4"
---

# Elaborati Grafici Costruttivi — Opere Civili PE iliad

Questa skill guida la redazione delle tavole costruttive delle opere civili, differenziate per tipologia di sito.

## NS-RL — New Site RawLand: Tavole Costruttive

### Tavola 1 — Tracciamento

Contenuto minimo:
- Planimetria dell'area con sistema di coordinate (UTM WGS84 o Gauss-Boaga)
- Coordinate angoli del sito
- Orientamento nord geografico
- Dimensioni perimetrali dell'area
- Distanze da elementi di riferimento (strade, confini, edifici)
- Posizione del palo con coordinate e distanza dai confini
- Posizione platea con dimensioni e distanza dai confini
- Capibastone/caposaldi di riferimento

### Tavola 2 — Sezioni di Sito

Contenuto obbligatorio:
- Sezione trasversale e longitudinale del sito
- Indicazione: livello piano campagna, piano platea, piano fondazione
- Profondità di scavo per fondazione e platea
- Indicazione tipo di terreno (da relazione geotecnica)
- **Tabella riassuntiva mc di scavo** (obbligatoria):
  - Volume scavo fondazione palo
  - Volume scavo platea
  - Volume scavo cavidotti
  - Eventuali volumi aggiuntivi con motivazione (ragioni operative o di sicurezza)
  - Totale mc di scavo
- Indicazione smaltimento materiale di risulta

### Tavola 3 — Sviluppo Fondazione (Plinto del Palo)

Contenuto obbligatorio:
- Pianta del plinto con dimensioni in pianta
- Sezione del plinto con:
  - Quota testa plinto (rispetto p.c.)
  - Quota piano di posa (rispetto p.c.)
  - Dimensioni plinto (L × B × H)
  - Armatura longitudinale (diametro, numero, passo)
  - Armatura trasversale (staffe: diametro, passo)
  - Copriferro
  - Classe calcestruzzo (es. C25/30 o C28/35) e classe esposizione
  - Bulloneria di ancoraggio palo (diametro, numero, lunghezza, materiale, zincatura)
  - Piastra di base palo (dimensioni, spessore, qualità acciaio)
- **Tabella riassuntiva fondazione:**

| Voce | Valore |
|------|--------|
| Dimensioni plinto (L × B × H) | [m × m × m] |
| Volume cls plinto | [m³] |
| Peso ferri d'armatura | [kg] |
| Classe calcestruzzo | [C25/30] |
| Classe acciaio armatura | [B450C] |

### Tavola 4 — Sviluppo Platea

Contenuto obbligatorio:
- Pianta della platea con dimensioni
- Sezione della platea
- Spessore platea (tipicamente 15-20 cm)
- Armatura (rete elettrosaldata o barre, diametro e passo)
- Posizione e dimensioni pozzetti di ispezione
- Percorso tubazioni sotto platea (diametri, materiali, profondità)
- **Elementi da annegare nella platea** (obbligatori, da indicare chiaramente):
  - Montanti del cancello di ingresso
  - Montanti della recinzione
  - Ferri di chiamata per baggioli/basamenti apparati
  - Tubi corrugati per passaggio cavi
  - Connettori equipotenziali
- **Tabella riassuntiva platea:**

| Voce | Valore |
|------|--------|
| Dimensioni platea (L × B × H) | [m × m × m] |
| Volume cls platea | [m³] |
| Peso rete/ferri d'armatura | [kg] |

### Tavola 5 — Cancello di Ingresso

Contenuto:
- Pianta con dimensione luce cancello (larghezza passaggio)
- Prospetto cancello (fronte esterno)
- Sezione verticale
- Tipo di cancello (scorrevole, battente, ecc.)
- Materiale e trattamento superficiale
- Serratura e sistema di apertura
- Fondazione montanti (dettaglio annegamento in platea)

### Tavola 6 — Recinzione

Contenuto:
- Planimetria con perimetro recinzione e lunghezza totale
- Sezione tipo della recinzione
- Altezza recinzione (tipicamente ≥ 2,00 m)
- Tipo di recinzione (rete metallica zincata plastificata su pali tubolari, muratura, ecc.)
- Interasse pali
- Fondazione tipo pali (dettaglio interramento o ancoraggio in platea)
- Eventuale filo spinato sommitale

### Tavola 7 — Carpenteria a Terra

Per ogni elemento di carpenteria metallica a terra (basamenti apparati, shelter, sistemi di ancoraggio):

Contenuto obbligatorio:
- Tavola costruttiva con dimensioni e spessori di ogni componente
- Qualità acciaio (tipicamente S275 o S355)
- Trattamento superficiale (zincatura a caldo per immersione, classe, spessore)
- Saldature (tipo, classe)

**Lista pezzi obbligatoria:**

| Pos. | Descrizione | Profilo/Sezione | Lunghezza [m] | N° | Peso unit. [kg] | Peso tot. [kg] |
|------|-------------|-----------------|---------------|----|-----------------|----------------|
| | | | | | | |
| | **TOTALE CARPENTERIA STRUTTURALE** | | | | | **[kg]** |
| | Bulloneria (incidenza ≤ 10%) | | | | | **[kg]** |
| | Zincatura (incidenza ≤ 10%) | | | | | **[kg]** |
| | **TOTALE COMPLESSIVO** | | | | | **[kg]** |

> **NOTA CRITICA**: L'incidenza di bulloni + zincatura deve essere ≤ 10% del peso della carpenteria strutturale. Verificare sempre questo requisito.

---

## NS-RT — New Site RoofTop: Tavole Costruttive

### Tavola 1 — Tracciamento Baggioli

Contenuto:
- Pianta della copertura in scala con identificazione univoca di ogni baggiolo
- Numerazione baggioli (B1, B2, ecc.)
- Quote e distanze dei baggioli dai bordi e tra loro
- Posizione strutture esistenti (parapetti, vani scala, ecc.)
- Sistema di riferimento

### Tavola 2 — Sviluppo Dettagliato Baggioli

Per ogni tipo di baggiolo (o per ogni baggiolo se diversi tra loro):

Contenuto obbligatorio:
- Pianta e sezione del baggiolo con dimensioni
- Stratigrafia della copertura esistente
- **Demolizioni e ripristini**: indicare chiaramente cosa viene demolito e come viene ripristinato il manto impermeabile
- **Collegamento alla struttura portante esistente**: dettaglio dell'ancoraggio al solaio (forometria, diametro fori, profondità)
- **Tipologia resine**: specificare il tipo di resina epossidica usata per l'ancoraggio (produttore, codice prodotto, caratteristiche meccaniche)
- Dimensioni del baggiolo (L × B × H)
- Classe calcestruzzo (se in cls armato)
- Armatura (se presente)

### Tavola 3 — Tavole di Assieme Carpenteria

- Pianta della copertura con posizione di tutte le strutture porta antenne
- Prospetti (almeno 2 lati) con strutture porta antenne
- Sezioni significative
- Posizionamento su baggioli o strutture esistenti con misure di posizionamento

### Tavola 4 — Costruttivi Carpenteria

Dettaglio costruttivo di ogni elemento di carpenteria:
- Palina porta antenne (dimensioni, spessori, flange)
- Sbracci porta antenne (geometria, sezioni)
- Sistemi di fissaggio alla struttura esistente

### Tavola 5 — Distinta Carpenteria RoofTop

La distinta deve essere **suddivisa** in due parti:

**Parte A — Carpenteria strutture porta antenne:**

| Pos. | Descrizione | Profilo/Sezione | Lunghezza [m] | N° | Peso unit. [kg] | Peso tot. [kg] |
|------|-------------|-----------------|---------------|----|-----------------|----------------|
| | | | | | | **[kg]** |

**Parte B — Altra carpenteria (basamenti, canaline, supporti, ecc.):**

| Pos. | Descrizione | Profilo/Sezione | Lunghezza [m] | N° | Peso unit. [kg] | Peso tot. [kg] |
|------|-------------|-----------------|---------------|----|-----------------|----------------|
| | | | | | | **[kg]** |

**Riepilogo:**

| Voce | Peso [kg] | % |
|------|-----------|---|
| Carpenteria strutture porta antenne (A) | | |
| Altra carpenteria (B) | | |
| Bulloneria (≤ 10% totale A+B) | | |
| Zincatura (≤ 10% totale A+B) | | |
| **TOTALE** | | 100% |

---

## TC-RL — Transfer/Colocation RawLand: Tavole Costruttive

Oltre alle tavole del caso NS-RL (adattate alla situazione di colocazione), aggiungere:

### Tavola Carpenteria in Quota

Per i nuovi supporti che vengono installati sul palo esistente:
- Sviluppo porta antenne in quota
- Sviluppo porta parabole in quota
- Sviluppo porta moduli in quota
- Lista pezzi e tabella peso (incl. bulloni e zincatura)

### In caso di rinforzo fondazione

- Sezioni di sito con indicazione del rinforzo del plinto e area di scavo
- Tabella mc di scavo aggiuntivi + volumi demolizioni manufatti esistenti
- Sviluppo rinforzo plinto (volumi cls e peso ferri d'armatura)

---

## Regole Generali per gli Elaborati Civili

1. **Scala**: indicare sempre la scala; usare scale normalizzate (1:100, 1:50, 1:20, 1:10, 1:5)
2. **Quotatura**: quotare tutti gli elementi significativi in modo completo
3. **Cartiglio**: ogni tavola deve avere cartiglio con: Codice Sito, Nome Sito, Titolo tavola, Scala, Data, Rev., Fornitore, Progettista
4. **Unità di misura**: misure lineari in [m] o [mm] con indicazione; pesi in [kg]; volumi in [m³]
5. **Materiali**: specificare sempre classe calcestruzzo, classe acciaio, trattamento superficiale
6. **Normative di riferimento**: NTC 2018 (D.M. 17/01/2018), EC2 per cls armato, EC3 per acciaio

## Attivare Skill Complementari

- **progettista-strutturale** — per il calcolo strutturale delle opere civili (NTC 2018)
- **impianti-elettrici** — per la parte di cavidotti e tubazioni
