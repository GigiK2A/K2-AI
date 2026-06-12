---
name: ai-archive-templates-fiscal
description: Skill settoriale per skillizzazione archivio studi commercialisti italiani — template ready-to-use per 30-50 documenti tipici. Bilanci civilistici, dichiarativi (Redditi PF/SP/SC, IRAP, IVA, LIPE, 770, CU), F24, contabilità ord/sempl, perizie di stima, pareri tributari, ricorsi CGT, comunicazioni AdE/INPS/CCIAA, lettere clienti. Differenziati per area — fiscale dichiarativa, contabilità, bilancio, contenzioso tributario, consulenza societaria, perizie. Usa SEMPRE quando ai-knowledge-skillization-studio è attivata per studio commercialisti, oppure cliente commercialista dice skill bilancio, template dichiarazione redditi, skill F24, skill ricorso CGT, skill perizia, skill parere tributario, knowledge codification studio commercialista. Skillizzabilità realistica 60-75%. NON usare per altri settori, consulenza tributaria sostantiva, atti societari notarili (vai a notarial).
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


# ai-archive-templates-fiscal — Template skill settoriali per studi commercialisti

## 1. Cosa fa questa skill

Complemento operativo di `ai-knowledge-skillization-studio` per il settore della consulenza commercialista, tributaria e societaria italiana, per studi di dottori commercialisti, esperti contabili e consulenti tributari iscritti all'albo ODCEC.

### Perché è un buon target di skillizzazione

Skillizzabilità media 60-75%, dovuta a:

1. **Calendario fiscale ricorrente** — il 70-80% del lavoro è dettato da scadenze ripetitive (LIPE trimestrale, F24 mensili, dichiarativi annuali).
2. **Volume documentale alto** — anche un piccolo studio gestisce 50-200 clienti, ognuno produce 50-150 documenti/anno.
3. **Strutture documentali codificate** — bilanci con schemi civilistici art. 2424-2425 c.c., dichiarativi su modelli AdE, F24 standardizzati.
4. **Cliente-tipo stratificato** — PMI manifatturiera, professionista forfettario, SRL servizi → pattern ricorrenti riusabili.

**Limite di skillizzabilità**: la consulenza tributaria sostantiva (interpretazioni, scelte di struttura fiscale, contenzioso complesso) resta indelegabile.

### Pricing

Pricing K2-AI tipico: **22-90K euro one-shot** + retainer 800-2.000 euro/mese. ROI tipico 6-12 mesi.

---

## 2. Quando attivarsi

### Trigger
- Skillization in corso per studio commercialista
- "Skill bilancio civilistico", "skill nota integrativa"
- "Skill dichiarazione redditi PF/SP/SC", "skill IVA / LIPE", "skill F24"
- "Skill perizia di stima", "skill parere tributario"
- "Skill ricorso Corte di Giustizia Tributaria"
- "Knowledge codification studio commercialista"

### Quando NON attivarsi
- Skillization per altri settori
- Consulenza tributaria sostantiva
- Atti societari notarili (vai a `ai-archive-templates-notarial`)
- Consulenza giuslavoristica (vai a `ai-archive-templates-payroll`)

---

## 3. Le aree del settore commercialista

### Area 1 — Bilanci e nota integrativa (skillizzabilità 75-85%)
- Bilancio abbreviato art. 2435-bis, ordinario, micro art. 2435-ter
- Nota integrativa (XBRL)
- Relazione sulla gestione
- Verbale assemblea approvazione bilancio
- Deposito CCIAA (FedraPlus / Telemaco)
- Bilancio consolidato
- Riclassificazione gestionale

### Area 2 — Dichiarativi fiscali (skillizzabilità 70-85%)
- Modello Redditi PF / 730 / SP / SC
- IRAP, IVA annuale, LIPE
- 770, CU Certificazione Unica
- Quadro RW, esterometro, Intrastat

### Area 3 — Contabilità (skillizzabilità 65-80%)
- Prima nota ordinaria
- Registrazioni acquisti / vendite / stipendi
- Scritture di rettifica e assestamento
- Libri IVA, registro beni ammortizzabili

### Area 4 — F24 e versamenti (skillizzabilità 85-95%)
- F24 ordinario, elide, accise
- Compensazioni
- Cessioni crediti d'imposta
- F23 residuale

### Area 5 — Consulenza societaria (skillizzabilità 55-70%)
- Verbali CdA / assemblee soci
- Costituzione SRL semplificata (parte commercialistica)
- Cessioni quote, aumenti capitale
- Operazioni straordinarie (parti commercialistiche)

### Area 6 — Pareri tributari e interpelli (skillizzabilità 50-65%)
- Parere tributario standard
- Interpello ordinario / disapplicativo / probatorio
- Istanza di rimborso

### Area 7 — Contenzioso tributario (skillizzabilità 40-60%)
- Ricorso CGT primo grado, memorie, appello
- Istanza di adesione, reclamo / mediazione
- Conciliazione giudiziale

### Area 8 — Comunicazioni clienti (skillizzabilità 75-90%)
- Lettera assegnazione incarico
- Lettera annuale tariffario
- Promemoria scadenze
- Comunicazione esiti dichiarazione

### Area 9 — Perizie e valutazioni (skillizzabilità 55-70%)
- Perizia di stima d'azienda (DCF, multipli, patrimoniale)
- Perizia conferimento art. 2343 c.c.
- Perizia fusione / scissione
- Rivalutazione partecipazioni / terreni L. 448/2001

### Area 10 — Comunicazioni con enti (skillizzabilità 85-95%)
- Risposte AdE, istanze rateazione / sospensione
- Comunicazioni INPS, INAIL, CCIAA
- Cassa Forense / Inarcassa

---

## 4. Pricing pacchetti

- **STARTER (22-35K €)**: 15-20 skill core, 1 cliente pilota, 6-8 settimane
- **STANDARD (45-70K €)**: 40-50 skill, Tier 2 privacy, 10-12 settimane
- **PREMIUM (75-130K €)**: 60-80 skill, Tier 3 privacy, knowledge base self-hosted, 14-18 settimane
- **Retainer**: 800-1.500 €/mese aggiornamenti normativi trimestrali

---

## 5. Compliance

**Privacy**: dati cliente includono dati particolari (sanitari per detrazioni, ISEE), reddituali, patrimoniali. Tier 2 obbligatorio, Tier 3 raccomandato per studi grandi. DPIA da predisporre.

**Codice deontologico ODCEC**: la skill non sostituisce mai firma e responsabilità del commercialista. Trasparenza obbligatoria sull'uso AI nel mandato.

**Aggiornamento normativo**: normativa tributaria cambia frequentemente (Legge di Bilancio + decreti + circolari AdE). Refresh trimestrale via `ai-manutenzione-evoluzione`.

**Conservazione**: documenti fiscali 10 anni (art. 22 DPR 600/1973, art. 2220 c.c.). PDF/A.
