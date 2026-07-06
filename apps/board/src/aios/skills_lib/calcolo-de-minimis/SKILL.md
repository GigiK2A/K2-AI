---
name: calcolo-de-minimis
description: >-
  Skill foglia del sistema AgevolazioniBoost K2-AI dedicata al calcolo preciso del
  de minimis residuo disponibile per un'impresa. Verifica la capienza rispetto alla
  soglia di 300.000 EUR su tre esercizi finanziari consecutivi introdotta dal
  Regolamento UE 2023/2831, in vigore dal 1 gennaio 2024. La skill guida l'utente
  nella consultazione del Registro Nazionale Aiuti (RNA), nel calcolo
  dell'equivalente sovvenzione lordo (ESL) per strumenti non-fondo perduto, nella
  gestione dei casi speciali (imprese collegate, fusioni, startup, imprese in
  difficoltà) e nella produzione di un output strutturato JSON per
  l'orchestratore AgevolazioniBoost. Trasversale a tutti gli strumenti agevolativi
  che operano sotto regime de minimis. Errori nel calcolo comportano revoca
  dell'aiuto, restituzione con interessi e sanzioni amministrative.
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


# calcolo-de-minimis

## Identità e scopo

Skill foglia dedicata al calcolo preciso del de minimis residuo disponibile per
un'impresa. È trasversale a tutti gli strumenti agevolativi del sistema
AgevolazioniBoost: qualsiasi domanda di aiuto pubblico concesso sotto regime de
minimis richiede la preventiva verifica dello spazio disponibile nel plafond
triennale. Errori nel calcolo portano a revoca dell'aiuto, obbligo di
restituzione con interessi e sanzioni amministrative. Questa skill guida
l'operatore o l'orchestratore attraverso l'intero processo: dalla lettura del
RNA alla simulazione numerica, fino alla produzione dell'output JSON
standardizzato.

---

## Sezione 1 — Cos'è il de minimis e perché è critico

### Riferimento normativo aggiornato

Il quadro normativo di riferimento è il **Regolamento UE 2023/2831** della
Commissione europea, pubblicato in Gazzetta Ufficiale dell'UE il 13 dicembre
2023 ed entrato in vigore il **1° gennaio 2024**. Ha sostituito integralmente
il precedente Reg. (UE) n. 1407/2013.

> AGGIORNAMENTO CRITICO: la nuova soglia è 300.000 EUR in tre esercizi
> finanziari consecutivi. La vecchia soglia era 200.000 EUR. Gli aiuti
> concessi sotto il Reg. 1407/2013 prima del 1° gennaio 2024 continuano
> a essere contati nel plafond triennale con il loro valore originale.

### Razionale del regime

La Commissione europea considera che aiuti di importo limitato, concessi a
singole imprese, non siano idonei a falsare la concorrenza nel mercato interno
né a incidere sugli scambi tra Stati membri. Per questo motivo tali aiuti sono
esenti dall'obbligo di notifica preventiva alla CE previsto dall'art. 108(3)
TFUE. Lo Stato membro può concedere l'aiuto immediatamente, senza attendere
l'autorizzazione della Commissione.

Il meccanismo funziona solo se l'importo cumulato rimane sotto soglia. Se la
soglia viene superata, l'intero aiuto che determina il superamento — non solo
la parte eccedente — può essere dichiarato illegale e va restituito.

### Chi deve calcolare

Qualsiasi impresa che intende ricevere un aiuto concesso sotto il regime de
minimis. L'obbligo di verifica ricade formalmente sull'ente concedente, ma
nella pratica è l'impresa beneficiaria a dichiarare gli aiuti ricevuti e a
garantire la capienza del plafond. La falsa dichiarazione configura
responsabilità amministrativa e penale.

### Conseguenze del superamento della soglia

- L'aiuto che supera la soglia è illegale ai sensi del diritto UE degli aiuti
  di stato.
- L'ente concedente è obbligato a recuperarlo, con interessi calcolati al
  tasso di riferimento della CE dal momento della concessione.
- L'impresa può essere esclusa da futuri incentivi per un periodo determinato.
- In caso di aiuti regionali o nazionali con cofinanziamento UE, il recupero
  può estendersi a tutto il progetto.

---

## Sezione 2 — I 3 esercizi finanziari: come si contano

### Regola generale

Si considerano l'**esercizio finanziario corrente** (quello in cui viene
presentata la domanda o viene concesso l'aiuto) più i **due esercizi finanziari
precedenti**. Il riferimento è l'esercizio finanziario dell'impresa, non
l'anno solare.

### Esempio numerico — esercizio coincidente con anno solare

Domanda presentata il 15 luglio 2026. Esercizio finanziario coincide con anno
solare (1 gennaio - 31 dicembre).

| Esercizio | Periodo         | Da considerare |
|-----------|-----------------|----------------|
| 2026      | 01/01 - 31/12   | SI             |
| 2025      | 01/01 - 31/12   | SI             |
| 2024      | 01/01 - 31/12   | SI             |
| 2023      | 01/01 - 31/12   | NO             |

Finestra di osservazione: 1° gennaio 2024 - 15 luglio 2026.

### Esempio numerico — esercizio non coincidente con anno solare

Impresa con esercizio finanziario 1° luglio - 30 giugno. Domanda presentata
il 15 marzo 2026, che ricade nell'esercizio 1° luglio 2025 - 30 giugno 2026.

| Esercizio | Periodo                   | Da considerare |
|-----------|---------------------------|----------------|
| 2025-2026 | 01/07/2025 - 30/06/2026   | SI (corrente)  |
| 2024-2025 | 01/07/2024 - 30/06/2025   | SI             |
| 2023-2024 | 01/07/2023 - 30/06/2024   | SI             |
| 2022-2023 | 01/07/2022 - 30/06/2023   | NO             |

Finestra di osservazione: 1° luglio 2023 - 15 marzo 2026.

### Data di concessione vs data di erogazione

Attenzione critica: un aiuto de minimis si registra nell'esercizio in cui viene
**concesso** (data del provvedimento di concessione, delibera, decreto o
contratto), non nell'esercizio in cui viene **erogato** (accredito bancario).

Esempio: un contributo concesso con decreto del 20 novembre 2023 ma erogato
il 10 febbraio 2024 va imputato all'esercizio 2023, non al 2024. Se la finestra
di osservazione parte dal 1° gennaio 2024, questo aiuto NON rientra nel calcolo.

---

## Sezione 3 — Cosa conta nel de minimis e cosa no

### CONTA nel plafond de minimis

| Strumento                             | Come si conta                        | Nota                                    |
|---------------------------------------|--------------------------------------|-----------------------------------------|
| Contributo a fondo perduto de minimis | Importo nominale concesso            | Regime de minimis indicato nel decreto  |
| Finanziamento agevolato de minimis    | ESL (equivalente sovvenzione lordo)  | Differenziale tasso mercato/agevolato   |
| Garanzia de minimis                   | ESL calcolato sulla quota garantita  | Metodo safe harbour o calcolo effettivo |
| Tax credit concesso sotto de minimis  | Importo del credito d'imposta        | Verificare regime del singolo strumento |
| Riduzione di oneri fiscali de minimis | Valore dell'agevolazione fiscale     | Solo se il regime è de minimis          |

### NON CONTA nel plafond de minimis

- **Aiuti GBER (Reg. 651/2014)**: regime separato con proprie esenzioni per
  categoria (R&S, formazione, investimenti PMI, ecc.). Non si sommano al
  de minimis.
- **Aiuti notificati e autorizzati dalla CE**: approvati individualmente o
  tramite regime notificato. Non de minimis.
- **Incentivi fiscali generali non selettivi**: IRES ordinaria, IRAP ordinaria,
  ammortamenti standard. Non sono aiuti di stato perché non selettivi.
- **Agevolazioni de minimis settore agricolo**: soglia separata di 20.000 EUR
  (Reg. UE 2019/316 — verificare aggiornamenti). Non si cumula con de minimis
  generale.
- **Agevolazioni de minimis settore pesca/acquacoltura**: soglia separata di
  30.000 EUR (Reg. UE 2022/2514). Regime separato.
- **Indennizzi da calamità naturali**: non qualificano come aiuto di stato.
- **SIEG**: regime de minimis separato con soglia 750.000 EUR su tre anni
  (Reg. UE 2023/2832).

### Regola del cumulo

De minimis di tipo diverso (generale, agricolo, pesca, SIEG) non si sommano
tra loro ai fini di ciascun plafond. Un'impresa che opera sia nel settore
agricolo sia in altri settori deve tenere plafond separati per ciascun regime
e garantire che le attività siano chiaramente distinte contabilmente.

---

## Sezione 4 — Come leggere il Registro Nazionale Aiuti (RNA)

Il RNA è la banca dati nazionale degli aiuti di stato, gestita dal Ministero
delle Imprese e del Made in Italy (MIMIT). Tutti gli enti concedenti sono
obbligati a registrare gli aiuti concessi prima dell'erogazione.

### Step-by-step per la consultazione pubblica

**Step 1 — Accesso al portale**
Navigare su `https://www.rna.gov.it` > sezione "Trasparenza" > "Consultazione
aiuti". Non richiede autenticazione per la consultazione pubblica.

**Step 2 — Ricerca per codice fiscale**
Inserire il Codice Fiscale dell'impresa nel campo "CF Beneficiario". Selezionare
il periodo di interesse. Eseguire la ricerca.

**Step 3 — Lettura dei risultati**
Per ogni riga della lista esaminare:
- **Data concessione**: è la data rilevante per il calcolo triennale.
- **Importo concessione**: importo nominale o ESL, a seconda dello strumento.
- **Regime**: verificare che sia "de minimis" e indicare il riferimento
  normativo (Reg. 1407/2013 o Reg. 2023/2831).
- **Ente concedente**: utile per eventuali verifiche di dettaglio.
- **Misura**: nome del bando/strumento per identificare eventuali duplicati.

**Step 4 — Filtro per regime de minimis**
Escludere tutti i record con regime GBER, aiuti notificati o altri regimi.
Sommare solo gli aiuti con regime de minimis Reg. 1407/2013 e Reg. 2023/2831,
con data concessione ricadente nella finestra dei tre esercizi.

**Step 5 — Confronto con soglia**
Totale de minimis negli ultimi tre esercizi <= 300.000 EUR: plafond capiente.
Totale de minimis negli ultimi tre esercizi > 300.000 EUR: plafond esaurito.
Differenza: spazio residuo disponibile.

**Step 6 — Confronto con la soglia 300.000 EUR**
Calcolare: 300.000 - totale consumato = de minimis residuo disponibile.

### Avvertenza su ritardi di registrazione

Il RNA può presentare ritardi anche significativi tra la data di concessione e
la data di caricamento nel sistema da parte dell'ente concedente:
- Bandi comunali o regionali minori: ritardi di 30-90 giorni.
- Aiuti automatici (es. tax credit): possono essere registrati in batch dopo
  mesi dalla concessione.

**Procedura obbligatoria**: richiedere sempre all'impresa una dichiarazione
scritta degli aiuti de minimis ricevuti nell'ultimo triennio, anche se non
ancora visibili sul RNA. La dichiarazione dell'impresa ha valore legale ai
fini della verifica di cumulo. Il disallineamento tra RNA e dichiarazione va
segnalato come nota critica nell'output.

---

## Sezione 5 — L'equivalente sovvenzione lordo (ESL)

L'ESL è la misura standard per confrontare strumenti di aiuto eterogenei
(contributi, prestiti, garanzie) su base omogenea. Per i contributi a fondo
perduto l'ESL coincide con l'importo nominale. Per gli altri strumenti si
calcola come segue.

### ESL per finanziamento agevolato

L'ESL è il vantaggio economico derivante dall'applicazione di un tasso
inferiore a quello di mercato, attualizzato alla data di concessione.

Formula generale:

```
ESL = Sommatoria [ (tasso_mercato - tasso_agevolato) * quota_capitale_t
                   / (1 + tasso_attualizzazione)^t ]
```

Dove:
- `t` = anno del piano di rimborso
- `tasso_mercato` = tasso di riferimento CE (per EUR 2025: circa 3,5-4,5%
  a seconda del rating dell'impresa, pubblicato dalla Commissione)
- `tasso_agevolato` = tasso effettivo del finanziamento
- `quota_capitale_t` = quota capitale in essere nell'anno t

**Esempio numerico**: Finanziamento di 500.000 EUR a tasso 0,5% su 5 anni,
tasso di mercato 4,0%, rimborso in quote capitali uguali da 100.000 EUR/anno.

| Anno | Capitale in essere | Differenziale | Fattore att. 4% | ESL annuo |
|------|-------------------|---------------|-----------------|-----------|
| 1    | 500.000           | 3,5%          | 0,9615          | 16.827    |
| 2    | 400.000           | 3,5%          | 0,9246          | 12.944    |
| 3    | 300.000           | 3,5%          | 0,8890          | 9.334     |
| 4    | 200.000           | 3,5%          | 0,8548          | 5.984     |
| 5    | 100.000           | 3,5%          | 0,8219          | 2.877     |
| **Totale ESL** |            |               |                 | **47.966**|

L'ESL imputabile al de minimis è 47.966 EUR, non 500.000 EUR (nominale).

### ESL per garanzia pubblica

**Metodo safe harbour (semplificato)**: applicabile se la garanzia copre al
massimo l'80% del prestito e la perdita massima è predeterminata.

```
ESL = Importo_garantito * (tasso_garanzia_mercato - premio_garanzia_pagato)
      * durata_anni
```

**Metodo effettivo**: l'ESL è pari alla differenza tra il costo del
finanziamento senza garanzia pubblica e il costo con garanzia pubblica,
attualizzata al momento della concessione.

**Esempio numerico safe harbour**: Garanzia MCC su prestito di 200.000 EUR,
copertura 80% (= 160.000 EUR garantiti), durata 5 anni. Premio di mercato
stimato 2,0%, premio effettivamente pagato 0,5%.

```
ESL = 160.000 * (2,0% - 0,5%) * 5
    = 160.000 * 0,015 * 5
    = 12.000 EUR
```

### Nota operativa per il calcolo pratico

Nella maggior parte dei casi pratici, l'ente concedente registra direttamente
nel RNA l'ESL calcolato, non il nominale. Leggere sempre la colonna "Importo
ESL" del RNA, non la colonna "Importo nominale del prestito" o "Importo
garantito".

---

## Sezione 6 — Casi speciali

### 6.1 Imprese in difficoltà finanziaria

Le imprese in difficoltà finanziaria ai sensi degli Orientamenti CE sugli
aiuti di stato per il salvataggio e la ristrutturazione (2014/C 249/01)
**non possono ricevere aiuti de minimis**. Indicatori di difficoltà:
- Perdita di oltre il 50% del capitale sottoscritto per S.r.l./S.p.A.
- Procedura concorsuale in corso (fallimento, concordato, liquidazione
  giudiziale ai sensi del Codice della Crisi d'Impresa D.Lgs. 14/2019)
- Patrimonio netto negativo per due anni consecutivi (per PMI con meno di
  3 anni di vita: patrimonio netto negativo nell'esercizio più recente)

Azione richiesta: verificare sempre il bilancio dell'ultimo esercizio
disponibile prima di procedere con la verifica del plafond. Se emergono
segnali di difficoltà, impostare `warning_impresa_difficolta: true` e
interrompere il workflow.

### 6.2 Imprese agricole e della pesca

- **Settore agricoltura primaria** (produzione agricola): soglia de minimis
  20.000 EUR in tre anni (Reg. UE 2019/316, che ha modificato il Reg.
  1408/2013). Verificare eventuali aggiornamenti successivi al 2024.
- **Settore pesca e acquacoltura**: soglia 30.000 EUR in tre anni
  (Reg. UE 2022/2514).
- Questi regimi sono separati e non si cumulano con il de minimis generale
  da 300.000 EUR.
- Un'impresa agro-alimentare che **trasforma** (non produce) prodotti
  agricoli ricade nel de minimis generale — la distinzione critica è tra
  produzione primaria e trasformazione/commercializzazione.

### 6.3 Imprese collegate — entità economica unica

Il de minimis si applica a livello di **entità economica unica**, non di
singola persona giuridica. Due o più imprese costituiscono un'entità unica
se si verifica almeno una delle seguenti condizioni:

- Una impresa detiene la maggioranza dei diritti di voto degli azionisti
  o soci dell'altra
- Una impresa ha il diritto di nominare o revocare la maggioranza dei
  membri del consiglio di amministrazione dell'altra
- Una impresa ha il diritto di esercitare un'influenza dominante sull'altra
  in virtù di un contratto o di clausole statutarie
- Una impresa può controllare da sola la maggioranza dei diritti di voto
  in virtù di un accordo con altri azionisti/soci

**Conseguenza pratica**: se Alfa S.r.l. controlla Beta S.r.l. al 60%, i de
minimis ricevuti da entrambe si sommano e il plafond complessivo del gruppo
è comunque 300.000 EUR, non 600.000 EUR.

Azione richiesta: raccogliere l'organigramma societario completo e
verificare l'esistenza di partecipazioni di controllo prima di eseguire
il calcolo. Se rilevate imprese collegate, impostare
`warning_impresa_collegata: true` e calcolare il de minimis aggregato
di gruppo.

### 6.4 Fusioni e acquisizioni

- Se l'impresa acquisita ha ricevuto de minimis negli ultimi tre anni,
  questi si trasferiscono all'impresa acquirente e vanno sommati al
  plafond dell'acquirente.
- In caso di fusione per incorporazione, il plafond residuo dell'incorporata
  si trasferisce all'incorporante.
- In caso di scissione, il de minimis pregresso va attribuito in proporzione
  alle attività cedute. Se non è possibile una attribuzione proporzionale,
  si considera interamente a carico di ciascuna delle entità risultanti.

### 6.5 Startup con esercizi corti

Un'impresa di recente costituzione non ha tre esercizi completi. La regola
si applica agli esercizi effettivamente trascorsi:

**Caso A** — Impresa costituita 1° marzo 2024, domanda a luglio 2026:
- Esercizio 2026 (corrente, parziale): 01/01/2026 - data domanda
- Esercizio 2025: 01/01/2025 - 31/12/2025
- Esercizio 2024 (primo, parziale): 01/03/2024 - 31/12/2024
- Si considerano tutti e tre, anche se il primo è parziale.

**Caso B** — Impresa costituita 1° febbraio 2026, domanda a luglio 2026:
- Solo l'esercizio corrente 2026 (unico disponibile).
- Plafond pieno 300.000 EUR teoricamente disponibile, ma la brevità
  della storia aziendale va segnalata in `note_critiche`.

---

## Sezione 7 — Calcolo pratico: simulatore

### Workflow guidato — domande da porre in sequenza

**Domanda 1 — Codice Fiscale dell'impresa**
Necessario per la ricerca sul RNA. Nel caso di imprese collegate, raccogliere
i CF di tutte le entità del gruppo prima di procedere.

**Domanda 2 — Esercizi finanziari da considerare**
- Qual è la data di presentazione della domanda (o data prevista di concessione)?
- L'esercizio finanziario coincide con l'anno solare?
- Se no, qual è la data di chiusura dell'esercizio?
- Output atteso: lista dei tre esercizi con date di inizio e fine precise.

**Domanda 3 — Aiuti de minimis rilevati dal RNA**
Elencare per ogni aiuto trovato sul RNA:
- Data concessione
- Ente concedente
- Strumento/misura
- Importo ESL registrato
- Regime (Reg. 1407/2013 o Reg. 2023/2831)
- Escludere esplicitamente gli aiuti GBER e i regimi notificati.

**Domanda 4 — Aiuti ricevuti ma non registrati**
L'impresa ha ricevuto aiuti de minimis concessi negli ultimi tre anni ma
non ancora visibili sul RNA? In caso affermativo raccogliere: importo ESL
stimato, ente concedente, data di concessione, riferimento documentale.

**Domanda 5 — Calcolo del totale consumato**

```
De minimis consumato = Somma ESL (aiuti RNA nel triennio)
                     + Somma ESL (aiuti dichiarati non ancora a RNA)
```

Esempio numerico completo:
- Contributo fondo perduto Regione Lombardia (01/03/2024): ESL 25.000 EUR
- Garanzia MCC Mediocredito (15/09/2024): ESL 12.000 EUR
- Voucher innovazione MIMIT (10/02/2025): ESL 10.000 EUR
- Finanziamento agevolato SIMEST (05/11/2025): ESL 47.966 EUR
- Contributo comunale dichiarato, non a RNA (20/01/2026): ESL 8.000 EUR

Totale consumato:
```
25.000 + 12.000 + 10.000 + 47.966 + 8.000 = 102.966 EUR
```

**Domanda 6 — De minimis residuo**

```
De minimis residuo = 300.000 - 102.966 = 197.034 EUR disponibili
```

**Domanda 7 — Verifica capienza per l'agevolazione richiesta**

Inserire l'ESL dell'agevolazione richiesta e confrontare:
- ESL richiesto <= residuo: capiente (SI) — indicare residuo post-concessione
- ESL richiesto > residuo: non capiente (NO) — indicare il deficit
- Deficit parzialmente colmabile: valutare riduzione dell'importo richiesto

Esempio A — agevolazione richiesta con ESL 50.000 EUR:
```
50.000 <= 197.034 → SI, capiente
Residuo post-concessione: 197.034 - 50.000 = 147.034 EUR
```

Esempio B — agevolazione richiesta con ESL 220.000 EUR:
```
220.000 > 197.034 → NO, non capiente
Deficit: 220.000 - 197.034 = 22.966 EUR
Opzione: ridurre l'importo richiesto fino a un massimo di 197.034 EUR ESL
```

---

## Sezione 8 — Output per orchestratore

Al termine del calcolo, la skill produce un oggetto JSON standardizzato
da passare all'orchestratore AgevolazioniBoost per le fasi successive
del workflow di istruttoria.

```json
{
  "de_minimis_residuo_eur": 197034,
  "de_minimis_consumato_eur": 102966,
  "soglia_applicabile_eur": 300000,
  "regolamento_riferimento": "UE 2023/2831",
  "esercizi_considerati": [
    {
      "anno": "2024",
      "data_inizio": "2024-01-01",
      "data_fine": "2024-12-31"
    },
    {
      "anno": "2025",
      "data_inizio": "2025-01-01",
      "data_fine": "2025-12-31"
    },
    {
      "anno": "2026",
      "data_inizio": "2026-01-01",
      "data_fine": "2026-12-31"
    }
  ],
  "aiuti_rilevati": [
    {
      "data_concessione": "2024-03-01",
      "ente_concedente": "Regione Lombardia",
      "misura": "Contributo fondo perduto PMI",
      "esl_eur": 25000,
      "regime": "Reg. UE 1407/2013",
      "fonte": "RNA"
    },
    {
      "data_concessione": "2024-09-15",
      "ente_concedente": "Mediocredito Centrale",
      "misura": "Garanzia MCC PMI",
      "esl_eur": 12000,
      "regime": "Reg. UE 1407/2013",
      "fonte": "RNA"
    },
    {
      "data_concessione": "2025-02-10",
      "ente_concedente": "MIMIT",
      "misura": "Voucher Innovazione",
      "esl_eur": 10000,
      "regime": "Reg. UE 2023/2831",
      "fonte": "RNA"
    },
    {
      "data_concessione": "2025-11-05",
      "ente_concedente": "SIMEST",
      "misura": "Finanziamento agevolato internazionalizzazione",
      "esl_eur": 47966,
      "regime": "Reg. UE 2023/2831",
      "fonte": "RNA"
    },
    {
      "data_concessione": "2026-01-20",
      "ente_concedente": "Comune di Milano",
      "misura": "Contributo commercio di prossimità",
      "esl_eur": 8000,
      "regime": "Reg. UE 2023/2831",
      "fonte": "dichiarazione_azienda"
    }
  ],
  "fonte_dati": "RNA_e_dichiarazione_azienda",
  "capienza_agevolazione_richiesta": true,
  "esl_agevolazione_richiesta_eur": 50000,
  "residuo_post_concessione_eur": 147034,
  "note_critiche": [
    "Presente aiuto dichiarato dall'azienda non ancora visibile sul RNA (Comune di Milano, 20/01/2026 — ESL 8.000 EUR). Richiedere documentazione di supporto (delibera o decreto di concessione).",
    "Verificare allineamento RNA entro 30 giorni dalla concessione dell'agevolazione richiesta.",
    "Il calcolo ESL per il finanziamento SIMEST è basato su tasso di mercato CE stimato al 4,0%. Verificare il tasso ufficiale pubblicato dalla Commissione alla data di concessione."
  ],
  "warning_impresa_collegata": false,
  "warning_impresa_difficolta": false,
  "warning_settore_agricoltura_pesca": false,
  "data_calcolo": "2026-04-24",
  "cf_impresa": "XXXXXXXXXXXXXXXXX"
}
```

### Legenda campi output

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `de_minimis_residuo_eur` | number | Plafond disponibile dopo tutti gli aiuti rilevati |
| `de_minimis_consumato_eur` | number | Totale ESL consumato nel triennio di riferimento |
| `soglia_applicabile_eur` | number | 300.000 regime generale; diverso per agricoltura/pesca/SIEG |
| `esercizi_considerati` | array | Tre esercizi finanziari con date precise di inizio e fine |
| `aiuti_rilevati` | array | Lista degli aiuti de minimis rilevati con tutti i metadati |
| `fonte_dati` | enum | `RNA` / `dichiarazione_azienda` / `RNA_e_dichiarazione_azienda` / `stima` |
| `capienza_agevolazione_richiesta` | bool | true se l'ESL richiesto rientra nel residuo disponibile |
| `esl_agevolazione_richiesta_eur` | number | ESL dell'agevolazione oggetto di istruttoria |
| `residuo_post_concessione_eur` | number | Plafond residuo dopo eventuale concessione dell'aiuto richiesto |
| `note_critiche` | array | Anomalie, disallineamenti RNA, dati da verificare, avvertenze |
| `warning_impresa_collegata` | bool | true se rilevate imprese collegate — calcolo aggregato necessario |
| `warning_impresa_difficolta` | bool | true se segnali di difficoltà finanziaria — blocco concessione |
| `warning_settore_agricoltura_pesca` | bool | true se attività in settore a soglia ridotta |

### Gestione degli errori e casi di incertezza

- **RNA non disponibile o in errore**: impostare `fonte_dati` su `stima` e
  aggiungere nota critica che richiede verifica manuale prima della concessione.
- **Dichiarazione incompleta dell'impresa**: segnalare in `note_critiche` e
  non procedere con la concessione finché non viene integrata con documentazione.
- **`warning_impresa_collegata` true**: il campo `de_minimis_residuo_eur` è
  da considerarsi provvisorio fino al completamento del calcolo aggregato di
  gruppo con i CF di tutte le entità collegate.
- **`warning_impresa_difficolta` true**: interrompere il workflow e segnalare
  all'operatore. Non procedere con la concessione dell'aiuto de minimis.
- **ESL non calcolato dall'ente concedente**: applicare il metodo di calcolo
  della Sezione 5, documentare le ipotesi utilizzate (tasso di mercato CE,
  piano di rimborso) e segnalare in `note_critiche` che il valore è una stima.
