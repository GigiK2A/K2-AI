# Quadro Arrivo Rete Multioperatore Modulare 4.0 — QARMOM 4.0

## Identificazione

- **Nome**: QAR-Multioperatore Modulare 4.0 (QARMOM 4.0)
- **Produttore**: Galata (una società Cellnex)
- **Disegno**: QARMOM 4.0/002 — Rev. D — 11 Ottobre 2019
- **Applicazione**: siti Raw Land Cellnex (apparati indoor shelter/cabinet o outdoor)

## Caratteristiche Meccaniche ed Elettriche

| Parametro | Valore |
|-----------|--------|
| Tensione nominale | 400/230 VAC |
| Sistema di neutro | TT |
| Icc presunta lato rete/contatore | 10 kA |
| Icc presunta lato operatori | 6 kA |
| Corrente nominale quadro | 160 A |
| Frequenza | 50 Hz |
| IP contenitore | 44 |
| Dimensioni | L=685mm, H=1840mm, P=330mm |

## Norme di Riferimento

| Componente | Norma |
|-----------|-------|
| Interruttori modulari | CEI EN 60947-2 |
| Blocchi differenziali | CEI EN 61009-1 |
| Lampade segnalazione | CEI EN 60947-5-1 |
| Sezionatori fusibili | CEI EN 60947-3 |
| Quadro assiemato | CEI EN 61439-2 |

## Schema Funzionale

### Lato Rete (circuiti 1-8)
- **SC1**: scaricatore SPD contro sovratensioni
- **F1**: sezionatore fusibile principale
- **Q1**: interruttore generale 4P 3F+N 160A curva C, lato contatore/rete
- **Q2**: commutatore RETE–0–GRUPPO (per eventuale gruppo di continuità)
- **TA1**: trasformatore di corrente lato rete
- **M1**: analizzatore di energia lato rete
- **RA**: relè ausiliario segnalazione scatto interruttore

### Trasformatore di Isolamento
- Rendimento >97%
- Collegamento primario: **a triangolo** (lato BT del distributore)
- Collegamento secondario: TN-S **a stella** con neutro messo a terra
- Lo schermo tra primario e secondario deve essere messo a terra

### Operatori Ospitati (circuiti 9-26 — fino a 7 operatori)
Per ogni operatore (Q3–Q7 per gli ospitati):
- Interruttore MT MODULARE 4Xnn(1) (corrente max in funzione della potenza richiesta)
- Blocco differenziale: 63/1000, tipo A[5]
- Trasformatore di corrente misura: TA (rapporto in funzione della corrente)
- Analizzatore multifunzione (Mor. Pas 35mmq/4)
- Trasformatore amperometrico: 3F 125A/1 (per misura energia)
- Riarmo automatico differenziale

### Misure e Protezioni Aggiuntive
- Circuiti 24-26: F1, F2, F3 — fusibili portafusibili 10x38 Gg 2A (1) per protezioni accessorie
  - Prot. Misura VAc 3F: 3P+N 690V 32A
  - Prot. Misura VAc 1F: 1P+N 690V 32A
  - Alim. Anal. Mult.: 10x38 Gg 2A (1)

## Funzioni del Quadro

1. Sezionamento linea montante dal contatore (se distanza QAR-contatore > 3 m)
2. Protezione magnetotermica differenziale a valle del quadro (guasti a terra, contatti indiretti)
3. Misura dell'energia elettrica per ogni operatore ospitato
4. Protezione contro sovratensioni da rete (SPD)
5. Svincolo neutro e isolamento galvanico verso la rete BT (con trasformatore di isolamento)
6. Alimentazione e monitoraggio consumi dei circuiti di servizio del sito
7. Ospitare e alimentare la RTU (Remote Terminal Unit) per monitoraggio remoto
8. Espansione modulare fino a max 4×400V trifase + 2×230V monofase (160A totali)

## Presa Gruppo di Continuità

- **Presa gruppo**: 400V 3F+N+T corrente nominale **125A**
- **Commutatore Q2**: RETE–0–GRUPPO (evita il parallelo tra i due sistemi)

## Regola di Dimensionamento Interruttore Operatore

L'interruttore dedicato a ogni operatore è dimensionato sulla **potenza nominale massima richiesta** dichiarata nel modulo VIC (o Service Order):

| Tensione | Formula | Esempio 20 kW |
|----------|---------|---------------|
| 400V 3F | It = Pt/(1,732 × Vt × cosφ) | 31,9 A → interruttore 32A |
| 230V 1F | Im = P/(Vm × cosφ) | 55,5 A → interruttore 63A |

**Tutti i dispositivi elettrici devono possedere le certificazioni di legge (ab-origine) del produttore**, allegate ad ogni elemento di fornitura. Una copia deve essere sempre presente internamente al quadro.

## Installazione

- Posizionato in prossimità della recinzione del sito (non all'interno dell'area degli apparati)
- Accessibile solo a personale Cellnex (non agli operatori ospitati)
- Connessione all'impianto di terra del sito
