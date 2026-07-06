---
name: calcolo-decontribuzione-assunzioni
description: Skill foglia per il calcolo dei benefici economici derivanti dai bonus assunzioni e dalle decontribuzioni per PMI italiane — esonero under 36, donne svantaggiate, Decontribuzione Sud, incentivo disabili, apprendistato. Raccoglie il profilo del lavoratore (età, genere, disoccupazione, disabilità), il tipo di contratto, la zona geografica e la RAL; identifica tutti i bonus applicabili con percentuale esonero, massimale mensile, durata e risparmio totale stimato; individua il bonus ottimale o la combinazione migliore (gestione non cumulabilità); produce simulazione numerica con tabella per bonus, raccomandazione finale e checklist adempimenti INPS. Invocabile standalone o dall'orchestratore flusso-agevolazioni-pmi. Attenzione — la presentazione della domanda richiede un consulente del lavoro abilitato.
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
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --materia bilancio_finanza_pubblica --limit 5
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

Knowledge pack norme: `~/normattiva_ai/knowledge_packs/bilancio_finanza_pubblica/`

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# calcolo-decontribuzione-assunzioni — Simulatore Bonus Assunzioni PMI

## 1. Cosa fa questa skill (e perché esiste)

Questa skill foglia **calcola il valore economico dei bonus assunzioni e delle decontribuzioni contributive** disponibili per le PMI italiane. Traduce il profilo di un'assunzione pianificata in numeri concreti: quanti euro di contributi previdenziali l'azienda risparmia, per quanti mesi, a quali condizioni.

Il target è duplice:
- **Standalone**: il titolare di PMI o il suo consulente del lavoro vuole sapere se assumere un determinato profilo conviene di più con l'esonero under 36 o con la Decontribuzione Sud, e quanto vale esattamente.
- **Invocata da `flusso-agevolazioni-pmi`**: l'orchestratore delega il calcolo di dettaglio ogni volta che tra gli investimenti pianificati compaiono assunzioni.

Il valore di questa skill è nella **precisione numerica** e nella **gestione della non cumulabilità**: i bonus assunzioni hanno regole di sovrapposizione complesse, e sbagliare la combinazione significa lasciare soldi sul tavolo o — peggio — ricevere una contestazione INPS.

> **Avvertenza obbligatoria**: questa skill produce una simulazione a supporto delle decisioni. La presentazione della domanda all'INPS, la comunicazione preventiva obbligatoria e la gestione dell'intero iter burocratico devono essere affidate a un **consulente del lavoro abilitato**. Questo strumento non sostituisce la consulenza previdenziale professionale.

---

## 2. Quando attivarsi

Attivati se:
- L'utente menziona assunzioni pianificate per i prossimi 6-12 mesi.
- L'utente chiede "quanto risparmio assumendo un under 36?", "ho sentito parlare di esonero contributivo", "cosa è la Decontribuzione Sud?", "conviene fare apprendistato?".
- L'orchestratore `flusso-agevolazioni-pmi` ha identificato assunzioni tra gli investimenti pianificati.
- L'utente deve scegliere tra più profili di candidati e vuole ottimizzare il beneficio contributivo.

Non attivarti se la domanda riguarda esclusivamente la ricerca del candidato, il contratto collettivo applicabile (materia che spetta al consulente del lavoro) o il costo del lavoro lordo senza interesse per le agevolazioni.

---

## 3. Input richiesti

Raccogliere in modo conversazionale — non un form rigido. Se l'utente non conosce un dato, procedere con ipotesi esplicite e segnalarle nell'output.

### Per ogni assunzione pianificata

**Profilo del lavoratore**
- Età anagrafica alla data di assunzione prevista
- Genere (rilevante per esonero donne svantaggiate)
- Stato occupazionale: occupato, disoccupato da meno di 6 mesi, disoccupato da 6-12 mesi, disoccupato da 12-24 mesi, disoccupato da oltre 24 mesi
- Settori precedenti (per donne: settori svantaggiati ai sensi D.M. annuale MLPS)
- Presenza di disabilità (tipo e percentuale di invalidità riconosciuta ai sensi L. 68/1999)
- Il soggetto ha già avuto un contratto a tempo indeterminato in precedenza? (rilevante per esonero under 36)

**Contratto**
- Tipo: tempo indeterminato, apprendistato professionalizzante, apprendistato per la qualifica, determinato (i bonus principali sono limitati all'indeterminato)
- Part-time o full-time (incide sul massimale mensile pro-quota)
- Mansione e inquadramento (per il calcolo della RAL)

**Azienda**
- Zona geografica della sede di lavoro: Nord, Centro, Sud/Isole (per Decontribuzione Sud le regioni ammesse sono Abruzzo, Basilicata, Calabria, Campania, Molise, Puglia, Sardegna, Sicilia)
- Settore ATECO (alcune agevolazioni escludono settori specifici: agricoltura, pesca, PA)
- L'azienda ha effettuato licenziamenti collettivi o individuali per GMO negli ultimi 6 mesi nella stessa unità produttiva e per la stessa qualifica? (condizione di decadenza)
- L'azienda è in regola con il DURC?

**RAL e costo contributivo**
- RAL prevista (€/anno)
- CCNL applicato (per calcolo aliquota contributiva datoriale media applicabile)

Se la RAL non è nota: usare come proxy i minimi tabellari CCNL per la mansione indicata, segnalando l'ipotesi.

---

## 4. Catalogo bonus assunzioni — regole di calcolo

### 4.1 Esonero contributivo under 36 (o under 35 in certi regimi ZES)

**Riferimento normativo**: art. 1 cc. 10-15 L. 178/2020 (Legge di Bilancio 2021) e proroghe annuali successive. Verificare la Legge di Bilancio dell'anno di assunzione per conferma proroga e massimali aggiornati.

**Condizioni**:
- Lavoratore con meno di 36 anni compiuti alla data di assunzione (soglia sotto i 36 al momento della stipula)
- Primo contratto a tempo indeterminato in assoluto (il lavoratore non deve aver avuto precedenti contratti a tempo indeterminato con nessun datore di lavoro)
- Il lavoratore non deve essere stato assunto a tempo indeterminato dallo stesso datore negli ultimi 6 mesi
- Azienda non deve aver effettuato licenziamenti individuali per GMO o collettivi nei 6 mesi precedenti nella stessa unità produttiva per la stessa qualifica

**Agevolazione**:
- Esonero dal versamento dei contributi previdenziali a carico del datore di lavoro (esclusi: premi INAIL, contributo di solidarietà, contributi al Fondo di Tesoreria INPS)
- Percentuale esonero: **100% dei contributi datoriali**
- Massimale: **6.000 EUR/anno** (500 EUR/mese) — per assunzioni al Sud può arrivare a **8.060 EUR/anno** (in specifici regimi; verificare Legge di Bilancio applicabile)
- Durata: **36 mesi** (48 mesi per assunzioni in regioni del Mezzogiorno in certi regimi)
- Benefit totale stimabile: fino a 18.000 EUR su 36 mesi (cap 500 EUR/mese × 36)

**Calcolo pratico**:
```
Contributi datoriali mensili = RAL_mensile × aliquota_contributiva_datoriale
Esonero mensile = MIN(Contributi_datoriali_mensili; massimale_mensile)
Risparmio totale = Esonero_mensile × mesi_durata
```

---

### 4.2 Esonero donne svantaggiate

**Riferimento normativo**: art. 4 cc. 8-11 L. 92/2012 (Legge Fornero) + D.M. annuale MLPS che definisce i settori svantaggiati per l'anno di riferimento.

**Condizioni** (alternative — basta una):
- Donna disoccupata da almeno 24 mesi (indipendentemente dal settore)
- Donna disoccupata da almeno 6 mesi e residente in area svantaggiata (definita da MLPS) o inserita in settore con forte disparità di genere (definito da D.M. MLPS annuale)
- Donna priva di impiego regolarmente retribuito da almeno 6 mesi con mansioni in settori con tasso di disparità uomo-donna superiore almeno del 25% alla media nazionale

**Agevolazione**:
- Esonero dal versamento dei contributi previdenziali a carico del datore di lavoro
- Percentuale esonero: **100% dei contributi datoriali**
- Massimale: **8.060 EUR/anno** (circa 671 EUR/mese)
- Durata: **18 mesi** per contratti a tempo indeterminato; **12 mesi** per contratti a termine (poi prorogati a tempo indeterminato)
- Benefit totale stimabile: fino a 12.090 EUR su 18 mesi

**Attenzione**: questo esonero è soggetto a autorizzazione UE (Regolamento de minimis o GBER). Verificare con il consulente del lavoro la procedura di comunicazione preventiva INPS (flusso UNIEMENS).

---

### 4.3 Decontribuzione Sud

**Riferimento normativo**: art. 1 cc. 161-168 L. 178/2020 (proroga triennale 2021-2029 con riduzione progressiva dell'aliquota). Subordinata ad autorizzazione UE — verificare stato autorizzativo aggiornato.

**Regioni ammesse**: Abruzzo, Basilicata, Calabria, Campania, Molise, Puglia, Sardegna, Sicilia.

**Condizioni**:
- Sede di lavoro (unità produttiva) ubicata in una delle regioni ammesse
- Applicabile a **tutti i lavoratori** (non solo nuove assunzioni) con contratto subordinato
- Esclusi: lavoratori domestici, settore agricolo (regime separato), enti pubblici non economici
- Azienda in regola con DURC

**Agevolazione** (aliquote decrescenti per fase):
- 2021-2025: esonero del **30%** dei contributi datoriali (senza massimale fisso per dipendente, ma con massimale de minimis complessivo per azienda)
- 2026-2027: esonero del **20%**
- 2028-2029: esonero del **10%**

**Calcolo pratico** (fase 2021-2025):
```
Contributi datoriali mensili = RAL_mensile × aliquota_contributiva_datoriale
Esonero mensile = Contributi_datoriali_mensili × 30%
Risparmio annuo = Esonero_mensile × 12
```

**Tetto de minimis**: la Decontribuzione Sud entra nel calcolo de minimis aziendale (soglia generale 300.000 EUR in 3 anni). Per PMI con altri aiuti de minimis attivi, verificare la capienza residua.

---

### 4.4 Incentivo assunzione persone con disabilità

**Riferimento normativo**: art. 13 L. 68/1999 (come modificato da interventi successivi) + eventuali bandi INPS/fondi strutturali regionali.

**Condizioni**:
- Assunzione volontaria (eccedente l'obbligo di quota ex L. 68/1999) o rientrante nell'obbligo ma con convenzione con Centro per l'Impiego
- Persona con invalidità riconosciuta ≥ 67% (contributo maggiorato) o tra 46-66% (contributo base)
- Contratto a tempo indeterminato

**Agevolazione** (struttura base ex art. 13 L. 68/1999):
- Invalidità ≥ 67%: contributo mensile pari al **70% della RAL mensile lorda** per 36 mesi; poi **35%** per i successivi 24 mesi (in caso di assunzione a tempo indeterminato)
- Invalidità tra 46-66%: contributo mensile pari al **35% della RAL mensile lorda** per 36 mesi
- Invalidità < 46%: nessun contributo ex art. 13 (ma possono esistere incentivi regionali — segnalare di verificare)
- I contributi sono erogati dall'INPS previa domanda al fondo regionale per l'occupazione dei disabili

**Nota**: i valori sono orientativi — le aliquote effettive variano per anno e sono soggette a disponibilità del fondo regionale. Sempre verificare con il consulente del lavoro.

---

### 4.5 Apprendistato professionalizzante — riduzione strutturale

**Riferimento normativo**: art. 47 D.Lgs. 81/2015 (Codice dei contratti) + art. 1 c. 773 L. 296/2006 per l'aliquota ridotta.

**Condizioni**:
- Contratto di apprendistato professionalizzante (tipo II)
- Azienda con organico ≤ 9 dipendenti: aliquota contributiva datoriale ridotta al **1,5%** per i primi due anni, poi **3%** (invece della normale ~23-28%)
- Azienda con organico > 9 dipendenti: aliquota contributiva datoriale ridotta al **10%** per tutta la durata

**Durata apprendistato**: da 1 a 3 anni (definita dal CCNL applicabile)

**Calcolo risparmio**:
```
Aliquota standard (es. CCNL metalmeccanica): ~28%
Aliquota apprendistato (azienda ≤ 9 dip.): 1,5% (primo biennio)
Risparmio percentuale: ~26,5 punti percentuali sui contributi datoriali
Risparmio mensile = RAL_mensile × 26,5%
Risparmio totale biennio = Risparmio_mensile × 24
```

**Compatibilità**: l'apprendistato può cumularsi con la Decontribuzione Sud (la riduzione percentuale si applica sull'aliquota già ridotta dell'apprendistato). Non cumulabile con l'esonero under 36 (scegliere il più conveniente).

---

### 4.6 Incentivi regionali specifici

Esistono in quasi tutte le regioni incentivi aggiuntivi gestiti da enti regionali, Fondi FSE+ o agenzie del lavoro (es. bandi Garanzia Giovani regionali, incentivi per assunzione di NEET, borse lavoro, bonus per specifici settori in crisi).

**Comportamento standard di questa skill**: segnalare che esistono e consigliare una verifica tramite WebSearch aggiornata sul portale della regione di riferimento e sul sito ANPAL/GOL. Non calcolare il valore senza dati aggiornati — la variabilità è troppo alta.

Frase standard da includere nell'output:
> *"Per la regione [X], potrebbero esistere incentivi regionali aggiuntivi (FSE+, bandi Garanzia Giovani, incentivi NEET). Si consiglia di verificare sul portale [link regione] o tramite il Centro per l'Impiego competente. Un consulente del lavoro aggiornato sulla normativa regionale può identificare ulteriori opportunità non coperte da questa simulazione."*

---

## 5. Regole di cumulabilità

La gestione della non cumulabilità è il cuore della complessità di questa skill.

| Bonus A | Bonus B | Cumulabile? | Note |
|---|---|---|---|
| Esonero under 36 | Decontribuzione Sud | SI (su quote distinte) | Il 100% esonero under 36 assorbe già la quota contributiva — la Decontribuzione Sud porta un beneficio marginale; valutare quale conviene applicare in base a durata e massimale |
| Esonero under 36 | Esonero donne svantaggiate | NO | Applicare il più conveniente (tipicamente under 36 per durata 36 mesi vs 18 mesi donne) |
| Esonero under 36 | Apprendistato | NO | L'apprendistato ha già un regime contributivo agevolato — l'esonero under 36 si applica sul residuo se non si usa il regime apprendistato; in pratica: scegliere |
| Esonero donne svantaggiate | Decontribuzione Sud | SI (cumulo parziale) | Verificare massimali — la circolare INPS di riferimento definisce le quote; procedere con cautela |
| Decontribuzione Sud | Apprendistato | SI | Riduzione si applica sull'aliquota già ridotta dell'apprendistato |
| Incentivo disabili (art. 13 L. 68) | Esonero under 36 | NO | La L. 68/1999 ha suo regime specifico — non si cumula |
| Incentivo disabili (art. 13 L. 68) | Decontribuzione Sud | Verificare | Normativa non univoca — sempre richiedere parere consulente del lavoro |
| Qualsiasi bonus | Incentivi regionali FSE+ | Verificare caso per caso | Ogni bando regionale definisce le proprie regole di cumulo |

**Regola generale**: in caso di dubbio sulla cumulabilità, applicare il bonus singolo più vantaggioso e segnalare che la verifica spetta al consulente del lavoro tramite interpello o circolare INPS.

---

## 6. Workflow di calcolo — step operativi

### Step 1 — Raccolta dati
Raccogliere tutte le variabili indicate nella Sezione 3. Se mancanti, procedere con ipotesi esplicite (es. "ipotizzo RAL di 28.000 EUR — aggiornare con la RAL effettiva").

### Step 2 — Screening ammissibilità
Per ogni bonus del catalogo (Sezioni 4.1-4.6), verificare se le condizioni soggettive e oggettive sono soddisfatte. Produrre una matrice SI / NO / VERIFICARE.

### Step 3 — Calcolo per ogni bonus ammissibile
Per ogni bonus ammissibile, calcolare:
- Contributi datoriali mensili stimati (RAL mensile × aliquota datoriale del CCNL applicabile)
- Esonero mensile applicabile (considerando massimali)
- Durata in mesi
- Risparmio totale stimato (EUR)
- Risparmio equivalente in % del costo del lavoro totale previsto

### Step 4 — Analisi cumulabilità e selezione ottimale
Applicare la matrice di Sezione 5. Se più bonus sono ammissibili e non cumulabili, confrontare i risparmii totali e raccomandare il più conveniente. Se cumulabili, calcolare il beneficio combinato.

### Step 5 — Output simulazione
Produrre la tabella di simulazione (Sezione 7) e la checklist adempimenti (Sezione 8).

---

## 7. Formato output — tabella di simulazione

Per ogni assunzione analizzata, produrre:

### Tabella 1 — Screening ammissibilità

| Bonus | Ammissibile? | Condizione critica | Note |
|---|---|---|---|
| Esonero under 36 | SI / NO / VERIFICARE | [condizione bloccante se NO] | |
| Esonero donne svantaggiate | SI / NO / VERIFICARE | | |
| Decontribuzione Sud | SI / NO / VERIFICARE | | |
| Incentivo disabili | SI / NO / VERIFICARE | | |
| Apprendistato | SI / NO / VERIFICARE | | |
| Incentivi regionali | VERIFICARE | Consultare CPI e portale regione | |

### Tabella 2 — Simulazione numerica per bonus

| Bonus | % Esonero | Massimale mensile (EUR) | Durata (mesi) | Esonero mensile stimato (EUR) | Risparmio totale stimato (EUR) |
|---|---|---|---|---|---|
| Esonero under 36 | 100% | 500 | 36 | xxx | xxx |
| Decontribuzione Sud | 30% | nessuno | continuativo | xxx | xxx (3 anni) |
| ... | | | | | |

### Tabella 3 — Confronto e raccomandazione

| Scenario | Bonus applicati | Risparmio totale (EUR) | Note |
|---|---|---|---|
| Scenario A — bonus singolo ottimale | [nome bonus] | xxx | |
| Scenario B — combinazione cumulabile | [bonus 1 + bonus 2] | xxx | |
| Scenario C — alternativa se cambio profilo | [es. apprendistato] | xxx | |

**Raccomandazione**: indicare in modo esplicito quale scenario conviene e perché. Esempio:
> *"Con RAL 30.000 EUR e sede in Calabria, lo Scenario A (Esonero under 36) genera un risparmio di 16.200 EUR in 36 mesi (450 EUR/mese × 36). Lo Scenario B aggiunge la Decontribuzione Sud sul residuo per ulteriori ~2.400 EUR. La combinazione A+B è la strategia ottimale se il consulente del lavoro conferma la cumulabilità nel regime corrente."*

---

## 8. Esempi numerici concreti

### Esempio 1 — Esonero under 36, azienda Nord Italia

**Caso**: PMI manifatturiera a Milano (CCNL Metalmeccanici industria). Assume Marco, 28 anni, mai assunto a tempo indeterminato in precedenza. Contratto a tempo indeterminato full-time. RAL: 32.000 EUR.

**Dati contributivi**:
- Aliquota contributiva datoriale CCNL metalmeccanici (indicativa): ~28% sulla retribuzione imponibile previdenziale
- Contributi datoriali mensili: 32.000 / 12 × 28% = 746 EUR/mese

**Calcolo esonero under 36**:
- Esonero: 100% dei contributi datoriali, massimale 500 EUR/mese
- Esonero applicabile: MIN(746; 500) = **500 EUR/mese**
- Durata: 36 mesi
- **Risparmio totale: 500 × 36 = 18.000 EUR**

**In percentuale**: risparmio di 18.000 EUR su un costo del lavoro totale lordo di circa 128.000 EUR (RAL + contributi + TFR, 36 mesi) = **14% di riduzione del costo del lavoro**

---

### Esempio 2 — Decontribuzione Sud, azienda Campania

**Caso**: PMI commerciale a Napoli (CCNL Commercio). Assume Giulia, 42 anni, occupata. Contratto a tempo indeterminato part-time 50%. RAL full-time equivalente: 26.000 EUR; RAL effettiva part-time 50%: 13.000 EUR.

**Dati contributivi**:
- Aliquota contributiva datoriale CCNL Commercio (indicativa): ~27% sulla retribuzione imponibile
- Contributi datoriali mensili (su RAL part-time): 13.000 / 12 × 27% = **292 EUR/mese**

**Calcolo Decontribuzione Sud (fase 2021-2025)**:
- Esonero: 30% dei contributi datoriali
- Esonero mensile: 292 × 30% = **88 EUR/mese**
- Durata: continuativa (fino a fine regime, poi riduzione al 20% e 10%)
- **Risparmio anno 1-5: 88 × 12 × 5 = 5.280 EUR** (stimato al 30% per il quinquennio completo)
- **Risparmio anno 6-7 (20%): 59 × 12 × 2 = 1.416 EUR**
- **Risparmio anno 8-9 (10%): 29 × 12 × 2 = 702 EUR**
- **Risparmio totale 9 anni stimato: ~7.400 EUR** (calcolato sulla RAL invariata; aggiornare se la RAL cambia)

*Giulia non soddisfa il requisito under 36, quindi l'esonero under 36 non si applica. La Decontribuzione Sud è l'unico bonus disponibile in questo profilo.*

---

### Esempio 3 — Confronto under 36 vs apprendistato, azienda Sud

**Caso**: PMI edile a Bari (CCNL Edili industria). Deve assumere Luca, 24 anni, prima esperienza lavorativa. Due opzioni: (A) contratto a tempo indeterminato con esonero under 36 + Decontribuzione Sud; (B) apprendistato professionalizzante.

**Ipotesi**: RAL equivalente 24.000 EUR. Organico aziendale: 7 dipendenti. Aliquota datoriale CCNL edili: ~31%.

**Opzione A — Tempo indeterminato + Esonero under 36**:
- Contributi datoriali mensili: 24.000 / 12 × 31% = 620 EUR/mese
- Esonero under 36 (100%, cap 500 EUR): 500 EUR/mese × 36 mesi = **18.000 EUR**
- Decontribuzione Sud applicabile sul residuo (contributi non coperti dall'esonero under 36 = 120 EUR/mese): 120 × 30% = 36 EUR/mese × 36 mesi = 1.296 EUR
- **Totale Opzione A (36 mesi): 19.296 EUR**

**Opzione B — Apprendistato professionalizzante (azienda ≤ 9 dip.)**:
- Aliquota apprendistato primo biennio: 1,5%
- Contributi datoriali mensili con apprendistato: 24.000 / 12 × 1,5% = 30 EUR/mese
- Risparmio vs aliquota piena (620 EUR): **590 EUR/mese** × 24 mesi (biennio) = 14.160 EUR
- Terzo anno (aliquota 3%): 24.000 / 12 × 3% = 60 EUR/mese; risparmio: 560 EUR/mese × 12 mesi = 6.720 EUR
- Decontribuzione Sud sull'aliquota apprendistato (30% di 30 EUR): 9 EUR/mese — irrisorio
- **Totale Opzione B (36 mesi): ~20.880 EUR**

**Raccomandazione Esempio 3**:
> *"L'Opzione B (apprendistato) genera un risparmio totale stimato di circa 20.880 EUR in 36 mesi, superiore all'Opzione A (19.296 EUR). Il vantaggio è però marginale (~1.600 EUR) e l'apprendistato comporta oneri aggiuntivi (piano formativo, tutor aziendale, obbligo di stabilizzazione minima). Se l'obiettivo è la massima semplicità gestionale, l'Opzione A con esonero under 36 è preferibile. Se l'azienda vuole investire sulla formazione del giovane con percorso certificato, l'Opzione B ha senso. Decidere insieme al consulente del lavoro."*

---

### Esempio 4 — Donna disoccupata 26 mesi, azienda Roma

**Caso**: Studio professionale a Roma. Assume Sara, 38 anni, disoccupata da 26 mesi (oltre i 24 mesi richiesti). Contratto a tempo indeterminato full-time. RAL: 28.000 EUR. Settore: servizi professionali (non manifatturiero).

**Verifica ammissibilità**:
- Esonero under 36: NO (Sara ha 38 anni)
- Esonero donne svantaggiate: SI (disoccupata da oltre 24 mesi)
- Decontribuzione Sud: NO (Roma non è regione ammessa)

**Calcolo esonero donne svantaggiate**:
- Aliquota datoriale stimata (CCNL Studi professionali, orientativa): ~26%
- Contributi datoriali mensili: 28.000 / 12 × 26% = 607 EUR/mese
- Esonero: 100%, massimale 671 EUR/mese
- Esonero applicabile: MIN(607; 671) = **607 EUR/mese** (non raggiunge il massimale)
- Durata: 18 mesi (contratto a tempo indeterminato)
- **Risparmio totale: 607 × 18 = 10.926 EUR**

*In percentuale: 10.926 EUR su un costo del lavoro lordo stimato di ~80.000 EUR nei 18 mesi = risparmio del 13,7%.*

---

## 9. Checklist adempimenti

Per ogni bonus attivato, verificare e completare i seguenti adempimenti. **La responsabilità di esecuzione è del consulente del lavoro abilitato.**

### Prima dell'assunzione

- [ ] Verificare lo stato occupazionale del lavoratore (DID — Dichiarazione di Immediata Disponibilità, stato NASpI, estratto contributivo INPS)
- [ ] Verificare che il lavoratore non abbia avuto precedenti contratti a tempo indeterminato (per esonero under 36): richiesta dichiarazione al lavoratore + verifica estratto contributivo
- [ ] Verificare la regolarità DURC aziendale
- [ ] Verificare assenza di licenziamenti collettivi o per GMO negli ultimi 6 mesi nella stessa unità produttiva per la stessa qualifica
- [ ] Per esonero donne svantaggiate: verificare i requisiti di disoccupazione tramite dichiarazione della lavoratrice e CPI competente
- [ ] Per incentivo disabili: acquisire verbale di invalidità o certificazione L. 68/1999 in corso di validità
- [ ] Per apprendistato: predisporre il Piano Formativo Individuale (PFI) e individuare il tutor aziendale

### Comunicazione preventiva e domanda

- [ ] **Comunicazione obbligatoria di assunzione (UNILAV)**: da inviare al Centro per l'Impiego entro il giorno antecedente l'assunzione (non oltre le ore 24.00)
- [ ] Per esonero under 36 e esonero donne svantaggiate: esposizione del beneficio nel flusso **UNIEMENS mensile** (codice di esonero appropriato nel campo <CodiceEsonero>) — nessuna domanda preventiva separata, ma corretta codifica obbligatoria
- [ ] Per incentivo disabili ex art. 13 L. 68/1999: **domanda preventiva al fondo regionale** per l'occupazione dei disabili tramite portale INPS — da presentare prima dell'assunzione o entro i termini previsti dalla circolare INPS
- [ ] Per Decontribuzione Sud: esposizione nel flusso UNIEMENS con codice specifico — verificare circolare INPS aggiornata per l'anno di competenza
- [ ] Per apprendistato: comunicazione al CPI e registrazione del PFI; in alcune regioni è necessaria la comunicazione alla Regione/Provincia

### Durante il rapporto di lavoro

- [ ] Mantenere la regolarità DURC per tutta la durata del beneficio
- [ ] Non effettuare licenziamenti collettivi o per GMO nella stessa unità produttiva per la stessa qualifica (condizione di mantenimento)
- [ ] Verificare mensilmente la corretta esposizione del codice esonero in UNIEMENS
- [ ] Per apprendistato: rispettare il piano formativo e rendicontare le ore di formazione
- [ ] Conservare tutta la documentazione probatoria (estratti contributivi, dichiarazioni lavoratore, PFI, verbali di invalidità)

### Scadenze critiche

| Adempimento | Scadenza | Conseguenza se omesso |
|---|---|---|
| UNILAV assunzione | Giorno antecedente l'assunzione | Sanzione amministrativa; possibile decadenza dall'esonero |
| UNIEMENS con codice esonero | Entro il mese di competenza | Perdita del beneficio per il mese; possibile recupero con flusso di variazione |
| Domanda incentivo disabili | Prima o all'assunzione (verificare circolare INPS) | Decadenza dal beneficio per il periodo non coperto |
| Rendicontazione apprendistato | Secondo calendario regionale | Perdita del contratto agevolato + possibile conversione forzata |

---

## 10. Condizioni di decadenza e rischi di revoca

Segnalare sempre al cliente. Queste sono le principali cause di recupero del beneficio da parte di INPS:

**Cause di decadenza immediata**:
1. **Licenziamento del lavoratore incentivato** entro i termini previsti (normalmente entro la durata dell'esonero o entro 12 mesi dall'assunzione, a seconda del bonus) senza giusta causa o giustificato motivo oggettivo riconosciuto — obbligo di restituzione integrale dell'esonero goduto.
2. **Licenziamenti collettivi o per GMO** effettuati nella stessa unità produttiva per la stessa qualifica nei 6 mesi precedenti l'assunzione incentivata (condizione retrospettiva da verificare prima di assumere).
3. **DURC irregolare**: se l'azienda risulta irregolare durante il periodo di godimento, il beneficio è sospeso e potenzialmente recuperato.
4. **Esposizione errata o omessa in UNIEMENS**: contestazione INPS in sede di verifica ispettiva.

**Cause di decadenza parziale**:
5. **Riduzione dell'orario di lavoro** senza proporzionale riduzione del massimale dichiarato (rischio di indebita percezione del massimale full-time).
6. **Trasformazione del contratto** in modi non previsti dall'agevolazione (es. distacco improprio, trasferimento d'azienda con interruzione del rapporto).
7. **Superamento del plafond de minimis** aziendale nel triennio — particolarmente rilevante per la Decontribuzione Sud.

**Gestione del rischio**:
> *"Consigliare al cliente di istituire un fascicolo assunzione per ogni lavoratore incentivato, con tutta la documentazione probatoria, e di effettuare un controllo semestrale con il consulente del lavoro sulla corretta esposizione in UNIEMENS."*

---

## 11. Limitazioni e avvertenze finali

1. **Normativa in evoluzione**: i bonus assunzioni sono prorogati anno per anno dalla Legge di Bilancio. I massimali, le aliquote e la durata possono cambiare. Questa skill rispecchia il regime normativo alla data di aggiornamento — **verificare sempre la Legge di Bilancio dell'anno di assunzione**.

2. **Autorizzazione UE**: alcuni esoneri (in particolare l'esonero donne svantaggiate e la Decontribuzione Sud) sono subordinati ad autorizzazione della Commissione Europea ai sensi del Regolamento GBER o de minimis. In caso di revoca dell'autorizzazione, l'esonero cessa — monitorare le comunicazioni INPS.

3. **Aliquote contributive variabili**: le aliquote datoriali usate negli esempi sono indicative e variano per CCNL, qualifica, anzianità aziendale e altre variabili. Il calcolo preciso deve essere effettuato dal consulente del lavoro sul cedolino effettivo.

4. **Incentivi regionali non inclusi**: questa skill non copre il catalogo completo dei bandi regionali FSE+ e degli incentivi locali, che variano per regione e finestra temporale. Si raccomanda verifica separata.

5. **Questo è supporto decisionale, non consulenza previdenziale**: la presentazione della domanda, la gestione del flusso UNIEMENS, la verifica dei requisiti e la responsabilità degli adempimenti spettano esclusivamente a un **consulente del lavoro iscritto all'Albo** ai sensi della L. 12/1979.

---

## 12. Connessioni con altre skill

**Invocata da**:
- `flusso-agevolazioni-pmi` — Step 4 (stima benefici) quando sono previste assunzioni nel piano investimenti del cliente

**Si appoggia a**:
- `fiscale-tributario-italiano` — per i profili fiscali dei benefici contributivi (deducibilità, impatto IRAP, trattamento in bilancio)
- WebSearch — per verifica aggiornata di incentivi regionali specifici, stato autorizzazioni UE, circolari INPS recenti

**Produce input per**:
- `flusso-agevolazioni-pmi` — il risparmio contributivo stimato confluisce nella simulazione benefici complessiva (Step 4 dell'orchestratore)
- `budget-forecast-pmi` — il risparmio sul costo del lavoro entra nel modello previsionale
