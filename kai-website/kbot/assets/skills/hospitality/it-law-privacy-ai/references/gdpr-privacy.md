# REF: GDPR, Privacy, Trasferimenti Extra-UE, DPO, DPIA

## GDPR – Reg. UE 2016/679

### Applicabilità e Scope (Art. 2-3)

- **Art. 2**: Applicazione a trattamento dati personali (automatico e non) di responsabili/incaricati stabiliti UE, o extra-UE se offerta di beni/servizi a residenti UE o monitoraggio comportamento in UE.
- **Art. 3 (Applicazione territoriale)**:  
  - Controller/processor con stabilimento UE → GDPR sempre  
  - Extra-UE ma offerta servizi/beni a residenti UE → GDPR si applica  
  - Monitoraggio comportamento EU residents → GDPR si applica anche da extra-UE  
  - **Esenzioni**: Attività fuori scope unione, sicurezza/politica estera, autorità penali

---

### Attori Principali

| Ruolo | Definizione (Art. 4) | Responsabilità |
|-------|---------------------|-----------------|
| **Data Controller** (Art. 4(7)) | Determina finalità e mezzi del trattamento | Compliance GDPR, sicurezza, DPA, DPIA |
| **Data Processor** (Art. 4(8)) | Tratta dati per conto controller (su istruzioni) | Segue istruzioni, sicurezza tecnica, data breach |
| **Data Subject** (Art. 4(1)) | Persona fisica identificabile | Titolare dei diritti (accesso, erasure, etc.) |
| **DPO** (Art. 4(18)) | Data Protection Officer (consulente indipendente) | Art. 39: monitoraggio compliance, contatto per diritti |

**Data Subject identificabile** (Rec. 26): Account, ID online, identificatori fisici+digitali, o dati che permettono identificazione ragionevole.

---

### Guiding Principles (Art. 5)

| Principio | Significato |
|-----------|------------|
| **Lawfulness** | Trattamento legittimo (Art. 6), trasparente (Rec. 39) |
| **Fairness** | Non utilizzo ingannevole, buona fede (Rec. 39) |
| **Transparency** | Data subject informato (Art. 13-14) |
| **Purpose Limitation** | Dati raccolti per finalità esplicita, specifica, legittima; no ridestinazione senza consenso/base giuridica |
| **Data Minimization** | Raccogliere solo dati necessari, rilevanti, limitati (proporzionalità) |
| **Accuracy** | Dati corretti, aggiornati; rettifica/cancellazione se inesatti |
| **Storage Limitation** | Conservare max per durata necessaria (dipende da contesto; no indefinito) |
| **Integrity & Confidentiality** | Art. 32: security misure (tecnico-organizzative) adeguate al rischio |
| **Accountability** | Art. 5(2), 24, 32: Responsabilità dimostrabile (documentazione, DPIA, etc.) |

**Burden of Proof**: Controller deve dimostrare compliance (Rec. 39, Art. 5(2)).

---

## Basi Giuridiche del Trattamento (Art. 6)

Uno almeno tra:

| Base | Requisiti |
|------|-----------|
| **Consenso** (6(1)(a)) | Libero, specifico, informato, non ambiguo, revocabile, prova forma. Es. personalized advertising (TikTok case). **No pre-checked boxes.** |
| **Contratto** (6(1)(b)) | Trattamento necessario per esecuzione contratto con data subject o adempimento richiesta pre-contrattuale |
| **Obbligo Legale** (6(1)(c)) | Legge, decreto, regolamento nazionale/UE obbliga trattamento (es. antiriciclaggio, tasse) |
| **Interesse Vitale** (6(1)(d)) | Protezione vita data subject (es. emergenza medica, sicurezza pubblica in pericolo) |
| **Compito Pubblico** (6(1)(e)) | Autorità pubblica: trattamento necessario per compito pubblico o pubblica autorità (es. PA) |
| **Interesse Legittimo** (6(1)(f)) | Controller/terzo ha interesse reale (non generico). **Balancing test**: interesse vs. diritti data subject. Es. fraud prevention, direct marketing (con limiti), R&D. **Vietato per minori, privati per finalità servizi pubblici** |

**Condizioni aggiuntive**: Art. 6(1)(f) richiede **balancing** tra interesse legittimo controller e diritti fondamentali data subject (privacy, protezione dati, fede in dati, non essere semplificato/oggettificato fuori contesto). Es. **Google LLC c. Dirección General**: interesse pubblico a libertà informazione può bilanciare diritto all'oblio, ma solo se rilevante socialmente.

---

## Dati Particolari (Art. 9 – Categorie Speciali)

**Divieto generale**: Trattamento vietato per dati che rivelano razza/etnia, opinioni politiche, convinzioni religiose/filosofiche, appartenenza sindacale, dati genetici, biometrici (per identificazione), dati sanità, vita sessuale.

**Eccezioni** (Art. 9(2)):
- Consenso esplicito data subject
- Obbligo legale occupazionale
- Protezione interessi vitali (es. emergenza medica)
- Attività legittima org. non-profit con garanzie
- Dati pubblicamente dichiarati da data subject
- Ragioni interesse pubblico sostanziale (legge)
- Finalità sanitaria/assistenza (professionisti, ricerca medica)
- Interesse pubblico archivi/ricerca storica/statistica
- **NG v. Direktor caso**: Dati biometrici (DNA, impronte) in db polizia post-riabilitazione = sproporzionato, viola Art. 7-8 CFREU (privacy/protezione dati). Retention indefinita = incostituzionale.

---

## Diritti dell'Interessato

### 1. Right to be Informed (Art. 13-14)
- **Art. 13** (raccolta diretta): Identity controller, DPO, finalità, base giuridica, destinatari, retention period, diritti (accesso, rettifica, erasure, obiezione, decision-making), ricorso supervisory authority, fonte dati
- **Art. 14** (raccolta indiretta da terze parti): Stesse info + circostanze raccolta, periodo entro cui info va fornita (non oltre 1 mese se dati usati, 3 mesi se non usati)

### 2. Right of Access (Art. 15)
- Data subject chiede confirmation se trattamento in corso + accesso a copia dati + metadati (categorie, finalità, destinatari, retention, diritti)
- **SCHUFA case (C-634/2021)**: Credit agency automated decision-making per scoring (creditworthiness) = soggetta a Art. 22 GDPR (diritti ADM). Summary explanation sì (no trade secret override), ma full algorithm disclosure no se proprietary.
- Controller deve rispondere **senza indebito ritardo, max 30 gg** (estensibile 60 gg se complesso)
- **Gratuito** primo accesso anno; ulteriori richieste: ragionevole fee

### 3. Right of Rectification (Art. 16)
- Data subject richiede rettifica dati inesatti/incompleti
- Controller corregge senza indebito ritardo + notifica a destinatari (se Art. 19)
- **C-460/2020 (T.U. & R.E. v. Google)**: Search engine: data subject deve provare inaccuratezza/diffamatorietà con "relevant & sufficient evidence"; se non ovvio, Google non tenuto rimuovere (burden on data subject per search results su terzi)

### 4. Right to Erasure – "Right to be Forgotten" (Art. 17)
- Data subject richiede cancellazione dati quando:
  - Non più necessari per finalità originaria
  - Consenso ritirato (base Art. 6(1)(a))
  - Trattamento illegittimo
  - Obbligo legale cancellazione
  - Data subject oppone (Art. 21) e nessun interesse controller prevale
  - Dati minori (raccolti infanzia)
- **Eccezioni** (Art. 17(3)): Libertà espressione/informazione; obbligo legale conservazione; interesse pubblico (sanità, ricerca); compiti pubblici; interesse legittimo controller (se no overridden)
- **Google Spain (C-131/12)**: Right to be Forgotten apply a search engines = data controller. De-referencing required per EU domains (not global, per CNIL case C-507/17). Balancing: privacy interest vs. public interest to access info, freedom expression, freedom information.
- **CNIL v. Google (C-507/17)**: Scope EU-wide ma non global; de-referencing apply EU domains; Google deve tech block per EU IPs (geo-blocking).

### 5. Right to Data Portability (Art. 20)
- Data subject richiede copia dati in formato strutturato, leggibile (CSV, JSON), portable, machine-readable
- Data raccolti su base consenso (Art. 6(1)(a)) o contratto (Art. 6(1)(b))
- Trattamento automatizzato
- Controller cede dati direttamente a data subject o a processor (se tecnicamente fattibile)
- **Escluso**: Dati terzi (solo se ottenuti data subject).

### 6. Right to Object (Art. 21)
- **Art. 21(1)**: Data subject può opporsi a trattamento basato su Art. 6(1)(e) (compito pubblico) o 6(1)(f) (interesse legittimo). Controller deve cessar trattamento salvo se compelli interessi override.
- **Art. 21(2)**: Diritto opporsi direct marketing; cessar trattamento senza condizioni (opt-out)
- **Art. 21(3) & (4)**: Special categories (Art. 9) + automated processing (Art. 22) = diritto categorico opposizione se no explicit consent

### 7. Rights related to Automated Decision-Making (Art. 22)
- **Art. 22(1)**: Data subject ha diritto non essere soggetto a decisione basata su processing automatico se ha effetti giuridici significativi.
- **Art. 22(3)** Eccezioni: (a) necessario esecuzione contratto, (b) autorizzato legge, (c) consenso esplicito
- **Art. 22(4)**: Controller implementa safeguards: informazione data subject, contestabilità, intervento umano, motivazione, data correction
- **SCHUFA**: Automated credit scoring = Art. 22 applies; companies must provide transparency + ability to challenge + human intervention avenue; summary explanation (non full algorithm) required

### 8. Right to Lodge Complaint (Art. 77)
- Data subject può ricorrere a Supervisory Authority (DPA nazionale) se ritiene violazione GDPR
- Ricorso senza pagare fee, bonus priorità violazioni gravi

---

## Data Protection Impact Assessment (DPIA – Art. 35)

**Quando obbligatoria:**
- Trattamento su larga scala (Art. 35(3)(a))
- Processing sistematico dati sensibili (Art. 9) o dati criminali (Art. 10)
- Monitoraggio comportamento (tracking online) (Art. 35(3)(b))
- Automated decision-making con significativi effetti legali (Art. 22)
- Nuove tecnologie (IA, biometria, etc.)
- Fusioni/acquisizioni (massicce banche dati)

**Contenuto DPIA**:
1. Descrizione processing (finalità, categorie dati, categorie recipients)
2. Valutazione rischi a diritti/libertà data subjects
3. Misure mitigazione (tecnico-organizzative)
4. Consultation supervisory authority (se rischio residuo elevato)

**Persona responsabile**: Entrambi controller e processor devono documentare DPIA; DPO consulta (Art. 35(2)).

**Esito**: Se rischi non mitigabili → consultare DPA prima launching processing.

---

## Data Protection Officer (DPO – Art. 37-39)

**Quando obbligatorio designare DPO:**
- **Art. 37(1)(a)**: Pubblica autorità o body pubblico (salvo corti) → **sempre**
- **Art. 37(1)(b)**: Core activities consistono in systematic, large-scale monitoring data subjects (es. social network, fintech, AdTech) → **sempre**
- **Art. 37(1)(c)**: Core activities: large-scale processing special categories (Art. 9) + criminal data (Art. 10) → **sempre**
- **Art. 37(4)**: Casi facoltativi: se utile per compliance (recommended anche per PMI se trattamento rischioso)

**Requisiti DPO**:
- Expertise in data protection law + practice
- Ability to fulfill Art. 39 tasks (independence + no conflicts)
- Può essere staff member o contracted service

**Posizione DPO** (Art. 38):
- Diretto report a management (no dismissal/penalization per performing duties)
- Data subject può contattare DPO per qualsiasi questione trattamento dati
- Bound by secrecy/confidentiality
- Può assumere altri compiti se no conflict of interest

**Compiti DPO** (Art. 39):
- Monitoraggio compliance GDPR
- Cooperare con supervisory authority
- Punto di contatto per diritti data subjects
- Assistere controller in DPIA + Art. 36 consultations
- Educazione/awareness interno
- Documentazione compliance (record processing)

---

## Data Breach & Notification (Art. 33-34)

**Quando notificare**:
- Unauthorized/accidental access, disclosure, alteration, destruction personal data
- **Art. 33**: Controller notifica **data protection authority (DPA)** senza indebito ritardo, max **72 ore** se likely to result in risk to rights/freedoms
- **Art. 34**: Se **high risk** → also notify data subjects senza indebito ritardo (es. compromised passwords, unencrypted PII breached, malicious intent)
- **Processor** notifica controller quando becomes aware breach

**Cosa comunicare (Art. 33(3))**:
- Facts breach
- Likely consequences
- Measures taken/proposed to address + mitigate
- DPO contact or authority contact point

**Eccezioni notification (Art. 34(3))**:
- Encrypted data (se encryption key not compromised)
- Pseudonymized (se key compromise not feasible)
- Immediate remediation (es. fix bug immediatamente)

---

## International Transfers Extra-UE (Art. 44-50)

**Restrizione**: Transfers to non-EU countries vietati unless:

### 1. **Adequacy Decision** (Art. 45)
- EU Commission determina che paese terzo ha livello "adequate" di data protection
- Es. Canada (PIPEDA), Japan (APPI), UK (post-Brexit), etc.
- **Pericoloso**: USA framework = controverso (GDPR privacy shield invalidato 2020; Standard Contractual Clauses – SCC – ok ma con supplementary measures per Schrems II C-311/18)

### 2. **Standard Contractual Clauses (SCC)** (Art. 46(2)(c) & 46(5))
- EU-approved model contractual terms tra controller/processor + third-party processor
- Binding anche se not signed (implied by data flows)
- **REQUIREMENT post-Schrems II**: Supplementary measures se importing country law allows govt access (es. USA CLOUD Act, FISA). Valutazione caso-caso (data sensitivity, length retention, recipient country surveillance law).

### 3. **Binding Corporate Rules (BCR)** (Art. 46(2)(b))
- Intra-group policy (multinational): group binding policy per data transfers tra affiliate
- Requires prior approval by supervisory authorities
- Es. Google, Meta multinational group BCR

### 4. **Explicit Consent** (Art. 49)
- Data subject può esplicitamente consent extra-EU transfer, sapendo no adequate safeguards
- Raro, richiede full informazione rischi

### 5. **Derogations** (Art. 49)
- Contratto data subject; interessi vitali; legal claims; compito pubblico; interests pursuit data subject/controller/third party (limited, ad-hoc)
- Es. emergency medical data transfer abroad

**Key Case – Schrems II (C-311/18)**:  
USA CLOUD Act permite law enforcement access dati da US cloud providers senza due process. CJEU ruled SCC still valid **BUT** supplementary measures (encryption, pseudonymization, data minimization, access logs, notification data subject) required se importing country = high surveillance risk. Impact: SCC to USA now requires documented risk assessment + compensation measures.

---

## Supervisory Authorities & Enforcement (Art. 51-84)

### DPA Role
- Independent (national) authority per data protection supervision
- Investigate complaints, audits, enforcement
- Issue warnings, reprimands, administrative fines
- **Art. 51**: DPA per Member State (IT: Garante Privacy). **NOT bound by executive authority.**

### Fines (Art. 83-84)

| Tier | Violation | Fine Cap |
|------|-----------|----------|
| **Tier 1** | Art. 83(4): Low-severity (controller/processor obligations) | Up to €10M or 2% global turnover |
| **Tier 2** | Art. 83(5): High-severity (fundamental principles, rights, international transfers) | Up to €20M or 4% global turnover |

**Factors** (Art. 83(2)):
- Nature, gravity, duration violation
- Intentionality, negligence
- Data subject categories affected
- Prior infractions
- Cooperation DPA
- Security measures adopted
- If profit derived from violation = deprivation profit
- Age company, financial situation

**Examples**:
- **Meta (Ireland DPA)**: €405M (WhatsApp + Instagram) for GDPR compliance 2021-2022
- **Google (France CNIL)**: €90M cookies tracking without valid consent 2020
- **TikTok (Italy DPA 2024)**: Fines for minors data handling, consent issues

---

## Practical Checklist: GDPR Implementation

**1. Inventory**
- [ ] Identify all data processing activities
- [ ] Map controller/processor relationships
- [ ] Document retention schedules per purpose
- [ ] Assess which processing triggers DPIA

**2. Legal Basis**
- [ ] Confirm Art. 6 base for each processing (consent, contract, legal obligation, etc.)
- [ ] If legitimate interest (6(1)(f)): document balancing test
- [ ] Ensure special category processing (Art. 9) has explicit base + safeguards

**3. Data Subject Rights**
- [ ] Create mechanism to fulfill Art. 15 (access), 16 (rectification), 17 (erasure), 20 (portability) requests
- [ ] Template privacy notices (Art. 13-14)
- [ ] Escalation procedure for objections (Art. 21)

**4. DPO & Governance**
- [ ] Assess if DPO mandatory (public body, large-scale processing, sensitive data)
- [ ] If required: designate, communicate contact to DPA
- [ ] Establish DPO reporting line, independence

**5. Security & Data Breach**
- [ ] Implement Art. 32 measures (encryption, pseudonymization, access controls, logs, etc.)
- [ ] Incident response plan: breach detection → 72hr DPA notification + high-risk data subject notice
- [ ] Test procedures (drills, penetration testing)

**6. Documentation & Accountability**
- [ ] Records of Processing (Art. 30): controller + processor version
- [ ] DPIA for high-risk processing (Art. 35)
- [ ] Data Processing Agreements (DPA) with processors (Art. 28)
- [ ] Consent evidence (if relying on consent)

**7. International Transfers**
- [ ] If extra-UE: Adequate country OR SCC + supplementary measures OR explicit consent
- [ ] Schrems II assessment: surveillance law country → risk analysis → mitigations

**8. Training & Awareness**
- [ ] Staff training on GDPR roles, obligations, data subject rights
- [ ] Privacy by design culture
- [ ] Regular audit + DPA consultation

---

**Reference Regulation**: Reg. UE 2016/679  
**Related Directives**: LED 2016/680 (law enforcement), eIDAS 910/2014, Data Act, Data Governance Act  
**Key CJEU Cases**: Google Spain, CNIL v. Google, Digital Rights Ireland, SCHUFA, NG v. Direktor, Schrems II, TikTok cases  
**Italian Authority**: Garante Privacy (www.garanteprivacy.it)
