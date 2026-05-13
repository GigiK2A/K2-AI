---
name: flusso-ai-studi-professionali
description: Orchestratore master per progetti di consulenza AI rivolti agli studi professionali italiani — legali, medici, commercialisti, notarili, ingegneri, architetti, psicologi, consulenti del lavoro. Coordina le 4 fasi metodologiche (assessment, roadmap, implementazione pilota, manutenzione evolutiva) e attiva le skill trasversali (privacy tiered, skillization knowledge) e settoriali (template engineering, legal, medical, notarial). Usa SEMPRE per richieste tipo consulenza AI studio professionale, AI per professionisti, digitalizzazione studio, AI Act studio, GDPR e AI per professionisti, formazione AI per avvocati medici notai commercialisti. Identifica settore, dimensione, fase del cliente, e instrada alle skill operative. Pacchetti STARTER 3.5-5.5K euro, STANDARD 12-22K, PREMIUM 35-80K più retainer 800-2.500 euro/mese. NON usare per consulenza AI a PMI generiche (vai a flussi-Boost), per implementazione tecnica AI tool, per consulenza professionale sostantiva.
---

# flusso-ai-studi-professionali — Orchestratore consulenza AI per studi professionali

## 1. Cosa fa questa skill

Questa skill è **l'orchestratore master di una nuova linea di business K2-AI ad altissimo potenziale**: la consulenza per l'introduzione di intelligenza artificiale negli studi professionali italiani. Risolve un problema strategico di mercato che sta esplodendo:

**Il contesto di mercato**: gli studi professionali italiani (circa 800.000 entità tra avvocati, commercialisti, medici, ingegneri, architetti, dentisti, notai, ecc.) si trovano nel 2026 in una fase di **adozione AI urgente ma confusa**. Tre forze convergenti:

1. **AI Act UE (Reg. 2024/1689)** in vigore con obblighi specifici per sistemi ad alto rischio usati da professionisti (es. assistenza decisionale medica, valutazioni economiche)
2. **DDL AI italiano** (in approvazione 2025-2026) che introduce disciplina specifica per AI in ambito sanitario, giudiziario, lavoro
3. **Pressione competitiva**: i clienti chiedono efficienza e i professionisti che adottano AI vincono i mandati. Chi non lo fa, perde quote di mercato del 5-10% l'anno.

**Il problema**: la maggior parte dei professionisti italiani ha letto qualcosa, ha provato ChatGPT, ma **non ha idea di come strutturare un'introduzione AI seria nel proprio studio**. Le opzioni sono troppe, i vincoli deontologici poco chiari, il rischio di sanzioni reale, gli investimenti senza ROI documentato sono frequenti.

**Il valore K2-AI**: posizionarsi come consulente metodologico di riferimento per questa transizione. Ticket medio progetto 8-50K€ + retainer 800-1.500€/mese. Mercato addressable Italia: 50.000+ studi nei prossimi 36 mesi.

L'orchestratore ha tre funzioni:

1. **Riconoscimento contesto**: identifica settore professionale + fase del percorso + maturità AI dello studio
2. **Routing dinamico**: instrada alla combinazione "skill di fase × skill settoriale" più appropriata
3. **Coordinamento multi-skill**: per richieste complesse, attiva più skill in parallelo o sequenza

---

## 2. Architettura del sistema

L'ecosistema AI per studi professionali è strutturato a 3 livelli.

### Livello 1 — Orchestratore (questa skill)
Riconosce, instrada, coordina. Tiene la metodologia comune e la roadmap commerciale.

### Livello 2 — 4 Skill di fase (settore-agnostiche)
Coprono il ciclo di vita del progetto di consulenza:

- **ai-assessment-studio** — Fase 1: discovery, mappatura processi, analisi maturità AI, raccolta requisiti, gap analysis
- **ai-roadmap-progettazione** — Fase 2: studio di fattibilità, selezione tool, business case, proposta operativa, prioritizzazione casi d'uso
- **ai-implementazione-pilota** — Fase 3: setup tecnico, training del personale, change management, esecuzione pilota controllato, governance
- **ai-manutenzione-evoluzione** — Fase 4: monitoring KPI, ottimizzazione continua, scaling progressivo, retainer evolutivo

### Livello 3 — Skill settoriali (knowledge dense, settore-specifiche)
Forniscono casi d'uso, normativa specifica, vincoli deontologici, tool consigliati, benchmark adozione, vendor di settore. Da costruire in fase 2:

- ai-studio-legale (avvocati)
- ai-studio-commercialista (dottori commercialisti, esperti contabili)
- ai-studio-medico (medici di base, specialisti, poliambulatori)
- ai-studio-dentistico (odontoiatri, ortodontisti)
- ai-studio-ingegneria (ingegneri civili, industriali, gestionali)
- ai-studio-architettura (architetti, paesaggisti)
- ai-studio-notarile (notai)
- ai-studio-consulenza-lavoro (consulenti del lavoro)
- + ulteriori settori (vedi sezione 9)

### Combinazione dinamica
L'orchestratore combina **skill di fase × skill settoriale** in 32+ combinazioni possibili (4 fasi × 8+ settori), garantendo profondità sia metodologica che settoriale.

---

## 3. Quando attivarsi

### Trigger espliciti

**Per qualsiasi settore professionale**:
- "Voglio introdurre AI nel mio studio"
- "AI per studi [legali / medici / commercialisti / ecc.]"
- "ChatGPT per professionisti"
- "Automatizzare lo studio con AI"
- "Quanto costa l'AI per un avvocato/commercialista/medico"
- "Quale AI usare nel mio studio"
- "AI Act e il mio studio"
- "DDL AI per avvocati / medici / ecc."
- "Trasformazione digitale studio"
- "Tool AI per professionisti"
- "ROI dell'AI per uno studio"

**Trigger relativi a fase specifica**:
- Fase 1 (Assessment): "Da dove partire con AI", "Stato attuale studio", "Non so se AI fa per me"
- Fase 2 (Progettazione): "Selezionare tool AI", "Roadmap AI studio", "Business case AI"
- Fase 3 (Implementazione): "Implementare ChatGPT in studio", "Formare il personale su AI", "Pilota AI"
- Fase 4 (Manutenzione): "Ottimizzare AI in studio", "Misurare ROI AI", "Scalare AI studio"

**Trigger contestuali**:
- Cliente professionista in customer-success-manager esprime interesse per AI
- Pubblicazione di nuovi obblighi normativi (AI Act high-risk, DDL AI)
- Sanzioni a studi per uso scorretto di AI (eventi mediatici)
- Richiesta clienti dello studio per servizi AI-enabled

### Quando NON attivarsi

- Per AI generativa **uso personale** non professionale (uso pubblico ChatGPT)
- Per implementazione AI in **PMI manifatturiere/ricettive/commerciali** (usare AdvisorBoost/StrategyBoost)
- Per **AI compliance generale** non specifica per studi professionali (it-law-privacy-ai)
- Per **sviluppo software AI da zero** (non è il dominio K2-AI)
- Per **consulenza tecnica avanzata** (LLM fine-tuning, ML engineering — richiede partner tecnico)
- Per **AI nei processi legali/giudiziali** dove serve avvocato specialista (consulenza giuridica vera)

---

## 4. Logica di routing

### Step 1 — Identificazione settore professionale

Domande di disambiguazione (se non chiaro dal contesto):

> "Per costruirti un percorso preciso, mi serve sapere:
> 1. Tipo di studio: legale / commercialista / medico / dentistico / ingegneria / architettura / notarile / altro
> 2. Numero professionisti + collaboratori
> 3. Specializzazione (es. diritto societario, fiscale aziendale, ortopedia, edilizia residenziale)
> 4. Sede principale (regione)"

Settore identificato → seleziona skill settoriale appropriata (se disponibile).

### Step 2 — Identificazione fase del percorso

Mapping dei trigger linguistici alle fasi:

**Fase 1 — Assessment** (se cliente):
- È al primo contatto con il tema AI
- Non ha mai usato sistematicamente AI
- Chiede "da dove iniziare", "ha senso per me?"
- Vuole capire opportunità senza commitment
- Ha provato qualcosa ma in modo non strutturato

**Fase 2 — Progettazione** (se cliente):
- Ha completato assessment (con K2-AI o autonomamente)
- Sa cosa vuole fare ma non come
- Chiede comparazioni tra tool
- Vuole business case quantificato
- Sta valutando investimenti specifici

**Fase 3 — Implementazione** (se cliente):
- Ha approvato roadmap e budget
- Vuole partire con pilota
- Chiede setup tecnico, training
- Si confronta con resistenza interna
- Definizione di workflow operativi

**Fase 4 — Manutenzione/Evoluzione** (se cliente):
- Ha già implementato (con K2-AI o altri)
- Cerca ottimizzazione, scaling
- KPI da monitorare
- Refresh stack tecnologico
- Espansione a nuovi processi

### Step 3 — Identificazione livello di maturità AI

Score 0-3 da estrarre da segnali:

- **Livello 0 (Awareness)**: ne ha sentito parlare, mai usato in studio
- **Livello 1 (Exploration)**: usa ChatGPT/Copilot occasionalmente come singolo, no integrazione
- **Livello 2 (Pilot)**: ha 1-2 tool integrati su processi specifici, sperimentale
- **Livello 3 (Adoption)**: AI integrata in 3+ processi core, governance presente

### Step 4 — Routing decisionale

Matrice fase × maturità → skill da attivare:

| Fase cliente | Skill di fase | Skill settoriale | Note |
|--------------|---------------|------------------|------|
| Fase 1 (Assessment) | ai-assessment-studio | ai-studio-{settore} (se disponibile) | Discovery prioritario |
| Fase 2 (Progettazione) | ai-roadmap-progettazione | ai-studio-{settore} | Tool selection settoriale |
| Fase 3 (Implementazione) | ai-implementazione-pilota | ai-studio-{settore} | Casi d'uso settoriali |
| Fase 4 (Manutenzione) | ai-manutenzione-evoluzione | ai-studio-{settore} | Trend settoriali |
| Multi-fase / strategico | Tutte e 4 + settoriali | Coordinamento orchestratore | Programmi integrati |

### Step 5 — Activation pattern

Per request standard: orchestratore → fase + settore (2 skill).

Per request complesso: orchestratore → 2 fasi + settore (es. "voglio capire stato attuale e proposta complessiva" = assessment + roadmap).

Per programma full: orchestratore → tutte e 4 fasi + settore + skill K2-AI commerciali (pricing-proposal-generator, customer-success-manager).

---

## 5. Posizionamento commerciale del programma

### Pacchetti standard K2-AI

**Pacchetto STARTER — "AI Assessment Studio"** (3.500-5.500€)
- Skill attivate: ai-assessment-studio + ai-studio-{settore}
- Durata: 3-4 settimane
- Output: report assessment 30-50 pagine, 5-10 quick win identificati, roadmap preliminare
- Target: studi al livello 0-1 di maturità che vogliono capire potenziale

**Pacchetto STANDARD — "AI Roadmap & Pilota"** (12.000-22.000€)
- Skill attivate: ai-assessment-studio + ai-roadmap-progettazione + ai-implementazione-pilota + ai-studio-{settore}
- Durata: 3-5 mesi
- Output: assessment + roadmap dettagliata + pilota implementato su 1-3 use case + training base personale
- Target: studi al livello 1-2 che vogliono percorso completo

**Pacchetto PREMIUM — "AI Transformation Studio"** (35.000-80.000€)
- Skill attivate: tutte le 4 fasi + skill settoriale + retainer 12 mesi
- Durata: 12-18 mesi
- Output: trasformazione AI completa su 5-10 processi + governance + KPI + scaling
- Target: studi medio-grandi (10+ professionisti) che vogliono diventare AI-first

**Retainer "AI Operations"** (800-2.500€/mese)
- Skill attivata: ai-manutenzione-evoluzione + skill settoriale
- Durata: ricorrente
- Output: monitoring continuo, aggiornamenti normativi, ottimizzazione, support
- Target: studi che hanno completato implementazione

### Pricing differenziato per settore

Settori a domanda alta + alto valore unitario (premium pricing):
- Legale (alti ticket, urgenza AI Act, processo elevato)
- Medico (compliance complessa, alto valore percepito)
- Notarile (audience piccola ma altissimo valore)

Settori standard (pricing base):
- Commercialisti, ingegneri, architetti
- Consulenti del lavoro, dentisti

### Pricing differenziato per dimensione studio

**Studio singolo (1 professionista)**: -25% sui pacchetti standard. Spesso solopreneur con budget limitato.

**Studio piccolo (2-5 prof)**: prezzi base.

**Studio medio (6-15 prof)**: +20-30%. Maggiore complessità di change management.

**Studio strutturato (16-50 prof)**: +50-100%. Multi-stakeholder, governance complessa.

**Network/multi-sede (50+)**: pricing custom (50-150K€). Spesso richiede project team dedicato.

---

## 6. Workflow operativo dell'orchestratore

### Step 1 — Prima discovery (5-10 min)

Domande prioritarie:
- Tipo di studio + dimensione
- Specializzazione professionale
- Stato attuale uso AI (se c'è)
- Cosa li ha spinti a contattarti adesso (trigger event)
- Eventuali esperienze precedenti di consulenza AI
- Aspettative principali

### Step 2 — Identificazione fase + maturità

Da risposte step 1, classifica in matrice.

### Step 3 — Routing skill

Attiva combinazione "skill di fase × skill settoriale" appropriata.

Se skill settoriale non ancora costruita, usa la skill di fase + nota di completare il knowledge gap settoriale via web search puntuale + gap-tracker per arricchimento futuro.

### Step 4 — Proposta percorso

Sulla base del routing:
- Se cliente in Fase 1: propone Pacchetto STARTER come entry point
- Se cliente in Fase 2: propone Pacchetto STANDARD oppure salta direttamente a Roadmap (se assessment già fatto)
- Se cliente in Fase 3-4: propone implementazione + retainer

Eventualmente chiama pricing-proposal-generator per documento commerciale formale.

### Step 5 — Esecuzione (delegata alla skill di fase)

L'orchestratore "passa la palla" alla skill di fase con un brief strutturato:

```
Cliente: [profilo]
Settore: [specifico]
Maturità AI: [livello]
Obiettivi dichiarati: [lista]
Vincoli: [budget, tempi, deontologici]
Output atteso: [specifico per fase]
Skill settoriale di supporto: [ai-studio-X o "non disponibile, usare web search"]
```

### Step 6 — Coordinamento multi-fase (se richiesto)

Per programmi complessi:
- Mantiene "stato del progetto" (output di una fase = input della successiva)
- Garantisce continuità metodologica
- Aggrega deliverable cross-fase per QBR/report finale

### Step 7 — Handoff a customer success

Una volta avviato programma, passa cliente a customer-success-manager per gestione lifecycle. L'orchestratore resta disponibile per richieste contestuali specifiche.

---

## 7. Quadro normativo di riferimento (panoramica)

L'orchestratore mantiene il riferimento normativo macro che le skill di fase e settoriali approfondiscono.

### Normativa UE
- **AI Act (Reg. UE 2024/1689)**: classificazione sistemi AI per livello di rischio. Sistemi "ad alto rischio" includono: assistenza decisionale in giustizia (avvocati), medicina diagnostica (medici), educazione, lavoro
- **GDPR (Reg. UE 2016/679)**: trattamento dati personali, particolare attenzione a categorie particolari (dati sanitari, giudiziari)
- **Data Act, Data Governance Act**: condivisione e accesso ai dati

### Normativa italiana
- **DDL AI italiano** (in approvazione 2025-2026): disciplina specifica per AI in ambito sanitario, giudiziario, pubblica amministrazione
- **D.Lgs. 196/2003 (Codice Privacy)**: integrazione GDPR per Italia
- **D.Lgs. 138/2024 (NIS2)**: cybersecurity per soggetti critici (alcuni studi rientrano)

### Codici deontologici professionali (variano per ordine)
- **CNF — Codice Deontologico Forense**: artt. su uso tecnologie, segreto professionale, dovere competenza
- **CNDCEC — Codice Deontologico Commercialisti**: artt. su tecnologie e responsabilità professionale
- **FNOMCeO — Codice Deontologia Medica**: artt. 14 (uso tecnologie), 78 (telemedicina)
- **CNI — Deontologia Ingegneri**: dovere aggiornamento, responsabilità progettuale
- **CNAPPC — Architetti**: deontologia professionale
- **CNN — Notai**: art. su tecnologia informatica
- **CNO — Consulenti Lavoro**: artt. su trattamento dati

### Aggiornamento continuo
La normativa evolve rapidamente. L'orchestratore segnala alla skill di fase di verificare via knowledge-source-italia + web search se la richiesta richiede informazioni puntuali aggiornate.

---

## 8. Esempio applicato — Routing in azione

### Input
"Sono avvocato, studio a Bologna, 4 colleghi, ci occupiamo principalmente di diritto civile e contenzioso. Ho letto dell'AI Act e mi chiedo se devo cambiare qualcosa nello studio. Usiamo già ChatGPT a volte per draft di lettere, ma senza regole. Da dove inizio?"

### Output orchestratore

```
═══════════════════════════════════════════════════════
ROUTING ANALYSIS
═══════════════════════════════════════════════════════

📊 Profilo cliente identificato:
   Settore: Studio legale (ai-studio-legale)
   Specializzazione: Diritto civile + contenzioso
   Dimensione: 5 professionisti (small studio)
   Sede: Bologna (Nord Italia)

📈 Maturità AI: Livello 1 (Exploration)
   - ChatGPT usato occasionalmente
   - Nessuna policy/procedura interna
   - Nessuna integrazione strutturata

🎯 Fase identificata: FASE 1 (Assessment)
   Trigger linguistici: "da dove inizio", "devo cambiare 
   qualcosa", "senza regole"

⚡ Trigger event: AI Act
   Urgenza media-alta. AI Act è in vigore con obblighi 
   applicabili a uso professionale.

═══════════════════════════════════════════════════════
PERCORSO RACCOMANDATO
═══════════════════════════════════════════════════════

📦 Pacchetto STARTER consigliato: "AI Assessment Studio Legale"
   Prezzo: 4.500€ + IVA (range 3.500-5.500€)
   Durata: 3-4 settimane
   
🛠 Skill che verranno attivate:
   1. ai-assessment-studio (metodologia)
   2. ai-studio-legale (knowledge settoriale)

📋 Output atteso:
   - Report assessment 30-50 pagine
   - Mappatura uso AI attuale + gap normativi (AI Act, 
     deontologia forense, GDPR)
   - 5-10 quick win identificati per studio 5-prof
   - Policy interna AI usage (template ready)
   - Roadmap preliminare 12 mesi
   - 1 workshop formativo (2h) con i 5 professionisti

⚖ Focus deontologico:
   - Art. 19 Codice Deontologico Forense (segreto 
     professionale e tecnologie)
   - Art. 14 (dovere competenza)
   - Recenti orientamenti CNF su AI

🚀 Next steps suggeriti:
   1. Discovery call 30 min per confermare fit (gratuita)
   2. Se OK, proposta formale in 48h
   3. Avvio assessment entro 1 settimana

═══════════════════════════════════════════════════════
HANDOFF A SKILL DI FASE
═══════════════════════════════════════════════════════

Brief per ai-assessment-studio:

Cliente: Studio Legale Bologna 5 prof
Settore: Legale - civile + contenzioso  
Maturità AI: Livello 1
Obiettivi dichiarati: 
  - Compliance AI Act
  - Strutturare uso AI esistente
  - Capire opportunità non ancora esplorate
Vincoli: 
  - Budget non dichiarato (probabile entry-level)
  - Sensibilità deontologica alta
Output atteso: Report STARTER, roadmap preliminare
Skill settoriale: ai-studio-legale (DA ATTIVARE)

[Procedi con ai-assessment-studio + ai-studio-legale]
═══════════════════════════════════════════════════════
```

---

## 9. Settori coperti e roadmap espansione

### Settori "core" prioritari (skill settoriali da costruire per primi)

1. **ai-studio-legale** — avvocati, praticanti, studi associati
2. **ai-studio-commercialista** — commercialisti, esperti contabili, revisori
3. **ai-studio-medico** — medici di base, specialisti, poliambulatori, RSA
4. **ai-studio-dentistico** — odontoiatri, ortodontisti, igienisti
5. **ai-studio-ingegneria** — ingegneri civili, industriali, gestionali, informatici
6. **ai-studio-architettura** — architetti, paesaggisti, interior designer
7. **ai-studio-notarile** — notai
8. **ai-studio-consulenza-lavoro** — consulenti del lavoro

### Settori "estesi" (espansione successiva)

9. **ai-studio-psicologi** — psicologi clinici, psicoterapeuti, neuropsichiatri
10. **ai-studio-veterinari** — veterinari, cliniche veterinarie
11. **ai-studio-agronomi** — agronomi, periti agrari
12. **ai-studio-geometri** — geometri, periti edili
13. **ai-studio-periti** — periti industriali, periti assicurativi
14. **ai-studio-farmacisti** — farmacisti titolari, farmacie
15. **ai-studio-revisori** — revisori contabili, sindaci
16. **ai-studio-consulenti-finanziari** — consulenti finanziari, promotori

### Settori "verticali specifici" (alta nicchia, alto valore)

17. **ai-studio-fiscalista-internazionale** — sub-specializzazione di commercialisti
18. **ai-studio-radiologi** — sub-specializzazione medica con AI altamente applicabile
19. **ai-studio-chirurghi** — sub-specializzazione medica
20. **ai-studio-tributaristi** — avvocati tributaristi (incrocio legale + fiscale)
21. **ai-studio-traduttori-interpreti** — traduttori giurati, interpreti tribunali
22. **ai-studio-mediatori** — mediatori civili, arbitri
23. **ai-studio-fotografi-creativi** — fotografi professionali (AI generativa altissima rilevanza)
24. **ai-studio-grafici-designer** — designer freelance/studi creativi

### Settori "para-professionali" (estensione del concetto)

25. **ai-amministratori-condominio** — amministratori condominio
26. **ai-agenti-immobiliari** — agenti, agenzie immobiliari
27. **ai-coach-consulenti-aziendali** — coach professionisti, consulenti freelance
28. **ai-formatori-trainer** — formatori professionisti, trainer aziendali

### Logica di prioritizzazione

I settori vanno costruiti in base a:
- **Volume mercato** (numero studi in Italia)
- **Ticket medio sostenibile** (PIL del settore)
- **Urgency normativa** (AI Act high-risk classification)
- **Domanda manifesta** (richieste già arrivate o segnalate)
- **Difendibilità competitiva** (settori dove K2-AI ha edge)

Suggerimento operativo: costruire settori 1-8 come "core" + scegliere 2-3 dei "verticali specifici" se Luca ha contatti diretti in quei nicchie.

---

## 10. Integrazione con altre skill K2-AI

### Skill K2-AI commerciali invocate dall'orchestratore

- **lead-qualifier**: per qualifica iniziale lead da check Express o LinkedIn
- **pricing-proposal-generator**: per proposta commerciale formale dei pacchetti
- **customer-success-manager**: per gestione lifecycle cliente in retainer
- **quarterly-business-review**: per QBR clienti AI in retainer
- **case-study-generator**: per documentare progetti AI completati

### Skill di dominio K2-AI rilevanti

- **it-law-privacy-ai**: per riferimenti normativi GDPR + AI Act + DDL AI
- **diritto-italiano**: per principi giuridici rilevanti
- **fiscale-tributario-italiano**: per aspetti fiscali (deducibilità, ammortamenti, super-deduzione AI in ddl)
- **consulente-sicurezza-lavoro**: per sicurezza dati / privacy in ambito sanitario o legale
- **diritto-societario-italiano**: per studi associati come società tra professionisti

### Skill K2-AI trasversali

- **knowledge-source-italia**: per fonti aggiornate normative + casi giurisprudenziali
- **psicologia-marketing**: per change management e adozione interna
- **management-bocconi**: per teoria organizzativa + change management

---

## 11. Errori comuni dell'orchestratore da evitare

- **Non saltare la disambiguazione settore**: un avvocato e un commercialista hanno bisogni completamente diversi anche se entrambi sono "studi professionali"
- **Non saltare l'identificazione fase**: vendere un pacchetto STANDARD a chi sta in Fase 4 è sbagliato e perde credibilità
- **Non sottovalutare la dimensione studio**: 1 prof solo vs 30 prof è cambio di paradigma
- **Non spingere il pacchetto PREMIUM su tutti**: la maggior parte degli studi parte naturalmente da STARTER
- **Non confondere maturità con dimensione**: studio con 30 prof può essere a Livello 0 di AI; freelance da solo può essere a Livello 2
- **Non promettere conformità AI Act garantita**: K2-AI supporta, l'avvocato/DPO certifica
- **Non sostituirsi a figure specializzate**: K2-AI non fa fine-tuning LLM, non scrive codice ML, non valuta GDPR DPIA in modo formale (salvo affiancamento DPO)
- **Non ignorare la dimensione deontologica**: ogni ordine professionale ha regole specifiche, vanno rispettate (skill settoriali approfondiscono)
- **Non passare a skill di fase senza brief**: evita "telefono senza fili" perdendo contesto
- **Non fissare prezzi senza considerare regione**: studi del Nord pagano più del Sud per stesso servizio
- **Non saltare la cura del passaggio normativo**: clienti professionisti danno enorme peso alla compliance, è il loro core business

---

## 12. KPI di salute della linea AI Studi Professionali

Da monitorare via k2ai-business-dashboard, area "Sales" e "Customer":

- **Lead AI Studi/mese**: target crescente, da 5 a 20+ in 12 mesi
- **Conversion lead → cliente**: target >25% (servizio premium)
- **Mix pacchetti**: target 50% STARTER, 35% STANDARD, 15% PREMIUM
- **Mix settori**: target diversificato, no settore >35%
- **NPS clienti AI**: target >50 (alto, perché è settore mission-critical per il cliente)
- **Retention retainer 12 mesi**: target >80%
- **LTV medio cliente AI Studio**: target >12.000€ (vs 4.000€ media K2-AI)
- **Referral rate**: target >30% (i professionisti si parlano molto)

---

## 13. Disclaimer professionale

Inserire in tutti i deliverable cliente:

> "K2-AI fornisce consulenza metodologica e operativa per l'introduzione di sistemi di intelligenza artificiale negli studi professionali. K2-AI non sostituisce le figure di Data Protection Officer (DPO), del consulente legale specializzato in diritto delle nuove tecnologie, del consulente cybersecurity certificato, dei revisori dei conti per gli aspetti contabili, né degli ordini professionali per le valutazioni deontologiche. Il professionista resta unico responsabile della conformità normativa e deontologica del proprio operato."

Questo disclaimer protegge K2-AI e chiarifica il perimetro al cliente.
