---
name: credito-rd-innovazione
description: >-
  Skill foglia AgevolazioniBoost per i tax credit R&S, Innovazione Tecnologica, Design e Ideazione
  Estetica previsti dalla L. 160/2019 (art. 1 cc. 198-209) e successive modifiche. Guida operativa
  alla classificazione corretta delle attività (R&S vs Innovazione vs Design vs routine), al calcolo
  delle aliquote applicabili, alla costruzione della documentazione probatoria (quaderno di
  laboratorio, perizia asseverata, lettere di incarico), alla cumulabilità con Patent Box e
  all'utilizzo in compensazione F24. Include schema decisionale a 5 domande, 10 esempi concreti di
  classificazione, tabelle riepilogative delle aliquote, checklist pre-utilizzo a 15 punti e
  mappatura dei 5 principali rischi di contestazione fiscale con relative misure preventive.
  Output strutturato JSON per orchestratore con stima del beneficio, flag documentazione e
  indicazione sulla necessità di consulente specializzato.
---








<!-- LEGAL-EVIDENCE-BLOCK-V7 -->
## Tools Normattiva + Giurisprudenza (CCost + CGUE + CEDU + CdS/TAR + Cassazione) — verifica obbligatoria

Hai 5 toolkit locali + 1 lookup live per consulenza legale evidence-based:
- **Normattiva** — ~42.000 norme italiane (DB FTS5)
- **Corte Costituzionale** — 22.258 pronunce + 46.154 massime (1956→2026)
- **Corte di Giustizia UE + Tribunale UE** — ~38.000 cause (2005→2026)
- **Corte EDU (Strasburgo)** — 10.000 casi contro l'Italia (2001→2026), con traduzioni ufficiali Min. Giustizia
- **Giustizia Amministrativa** — Consiglio di Stato + TAR + CGARS (2024→2025, in espansione)
- **Cassazione (LIVE pubblica)** — SentenzeWeb italgiure, accesso pubblico zero-setup (~188k civ + ~236k pen, testo integrale)

### Workflow obbligatorio

**A. Norme italiane**
```bash
python3 ~/normattiva_ai/tools/cita.py "<es. D.Lgs 81/2008>"
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --materia tributario --limit 5
```

**B. Corte Costituzionale**
```bash
python3 ~/giurisprudenza_ai/tools/cross_norma_sentenza.py "art. 32 Cost." --limit 10
python3 ~/giurisprudenza_ai/tools/rag_giurisprudenza.py "<query>" --anno-da 2018
python3 ~/giurisprudenza_ai/tools/cita_sentenza.py "Corte cost. N/AAAA"
```

**C. CGUE (diritto UE / GDPR / appalti / antitrust / privacy / dogana)**
```bash
python3 ~/cgue_ai/tools/cross_norma_cgue.py "art. 101 TFUE" --limit 10
python3 ~/cgue_ai/tools/cross_norma_cgue.py "Reg. UE 679/2016"        # GDPR
python3 ~/cgue_ai/tools/rag_cgue.py "<query>" --anno-da 2018
python3 ~/cgue_ai/tools/cita_cgue.py "C-16/05"
```

**D. CEDU (diritti fondamentali / equo processo art. 6 / detenzione art. 3 / proprietà P1-1 / vita privata art. 8)**
```bash
python3 ~/cedu_ai/tools/cross_articolo_cedu.py "art. 6" --solo-importanti --limit 10
python3 ~/cedu_ai/tools/rag_cedu.py "<query>" --anno-da 2015
python3 ~/cedu_ai/tools/cita_cedu.py "63386/16"      # numero di ricorso
```

**E. Giustizia Amministrativa — CdS/TAR (appalti, edilizia, accesso atti, SCIA, silenzio, espropri, PA)**
```bash
python3 ~/gad_ai/tools/cross_norma_gad.py "D.Lgs 36/2023" --limit 10   # appalti
python3 ~/gad_ai/tools/cross_norma_gad.py "Legge 241/1990"             # procedimento
python3 ~/gad_ai/tools/rag_gad.py "<query>" --sede cds --anno-da 2024
```

**F. Cassazione (LIVE pubblica — civile/penale, legittimità) — zero setup**
```bash
# Verifica/recupera un precedente di Cassazione (SentenzeWeb pubblico, nessun login)
python3 ~/cassazione_ai/tools/cassazione_lookup.py --cit "Cass. civ. 12345/2023"
python3 ~/cassazione_ai/tools/cassazione_lookup.py --q "licenziamento giusta causa" --sezione civ --rows 5
python3 ~/cassazione_ai/tools/cassazione_lookup.py --cit "Cass. civ. 12345/2023" --full   # testo integrale
python3 ~/cassazione_ai/tools/check_cassazione.py --file <output.md>                        # verifica citazioni
```
Copre la finestra pubblica (~ultimi 5 anni + storico parziale). Se una citazione MANCA può essere fuori finestra; dillo, non inventare la massima.

**G. Verifica finale (prima del deliverable, su ogni file MD prodotto)**
```bash
python3 ~/normattiva_ai/tools/check_citazioni.py --file <output.md> --strict
python3 ~/giurisprudenza_ai/tools/check_sentenze.py --file <output.md> --strict
python3 ~/cgue_ai/tools/check_cgue.py --file <output.md> --strict
python3 ~/cedu_ai/tools/check_cedu.py --file <output.md> --strict
python3 ~/gad_ai/tools/check_gad.py --file <output.md> --strict
```

Knowledge pack norme: `~/normattiva_ai/knowledge_packs/tributario/`

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# Skill — Credito d'Imposta R&S, Innovazione Tecnologica, Design

## Identità e scopo

Skill foglia AgevolazioniBoost per i tax credit R&S, Innovazione Tecnologica, Design e Ideazione
Estetica (L. 160/2019, art. 1 cc. 198-209 e successive modifiche). Uno degli strumenti più
sottoutilizzati perché le PMI non sanno di averne diritto, e uno dei più rischiosi se mal
documentato. Questa skill guida l'utente nella classificazione delle attività, nel calcolo del
beneficio, nella costruzione del fascicolo documentale e nella gestione dei rischi di
contestazione.

---

## Sezione 1 — I 4 tipi di attività e le loro aliquote

### La distinzione critica

La classificazione corretta dell'attività determina l'aliquota applicabile. Classificare male
significa rischiare un recupero a tassazione piena, più sanzioni e interessi.

---

### 1. Ricerca e Sviluppo (R&S)

**Definizione tecnica** (dal Manuale di Frascati OCSE, recepito dalla normativa italiana):
- **Ricerca fondamentale**: lavoro teorico o sperimentale volto all'acquisizione di nuove
  conoscenze sui fondamenti di fenomeni e fatti osservabili, senza applicazione immediata.
- **Ricerca industriale**: ricerca pianificata volta ad acquisire nuove conoscenze da utilizzare per
  sviluppare nuovi prodotti/processi/servizi o migliorare quelli esistenti.
- **Sviluppo sperimentale**: acquisizione, combinazione, strutturazione e utilizzo di conoscenze
  esistenti per produrre piani e progetti di nuovi prodotti/processi/servizi.

**Caratteristica discriminante**: deve esistere **incertezza scientifica o tecnologica** sull'esito.
Il processo deve avanzare la frontiera della conoscenza dell'impresa (non solo del mercato).
Si documentano i tentativi falliti — la fallibilità è prova di R&S genuina.

**Aliquota base**: 10% delle spese ammissibili
**Aliquota Mezzogiorno**: maggiorata per imprese nelle regioni del Sud (verificare decreto
attuativo vigente — storicamente 25% per grandi imprese, 35% per medie, 45% per piccole nelle ZES)

---

### 2. Innovazione Tecnologica

**Definizione**: attività finalizzate alla realizzazione di prodotti o processi di produzione
**nuovi o sostanzialmente migliorati** rispetto a quelli già realizzati o applicati dall'impresa.
Non è richiesta la novità per il mercato — è sufficiente la novità per l'impresa.
Si applica tecnologia esistente e nota, combinandola o adattandola a nuovi scopi.

**Aliquota base**: 5% delle spese ammissibili
**Aliquota maggiorata (10%)**: per attività di innovazione tecnologica finalizzate alla
**transizione ecologica** (riduzione emissioni, efficienza energetica, economia circolare) o alla
**transizione digitale** (Industry 4.0, intelligenza artificiale, blockchain, IoT industriale).
Condizione: l'impresa deve dimostrare che l'innovazione ha come obiettivo principale la
transizione — non è sufficiente un impatto marginale.

> **Attenzione**: non confondere con Transizione 5.0 (credito d'imposta investimenti in beni
> strumentali 4.0/5.0, disciplina separata). Il credito innovazione tecnologica si riferisce alle
> attività di ricerca e sviluppo interne, non all'acquisto dei macchinari.

---

### 3. Design e Ideazione Estetica

**Definizione**: attività di design industriale e ideazione estetica per nuove collezioni,
prodotti o campionari, finalizzate a migliorare l'immagine estetica e funzionale dei prodotti.

**Settori applicabili** (tassativi):
- Tessile e moda
- Abbigliamento e calzature
- Occhialeria
- Oreficeria e gioielleria
- Ceramica e porcellana
- Arredamento e design d'interni

**Aliquota**: 5% delle spese ammissibili (verificare aggiornamenti normativi annuali)

---

### 4. Transizione ecologica e digitale — Riepilogo condizioni aliquota maggiorata

Per accedere all'aliquota del 10% nell'innovazione tecnologica occorre:
1. Attività classificabile come Innovazione Tecnologica (non R&S, non design)
2. Obiettivo principale: transizione ecologica OPPURE transizione digitale
3. Documentazione specifica dell'obiettivo di transizione nel project notebook
4. Per transizione ecologica: KPI ambientali misurabili (es. riduzione CO2, consumo energetico)
5. Per transizione digitale: implementazione di tecnologie 4.0/digitali certificate

---

### Tabella riepilogativa aliquote

| Tipo attività               | Aliquota base | Aliquota maggiorata        | Spesa massima annua |
|-----------------------------|---------------|----------------------------|---------------------|
| R&S                         | 10%           | Fino a 45% (Mezzogiorno)   | 20.000.000 EUR      |
| Innovazione Tecnologica     | 5%            | 10% (eco/digitale)         | 2.000.000 EUR       |
| Design e Ideazione Estetica | 5%            | —                          | 2.000.000 EUR       |
| Transizione ecologica/dig.  | 10%           | —                          | 2.000.000 EUR       |

> Nota: i massimali e le aliquote sono soggetti a variazioni con leggi di bilancio annuali.
> Verificare sempre la normativa vigente per il periodo di imposta in esame.

---

## Sezione 2 — Spese ammissibili per tipo

### R&S — Spese ammissibili

| Categoria di spesa                    | Note operative                                                              |
|---------------------------------------|-----------------------------------------------------------------------------|
| Personale ricercatore e tecnico       | Solo personale con ruolo R&S esplicito; inclusi dottorandi e collaboratori  |
| Quote ammortamento strumentazione     | Pro-quota uso effettivo per R&S; non l'intero ammortamento                  |
| Contratti ricerca con università/enti | Contratti con enti pubblici o privati accreditati                           |
| Contratti ricerca con altre imprese   | Imprese non controllate/collegate; documentare contenuto                    |
| Brevetti e know-how acquisiti         | Ammortamento e canoni di licenza su IP utilizzato                           |
| Consulenze tecniche e perizie         | Specialisti qualificati con contratto specifico                             |
| Materiali di consumo per prove        | Solo se direttamente imputati al progetto R&S                               |

### Innovazione Tecnologica e Design — Spese ammissibili

| Categoria di spesa             | Note operative                                         |
|--------------------------------|--------------------------------------------------------|
| Personale tecnico              | Direttamente impiegato nelle attività di innovazione   |
| Materiali e forniture          | Campioni, prototipi, materiali di test                 |
| Contratti di innovazione       | Con soggetti terzi qualificati                         |
| Software dedicato              | Licenze specifiche per il progetto di innovazione      |
| Consulenze specializzate       | Con documentazione del contributo specifico            |

### Cosa NON è ammissibile (in tutte le categorie)

- Costi generali e overhead non direttamente imputabili
- Attività di routine: controllo qualità ordinario, manutenzione ordinaria, aggiornamenti
  software standard, attività di supporto non tecnico
- Test standard pre-produzione senza finalità innovativa
- Studi di mercato, analisi commerciali, attività promozionali
- Formazione generica del personale
- Costi di produzione in serie (anche se relativi a prodotti nuovi)

---

## Sezione 3 — Il problema della distinzione: R&S vs Innovazione vs Routine

### La trappola principale

L'AdE nelle istruttorie tende a riclassificare le attività verso la categoria con aliquota
inferiore (o verso la routine, esclusa del tutto). Il contribuente ha l'onere di provare la
classificazione superiore.

---

### Schema decisionale — 5 domande per classificare un'attività

```
DOMANDA 1: L'attività risolve un'incertezza scientifica o tecnologica
           il cui esito non è prevedibile con le conoscenze disponibili?

   SI  → Probabile R&S → vai a D2
   NO  → vai a D3

DOMANDA 2: L'incertezza riguarda principi scientifici o leggi fisiche/chimiche/biologiche
           (non solo preferenze di mercato o fattibilità commerciale)?

   SI  → R&S confermata
   NO  → Rivalutare: forse è innovazione con incertezza tecnica → vai a D3

DOMANDA 3: L'attività porta a un prodotto, processo o servizio
           nuovo o sostanzialmente migliorato RISPETTO A QUANTO GIA' FA L'IMPRESA?

   SI  → Innovazione Tecnologica → vai a D4
   NO  → Attività di routine (non agevolabile)

DOMANDA 4: L'obiettivo principale è ridurre impatti ambientali
           o implementare tecnologie digitali/Industry 4.0?

   SI  → Innovazione con aliquota maggiorata (10%)
   NO  → Innovazione standard (5%)

DOMANDA 5 (solo per settori specifici): L'attività riguarda design estetico
           per nuove collezioni nei settori tessile/moda/calzature/occhialeria/orafo/ceramica/arredo?

   SI  → Design e Ideazione Estetica (5%)
   NO  → Applicare classificazione da D3/D4
```

---

### 10 esempi concreti con classificazione corretta

**Esempio 1** — "Abbiamo migliorato il nostro processo produttivo"
- Classificazione: dipende. Se si è applicata tecnologia già nota per ottimizzare un processo
  esistente → **Innovazione Tecnologica (5%)**. Se il processo era già ottimizzato e si trattava
  di aggiustamenti ordinari → **Routine (non agevolabile)**.
- Segnale discriminante: esisteva un benchmark di processo da battere? C'era incertezza
  sull'esito del miglioramento?

**Esempio 2** — "Stiamo sviluppando un nuovo algoritmo di machine learning"
- Classificazione: se l'algoritmo usa tecniche note applicate a un nuovo dominio →
  **Innovazione Tecnologica (5%)**. Se l'algoritmo risolve un problema matematico o di
  apprendimento non ancora risolto in letteratura → **R&S (10%)**.
- Segnale discriminante: esiste pubblicazione scientifica sul problema? L'esito era
  prevedibile con le conoscenze disponibili?

**Esempio 3** — "Proviamo nuovi materiali nel nostro prodotto"
- Classificazione: dipende dalla novità scientifica. Se si combinano materiali noti in modo
  noto → **Routine**. Se si testa una combinazione non documentata con esito incerto →
  **R&S**. Se si applica un materiale noto a un nuovo uso industriale → **Innovazione (5%)**.

**Esempio 4** — "Abbiamo sviluppato una nuova collezione moda con nuovi tessuti"
- Classificazione: se l'impresa è nel settore tessile e il lavoro riguarda l'ideazione estetica
  della collezione → **Design e Ideazione Estetica (5%)**. Se si è anche sviluppato un nuovo
  processo di lavorazione del tessuto → si può avere doppia classificazione per parti distinte.

**Esempio 5** — "Abbiamo installato un sistema IoT per monitorare la produzione"
- Classificazione: l'installazione di sistemi noti non è R&S. Se l'adattamento all'impianto
  ha richiesto sviluppo software custom significativo → **Innovazione digitale (10%)**. Se è
  stato tutto configurazione standard → **non agevolabile**.

**Esempio 6** — "Stiamo testando una nuova formula chimica"
- Classificazione: se la formula è nuova per la scienza → **R&S (10%)**. Se la formula è
  nota ma nuova per l'impresa → **Innovazione (5%)**. Se è una variante marginale di
  formula già usata dall'impresa → **Routine (non agevolabile)**.

**Esempio 7** — "Abbiamo fatto prove su prototipo con esiti negativi"
- Classificazione: gli esiti negativi sono la prova più forte di R&S genuina. Documentare
  i fallimenti è essenziale. → **R&S confermata** se c'era incertezza scientifica.

**Esempio 8** — "Abbiamo ridisegnato il packaging del prodotto"
- Classificazione: se il redesign riguarda solo l'estetica commerciale → **non agevolabile**
  (attività di marketing). Se riguarda innovazione del materiale con obiettivo riduzione
  plastica documentato → **Innovazione ecologica (10%)**.

**Esempio 9** — "Abbiamo sviluppato un software gestionale interno"
- Classificazione: sviluppo software standard per gestione aziendale → **non agevolabile**.
  Se il software usa tecniche di AI/ML non standard o risolve problemi tecnici nuovi →
  **Innovazione digitale (10%)** o **R&S** se c'è ricerca algoritmica originale.

**Esempio 10** — "Stiamo ottimizzando il consumo energetico del nostro impianto"
- Classificazione: se si adotta tecnologia nota (inverter, LED, ecc.) → **non agevolabile**
  (efficienza ordinaria). Se si sviluppa un sistema di controllo energetico innovativo
  integrato con dati di processo → **Innovazione ecologica (10%)**.

---

### Regola pratica per classificare

> Se c'è **incertezza sull'esito** e si documentano **tentativi falliti** → probabile R&S.
> Se si **applica tecnologia nota** per migliorare qualcosa di esistente → Innovazione.
> Se il risultato era **atteso e routinario** → non agevolabile.

---

## Sezione 4 — La documentazione: quaderno di laboratorio e perizia

### Quaderno di laboratorio / Project Notebook

Il quaderno di laboratorio è la spina dorsale della documentazione. Senza di esso,
la contestazione in sede di accertamento è quasi certa.

**Come strutturarlo — contenuto minimo per ogni registrazione:**
```
- Data (gg/mm/aaaa)
- Progetto di riferimento (codice/titolo)
- Attività svolta (descrizione tecnica, non generica)
- Persone coinvolte (nome, ruolo, ore dedicate)
- Strumenti/attrezzature utilizzati
- Risultati ottenuti (anche negativi — anzi, soprattutto negativi)
- Stato avanzamento e prossimi passi
- Firma del responsabile tecnico
```

**Regola fondamentale — contemporaneità**: il quaderno deve essere compilato contestualmente
all'attività, non ricostruito a posteriori. L'AdE può rilevare la contemporaneità attraverso
metadati digitali, coerenza delle date con altri documenti (buste paga, fatture fornitori),
testimonianze. La ricostruzione postuma è una delle principali cause di contestazione.

**Strumenti accettati:**
- Sistema informatico con log di accesso e modifica (preferibile — i metadati sono prova)
- Fogli fisici datati e firmati (scansionare e archiviare)
- Software di project management dedicato (Jira, Asana, LabArchives, ecc.) con export
- ERP aziendale con modulo R&S dedicato

---

### Perizia Asseverata

**Quando è obbligatoria**: per importi di tax credit superiori a **30.000 EUR** per periodo
di imposta (verificare soglia in relazione alla normativa vigente per il periodo specifico).
La perizia è fortemente raccomandata anche sotto soglia per progetti complessi.

**Chi può redigerla** (soggetti abilitati):
- Dottori commercialisti iscritti all'albo
- Revisori legali iscritti al registro
- Periti industriali con competenza nella materia
- Esperti in valutazione della ricerca (per R&S con contenuto scientifico elevato)

**Cosa deve contenere la perizia asseverata:**
1. Identificazione dell'impresa e del/dei progetto/i
2. Descrizione tecnica delle attività svolte
3. Classificazione motivata (R&S / Innovazione / Design) con riferimenti normativi
4. Analisi della documentazione di supporto (quaderno di laboratorio, contratti, buste paga)
5. Calcolo analitico delle spese ammissibili per categoria
6. Attestazione della completezza e veridicità della documentazione esaminata
7. Firma e timbro del perito con asseverazione della responsabilità

**Costo indicativo**: da 2.000 EUR a 15.000 EUR a seconda della complessità del progetto
e del numero di periodi di imposta coperti. Per grandi imprese con progetti pluriennali,
i costi possono essere superiori.

**Tempistica**: prevedere almeno 30-60 giorni per una perizia complessa. La perizia deve
essere pronta prima dell'utilizzo del credito in compensazione F24.

---

### Contratti di lavoro e lettere di incarico

Il personale impiegato nelle attività R&S/innovazione deve essere identificato con:
- Ruolo R&S esplicito nel contratto di lavoro (o mansionario allegato)
- In alternativa: lettera di incarico specifica per il progetto, con indicazione delle
  ore dedicate e delle attività assegnate
- Timesheet mensili firmati dal responsabile di progetto
- Corrispondenza tra ore dichiarate e ore di lavoro contrattualizzate

---

## Sezione 5 — Cumulabilità con Patent Box

### Patent Box (art. 6 D.L. 146/2021 — Patent Box "semplificato")

Il regime vigente prevede una **maggiorazione del 110%** dei costi di R&S direttamente
collegati allo sviluppo, mantenimento e accrescimento di beni immateriali (IP) tutelati:
brevetti industriali, software protetto da copyright, disegni e modelli industriali.

### Come funziona la cumulabilità

Le **stesse spese R&S** possono generare contemporaneamente:
1. **Tax credit R&S** (10% della spesa ammissibile) — credito d'imposta diretto
2. **Beneficio Patent Box** (110% della spesa come deduzione maggiorata da IRES/IRPEF)

Non si tratta di doppia agevolazione sulla stessa base, ma di due meccanismi distinti
che operano su versanti diversi (credito d'imposta vs deduzione maggiorata).

### Esempio numerico — investimento 100.000 EUR in R&S su brevetto

**Ipotesi**: PMI con aliquota IRES 24%, spesa R&S di 100.000 EUR per sviluppo di brevetto.

```
BENEFICIO TAX CREDIT R&S:
  Spesa ammissibile:          100.000 EUR
  Aliquota tax credit:             10%
  Credito d'imposta:           10.000 EUR  (riduzione diretta delle imposte dovute)

BENEFICIO PATENT BOX:
  Maggiorazione deducibile:   110.000 EUR  (110% di 100.000 EUR)
  Risparmio IRES (24%):        26.400 EUR

BENEFICIO TOTALE CUMULATO:
  Tax credit:                  10.000 EUR
  Risparmio IRES Patent Box:   26.400 EUR
  TOTALE BENEFICIO:            36.400 EUR

  Rendimento effettivo sull'investimento R&S: 36,4% di ritorno fiscale
```

### Condizioni per la cumulabilità

1. Il **nexus** tra costi R&S e IP tutelato deve essere documentato analiticamente
2. Traccia delle spese per progetto specifico e collegamento con il brevetto/IP
3. L'IP deve essere effettivamente detenuto e sfruttato dall'impresa
4. La documentazione deve essere predisposta prima dell'utilizzo (non a posteriori)
5. Per il Patent Box è necessaria documentazione specifica (ruling preventivo o
   documentazione idonea da conservare)

---

## Sezione 6 — Utilizzo in compensazione F24

### Modalità di fruizione

Il tax credit R&S/Innovazione/Design è utilizzabile **esclusivamente in compensazione
tramite modello F24** (non è rimborsabile in denaro).

**Non si applica il limite annuo di compensazione** di 250.000 EUR (art. 34 L. 388/2000)
né il limite di 700.000 EUR per i crediti d'imposta agevolativi — verificare normativa
vigente che ha modificato più volte questi limiti.

### Ripartizione in quote annuali

Il credito maturato in un periodo di imposta è utilizzabile in **3 quote annuali di pari
importo** (1/3 per anno). La prima quota è disponibile dall'anno successivo a quello di
maturazione. Verificare eventuali modifiche normative che hanno temporaneamente previsto
utilizzo in 5 quote per specifici periodi.

**Esempio**: credito maturato nell'anno X = 30.000 EUR
- Anno X+1: compensabile 10.000 EUR
- Anno X+2: compensabile 10.000 EUR
- Anno X+3: compensabile 10.000 EUR

### Codici tributo F24

| Tipo attività                          | Codice tributo |
|----------------------------------------|----------------|
| R&S (L. 160/2019)                      | 6938           |
| Innovazione Tecnologica                | 6939           |
| Design e Ideazione Estetica            | 6940           |
| Innovazione tecnologica ecologica/dig. | 6941           |

> Verificare sempre i codici tributo aggiornati sul sito AdE prima di compilare il modello F24.
> L'errore nel codice tributo può generare irregolarità nella compensazione.

### Periodo di utilizzo — regole sulla decorrenza

- Il credito è **irretroattivo**: si calcola sulle spese effettivamente sostenute nel periodo
  di imposta (competenza economica)
- La compensazione decorre dal **periodo d'imposta successivo** a quello di maturazione
- Il credito **non scade** (può essere riportato agli anni seguenti se non utilizzato)
- Obbligo di **visto di conformità** sulla dichiarazione dei redditi per crediti sopra soglia
  (verificare limite vigente — storicamente 5.000 EUR)

---

## Sezione 7 — Rischi: accertamenti e contestazioni

### I 5 rischi principali nelle istruttorie fiscali

---

**Rischio 1 — Riclassificazione dell'attività**

Descrizione: l'AdE riclassifica un'attività da R&S (10%) a innovazione ordinaria (5%)
o da innovazione a routine (0%), recuperando la differenza di aliquota più sanzioni.

Segnali di allerta:
- Attività descritte in modo generico nella documentazione ("sviluppo prodotto", "test")
- Assenza di documentazione dell'incertezza scientifica/tecnologica iniziale
- Nessun tentativo fallito documentato per le attività classificate R&S

Misura preventiva:
- Descrizione tecnica dettagliata delle attività nel project notebook
- Per R&S: documentare esplicitamente l'ipotesi scientifica da verificare e i tentativi falliti
- Ottenere parere tecnico preliminare da esperto del settore (non solo commercialista)

---

**Rischio 2 — Documentazione postuma**

Descrizione: l'AdE contesta che il quaderno di laboratorio o altra documentazione sia
stata prodotta retroattivamente per giustificare il credito già utilizzato.

Segnali di allerta:
- Metadati digitali che mostrano date di creazione successive all'utilizzo del credito
- Coerenza temporale sospetta (documenti creati tutti nello stesso giorno)
- Assenza di corrispondenza con altri documenti datati (email, ordini fornitori)

Misura preventiva:
- Utilizzare sistemi con log immutabile (software con timestamp certificato)
- Conservare email e comunicazioni coeve alle attività
- Non iniziare a documentare dopo aver deciso di usare il credito — documentare in real time

---

**Rischio 3 — Personale non qualificato o non dedicato**

Descrizione: il personale incluso nelle spese ammissibili non ha competenze adeguate
per le attività dichiarate o non era effettivamente dedicato al progetto R&S.

Segnali di allerta:
- Personale amministrativo o commerciale incluso come "ricercatore"
- Timesheet non coerenti con le presenze in azienda
- Assenza di correlazione tra qualifica contrattuale e attività R&S dichiarata

Misura preventiva:
- Lettere di incarico specifiche con descrizione del ruolo R&S
- Timesheet dettagliati e firmati a cadenza settimanale o mensile
- Per grandi progetti: organigramma del team R&S con CV dei ricercatori

---

**Rischio 4 — Spese di routine incluse per errore**

Descrizione: spese ordinarie (manutenzione, controllo qualità, aggiornamenti software
standard) vengono incluse nelle spese ammissibili, gonfiando il credito.

Segnali di allerta:
- Spese R&S corrispondenti a costi ricorrenti ogni anno in misura simile
- Attività incluse che non generano mai output tangibili (prototipi, relazioni, test)
- Fornitura di servizi standard da parte di consulenti abituali dell'impresa

Misura preventiva:
- Separare contabilmente i costi R&S/innovazione con centri di costo dedicati
- Ogni spesa inclusa deve essere collegata a un progetto specifico con output atteso
- Review annuale del commercialista prima dell'utilizzo del credito

---

**Rischio 5 — Mancanza della perizia asseverata**

Descrizione: il credito viene utilizzato in compensazione senza la perizia asseverata
obbligatoria, rendendo il credito non fruibile e soggetto a recupero integrale.

Segnali di allerta:
- Credito superiore a 30.000 EUR senza perizia in essere
- Perizia redatta dopo l'utilizzo del credito in F24
- Perizia redatta da soggetto non abilitato

Misura preventiva:
- Verificare la soglia di obbligatorietà prima di ogni utilizzo
- Commissionare la perizia con anticipo di almeno 60 giorni rispetto all'utilizzo
- Verificare l'abilitazione del perito prima del conferimento dell'incarico

---

## Sezione 8 — Checklist pre-utilizzo (15 domande)

Prima di utilizzare il tax credit in compensazione F24, l'impresa deve rispondere
affermativamente a tutte le domande applicabili:

```
CLASSIFICAZIONE ATTIVITA'
[ ] 1. Le attività svolte sono state classificate formalmente (R&S / Innovazione / Design)?
[ ] 2. La classificazione è supportata da una descrizione tecnica dettagliata per progetto?
[ ] 3. Sono stati esclusi esplicitamente i costi di routine non agevolabili?

DOCUMENTAZIONE CONTEMPORANEA
[ ] 4. Il quaderno di laboratorio / project notebook è stato compilato contestualmente?
[ ] 5. Ogni registrazione include data, persone, attività, risultati e ore?
[ ] 6. I tentativi falliti (per R&S) sono stati documentati?

PERSONALE
[ ] 7. Il personale incluso ha un contratto o lettera di incarico con ruolo R&S esplicito?
[ ] 8. I timesheet mensili sono disponibili e firmati dal responsabile?
[ ] 9. Le ore dichiarate sono coerenti con i contratti di lavoro e le presenze?

CALCOLO DEL CREDITO
[ ] 10. Le spese ammissibili sono state calcolate su base di competenza economica?
[ ] 11. I centri di costo dedicati R&S sono separati dalla contabilità ordinaria?
[ ] 12. L'importo del credito è stato verificato da un professionista abilitato?

PERIZIA E FORMALI
[ ] 13. Se il credito supera 30.000 EUR, la perizia asseverata è disponibile e firmata?
[ ] 14. Il codice tributo F24 corretto è stato verificato sul sito AdE?
[ ] 15. È presente il visto di conformità sulla dichiarazione dei redditi se richiesto?
```

---

## Sezione 9 — Output per orchestratore

Al termine dell'analisi, restituire il seguente oggetto JSON all'orchestratore:

```json
{
  "skill": "credito-rd-innovazione",
  "versione_normativa": "L. 160/2019 e s.m.i.",
  "periodo_imposta_analizzato": "AAAA",
  "tipo_attivita": ["rs", "innovazione", "design", "transizione"],
  "dettaglio_attivita": [
    {
      "tipo": "rs",
      "descrizione_progetto": "...",
      "spesa_ammissibile_eur": 0,
      "aliquota_applicabile_pct": 10,
      "beneficio_stimato_eur": 0
    },
    {
      "tipo": "innovazione",
      "descrizione_progetto": "...",
      "spesa_ammissibile_eur": 0,
      "aliquota_applicabile_pct": 5,
      "beneficio_stimato_eur": 0
    }
  ],
  "beneficio_totale_stimato_eur": 0,
  "cumulabilita_patent_box": false,
  "beneficio_patent_box_stimato_eur": 0,
  "beneficio_cumulato_totale_eur": 0,
  "documentazione_presente": false,
  "documentazione_mancante": [
    "quaderno_laboratorio",
    "timesheet_personale",
    "lettere_incarico",
    "perizia_asseverata",
    "centri_costo_dedicati"
  ],
  "rischi_principali": [
    "riclassificazione_attivita",
    "documentazione_postuma",
    "personale_non_qualificato",
    "spese_routine_incluse",
    "mancanza_perizia"
  ],
  "soglia_perizia_superata": false,
  "quote_annuali_utilizzo": 3,
  "prima_quota_disponibile_anno": "AAAA+1",
  "consulente_necessario": true,
  "note_operative": "..."
}
```

### Valori ammessi per i campi

- `tipo_attivita`: array con uno o più tra `"rs"`, `"innovazione"`, `"design"`, `"transizione"`
- `documentazione_mancante`: array con uno o più tra `"quaderno_laboratorio"`,
  `"timesheet_personale"`, `"lettere_incarico"`, `"perizia_asseverata"`,
  `"centri_costo_dedicati"`, `"contratti_ricerca"`, `"cv_ricercatori"`
- `rischi_principali`: array con uno o più tra `"riclassificazione_attivita"`,
  `"documentazione_postuma"`, `"personale_non_qualificato"`, `"spese_routine_incluse"`,
  `"mancanza_perizia"`
- `consulente_necessario`: `true` sempre se `soglia_perizia_superata: true` o se
  `rischi_principali` ha 2 o più elementi

---

## Note finali operative

Questa skill deve essere invocata preferibilmente **prima** che l'impresa sostenga le spese
(per impostare correttamente la documentazione fin dall'inizio) o al più tardi **prima**
dell'utilizzo del credito in F24 (per verificare la solidità del fascicolo documentale).

L'utilizzo del credito senza adeguata documentazione espone l'impresa a recupero integrale
del credito, sanzione dal 100% al 200% del credito non spettante, e interessi di mora.
Il rapporto rischio/beneficio è favorevole solo con una documentazione rigorosa.
