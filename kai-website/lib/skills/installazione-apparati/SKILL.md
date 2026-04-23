---
name: installazione-apparati
description: >
  Skill per l'installazione degli apparati Nokia AirScale nei siti iliad, configurazioni T1 e T3,
  moduli RFM, RRH, FCOB, ACOC, NodeBox, FPRB, cablaggio feederless. Usa SEMPRE questa skill
  quando l'utente dice "installazione apparati iliad", "configurazione T1", "configurazione T3",
  "FCOB iliad", "ACOC iliad", "moduli RFM iliad", "moduli RRH iliad", "AirScale Nokia iliad",
  "NodeBox iliad", "FPRB sito", "cablaggio apparati", "jumper antenna iliad", "feederless",
  "palina installazione RRH", "FPKC montaggio", "ONE CLIP RAIL iliad", "BOOKMOUNT iliad",
  "checklist installazione apparati", "configurazione sito iliad", "T1 rawland", "T3 rooftop".
metadata:
  version: "0.1.0"
  author: "Luca Rossi"
  riferimento: "Linee guida installazione apparati iliad v.1.3"
---

# Installazione Apparati — Siti iliad Nokia AirScale

Questa skill guida l'installazione degli apparati nei siti iliad basati su tecnologia Nokia AirScale, secondo le Linee guida installazione apparati v.1.3.

> **Nota di sicurezza**: La realizzazione di cablaggi elettrici è rivolta esclusivamente a personale competente e certificato. Le attività devono essere svolte in osservanza del D.Lgs. n. 81/2008 con uso dei DPI necessari.

---

## Configurazioni Standard di Sito

iliad prevede due configurazioni standard:

### Configurazione T1 — Impianto non distribuito (RawLand tipico)

- Installazione non distribuita: **max 7 moduli radio RFM** condivisi con un massimo di **3 settori**
- Moduli radio installati all'interno del cabinet (FCOB)
- Soluzione feederless: moduli nelle immediate vicinanze dell'antenna, connessi con soli **jumper** (lunghezza massima **10 m**)
- Tipica per siti RawLand (palo + shelter/cabinet a terra)

### Configurazione T3 — Impianto distribuito (RoofTop standard)

- Installazione distribuita con moduli **RRH** (Radio Remote Head)
- Standard per siti **RoofTop** e per impianti in ambienti chiusi (room)
- Può prevedere: TMA/MHA, feeder, jumper (soluzione Feederline se necessario distanziare i moduli)
- Per tutti i siti RoofTop si predilige la configurazione T3 per minor impatto sonoro e manutentivo

> **Ogni deviazione dallo standard T1/T3 deve essere concordata con iliad.**

---

## Componenti di Sito

### 5.1 Quadri di Distribuzione Elettrica AC/DC

| Quadro | Uso | Caratteristiche |
|--------|-----|-----------------|
| **QPL** | Siti RT piccoli | Presa luce, protezione differenziale modulare o scatolato |
| **ICA** | Siti RL grandi, 5G | Interruttore Controllo e Alimentazione, trifase 400V o 230V, con/senza trasformatore |
| **MiniTD** | Siti RL standard | Mini Tavolo Distribuzione, configurazione 5G o microwave |

Per gli schemi unifilari standard consultare i file CFE-ILIAD nella cartella `02 - Impianti/01 - Quadri Elettrici/`.

### 5.2 Stazione di Energia FPRB e Moduli Batteria FPBC

- **FPRB** (Flexi Power Rack Battery): raddrizzatore AC/DC, fornisce alimentazione -48V DC ai moduli radio
- **FPBC**: moduli batteria abbinati al FPRB
- Installazione secondo Nota Tecnica FPRB/FPRB-A (cartella `02 - Impianti/05 - Stazione di energia/`)
- Il FPRB alimenta: FCOB, ACOC, moduli radio RFM/RRH, NodeBox

### 5.3 Moduli AirScale SM

| Modulo | Descrizione | Note |
|--------|-------------|------|
| **AMIx** | AirScale Indoor Module | BBU indoor |
| **ASIA** | AirScale Indoor Unit | Baseband |
| **ASIB** | AirScale Indoor Base | Baseband |
| **ABIO** | AirScale Baseband I/O | I/O module |
| **ABOC** | AirScale Baseband Outdoor | Outdoor baseband |

### 5.4 Cabinet FCOB (configurazione T1)

Il FCOB (Flexi Compact Outdoor Base) è il cabinet per configurazioni T1 non distribuite. Contiene:
- I moduli AirScale SM (BBU)
- I moduli radio RFM (fino a 7)
- Il NodeBox
- Connessione con soli jumper alle antenne (max 10m)

Installazione tipica:
- A terra su basamento/platea (RawLand)
- Su parete (wall mounted, configurazione T3)

### 5.5 Cabinet ACOC (configurazione T3)

L'ACOC (AirScale Compact Outdoor Cabinet) è il cabinet per configurazioni T3 distribuite:
- Contiene i moduli AirScale SM
- I moduli RRH vengono installati in quota sulla struttura porta antenne
- Collegamento BBU-RRH via fibra ottica fronthaul

### 5.6 AirScale Moduli Radio

#### 5.6.1 Moduli RFM — Installazione

- Installazione a plinto (rack su basamento)
- Installazione a palina (con kit FMFA, FPKC o ONE CLIP RAIL)
- Cablaggio RF: cavi coassiali tra RFM e antenne con connettori DIN 7/16

**Checklist installazione RFM:**
- RFM posizionato secondo schema di sito
- Cavi RF collegati ai settori corretti (A, B, C per 3 settori)
- Cavo di alimentazione DC collegato al FPRB
- Fibra ottica di fronthaul collegata
- Cavo allarmi collegato
- Messa a terra eseguita

#### 5.6.2 Moduli RRH — Installazione (T3)

Modalità installative RRH:

| Kit | Modalità | Utilizzo |
|-----|----------|---------|
| **FPKC** | A palina | Standard palina porta antenne |
| **FPKA** | A palina | Alternativo |
| **Dietro antenna** | Integrato | Solo se antenna compatibile |
| **BOOKMOUNT Kit** | A palina | Configurazione specifica |
| **ONE CLIP RAIL** | A palina, telaio | Montaggio rapido su palina o telaio |

**Configurazione T3 — cablaggio RRH:**
- Cavo DC dal FPRB all'RRH in quota (lunghezza massima secondo schema)
- Fibra ottica fronthaul: dal BBU (FCOB/ACOC) all'RRH
- Jumper RF: dall'RRH all'antenna (max 10m)
- Messa a terra RRH: collegamento al sistema di terra del palo
- Cavo allarmi/EAC

**Cablaggio sincronismo:**
- Segnale GPS per sincronismo 5G
- Collegamento antenna GPS al modulo BBU

### 5.7 NodeBox

Il NodeBox è l'unità di connessione/distribuzione nella configurazione feederless:

**Checklist NodeBox:**
- Posizionamento secondo schema di sito
- Connessioni ottiche verificate
- Cavi di alimentazione collegati
- Messa a terra eseguita
- LED di stato verificati

### 5.8 FOC — Flexi Outdoor Case (aggiuntivo)

Cabinet addizionale per configurazioni con maggiore numero di moduli o per futura espansione.

---

## Cablaggio RF — Regole Feederless

La configurazione feederless è lo standard iliad e prevede:
- **Nessun cavo coassiale** per l'intera linea di antenna (eliminazione feeder)
- I moduli radio (RFM o RRH) vengono installati nelle **immediate vicinanze** delle antenne
- Connessione con soli **jumper** (connettori DIN 7/16 o N)
- **Lunghezza massima jumper: 10 m** per entrambe le soluzioni T1 e T3

In caso di necessità di distanziare i moduli dai radianti (soluzione **Feederline**):
- Installazione di TMA/MHA nei pressi del sistema radiante
- Calata e cablaggio RF composta da feeder e jumper (es. 7/8", 1+1/4", ecc.)
- Eventuali Multiplexer

---

## Link Ottici per Moduli Radio e Trasmissione

Cablaggio ottico:

| Collegamento | Tipo fibra | Connettori | Lunghezza |
|-------------|-----------|------------|-----------|
| BBU → RRH (fronthaul) | OM3 MM | OCTIS/SFP+ | Secondo schema sito |
| BBU → trasmissione | SMF 9/125 | LC | Secondo schema |
| Sincronismo GPS | Coassiale | SMA | Da antenna GPS al BBU |

---

## Allarmi Esterni ed EAC

- **EAC** (External Alarm Cable): collegamento allarmi esterni al cabinet
- Allarmi tipici: porta sito, sensori ambientali, allarme rete elettrica
- Tipo cavo allarmi: schermato, sezione adeguata
- Connessione alla scheda allarmi del BBU

---

## Note Operative Importanti

1. **Approvazione preventiva**: tutti i prodotti e soluzioni tecniche devono essere preventivamente approvati da iliad
2. **Deviazioni dallo standard**: qualsiasi configurazione diversa da T1/T3 deve essere concordata con iliad
3. **TSSR**: la survey preliminare e il TSSR devono essere completati prima dell'installazione
4. **Documenti in loco**: schede radio, FSC (configurazione finale), schede tecniche e documenti esecutivi devono essere presenti in cantiere durante l'installazione

## Attivare Skill Complementari

- **elaborati-impianti** — per la progettazione degli impianti elettrici del sito
- **aweud-mmwave** — per l'installazione di apparati 5G mmWave (AWEUD)
- **tssr-b40-filler:scheda-radio-reader** — per la lettura della Scheda Radio prima dell'installazione
