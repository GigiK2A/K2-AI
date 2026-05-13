# Fornitura Energia agli Operatori Ospitati — CNP_TS21_006/007

## Riferimenti Normativi

- **CNP_TS21_006** (Rev. 1.1 — 24/09/2021): Connessione rete elettrica cliente WindTre
- **CNP_TS22_007**: Connessione rete elettrica cliente Linkem
- Tutte le normative CEI vigenti, DM 37/2008, DPR 462/2001

**Tutti i dispositivi devono essere conformi agli standard CE e certificati. Installati secondo indicazioni del fabbricante.**

## Generalità

Cellnex a seguito delle richieste degli operatori ospitati (modulo VIC o Service Order) predispone la connessione al proprio impianto elettrico. L'ospitato deve dichiarare:
- **Potenza nominale massima richiesta** in kW
- **Tensione nominale** di erogazione

Tutte le attività devono essere conformi alle norme tecniche italiane vigenti (CEI, DM 37/2008). La rispondenza alle norme è verificata con propri tecnici di fiducia dall'ospitato.

## Caratteristiche della Connessione

### Punto di Attestazione
Cellnex fornisce un **unico punto di attestazione** per ogni operatore, chiaramente identificato con etichetta, posizionato in uno dei quadri elettrici del sito. Dal punto di attestazione, l'ospitato deriva la propria linea montante verso il proprio Quadro di Distribuzione Interfaccia Apparati (QIA).

### Tipologie di Fornitura Disponibili

| Tipo | Caratteristiche | Note |
|------|----------------|------|
| AC 400V 3F+N | Trifase standard | Caso più comune |
| AC 230V 1F | Monofase | Per carichi ridotti |
| AC 230V 3F | Solo se unica disponibilità dal distributore | Caso particolare |
| DC -48V | Tramite stazione di energia Cellnex | Su richiesta specifica |

### Fornitura in Corrente Alternata (AC)
Cellnex rende disponibile un **interruttore 4P (3F+N) magnetotermico o magnetotermico-differenziale curva "C"** a 400V nominale.

A questo verrà collegato il Quadro di Distribuzione Interfaccia Apparati (QIA) dell'ospitato, che:
- Deve contenere i dispositivi di protezione e sicurezza verso i propri apparati
- Deve contenere le proprie linee previste dalla normativa
- L'ospitato è sempre obbligato a verificare la rispondenza alle norme della propria installazione

### Fornitura in Corrente Continua DC (-48V)
Cellnex determina opportunamente il punto di erogazione sulla base della potenza richiesta dall'ospitato.

## Dimensionamento

### Formula di Calcolo Corrente Interruttore

| Tensione | Formula It (trifase) | Formula Im (monofase) |
|---------|---------------------|-----------------------|
| 400V 3F | It = Pt/(1,732 × Vt × cosφ) | — |
| 230V 1F | — | Im = P/(Vm × cosφ) |

**Esempio WindTre 5G**: per massima configurazione con sistemi radianti + batterie (3,5 kW da contratto 5G):
- Considerata soglia tolleranza eccesso e contemporaneità carica batterie
- Richiesta trifase 20 kW: It = 31,9 A → interruttore 32A; Im = 55,5 A

Cellnex effettua le valutazioni in merito all'adeguamento dell'impianto nei **parametri massimi esplicitati** nelle specifiche per singolo operatore.

## Punto di Connessione

Il punto di connessione è individuato in uno dei quadri elettrici del sito (QARMOM o quadri derivati), correttamente identificato con etichetta e indicato all'ospitato.

**Accessibilità**: la porzione di impianto a monte del punto di attestazione è di competenza Cellnex e **non è accessibile al personale degli operatori ospitati**. Per lavori sulla montante di collegamento tra quadro Cellnex e QIA dell'ospitato, l'ospitato deve richiedere l'intervento di personale Cellnex per disarmare l'interruttore.

## Segnalazione Scatto Interruttore

Il punto di connessione fornito da Cellnex garantisce, tramite contatto ausiliario, la segnalazione di scatto interruttore ai fini della responsabilità di intervento.

## Certificazioni

Tutti i dispositivi oggetto della fornitura, sia semplici che complessi, devono possedere le certificazioni di legge (ab-origine) del produttore, allegate ad ogni elemento di fornitura, garantendo la rispondenza a tutte le prescrizioni vigenti (norme tecniche, di settore, di qualità, di sicurezza, ecc.).
