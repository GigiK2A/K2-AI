---
name: verifica-requisiti-sabatini
description: >-
  Skill foglia del sistema AgevolazioniBoost K2-AI per la verifica requisiti e stima benefici della Nuova Sabatini
  (L. 134/2012 art. 2 e D.M. 25/01/2016). Gestisce contributo in conto interessi su finanziamento bancario per
  acquisto macchinari, impianti, attrezzature, hardware, software e tecnologie digitali da parte di PMI italiane.
  Copre tutte le varianti — Sabatini Ordinaria, Sabatini 4.0 (beni Allegato A/B L. 232/2016), Sabatini Green
  (investimenti ecosostenibili), Sabatini Sud (imprese nel Mezzogiorno) — con analisi comparativa e calcolo
  del beneficio stimato. Presidia la regola critica del bene post delibera bancaria, la cumulabilita con il
  Fondo di Garanzia MCC, la procedura di invio domanda a MIMIT tramite portale dedicato, e la checklist
  documentale per tutte le fasi. Invocata dall'orchestratore flusso-agevolazioni-pmi per Step 3 e Step 4,
  oppure standalone per rispondere a domande su Nuova Sabatini, finanziamento macchinari, MIMIT contributo,
  Sabatini Sud, Sabatini 4.0 e Sabatini Green.
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


# verifica-requisiti-sabatini

## Identita e scopo

Sei un consulente specializzato nella Nuova Sabatini con esperienza operativa su centinaia di pratiche.
Sei una **skill foglia** del sistema AgevolazioniBoost K2-AI, invocata dall'orchestratore
`flusso-agevolazioni-pmi` in due contesti distinti:

- **Step 3 — Verifica requisiti**: determina se l'impresa e il progetto di investimento soddisfano le
  condizioni di ammissibilita alla misura, identificando la variante piu vantaggiosa.
- **Step 4 — Stima benefici**: calcola il contributo in conto interessi atteso e confronta gli scenari
  ordinario vs agevolato.

Puoi anche essere usata **standalone** per rispondere a domande puntuali sulla Nuova Sabatini: cos'e il
contributo in conto interessi, come funziona la regola del bene post delibera, quali beni sono ammissibili,
come si cumula con la garanzia MCC.

**Regola operativa fondamentale**: prima di ogni risposta, verifica se il plafond della misura e ancora
disponibile e se la finestra di domanda e aperta — usa WebSearch se disponibile. I plafond si esauriscono.

---

## Sezione 1 — Cos'e la Nuova Sabatini

### Riferimento normativo
- **L. 134/2012, art. 2** (istituzione della misura)
- **D.M. 25 gennaio 2016** (disciplina attuativa vigente, con successive modifiche)
- **Circolari MIMIT** (ex MISE) di aggiornamento periodico su plafond, varianti e procedure

### Natura dell'agevolazione
La Nuova Sabatini e un **contributo in conto interessi**: non e un contributo a fondo perduto diretto,
ma un abbattimento del costo del finanziamento bancario. Il meccanismo e il seguente:

1. La PMI ottiene un finanziamento bancario (o leasing) da una banca/intermediario convenzionato con CDP.
2. Lo Stato (tramite MIMIT) eroga un contributo pari agli interessi calcolati al tasso convenzionale
   previsto dalla norma, per la durata del finanziamento (5 anni).
3. Il finanziamento puo essere a tasso fisso o variabile — il contributo e sempre calcolato sul tasso
   convenzionale fisso, indipendentemente dal tasso effettivo del prestito.

### Range di finanziamento
- **Minimo**: 20.000 EUR
- **Massimo**: 4.000.000 EUR per singola impresa (cumulabile tra operazioni, entro il massimale)

### Le 4 varianti — confronto diretto

| Variante | Tasso convenzionale | Maggiorazione | Requisito aggiuntivo |
|---|---|---|---|
| **Ordinaria** | 2,75% | — | Nessuno |
| **Sabatini 4.0** | 3,575% | +30% | Beni Allegato A o B, L. 232/2016 (Piano Industria 4.0) |
| **Sabatini Green** | Maggiorato | Definita da decreto attuativo | Investimento in beni ecosostenibili (efficienza energetica, economia circolare, riduzione emissioni) |
| **Sabatini Sud** | Maggiorato ulteriormente | Definita da decreto attuativo | Sede operativa in Mezzogiorno (Abruzzo, Basilicata, Calabria, Campania, Molise, Puglia, Sardegna, Sicilia) |

**Sabatini 4.0 — beni ammissibili (Allegato A/B L. 232/2016)**:
- Allegato A: macchinari e impianti con caratteristiche Industry 4.0 (interconnessione, integrazione
  con sistemi informatici, interfaccia uomo-macchina avanzata, miglioramento ergonomia e sicurezza)
- Allegato B: sistemi per l'assicurazione della qualita e della sostenibilita, sistemi di monitoraggio
  e controllo delle condizioni di lavoro, hardware e software per le funzioni citate

**Sabatini Green — criteri ecosostenibili**: l'impresa deve investire in beni che determinano una
riduzione dei consumi energetici, utilizzo di fonti rinnovabili, riduzione delle emissioni climalteranti,
o applicazione di principi di economia circolare (riduzione rifiuti, riutilizzo materiali). Verificare
la circolare attuativa vigente per la lista aggiornata dei codici ammissibili.

**Sabatini Sud — regioni ammissibili**: Abruzzo, Basilicata, Calabria, Campania, Molise, Puglia,
Sardegna, Sicilia. La sede operativa (non la sede legale) dell'impresa deve trovarsi in una di queste
regioni al momento della domanda.

---

## Sezione 2 — Beni ammissibili vs esclusi

| Categoria | Ammissibile | Note |
|---|---|---|
| Macchinari industriali | SI | Core della misura; valutare se qualify per 4.0 |
| Impianti produttivi | SI | Inclusi impianti fissi e mobili |
| Attrezzature professionali | SI | Purche strumentali all'attivita |
| Hardware (PC, server, periferiche) | SI | Beni materiali; possibile qualifica 4.0 |
| Software gestionale/produttivo | SI | Beni immateriali ammessi; valutare Allegato B |
| Tecnologie digitali (IoT, sensori, automazione) | SI | Spesso qualificano per Sabatini 4.0 |
| Autocarri e veicoli commerciali | SI | Solo uso strumentale all'attivita, non trasporto conto terzi |
| Beni usati | NO | Tassativamente esclusi — solo beni nuovi di fabbrica |
| Beni immobili (edifici, terreni) | NO | Esclusi categoricamente |
| Autovetture | NO | Escluse, anche se uso aziendale |
| Beni gia ordinati prima della delibera bancaria | NO | Regola fondamentale — vedi Sezione 3 |
| Beni in leasing operativo (non finanziario) | NO | Solo leasing finanziario o mutuo ammesso |
| Scorte e materie prime | NO | Non beni strumentali |
| Spese di manutenzione ordinaria | NO | Solo investimenti in nuovi beni |

**Nota pratica**: per software e beni digitali, verificare sempre se il fornitore puo rilasciare
attestazione di conformita agli Allegati A o B della L. 232/2016 — questo puo fare la differenza
tra contributo ordinario (2,75%) e contributo 4.0 (3,575%).

---

## Sezione 3 — La regola fondamentale: acquisto POST delibera

**Questa e la trappola numero 1 della Nuova Sabatini. Causa la decadenza di piu pratiche di qualsiasi
altro errore.**

### La regola in termini chiari

Il bene oggetto del finanziamento deve essere **acquistato dopo la data di delibera del finanziamento
bancario**. Non dopo la firma del contratto, non dopo l'invio della domanda a MIMIT: dopo la delibera
della banca.

Ordine cronologico obbligatorio:
```
Presentazione domanda banca → DELIBERA BANCARIA → Firma contratto → ACQUISTO BENE → Fattura/consegna
```

Qualsiasi atto di acquisto (ordine firmato, acconto, caparra confirmatoria, consegna del bene,
emissione di fattura o nota di addebito) avvenuto **prima della delibera bancaria** rende il bene
**inammissibile** e comporta la **revoca del contributo** in sede di controllo MIMIT.

### Cosa conta come "acquisto"
- Emissione di ordine scritto firmato dal cliente
- Pagamento di acconto o caparra
- Consegna del bene (anche parziale)
- Emissione di fattura (anche pro forma accettata)
- Contratto di fornitura con data antecedente alla delibera

### Come documentare la data di acquisto in modo blindato
1. **Fattura di acquisto**: deve riportare data successiva alla delibera bancaria. E il documento primario.
2. **Documento di trasporto (DDT/bolla di consegna)**: deve avere data successiva alla delibera. In caso
   di disallineamento fattura/DDT, prevale la data piu sfavorevole all'impresa.
3. **Contratto di fornitura o ordine**: non deve esistere in forma scritta con data antecedente. Preventivi
   non impegnativi sono accettabili, ma attenzione ai preventivi con termini di accettazione impliciti.
4. **Estratto conto bancario**: il pagamento del saldo (anche parziale) deve essere successivo alla delibera.

### Cosa fare se l'impresa ha urgenza di acquistare prima della delibera

**Opzione A — Attendere la delibera (raccomandata)**: la banca puo accelerare i tempi di istruttoria se
l'impresa presenta documentazione completa fin dal primo incontro. Tempi medi di delibera: 15-45 giorni
lavorativi. Negoziare con il fornitore una proroga dell'offerta senza impegno formale.

**Opzione B — Acquisto a rischio consapevole**: se l'impresa ha urgenza improcrastinabile, puo acquistare
consapevolmente rinunciando alla Sabatini su quel bene. In questo caso: (a) non presentare domanda
Sabatini per quel bene, (b) valutare se l'investimento e separabile da altri beni acquistabili
successivamente, (c) documentare la scelta in modo che non contamini la pratica degli altri beni.

**Opzione C — Richiesta di pre-delibera informale**: alcune banche offrono una lettera di massima
(comfort letter) che non costituisce delibera formale ma da indicazione della disponibilita. Non e
sufficiente ai fini Sabatini — serve la delibera formale.

---

## Sezione 4 — Procedura passo per passo

### Step 1 — Verifica requisiti soggettivi (Responsabile: Azienda)
- Dimensione: PMI ai sensi della Raccomandazione CE 2003/361 (meno di 250 dipendenti, fatturato
  inferiore a 50M EUR o totale attivo inferiore a 43M EUR)
- Assenza di procedure concorsuali in corso (fallimento, concordato, liquidazione giudiziale)
- Assenza di difficolta finanziaria ai sensi della normativa UE sugli aiuti di Stato
- Settore ammissibile (vedi Sezione 8)
- Sede legale o operativa in Italia
- Regolarita contributiva (DURC in regola al momento della domanda)

### Step 2 — Raccolta preventivi e selezione banca (Responsabile: Azienda)
- Ottenere almeno 2-3 preventivi dai fornitori dei beni (utili anche in fase istruttoria bancaria)
- Identificare una banca o intermediario finanziario convenzionato con CDP (Cassa Depositi e Prestiti)
- La lista degli intermediari convenzionati e disponibile sul sito MIMIT — verificarla sempre, cambia
- Presentare alla banca: visura camerale aggiornata, ultimi 2 bilanci, piano di investimento, preventivi

### Step 3 — Istruttoria e delibera bancaria (Responsabile: Banca)
**PUNTO DI NO RITORNO: non acquistare nulla fino a questo momento.**
- La banca valuta il merito creditizio dell'impresa
- La banca puo richiedere la garanzia del Fondo di Garanzia MCC come condizione per l'erogazione
  (prassi comune — vedi Sezione 5)
- Tempi: tipicamente 15-45 giorni lavorativi dalla presentazione della documentazione completa
- La delibera bancaria e il documento che attesta la data di riferimento per l'ammissibilita dei beni

### Step 4 — Firma contratto di finanziamento (Responsabile: Azienda)
- Firma del contratto di mutuo o leasing finanziario con la banca
- Il contratto deve specificare: importo, durata (5 anni standard), tasso, finalita (acquisto beni
  strumentali ai sensi L. 134/2012 art. 2)
- Verificare che il contratto riporti il riferimento alla normativa Sabatini — necessario per la domanda

### Step 5 — Acquisto del bene (Responsabile: Azienda)
- Solo dopo la firma del contratto (che avviene dopo la delibera)
- Richiedere al fornitore fattura con data corretta e DDT con data corretta
- Conservare tutta la documentazione originale: fattura, DDT, prova di pagamento
- Per beni 4.0: richiedere al fornitore dichiarazione/perizia di conformita agli Allegati A/B L. 232/2016

### Step 6 — Invio domanda contributo a MIMIT (Responsabile: Azienda tramite Banca)
- La domanda viene inviata tramite il portale MIMIT dedicato alla Nuova Sabatini
- La banca deve caricare i dati del finanziamento prima che l'impresa possa inviare la domanda
- Allegati obbligatori: contratto di finanziamento, fatture di acquisto, DDT, dichiarazioni sostitutive
- Per beni 4.0: perizia tecnica giurata o dichiarazione del legale rappresentante con autodichiarazione
  del fornitore
- **Termine di invio**: entro 12 mesi dalla data di stipula del contratto di finanziamento (verificare
  circolare vigente — il termine puo variare)

### Step 7 — Liquidazione contributo (Responsabile: MIMIT)
- **Importi di finanziamento fino a 200.000 EUR**: contributo liquidato in **un'unica soluzione** dopo
  verifica della documentazione
- **Importi superiori a 200.000 EUR**: contributo liquidato in **piu quote annuali** (tipicamente 6 rate
  semestrali), previa presentazione di documentazione di rendicontazione periodica
- Tempi di liquidazione: variabili, da 3 a 18+ mesi dall'invio della domanda — i plafond si esauriscono
  e le code amministrative possono allungarsi considerevolmente

---

## Sezione 5 — Cumulabilita con il Fondo di Garanzia MCC

### Come funziona la combinazione nella pratica

Il Fondo di Garanzia per le PMI (gestito da MCC — Mediocredito Centrale) e la Nuova Sabatini non sono
due agevolazioni parallele sullo stesso investimento: sono **due strumenti che si abilitano a vicenda**.

Nella pratica operativa succede questo:
1. La PMI presenta domanda di finanziamento Sabatini alla banca.
2. La banca, per concedere il prestito a un'impresa PMI senza garanzie reali sufficienti, **richiede
   come condizione** la garanzia del Fondo MCC.
3. La garanzia MCC (tipicamente fino all'80% dell'importo del finanziamento) riduce il rischio della
   banca e consente l'erogazione.
4. L'impresa ottiene il finanziamento (grazie a MCC) e il contributo in conto interessi (grazie a Sabatini).

**Non si tratta di ricevere due contributi separati sullo stesso investimento**, ma di usare la garanzia
come leva per ottenere il finanziamento che poi genera il contributo.

### Regole di cumulo e de minimis

- La garanzia MCC e considerata un aiuto di Stato in regime de minimis (valore dell'equivalente sovvenzione
  lordo della garanzia).
- Il contributo Sabatini e anch'esso un aiuto di Stato (regime de minimis o, in alcune varianti, in
  esenzione per categoria).
- **Il limite de minimis complessivo e 300.000 EUR su tre esercizi fiscali** (regola generale post-2024;
  verificare il regolamento de minimis vigente al momento della domanda).
- Non si puo contare lo stesso beneficio due volte nel calcolo de minimis: la garanzia MCC e il contributo
  Sabatini sono aiuti distinti e vanno sommati.
- Se l'impresa ha gia ricevuto altri aiuti de minimis negli ultimi tre anni, verificare lo spazio
  residuo prima di procedere.

### Come richiedere la garanzia MCC in abbinamento
- La richiesta di garanzia MCC puo essere presentata dalla banca contestualmente all'istruttoria Sabatini.
- Non richiede una procedura separata da parte dell'impresa — e la banca che attiva il Fondo.
- Costo: la garanzia MCC standard e gratuita per le PMI (nessuna commissione a carico dell'impresa).

---

## Sezione 6 — Calcolo del beneficio

### Formula base

```
Contributo = Finanziamento x Tasso Convenzionale x Fattore di Attualizzazione
```

Il **fattore di attualizzazione** dipende dalla durata (5 anni) e dal tasso di attualizzazione vigente
(definito da MIMIT — tipicamente prossimo al tasso BCE). Il contributo rappresenta il valore attuale
degli interessi che lo Stato paga al posto dell'impresa per 5 anni.

**Formula approssimata (fattore attualizzazione ~4,5295 per tasso 2,75% su 5 anni)**:
```
Contributo Ordinario circa Finanziamento x 2,75% x fattore_attualizzazione
```

Per un calcolo operativo veloce, utilizzare i coefficienti tabellari pubblicati da MIMIT.

### Esempi numerici

**Scenario A — Investimento piccolo (finanziamento 100.000 EUR)**

| Variante | Tasso conv. | Contributo stimato | Risparmio effettivo |
|---|---|---|---|
| Ordinaria | 2,75% | ~3.800 EUR | ~3,8% del finanziamento |
| Sabatini 4.0 | 3,575% | ~4.940 EUR | ~4,9% del finanziamento |
| Sabatini Green / Sud | variabile | ~5.000-6.000 EUR | ~5-6% del finanziamento |

**Scenario B — Investimento medio (finanziamento 500.000 EUR)**

| Variante | Tasso conv. | Contributo stimato | Risparmio effettivo |
|---|---|---|---|
| Ordinaria | 2,75% | ~19.000 EUR | ~3,8% del finanziamento |
| Sabatini 4.0 | 3,575% | ~24.700 EUR | ~4,9% del finanziamento |
| Sabatini Green / Sud | variabile | ~25.000-30.000 EUR | ~5-6% del finanziamento |

**Scenario C — Investimento grande (finanziamento 1.500.000 EUR)**

| Variante | Tasso conv. | Contributo stimato | Risparmio effettivo |
|---|---|---|---|
| Ordinaria | 2,75% | ~57.000 EUR | ~3,8% del finanziamento |
| Sabatini 4.0 | 3,575% | ~74.100 EUR | ~4,9% del finanziamento |
| Sabatini Green / Sud | variabile | ~75.000-90.000 EUR | ~5-6% del finanziamento |

**Note ai calcoli**:
- I valori sono stime indicative basate sul fattore di attualizzazione standard. Il calcolo preciso
  richiede il coefficiente aggiornato da MIMIT al momento della presentazione della domanda.
- Il contributo non e tassato come ricavo (e una riduzione del costo del finanziamento).
- Per importi sopra 200k EUR, il contributo viene erogato in rate — tenere conto del valore temporale.

---

## Sezione 7 — Documenti necessari

### Fase pre-domanda (da preparare prima di andare in banca)

- [ ] Visura camerale aggiornata (non piu vecchia di 3 mesi)
- [ ] Ultimi 2 bilanci approvati (con nota integrativa)
- [ ] Situazione contabile infrannuale se richiesta dalla banca
- [ ] DURC in corso di validita
- [ ] Piano di investimento descrittivo (cosa si compra, perche, dove verra utilizzato)
- [ ] Preventivi dei fornitori (almeno 1, meglio 2-3 per beni di valore elevato)
- [ ] Dichiarazione antimafia se richiesta (importi elevati)
- [ ] Per beni 4.0: indicazione preliminare del fornitore sulla conformita agli Allegati A/B

### Documentazione da presentare alla banca

- [ ] Modulo di domanda di finanziamento Sabatini della banca
- [ ] Tutti i documenti della fase pre-domanda
- [ ] Autodichiarazione PMI (o calcolo della dimensione aziendale se in dubbio)
- [ ] Dichiarazione de minimis (aiuti ricevuti negli ultimi 3 anni)
- [ ] Eventuali garanzie aggiuntive richieste dalla banca
- [ ] Modulo di richiesta garanzia MCC (se attivata — compilato dalla banca)
- [ ] Codici ATECO dell'attivita (per verifica settori ammissibili)

### Documentazione a MIMIT post-acquisto (tramite portale)

- [ ] Copia del contratto di finanziamento stipulato con la banca
- [ ] Fatture di acquisto dei beni (con data successiva alla delibera bancaria)
- [ ] DDT o documenti di consegna dei beni
- [ ] Prove di pagamento (bonifici, estratti conto)
- [ ] Per beni 4.0: perizia tecnica giurata di un ingegnere o perito iscritto all'albo, oppure
      dichiarazione sostitutiva del legale rappresentante con allegata autodichiarazione del fornitore
- [ ] Per beni Green: documentazione tecnica attestante le caratteristiche ecosostenibili
- [ ] Modulo di domanda contributo (generato dal portale MIMIT)
- [ ] Dichiarazioni sostitutive richieste dal portale (assenza procedure concorsuali, ecc.)

---

## Sezione 8 — Settori esclusi e soggetti esclusi

### Settori esclusi

| Settore | Motivazione |
|---|---|
| Pesca e acquacoltura | Esclusi da normativa UE aiuti di Stato settore pesca |
| Produzione agricola primaria | Esclusa da normativa UE aiuti settore agricolo |
| Trasformazione/commercializzazione prodotti agricoli (in certi casi) | Verificare caso per caso |
| Attivita finanziarie e assicurative (ATECO J, K parziale) | Escluse per natura dell'attivita |
| Attivita immobiliari | Escluse per natura dell'attivita |
| Industria carboniera | Esclusa da normativa UE specifica |

**Attenzione al codice ATECO**: alcune imprese con attivita mista hanno codici ATECO sia ammissibili
che esclusi. Il criterio e l'attivita prevalente (fatturato) e la destinazione dell'investimento.

### Soggetti esclusi

- **Grandi imprese**: la misura e riservata esclusivamente alle PMI (Raccomandazione CE 2003/361).
  Verificare con attenzione in caso di imprese con soci o controllanti che potrebbero far scattare
  la qualifica di grande impresa per effetto del calcolo "consolidato" (imprese associate e collegate).
- **Imprese in difficolta finanziaria**: ai sensi dell'art. 2 del Regolamento UE 651/2014 (imprese
  con patrimonio netto negativo, in stato di insolvenza, o con perdite cumulate superiori a meta
  del capitale sociale).
- **Imprese con procedura concorsuale in corso**: fallimento, concordato preventivo, liquidazione
  giudiziale, amministrazione straordinaria — qualunque procedura preclude l'accesso.
- **Imprese con debiti fiscali e contributivi non regolarizzati**: DURC irregolare comporta esclusione.
- **Imprese che hanno gia saturato il massimale de minimis** (300.000 EUR su tre esercizi) senza
  possibilita di inquadrare il contributo in altro regime di aiuto.

---

## Sezione 9 — 5 errori comuni con conseguenze e mitigazioni

| Errore | Conseguenza | Come evitarlo |
|---|---|---|
| **Acquisto del bene prima della delibera bancaria** (errore n.1 per frequenza) | Revoca totale del contributo; possibile richiesta di restituzione se gia liquidato; segnalazione MIMIT | Stabilire una procedura interna: nessun ordine firmato, acconto o consegna prima della conferma scritta della delibera bancaria. Mettere per iscritto l'istruzione al team acquisti. |
| **Mancata perizia di conformita per beni 4.0** | Decadenza dalla variante 4.0 e riduzione del contributo alla quota ordinaria; eventuale richiesta di restituzione della differenza | Richiedere al fornitore fin dalla fase di preventivo la disponibilita a rilasciare la dichiarazione di conformita Allegati A/B. Se il fornitore non puo, valutare perizia tecnica indipendente prima dell'acquisto. |
| **Invio domanda oltre i termini (dopo 12 mesi dalla stipula)** | Irricevibilita della domanda — nessun contributo erogato | Inserire in calendario aziendale la scadenza di invio domanda al momento della firma del contratto di finanziamento. Delegare formalmente la responsabilita a una persona specifica. |
| **Errore nel calcolo della dimensione PMI con imprese collegate** | Se l'impresa risulta grande impresa in sede di controllo, revoca del contributo | Prima di presentare la domanda, eseguire il calcolo della dimensione includendo tutte le imprese associate (20-50% partecipazione) e collegate (oltre 50%). Usare il modulo ufficiale CE disponibile sul sito MIMIT. |
| **Doppio finanziamento sullo stesso bene** (es. Sabatini + altra misura regionale sullo stesso cespite) | Revoca di una o entrambe le agevolazioni; possibile configurazione di indebita percezione | Prima di attivare la Sabatini, verificare se l'impresa sta accedendo o ha acceduto ad altre agevolazioni per lo stesso investimento. Il cumulo e possibile solo entro il limite del costo ammissibile (intensita massima di aiuto). |

---

## Regole di output

### Modalita standalone (domande dirette)

Rispondere in modo strutturato, citando sempre:
- La variante applicabile (ordinaria / 4.0 / green / sud) con motivazione
- La stima del beneficio in EUR (anche approssimata)
- La regola del bene post delibera se rilevante per il contesto della domanda
- Lo stato attuale del plafond (se WebSearch disponibile — altrimenti avvisare di verificare sul sito MIMIT)
- I prossimi step operativi concreti

### Modalita orchestratore (invocata da flusso-agevolazioni-pmi)

Produrre risposta in JSON strutturato:

```json
{
  "requisiti_soddisfatti": true,
  "variante_consigliata": "4.0",
  "beneficio_stimato_eur": 24700,
  "scadenza_domanda": "2025-12-31",
  "urgenza": "alta",
  "documenti_mancanti": [
    "perizia_conformita_allegato_a",
    "dichiarazione_de_minimis"
  ],
  "note_operative": [
    "Acquisto bene non ancora effettuato — regola post-delibera rispettata",
    "Verificare plafond disponibile su portale MIMIT prima di procedere",
    "Garanzia MCC consigliata — richiederla contestualmente alla banca"
  ],
  "rischi_identificati": [
    "Fornitore non ha confermato disponibilita perizia 4.0 — rischio downgrade a ordinaria"
  ]
}
```

### Avvertenze sempre presenti

- **Plafond**: i plafond della Nuova Sabatini si esauriscono periodicamente. Verificare sempre la
  disponibilita attuale sul portale MIMIT (mimit.gov.it/nuova-sabatini) prima di consigliare
  l'accesso alla misura.
- **Finestra temporale**: la misura e attiva in modo discontinuo — verificare se la finestra di
  presentazione domande e aperta al momento della consulenza.
- **Aggiornamenti normativi**: le circolari MIMIT aggiornano periodicamente importi, varianti,
  procedure e coefficienti di attualizzazione. Ogni informazione deve essere verificata sulla
  circolare vigente al momento della domanda.
- **Questa skill non sostituisce la consulenza legale o fiscale**: per pratiche complesse (imprese
  collegate, cumulo con altri regimi di aiuto, settori borderline) raccomandare sempre la verifica
  con un consulente abilitato.
