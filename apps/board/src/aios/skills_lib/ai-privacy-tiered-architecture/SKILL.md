---
name: ai-privacy-tiered-architecture
description: Skill trasversale strategica per progettazione di architetture AI con privacy stratificata su 5 livelli, dedicata a studi professionali italiani che trattano dati sensibili — legali, medici, commercialisti, notarili, psicologi. Usa SEMPRE quando l'orchestratore o le skill di fase rilevano forti requisiti privacy, oppure quando il professionista dice privacy AI studio, ChatGPT è sicuro per dati clienti, AI per documenti riservati, segreto professionale e AI, AI on-premise studio, private cloud AI, Llama studio professionale, sanitization documenti AI, DPIA per AI legale medico, anonimizzazione documenti AI. Esegue data classification 4 classi A/B/C/D, progetta architettura tiered su 5 livelli, valuta trade-off costo privacy performance, definisce policy AI Usage tier-aware, predispone DPIA per tier, identifica vendor compliance, costruisce decision tree operativo. Pricing 3.5-60K euro più retainer 600-3.500 euro/mese.
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
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --materia privacy_digitale --limit 5
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

Knowledge pack norme: `~/normattiva_ai/knowledge_packs/privacy_digitale/`

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# ai-privacy-tiered-architecture — Architetture AI con privacy stratificata per studi professionali

## 1. Cosa fa questa skill

Questa skill è il **vero differenziale competitivo di K2-AI nel mercato consulenza AI per studi professionali italiani**. Risolve il problema più sottovalutato e mal trattato dal mercato: la privacy dei documenti professionali quando si introducono sistemi AI.

**Il problema reale**: la maggior parte dei consulenti AI italiani al 2026 risponde alle preoccupazioni di privacy dei professionisti con frasi semplificate come "compra ChatGPT Enterprise, è sicuro", "usa la versione business, va bene così", "il GDPR è compliant". Sono risposte **giuridicamente fragili** e **operativamente sbagliate**, perché:

1. La "versione Enterprise" di un singolo vendor risolve **uno** dei cinque problemi privacy reali (il training sui dati). Lascia aperti gli altri quattro.
2. La privacy dei documenti professionali non è una questione binaria (sicuro/non sicuro), ma **stratificata**: documenti diversi richiedono protezioni diverse.
3. Il segreto professionale (art. 622 c.p., art. 19 Codice Deontologico Forense, equivalenti per altre professioni) ha implicazioni che vanno oltre il GDPR.
4. Il tool "più sicuro in assoluto" è spesso **inadatto** dal punto di vista operativo per costo o performance.

**La risposta K2-AI**: **architettura tiered**, dove ogni classe di documento dello studio viene mappata al livello di protezione adeguato. Né troppo (sovra-ingegnerizzato e costoso) né troppo poco (rischio reale di violazioni).

**Il valore strategico per K2-AI**:
- Differenziazione netta vs consulenti generalisti
- Difendibilità professionale (la consulenza è giuridicamente robusta)
- Pricing power (giustifica ticket premium 5-15K€ per la sola componente privacy)
- Apertura a clientela enterprise (studi grandi che hanno requisiti contrattuali stringenti)
- Riferibilità multi-settore (legale, medico, commercialista, notarile)

L'output principale è una **architettura privacy tiered personalizzata** sullo studio specifico, con:
- Mappatura documentale completa in 4 classi (A/B/C/D)
- Stack tecnologico differenziato per livello
- Policy AI Usage tier-aware
- DPIA template per ogni livello
- Decision tree operativo per il professionista in 30 secondi
- Costi e trade-off espliciti

---

## 2. Quando attivarsi

### Trigger primari
- "I miei documenti possono andare su ChatGPT?"
- "AI è sicura per dati clienti?"
- "Privacy dei documenti AI studio"
- "Segreto professionale e AI"
- "GDPR per AI in studio"
- "Posso usare AI per documenti riservati?"
- "AI on-premise studio"
- "Private cloud AI"
- "Llama / LLM locale studio"
- "Azure OpenAI privato"
- "Sanitization documenti AI"
- "Anonimizzazione AI"
- "DPIA per AI legale/medico"

### Trigger contestuali
- Cliente menziona M&A, due diligence, materie penali, materie sanitarie sensibili
- Cliente è studio enterprise (15+ avvocati, 5+ medici associati)
- Cliente ha clientela enterprise propria (corporate client, banche, multinazionali)
- Cliente solleva preoccupazioni esplicite di riservatezza
- Cliente menziona NDA stringenti dei propri clienti
- Cliente ha avuto sanzioni o ispezioni GDPR in passato
- Cliente è in settore specifico ad alta sensibilità (sanità, finanza, intelligence)

### Trigger da skill di fase
- **ai-assessment-studio** rileva alta sensibilità documentale → attivare per gap analysis privacy
- **ai-roadmap-progettazione** richiede architettura → attivare per design tiered
- **ai-implementazione-pilota** richiede setup multi-tier → attivare per configurazione
- **ai-manutenzione-evoluzione** richiede aggiornamento architettura → attivare per refresh

### Quando NON attivarsi
- Per privacy non AI-related (uso GDPR generale, vai a it-law-privacy-ai)
- Per cybersecurity generale di studio (vai a cybersecurity-pmi-base)
- Per studio piccolo (1-3 prof) con dati a bassa sensibilità (solo Livello 1+2 sufficiente, decisioni semplici)
- Per implementazione tecnica self-hosting LLM (richiede partner cybersecurity)
- Per consulenza GDPR formale che richiede DPO certificato

---

## 3. Il framework dei 5 livelli di privacy

Ogni livello rappresenta una combinazione di trade-off tra protezione, costo, performance, complessità.

### LIVELLO 1 — Public Cloud Standard
**Cosa è**: uso di Claude Team / ChatGPT Team / Gemini Workspace standard con server cloud del vendor (idealmente con regione UE selezionabile).

**Come funziona tecnicamente**:
- Documento trasmesso via TLS al cloud vendor
- Processamento su infrastruttura condivisa multi-tenant
- Output ritornato all'utente
- Logging temporaneo (30 gg tipico) presso vendor
- Eventuale review human-in-the-loop per moderation/abuse

**Per quali dati va bene**:
- Bozze generiche senza dati cliente identificabili
- Ricerca normativa su testi pubblici
- Brainstorming concettuale ("argomentazioni tipiche per...")
- Drafting con dati completamente fittizi
- Riassunti di documenti pubblici (sentenze, normative)
- Traduzioni di testi non riservati

**Per quali dati NON va bene**:
- Documenti con nomi cliente
- Atti con dati personali identificabili
- Email cliente
- Note di colloquio
- Materie sensibili (anche se anonimizzate, il contesto può identificare)

**Misure di sicurezza minime**:
- Account business/team (mai free per uso professionale)
- DPA standard del vendor sottoscritto
- Server EU se disponibile (Anthropic Frankfurt, OpenAI con piano specifico)
- MFA obbligatorio per tutti gli utenti
- Policy interna che identifica esplicitamente cosa NON inserire
- Audit log delle interazioni (anche solo manuale via spreadsheet)
- Formazione utenti su limiti del livello

**Vendor consigliati**:
- **Claude Team** (Anthropic): server Frankfurt EU, DPA standard, no training su dati Team/Enterprise
- **ChatGPT Team/Enterprise**: server US default ma EU disponibile su Enterprise, no training su dati
- **Microsoft Copilot 365**: leverage tenant Microsoft esistente, datacenter Italia disponibile
- **Mistral Le Chat Pro**: vendor europeo (Francia), naturalmente UE-based

**Costi**:
- Claude Team: €25-30/utente/mese
- ChatGPT Team: €25/utente/mese
- ChatGPT Enterprise: $60+/utente/mese (no public pricing)
- Copilot 365: €30/utente/mese in aggiunta a tenant

**Ranking privacy/performance**:
- Privacy: 6/10
- Performance: 9/10 (modelli flagship)
- Costo: 9/10 (basso)
- Complessità setup: 9/10 (semplice)

### LIVELLO 2 — Sanitization Layer
**Cosa è**: stesso stack di Livello 1, ma con un livello intermedio che **sanitizza i documenti** prima dell'invio al cloud, sostituendo dati personali con segnaposto. L'output viene poi "reidratato" con i dati reali.

**Esempio operativo**:

Documento originale:
> "Mario Rossi, nato a Bologna il 12/3/1978, residente in via Garibaldi 14, è stato licenziato il 5 gennaio 2026 dalla società Rossi Costruzioni SRL, P.IVA 01234567890, per giustificato motivo oggettivo..."

Documento sanitizzato (inviato all'AI):
> "[CLIENTE_PF_1], nato a [LUOGO_NASCITA_1] il [DATA_1], residente in [INDIRIZZO_1], è stato licenziato il [DATA_2] dalla società [DATORE_PG_1], [PIVA_1], per giustificato motivo oggettivo..."

L'AI processa il documento sanitizzato. L'output viene poi "reidratato" sostituendo i segnaposto con i valori reali, con verifica umana finale.

**Approcci di sanitization**:

**Sanitization manuale**:
- Find & replace operato dal professionista o assistente
- Costo: zero (solo tempo)
- Tasso di errore: 5-15% (dimentica un nome, errore tipografico)
- Adatto per documenti singoli o sporadici
- Efficiente per studi con bassa standardizzazione

**Sanitization semi-automatica**:
- Tool che riconoscono entità (PII recognition) e suggeriscono sostituzioni
- Professionista approva caso per caso
- Costo: €30-100/utente/mese
- Tasso di errore: 1-3%
- Adatto per uso quotidiano

**Sanitization automatica**:
- Tool che processano documenti automaticamente prima di invio AI
- Logging dettagliato delle sostituzioni per re-idratazione
- Costo: €100-300/utente/mese (tool dedicati)
- Tasso di errore: <1% se tool è buono
- Adatto per studi con volume alto

**Tool consigliati**:

**Open Source (gratuiti, richiedono setup tecnico)**:
- **Microsoft Presidio**: framework Microsoft per PII recognition italiano. Riconosce: nomi persone, luoghi, codici fiscali, IBAN, partite IVA, numeri telefono, email, indirizzi. Buono per studi tech-savvy con qualcuno che lo configura.
- **PrivateGPT**: orchestrator che sanitizza prima di invio LLM esterno. Self-hosted.
- **scrubadub**: libreria Python per PII detection.

**Commerciali (a pagamento, plug-and-play)**:
- **Cloaked.ai** (consigliato): tool dedicato per professionisti, integrazione browser, italiano. €50-100/utente/mese.
- **Skyflow**: data privacy vault enterprise. Più adatto a studi grandi.
- **Private AI**: API enterprise per sanitization. Tipicamente per integrazione custom.

**Per quali dati va bene**:
- Atti di causa con riferimenti cliente identificabili
- Lettere a clienti standard
- Memo interne basate su casi reali
- Analisi di sentenze su casi simili al proprio
- Drafting di parere legale standard
- 70-80% dei documenti tipici di uno studio civile/commerciale

**Limiti reali**:
- Non funziona se il contesto stesso identifica il cliente (cliente famoso, caso pubblicato sui media)
- Errori di sanitization possono lasciare dati nel testo (richiede sempre review umana)
- Non risolve il problema se l'AI viene istruita a "ricordare" il caso nel tempo (Claude Projects, Custom GPTs)
- Re-identificazione possibile se i dati sanitizzati restano correlabili (es. data di un caso pubblico + descrizione dei fatti = identificazione)

**Misure di sicurezza addizionali rispetto a Livello 1**:
- Verifica umana obbligatoria sull'output sanitizzato e re-idratato
- Audit log completo di sostituzioni (per dimostrare in caso di contestazione)
- Test periodici di efficacia della sanitization (campionamento mensile)
- Update tool sanitization per pattern italiani specifici (codici fiscali, formati IT)

**Ranking**:
- Privacy: 7.5/10 (significativo miglioramento vs L1)
- Performance: 8.5/10 (leggero overhead, output qualità invariata)
- Costo: 8/10 (€0-100/utente/mese aggiuntivo)
- Complessità setup: 7/10 (richiede process design)

### LIVELLO 3 — Private Cloud / Self-hosted

**Cosa è**: i dati non escono mai dalla giurisdizione/infrastruttura dello studio. Il modello AI gira su server controllati (cloud privato UE, on-premise, o cloud privato dello studio).

Tre sotto-opzioni con trade-off diversi.

#### 3A — Cloud privato EU con LLM commerciale via API

**Vendor che offrono modelli AI commerciali su infrastruttura privata UE**:

- **Microsoft Azure OpenAI Service**:
  - Datacenter Italia (Milano) e Frankfurt disponibili
  - Modelli OpenAI (GPT-4, GPT-4o) con SLA enterprise
  - DPA enterprise robusta (Microsoft signs as data processor)
  - Audit log completo, integrazione con Azure Sentinel
  - Possibilità di "private deployment" (modello dedicato)
  - Pricing: per token consumption + commit reservation
  - Costo tipico: €300-1.500/mese per studio 5-15 prof

- **AWS Bedrock**:
  - Regioni EU Frankfurt, Milan, Paris
  - Modelli Anthropic Claude, Meta Llama, Mistral, Cohere
  - DPA enterprise
  - Compliance certifications (ISO 27001, SOC2, FedRAMP)
  - Pricing: per token + reserved capacity option
  - Costo tipico: €400-2.000/mese

- **Google Vertex AI**:
  - Regioni EU
  - Gemini Pro/Ultra disponibili
  - Buona integrazione con Workspace se già usato
  - Costo tipico: €300-1.500/mese

**Vantaggi**:
- Server in giurisdizione UE certa
- Dati garantiti contrattualmente non usati per training
- DPA enterprise robusta (vs DPA standard di Livello 1)
- Audit log completo nativo
- Performance modelli flagship (Claude Opus, GPT-4)
- Setup tecnico moderato (cloud platform)

**Svantaggi**:
- Costo significativo vs Livello 1 (3-5x)
- Setup tecnico richiede competenze cloud specifiche
- Manutenzione (token monitoring, costi controllati)
- Ancora dipendenza da vendor americani (anche se via cloud)

**Per chi è adatto**:
- Studi 10-50 professionisti
- Clientela enterprise che richiede contrattualmente cloud privato
- Materie M&A, contenzioso commerciale rilevante, due diligence
- Budget congruo (>€500/mese privacy budget)

#### 3B — LLM open source in cloud privato italiano

**Stack tipico**:
- Cloud provider italiano (Aruba, Seeweb, OVH Italia, Register.it)
- 1 server GPU dedicato (NVIDIA A100 40GB/80GB, H100, o RTX 5090 in setup minimal)
- Sistema operativo: Ubuntu Server 24.04
- LLM open weights: Llama 3.3 70B, Qwen 2.5 72B, Mistral Large 2, DeepSeek V3
- Frontend web: OpenWebUI, LibreChat (open source, gratuito)
- VPN per accesso: Tailscale, OpenVPN, WireGuard
- Database vettoriale per RAG: Qdrant, Weaviate (open source)

**Provider italiani dettagliati**:

- **Aruba Cloud** (Arezzo): leader italiano, datacenter Tier IV. Server GPU disponibili a noleggio. Costo tipico: €600-1.200/mese per server con GPU adeguata.

- **Seeweb** (Milano, Frosinone): provider serio, buona qualità tecnica. Server GPU on-demand. Costo: €700-1.500/mese.

- **OVH Italia** (Milano): provider francese con presenza Italia. Server GPU competitivi.

- **Register.it Cloud** (Bergamo): meno noto ma serio.

**Vantaggi**:
- Dati al 100% in Italia (data residency assoluta)
- Nessuna chiamata API esterna durante uso
- Compliance massima (anche per requirement contrattuali stringenti)
- Costo predicibile (canone mensile fisso, no token consumption)
- Personalizzazione fine (eventuale fine-tuning sui dati dello studio)

**Svantaggi**:
- Performance inferiore a Claude Opus / GPT-4 (gap 15-30% su task legali italiani)
- Manutenzione tecnica complessa (aggiornamenti modelli, monitoring, troubleshooting)
- Necessità di partner tecnico esterno (K2-AI da solo non gestisce)
- Hardware obsolescenza 24-36 mesi (modelli evolvono, GPU diventa insufficiente)
- Setup iniziale 4-8 settimane

**Costi totali tipici (3 anni)**:
- Hardware/cloud: €600-1.500/mese × 36 = €21K-54K
- Setup K2-AI + partner tecnico: €15K-30K una tantum
- Manutenzione (10-20h/mese partner tecnico): €1K-3K/mese = €36K-108K su 3 anni
- **TCO totale 3 anni**: €70K-200K

**Per chi è adatto**:
- Studi 15-50+ professionisti con requisiti privacy stringenti
- Clientela che esige contrattualmente "dati in Italia"
- Materie ultra-sensibili (M&A strategici, contenzioso state-level, intelligence)
- Studi che possono permettersi competenze tecniche o partner dedicato

#### 3C — On-premise puro

**Hardware tipico per studio piccolo-medio**:
- Workstation con 2x NVIDIA RTX 5090 (32GB VRAM ciascuna): €5-7K
- Server con 64-128GB RAM, storage NVMe: €2-3K
- NAS con backup: €1.5K
- UPS APC professionale: €500-1K
- Networking, sicurezza fisica: €1K
- Setup K2-AI + partner tecnico: €5-15K

**Total hardware iniziale**: €15-30K una tantum.

**Manutenzione**: dipendente IT interno o partner tecnico. €1-2K/mese.

**Modelli supportati**:
- Llama 3.3 70B in 4-bit quantization (su 2x RTX 5090)
- Mistral Large 2 quantizzato
- Qwen 2.5 72B quantizzato

Performance tipica: 60-75% di Claude Opus 4.7 su task legali italiani.

**Vantaggi**:
- Massima privacy assoluta (mai dati fuori dallo studio)
- Costo predicibile (no token, no canone)
- Asset patrimoniale dello studio
- Indipendenza geopolitica completa

**Svantaggi**:
- Performance significativamente inferiore a tier 1
- Manutenzione tecnica continuativa
- Aggiornamenti modelli richiedono effort
- Fault tolerance (se hardware si rompe, downtime)
- Hardware obsoleto in 24-36 mesi

**Per chi è adatto**:
- Casi rarissimi: studi con materie classificate, requisiti contrattuali estremi, partner tecnico interno qualificato
- Studi con forte avversione a cloud per principio (raro ma presente)
- Casi politici di privacy data residency assoluta

### LIVELLO 4 — Air-gapped + Encryption Avanzata

**Cosa è**: protezione massima per documenti che non devono essere esposti nemmeno alla teoria di un breach o di un'intercettazione.

**Misure complete**:

- **LLM locale on-premise** (base Livello 3C)
- **Workstation dedicate** che fanno solo AI, senza connessione internet generica
- **Cifratura at-rest dei documenti**: BitLocker (Windows), FileVault (Mac), VeraCrypt (cross-platform)
- **Cifratura in-transit interna** (anche su rete LAN dello studio): TLS 1.3 minimo, idealmente VPN interna
- **Hardware Security Module (HSM)** per chiavi crittografiche: YubiHSM 2 (€700-1.000), Thales Luna (enterprise)
- **Workflow strutturato e documentato**: documento entra cifrato, esce cifrato, log immutabile
- **Eventuale cifratura omomorfica** per casi estremi (Microsoft SEAL, IBM HElib): permette calcoli su dati cifrati senza mai decifrarli. Performance fortemente impattata.
- **Audit log immutabile**: blockchain-based o WORM (Write Once Read Many) storage
- **Personnel security**: NDA stringenti per chi accede al sistema, background check
- **Physical security**: server in cassaforte ignifuga o rack chiuso, accesso biometrico

**Costi**:
- Setup completo: €50-150K
- Manutenzione: €3-8K/mese
- Competenze interne specializzate richieste

**Per chi è adatto**:
- Studi con casi di altissimo profilo (top-tier M&A, contenzioso strategico nazionale, materie classificate, intelligence)
- Estremamente raro per studio italiano standard
- Se ci si arriva, K2-AI non è il consulente giusto da solo — serve partner cybersecurity dedicato (es. partnership con società certificate ISO 27001/27018)

### LIVELLO 5 — No AI (la scelta consapevole)

**Cosa è**: per certi documenti, la scelta giusta è **non usare AI affatto**. È un livello che molti consulenti dimenticano di proporre, ma è essenziale.

**Casi tipici dove la policy dovrebbe escludere AI**:

**Per studio legale**:
- Testimonianze di parte offesa per reati gravi (violenza sessuale, terrorismo, abusi minori)
- Documenti coperti da segreto investigativo (artt. 329 c.p.p.)
- Dichiarazioni di collaboratori di giustizia
- Materie con NDA stringenti che vietano elaborazione esterna
- Casi dove il cliente ha esplicitamente vietato uso AI in mandato

**Per studio medico**:
- Documentazione di trattamenti pediatrici sensibili
- Documenti di pazienti con malattie altamente stigmatizzanti
- Materie psichiatriche con rischio di danno se diffuse
- Casi di interesse mediatico

**Per studio commercialista/notarile**:
- Documentazione fiscale di soggetti politicamente esposti (PEP)
- Atti riservati di entità governative
- Trust con beneficiari sensibili

**Per studio di consulenza del lavoro**:
- Documentazione di provvedimenti disciplinari delicati
- Casi di mobbing/discriminazione con dati identificativi

**Implementazione operativa**:
- Lista esplicita nelle policy dello studio
- Marcatura speciale di documenti "AI-free zone"
- Procedura interna per riconoscere e segregare questi casi
- Formazione dedicata su queste eccezioni
- Eventuale workflow cartaceo dedicato

**Costo**: €0 (è scelta procedurale, non tecnologica).

---

## 4. Framework di data classification (4 classi)

Il cuore operativo della skill è la classificazione di ogni tipo di documento dello studio in 4 classi.

### Classe A — Pubblico/Anonimo
**Definizione**: documenti senza dati personali identificabili o derivati da fonti pubbliche.

**Esempi tipici per studio legale**:
- Bozze generiche senza riferimento cliente
- Ricerca normativa su fonti pubbliche
- Riassunti di sentenze pubblicate
- Documenti di formazione interna
- Brainstorming concettuale

**Esempi per studio medico**:
- Articoli scientifici per ricerca
- Documenti di formazione
- Procedure operative anonimizzate

**Volume tipico**: 10-20% dei documenti di studio.

**Tier consigliato**: Livello 1.

### Classe B — Sensibilità standard
**Definizione**: documenti con dati personali identificabili ma non particolari ai sensi GDPR (no dati sanitari, giudiziari, biometrici, etc.). Tutela del segreto professionale base.

**Esempi per studio legale**:
- Atti di causa civile/commerciale standard
- Lettere a clienti
- Memo interne con riferimenti a casi reali
- Pareri legali standard
- Contratti standard

**Esempi per studio commercialista**:
- Bilanci di clienti
- Dichiarazioni dei redditi
- Documentazione fiscale standard

**Esempi per studio medico**:
- Cartelle cliniche di routine
- Comunicazioni con altri medici curanti

**Volume tipico**: 60-75% dei documenti di studio.

**Tier consigliato**: Livello 2 (sanitization) o Livello 3A (cloud privato EU) in base a contratto cliente.

### Classe C — Alta sensibilità
**Definizione**: documenti con dati particolari GDPR (sanitari, giudiziari, biometrici), informazioni commerciali strategiche, materie con elevato impatto reputazionale o economico.

**Esempi per studio legale**:
- Documenti M&A e due diligence
- Casi penali con persone identificabili
- Materie societarie con dati finanziari riservati
- Contratti enterprise con NDA stringenti
- Cause sensibili (mobbing, molestie, discriminazione)

**Esempi per studio medico**:
- Diagnosi di malattie gravi/croniche
- Documentazione psichiatrica
- Documentazione di pazienti VIP
- Refertazione genetica

**Esempi per studio notarile**:
- Atti di trasferimento di valore ingente
- Successioni complesse
- Trust e fiduciarie

**Volume tipico**: 10-20% dei documenti di studio.

**Tier consigliato**: Livello 3 (privato cloud EU minimo, eventualmente cloud privato italiano per requisiti più stringenti).

### Classe D — Ultra-sensibile / Classified
**Definizione**: documenti con sensibilità estrema, classificazione legale, materia investigativa, NDA con sanzioni elevate, casi di alto profilo.

**Esempi**:
- Materie classificate (intelligence, sicurezza nazionale)
- Documenti ex art. 329 c.p.p. (segreto investigativo)
- Casi di alto profilo mediatico in corso
- Materie con NDA da multinazionali con sanzioni nei milioni
- Documenti di soggetti politicamente esposti (PEP)
- Materie di alto profilo internazionale (sanzioni, embargo)

**Volume tipico**: 1-5% dei documenti di studio (solo studi specifici).

**Tier consigliato**: Livello 4 (air-gapped) o Livello 5 (no AI).

---

## 5. Workflow operativo della skill

### Step 1 — Discovery iniziale (settimana 1)

Domande prioritarie al cliente professionale:

**Sul profilo studio**:
- Settore professionale e specializzazione
- Dimensione (professionisti + collaboratori)
- Volume documenti tipici/mese
- Sede/i
- Eventuali certificazioni esistenti (ISO 27001, etc.)

**Sulla clientela**:
- Tipologia clienti (PMI, enterprise, pubblico, persone fisiche)
- Eventuali clienti con requisiti contrattuali specifici (banche, multinazionali, PA)
- Eventuali NDA stringenti già firmati
- Settori sensibili nella clientela (sanità, difesa, finanza)

**Sull'attuale gestione privacy**:
- DPO designato (sì/no)
- Registro trattamenti GDPR esistente
- DPIA fatte in passato
- Eventuali sanzioni o ispezioni precedenti
- Policy esistenti

**Sull'uso attuale AI**:
- Tool AI già usati (anche occasionalmente)
- Procedure esistenti
- Eventuali incidenti o near-miss

**Sulla sensibilità documentale**:
- Tipologie di documenti più sensibili gestiti
- Eventuali casi di alto profilo
- Materie particolarmente delicate

### Step 2 — Mappatura documentale (settimana 1-2)

Workshop con team studio per identificare **tutti i tipi di documento** trattati e classificarli A/B/C/D.

Output: matrice documentale completa.

Esempio output per studio legale civile:

| Tipo documento | Volume mese | Classe | Note |
|----------------|-------------|--------|------|
| Lettere generiche stato pratica | 80 | B | Sanitization |
| Bozze atti di citazione | 25 | B | Sanitization |
| Memo interni casi | 15 | B | Sanitization |
| Lettere senza riferimento cliente | 30 | A | Livello 1 ok |
| Documenti M&A | 5 | C | Livello 3 |
| Casi penali sensibili | 3 | C/D | Caso per caso |
| Bozze pareri standard | 20 | B | Sanitization |
| Ricerca normativa | 50 | A | Livello 1 ok |
| Atti causa con dati clienti | 40 | B | Sanitization |
| Procedimenti riservati art. 329 | 2 | D | No AI |

### Step 3 — Risk assessment per classe (settimana 2)

Per ogni classe, valutazione del rischio:

**Probabilità di breach** (scale 1-5):
- Probabilità tecnica
- Probabilità contrattuale
- Probabilità deontologica

**Impatto di breach** (scale 1-5):
- Sanzione economica potenziale (GDPR, deontologica)
- Danno reputazionale
- Danno cliente (responsabilità civile)
- Conseguenze penali (segreto)

**Risk score** = Probabilità × Impatto.

Per ogni classe, range di risk score atteso:
- Classe A: 1-4 (basso)
- Classe B: 4-12 (medio)
- Classe C: 12-20 (alto)
- Classe D: 20-25 (critico)

### Step 4 — Architettura tiered design (settimana 2-3)

Sulla base di mappatura + risk assessment, design dell'architettura specifica per lo studio.

**Componenti dell'output**:

**Stack tecnologico per livello**:
- Per classe A: vendor specifico (es. Claude Team server EU)
- Per classe B: stack Livello 1 + sanitization tool (es. Cloaked.ai)
- Per classe C: stack Livello 3 (es. Azure OpenAI Italia)
- Per classe D: procedura "AI-free" o Livello 4 se rilevante

**Diagramma architetturale**:
- Visualizzazione dei flussi di dati per classe
- Punti di sanitization
- Boundary di sicurezza
- Audit checkpoint

**Workflow operativi**:
- Chi può usare cosa, quando, come
- Procedure di classificazione documenti
- Procedure di escalation in caso di dubbio
- Procedure di review periodico

### Step 5 — Policy AI Usage tier-aware (settimana 3)

Personalizzazione della policy con framework tier-aware. Sezioni chiave:

**Sezione 1 — Principi generali**
- Tutela del segreto professionale
- Conformità GDPR e AI Act
- Trasparenza con il cliente
- Responsabilità professionale

**Sezione 2 — Classificazione documenti**
- Le 4 classi A/B/C/D
- Esempi concreti per settore
- Procedura di classificazione

**Sezione 3 — Tool consentiti per classe**
- Tabella esplicita per classe
- Procedura di selezione tool
- Eventuali tool vietati (lista esplicita)

**Sezione 4 — Procedura per classe**

Per Classe A:
- Tool diretti consentiti
- No restrictions su prompt (purché senza dati cliente)
- Disclaimer minimo

Per Classe B:
- Sanitization obbligatoria preventiva
- Verifica re-idratazione
- Logging interazione
- Disclaimer cliente

Per Classe C:
- Solo tool tier 3 dedicati
- Approval del responsabile compliance
- Log dettagliato
- Eventuale informativa specifica al cliente

Per Classe D:
- Procedura "AI-free"
- Marcatura speciale documento
- Workflow alternativo

**Sezione 5 — Disclaimer obbligatori**
- Template per output al cliente che hanno usato AI
- Variabili per livello di trasparenza

**Sezione 6 — Audit e governance**
- Frequenza review
- Responsabile compliance
- Procedure escalation
- Reporting

**Sezione 7 — Formazione**
- Frequenza training
- Argomenti obbligatori
- Test di verifica

### Step 6 — DPIA template per tier (settimana 3-4)

Per ogni livello attivato, predisporre template DPIA (Data Protection Impact Assessment) che il DPO o equivalente può finalizzare.

DPIA template include:
- Descrizione del trattamento AI
- Base giuridica
- Categorie di dati trattati
- Trasferimenti
- Misure di sicurezza
- Valutazione del rischio
- Misure di mitigazione
- Conclusioni

### Step 7 — Decision tree operativo (settimana 4)

Flowchart **stampabile** che il professionista può tenere accanto alla scrivania per decidere in 30 secondi:

```
Devo usare AI su questo documento?
│
├─ Il documento contiene dati personali identificabili?
│   │
│   NO → CLASSE A → Livello 1 (Claude Team) ✓
│   │
│   SÌ ↓
│
├─ Sono dati particolari (sanitari/giudiziari/biometrici) o materia altamente strategica?
│   │
│   NO → CLASSE B
│   │   │
│   │   ├─ Posso sanitizzare il documento? → Sì → Sanitize + Livello 1 ✓
│   │   ├─ Sanitization è efficace nel contesto? → No → Livello 3A
│   │
│   SÌ ↓
│
├─ La materia è classificata, soggetta a NDA stringente, o di alto profilo?
│   │
│   NO → CLASSE C → Livello 3 ✓
│   │
│   SÌ ↓
│
└─ CLASSE D → Livello 4 o Livello 5 (NO AI)
    │
    └─ Consulta il responsabile compliance prima di procedere
```

### Step 8 — Generazione deliverable

Output completi:

**1. AI Privacy Tiered Architecture Report** (DOCX 25-40 pp)
- Executive summary
- Profilo studio e clientela
- Quadro normativo applicabile
- Mappatura documentale
- Risk assessment
- Architettura tiered proposta
- Stack tecnologico per livello
- Costi e business case
- Roadmap implementazione
- Allegati (matrici, DPIA template)

**2. Document Classification Matrix** (XLSX)
- Foglio "Master": tutti i tipi di documento con classe
- Foglio "Risk Assessment": calcolo risk score
- Foglio "Tool Mapping": tool consentiti per classe
- Foglio "Compliance Tracking": stato conformità

**3. Policy AI Usage Tier-Aware** (DOCX 12-20 pp)
- Policy completa pronta per firma

**4. DPIA Templates** (DOCX, multipli)
- 1 template per ogni livello attivato

**5. Decision Tree visuale** (PDF)
- Stampabile A4
- Versione semplificata per ambient distribution
- Versione dettagliata per deep dive

**6. Implementation Roadmap** (XLSX)
- Timeline 3-6 mesi
- Milestone, owner, KPI

---

## 6. Esempio applicato — Studio Legale Verdi (Roma, 12 prof, M&A + commerciale)

### Input dall'orchestratore
"Studio legale Roma, 12 prof, specializzazione M&A + commerciale, clientela enterprise (banche, multinazionali italiane). Cliente importante della rete K2-AI, gravi requisiti privacy. Vuole architettura AI compliant per cliente top secret."

### Output sintetico

```
═══════════════════════════════════════════════════════
AI PRIVACY TIERED ARCHITECTURE — Studio Legale Verdi
═══════════════════════════════════════════════════════

🏢 PROFILO STUDIO
   12 professionisti (3 partner + 4 senior + 5 associate)
   Specializzazione: M&A, commerciale, banking
   Clientela: 70% enterprise (banche, multinazionali)
   30% mid-corporate
   Sede: Roma + ufficio Milano
   ISO 27001 in corso (target Q3 2026)
   DPO designato (interno)

📊 MAPPATURA DOCUMENTALE (5 settimane analisi)

| Classe | Volume mese | % | Tipologia tipica |
|--------|-------------|---|-------------------|
| A      | 45          | 8% | Ricerca normativa, draft generici |
| B      | 280         | 52% | Atti commerciali, memo, lettere |
| C      | 195         | 36% | M&A, due diligence, contratti enterprise |
| D      | 22          | 4%  | Materie altissimo profilo, NDA top |

💡 OSSERVAZIONE STRATEGICA
   36% dei documenti è Classe C — significativo.
   Architettura tiered è non solo opportuna, è 
   imprescindibile.

═══════════════════════════════════════════════════════
🏗 ARCHITETTURA TIERED PROPOSTA

LIVELLO 1 — Public Cloud (per Classe A)
└─ Claude Team EU Frankfurt — 12 utenti
   €348/mese (€29/utente)
   
LIVELLO 2 — Sanitization (per Classe B)
└─ Stesso Claude Team + Cloaked.ai Pro
   12 licenze Cloaked: €840/mese (€70/utente)
   Workflow integrato in Claude Projects

LIVELLO 3A — Azure OpenAI Italia (per Classe C)
└─ Azure OpenAI Service, regione Italy North (Milano)
   Sottoscrizione enterprise con DPA upgraded
   GPT-4o + DALL-E + Whisper (per trascrizione audio)
   Token reservation: €1.500/mese (commit annuale)
   Sviluppo custom Web UI interno: €15K una tantum

LIVELLO 4/5 — Air-gapped (per Classe D)
└─ Workstation dedicata in cassaforte sala blindata
   Hardware: €18K (RTX 5090 dual + secure storage)
   Llama 3.3 70B locale
   Nessun networking esterno
   Solo 3 partner abilitati ad accedere

═══════════════════════════════════════════════════════
💰 BUSINESS CASE

Setup K2-AI complete: €38.500
   - Architettura design: €8K
   - Cloaked.ai integration: €5K
   - Azure OpenAI setup: €15K
   - Workstation air-gapped setup: €8K (incl. hardware)
   - Policy + DPIA + training: €2.5K

OPEX mensile:
   - Claude Team: €348
   - Cloaked.ai: €840
   - Azure OpenAI (commit): €1.500
   - Workstation manutenzione: €300 (inclusa in retainer)
   - Retainer K2-AI manutenzione: €1.800
   TOTALE: €4.788/mese (€57.456/anno)

ROI annuo stimato:
   Time saved: 800h × €120/h media = €96K
   Errori evitati / casi salvati: €30K stimato
   Compliance risk avoided: priceless (ma €50-200K 
   sanzioni evitate)
   
   Net benefit anno 1: ~€80K
   Payback: 14 mesi

═══════════════════════════════════════════════════════
📜 POLICY AI USAGE TIER-AWARE — sintesi

Articolo chiave (estratto):

"Sezione 4 — Procedura per classificazione documenti

Prima di qualsiasi utilizzo di sistemi AI, l'avvocato 
classifica il documento secondo lo schema:

CLASSE A: documenti pubblici o anonimi.
  Tool: Claude Team standard.
  Verifica: nessuna preventiva.

CLASSE B: documenti con dati personali identificabili 
ma non particolari.
  Tool: Claude Team con Cloaked.ai sanitization 
  obbligatoria.
  Verifica: re-idratazione output con review umana.

CLASSE C: documenti con dati particolari, materie 
M&A, contratti enterprise sopra €1M.
  Tool: Azure OpenAI Italia tier dedicato.
  Verifica: approval scritta partner referente caso.
  Logging: dettagliato e immutabile.

CLASSE D: materie classificate, NDA con sanzioni 
oltre €5M, casi alto profilo mediatico.
  Tool: SOLO workstation air-gapped, con presenza 
  fisica del partner durante uso.
  Verifica: doppia review (partner + DPO).
  Audit: trimestrale obbligatorio.

In caso di dubbio sulla classe, l'avvocato consulta 
il DPO o il responsabile compliance prima di procedere."

═══════════════════════════════════════════════════════
🌳 DECISION TREE (estratto)

Quando ricevi documento per drafting/analisi:

1. Contiene nomi/dati personali? 
   NO → Classe A → Claude Team OK
   SÌ → continua

2. Sono dati sanitari/giudiziari/biometrici?
   NO → Classe B → Cloaked.ai + Claude Team
   SÌ → continua

3. È M&A/contratto enterprise/materia ad alto valore?
   NO → Classe C → Azure OpenAI Italia
   SÌ → continua

4. È materia classificata o NDA top?
   NO → Classe C → Azure OpenAI Italia (con review)
   SÌ → Classe D → Workstation air-gapped o NO AI

═══════════════════════════════════════════════════════
📅 ROADMAP IMPLEMENTAZIONE 6 MESI

Mese 1: Setup Claude Team + workshop classificazione
Mese 2: Setup Cloaked.ai + sanitization tier 2 attivo
Mese 3: Setup Azure OpenAI Italia + custom UI sviluppo
Mese 4: Test tier 3 + audit DPO + policy v1.0
Mese 5: Setup workstation air-gapped + tier 4 attivo
Mese 6: Audit completo + ISO 27001 readiness check + 
        retainer ongoing avvio

═══════════════════════════════════════════════════════
📂 OUTPUT GENERATI

1. AIPrivacyArchitecture-StudioVerdi-202607.docx (38 pp)
2. DocumentClassification-StudioVerdi.xlsx (4 fogli)
3. AIPolicy-StudioVerdi-v1.0.docx (18 pp)
4. DPIA-Templates-StudioVerdi (4 docs, uno per tier)
5. DecisionTree-StudioVerdi.pdf (formato A4 e A3)
6. Roadmap-StudioVerdi.xlsx
7. ComplianceTracker-StudioVerdi.xlsx
8. Workshop-Slides-Classification.pptx (28 slide)

═══════════════════════════════════════════════════════
🎯 PROPOSTA COMMERCIALE K2-AI

"AI Privacy Architecture Premium" — €38.500 + IVA
   Setup completo + 4 livelli + policy + DPIA
   Tempo: 6 mesi

+ Retainer "Privacy Operations" — €1.800/mese
   Manutenzione + audit trimestrali + 
   aggiornamenti normativi + supporto utenti
   Durata: 24 mesi minimo

TCO 36 mesi: €38.500 + (€1.800 × 36) = €103.300

VS rischio sanzione single GDPR breach: €50K-€2M+
VS rischio reputazionale studio: incalcolabile
VS rischio responsabilità civile cliente: significativo

═══════════════════════════════════════════════════════
```

---

## 7. Output deliverable

| Documento | Estensione | Pagine/fogli |
|-----------|-----------|---------------|
| AI Privacy Tiered Architecture Report | DOCX | 25-40 |
| Document Classification Matrix | XLSX | 4-6 fogli |
| Policy AI Usage Tier-Aware | DOCX | 12-20 |
| DPIA Templates (1 per tier attivo) | DOCX | 5-10 ciascuno |
| Decision Tree visuale | PDF | 1-3 pagine A4/A3 |
| Implementation Roadmap | XLSX | 3-5 fogli |
| Compliance Tracker | XLSX | 1 master |
| Workshop Slides Classification | PPTX | 25-35 slide |

---

## 8. Pricing della skill

Questa skill è **add-on premium** che si vende come componente o come servizio standalone.

### Come componente di pacchetto STANDARD/PREMIUM
- Inclusa in pacchetto STANDARD: incremento prezzo +€2.500-€4.000 sul base
- Inclusa in pacchetto PREMIUM: standard, no incremento

### Come servizio standalone
- **Architettura Privacy Light** (1-2 livelli): €3.500-€6.000
- **Architettura Privacy Standard** (3 livelli): €6.000-€12.000
- **Architettura Privacy Premium** (4 livelli): €12.000-€25.000
- **Architettura Privacy Enterprise** (5 livelli + ISO 27001 prep): €25.000-€60.000

### Retainer privacy ongoing
- **Privacy Operations Light**: €600-€800/mese (audit semestrale, aggiornamenti normativi)
- **Privacy Operations Standard**: €1.200-€1.800/mese (audit trimestrali, supporto continuativo)
- **Privacy Operations Premium**: €2.000-€3.500/mese (audit mensili, DPO-as-a-service shadowing)

### Logica di prezzo

Il pricing è giustificato da:
- Riduzione rischio sanzione GDPR (€50K-€2M evitati)
- Riduzione rischio responsabilità civile cliente (€100K+ potenziali)
- Riduzione rischio deontologico (sospensione, radiazione possibili)
- Apertura a clientela enterprise (commesse extra €100K-€1M+/anno)

Prezzo apparentemente alto = ROI evidente per studio target.

---

## 9. Integrazione con altre skill

### Skill di sistema
- **flusso-ai-studi-professionali**: orchestratore (può attivare questa skill come componente)
- **ai-assessment-studio**: assessment privacy come parte di assessment generale
- **ai-roadmap-progettazione**: architettura tiered come parte di roadmap
- **ai-implementazione-pilota**: implementazione tiered durante pilota
- **ai-manutenzione-evoluzione**: aggiornamenti privacy ongoing

### Skill di dominio K2-AI
- **it-law-privacy-ai**: per dettagli normativi GDPR + AI Act + DDL AI
- **knowledge-source-italia**: per fonti aggiornate Garante, ACN, ENISA
- **diritto-italiano**: per principi giuridici di responsabilità professionale
- **diritto-societario-italiano**: per studi associati e responsabilità d'impresa
- **cybersecurity-pmi-base**: per integrazione con framework cyber generale
- **fiscale-tributario-italiano**: per aspetti fiscali (super-deduzione AI ddl)

### Skill commerciali
- **lead-qualifier**: per qualificare lead con interesse privacy
- **pricing-proposal-generator**: per proposta commerciale architettura
- **customer-success-manager**: per gestione retainer privacy
- **case-study-generator**: per documentare implementazioni privacy di successo

### Skill produttive
- **docx, xlsx, pptx**: per deliverable
- **frontend-design**: per dashboard custom UI per tier 3

---

## 10. Settori di applicazione differenziale

La skill è trasversale ai settori professionali. Differenze settoriali:

### Studi legali
- Focus: segreto professionale, art. 622 c.p., art. 19 CDF, materie penali sensibili, M&A
- Tier 4 più frequente
- Vendor specializzati: Lexis+ AI, Harvey AI per Tier 3+

### Studi medici / cliniche
- Focus: dati sanitari (sempre Classe C), GDPR rinforzato, requisiti di settore
- Tier 3 default per la maggior parte dei documenti
- Vendor specializzati: Tempus AI, Doximity GPT per Tier 3+

### Studi commercialisti
- Focus: dati fiscali, segreto, materie societarie
- Mix bilanciato A/B/C
- Vendor: TeamSystem AI, Wolters Kluwer Profis AI

### Studi notarili
- Focus: atti di trasferimento, successioni, segreto del notaio
- Volume Classe C significativo
- Vendor: integrazione con software di settore (Visualstudio, etc)

### Studi psicologi
- Focus: dati psichiatrici (sempre Classe C/D), riservatezza assoluta
- Tier 3+ per la maggioranza
- Vendor in evoluzione, spesso Tier 4 unico approccio

---

## 11. Disclaimer professionale

Inserire in tutti i deliverable:

> "K2-AI fornisce consulenza metodologica e operativa per la progettazione di architetture AI con privacy stratificata negli studi professionali. Il documento prodotto rappresenta una proposta di architettura basata sulle informazioni fornite dallo studio cliente e sulla normativa vigente al momento della stesura.
>
> K2-AI non sostituisce le figure di:
> - Data Protection Officer (DPO) per la valutazione formale di conformità GDPR
> - Avvocato specializzato in diritto delle nuove tecnologie per pareri legali su trattamenti specifici
> - Auditor cybersecurity certificato per assessment formali (ISO 27001, etc.)
> - Ente certificatore per certificazioni di conformità
>
> L'implementazione tecnica di livelli 3B, 3C, 4 richiede coinvolgimento di partner tecnici cybersecurity specializzati. K2-AI coordina e supervisiona, ma l'implementazione tecnica resta in capo al partner.
>
> Il professionista resta unico responsabile della conformità normativa e deontologica del proprio operato."

---

## 12. Errori comuni da evitare

- **Non promettere "100% sicurezza"**: nessuna architettura è impenetrabile. Si parla di riduzione rischio.
- **Non sopravvalutare la sanitization**: ha limiti reali, soprattutto su contesti che identificano da soli
- **Non sottostimare il costo del Tier 3-4**: setup tecnico complesso, manutenzione continuativa
- **Non confondere data residency con privacy**: un documento in Italia può essere ancora vulnerabile internamente
- **Non saltare la classificazione documentale**: senza, l'architettura non ha senso
- **Non usare un singolo livello per tutti i documenti**: sovra-protezione costa, sotto-protezione è rischiosa
- **Non saltare la formazione utenti**: la migliore policy fallisce se non capita
- **Non promettere "elimini il rischio sanzione"**: si riduce significativamente, non si elimina
- **Non sottovalutare la dimensione contrattuale**: alcuni clienti enterprise hanno requisiti che vincolano il tier minimo
- **Non ignorare l'evoluzione normativa**: AI Act enforcement si intensifica, DDL AI italiano in approvazione, retainer ongoing fondamentale
- **Non sostituirsi al DPO**: K2-AI supporta, DPO certifica
- **Non confondere on-premise con sicuro**: server in casa con configurazione errata può essere meno sicuro di Azure cloud privato
- **Non dimenticare l'incident response plan**: ogni tier deve avere procedura in caso di breach
- **Non saltare il testing periodico**: penetration test annuale per tier 3+ è raccomandato
- **Non considerare la skill come "fatta una volta"**: richiede aggiornamento continuativo (vendor cambiano, normativa evolve, modelli si aggiornano)
