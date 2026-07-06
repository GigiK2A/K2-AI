# Analisi del Progetto Esecutivo per Valutazione Rischi Specifici

> Questo reference guida l'analisi della documentazione progettuale (scheda radio, planimetrie, order form, tavole tecniche, relazioni) per individuare rischi specifici del cantiere legati al posizionamento, alla configurazione impiantistica e alle condizioni del sito.

---

## A. Principio: dal progetto ai rischi

Un PSC conforme non può basarsi su ipotesi generiche. L'Allegato XV del D.Lgs. 81/2008 (punto 2.1.2, lettere a-d) impone che il PSC contenga la descrizione dell'opera e del contesto **specifico** in cui si colloca. Il progetto esecutivo è la fonte primaria da cui ricavare:

1. **Dove** si lavora → posizionamento, quota, tipo di struttura → rischi di caduta, accesso, interferenze
2. **Cosa** si installa → peso, dimensioni, numero componenti → rischi MMC, sollevamento, ingombro
3. **Come** si lavora → sequenza fasi, attrezzature necessarie → rischi interferenziali, macchine
4. **Con cosa** si interagisce → impianti esistenti, strutture adiacenti, sottoservizi → rischi elettrici, CEM, cedimento

---

## B. Documenti progettuali tipici e cosa estrarre

### B.1 — Scheda Radio / Scheda Tecnica Sito (TLC)

La Scheda Radio è il documento cardine per i cantieri K2A TLC. Contiene:

| Dato da estrarre | Dove si trova nella Scheda Radio | Impatto sul PSC |
|-----------------|--------------------------------|-----------------|
| **Codice sito e nome** | Intestazione | Cap. 2 Anagrafica |
| **Indirizzo, Comune, Provincia** | Dati generali | Cap. 2 + Cap. 6.1 Inquadramento |
| **Tipo sito** (Roof Top / Palo / Lattice / Ground Based) | Classificazione | Determina l'intero profilo di rischio |
| **Altezza struttura** (palo/edificio) | Dati tecnici | Cap. 15.1 Caduta dall'alto: quota = gravità |
| **Quota installazione antenne** | Configurazione radio | Quota lavoro in quota → tirante d'aria, DPI |
| **Numero settori e tecnologie** | Configurazione radio | N° antenne/parabole → durata fase, MMC |
| **Tipo di antenne** (panel, parabole MW) | Dettaglio componenti | Peso e dimensioni → modalità sollevamento |
| **Numero RRH** | Componenti outdoor | Peso unitario ≈ 8-15 kg → MMC |
| **Tipo cabinato/shelter** | Apparati outdoor | Peso, dimensioni → autogrù necessaria? |
| **Accesso al sito** | Note operative | Scala interna/esterna, botola, portone → rischio accesso |
| **Proprietà del sito** | Dati giuridici | Rawland (proprio) / Roof Top (condominio/privato) |
| **SRB esistenti di altri gestori** | Colocazione | CEM da impianti attivi durante lavori |
| **Coordinate GPS** | Geolocalizzazione | Verifica Google Maps/Earth per contesto |

**Azione**: Per ogni dato estratto, valuta l'impatto sui rischi e inseriscilo nella sezione PSC corrispondente.

---

### B.2 — Planimetria / Layout di Copertura o Area

| Elemento da analizzare | Rischio associato | Capitolo PSC |
|----------------------|-------------------|-------------|
| **Posizione SRB sulla copertura/area** | Distanza dal bordo → caduta dall'alto | Cap. 15.1 |
| **Percorso di accesso dal punto di ingresso alla postazione** | Lunghezza, ostacoli, dislivelli → inciampo, caduta | Cap. 7, 15.8 |
| **Distanza dal bordo copertura** (se Roof Top) | < 2 m dal bordo → zona rossa obbligatoria | Cap. 15.1, Cap. 12 |
| **Posizione quadro elettrico** | Distanza dagli apparati → lunghezza cavi, percorso | Cap. 15.3 |
| **Posizione punto di carico/scarico materiali** | Sotto la zona lavori? → caduta materiali | Cap. 15.2 |
| **Impianti di altri gestori in copertura** | Distanza → CEM durante lavori; interferenza fisica | Cap. 15.4, Cap. 9.4 |
| **Lucernari, aperture, abbaini** | Caduta attraverso copertura fragile | Cap. 15.1 (critico) |
| **Area disponibile per stoccaggio materiali** | Ingombro, spazi ristretti → MMC, urti | Cap. 9.3 |
| **Presenza di parapetti** (continui o discontinui) | Gap nei parapetti → caduta | Cap. 15.1 |
| **Linee vita esistenti** | Punti di ancoraggio disponibili → tipo DPI | Cap. 12 |
| **Orientamento dell'impianto** (azimut settori) | Direzione lavoro → esposizione vento/sole | Cap. 15.6 |
| **Zona fondazioni** (se Palo/Rawland) | Profondità scavo, tipo terreno → cedimento | Cap. 15.10 |

**Azione**: Sovrapponi mentalmente il flusso delle lavorazioni alla planimetria e identifica i punti critici di interferenza spaziale.

---

### B.3 — Order Form / Computo Metrico

| Dato da estrarre | Impatto sul PSC |
|-----------------|-----------------|
| **Importo lavori** | Cap. 20 Stima costi sicurezza (incidenza %) |
| **Elenco lavorazioni previste** | Cap. 16 Cronoprogramma + Cap. 18 Schede fase |
| **Voci di sicurezza (es. HAS001)** | Cap. 20 — confronto con stima analitica CSE |
| **Durata prevista** | Uomini/giorno → soglia Notifica Preliminare |
| **Tipo di struttura da installare** | Palo Fast Site / traliccio / solo antenne → profilo rischi diverso |
| **Necessità autogrù** | Cap. 15.2 (carichi sospesi), Cap. 11 (attrezzature) |
| **Scavi previsti** (fondazioni, cavidotti) | Cap. 15.10 (scavi) — profondità, armatura |

---

### B.4 — Tavole Strutturali / Relazione Geotecnica

| Elemento | Rischio | Capitolo PSC |
|----------|---------|-------------|
| **Profondità fondazioni** | > 1,5 m → armatura pareti scavo obbligatoria | Cap. 15.10 |
| **Tipo di terreno** (coeso/incoerente) | Scarpata sicura vs armatura → DPC diversi | Cap. 15.10, Cap. 8.1 |
| **Falda freatica** | Allagamento scavo → pompaggio, DPI | Cap. 8.1 |
| **Peso della struttura** (palo, carpenteria) | Portata autogrù necessaria → verifica certificato | Cap. 11, Cap. 15.2 |
| **Carichi in copertura** (se Roof Top) | Portata solaio vs peso impianto + operatori + attrezzature | Rischio cedimento strutturale |
| **Tipo di ancoraggio** (chimico, meccanico) | Tempo di presa → fase sequenziale obbligata | Cap. 16 cronoprogramma |

---

### B.5 — Relazione CEM / Parere ARPA

| Dato | Impatto sul PSC |
|------|-----------------|
| **Livelli CEM previsti a quota lavoro** | Cap. 15.4 — P e D calibrate su misura |
| **Raggio zona di rispetto** | Cap. 9.1 — recinzione/segnaletica da posizionare |
| **SRB adiacenti attive durante lavori** | CEM residuo → obbligo misura preventiva (art. 210) |
| **Potenza di emissione** | Discriminante per classificazione rischio CEM |

---

### B.6 — Relazione Paesaggistica / Autorizzazione

| Dato | Impatto sul PSC |
|------|-----------------|
| **Vincoli paesaggistici/monumentali** | Limitazioni su recinzione, ponteggi, PLE, colori |
| **Prescrizioni della Soprintendenza** | Modalità di accesso, orari, protezione superfici |
| **Zona sismica** | Classificazione → verifica strutturale fondazioni |
| **Zona alluvionale (PAI)** | Cap. 8.1 — rischio idrogeologico |

---

## C. Matrice posizionamento → profilo di rischio

Il posizionamento del sito determina il profilo di rischio dominante. Questa matrice collega il tipo di sito ai rischi principali che **devono** essere presenti nel PSC:

### C.1 — PALO / RAWLAND (suolo aperto)

| Rischio dominante | P | D | Note progettuali |
|-------------------|---|---|-----------------|
| Caduta dall'alto (15.1) | 3 | 3 | Quota = altezza palo (24-30 m). Tirante d'aria critico. |
| Caduta materiali (15.2) | 3 | 3 | Zona interdetta = raggio palo + 5 m |
| Scavi fondazioni (15.10) | 2 | 3 | Profondità da relazione geotecnica. Armatura se > 1,5 m |
| Ribaltamento autogrù (aggiuntivo) | 2 | 3 | Verifica portanza terreno per stabilizzatori |
| Carichi sospesi (15.2b) | 3 | 3 | Palo + carpenterie sollevate con autogrù |
| Elettrocuzione (15.3) | 2 | 3 | Collegamento rete elettrica |
| CEM (15.4) | 1 | 2 | New Site: non attivo durante installazione. Se upgrade: misura |

### C.2 — ROOF TOP (copertura edificio esistente)

| Rischio dominante | P | D | Note progettuali |
|-------------------|---|---|-----------------|
| Caduta dall'alto dal bordo (15.1) | 3 | 3 | Distanza postazione-bordo dalla planimetria. Parapetti? |
| Caduta attraverso copertura fragile (15.1b) | 3 | 3 | Solo se fibrocemento/ondulato/lucernari |
| Caduta nel vano scala (15.1c) | 2 | 3 | Botola senza parapetto, scala alla marinara |
| Caduta materiali su area pubblica (15.2) | 3 | 3 | Se edificio su strada/piazza → mantovana obbligatoria |
| Accesso (15.8) | 2 | 2 | Scala interna stretta, chiavi, portone condominiale |
| MMC su scale (15.5) | 2 | 2 | Trasporto materiali a mano se no ascensore/montacarichi |
| CEM da colocati (15.4) | 2 | 2 | Impianti altri gestori attivi → misura preventiva |
| Cedimento strutturale (aggiuntivo) | 1 | 3 | Verifica portata solaio se carico concentrato |

### C.3 — LATTICE / TRALICCIO

| Rischio dominante | P | D | Note progettuali |
|-------------------|---|---|-----------------|
| Caduta dall'alto (15.1) | 3 | 3 | Altezza traliccio (30-50 m). Progressione verticale. |
| Caduta materiali (15.2) | 3 | 3 | Zona interdetta ampia |
| CEM da colocati (15.4) | 3 | 2 | Traliccio spesso multigestore → più SRB attive |
| Folgorazione da scariche atmosferiche | 2 | 3 | Struttura metallica alta → LPS obbligatorio |
| Microclima (15.6) | 2 | 2 | Esposizione vento a quota elevata |

### C.4 — INDOOR / GROUND BASED

| Rischio dominante | P | D | Note progettuali |
|-------------------|---|---|-----------------|
| Elettrocuzione (15.3) | 2 | 3 | Lavori su quadri e cablaggio in locale tecnico |
| Spazi confinati (se locale interrato) | 2 | 3 | Ventilazione, rilevatore gas |
| MMC (15.5) | 2 | 2 | Trasporto apparati in spazi ristretti |
| CEM (15.4) | 1-2 | 2 | Se impianti attivi nel locale → misura |

---

## D. Procedura di analisi del progetto esecutivo

### D.1 — Raccolta documenti

Chiedi all'utente (o verifica se ha già fornito):
1. Scheda Radio / Scheda Tecnica Sito (obbligatorio per K2A TLC)
2. Planimetria copertura/area con posizione SRB (molto importante)
3. Order Form o computo metrico (importante per costi e lavorazioni)
4. Tavole strutturali / relazione geotecnica (se disponibili — critica per scavi)
5. Relazione CEM / parere ARPA (se disponibile)
6. Foto del sito (vedi `references/analisi-foto-rischi.md`)

### D.2 — Analisi sistematica

Per ogni documento ricevuto:

1. **Estrai i dati** secondo le tabelle B.1–B.6
2. **Identifica il tipo di sito** → seleziona il profilo di rischio dalla matrice C
3. **Sovrapponi progetto e rischi**: per ogni lavorazione prevista nel progetto, valuta:
   - A che quota si lavora?
   - Con quali attrezzature?
   - Quanto pesano i componenti?
   - Dove si posizionano rispetto al bordo/alla zona pubblica?
   - Ci sono impianti attivi nelle vicinanze?
4. **Calibra P e D** sulla base dei dati progettuali reali, non su valori generici
5. **Produci il report** con il formato della sezione E

### D.3 — Integrazione nel PSC

I risultati dell'analisi del progetto confluiscono in:

| Sezione PSC | Cosa inserire |
|------------|--------------|
| Cap. 2 (Anagrafica) | Dati sito dalla Scheda Radio |
| Cap. 6 (Descrizione opera) | Descrizione intervento dal progetto esecutivo; clausola informazioni committente |
| Cap. 7 (Area di lavoro) | Caratteristiche area dal progetto + planimetria |
| Cap. 8 (Rischi intrinseci) | Fattori esterni rilevati da planimetria e contesto |
| Cap. 9 (Organizzazione) | Layout cantiere coerente con planimetria |
| Cap. 11 (Attrezzature) | Macchine necessarie per le lavorazioni previste |
| Cap. 15 (Rischi) | P e D calibrate su dati progettuali; garanti per R ≥ 6 |
| Cap. 16 (Cronoprogramma) | Fasi da order form / computo metrico |
| Cap. 18 (Schede lavorazioni) | Una scheda per ogni lavorazione prevista nel progetto |
| Cap. 20 (Costi sicurezza) | Stima analitica basata su lavorazioni reali |

---

## E. Formato del report di analisi progettuale

Per ogni documento analizzato, produci una sintesi nel formato seguente:

```
📐 ANALISI PROGETTO — [TIPO_DOCUMENTO]
Sito: [CODICE_SITO] [NOME_SITO]
Tipo: [TIPO_SITO] — [TIPO_INTERVENTO]

DATI CHIAVE ESTRATTI:
- Quota lavoro: [QUOTA] m
- Struttura: [TIPO_STRUTTURA] h=[ALTEZZA] m
- N° antenne: [N] × [TIPO] a quota [Q] m — peso unitario ≈ [P] kg
- N° parabole: [N] × Ø [D] cm a quota [Q] m
- N° RRH: [N] — peso unitario ≈ [P] kg
- Accesso: [DESCRIZIONE_ACCESSO]
- Impianti colocati: [SÌ/NO — dettaglio]

RISCHI SPECIFICI DERIVANTI DAL PROGETTO:
1. [Rischio] → P=[X] D=[X] R=[X] — Motivazione dal dato progettuale
2. [Rischio] → P=[X] D=[X] R=[X] — Motivazione dal dato progettuale
3. ...

LAVORAZIONI PREVISTE (per cronoprogramma):
1. [Fase] — durata stimata [GG] gg — [N] operatori
2. [Fase] — durata stimata [GG] gg — [N] operatori
3. ...

ATTREZZATURE NECESSARIE:
- [Attrezzatura] — motivazione
- ...

VERIFICHE DA RICHIEDERE (dati mancanti):
- [Dato mancante] — a chi richiederlo
- ...
```

---

## F. Sinergia con analisi fotografica

L'analisi del progetto esecutivo e l'analisi fotografica sono **complementari**:

| Aspetto | Progetto esecutivo | Foto del sito |
|---------|-------------------|---------------|
| Quota di lavoro | Dato esatto dalla scheda radio | Stima visiva approssimata |
| Parapetti | Indicati/non indicati in planimetria | Stato reale visibile (altezza, integrità, gap) |
| Sottoservizi | Indicati nelle tavole | Chiusini e pozzetti visibili a terra |
| Accesso | Descritto nelle note operative | Condizioni reali (fango, pendenza, larghezza) |
| SRB esistenti | Colocazione indicata nella scheda radio | Visibili nelle foto (tipo, posizione, stato) |
| Terreno | Relazione geotecnica (se disponibile) | Tipo apparente (argilla, sabbia, roccia) |

**Regola**: quando sia il progetto che le foto sono disponibili, i dati progettuali forniscono i valori esatti (quote, pesi, dimensioni), mentre le foto forniscono le condizioni reali (stato conservativo, ostacoli, contesto). In caso di discrepanza, segnalare nel PSC e prescrivere verifica in sopralluogo.
