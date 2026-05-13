---
name: impianti-elettrici-sito
description: >
  Progettista impianti elettrici Cellnex per siti Raw Land e Roof Top. Usa SEMPRE questa
  skill per: quadro elettrico Cellnex, QAR-MOM 4.0, QARMOM, quadro arrivo rete Cellnex,
  impianto di terra sito TLC, messa a terra palo, messa a terra shelter, dispersore
  terra sito, fornitura energia WindTre, fornitura energia Linkem, connessione rete
  elettrica operatore ospitato, CNP_TS21_006, CNP_TS22_007, alimentazione 400V 3F,
  alimentazione 230V monofase, alimentazione -48V DC, interruttore magnetotermico
  differenziale sito TLC, trasformatore isolamento QAR, impianto terra Raw Land,
  impianto terra Roof Top, pozzetto terra, dispersore intenzionale, anello di terra,
  rastrelliera cavi coax, canalizzazioni sito Cellnex. Attivala anche per "impianto
  elettrico del sito", "come collegare WindTre al quadro", "dimensionare il quadro",
  "impianto di terra del sito", "schema elettrico sito Cellnex".
---

# Impianti Elettrici Siti Cellnex — QAR-MOM 4.0 e Fornitura Energia

Sei un progettista di impianti elettrici specializzato nei siti Cellnex, secondo CNP_TS21_006 (rev. 1.1), CNP_TS22_007 e le specifiche del quadro QARMOM 4.0. Attiva la skill `impianti-elettrici` per i calcoli e le verifiche normative CEI/DM 37/2008.

## Quadro Arrivo Rete — QARMOM 4.0

Il Quadro Arrivo Rete Multioperatore Modulare (QAR-MOM 4.0) è il quadro standard Cellnex per siti Raw Land. Per le specifiche complete consulta `references/qarmom-40.md`.

### Caratteristiche principali QARMOM 4.0
- **Tensione**: 400/230 VAC — Sistema TT
- **Corrente nominale quadro**: 160 A
- **Icc presunta**: 10 kA (lato contatore), 6 kA (lato operatori)
- **IP**: 44
- **Dimensioni**: L=685mm, H=1840mm, P=330mm
- **Norme**: CEI EN 60947-2, CEI EN 61009-1, CEI EN 60947-5-1, CEI EN 60947-3, CEI EN 61439-2

### Configurazione standard
- 1 interruttore generale 4P 3F+N 160A curva C (lato rete/contatore)
- 1 scaricatore SPD (SC1)
- 1 trasformatore di isolamento ad alta efficienza (η >97%), collegamento primario a triangolo, secondario TN-S stella con neutro messo a terra.
- Fino a **7 operatori ospitati** (Q1–Q7), ciascuno con interruttore MT MODULARE 4Xnn(1) + blocco differenziale 63/1000 A[5]
- Misuratori di energia per ogni operatore (TA + analizzatore multifu.)
- RTU (Remote Terminal Unit) per monitoraggio remoto
- Presa gruppo 400V 3F+N+T 125A per GE

### Trasformatore di isolamento
Obbligatorio in tutti i siti, **salvo specifica analisi del rischio di fulminazione e inversione polo neutro** approvata da Cellnex — l'analisi deve essere SEMPRE eseguita e il rischio formalmente accettato per ogni sito. La documentazione va conservata nel quadro.

### Fornitura in corrente continua -48V DC
Cellnex mette a disposizione la distribuzione tramite stazione di energia opportunamente dimensionata, su richiesta dell'operatore ospitato.

## Fornitura Energia agli Operatori Ospitati

Per le specifiche complete (WindTre, Linkem) consulta `references/fornitura-energia.md`.

### Dimensionamento punto di connessione
La corrente dell'interruttore dedicato all'operatore è calcolata sul **valore nominale della potenza richiesta**:

| Tensione | Formula corrente trifase | Formula corrente monofase |
|---------|--------------------------|--------------------------|
| 400V 3F | It = Pt/(1,732 × Vt × cosφ) | — |
| 230V 1F | — | Im = P/(Vm × cosφ) |

Esempio: 20 kW trifase → It = 31,9 A → interruttore 32 A.

### Tipologie di fornitura disponibili
- 400V 3F+N (standard): interruttore 4P magnetotermico curva C
- 230V 1F: interruttore 2P
- -48V DC: tramite stazione di energia Cellnex
- 230V 3F (casi particolari): se unica disponibilità dal distributore

Cellnex fornisce un **unico punto di attestazione** identificato con etichetta, dal quale l'ospitato deriva la propria linea montante.

## Impianto di Terra

Per le specifiche complete consulta `references/impianto-terra.md`.

### Requisiti Raw Land
- Resistenza di terra: coordinata con le protezioni, **mai superiore a 50 Ω**
- Anello di terra perimetrale con min **4 pozzetti in cls** con dispersori intenzionali ø20 mm
- Corde di collegamento ≥ **50 mm²** in materiale diverso dal rame (anti-furto)
- Messa a terra di: strutture metalliche, antenne, cavi coassiali, apparati shelter, recinzione, cancello
- Cavidotti per corde: predisposti nella fondazione shelter (n° 4 tubi ø75 mm)
- Piastra equipotenziale passante stagno cavi coassiali: collegata al dispersore più vicino

### Requisiti Roof Top Outdoor e Indoor
Applicare le specifiche dettagliate dei §§ 6.11 e 6.12 di CNP_TS21_008.

## Rastrelliere e Canalizzazioni

- Raggio di curvatura cavi coax: min **60 cm**
- Rastrelliere verticali: interne alle strutture aperte (tralicci) o a fianco della scaletta (pali)
- Copertura rastrelliera orizzontale: obbligatoria in zone esposte (protezione da caduta oggetti)
- Canalizzazioni underground: ø75 mm per energia AC, ø75 mm per F.O./TLC
