---
name: ai-roadmap-progettazione
description: Skill di Fase 2 — Progettazione roadmap AI per studi professionali. Sulla base dell'assessment, costruisce piano operativo 12-24 mesi con scelta tool e vendor (matrice 10 criteri), architettura tecnica, business case dettagliato, perimetro pilota. Usa SEMPRE dopo assessment completo, oppure quando cliente dice roadmap AI studio, piano implementazione AI, quali tool AI scegliere, business case AI per studio, vendor selection AI. Differenzia per settore (legal, medical, ingegneria, notarile) e per pacchetto (STARTER, STANDARD, PREMIUM). Tassonomia 6 categorie tool, evaluation framework vendor, configurazione architettura cloud o privata, calcolo ROI 24-36 mesi, identificazione perimetro pilota. Output roadmap dettagliata, vendor matrix, business case, Gantt 18 mesi. Pricing 8-25K euro. NON usare per assessment iniziale (Fase 1), per implementazione concreta (Fase 3), per skillizzazione metodologica.
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
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --materia civile --limit 5
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

Knowledge pack norme: `~/normattiva_ai/knowledge_packs/civile/`

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# ai-roadmap-progettazione — Fase 2: Roadmap e progettazione AI per studi professionali

## 1. Cosa fa questa skill

Questa skill esegue la **fase di progettazione strategica e tecnica** dopo l'assessment. È il momento in cui le opportunità identificate vengono trasformate in **piano operativo concreto, comparabile, decidibile**.

Il valore strategico è duplice:

**Per il cliente professionista**: trasforma l'incertezza ("ho mille opzioni") in chiarezza decisionale ("queste sono le 3 mosse, in questo ordine, con questo budget, con questi rischi"). Il 70% dei progetti AI fallisce in fase di progettazione perché si sceglie il tool sbagliato per il proprio contesto. Questa skill mitiga il rischio con vendor selection metodologica.

**Per K2-AI**: è la fase dove si vince il pacchetto STANDARD/PREMIUM (15.000-80.000€). Una roadmap ben fatta è il documento che giustifica l'investimento maggiore e attiva il commitment pluriennale. Inoltre, è la fase in cui si definisce l'architettura tecnica, i partner di implementazione (vendor stack), e i criteri di successo che guideranno la Fase 3.

L'output principale è una **roadmap dettagliata 12-24 mesi** con:
- 8-15 progetti specifici prioritizzati
- Vendor matrix per ogni progetto (3-5 alternative valutate)
- TCO (Total Cost of Ownership) per opzioni
- Business case con ROI, payback, scenario analysis
- Architettura tecnica integrata
- Risk register dettagliato
- Proposta operativa Fase 3

Durata tipica fase: **4-8 settimane**. Pricing tipico: **6.000-15.000€** (incluso in pacchetto STANDARD).

---

## 2. Quando attivarsi

### Trigger
- "Roadmap AI per studio"
- "Quale tool AI scegliere"
- "Comparare ChatGPT, Claude, Gemini, Copilot"
- "Business case AI"
- "Studio fattibilità AI"
- "Vendor selection AI"
- "Build vs buy AI"
- "Architettura AI studio"

### Quando NON attivarsi
- Cliente non ha completato assessment (vai a ai-assessment-studio)
- Cliente ha già scelto tool e vuole implementare (vai a ai-implementazione-pilota)
- Cliente ha implementato e vuole ottimizzare (vai a ai-manutenzione-evoluzione)

---

## 3. Framework di selezione e progettazione

### 3.1 Tassonomia dei tool AI per studi professionali

I tool si raggruppano in **6 categorie funzionali**:

**Categoria 1 — General Purpose LLM (chat assistente)**
- ChatGPT Plus/Team/Enterprise (OpenAI)
- Claude Pro/Team/Enterprise (Anthropic)
- Gemini Advanced (Google)
- Microsoft Copilot Pro / 365 Copilot
- Perplexity Pro

Uso tipico: drafting, brainstorming, ricerca, riassunti.

**Categoria 2 — Document Intelligence (OCR, estrazione, classificazione)**
- Adobe Acrobat AI / Acrobat Pro
- DocuSign + AI (per studio legale)
- Microsoft Syntex
- Google Document AI
- Soluzioni italiane verticali (es. iText)

Uso tipico: digitalizzazione archivi, estrazione dati da documenti, classificazione.

**Categoria 3 — Specialized Vertical AI (settore-specifico)**

Per settore legale:
- Lexis+ AI (italiano disponibile)
- Westlaw Edge (USA, parziale italiano)
- DeJure AI (Wolters Kluwer)
- Giuffrè OneLEGALE AI
- Harvey AI (premium, segmento alto)

Per settore medico:
- Pixee Medical
- Boppli Medical
- Tempus AI
- Doximity GPT

Per settore commercialista:
- TeamSystem AI
- Wolters Kluwer Profis AI
- Datev AI

Per altri settori: skill settoriale ai-studio-{settore} fornisce vendor list aggiornata.

**Categoria 4 — Audio/Video AI (trascrizione, traduzione, generazione)**
- Otter.ai (trascrizione meeting)
- Whisper (OpenAI, open source)
- Descript (audio/video editing)
- Loom AI (video aziendali)

**Categoria 5 — Workflow & Automation (no-code/low-code)**
- Zapier + AI (integrazione tool)
- Make.com (ex Integromat)
- Microsoft Power Platform + Copilot Studio
- n8n (open source, self-hosted)

**Categoria 6 — Custom GPT / Agent Building**
- OpenAI GPTs / Assistants API
- Claude Projects
- Anthropic Agent SDK
- Custom development con API

### 3.2 Matrice di valutazione tool (10 criteri K2-AI)

Per ogni candidato tool, valutazione 0-5 su:

1. **Functional Fit** — corrispondenza ai casi d'uso identificati nell'assessment
2. **Quality of Output** — accuratezza, qualità linguistica italiana, attinenza
3. **Compliance Posture** — conformità GDPR, AI Act, DDL AI, certificazioni (ISO 27001, SOC2)
4. **Data Residency** — dove sono i dati (UE preferito), trasferimenti extra-UE
5. **Integration** — integrazione con stack esistente dello studio
6. **Pricing Sustainability** — costo proporzionato a budget studio
7. **Vendor Stability** — affidabilità fornitore, longevità prevedibile
8. **Support & Documentation** — supporto in italiano, qualità docs
9. **Adoption Curve** — facilità di formazione team
10. **Strategic Fit** — coerenza con visione studio e direzione settore

Score totale ponderato → ranking tool.

### 3.3 Build vs Buy decision framework

Per ogni opportunità identificata, decisione:

**BUY (tool ready)**: 
- Quando esiste tool specifico ben fatto
- Effort < 4 settimane
- Costo licenza ragionevole
- Vendor affidabile

**BUILD/CUSTOMIZE (custom GPT, agente custom)**:
- Quando il tool generico non basta
- Quando il dato è proprietary (knowledge studio)
- Quando il vincolo deontologico richiede controllo
- Quando il differenziale competitivo è la customizzazione

**HYBRID (tool + customizzazione)**:
- Default per la maggior parte degli studi
- Es. Claude Projects + custom GPT su archivio + integrazioni Zapier

### 3.4 Architettura di riferimento tipica per studio professionale

Pattern raccomandato per studi 2-15 prof:

```
┌──────────────────────────────────────────────────────┐
│  LIVELLO INTERFACCIA (cosa usa il professionista)   │
│  - Browser web (ChatGPT, Claude, Gemini)             │
│  - Plugin Office (Copilot)                           │
│  - App custom GPT in chat                            │
└──────────────────────────────────────────────────────┘
                        │
┌──────────────────────────────────────────────────────┐
│  LIVELLO LLM (cervello generativo)                   │
│  - Primary: Claude Pro/Team o ChatGPT Team           │
│  - Specialized: Lexis+ AI / DeJure AI / DocAI        │
└──────────────────────────────────────────────────────┘
                        │
┌──────────────────────────────────────────────────────┐
│  LIVELLO KNOWLEDGE (dati dello studio)               │
│  - Claude Projects / NotebookLM (RAG)                │
│  - SharePoint / Drive (storage)                      │
│  - Database clienti gestionale                       │
└──────────────────────────────────────────────────────┘
                        │
┌──────────────────────────────────────────────────────┐
│  LIVELLO AUTOMAZIONE (workflow)                      │
│  - Zapier / Make per integrazioni                    │
│  - Power Automate / n8n                              │
└──────────────────────────────────────────────────────┘
                        │
┌──────────────────────────────────────────────────────┐
│  LIVELLO GOVERNANCE                                  │
│  - Policy AI usage                                   │
│  - Audit log                                         │
│  - DPIA per nuovi sistemi                            │
└──────────────────────────────────────────────────────┘
```

---

## 4. Workflow operativo

### Step 1 — Review assessment + sintesi opportunità (settimana 1)

Riprende output Fase 1:
- Lista quick win
- Lista progetti strategici
- ROI stime preliminari
- Vincoli e priorità cliente

Operazioni:
- Ricontatta cliente per confermare priorità
- Raccoglie eventuali aggiornamenti
- Verifica budget effettivo disponibile
- Conferma orizzonte temporale

### Step 2 — Approfondimento casi d'uso (settimana 1-2)

Per ogni opportunità in shortlist (top 8-15), approfondisce:
- **Use case detail**: chi lo fa, quando, perché, output atteso, qualità richiesta
- **Volume preciso**: numero esecuzioni/mese
- **Sensibilità dati**: livello di confidenzialità
- **Output integration**: dove va il risultato dell'AI (email, doc, gestionale)
- **Approval workflow**: chi review prima di output cliente

Output: scheda dettagliata per ogni use case (1-2 pagine).

### Step 3 — Vendor research e shortlisting (settimana 2-3)

#### Long list candidati
Per ogni use case, identificare 5-10 tool candidati:
- Da database K2-AI (skill settoriale fornisce input)
- Da web search aggiornato (vendor landscape evolve rapidamente)
- Da raccomandazioni community professionale italiana
- Da report di settore (Gartner, Forrester se accessibili)

#### Filtering criteri base
Eliminare candidati che falliscono criteri non negoziabili:
- ❌ No supporto italiano
- ❌ No conformità GDPR (server US senza SCC, no DPA)
- ❌ No vendor stability (startup <2 anni)
- ❌ Pricing fuori scala (>10x budget cliente)

#### Short list (3-5 candidati per use case)
I candidati che passano il filtering, valutati con matrice 10 criteri.

### Step 4 — Tool deep dive (settimana 3-4)

Per i tool top 3 di ogni shortlist:

#### Demo / trial
- Setup demo con vendor (eventualmente per K2-AI, non per cliente)
- Trial gratuito quando disponibile
- Test concreto su use case specifico cliente
- Valutazione output qualità

#### Reference call
- Quando possibile, parlare con altri studi italiani che usano il tool
- Network professionale K2-AI / contatti settoriali

#### TCO calculation per tool
- **One-time costs**: setup, training, customizzazione, migrazione dati
- **Recurring costs**: licenze (per utente, mensili o annuali), supporto
- **Hidden costs**: tempo apprendimento staff, storage cloud, eventuali API call costs
- **Stima 3 anni**: TCO totale 36 mesi

#### Output Step 4
- Schede dettagliate top 3 tool per use case
- TCO matrix
- Reference notes (anonimizzate)

### Step 5 — Architettura tecnica integrata (settimana 4-5)

Design dell'architettura overall che integra tool selezionati:

#### Architecture diagram
Visualizzazione con:
- Tool selezionati per livello
- Flussi di dati tra tool
- Punti di integrazione (API, plugin, manuali)
- Boundary security
- Touch point professionista

#### Data flow analysis
Per ogni dato sensibile:
- Da dove parte
- Dove transita
- Dove si ferma
- Chi può accedervi
- Tempo di retention

#### Conformità normativa
Per architettura proposta:
- Verifica GDPR (DPIA se necessaria)
- Verifica AI Act (categoria di rischio)
- Verifica DDL AI italiano (se applicabile a settore)
- Verifica deontologia (skill settoriale)

### Step 6 — Business case + scenario analysis (settimana 5-6)

#### ROI quantificato per progetto
Per ogni progetto in roadmap:
- **Costi**: implementazione + ricorrenti × 36 mesi
- **Benefici**: tempo risparmiato × costo orario, errori ridotti, nuovi servizi
- **Net benefit cumulato 36 mesi**
- **Payback period**
- **NPV** (con discount rate 8%)
- **IRR**

#### Scenario analysis
Tre scenari:
- **Conservative**: ROI 60% del baseline (cose vanno meno bene)
- **Base case**: ROI baseline calcolato
- **Optimistic**: ROI 130% baseline (sinergie inattese)

Per ogni scenario, calcola payback e ROI 36 mesi.

#### Sensitivity analysis
Variabili chiave:
- Tempo risparmiato effettivo (-30% / 0 / +30%)
- Costo licenze (variazione +20%)
- Adoption rate team (50% / 80% / 100%)

Per ogni variabile, impatto su business case complessivo.

### Step 7 — Roadmap dettagliata 12-24 mesi (settimana 6-7)

#### Sequenziamento progetti

Logica di prioritizzazione:
- **Wave 1 (mesi 1-3)**: 3-5 quick win con effort < 2 settimane ciascuno + setup governance base
- **Wave 2 (mesi 4-6)**: 2-3 quick win avanzati + avvio 1 progetto strategico tier 1
- **Wave 3 (mesi 7-12)**: completamento progetto strategico + avvio 2° + scaling quick win
- **Wave 4 (mesi 13-24)**: progetti strategici tier 2/3 + ottimizzazione continua + scaling

Per ogni wave:
- Progetti specifici
- Owner (interno studio + K2-AI + vendor)
- Milestone con date
- Budget allocato
- KPI di successo

#### Capacity planning
- Tempo richiesto al team interno per ogni progetto
- Eventuali figure aggiuntive necessarie
- Effort K2-AI in giornate/uomo

### Step 8 — Risk register dettagliato (settimana 7)

Per ogni rischio identificato:
- **Categoria**: tecnico, normativo, organizzativo, finanziario
- **Probabilità**: bassa/media/alta
- **Impatto**: basso/medio/alto/critico
- **Mitigazione**: azione preventiva
- **Contingenza**: piano B se materializza
- **Owner**: chi monitora

Tipici rischi per studi professionali:
- Resistenza staff a change (organizzativo, alto, frequente)
- Tool vendor che cambia pricing/policy (finanziario, medio)
- AI Act enforcement più stringente del previsto (normativo, medio)
- Data breach via tool AI (tecnico, alto, critico)
- Cliente perde fiducia per uso AI (relazionale, medio)
- ROI inferiore al previsto (finanziario, medio)

### Step 9 — Proposta operativa Fase 3 (settimana 7-8)

#### Documento di proposta
DOCX 25-40 pagine strutturato:

1. **Executive summary** (2-3 pp)
2. **Recap assessment** (2 pp)
3. **Roadmap dettagliata** (5-7 pp)
4. **Vendor selection completa** (5-8 pp)
5. **Architettura tecnica** (3-4 pp)
6. **Business case e scenari** (3-5 pp)
7. **Risk register** (2-3 pp)
8. **Piano implementazione Fase 3** (3-5 pp)
9. **Pricing e pacchetti** (1-2 pp)
10. **Timeline e milestone** (1-2 pp)
11. **Allegati** (vendor schede, TCO matrix, etc)

#### Workshop di presentazione (120 min)
Presentazione dettagliata:
- Walk-through proposta
- Discussione architettura
- Comparazione opzioni
- Decisioni operative su vendor (con cliente che sceglie)
- Definizione go/no-go per Fase 3
- Sign-off proposta

---

## 5. Esempio applicato — Studio Legale Rossi (Fase 2)

### Input dall'assessment (Fase 1 completata)
Maturity 38/100, 8 quick win identificati, 3 progetti strategici, ROI annuo potenziale €68.640. Cliente conferma interesse a procedere con Pacchetto STANDARD AI Roadmap & Pilota (16.500€).

### Output sintetico Fase 2

```
═══════════════════════════════════════════════════════
AI ROADMAP & DESIGN — Studio Legale Rossi
═══════════════════════════════════════════════════════

🎯 OPPORTUNITÀ CONFERMATE: 8 quick win + 1 progetto 
   strategico priorità (PS1 "Avvocato Augmented")

📦 VENDOR SELECTION TOP 3 PER USE CASE PRINCIPALE

USE CASE 1: Drafting bozze lettere/atti
Score Vendor (10 criteri):

| Tool | Score | Pricing 5 utenti |
|------|-------|------------------|
| Claude Pro Team | 4.4/5 ✅ | €100/mese |
| ChatGPT Team | 4.2/5 | €125/mese |
| Microsoft Copilot 365 | 3.8/5 | €145/mese |

🏆 RACCOMANDATO: Claude Team
   Motivazione: 
   - Migliore qualità output italiano
   - Server EU disponibili (Anthropic Frankfurt)
   - DPA standard fornito
   - Claude Projects integrato per knowledge

USE CASE 2: Ricerca giurisprudenza
| Tool | Score | Pricing 5 utenti |
|------|-------|------------------|
| Lexis+ AI Italia | 4.6/5 ✅ | €445/mese (5 utenti) |
| Wolters Kluwer DeJure AI | 4.0/5 | €380/mese |
| NotebookLM (Google) | 3.5/5 | Gratuito |

🏆 RACCOMANDATO: Lexis+ AI Italia
   Motivazione:
   - Database giurisprudenza italiana completo
   - AI specializzato dominio legale
   - Integrazione con normative aggiornate
   - Reference: 200+ studi italiani lo usano

USE CASE 3: Trascrizione audio
| Tool | Score | Pricing |
|------|-------|---------|
| Otter.ai Business EU | 4.3/5 ✅ | €17/utente/mese |
| Whisper API self-hosted | 3.8/5 | Variabile |
| Descript | 3.5/5 | €30/utente/mese |

🏆 RACCOMANDATO: Otter.ai Business EU

[Altri 5 use case con vendor selection completa...]

═══════════════════════════════════════════════════════
🏗 ARCHITETTURA TECNICA RACCOMANDATA

Stack consolidato:
├─ Claude Team (cuore generativo, 5 utenti, €100/m)
├─ Claude Projects (knowledge interno per area civile)
├─ Lexis+ AI (ricerca giurisprudenza, €445/m)
├─ Otter.ai (trascrizione, €85/m)
├─ NotebookLM (analisi atti lunghi, gratuito)
├─ Lexdoit (gestionale esistente, integrazione via 
│         Zapier, €25/m)
└─ Policy AI Usage v1.0 (governance K2-AI fornita)

📊 TCO 36 MESI: €36.420
   Year 1: €11.140 (include setup K2-AI)
   Year 2: €12.620
   Year 3: €12.660

═══════════════════════════════════════════════════════
💰 BUSINESS CASE

Scenario CONSERVATIVO (-30% efficacy):
- Risparmio annuo: €48.048
- Payback: 14 mesi
- ROI 36 mesi: 296%

Scenario BASE (assessment baseline):
- Risparmio annuo: €68.640
- Payback: 9 mesi
- ROI 36 mesi: 466%

Scenario OTTIMISTICO (+30% sinergie):
- Risparmio annuo: €89.232
- Payback: 7 mesi
- ROI 36 mesi: 635%

NPV (discount 8%, base case): €138.500
IRR: 87%

═══════════════════════════════════════════════════════
📅 ROADMAP DETTAGLIATA 18 MESI

Wave 1 (mesi 1-3): "Foundation"
- Setup Claude Team + Projects
- Setup Lexis+ AI
- Setup Otter.ai
- Workshop formativo team (8h totali)
- Policy AI Usage v1.0
- Quick win 1, 2, 3 implementati
- Budget: €5.500 K2-AI + €1.450 vendor

Wave 2 (mesi 4-6): "Acceleration"
- Quick win 4, 5, 6, 7 implementati
- Avvio "Avvocato Augmented" Phase 1 (custom GPT)
- KPI tracking attivato
- Budget: €4.500 K2-AI + €1.500 vendor

Wave 3 (mesi 7-12): "Strategic"
- "Avvocato Augmented" Phase 2 + 3 (knowledge base RAG)
- Quick win 8 implementato
- Audit interno conformità
- Budget: €6.500 K2-AI + €4.350 vendor

Wave 4 (mesi 13-18): "Optimization"
- Ottimizzazione su base dati 12 mesi
- Eventuale espansione casi d'uso
- Refresh tool + valutazione cambi
- Budget: retainer 800€/mese

═══════════════════════════════════════════════════════
🚨 RISK REGISTER (top 5)

R1 — Resistenza socio senior (60+ anni)
   Probabilità: ALTA | Impatto: ALTO
   Mitigation: workshop dedicato + buddy junior 
   Contingenza: implementazione progressiva, mai forzata

R2 — Lexis+ AI annuncia aumento prezzo (frequente)
   Probabilità: MEDIA | Impatto: MEDIO
   Mitigation: contratto biennale lock-in
   Contingenza: alternativa DeJure pronta

R3 — Cliente importante chiede no-AI policy
   Probabilità: BASSA | Impatto: ALTO
   Mitigation: comunicazione proattiva trasparente
   Contingenza: workflow segregato per quel cliente

R4 — Modifiche AI Act enforcement (2026-2027)
   Probabilità: MEDIA | Impatto: MEDIO
   Mitigation: monitoraggio mensile via K2-AI
   Contingenza: review architettura se necessario

R5 — Data breach via tool AI (improbabile ma critico)
   Probabilità: BASSA | Impatto: CRITICO
   Mitigation: vendor enterprise + policy stringente
   Contingenza: incident response plan attivato

═══════════════════════════════════════════════════════
📦 PROPOSTA FASE 3 — IMPLEMENTAZIONE PILOTA

Pacchetto raccomandato: STANDARD esteso (attivo)
Durata: 5 mesi (Wave 1 + Wave 2)
Investimento K2-AI: 10.000€ (incluso in pacchetto 
da 16.500€ già firmato)

Deliverable Fase 3:
- Implementazione tecnica completa
- Workshop formativi (3 sessioni × 2h)
- Policy AI Usage definitiva
- Manuale operativo per studio
- Cruscotto KPI implementato
- Affiancamento operativo 90 giorni

Successivamente: retainer 800€/mese per Wave 3 + 4 
(ai-manutenzione-evoluzione)

═══════════════════════════════════════════════════════
📂 OUTPUT DELIVERABLE GENERATI:

1. AIRoadmap-StudioRossi-202607.docx (38 pp)
2. AIVendorMatrix-StudioRossi.xlsx (8 fogli)
3. AIArchitecture-StudioRossi.pdf (diagramma)
4. AIBusinessCase-StudioRossi.xlsx (with scenari)
5. AIRiskRegister-StudioRossi.xlsx
6. AIRoadmap-Slides-StudioRossi.pptx (35 slide)

Workshop di presentazione: 120 min, calendarizzato 
settimana 8.

═══════════════════════════════════════════════════════
```

---

## 6. Output deliverable

### Pacchetto STANDARD/PREMIUM (Fase 2 inclusa)

| Documento | Estensione | Pagine/fogli |
|-----------|-----------|--------------|
| AI Roadmap & Design Report | DOCX | 25-40 |
| Vendor Matrix | XLSX | 8-12 fogli |
| Architecture Diagram | PDF/PNG | 1-3 |
| Business Case detailed | XLSX | con simulazione what-if |
| Risk Register | XLSX | 1 master |
| Slides Roadmap presentation | PPTX | 30-40 |

### Workshop di presentazione: 120 min live

---

## 7. Integrazione con altre skill

### Skill di sistema
- **flusso-ai-studi-professionali**: orchestratore
- **ai-assessment-studio**: input alla Fase 2 (deve essere completata prima)
- **ai-implementazione-pilota**: ricevente output (Fase 3)
- **ai-studio-{settore}**: knowledge settoriale, vendor specifici

### Skill K2-AI di dominio
- **it-law-privacy-ai**: per dettagli compliance
- **knowledge-source-italia**: per vendor research aggiornato
- **fiscale-tributario-italiano**: per agevolazioni fiscali (Transizione 5.0 include AI, super-ammortamento)
- **flusso-agevolazioni-pmi**: per identificare eventuali bandi che coprono parte investimento

### Skill K2-AI commerciali
- **pricing-proposal-generator**: per proposta formale Fase 3
- **teoria-dei-giochi-decisioni**: per scelte build/buy/hybrid complesse

### Skill produttive
- **docx, xlsx, pptx**: per deliverable

---

## 8. Errori comuni da evitare

- **Non saltare la review assessment**: cose possono essere cambiate dal cliente, sempre verificare priorità attuali
- **Non basare vendor selection su brand awareness**: tool meno noti possono essere migliori per contesto specifico
- **Non sottovalutare costi nascosti**: tempo apprendimento, customizzazione, integrazione spesso = 30-50% del costo licenza
- **Non usare TCO solo a 12 mesi**: 36 mesi minimo per decisioni vendor stratificate
- **Non scegliere tool senza demo concreta**: il marketing vendor mente sempre
- **Non ignorare la dimensione cultura interna**: tool migliore "sulla carta" può fallire se team lo rigetta
- **Non promettere ROI esatti**: scenario analysis con range, non valori puntuali
- **Non sottostimare il change management**: tipicamente 30-40% dell'effort totale
- **Non sceglier tool senza data residency UE**: rischio GDPR alto, soprattutto in dominio legale/medico
- **Non chiudere architettura senza disclaimer manutenibilità**: stack AI evolve rapidamente, design deve essere flessibile
- **Non saltare risk register**: il cliente deve sapere cosa può andar male
- **Non preparare workshop di presentazione senza prove**: demo live di tool durante workshop massimizza decisioni rapide
