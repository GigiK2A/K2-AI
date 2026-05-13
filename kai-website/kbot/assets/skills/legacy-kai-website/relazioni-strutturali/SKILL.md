---
name: relazioni-strutturali
description: >
  Skill per la redazione delle relazioni strutturali del PE iliad: calcolo palo, fondazione,
  verifica strutture esistenti, relazione geotecnica e geologica. Usa SEMPRE questa skill
  quando l'utente dice "relazione calcolo palo iliad", "relazione fondazione iliad",
  "verifica palo esistente iliad", "asseverazione palo", "verifica statica fondazione iliad",
  "verifica idoneità statica iliad", "contenuti minimi verifica statica", "Form VS iliad",
  "relazione geotecnica sito iliad", "relazione geologica sito iliad", "calcolo strutturale PE",
  "sfruttamenti struttura", "marginalità 15-20%", "unifilare struttura palo", "piano
  manutenzione palo", "tabella sfruttamenti fondazione", "verifica capacità portante plinto",
  "idoneità strutturale palo", "carichi vento antenne iliad", "verifica ancoraggi rooftop",
  "verifiche elementi non strutturali", "validazione risultati NTC 2018".
metadata:
  version: "0.2.0"
  author: "Luca Rossi"
  riferimento: "Linea Guida PE iliad v.1.1; Linee Guida Verifiche Statiche iliad v.1.4; NTC 2018"
---

# Relazioni Strutturali — PE iliad

Questa skill guida la redazione delle relazioni strutturali richieste dal PE iliad, differenziate per tipologia di sito.

## Struttura Standard della Verifica di Idoneità Statica (LG VS v1.4)

La "Linea Guida Verifiche di Idoneità Statica — Contenuti Minimi" iliad v1.4 (aggiornata 06/2024) definisce la struttura obbligatoria per tutte le relazioni strutturali su strutture esistenti (TC-RL, TC-RT) **e** per le relazioni di calcolo su strutture nuove. Ogni relazione deve seguire questa struttura in 16 capitoli + allegati:

| Cap. | Titolo | Note |
|------|--------|------|
| 1 | Descrizione dell'opera e della tipologia strutturale | Tipologia (palo flangiato/poligonale/rooftop/traliccio/strallato), proprietario, motivo della verifica; per RT: schema strutturale edificio ospite; schema caratteristiche geometriche (tronchi, n. lati, diametri, spessori, dimensioni bulloni) + fotodoc stato di fatto |
| 2 | Inquadramento normativo | Vedere normative obbligatorie in `references/struttura-vs-iliad.md` |
| 3 | Documentazione esistente della struttura | Elenco documenti (VS precedenti, RSU, collaudi, rilievi) con committente, professionista, data; se assenti: piano di indagini per caratterizzazione |
| 4 | Materiali e caratteristiche meccaniche | Qualità acciaio, risultati prove/certificati, cls fondazione |
| 5 | Parametri di progetto e geometria | Zona vento, zona sismica, classe rugosità, parametri sito |
| 6 | Analisi dei carichi | 6.1 Permanenti; 6.2 Semi-permanenti; 6.3 Accidentali; 6.4 Azione del vento (Cap. 3.3 NTC 2018) con carichi concentrati e distribuiti; 6.5 Azione del sisma |
| 7 | Combinazioni di carico | SLU, SLE, combinazioni fondamentale/eccezionale/sismica |
| 8 | Metodo di calcolo e modello di schematizzazione | Software usato, modello FEM o analitico, ipotesi di calcolo |
| 9 | Codice di calcolo utilizzato | Nome software, versione, certificazione |
| 10 | Tabelle sintetiche delle verifiche di resistenza | **Tabella sfruttamenti** per tutte le verifiche SLU con marginalità ≥ 15-20% |
| 11 | Strutture RawLand — Verifiche della fondazione | Solo NS-RL e TC-RL |
| 12 | Strutture RoofTop — Verifica ancoraggi | Solo NS-RT e TC-RT: verifica bulloni/resine di ancoraggio baggioli |
| 13 | Verifiche elementi non strutturali | Sbracci, flange, bullonerie, saldature |
| 14 | Conclusioni | Giudizio di idoneità esplicito (IDONEO / IDONEO CON PRESCRIZIONI / NON IDONEO) |
| 15 | Validazione dei risultati (Cap. 10 NTC 2018) | Verifica indipendente o con metodo alternativo |
| 16 | Allegati | Estratti calcolo, schede tecniche, certificati materiali |
| App. A | Appendice A | Documentazione fotografica stato di fatto |
| App. B | Appendice B | Appendice tecnica integrativa |

> **Riferimento Form VS**: Per la compilazione standardizzata utilizzare il `Form VS.xlsm` disponibile nella cartella `03 - Opere Civili/03 - Verifiche Statiche/`.

---

## Relazioni Strutturali per Tipologia

| Relazione | NS-RL | NS-RT | TC-RL | TC-RT |
|-----------|:-----:|:-----:|:-----:|:-----:|
| Calcolo Palo (nuova struttura) | ✓ | ✓ | — | — |
| Verifica/Asseverazione Palo Esistente | — | — | ✓ | ✓ |
| Calcolo Fondazione (nuovo plinto) | ✓ | — | — | — |
| Verifica Fondazione Esistente | — | — | ✓ | — |
| Relazione Geotecnica | ✓ | — | ✓ | — |
| Relazione Geologica | ✓ | — | se nec. | — |

---

## 1. Relazione di Calcolo del Palo (NS-RL, NS-RT)

### Struttura della Relazione

**1.1 Normativa di riferimento**
- D.M. 17/01/2018 — NTC 2018
- Circolare applicativa NTC 2018 (C.S.LL.PP. n. 7/2019)
- CNR-DT 207/2008 — Azioni del vento
- EN 1993 — Eurocodice 3 (acciaio)
- EN 50341 — Linee elettriche aeree (per riferimento carichi antenne)

**1.2 Descrizione struttura**
- Tipologia palo (poligonale, tubolare, traliccio)
- Altezza totale fuori terra [m]
- Numero di tronchi e altezze di giunzione
- Diametro e spessore tronco superiore e inferiore
- Qualità acciaio (tipicamente S355J0 o S355JR per pali zincati)
- Tipo di flangia di giunzione
- Trattamento superficiale (zincatura a caldo EN ISO 1461)

**1.3 Carichi agenti**
- Zona di vento (da NTC 2018 in base al Comune)
- Classe di rugosità del terreno
- Velocità di riferimento del vento Vb [m/s]
- Pressione cinetica di riferimento qb [N/m²]
- Carichi antenne (area equivalente esposta al vento SEV per ogni antenna)
- Carichi apparati in quota (area SEV)
- Peso proprio palo e apparati

**1.4 Analisi strutturale**
- Modello di calcolo (travata a mensola incastrata alla base)
- Azioni di calcolo (SLU — Stato Limite Ultimo)
- Combinazioni di carico (art. 2.5.3 NTC 2018)
- Risultati: momento flettente alla base Md, taglio Vd, azione assiale Nd

**1.5 Verifiche SLU — Tabella Sfruttamenti**

| Verifica | Sezione | Valore calc. | Valore amm. | Sfruttamento [%] | OK |
|----------|---------|:---:|:---:|:---:|:---:|
| Flessione composta | Base | | | | |
| Taglio | Base | | | | |
| Deformazione (freccia in sommità) | Sommità | | | | |
| Flangia di giunzione | Giunzione | | | | |
| Bulloni flangia | Giunzione | | | | |
| Piastra di base | Base | | | | |
| Tirafondi/fondazione | Interfaccia | | | | |

> **REGOLA ILIAD**: Sfruttamenti ≤ 80-85% (marginalità residua ≥ 15-20%).
> Segnalare in rosso qualsiasi sfruttamento > 85%.

**1.6 Allegati obbligatori**
- Tabella riassuntiva sfruttamenti (come sopra)
- **Piano di Manutenzione** (verifica bulloni flangia, ispezione corrosione, periodicità)
- **Unifilare della struttura** (schema grafico quotato con: altezze di giunzione, posizione antenne, posizione apparati, codici componenti)

---

## 2. Verifica / Asseverazione Palo Esistente (TC-RL, TC-RT)

### Struttura della Relazione

**2.1 Rilievo struttura esistente**
- Dati identificativi (produttore se noto, anno installazione se noto)
- Tipologia palo (poligonale, tubolare, ecc.)
- Altezza totale fuori terra (misurata)
- Diametri e spessori (misurati, con indicazione metodo di misurazione)
- Stato di conservazione: valutazione visiva e/o con prove (classificare: BUONO / DISCRETO / SCADENTE)
- Eventuali anomalie (corrosione, deformazioni, crepe nelle saldature, ecc.)
- Carichi radio attualmente installati (carichi esistenti da mantenere)

**2.2 Nuovi carichi da iliad**
- Antenne e apparati iliad da installare
- Area equivalente esposta al vento (SEV) di ogni nuovo elemento
- Peso di ogni nuovo elemento
- Quote di installazione

**2.3 Verifica strutturale**
Stessa metodologia del punto 1, applicata alla struttura esistente con carichi totali (esistenti + nuovi iliad).

**2.4 Confronto carichi esistenti vs nuovo stato**

| Parametro | Stato attuale | Stato futuro (+ iliad) | Variazione [%] |
|-----------|:---:|:---:|:---:|
| Momento alla base Md [kNm] | | | |
| Taglio alla base Vd [kN] | | | |
| Sfruttamento massimo [%] | | | |

**2.5 Giudizio di Idoneità**

Il giudizio deve essere espresso esplicitamente in una delle tre forme:

- ✅ **IDONEO**: La struttura è adeguata a sostenere i nuovi carichi iliad con marginalità ≥ 15-20%. Non sono necessari interventi strutturali.

- ⚠️ **IDONEO CON PRESCRIZIONI**: La struttura è adeguata con le seguenti prescrizioni: [elenco prescrizioni operative o installative].

- ❌ **NON IDONEO**: La struttura non è adeguata. Motivazione: [carichi eccessivi / stato di conservazione scadente / sfruttamento > 100%]. Azioni richieste: [sostituzione palo / rinforzo strutturale / riduzione carichi].

**2.6 Firma e asseverazione**
La relazione deve essere firmata e asseverata da Ingegnere Strutturista iscritto all'Ordine.

---

## 3. Relazione di Calcolo delle Fondazioni (NS-RL)

### Struttura della Relazione

**3.1 Normativa di riferimento**
- NTC 2018 Cap. 6 (Progettazione Geotecnica)
- Circolare NTC 2018 Cap. C6

**3.2 Dati geotecnici**
- Stratigrafia dal sondaggio geotecnico (o da dati bibliografici per siti noti)
- Parametri geotecnici strati principali (γ, c', φ', cu)
- Falda freatica (assenza o profondità)

**3.3 Geometria fondazione**
- Tipo di fondazione (plinto a pianta quadrata/circolare)
- Dimensioni (L × B × H per plinto, φ per plinto circolare)
- Profondità di posa rispetto al piano campagna

**3.4 Azioni di calcolo alla base del palo**
- Md (momento flettente) [kNm]
- Vd (taglio) [kN]
- Nd (azione assiale) [kN]
Derivate dalla relazione di calcolo del palo.

**3.5 Verifiche SLU fondazione**

| Verifica | Valore calc. | Valore amm. | Sfruttamento [%] |
|----------|:---:|:---:|:---:|
| Capacità portante terreno (GEO) | | | |
| Scorrimento (GEO) | | | |
| Ribaltamento (EQU) | | | |
| Pressoflessione cls plinto (STR) | | | |
| Punzonamento | | | |
| Taglio plinto (senza arm. trasversale) | | | |
| Tirafondi a trazione | | | |
| Ancoraggio tirafondi nel cls | | | |

> **REGOLA ILIAD**: Mantenere marginalità **15-20%** (sfruttamento ≤ 80-85%) per tutte le verifiche principali.

**3.6 Armatura plinto**
- Armatura inferiore: diametro × numero barre in entrambe le direzioni
- Armatura superiore (se necessaria)
- Staffe (se presenti)
- Copriferro (min. 40 mm per fondazione)
- Classe calcestruzzo (C25/30 minimo, classe esposizione XC2)

---

## 4. Verifica Statica Fondazione Esistente (TC-RL)

Struttura analoga alla relazione di calcolo (punto 3), con le seguenti differenze:

- **Rilievo fondazione esistente**: dimensioni da rilievo o da documentazione originale
- **Carico attuale**: carichi degli operatori già presenti
- **Nuovo carico iliad**: carico addizionale da integrare
- **Verifica incremento di carico**: confronto sfruttamenti prima e dopo l'installazione iliad
- **Giudizio di idoneità**: IDONEA / IDONEA CON PRESCRIZIONI / NON IDONEA (con motivazione)
- **In caso di Non Idoneità**: proposta di rinforzo (cordolo ampliamento plinto)

---

## 5. Relazione Geotecnica (NS-RL, TC-RL)

Struttura minima:
- Inquadramento geografico e geologico dell'area
- Descrizione delle indagini eseguite (sondaggi, prove SPT, prove CPT, ecc.)
- Stratigrafia del sottosuolo con descrizione litologica di ogni strato
- Parametri geotecnici di progetto per ogni strato
- Livello di falda
- Valutazione capacità portante del terreno di posa (Rd per combinazione EQU, GEO)
- Indicazioni per il dimensionamento della fondazione

---

## 6. Relazione Geologica (NS-RL, TC-RL se necessario)

Struttura minima:
- Inquadramento geologico regionale
- Litologia e assetto strutturale locale
- Geomorfologia dell'area
- Idrogeologia
- Valutazione sismicità (zona sismica, ag, F0, TC*)
- Eventuale microzonazione sismica
- Conclusioni e indicazioni per la progettazione

---

## Attivare Skill Complementari

- **progettista-strutturale** — per i calcoli strutturali dettagliati (NTC 2018, EC2, EC3, verifica acciaio, cemento armato, fondazioni)
- **cellnex-progettazione-esecutiva:verifica-strutture-esistenti** — per confronto con metodologia Cellnex su pali esistenti
- **cellnex-progettazione-esecutiva:rinforzi-pali** — per interventi di rinforzo strutturale
