---
name: ai-archive-templates-legal
description: Skill settoriale per skillizzazione dell'archivio di studi legali italiani — fornisce template ready-to-use per i 30-50 tipi di documento tipici del settore. Atti di causa, lettere, pareri, ricorsi, memorie, contratti, procedure. Differenziati per area pratica — civile, commerciale, lavoro, tributario, condominiale, recupero crediti, M&A, immobiliare, famiglia, penale (con cautela). Usa SEMPRE quando ai-knowledge-skillization-studio è attivata per studio legale, oppure quando cliente avvocato dice skill atti studio legale, template lettere diffida, skill ricorso tributario, skill memoria difensiva, skill atto citazione, skill parere legale, knowledge codification studio legale. Focus su aree alta standardizzazione — recupero crediti, lavoro, tributario, condominiale, M&A standard. Skillizzabilità realistica 40-60% (vs 70-80% ingegneria). Tier 1 ad alto ROI vs Tier 2 supporto. NON usare per altri settori, per consulenza legale sostantiva.
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


# ai-archive-templates-legal — Template skill settoriali per studi legali

## 1. Cosa fa questa skill

Questa skill è il **complemento operativo di `ai-knowledge-skillization-studio`** per il settore legale italiano. Fornisce template ready-to-use per le tipologie documentali tipiche degli studi legali, **con consapevolezza onesta dei limiti** della skillizzazione in questo settore.

### Premessa strategica importante

A differenza dell'ingegneria, dove la skillizzazione cattura 70-80% del valore operativo, nel mondo legale **la cattura realistica è 40-60%**. Questa skill è progettata per **massimizzare quel 40-60%**, non per promettere falsamente di più.

Aree dove la skillizzazione legale è altamente efficace (Tier 1):
- Documenti procedurali standard (atti, ricorsi, memorie tipo)
- Comunicazioni e lettere ricorrenti
- Procedure interne dello studio
- Knowledge giurisprudenziale (interrogazione archivio sentenze)
- Compliance e deontologia

Aree dove la skillizzazione è supporto ma non sostituzione (Tier 2):
- Pareri legali su materie complesse
- Strategie processuali
- Negoziazioni
- Difese in materie penali sensibili

Aree dove la skillizzazione è proibita o sconsigliata:
- Decisioni giudizio strategico finale (sempre umane)
- Materie particolari deontologicamente (penale grave, famiglia minori)

### Il valore differenziale per studi legali

Anche con cattura "solo" del 40-60%, il valore è **estremamente rilevante** per studi legali con:
- Alto volume documentale standard (recupero crediti, lavoro)
- Specializzazione fortissima (tributario, fallimentare, arbitrato)
- Knowledge giurisprudenziale ricco da interrogare
- Problema di passaggio generazionale
- Necessità di onboarding rapido nuovi associate

Per questi studi, la skillizzazione genera ROI 3-8x in 24 mesi e asset patrimoniale durevole.

---

## 2. Quando attivarsi

### Trigger
- Skillization in corso per studio legale
- "Template skill avvocati"
- "Skill atto di citazione"
- "Skill ricorso tributario"
- "Skill lettera diffida"
- "Skill parere legale"
- "Skill memoria difensiva"
- "Skill recupero crediti"
- "Skill knowledge giurisprudenza"

### Quando NON attivarsi
- Skillization per altri settori
- Generica AI assessment senza skillization
- Implementazione tool senza skillization
- Consulenza legale sostantiva (richiede avvocato abilitato)

---

## 3. Le aree pratiche e la loro skillizzabilità

Differenziamo per area pratica perché il pattern di skillizzazione cambia significativamente.

### Area 1 — Diritto civile generale
**Skillizzabilità**: media (50-65%)
**Volume tipico**: alto
**Valore del template**: alto

Documenti skillizzabili:
- Atti di citazione (struttura procedurale fissa)
- Comparse di costituzione e risposta
- Note di replica e duplica
- Note conclusionali
- Memorie ex art. 183 c.p.c.
- Comparse conclusionali
- Atti di precetto
- Pignoramenti
- Lettere di diffida
- Lettere di costituzione in mora
- Pareri standard (responsabilità civile, danno, etc.)
- Procedimenti monitori (decreti ingiuntivi)

### Area 2 — Diritto commerciale e societario
**Skillizzabilità**: alta (60-75%)
**Volume tipico**: medio-alto
**Valore del template**: molto alto

Documenti skillizzabili:
- Atti di citazione commerciali
- Verbali di assemblea (sociale, soci, CdA)
- Atti di trasferimento partecipazioni
- Patti parasociali
- Contratti commerciali standard (vendita, fornitura, distribuzione, agenzia)
- Lettere commerciali standard
- Pareri societari ricorrenti
- Comunicazioni a Camera di Commercio
- Documenti per operazioni straordinarie standard

### Area 3 — Diritto del lavoro
**Skillizzabilità**: alta (65-80%)
**Volume tipico**: alto
**Valore del template**: altissimo

Una delle aree con migliore ROI di skillizzazione.

Documenti skillizzabili:
- Lettere di contestazione disciplinare
- Lettere di licenziamento
- Verbali di conciliazione (Tribunale, ITL, sindacale)
- Ricorsi ex art. 700 c.p.c.
- Ricorsi al Tribunale del Lavoro
- Ricorsi cumulativi (lavoratori)
- Memorie difensive in cause di lavoro
- Pareri standard (mobbing, demansionamento, licenziamento)
- Lettere CCNL e sindacali
- Documenti vertenze sindacali

### Area 4 — Diritto tributario
**Skillizzabilità**: altissima (70-85%)
**Volume tipico**: medio-alto
**Valore del template**: massimo

Una delle aree migliori per skillizzazione (insieme al recupero crediti).

Documenti skillizzabili:
- Ricorsi tributari (Corte di Giustizia Tributaria di Primo Grado)
- Appelli tributari (Secondo Grado)
- Memorie illustrative
- Atti di adesione
- Istanze di sospensione cautelare
- Istanze di autotutela
- Pareri tributari standard
- Lettere di contestazione cartelle
- Procedure conciliative

### Area 5 — Diritto immobiliare e condominiale
**Skillizzabilità**: alta (60-75%)
**Volume tipico**: alto
**Valore del template**: altissimo

Documenti skillizzabili:
- Convocazioni assemblea condominiale
- Verbali di assemblea condominiale
- Diffide e azioni contro condòmini morosi
- Decreti ingiuntivi condominiali
- Cause di danno da infiltrazione/parti comuni
- Cause di interpretazione regolamento
- Pareri condominiali ricorrenti
- Atti di compravendita immobiliare
- Contratti di locazione
- Sfratti per morosità e finita locazione

### Area 6 — Recupero crediti
**Skillizzabilità**: massima (80-95%)
**Volume tipico**: massimo
**Valore del template**: estremo

L'area con la più alta skillizzabilità in assoluto. Per studi che fanno principalmente recupero crediti, la skillizzazione è quasi automazione.

Documenti skillizzabili:
- Lettere di sollecito (vari livelli)
- Diffide stragiudiziali
- Decreti ingiuntivi (template ricorrenti)
- Atti di precetto
- Pignoramenti (mobiliare, immobiliare, presso terzi)
- Atti di esecuzione
- Lettere a debitori e debitori ceduti
- Procedure standard di recupero

### Area 7 — Diritto fallimentare e ristrutturazione
**Skillizzabilità**: media-alta (55-70%)
**Volume tipico**: medio
**Valore del template**: alto

Documenti skillizzabili:
- Istanze di fallimento
- Domande di ammissione al passivo
- Insinuazioni
- Ricorsi ex CCII (Codice Crisi Impresa)
- Documentazione composizione negoziata
- Memorie in cause concorsuali
- Pareri ricorrenti

### Area 8 — Famiglia (con cautela)
**Skillizzabilità**: bassa (30-45%)
**Volume tipico**: medio
**Valore del template**: limitato

Materia delicata. Skillizzazione utile solo per parti procedurali/standard, mai per contenuti sensibili (figli minori, situazioni delicate).

Documenti skillizzabili (con cautela):
- Ricorsi per separazione consensuale (struttura procedurale)
- Ricorsi per divorzio congiunto (struttura procedurale)
- Procedure di negoziazione assistita
- Verbali di mediazione

Documenti NON skillizzabili:
- Ricorsi contenziosi su minori (sempre custom)
- Documenti su situazioni gravi (violenza, abusi)
- Pareri su casi specifici complessi

### Area 9 — Penale (con grande cautela)
**Skillizzabilità**: bassissima (10-25%)
**Volume tipico**: variabile
**Valore del template**: molto limitato

Materia altamente delicata. Skillizzazione realisticamente solo per:
- Strutture procedurali generiche
- Documenti amministrativi (nomine, deleghe)
- Comunicazioni standard

NON skillizzare mai:
- Difese tecniche
- Memorie difensive sostanziali
- Strategie processuali
- Documenti su materie sensibili (reati gravi, abusi, violenza)

### Area 10 — M&A e operazioni straordinarie
**Skillizzabilità**: media (50-65% per parti standard)
**Volume tipico**: basso ma alto valore unitario
**Valore del template**: alto per parti standard

Documenti skillizzabili:
- Term sheet template
- LOI (Letter of Intent) standard
- NDA standard
- Due diligence checklist
- Clausole contrattuali standard (rep & warranties, indemnification)
- Documenti di closing standard

Documenti NON skillizzabili (caso per caso):
- Strategia complessiva del deal
- Negoziazione di clausole specifiche
- Pareri legali specifici sull'operazione

---

## 4. Tassonomia dei template skill per area legale

### Tier 1 — Templates ad alta skillizzabilità (priorità di costruzione)

**Recupero crediti** (8 template):
- skill-lettera-sollecito-livello-1
- skill-lettera-sollecito-livello-2-finale
- skill-diffida-stragiudiziale
- skill-decreto-ingiuntivo-ricorso
- skill-atto-precetto
- skill-pignoramento-presso-terzi
- skill-pignoramento-mobiliare
- skill-pignoramento-immobiliare

**Diritto del lavoro** (10 template):
- skill-contestazione-disciplinare
- skill-lettera-licenziamento-GMO
- skill-lettera-licenziamento-disciplinare
- skill-ricorso-tribunale-lavoro
- skill-memoria-difensiva-lavoro
- skill-conciliazione-ITL
- skill-vertenza-sindacale-lettera
- skill-parere-mobbing
- skill-parere-demansionamento
- skill-richiesta-CIGO-CIGS

**Diritto tributario** (8 template):
- skill-ricorso-CTPG-cartella
- skill-ricorso-CTPG-accertamento
- skill-appello-CTSG
- skill-istanza-sospensione-cautelare
- skill-istanza-autotutela
- skill-atto-adesione
- skill-memoria-illustrativa-tributaria
- skill-parere-tributario-standard

**Condominiale** (6 template):
- skill-convocazione-assemblea
- skill-verbale-assemblea
- skill-decreto-ingiuntivo-condominiale
- skill-causa-danno-infiltrazione
- skill-causa-interpretazione-regolamento
- skill-parere-condominiale

**Civile generico** (10 template):
- skill-atto-citazione-civile
- skill-comparsa-costituzione-risposta
- skill-memoria-art-183
- skill-comparsa-conclusionale
- skill-note-replica
- skill-precetto
- skill-lettera-diffida-civile
- skill-costituzione-mora
- skill-parere-responsabilita-civile
- skill-parere-danno-risarcibile

**Commerciale** (8 template):
- skill-verbale-assemblea-soci
- skill-verbale-CdA
- skill-cessione-quote
- skill-contratto-distribuzione
- skill-contratto-fornitura
- skill-contratto-agenzia
- skill-contratto-NDA
- skill-parere-societario

**Procedurali e amministrativi studio** (8 template):
- skill-procura-litem
- skill-mandato-difensivo
- skill-fattura-pro-forma
- skill-preventivo-cliente
- skill-comunicazione-stato-pratica
- skill-onboarding-cliente-nuovo
- skill-archiviazione-fascicolo
- skill-procedura-antiriciclaggio

**Totale Tier 1**: ~58 template ad alto valore

### Tier 2 — Template di supporto (skillizzazione media)

**Famiglia (parti procedurali)** (4 template):
- skill-separazione-consensuale-ricorso
- skill-divorzio-congiunto-ricorso
- skill-negoziazione-assistita
- skill-mediazione-familiare-verbale

**Fallimentare e ristrutturazione** (5 template):
- skill-istanza-fallimento
- skill-insinuazione-passivo
- skill-domanda-ammissione-stato-passivo
- skill-composizione-negoziata-doc
- skill-piano-attestato-doc

**Immobiliare** (5 template):
- skill-contratto-compravendita-base
- skill-contratto-locazione-uso-abitativo
- skill-contratto-locazione-commerciale
- skill-sfratto-morosita
- skill-sfratto-finita-locazione

**M&A standard** (5 template):
- skill-term-sheet-MA
- skill-LOI-standard
- skill-NDA-MA
- skill-due-diligence-checklist
- skill-clausole-RW-template

**Totale Tier 2**: ~19 template

### Tier 3 — Template di knowledge management (Tipo D)

Skill di consultazione e ricerca, non di produzione:

- skill-knowledge-giurisprudenza-cassazione (per ricerca casi simili)
- skill-knowledge-giurisprudenza-cassazione-sezione-lavoro
- skill-knowledge-giurisprudenza-merito-tribunale-X (per studi locali)
- skill-knowledge-cliente-storico-CRM
- skill-knowledge-pareri-precedenti-studio
- skill-knowledge-strategie-vincenti-studio

**Totale Tier 3**: ~6-12 template (custom per studio)

### Quality e procedurali (Tipo E)

- skill-checklist-pre-firma-atto
- skill-checklist-deposito-telematico
- skill-review-relazione-CTU
- skill-protocollo-conflitti-interessi

**Totale Quality**: ~4-8 template

---

## 5. Anatomia di un template legale

Esempio template — `skill-lettera-diffida-civile`:

```markdown
---
name: skill-lettera-diffida-civile
description: Template per lettera di diffida stragiudiziale in materia civile, da inviare al debitore/controparte come atto preliminare a eventuale azione giudiziale. Codifica struttura standard, criteri di scelta toni e contenuti, esempi reali dello studio [NOME STUDIO]. Da personalizzare con prassi e formulazioni specifiche del titolare.
domain: diritto-civile
document_type: lettera-stragiudiziale
practice_area: contenzioso-civile
frequency: alta
complexity: bassa
last_updated: [DATA]
version: 1.0
based_on_archive_examples: [N esempi reali analizzati]
---

# skill-lettera-diffida-civile

## 1. Scope e applicabilità

Questa skill produce una lettera di diffida stragiudiziale in materia civile.

**Quando usarla**:
- Diffida ad adempiere obbligazione contrattuale
- Diffida per cessazione condotta lesiva
- Diffida per risoluzione contratto
- Diffida ex art. 1454 c.c. (diffida ad adempiere)
- Costituzione in mora ex art. 1219 c.c.
- Atto preliminare a eventuale azione giudiziale

**Quando NON usarla**:
- Per recupero crediti puro (vedi skill-lettera-sollecito-*)
- Per materia di lavoro (vedi skill-lettera-contestazione-lavoro)
- Per materia condominiale (vedi skill-lettera-condominiale)
- Per materia commerciale specifica (vedi skill-lettera-commerciale)

## 2. Struttura della lettera

La lettera di diffida dello studio [NOME STUDIO] segue questa struttura:

### Sezione 1 — Intestazione
- Logo studio (se uso carta intestata)
- Riferimenti studio (mittente)
- Data e luogo
- Destinatario completo (nome, indirizzo, P.IVA se PG)
- Riferimento pratica/incarico

### Sezione 2 — Oggetto
- Sintesi efficace ("Diffida e costituzione in mora — [oggetto specifico]")
- Riferimento normativo se applicabile (art. 1454 c.c., art. 1219 c.c.)

### Sezione 3 — Apertura formale
- Identificazione legale del professionista
- Identificazione del cliente per cui si scrive
- Eventuale procura allegata o esibita
- Eventuale rinvio a corrispondenza precedente

### Sezione 4 — Esposizione dei fatti
- Cronologia oggettiva dei fatti rilevanti
- Riferimenti a documenti/contratti
- Eventuali riferimenti a corrispondenza precedente
- Tono asciutto, no aggettivi valutativi

### Sezione 5 — Esposizione delle ragioni di diritto
- Riferimenti normativi applicabili
- Eventuali riferimenti giurisprudenziali (selezionati)
- Argomentazione contenuta (15-30% del documento)
- Tono professionale, no toni eccessivamente combattivi

### Sezione 6 — Diffida formale
- Specifica intimazione a fare o non fare
- Termine entro cui adempiere (concreto, ragionevole)
- Conseguenze del mancato adempimento (azione giudiziale, costituzione in mora)
- Eventuali avvertimenti specifici

### Sezione 7 — Riserve
- Riserva di azioni ulteriori
- Riserva su eventuali altri profili
- Riserva sui maggiori danni

### Sezione 8 — Chiusura
- Formula di cortesia (asciutta)
- Sottoscrizione professionista
- Eventuali allegati elencati
- PEC/email per comunicazioni

## 3. Criteri di compilazione [DA PERSONALIZZARE]

### Tono e stile
- [Es. "Tono fermo ma cortese, mai aggressivo. La diffida è atto serio, non emotivo"]
- [Es. "Frasi articolate ma chiare, italiano forense corretto ma accessibile"]
- [Es. "Mai uso prima persona ('io chiedo'), sempre formula impersonale ('si chiede')"]

### Approccio strategico
- [Es. "Sempre offrire una via di uscita ragionevole alla controparte"]
- [Es. "Sempre lasciare spazio alla negoziazione, mai chiusura definitiva"]
- [Es. "Sempre invitare a contattare lo studio per chiarimenti"]

### Tempi
- [Es. "Termine standard: 15 giorni"]
- [Es. "Termini ridotti (7-10 gg) solo in casi di particolare urgenza"]
- [Es. "Termine maggiore (20-30 gg) per materie complesse o più destinatari"]

### Riferimenti giurisprudenziali
- [Es. "Sì, sempre 1-2 riferimenti pertinenti se esistono"]
- [Es. "No, solo per casi complessi, altrimenti diventa memoria"]

### Lunghezza tipica
- [Es. "Standard 2-3 pagine, mai oltre 4"]

## 4. Esempi dall'archivio dello studio [DA PERSONALIZZARE]

### Esempio 1 — Diffida per inadempimento contrattuale (anonimizzato)
[Estratto reale, anonimizzato]

### Esempio 2 — Diffida per risoluzione (anonimizzato)
[Estratto reale]

### Esempio 3 — Diffida con tono fermo (caso di rifiuto persistente) (anonimizzato)
[Estratto reale]

### Esempio 4 — Diffida con apertura negoziale (caso conciliabile) (anonimizzato)
[Estratto reale]

### Esempio 5 — Diffida tra professionisti/aziende (anonimizzato)
[Estratto reale di rapporto B2B]

## 5. Casi limite e varianti

### Variante 1 — Destinatario PMI/microimpresa
- Tono leggermente più accessibile
- Spiegazione delle norme (PMI può non avere ufficio legale)
- Termini più ampi (15-20 gg vs 10)

### Variante 2 — Destinatario grande impresa/ente
- Tono più formale e tecnico
- Riferimenti normativi più articolati
- Eventuale doppia inoltro (PEC + raccomandata)

### Variante 3 — Diffida con notifica via UNEP
- Procedura formale
- Riferimenti specifici
- Costi diversi

### Variante 4 — Diffida internazionale (controparte estera)
- Lingua (italiano + traduzione)
- Riferimenti a Bruxelles I-bis se UE
- Notifica regolare internazionale

### Variante 5 — Diffida congiunta (più mittenti / più destinatari)
- Identificazione precisa di parti
- Eventuale solidarietà dei destinatari

### Variante 6 — Diffida in extremis prima di prescrizione
- Urgenza dichiarata
- Termine ridotto
- Motivazione esplicita dell'urgenza

## 6. Riferimenti normativi

- **Art. 1218 c.c.** — Responsabilità del debitore
- **Art. 1219 c.c.** — Costituzione in mora
- **Art. 1453 c.c.** — Risoluzione del contratto per inadempimento
- **Art. 1454 c.c.** — Diffida ad adempiere
- **Art. 1455 c.c.** — Importanza dell'inadempimento
- **Art. 1456 c.c.** — Clausola risolutiva espressa
- **Art. 2697 c.c.** — Onere della prova
- **Art. 1366 c.c.** — Interpretazione del contratto secondo buona fede

## 7. Lessons learned [DA PERSONALIZZARE]

Errori tipici da evitare (basati su esperienza dello studio):

- [Es. "Mai mettere termini troppo brevi: il giudice in causa potrebbe ritenerli inadeguati e sfavorire chi diffida"]
- [Es. "Mai dimenticare la specifica indicazione di costituzione in mora se serve"]
- [Es. "Sempre verificare l'indirizzo del destinatario (PEC ufficiale per imprese)"]
- [Es. "Sempre conservare ricevuta di consegna (PEC, R/R)"]
- [Es. "Mai usare termini medici o eccessivi: la diffida è atto giuridico, non polemica"]
- [Es. "Sempre coordinare con cliente prima dell'invio (l'effetto deteriora la relazione)"]

## 8. Checklist operativa

Pre-redazione:
- [ ] Procura/mandato ricevuto
- [ ] Documenti rilevanti raccolti
- [ ] Verifica indirizzo del destinatario (PEC se possibile)
- [ ] Verifica decorrenza termine prescrizione
- [ ] Coordinamento con cliente su strategia

Redazione:
- [ ] Struttura completa (8 sezioni)
- [ ] Termine concreto e ragionevole
- [ ] Conseguenze chiare
- [ ] Riferimenti normativi corretti
- [ ] Riserve adeguate
- [ ] Eventuali allegati

Post-redazione:
- [ ] Review titolare/responsabile
- [ ] Verifica destinatario corretto
- [ ] Invio (PEC + eventuale R/R)
- [ ] Conservazione ricevute
- [ ] Aggiornamento fascicolo cliente
- [ ] Calendarizzazione scadenza termine

## 9. Integrazione con altre skill

**Pre-diffida**:
- skill-onboarding-cliente-nuovo (se cliente nuovo)
- skill-procura-litem (per acquisire procura)

**Post-diffida (se inadempimento persiste)**:
- skill-atto-citazione-civile (azione giudiziale)
- skill-decreto-ingiuntivo-ricorso (recupero crediti)
- skill-mediazione-civile (se obbligatoria)

**Trasversali**:
- skill-knowledge-giurisprudenza-cassazione (per riferimenti)
- skill-checklist-pre-firma-atto (review qualità)

## 10. Output atteso

La skill produce:
- Lettera di diffida .docx (2-3 pp tipiche)
- Eventuale modulo invio PEC compilato
- Promemoria scadenza termine
- Aggiornamento fascicolo
```

Questo è uno dei ~58 template del Tier 1. La skill ne contiene di analoghi per ogni tipologia.

---

## 6. Considerazioni privacy specifiche per skillizzazione legale

A differenza dell'ingegneria, lo studio legale ha **vincoli privacy più stringenti** che impattano profondamente sull'architettura.

### Implicazioni operative

**Sanitization più rigorosa**: gli esempi reali nei template devono essere **profondamente anonimizzati**, non solo pseudonimizzati. Casi pubblicati sui media non possono essere usati come esempi anche con anonimizzazione (il contesto identifica).

**Architettura preferita**: Tier 3 (cloud privato EU) o Tier 4 (locale) per le materie particolari (penale, famiglia minori). Tier 1 + 2 sufficiente solo per Recupero crediti, Civile generico, Tributario.

**Knowledge giurisprudenziale**: i template di Tipo D (knowledge giurisprudenziale dello studio) sono particolarmente sensibili — contengono pattern strategici. Devono essere su infrastruttura privata.

**Connection con `ai-privacy-tiered-architecture`**: per studi legali, la skillizzazione deve sempre essere accompagnata da una progettazione privacy tiered. Le due skill si attivano insieme.

---

## 7. Pricing per skillizzazione legale

Considerando il valore catturato è 40-60% (vs 70-80% ingegneria) e la privacy è più costosa:

### Pacchetti

**SKILLIZATION LEGAL STARTER** — Studio piccolo legale (1-3 avv, archivio 1.000-3.000 doc)
- 25-40 skill (Tier 1)
- Architettura B (Cloud privato EU)
- Durata: 5-7 mesi
- **Pricing: 22.000-32.000€** + retainer 800-1.000€/mese

**SKILLIZATION LEGAL STANDARD** — Studio medio legale (5-15 avv, archivio 3.000-15.000 doc)
- 60-100 skill (Tier 1 + 2 + Tipo D iniziale)
- Architettura B/D
- Durata: 10-14 mesi
- **Pricing: 55.000-85.000€** + retainer 1.500-2.500€/mese

**SKILLIZATION LEGAL PREMIUM** — Studio grande legale (15+ avv, archivio 15.000+ doc)
- 120-200 skill (tutti Tier + Knowledge base avanzata)
- Architettura D/C in base a privacy
- Durata: 14-20 mesi
- **Pricing: 110-180.000€** + retainer 2.500-4.000€/mese

### Casi speciali ad alto pricing

**Studi specializzati ad alto volume standardizzato** (recupero crediti, lavoro, tributario):
- Skillizzabilità superiore al pattern medio (75-85%)
- Pricing **maggiorato 25-40%** rispetto pacchetto base
- ROI molto rapido (12-18 mesi)
- Esempio: studio recupero crediti 8 prof → pacchetto 70-95K€ giustificato

**Studi M&A enterprise** (clientela corporate top, requisiti privacy massimi):
- Architettura Tier 3-4
- Skillizzazione knowledge giurisprudenziale ricca
- Pricing **maggiorato 30-50%**
- Esempio: studio M&A 15 avv → pacchetto 110-150K€

---

## 8. Skill K2-AI esistenti rilevanti per legale

L'ecosistema K2-AI ha già skill legali di settore che alimentano la skillizzazione:

- **diritto-italiano** (civile, penale, amministrativo, tributario)
- **diritto-societario-italiano**
- **fiscale-tributario-italiano**
- **diritto-processuale**
- **antitrust-concorrenza-ue**
- **it-law-privacy-ai**
- **ss-trust-italiano**
- **consulente-pa-operativa**
- **fiscale-dogmatico-internazionale**

Queste skill agiscono come **knowledge base settoriale** che alimenta la costruzione delle skill cliente:
- Per skill cliente "ricorso tributario": K2-AI usa template di questa skill + knowledge da `fiscale-tributario-italiano` + esempi reali archivio cliente
- Per skill cliente "lettera diffida societaria": template + `diritto-societario-italiano` + esempi cliente

Risultato: **skill cliente di altissima qualità con minimo effort** grazie all'orchestrazione delle skill K2-AI esistenti.

---

## 9. Esempio applicato — Studio Tributario Romagna (4 avv, recupero crediti + tributario)

### Profilo
Studio specializzato a Cesena, 4 avvocati (1 senior + 3 junior), focus 60% recupero crediti + 30% tributario + 10% civile generico. Archivio 6.000 documenti significativi in 6 anni.

### Approccio Skillization

```
═══════════════════════════════════════════════════════
SKILLIZATION DESIGN — Studio Tributario Romagna
═══════════════════════════════════════════════════════

📊 ARCHIVIO ANALIZZATO

Distribuzione tipologie:
- Lettere di sollecito: 1.250 (recupero crediti)
- Decreti ingiuntivi: 890 
- Atti di precetto: 650
- Pignoramenti: 420
- Ricorsi tributari: 380
- Atti di adesione: 145
- Pareri standard: 280
- Altri: 1.985

Skillizzabilità complessiva valutata: 75% (alta)
Volume di documenti standard: ELEVATO
ROI atteso: ALTO

═══════════════════════════════════════════════════════
🏗 PIANO SKILL DA COSTRUIRE: 52 SKILL

Tier 1 (alta priorità):
- Recupero crediti: 8 skill
- Tributario: 8 skill  
- Civile generico: 6 skill
Subtotale: 22 skill

Tier 2 (media priorità):
- Procedure studio: 8 skill
- Knowledge base studio: 12 skill
- Quality check: 4 skill
Subtotale: 24 skill

Tier 3 (custom completamento):
- Skill specifiche studio: 6 skill
Subtotale: 6 skill

TOTALE: 52 skill in 12 mesi

═══════════════════════════════════════════════════════
🏛 ARCHITETTURA RACCOMANDATA

Architettura B (Cloud privato EU):
├─ Vector DB: Qdrant Cloud Frankfurt
├─ LLM: Azure OpenAI Italia (GPT-4o)
├─ Frontend: web app dedicata
└─ Storage: SharePoint privato

Costo: ~600€/mese
Setup: ~10.000€

═══════════════════════════════════════════════════════
📅 ROADMAP 12 MESI

Mesi 1-2: Discovery + Design (10.000€)
Mesi 3-4: Setup architettura B (10.000€)
Mesi 3-7: Batch 1 Recupero Crediti (8 skill) + 
          Batch 2 Tributario (8 skill) (22.000€)
Mesi 8-10: Batch 3 Civile + Procedure (14 skill) (12.000€)
Mesi 11-12: Knowledge base + completamento (22 skill) 
            (10.000€)

PRICING FINALE:
- Setup totale: 64.000€
- Retainer post: 1.500€/mese (24 mesi minimo)

═══════════════════════════════════════════════════════
💰 ROI ATTESO ANNO 2

Tempo risparmiato annuale stimato: ~1.200 ore
Equivalente economico (€100/h media): ~120.000€/anno

Asset patrimoniale stimato (in caso di vendita studio): 
+€80-150K di valore residuo

═══════════════════════════════════════════════════════
```

---

## 10. Output deliverable

| Deliverable | Estensione | Note |
|-------------|-----------|------|
| Set di skill .md (25-200) | Markdown | Personalizzate per studio |
| Skill personalizzate per area | .md | Per ogni area pratica |
| Knowledge base giurisprudenziale | .md indicizzato | Per query naturale |
| Manuale skill repository | DOCX 25-40 pp | Onboarding nuovi assunti |
| Architettura tecnica | DOCX | Setup cloud/locale |
| Policy AI Usage tier-aware | DOCX 12-20 pp | Privacy-aware |

---

## 11. Integrazione con altre skill

### Skill di sistema
- **flusso-ai-studi-professionali**: orchestratore
- **ai-knowledge-skillization-studio**: metodologia trasversale
- **ai-privacy-tiered-architecture**: critica per legale (privacy alta)
- **ai-assessment-studio**, **ai-roadmap-progettazione**, **ai-implementazione-pilota**, **ai-manutenzione-evoluzione**: ciclo completo

### Skill legali K2-AI esistenti (knowledge base)
Tutte le skill K2-AI legali alimentano la costruzione skill cliente.

### Skill commerciali
- **lead-qualifier**: qualifica clienti legali
- **pricing-proposal-generator**: proposta commerciale (con pricing settoriale)
- **customer-success-manager**: gestione cliente

---

## 12. Errori comuni da evitare

- **Non promettere skillizzazione "totale"**: il valore reale è 40-60%, comunicarlo onestamente
- **Non sovraestendere il Tier 1 a tutte le aree**: penale e famiglia con grande cautela
- **Non saltare la sanitization rigorosa**: privacy in legale è critica
- **Non promettere sostituzione del giudizio professionale**: skill sono supporto, non sostituzione
- **Non costruire knowledge giurisprudenziale senza pulizia**: archivio messy = skill messy
- **Non sottovalutare la privacy**: legal richiede architettura più costosa di engineering
- **Non confondere studio M&A con studio recupero crediti**: pattern di skillizzazione diversi
- **Non applicare template senza personalizzazione titolare**: la voce del titolare è il valore
- **Non saltare la formazione su limiti delle skill**: il team deve sapere quando AI vs giudizio umano
- **Non promettere ROI ingegneria**: 5-15x è ingegneria, in legale 3-8x è realistico
- **Non saltare la dimensione deontologica**: ogni skill deve rispettare codice deontologico forense
- **Non sottovalutare il valore del Tipo D**: per studi legali, knowledge base interrogabile è asset enorme
