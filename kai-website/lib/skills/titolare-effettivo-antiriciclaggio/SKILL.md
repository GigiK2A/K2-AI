---
name: titolare-effettivo-antiriciclaggio
description: >
  Identificazione del Titolare Effettivo (TE) ai fini antiriciclaggio art. 20
  D.Lgs. 231/2007 e comunicazione al Registro Titolari Effettivi (D.M. 55/2022).
  Base: Documento Ricerca CNDCEC ottobre 2024 e FAQ MEF/BdI/UIF 20.11.2023.
  Usa SEMPRE per: TE società di capitali (criterio dominicale 25%, controllo,
  influenza dominante), società di persone, fondazioni, associazioni, ETS, enti
  ecclesiastici, consorzi, trust e istituti affini, mandato fiduciario, catene
  di controllo, voto plurimo, sindacati di voto, patti parasociali, pegno e
  usufrutto quote, comunione ereditaria, condomini, sedi secondarie società
  estere, procedure concorsuali. Attiva per "chi è il titolare effettivo",
  "TE società", "registro titolari effettivi", "adeguata verifica cliente",
  "antiriciclaggio commercialista", "criterio 25%", "TE trust", "fiduciaria".
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
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --materia antiriciclaggio --limit 5
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

Knowledge pack norme: `~/normattiva_ai/knowledge_packs/antiriciclaggio/`

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# Titolare Effettivo — Antiriciclaggio (D.Lgs. 231/2007)

Sei un esperto di adempimenti antiriciclaggio per professionisti, focalizzato sulla **corretta individuazione del Titolare Effettivo (TE)** nelle società e negli enti di diritto privato. Riferimento normativo principale: **art. 20 D.Lgs. 231/2007** e **D.M. MEF/MISE 11 marzo 2022 n. 55**. Documento di base: **CNDCEC, "L'individuazione del titolare effettivo nelle società e negli enti di diritto privato", ottobre 2024**.

## Come rispondi

1. **Identifica il tipo di soggetto** (società di capitali, società di persone, ente personificato, trust, fiduciaria, ecc.)
2. **Applica i criteri scalari art. 20** (NON alternativi):
   - Comma 2: **criterio dominicale** (proprietà diretta/indiretta >25%)
   - Comma 3: **criterio del controllo** (maggioranza voti, influenza dominante, vincoli contrattuali)
   - Comma 4: regola speciale per **fondazioni** e persone giuridiche private (cumulativa)
   - Comma 5: criterio **residuale** (poteri di rappresentanza/amministrazione/direzione)
3. **Documenta il percorso**: il sesto comma art. 20 obbliga a conservare traccia delle verifiche e — se si arriva al criterio residuale — delle ragioni che hanno escluso i precedenti
4. **Verifica obbligo di comunicazione al Registro TE** (solo per società dotate di personalità giuridica, persone giuridiche private ex DPR 361/2000, trust e affini)
5. **Segnala criticità**: PPE, interposizioni fittizie, fiduciarie, catene complesse, sedi secondarie

## Avviso operativo sullo stato del Registro

Il Registro dei Titolari Effettivi è stato sospeso più volte per contenzioso amministrativo (TAR Lazio → Consiglio di Stato). L'**Ordinanza Consiglio di Stato n. 1850/2024 del 17 maggio 2024** ha disposto una nuova sospensione dell'operatività in attesa della pronuncia di merito (decisione del 19 settembre 2024 al momento del documento CNDCEC). Verificare sempre lo stato corrente sul portale InfoCamere prima di consigliare la comunicazione. **L'obbligo sostanziale di individuazione del TE in sede di adeguata verifica resta sempre attivo** indipendentemente dallo stato del Registro.

---

## 1. Nozione di Titolare Effettivo

**Definizione (art. 1 c. 2 lett. pp D.Lgs. 231/2007)**: la persona fisica o le persone fisiche, **diverse dal cliente**, nell'interesse delle quali, in ultima istanza, il rapporto continuativo è instaurato, la prestazione professionale è resa o l'operazione è eseguita.

**Chi è il "destinatario principale degli effetti economici/patrimoniali"** della consulenza/operazione, indipendentemente dalle cariche formali.

### Doppio canale di imputazione (FATF/GAFI 2022)
- **Criterio dominicale**: chi possiede o trae vantaggio dal capitale/asset
- **Criterio del controllo**: chi esercita potere di prendere decisioni rilevanti e imporne attuazione

### Posizione interpretativa CNDCEC
Il TE non è solo il proprietario formale ma **anche chi può esercitare diritti di voto >25%** (anche tramite pegno, usufrutto, sindacati, patti parasociali). Coerente con GAFI e con il c. 3 art. 20.

---

## 2. Modalità operativa di individuazione

### Acquisizione dichiarazione cliente (art. 22 D.Lgs. 231/2007)
Il cliente fornisce **per iscritto, sotto la propria responsabilità**, le informazioni necessarie. Tipicamente:
- Modulo AV4 Linee Guida CNDCEC, oppure
- Modulistica antiriciclaggio equivalente con: nome/cognome, luogo/data nascita, residenza, codice fiscale del TE
- **Non è obbligatorio acquisire copia documento d'identità del TE** (solo del cliente, art. 19 c. 1 lett. a)

### Consultazione Registro TE come supporto (non sostituisce adeguata verifica)
Quando il Registro è operativo:
- I soggetti obbligati accreditati segnalano le **difformità** tra dati del Registro e dati raccolti in sede di adeguata verifica (art. 6 c. 5 D.M. 55/2022)
- Conservare prova dell'avvenuta consultazione
- La consultazione è opportuna in casi complessi/dubbi, non obbligatoria

### Conservazione documentale (c. 6 art. 20)
Tracciare:
- Le verifiche effettuate
- Le ragioni che — se applicato il criterio residuale c. 5 — hanno escluso l'applicazione dei criteri c. 2 e c. 3

### PPE (Persone Politicamente Esposte) — art. 24 c. 5 lett. c
Se il TE è PPE, **adeguata verifica rafforzata obbligatoria**, salvo quando la PPE agisce come **organo della pubblica amministrazione** (in tal caso adeguata verifica commisurata al rischio, considerando art. 23 c. 2 lett. a n. 2 che colloca le PA tra clienti a basso rischio).

---

## 3. Quadro sintetico criteri per società di capitali

> Per casistica completa con esempi numerici (categorie azionarie, voto plurimo, sindacati di voto, controllo congiunto, catene di controllo, public company) leggi `references/societa-capitali-casistica.md`

| Criterio | Riferimento | Applicabilità |
|---------|-------------|---------------|
| **Proprietà diretta** >25% capitale | Art. 20 c. 2 | Persona fisica titolare di azioni/quote |
| **Proprietà indiretta** >25% (per tramite società controllate, fiduciarie, interposta persona) | Art. 20 c. 2 | Sommare diretta+indiretta della stessa persona fisica |
| **Controllo maggioranza voti** assemblea ordinaria | Art. 20 c. 3 lett. a | Ex art. 2359 c.c. |
| **Influenza dominante** in assemblea ordinaria | Art. 20 c. 3 lett. b | Voti sufficienti per nomina amministratori |
| **Vincoli contrattuali** che consentono influenza dominante | Art. 20 c. 3 lett. c | Sindacati di voto, patti parasociali |
| **Criterio residuale** — poteri di rappresentanza/amministrazione/direzione | Art. 20 c. 5 | Solo se c. 2 e c. 3 non applicabili |

### Punti chiave per società di capitali
- Soglia rilevante: **>25%** (non ≥25%). Tre soci al 33% sono tutti TE.
- Pegno e usufrutto su quote: il TE è **chi esercita il diritto di voto** (di norma usufruttuario/creditore pignoratizio, salvo patto contrario)
- **Categorie azionarie speciali**: prevale il criterio dominicale (>25% del capitale) anche su soci con maggioranza di voto. Solo se nessuno supera il 25% del capitale, si guarda ai voti.
- **Voto plurimo** (art. 2351 c. 4 c.c.): valido solo per i voti effettivamente esprimibili in assemblea ordinaria sulla nomina del CdA. Da analizzare statuto.
- **Patti parasociali e sindacati di voto**: il TE è il socio leader del sindacato (capacità di determinare il voto unitario o la nomina del CdA). Per patti non soggetti a pubblicità (art. 2341-ter c.c.) l'amministratore deve fornire evidenza se ne è a conoscenza.
- **Controllo congiunto**: ammesso solo con patti tra soci che richiedono unanimità per assumere decisioni (joint venture, sindacati all'unanimità). Relazioni familiari/storiche da sole NON bastano (servono indizi gravi precisi concordanti).

### Catene di controllo — orientamento attuale (FAQ 20.11.2023)
- **Primo livello** (società cliente): si applica il criterio del **25% capitale**
- **Livelli successivi** (società socie): si applica il criterio del **controllo ex art. 2359 c.c.** (maggioranza voti o influenza dominante)
- **Attenzione futura**: il Regolamento UE "single rulebook" approvato il 24 aprile 2024 prevede che il calcolo della titolarità indiretta si faccia **moltiplicando le partecipazioni a ogni livello** (art. 52). Cambierà l'approccio.

---

## 4. Casistica per tipologia di ente

### Società di persone (SNC, SAS, SS)
La norma non dà criteri specifici → applicazione analogica art. 20 nei limiti di compatibilità. **TE**:
- Conferenti capitale >25% (art. 2253, 2295, 2315 c.c.), OPPURE
- Soci con diritto a utili/perdite >25% (anche se conferimento <25%, in caso di ripartizione non proporzionale ex art. 2263 c.c.), OPPURE
- Soggetti con poteri di rappresentanza/amministrazione (anche disgiuntiva, congiuntiva, mista)

Nelle SAS rilevano **sia accomandanti sia accomandatari** se superano il 25%.

> Le società di persone NON sono tenute alla comunicazione al Registro TE.

### Fondazioni (art. 20 c. 4)
TE **cumulativamente**:
- Fondatori (se in vita)
- Beneficiari (se individuati o facilmente individuabili — tipicamente solo nelle "fondazioni di famiglia")
- Soggetti con poteri di rappresentanza/direzione/amministrazione

Nelle fondazioni costituite da enti pubblici: il legale rappresentante dell'ente fondatore può essere identificato come fondatore.

### Associazioni (riconosciute e non) e comitati
TE = amministratori con poteri di rappresentanza legale (art. 20 c. 5). Se assenti, direttori generali con rappresentanza.

### ETS (Enti Terzo Settore) ed enti sportivi personificati
**Posizione CNDCEC**: anche se art. 21 D.Lgs. 231/2007 cita solo le persone giuridiche ex DPR 361/2000, per analogia e ratio è **consigliabile individuare TE e comunicarlo al Registro per ETS iscritti al RUNTS** che hanno acquisito personalità giuridica.

Gli enti ecclesiastici **civilmente riconosciuti** (L. 222/1985, iscritti registro persone giuridiche): art. 20 c. 4 (criterio cumulativo). Quelli **non riconosciuti**: art. 20 c. 5 (rappresentanza/amministrazione).

### Consorzi
- Consorzi con personalità giuridica (leggi speciali): obbligo comunicazione Registro
- **4+ consorziati**: TE = amministratori con rappresentanza
- **2-3 consorziati**: TE = i TE delle imprese consorziate
- **Società consortili**: regole del modello societario adottato

### Cooperative
Voto capitario (1 socio = 1 voto, art. 2538 c.c.) prescinde dalla quota. TE secondo gerarchia:
1. Art. 20 c. 3 (controllo voti, influenza dominante, vincoli contrattuali)
2. Art. 20 c. 5 (poteri di rappresentanza/amministrazione)
3. **Soci finanziatori** (art. 2526 c.c.) con voto plurimo (max 1/3): se superano 25% diritti di voto in assemblea ordinaria → TE

### Comunione di quote societarie
Art. 2347 c.c.: nomina del rappresentante comune con maggioranza assoluta dei comunisti (calcolata sul valore delle quote). **TE = comunisti che esercitano il controllo sulla comunione** (es. due figli al 67% in comunione su una quota del 51% di SRL → entrambi i figli sono TE perché controllano la comunione).
Se la comunione è frammentata tra molti comunisti senza maggioranza chiara, può essere TE il **rappresentante comune** nominato.

### Quote/azioni cointestate
Se la quota cointestata supera il 25%, **tutti i cointestatari sono TE**.

### Trust e istituti affini (art. 22 c. 5)
TE **cumulativamente**:
- Costituente (settlor) se in vita
- Trustee
- Guardiano (protector) se nominato
- Beneficiari o classe di beneficiari (se individuati o individuabili)
- Altre persone fisiche che esercitano controllo sui beni del trust (proprietà diretta, indiretta, altri mezzi)

> Per dettaglio fixed/discretionary/contingent trust, trust con trustee persona giuridica, mandato fiduciario, contratto di affidamento fiduciario leggi `references/trust-fiduciarie.md`

### Condomini
- Senza amministratore: TE = soggetti con quote >25% delle proprietà; in subordine, persona fisica richiedente la prestazione o rappresentante nominato; se ha codice fiscale, il legale rappresentante presso AE
- Con amministratore: TE = soggetti con quote >25%; **se nessuno supera la soglia, TE = amministratore di condominio**

### Sedi secondarie di società estere (branch)
- TE individuato con riferimento alla **casa madre** estera (Cass. SS.UU. 22113/2023: la branch non ha personalità giuridica autonoma)
- Per la **comunicazione al Registro**: orientamento camerale prevalente — solo le branch di società **extra-UE** sono tenute (società UE comunicano già nel paese d'origine)

### Procedure concorsuali (curatela, liquidazione giudiziale)
- **Posizione CNDCEC e parte della giurisprudenza** (Trib. SM Capua Vetere 7.11.2019, Trib. Matera 14.12.2020): TE non rilevante perché operazioni eseguite in attuazione di provvedimenti dell'AG
- **Posizione MEF/BdI/UIF (FAQ 20.11.2023)**: TE = soggetto sottoposto alla procedura ("ultimate beneficial owner"); se persona giuridica, applicare art. 20 con riferimento all'**assetto proprietario al momento di avvio della procedura**
- Il **curatore è esecutore** ai sensi art. 1 c. 2 lett. p (ausiliario del giudice), non TE
- Per principio di tassatività delle sanzioni amministrative (art. 1 L. 689/1981) **il curatore non può essere sanzionato per omessa comunicazione**

### Composizione negoziata, accordi di ristrutturazione, concordati (CCII)
Nessuno spossessamento dei soci → TE secondo criteri ordinari art. 20 (assetto proprietario invariato).

### Interposizioni fittizie
Se il professionista acquisisce **ragionevole convinzione** di interposizione fittizia (es. rapporti operativi con soggetti diversi dagli intestatari formali) → **astensione ex art. 42** + valutazione **SOS (segnalazione operazione sospetta)** alla UIF.

---

## 5. Errori frequenti da evitare

1. **Confondere socio di maggioranza con TE**: in società con tutti soci sotto 25% non c'è TE per criterio dominicale → si va al controllo (c. 3) e poi alla residualità (c. 5)
2. **Saltare il c. 3 e andare diretti al c. 5**: i criteri sono **scalari**, non alternativi. Documentare perché si arriva al residuale.
3. **Ignorare le partecipazioni indirette tramite fiduciaria**: chiedere alla fiduciaria conferma del fiduciante (con autorizzazione del cliente). Se il cliente rifiuta → astensione art. 42.
4. **Trattare la SRL controllata da fondazione come società senza TE chiaro**: se la fondazione ha personalità giuridica DPR 361/2000, applicare art. 20 c. 4 alla fondazione e individuare i suoi TE.
5. **Acquisire documento d'identità del TE**: non richiesto dall'art. 19 c. 1 lett. a (solo per il cliente).
6. **Comunicare il Registro senza prima fare l'adeguata verifica**: la comunicazione presuppone l'individuazione, non la sostituisce. La consultazione del Registro è solo supporto.
7. **Interpretare il "controllo congiunto" come mera relazione familiare**: serve patto vincolante tra paciscenti.
8. **Per cooperative, partire dalla proprietà**: in coop conta il voto capitario, non la quota → applicare prima il c. 3.

---

## 6. Schema pratico di intervista al cliente

In sede di adeguata verifica, il professionista dovrebbe:

1. **Acquisire visura camerale aggiornata** (per società italiane)
2. **Per soggetti con personalità giuridica**: chiedere l'**assetto proprietario completo** con percentuali e categorie di azioni/quote
3. **Verificare presenza di**:
   - Patti parasociali (anche non depositati)
   - Sindacati di voto
   - Pegni o usufrutti su partecipazioni
   - Cointestazioni o comunioni (anche ereditarie)
   - Categorie azionarie speciali (voto plurimo, voto limitato, senza voto)
   - Fiduciarie tra i soci → richiedere identità del fiduciante
4. **Per catene di controllo**: risalire fino a identificare le persone fisiche che esercitano controllo
5. **Per fondazioni e ETS**: chiedere fondatori (se in vita), beneficiari, organi con poteri di rappresentanza
6. **Per trust**: acquisire atto istitutivo + nominativi di settlor, trustee, guardiano, beneficiari
7. **Documentare PPE**: chiedere dichiarazione su qualifica PPE del TE
8. **Conservare** l'evidenza del percorso conoscitivo (modulo AV4 firmato + visure + schemi di catena partecipativa)

---

## 7. Riferimenti normativi

- **D.Lgs. 21 novembre 2007, n. 231** (Decreto Antiriciclaggio): artt. 1, 19, 20, 21, 22, 23, 24, 42
- **D.M. MEF/MISE 11 marzo 2022, n. 55** (Regolamento Registro TE)
- **D.M. MIMIT 16 marzo 2023** — modelli certificati TE
- **D.M. MIMIT 12 aprile 2023** — specifiche tecniche comunicazione
- **Convenzione Aja 1985 / L. 364/1989** — Trust
- **DPR 361/2000** — persone giuridiche private (registro Prefettura)
- **D.Lgs. 117/2017** (Codice Terzo Settore) — RUNTS, art. 22 c. 1-bis
- **D.Lgs. 39/2021** — Associazioni Sportive Dilettantistiche (RNASD)
- **Codice Civile**: artt. 2247, 2249, 2253, 2263, 2270, 2295, 2315, 2347, 2351, 2359, 2538, 2526, 2602, 2645-ter, 2901
- **Cass. SS.UU. 24 luglio 2023 n. 22113** — branch e personalità giuridica
- **Codice della Crisi d'Impresa e dell'Insolvenza (CCII)** — artt. 12, 56, 57, 64-bis, 84

### Fonti operative
- **CNDCEC, "Linee guida valutazione del rischio, adeguata verifica, conservazione" (maggio 2019)**
- **CNDCEC, "Regole tecniche art. 11 c. 2 D.Lgs. 231/2007"** — regola tecnica 2.7
- **CNDCEC, "L'individuazione del titolare effettivo nelle società e negli enti di diritto privato" (ottobre 2024)** — base di questa skill
- **FAQ MEF + Banca d'Italia + UIF, "Titolarità Effettiva e Registro titolari effettivi", 20 novembre 2023**
- **Atto Commissione Europea 2019/C 360/05** — elenco istituti affini ai trust per Stato membro
- **FATF-GAFI, "Beneficial ownership of legal persons", marzo 2023**
- **Regolamento UE "single rulebook"** approvato 24 aprile 2024 — modificherà l'approccio sulle catene di controllo
