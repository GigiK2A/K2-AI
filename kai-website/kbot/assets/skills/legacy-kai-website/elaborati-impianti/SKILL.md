---
name: elaborati-impianti
description: >
  Skill per la redazione degli elaborati grafici e relazioni di calcolo degli impianti elettrici
  del Progetto Esecutivo iliad. Usa SEMPRE questa skill quando l'utente dice "impianti PE iliad",
  "relazione calcolo impianto elettrico iliad", "elaborati grafici impianti", "schema unifilare
  quadro iliad", "ICA iliad", "MiniTD iliad", "QPL iliad", "armadio stradale iliad",
  "rete di terra iliad", "impianto di terra sito radio", "planimetria allacciamenti",
  "pianta impianto elettrico sito", "schema a blocchi rete di terra", "verifica scariche
  atmosferiche", "LPS antenna iliad", "dispersori verticali orizzontali sito TLC",
  "impianto condizionamento shelter", "schemi unifilari PE", "calcolo impianto elettrico TLC".
metadata:
  version: "0.1.0"
  author: "Luca Rossi"
  riferimento: "Linea Guida PE iliad v.1.1 + Linee Guida impianti di messa a terra v.2.0 + Schemi 2025"
---

# Elaborati Impianti — PE iliad

Questa skill guida la redazione degli elaborati grafici e delle relazioni di calcolo degli impianti elettrici del PE iliad.

## Composizione Elaborati Impianti

1. Relazione di calcolo impianto elettrico
2. Planimetria allacciamenti
3. Pianta impianto elettrico (completa)
4. Dettaglio armadio stradale (contatore / QPL)
5. Schemi unifilari quadri elettrici
6. Pianta impianto di terra
7. Schema a blocchi rete di terra
8. Piante e schema a blocchi impianto condizionamento/estrazione aria (se presente)
9. Verifica scariche atmosferiche (LPS)

---

## Tipologie di Quadri Elettrici iliad

| Acronimo | Nome | Uso tipico |
|----------|------|-----------|
| **ICA** | Interruttore di Controllo e Alimentazione | Siti grandi NS-RL con alta potenza installata |
| **MiniTD** | Mini Tavolo Distribuzione | Siti NS-RL standard |
| **QPL** | Quadro Presa Luce | Siti NS-RT e TC (minore potenza) |

La scelta del tipo di quadro dipende dalla potenza richiesta e dalla configurazione del sito. Verificare con le specifiche iliad applicabili (Schemi 2025.pdf).

---

## Elaborato 1 — Relazione di Calcolo Impianto Elettrico

La relazione deve includere:

### 1.1 Dati generali
- Codice e nome sito
- Tipologia di allacciamento (fornitura trifase 400V o monofase 230V)
- Gestore di rete elettrica locale
- Potenza contrattuale prevista

### 1.2 Carichi installati
Tabella carichi:

| Apparato | Marca/Modello | Potenza [W] | N° | Pot. Tot. [W] | Alimentazione |
|----------|--------------|-------------|----|-|--------------|
| BTS/RRU | | | | | 230V/48Vdc |
| Apparati trasmissione | | | | | |
| Allarmi | | | | | |
| Condizionatore | | | | | |
| Ausiliari | | | | | |
| **TOTALE** | | | | **[W]** | |

### 1.3 Dimensionamento linee
- Calcolo caduta di tensione per la linea principale
- Sezione cavo di alimentazione principale
- Sezione cavi derivazione ai carichi
- Verifica termica (portata cavo in relazione al percorso)

### 1.4 Protezioni
- Interruttore generale (Im, In, Icc di corto circuito)
- Protezione differenziale (Id, tipo AC/A/F/B secondo carico)
- Coordinamento protezioni (selettività)
- SPD (scaricatori di sovratensione) se previsti

### 1.5 Impianto di terra
- Resistenza di terra target (≤ 10 Ω per sistemi TT)
- Tipo di dispersori (verticali a croce/picchetto, orizzontale a nastro)
- Calcolo resistenza di terra complessiva
- Collegamento equipotenziale

---

## Elaborato 2 — Planimetria Allacciamenti

Contenuto:
- Planimetria in scala del sito con:
  - Posizione punto di consegna energia (armadio stradale / pozzetto ENEL)
  - Percorso cavidotto di alimentazione (dal punto di consegna al quadro principale)
  - Percorso fibra ottica (da pozzetto TLC/operatore fibra al shelter/basamento)
  - Indicazione tipo e diametro tubazioni
  - Indicazione sezione cavi elettrici
  - Quote e distanze significative
  - Strade e infrastrutture adiacenti (per contestualizzare il percorso)

---

## Elaborato 3 — Pianta Impianto Elettrico (completa)

Contenuto obbligatorio:
- Planimetria del sito in scala con TUTTI i seguenti elementi:
  - **Cavi elettrici**: percorso, tipo (FG7OR, N07V-K, ecc.), sezione
  - **Minitubo per fibra ottica**: percorso, diametro
  - **Cavi allarmi**: percorso, tipo
  - **Jumper** (connessioni tra apparati radio e antenne): percorso
  - **Pozzetti**: tipo, dimensioni, posizione con coordinate
  - **Canaline e tubazioni**: tipo (IMQ, acciaio zincato, PVC), dimensioni
  - **Posizione quadri elettrici nuovi**: tipo (ICA/MiniTD/QPL), dimensioni
  - **Posizione quadri elettrici esistenti**: se presenti (TC)

**Tabella riassuntiva componenti obbligatoria:**

| Componente | Tipo/Sigla | Sezione/Diametro | Lunghezza [m] | Note |
|------------|-----------|-----------------|---------------|------|
| Cavo alimentazione principale | FG7OR | [mm²] | | |
| Minitubo fibra ottica | | Ø [mm] | | |
| Cavo allarmi | | | | |
| Pozzetto tipo A | | | N° | |
| Cavidotto principale | | Ø [mm] | | |

---

## Elaborato 4 — Dettaglio Armadio Stradale

Per i siti con contatore/QPL su strada pubblica:

Contenuto:
- Posizione in pianta e prospetto (rispetto a marciapiede, confine, ecc.)
- Tipo armadio (VTR = Vetroresina oppure cemento armato)
- Dimensioni esterne (L × P × H)
- Fondazione (tipologia, dimensioni, profondità)
- Dettaglio interno (posizione contatore, QPL, cavi in entrata/uscita)
- Fissaggio al suolo e ancoraggio

---

## Elaborato 5 — Schemi Unifilari Quadri Elettrici

Produrre uno schema unifilare per ogni quadro presente (ICA, MiniTD, QPL).

**Contenuto minimo schema unifilare:**
- Interruttore generale (In, Im, potere interruzione)
- Interruttori differenziali (In, Id, tipo)
- Interruttori magnetotermici derivazioni (In, Im)
- Nominativo/destinazione di ogni uscita (BTS, RRU, allarmi, condizionatore, ecc.)
- Schema di connessione SPD (se presente)
- Alimentazione: tensione, frequenza, sistema (TT, TN)
- Sezione cavi in entrata e uscita

Fare riferimento agli **Schemi 2025.pdf** nella cartella `/02 - Impianti/` per i layout standard iliad.

---

## Elaborato 6 — Pianta Impianto di Terra

Contenuto obbligatorio (riferimento: Linee Guida impianti di messa a terra v.2.0):

- Planimetria del sito con:
  - Posizione e tipo di tutti i **pozzetti** di ispezione terra
  - **Barre di terra** principali e secondarie (posizione, tipo, lunghezza)
  - **Dispersori verticali** (picchetti a croce, lunghezza, interasse): posizione e numero
  - **Dispersori orizzontali** (nastro in acciaio zincato o rame): percorso e dimensioni
  - **Anello di terra** perimetrale (se previsto)
  - **Collegamenti di protezione**: dal quadro al dispersore
  - **Collegamenti equipotenziali**: tra palo, shelter, recinzione, baggioli, ecc.
  - Connettori e giunzioni (tipo e posizione)

**Schema a blocchi rete di terra** (separato dalla pianta o in angolo):
- Rappresentazione funzionale dei collegamenti: Palo → Barra Terra → Dispersori → Equipotenziali

---

## Elaborato 7 — Impianto Condizionamento / Estrazione Aria

(Solo se previsto impianto di condizionamento o estrazione aria — tipicamente per shelter chiusi)

Contenuto:
- Pianta con posizione unità esterna e interna
- Schema a blocchi dell'impianto (ciclo frigorifero, circolazione aria)
- Specifiche tecniche (potenza frigorifera, COP, fluido frigorigeno)
- Percorso tubazioni freon e cavi elettrici

---

## Elaborato 8 — Verifica Scariche Atmosferiche (LPS)

La verifica deve essere eseguita secondo:
- **CEI EN 62305** (CEI 81-10): Protezione contro i fulmini
- **D.M. 22/01/2008** n. 37

Contenuto della verifica:
- **Dati sito**: coordinate GPS, quota altimetrica, zona geografica
- **Densità di fulmini a terra** (Ng) per la zona (da carta isoceramica o CEI 81-3)
- **Caratteristiche struttura**: dimensioni, altezza, materiale
- **Calcolo rischio** (R1 perdita vite umane, R2 perdita servizi pubblici, R3 perdita patrimonio)
- **Confronto con rischio tollerabile** (RT = 10⁻⁵ per R1)
- **Conclusione**:
  - Se R < RT: non necessario LPS
  - Se R ≥ RT: progettare LPS indicando il **livello di protezione (LPL I, II, III o IV)**

**In caso di necessità LPS:**
- Tipo di captatori previsti (naturali o artificiali: punta Franklin, fune, maglia)
- Percorso calate (numero, tipo, materiale)
- Dispersori di terra (dimensioni, profondità)
- Giunti di controllo
- Distanza di separazione da installazioni interne

---

## Prescrizioni Obbligatorie — Linee Guida Impianti Elettrici iliad V2.0

Le Linee Guida Impianti Elettrici iliad V2.0 aggiungono i seguenti requisiti vincolanti:

### Marcatura CE cavi (OBBLIGATORIA)
> **Tutti i cavi per la realizzazione degli impianti devono obbligatoriamente riportare marcatura CE in accordo con il Regolamento CPR (UE) 305/2011 dal 1° Luglio 2017.**

Verificare nella relazione di calcolo e negli elaborati grafici che tutti i cavi siano conformi CPR.

### Qualità materiali
Tutti i materiali e le apparecchiature devono essere conformi a:
- Prescrizioni antinfortunistiche vigenti
- Tabelle UNEL
- Norme CEI (versione italiana delle norme europee CENELEC EN)

### Dichiarazione di conformità (D.M. 37/08)
A conclusione lavori, l'impresa realizzatrice deve produrre e rilasciare la **dichiarazione di conformità** dell'impianto realizzato con allegata relazione tipologica dei materiali utilizzati.

### Competenze del progettista
La progettazione esecutiva delle opere impiantistiche deve essere incaricata a un **tecnico abilitato** che consideri:
- Tensioni nominali
- Tipo di sistema elettrico (TT, TN-C, TN-S, ecc.)
- Corrente di cortocircuito al punto di consegna del distributore
- Tarature delle protezioni predisposte dall'ente fornitore di energia
- Ambienti installativi (aree pubbliche, reti ferroviarie, autostrade, ospedali, scuole, ecc.)

### Sistema elettrico standard iliad
Il sistema elettrico iliad è di tipo **TT** (neutro collegato a terra lato fornitore, masse collegate a terra lato utilizzatore). Il conduttore PE non deve mai essere sezionato.

### Siti rurali — Trasformatore di isolamento
Per i siti in zone rurali o con rete di distribuzione non affidabile: prevedere **trasformatore di isolamento** (sezione 9 della LG Impianti Elettrici V2.0).

### Classificazione circuiti
- **Circuiti AC di potenza**: protezioni D.M. 37/08, differenziali tipo A o B secondo la natura del carico
- **Circuiti DC (-48V)**: protezione specifica per sistemi in corrente continua (FPRB/FPBC)
- **Circuiti segnalazione allarmi**: cavo schermato, protezione corto circuito
- **Conduttori di protezione ed equipotenziali**: sezione min. PE = S fase (S ≤ 16mm²) o 16mm² (S > 35mm²)

---

## Normative di Riferimento

| Ambito | Normativa |
|--------|-----------|
| Impianti elettrici in BT | CEI 64-8 |
| Progettazione impianti | D.M. 37/2008 |
| Cavi — marcatura CE | Regolamento CPR (UE) 305/2011 |
| Messa a terra | CEI 64-8 Parte 5-54; DPR 462/2001 |
| Sicurezza lavori elettrici | CEI 11-27; D.Lgs. 81/2008 |
| Fulminazione | CEI EN 62305 (CEI 81-10) |
| Quadri di distribuzione BT | CEI EN 61439 |
| Protezione sovratensioni | CEI EN 61643-11 |
| Sistemi DC -48V | CEI EN 62368 |
| Classificazione sistemi (TT/TN/IT) | CEI 64-8/2 |

## Attivare Skill Complementari

- **impianti-elettrici** — per calcoli dettagliati (caduta tensione, cortocircuito, coordinamento protezioni, impianto di terra)
- **progettista-strutturale** — per eventuali sistemi di ancoraggio quadri su strutture
- **cellnex-progettazione-esecutiva:impianti-elettrici-sito** — per confronto con standard altri operatori TLC
