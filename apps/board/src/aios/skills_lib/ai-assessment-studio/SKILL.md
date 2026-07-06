---
name: ai-assessment-studio
description: Skill di Fase 1 — Assessment AI per studi professionali italiani. Esegue diagnosi della maturità AI dello studio su 6 dimensioni (cultura, processi, dati, tool, governance, persone), analisi gap normativi (GDPR, AI Act, DDL AI, codice deontologico), inventario archivio documentale, identificazione 3-5 progetti AI ad alto valore. Usa SEMPRE in fase iniziale di progetti consulenza AI per studi, oppure quando il cliente dice assessment AI studio, valutazione maturità AI, dove sta il mio studio con AI, audit AI per professionisti, gap analysis AI. Genera report assessment 30-50 pagine, matrice maturità XLSX, intervista titolare, mappatura archivio, lista progetti prioritari, business case preliminare. Pricing 3.5-12K euro a seconda dimensione studio. NON usare per implementazione AI tool, per skillizzazione archivio, per design architetturale, per consulenza generica non AI.
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
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --limit 5
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

Knowledge pack norme: (skill generalista — nessun pack)

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# ai-assessment-studio — Fase 1: Assessment AI per studi professionali

## 1. Cosa fa questa skill

Questa skill esegue la **fase di discovery e diagnosi** di ogni progetto K2-AI per studi professionali. È il punto di ingresso operativo dopo che l'orchestratore ha identificato il cliente come candidato AI Assessment.

L'obiettivo è duplice:

**Per il cliente professionista**: ottenere una **fotografia oggettiva e strutturata** del suo studio rispetto all'introduzione di AI. Senza assessment serio, la maggior parte dei professionisti italiani sceglie tool AI sull'onda emotiva (cosa fa il collega, cosa ha letto sul giornale) anziché sui propri processi e bisogni reali. Risultato: 60-70% dei progetti AI non strutturati falliscono entro 12 mesi.

**Per K2-AI**: stabilire la **base credibile** per la proposta successiva (roadmap + implementazione). Un assessment ben fatto aumenta il conversion verso il pacchetto STANDARD/PREMIUM dal 30% al 65-75%, perché il cliente vede dati e non vendite.

L'output è un **report assessment** di 30-50 pagine che mappa:
- Processi attuali dello studio (workflow, tempo, persone, strumenti)
- Livello di maturità AI (0-3) misurato su 6 dimensioni
- Gap analysis normativa (AI Act, GDPR, DDL AI, codice deontologico)
- 5-15 quick win con effort e ROI stimati
- 3-5 progetti strategici per i 12-24 mesi
- Roadmap preliminare con prioritizzazione
- Draft di policy AI usage personalizzata per lo studio

Durata tipica fase: **3-4 settimane**. Pricing pacchetto STARTER: **3.500-5.500€**.

---

## 2. Quando attivarsi

### Trigger (oltre l'orchestratore)
- "Da dove parto con AI nel mio studio?"
- "Voglio capire se ha senso introdurre AI"
- "Audit AI studio"
- "Diagnosi AI"
- "Come stiamo messi con AI?"
- "Devo conformarmi all'AI Act?"
- "AI assessment studio"

### Quando NON attivarsi
- Per cliente già in fase di selezione tool (vai a ai-roadmap-progettazione)
- Per cliente che ha già implementato e vuole ottimizzare (vai a ai-manutenzione-evoluzione)
- Per studio con <2 professionisti che usa AI già strutturatamente (probabilmente non serve assessment formale, basta consulenza puntuale)

---

## 3. Le 6 dimensioni di maturità AI

Il framework K2-AI valuta lo studio su 6 dimensioni, ciascuna scorata 0-3.

### Dimensione 1 — People & Skills (cultura interna)
- Competenze AI attuali del team (titolari + collaboratori)
- Atteggiamento verso AI (entusiasta / scettico / paura)
- Esperienze precedenti con tool AI
- Disponibilità all'apprendimento
- Resistenze esplicite o implicite

### Dimensione 2 — Processes & Workflows (operatività)
- Processi standardizzati esistenti
- Documentazione interna dei processi
- Identificazione di tasks ripetitivi candidati ad AI
- Eventuali template/checklist consolidate
- Time tracking attuale (se presente)

### Dimensione 3 — Technology Stack (infrastruttura)
- Software gestionale studio in uso (es. Lexdoit, TeamSystem, Profis, Visualstudio Pelv, ecc.)
- Cloud / on-premise / ibrido
- Email + storage documenti
- Sistemi di comunicazione interna
- Eventuali tool AI già usati (anche occasionalmente)

### Dimensione 4 — Data & Knowledge Management (asset informativi)
- Volume e qualità documentale (atti, fatture, lettere, perizie, ecc.)
- Struttura archivio (cartelle, naming, ricercabilità)
- Database clienti
- Knowledge management interno (precedenti, casi, formulari)
- Backup e governance dati

### Dimensione 5 — Compliance & Governance (regole interne)
- Policy interne esistenti su uso tecnologie
- Procedure GDPR strutturate
- DPO designato (se obbligo)
- Eventuali procedure di gestione casi AI
- Coscienza normativa AI Act / DDL AI / deontologia

### Dimensione 6 — Strategy & Vision (visione direzionale)
- Visione del titolare/soci sul futuro dello studio
- Apertura a nuovi servizi AI-enabled per i clienti
- Tolleranza al rischio innovativo
- Orizzonte temporale di pianificazione
- Eventuali stimoli da clienti grandi

### Calcolo del Maturity Score

Score totale = somma punteggi 6 dimensioni / 18 × 100

Classificazione:
- **0-25**: Livello 0 — Awareness (ignaro / scettico)
- **26-50**: Livello 1 — Exploration (curioso, sperimenta singolarmente)
- **51-75**: Livello 2 — Pilot (ha avviato esperimenti strutturati)
- **76-100**: Livello 3 — Adoption (AI integrata in processi core)

La maggior parte degli studi italiani al 2026 si colloca tra **Livello 0 e 1** (60-70%).

---

## 4. Workflow operativo dell'assessment

L'assessment è strutturato in **5 step operativi distribuiti su 3-4 settimane**.

### Step 1 — Kick-off + raccolta documentale (settimana 1, giorni 1-3)

#### Kick-off call (90 min)
Partecipanti: titolare/i + eventuali soci + (se possibile) office manager.

Agenda:
- Presentazione metodologia K2-AI (15 min)
- Aspettative e obiettivi cliente (20 min)
- Vincoli e preoccupazioni (15 min)
- Timeline + deliverable + persone coinvolte (20 min)
- Avvio raccolta documenti (20 min)

#### Documentazione richiesta al cliente
Email post-kick-off con checklist documentale precisa:

**Obbligatori**:
- Organigramma studio (chi fa cosa, livelli gerarchici)
- Lista software in uso (gestionale, email, cloud, CRM, altri)
- Volume cause/incarichi/pratiche annue medie
- Tariffario / pricelist studio (se esiste)
- Eventuali procedure interne documentate (anche solo word)

**Auspicabili (non bloccanti)**:
- Sample di 5-10 documenti tipici (anonimizzati): es. lettera tipo, atto tipo, perizia, fattura, contratto
- Eventuali metriche di studio (fatturato, clienti attivi, ticket medio)
- Eventuali commenti/feedback clienti su servizio
- Eventuali analisi precedenti di consulenti

**Per compliance**:
- DPIA esistenti (se ci sono)
- Eventuale informativa GDPR cliente
- Eventuale registro trattamenti
- DPO designato (nome e contatto, se applicabile)

#### Output Step 1
- Memo kick-off (interno K2-AI)
- Checklist documentale inviata al cliente
- Setup cartella progetto condivisa (Drive/Notion)

### Step 2 — Mappatura processi (settimana 1-2, giorni 4-10)

#### Interviste strutturate
Una intervista 60-90 min per ogni "ruolo chiave":
- Titolare/i (visione + processi strategici)
- Soci/Senior (processi operativi core)
- Collaboratori junior (processi di esecuzione)
- Office manager / segreteria (processi amministrativi)

Tipicamente 3-5 interviste per studio piccolo, 5-10 per studio medio.

#### Domande chiave per intervista

Per ogni ruolo, esplora:
- "Descrivi una giornata tipo. Come la organizzi?"
- "Quali attività ti consumano più tempo?"
- "Quali errori ricorrenti vedi nel tuo lavoro o in quello dei colleghi?"
- "Cosa vorresti automatizzare se potessi?"
- "Cosa NON vorresti mai automatizzare? Perché?"
- "Hai mai usato strumenti AI? Cosa ti ha spinto/fermato?"
- "Cosa ti preoccupa dell'AI?"

#### Process mapping
Sulla base di interviste + documentazione, costruire **matrice di processi**:

| Processo | Frequenza | Tempo unitario | Persone coinvolte | Tool attuali | Pain points |
|----------|-----------|----------------|-------------------|--------------|-------------|
| Es. drafting lettera diffida | 3-5/settimana | 45 min | Avv. senior | Word | Ripetitivo, struttura simile |
| Es. ricerca giurisprudenza | 10/settimana | 90 min | Praticante | Google + DeJure | Tempo, completezza |

Tipicamente identificare 30-60 processi distinti per studio piccolo, 50-100 per studio medio.

#### Output Step 2
- Matrice processi completa (Excel)
- Note interviste (interno)
- Mappa visuale workflow tipo dello studio

### Step 3 — Maturity assessment + gap analysis (settimana 2-3, giorni 11-15)

#### Scoring 6 dimensioni
Per ogni dimensione, valuta evidenze raccolte e attribuisci punteggio 0-3 con motivazione.

#### Calcolo Maturity Score globale

#### Gap analysis normativa
Per ogni vincolo normativo, valutare conformità attuale:

**AI Act**:
- Lo studio usa o intende usare sistemi AI ad alto rischio? (es. assistenza decisionale automatica)
- Conformità ai requisiti di trasparenza
- Documentazione dei sistemi AI in uso

**GDPR**:
- DPIA per nuovi trattamenti AI-based
- Adeguatezza informative
- Trasferimenti extra-UE (molti tool AI hanno server US)
- Profilazione automatica e consenso

**DDL AI italiano** (per settori coperti):
- Sanità: requisiti specifici per AI in supporto diagnostico
- Giudiziario: requisiti per AI in supporto a decisioni
- Lavoro: AI in selezione e valutazione

**Codice deontologico settoriale**:
- Riferimento a skill settoriale ai-studio-{settore} per dettagli
- Es. avvocati: artt. 14, 19 Codice Deontologico Forense
- Es. medici: artt. 14, 78 Codice Deontologia Medica

#### Output Step 3
- Maturity Assessment Report (15-25 pagine)
- Gap Analysis matrix
- Risk register normativa

### Step 4 — Identificazione opportunità (settimana 3, giorni 16-19)

#### Quick win identification
Dalla matrice processi, identifica processi candidati a AI con:
- **Alto impatto**: tempo risparmiabile >2h/settimana
- **Basso effort**: implementabile con tool ready in <2 settimane
- **Basso rischio**: no impatto su decisioni critiche o dati ultra-sensibili

Tipicamente 5-15 quick win per studio piccolo.

Esempio matrice quick win:

| Quick Win | Processo | Tool consigliato | Effort | Tempo risparmio | Risk | Priority |
|-----------|----------|-------------------|--------|-----------------|------|----------|
| QW1 | Drafting prima bozza email cliente | ChatGPT/Claude + template | Basso (1 sett) | 3h/settimana | Basso | Alta |
| QW2 | Trascrizione registrazioni audio | Whisper/Otter | Basso (3 gg) | 5h/settimana | Basso | Alta |
| QW3 | Riassunto sentenze lunghe | Claude / NotebookLM | Basso (1 sett) | 4h/settimana | Medio | Media |

#### Strategic projects identification
Progetti più ambiziosi che richiedono mesi di implementazione:
- **Custom GPT/agente** per practice area specifica (es. avvocato civilista)
- **Knowledge base AI** dello studio (RAG su archivio storico)
- **Servizio AI-enabled per clienti** (es. pre-screening automatico)
- **Workflow automation completo** di un macro-processo

Tipicamente 3-5 progetti strategici per studio piccolo, 5-10 per medio.

#### ROI stimato
Per ogni opportunità, stima:
- **Costo implementazione** (tool + tempo K2-AI + tempo studio)
- **Costo ricorrente** (licenze tool, manutenzione)
- **Tempo risparmiato** (h/settimana × costo orario)
- **Payback period** (mesi)

Esempio:
- QW2 trascrizione audio: costo 200€/mese tool + 40h K2-AI implementazione (3.500€) → risparmio 5h/settimana × 60€/h × 4 sett = 1.200€/mese → payback 4 mesi.

#### Output Step 4
- Quick wins matrix (Excel)
- Strategic projects portfolio
- ROI estimates per progetto
- Heat map opportunità (visuale)

### Step 5 — Roadmap preliminare + report finale (settimana 3-4, giorni 20-28)

#### Roadmap preliminare 12 mesi
Sequenziamento delle opportunità:
- **Mesi 1-3**: 3-5 quick win (apprendimento + ROI immediato)
- **Mesi 4-6**: 2-3 quick win avanzati + avvio 1 progetto strategico
- **Mesi 7-9**: completamento 1° progetto strategico + avvio 2°
- **Mesi 10-12**: 2° progetto strategico + scaling

NB: questa è solo preliminare. La roadmap dettagliata viene fatta in Fase 2 (ai-roadmap-progettazione).

#### Draft policy AI usage
Documento operativo personalizzato sullo studio (5-10 pagine):
- Casi d'uso AI consentiti
- Casi d'uso AI vietati
- Tool autorizzati
- Procedure per dati clienti
- Disclaimer obbligatori
- Responsabilità professionale
- Aggiornamento e formazione

#### Report finale assessment
Documento DOCX 30-50 pagine strutturato:

1. **Executive summary** (2 pp) — sintesi per decisore
2. **Profilo studio** (2 pp) — chi sono, cosa fanno, dimensione
3. **Metodologia assessment** (1 p)
4. **Mappa processi** (5-7 pp)
5. **Maturity assessment 6 dimensioni** (8-10 pp)
6. **Gap analysis normativa** (4-6 pp)
7. **Quick wins identificati** (5-8 pp)
8. **Progetti strategici** (4-6 pp)
9. **ROI complessivo stimato** (1-2 pp)
10. **Roadmap preliminare 12 mesi** (2-3 pp)
11. **Raccomandazioni operative** (2-3 pp)
12. **Allegati**: matrice processi, draft policy, risk register

#### Workshop di restituzione (90 min)
Presentazione finale con:
- Walk-through report
- Discussione raccomandazioni
- Confronto su priorità
- Definizione next step (proposta Fase 2 / Roadmap)

#### Output Step 5
- AI-Assessment-Report-{Studio}-{YYYYMM}.docx (30-50 pp)
- AI-Assessment-Matrices-{Studio}.xlsx
- AI-Policy-Draft-{Studio}.docx
- Slides workshop di restituzione (PPTX 20-30 slide)
- Memo workshop (interno)

---

## 5. Esempio applicato — Studio Legale Rossi (Bologna, 5 prof)

### Input dall'orchestratore
"Studio Legale Bologna 5 prof, civile + contenzioso, Maturità 1, vuole AI assessment per AI Act e strutturare uso esistente. Pacchetto STARTER 4.500€, ai-studio-legale da attivare."

### Output sintetico assessment

```
═══════════════════════════════════════════════════════
AI ASSESSMENT — Studio Legale Rossi
═══════════════════════════════════════════════════════

📊 Profilo: 5 professionisti (3 soci, 2 collaboratori)
   Specializzazione: civile + contenzioso
   Volume: ~150 cause attive, ~400 lettere/anno
   Software: Lexdoit, Office 365, DropBox

🎯 MATURITY SCORE: 38/100 — LIVELLO 1 (Exploration)

Dimension breakdown:
- People & Skills: 1.5/3 (curiosi ma no formazione)
- Processes & Workflows: 1/3 (poco standardizzati)
- Technology Stack: 2/3 (gestionale ok)
- Data & Knowledge: 1.5/3 (archivio ricco ma poco organizzato)
- Compliance: 1/3 (no policy AI, GDPR base)
- Strategy & Vision: 1/3 (no visione articolata)

═══════════════════════════════════════════════════════
🚨 GAP ANALYSIS NORMATIVA

AI Act: ⚠ MEDIO RISCHIO
   - Non hanno mappato sistemi AI in uso (ChatGPT 
     occasionale = sistema AI ai sensi dell'art. 3)
   - Manca policy interna su uso AI per dati clienti

GDPR: ⚠ MEDIO RISCHIO  
   - Trasferimento dati a OpenAI (USA) senza valutazione
   - Manca DPIA per uso AI su dati cliente

Codice Deontologico Forense:
   - Art. 19 (segreto): rischio se dati cliente in 
     prompt ChatGPT senza tutele
   - Art. 14 (competenza): obbligo formazione tecnologica
   
DDL AI italiano (in approvazione):
   - Probabili obblighi di trasparenza con cliente

═══════════════════════════════════════════════════════
✅ TOP 8 QUICK WIN IDENTIFICATI

QW1 — Trascrizione registrazioni clienti
   Tool: Otter.ai con account UE
   Effort: 1 settimana | ROI: 5h/settimana
   Risparmio annuo stimato: €15.600
   Risk: Basso (con consenso cliente)

QW2 — Drafting prima bozza lettera diffida
   Tool: Claude Pro / ChatGPT Team con custom GPT
   Effort: 2 settimane | ROI: 3h/settimana
   Risparmio annuo: €9.360

QW3 — Ricerca giurisprudenza assistita
   Tool: Lexis Italia AI (€89/mese aggiuntivo) 
   o NotebookLM gratuito
   Effort: 1 settimana | ROI: 4h/settimana
   Risparmio annuo: €12.480

QW4 — Riassunto atti avversari lunghi
   Tool: Claude Projects con archivio causa
   Effort: 1 settimana | ROI: 2h/settimana
   Risparmio annuo: €6.240

QW5 — Email automatizzate stato pratica
   Tool: integrazione Lexdoit + automazione
   Effort: 3 settimane | ROI: 2h/settimana
   Risparmio annuo: €6.240

QW6 — Calcolo automatico parcelle complesse
   Tool: GPT custom su tariffario
   Effort: 1 settimana | ROI: 1h/settimana
   Risparmio annuo: €3.120

QW7 — Estrazione dati da PDF (sentenze, atti)
   Tool: ChatGPT Vision / Claude Vision
   Effort: 1 settimana | ROI: 2h/settimana
   Risparmio annuo: €6.240

QW8 — Knowledge base interna (precedenti)
   Tool: NotebookLM su archivio + indicizzazione
   Effort: 4 settimane | ROI: 3h/settimana
   Risparmio annuo: €9.360

TOTALE potenziale Quick Wins: €68.640/anno
Costo cumulato licenze: ~€2.800/anno
NET annuo: ~€65.800

═══════════════════════════════════════════════════════
🎯 3 PROGETTI STRATEGICI PROPOSTI

PS1 — "Avvocato Augmented" 
   Custom GPT specializzato civilista bolognese 
   con jurisprudence locale, formularie, prassi  
   Tribunale Bologna
   Effort: 12 settimane | Investimento: 18.000€
   ROI atteso: 30+h/settimana team
   Payback: 8-10 mesi

PS2 — "Cliente Self-Service"
   Portale clienti con AI per FAQ, 
   stato pratica, documenti
   Effort: 16 settimane | Investimento: 25.000€
   ROI atteso: differenziazione + nuovi clienti

PS3 — "Compliance AI Center"
   Sistema interno per gestione AI Act 
   compliance + audit trail + DPIA semi-auto
   Effort: 8 settimane | Investimento: 12.000€
   ROI: protezione professionale + sales pitch

═══════════════════════════════════════════════════════
📅 ROADMAP PRELIMINARE 12 MESI

Mesi 1-3: 4 quick win (QW1, QW2, QW3, QW7)
   + setup policy AI usage
   + workshop formativo team (4h)

Mesi 4-6: 4 quick win residui (QW4, QW5, QW6, QW8)
   + avvio PS1 "Avvocato Augmented" (Phase 1)

Mesi 7-9: PS1 fase 2 + completamento + 
   eventuale PS3 "Compliance AI Center"

Mesi 10-12: PS3 completamento + valutazione PS2 
   "Cliente Self-Service" / scaling
   
═══════════════════════════════════════════════════════
📦 PROPOSTA FASE 2 — ai-roadmap-progettazione

Sulla base assessment, raccomando:
   - Pacchetto STANDARD AI Roadmap & Pilota: 16.500€
   - Durata: 5 mesi
   - Output: Roadmap dettagliata + Pilota su 4 quick win 
     primari + Workshop formativo + Policy ufficiale

═══════════════════════════════════════════════════════
📂 OUTPUT DELIVERABLE GENERATI:

1. AIAssessment-StudioRossi-202605.docx (42 pp)
2. AIAssessment-Matrici-StudioRossi.xlsx
3. AIPolicy-Draft-StudioRossi.docx (8 pp)
4. AIAssessment-Slides-StudioRossi.pptx (24 slide)

═══════════════════════════════════════════════════════
```

---

## 6. Output deliverable per pacchetto

### Pacchetto STARTER (3.500-5.500€)

| Documento | Estensione | Pagine |
|-----------|-----------|--------|
| AI Assessment Report | DOCX | 30-50 |
| Matrici Excel (processi, opportunità, ROI) | XLSX | 5-8 fogli |
| Draft Policy AI Usage | DOCX | 5-10 |
| Slides workshop di restituzione | PPTX | 20-30 |
| Workshop di restituzione | Live | 90 min |

### Pacchetto STANDARD/PREMIUM (incluso come prima fase)

Tutti i documenti sopra + integrazione con output Fase 2 (roadmap dettagliata).

---

## 7. Integrazione con altre skill

### Skill di sistema
- **flusso-ai-studi-professionali**: orchestratore che attiva questa skill
- **ai-studio-{settore}**: skill settoriale per casi d'uso e vincoli specifici

### Skill K2-AI di dominio
- **it-law-privacy-ai**: per dettagli AI Act, GDPR, DDL AI
- **knowledge-source-italia**: per fonti aggiornate normativa
- **diritto-italiano**: per principi di responsabilità professionale
- **fiscale-tributario-italiano**: per aspetti fiscali (es. iperammortamento AI)

### Skill K2-AI commerciali post-assessment
- **pricing-proposal-generator**: per proposta Fase 2 (Roadmap)
- **customer-success-manager**: per gestione cliente in retainer

### Skill produttive
- **docx**: report finale
- **xlsx**: matrici
- **pptx**: slides workshop

---

## 8. Errori comuni da evitare

- **Non saltare la kick-off call**: senza fiducia iniziale, il cliente non condividerà info sensibili
- **Non procedere senza documenti**: l'assessment basato solo su intervista è superficiale
- **Non intervistare solo il titolare**: i collaboratori vedono cose che il titolare non vede
- **Non confondere maturità tecnologica generale con maturità AI**: studio con gestionale ottimo può essere a Livello 0 di AI
- **Non promettere riservatezza assoluta dei dati al cliente**: alcune cose vanno condivise (anonimizzate) per analisi K2-AI interna
- **Non sopravvalutare il ROI di quick win**: cifre realistiche > cifre eroiche
- **Non sottovalutare resistenze umane**: il problema #1 in studi professionali italiani è il change management
- **Non saltare la gap analysis normativa**: è la parte di valore più alto per professionisti
- **Non chiudere con "tante cose da fare"**: dare 3-5 priorità chiare, non lista di 30 cose
- **Non concludere senza proposta Fase 2**: il momento del workshop di restituzione è il momento di vendita migliore
- **Non promettere conformità AI Act garantita**: K2-AI mappa, l'avvocato/DPO formalizza
- **Non ignorare la dimensione personale**: titolare anziano scettico richiede approccio diverso da junior entusiasta
