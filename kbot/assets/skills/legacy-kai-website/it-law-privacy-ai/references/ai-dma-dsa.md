# REF: AI Act, DMA, DSA – Compliance & Enforcement

## AI Act – Reg. UE 2024/1689 (in vigore dal 2025)

### Risk-Based Classification

Reg. 2024/1689 classifica AI systems per rischio; obblighi variano per tier.

| Livello | Definizione | Esempi | Obblighi Principali |
|---------|------------|--------|-------------------|
| **Vietato (Prohibited)** | AI systems con rischio inaccettabile | Social credit scoring (comportamento); identificazione biometrica real-time targeting di minori; manipolazione comportamento (dark patterns); sfruttamento psicologico vulnerabili | Divieto assoluto (art. 5) |
| **Alto Rischio (High-Risk)** | Significativo danno diritti/libertà | Credit scoring; recruitment; controllo accesso servizi essenziali; identificazione biometrica; sistemi medicina; autonomous vehicles; gestione dati biometrici pubblici | Conformance assessment, registrazione, risk mitigation (art. 6-52) |
| **General-Purpose AI (GPAI)** | Model training dati massivi, versatile (es. LLM, vision models) | ChatGPT, GPT-4, LLaMA, Mistral, DALL-E | Trasparenza, test rischi, content filtering (art. 53-62) |
| **GPAI ad Alto Rischio (GPAI High-Risk)** | GPAI con capacità causare harm significativo (es. dual-use) | Modelli potenzialmente weaponizable, capaci autonoma azione | Upstream: sistema di governance, red-teaming, evaluations (art. 54-58) |
| **Basso/Minimo Rischio** | Trattamento automatico con minimo impatto | Chatbot customer service, spam filter, recommender systems generici | Compliance leggera (trasparenza, logo obbligatorio) |

### High-Risk AI Systems: Obblighi (Art. 6-52)

Quando AI system è classificato alto rischio:

**1. Risk Management System** (Art. 9)
- Continuous monitoring rischi residui
- Mitigation plan (tecnico-organizzative)
- Human oversight / intervention mechanism
- Post-deployment monitoring

**2. Data Governance** (Art. 10)
- Training data quality (raccolta, annotazione, no significant bias, representative)
- Validation data set disjoint da training
- Documented data source + origin
- Test set representative

**3. Technical Documentation** (Art. 11)
- Detailed AI model design, training data, validation metrics, testing procedures
- Risk assessment report
- Human oversight protocol

**4. Transparency & Disclosure** (Art. 13)
- **AI systems affecting legal rights**: Provider must disclose AI is involved
- **GDPR Art. 22 link**: Decision-making systems must inform data subjects
- Intelligibility per intended users

**5. Conformance Assessment** (Art. 23)
- Manufacturer o third-party notified body conducts assessment
- Technical file + audit trail
- EU Declaration of Conformity

**6. Registration** (Art. 49)
- High-risk AI systems registered in EU database
- Before placing on market
- Provider responsible for registration

**7. Post-Market Monitoring & Reporting** (Art. 25-26)
- Continuous monitoring system performance post-deployment
- Adverse events reporting (malfunctions, discrimination, etc.)
- Notified body / EU authority notification if serious risks

**8. Human Oversight** (Art. 14)
- Natural persons capable to understand/supervise operation
- Ability to intervene / stop system
- AI should **not override** human judgment w/o proportionate safeguard
- Training on AI capabilities/limitations

### General-Purpose AI (GPAI) – Art. 53-62

**Definition**: Foundation model (LLM, vision-language model) trained on vast unlabeled data, adaptable multiple tasks.

**GPAI Obligations**:

| Obligation | Requirement |
|-----------|------------|
| **Transparency** (Art. 53(1)) | Disclose that GPAI is trained; publish summary of training data |
| **Testing & Evaluation** (Art. 53(2)) | Benchmark systemic risks (hallucinations, bias, harmful content generation) |
| **Content Filter & Safeguards** (Art. 53(3)) | Prevent illegal content generation (CSAM, violence, etc.) |
| **Risk Mitigation** (Art. 54) | Identify, assess, mitigate systemic risks (model collapse, adversarial attacks, data poisoning) |
| **Documentation** (Art. 55(1)) | Technical documentation on training data, model architecture, evaluation results |
| **Downstream Monitoring** (Art. 55(2)) | Monitor how downstream users (fine-tuners, deployers) use model; report serious incidents to authorities |
| **Cyber Security** (Art. 55(3)) | Protect model & training infrastructure from unauthorized access / theft |

**GPAI High-Risk** (Art. 56):
- If GPAI can pose systemic risk (hallucinations leading to harm, dual-use capability for weapons/crime) → elevated obligations
- Red-teaming (adversarial testing)
- Upstream model evaluation before release
- Governance system for handling issues post-release
- **Exemption for open-source**: GPAI released under open-source license may exempt from Art. 53-56 IF provider takes mitigating measures

### Prohibited AI (Art. 5)

**Absolute bans**:

1. **Subliminal manipulation**: Techniques beyond conscious perception to distort behavior (Art. 5(1)(a))
2. **Exploitation vulnerabili**: AI designed to exploit physical/mental disability, age, social condition to materially distort free will (Art. 5(1)(b))
3. **Biometric identification real-time, non-law enforcement**: Mass ID systems (facial recognition) in public spaces without law enforcement context (Art. 5(1)(c))  
   - **Exception**: Law enforcement + specific purposes (counterterrorism, serious crime)
4. **Social credit scoring**: AI systems that assign credit rating behavior based on personality/social factors (Art. 5(1)(d))
   - **Impact**: Bans China-style social credit; limits corporate risk scoring unless transparent + consented

### Enforcement (Art. 77-90)

**National Competent Authorities**: Member States designate AI office + market surveillance authority.

| Infraction | Fine |
|-----------|------|
| Prohibited AI (Art. 5) | Up to €30M or 6% global turnover |
| High-risk non-compliance (Art. 6-52) | Up to €15M or 3% global turnover |
| GPAI non-compliance (Art. 53-58) | Up to €10M or 2% global turnover |
| Incorrect classification | Up to €10M or 2% global turnover |
| False documentation | Up to €10M or 2% global turnover |
| Misleading product description | Up to €7.5M or 1.5% global turnover |

**Remedies**: Bans, recalls, fines, public alerts.

---

## DMA – Reg. UE 2022/1925 (Digital Markets Act)

### Scope: Gatekeepers

**Gatekeeper = digital platform with:**
- Significant impact EU internal market (€7.5B+ annual turnover or €75B+ market cap)
- Position as gateway between businesses + consumers
- Entrenched, durable market power

**Current Designations** (2023-24):
- **Google** (Search, Play Store, ads)
- **Meta** (Facebook, Instagram, WhatsApp)
- **Amazon** (Marketplace, logistics)
- **Apple** (App Store)
- **TikTok** (Recommend algorithm)
- **Microsoft** (Azure, Bing)
- **Booking.com** (travel)

### Gatekeeper Obligations (Art. 5-7)

| Obligation | Requirement |
|-----------|------------|
| **Fair Access** (Art. 5(a)) | Provide business users fair, non-discriminatory access to platform |
| **Ranking Transparency** (Art. 5(b)) | Disclose parameters ranking search results, ads, content |
| **Data Portability** (Art. 5(c)) | Enable data subject & business users to obtain their data; facilitate switching between services |
| **Interoperability** (Art. 5(d)) | Allow third-party messengers interoperate with WhatsApp, Facebook Messenger (if technically feasible) |
| **Prohibition Self-Preferencing** (Art. 6(a)) | Cannot advantage own services vs. competitors' (es. YouTube ranking own music vs. Spotify) |
| **Access to Data** (Art. 6(b)) | Cannot restrict access business user data generated by their activity (unless consent, safety, IP) |
| **Prohibition Tying** (Art. 6(c)) | Cannot condition access one service on using another (no bundling coercion) |
| **Termination Fairness** (Art. 6(d)) | Cannot terminate business users without 30-day notice + reason; must allow appeal |
| **Cost Transparency** (Art. 6(e)) | Disclose costs of platform access, delivery, curation |
| **Ad Transparency** (Art. 6(f)) | Advertisers & publishers see data used for ad targeting; right to inspect |

### DMA Enforcement (Art. 16-26)

- **EU Commission** investigates (Art. 17); can issue cease-and-desist orders
- **Interim measures** if irreparable harm risk
- **Fines** up to €10M or 10% global turnover for obstruction
- **Structural remedies** (forced divestitures) if behavioral remedies insufficient
- **Monitoring** via independent compliance officer (if repeated infraction)

---

## DSA – Reg. UE 2022/2065 (Digital Services Act)

### Scope: All Online Platforms

DSA applies to **any service providing digital content transmission** to users (vastly broader than DMA gatekeepers):
- Social media platforms
- Video-sharing platforms
- Online marketplaces
- Search engines
- Messaging apps
- Streaming services

### Key Categories

| Category | Obligation Level |
|----------|-----------------|
| **All Providers** | Basic transparency, T&C, contact, complaint handling |
| **Hosting Services** | Notice-and-takedown (Directive 2000/31/CE compliance + DSA Art. 19-22) |
| **Online Platforms** | Content moderation, recommender systems, ad transparency, user rights |
| **Very Large Platforms (VLPs)** | Ad hoc for >45M EU users: systemic risk mitigation, independent audit, crisis response |

### Core Obligations

#### 1. **T&C & Transparency** (Art. 5, 14-15)
- Publish T&C in plain language; specify rules for content removal/restrictions
- Annual transparency report: moderation data, appeals, user complaints
- Accountability statement (who decides removals, criteria)

#### 2. **Illegal Content Removal** (Art. 17)
- Respond to legal removal notices (law enforcement, judicial orders, reports for CSAM/terrorism/hate speech)
- Remove illegal content & retain data for law enforcement if needed
- "Expeditious" removal (days, not months)
- No over-removal (copyright claims abuse = risk)

#### 3. **Hosting Service Safe Harbor** (Art. 18-21 = Directive 2000/31 CE alignment)
- Platform not liable for user-generated content if:
  - No actual knowledge of illegality
  - Upon notification (notice-and-takedown), acts **expeditiously** to remove/disable access
  - User not on platform's behalf (arm's length condition)
- **Caveat**: DSA now requires proactive monitoring systems + risk mitigation, reducing pure notice-based immunity

#### 4. **Recommender Systems** (Art. 27)
- **Transparency**: Disclose main parameters used in ranking / recommendation algorithm
- **User Control**: Offer alternative non-personalized ranking option
- **No Dark Patterns**: Cannot manipulate recommendation to nudge harmful content

#### 5. **Advertising Transparency** (Art. 24-26)
- **Ads Identification**: Label ads clearly; disclose advertiser
- **Ad Targeting Parameters**: Show why ad was targeted to user (age, interests, etc.)
- **Ad Archives**: Maintain searchable archive of political/issue ads (min. 6 months)

#### 6. **Dark Patterns Prohibition** (Art. 25)
- Cannot use deceptive design tricks to manipulate users into sharing data / performing unwanted actions
- Examples: Pre-checked consent boxes, confusing privacy settings, fake "close" buttons, countdown timers creating urgency
- **Penalty**: Up to €6% global turnover (or €60M if below 6%)

#### 7. **Minors Protection** (Art. 28)
- VLPs must implement safeguards for minors (age verification, parental consent, privacy by default)
- Limit profiling minors
- Prohibit manipulation minors

#### 8. **Crisis Response Protocol** (Art. 31)
- VLPs must have crisis management plan for systemic risks (disinformation, violence, etc.)
- Cooperation with authorities during emergencies

### Very Large Platforms (VLPs) – Enhanced Obligations (Art. 33-40)

**Trigger**: >45M monthly active users in EU.

| Obligation | Details |
|-----------|---------|
| **Risk Assessment** (Art. 34) | Annual assessment of systemic risks (illegal content, misinformation, manipulation, harm minors) + mitigation strategy |
| **External Audit** (Art. 37) | Independent audit of compliance measures + risk assessments; public report |
| **Crisis Plan** (Art. 38) | Procedure to handle crisis events (coordinated with authorities) |
| **Data Access Researchers** (Art. 40) | Provide vetted researchers access to data for systemic risk studying (subject to privacy) |
| **Coordination** | Participate in EU Digital Services Coordinator network |

### DSA Enforcement (Art. 51-78)

- **Digital Services Coordinators** (national authorities per MS)
- **EU Commission** oversight for VLPs
- **Fines**: Art. 74-75:
  - Up to €6% global turnover (all providers)
  - Up to €5% global turnover (VLPs for systemic risks)
  - Up to €50M if fine < €50M
- **Interim measures**, monitoring, mandatory compliance officers for repeat offenders

---

## DMA vs. DSA: Quick Comparison

| Aspect | DMA | DSA |
|--------|-----|-----|
| **Scope** | Gatekeepers (large, entrenched, multi-sided markets) | All digital platforms & hosting services |
| **Focus** | Competition (anti-monopoly) | Content moderation + user rights |
| **Key Obligations** | Interoperability, data portability, no self-preferencing, fair access | Moderation, transparency, recommender fairness, dark pattern prohibition |
| **Enforcement** | EU Commission (antitrust-style) | National coordinators + Commission (VLPs) |
| **Fines** | Up to 10% global turnover (DMA) | Up to 6% global turnover (DSA) |
| **Affected Platforms** | ~10 (Google, Meta, Amazon, Apple, Microsoft, TikTok, Booking) | All digital services (thousands) |

---

## Practical AI Act Compliance Checklist

### Classification & Risk Assessment
- [ ] Classify AI system per risk tier (prohibited, high-risk, GPAI, low-risk)
- [ ] Document classification rationale (use case, data, outputs, user population)
- [ ] If high-risk: conduct detailed risk assessment per Art. 6

### High-Risk Systems
- [ ] Risk management system: identify hazards, evaluate likelihood/severity, mitigation
- [ ] Training data governance: source, quality, bias testing, documentation
- [ ] Validation & testing: metrics, test sets, performance thresholds
- [ ] Technical documentation (Art. 11): architecture, training data summary, test results
- [ ] Conformance assessment: self-assessment or notified body audit
- [ ] Register system in EU NACE database
- [ ] Post-deployment monitoring: incident tracking, periodic reassessment
- [ ] Human oversight protocol: when/how humans review/override system decisions
- [ ] Transparency: disclose AI involvement to affected persons (e.g., HR, credit decisions)

### GPAI Obligations
- [ ] Publish summary of training data composition
- [ ] Document systemic risks identified (hallucinations, bias, harmful content potential)
- [ ] Implement content filters preventing illegal outputs
- [ ] If open-source: comply with simplified requirements (Art. 56(3))
- [ ] Downstream monitoring: track how users (fine-tuners, deployers) use model

### Organizational
- [ ] Designate compliance officer (if recurrent violations)
- [ ] Training: staff awareness on AI Act obligations
- [ ] Audit trail: maintain records of risk assessments, testing, incidents
- [ ] Incident response: procedure for reporting serious incidents to authorities

---

## DMA & DSA Compliance Checklist

### For Gatekeeper (DMA)
- [ ] Fair access business users (no discrimination)
- [ ] Ranking transparency: disclose algorithm parameters
- [ ] Data portability: facilitate data subject/business user data export
- [ ] No self-preferencing: treat own services equivalent to competitors
- [ ] Termination fairness: 30-day notice, appeal mechanism
- [ ] Cost transparency: disclose fees, delivery costs
- [ ] Annual compliance report to EU Commission

### For All Platforms (DSA)
- [ ] Terms & Conditions: clear, transparent, plain language
- [ ] Contact info: designated legal representative + single point of contact (SPOC)
- [ ] Moderation transparency: annual report on removals, appeals, decisions
- [ ] Illegal content: respond to law enforcement notices expeditiously
- [ ] Recommender systems: disclose parameters, offer alternative ranking
- [ ] Advertising: label ads, show targeting rationale, maintain ad archive
- [ ] Dark patterns: audit design for deceptive tricks; remove if found
- [ ] Minors: age-appropriate safeguards if users <18

### For Very Large Platforms (DSA)
- [ ] Systemic risk assessment: annual eval illegal content, misinformation, manipulation, minors harm
- [ ] Mitigation strategy: concrete measures for identified risks
- [ ] External audit: independent assessment + public report (Art. 37)
- [ ] Crisis plan: protocol for emergencies (coordination with authorities)
- [ ] Researcher access: vetted researchers can access data for systemic risk studies
- [ ] Regulatory coordination: participate in EU Digital Services Coordinator meetings

---

**Reference**: Reg. 2024/1689 (AI Act), Reg. 2022/1925 (DMA), Reg. 2022/2065 (DSA), Directive 2000/31/CE (e-commerce), Directive 2004/48/CE (IP enforcement)

**EU Guidance**: AI Act Implementation Group, DSA Transparency Reports Database, DMA Compliance Guidelines (EC)

**Enforcement Authority**: EU Commission (DMA, DSA gatekeepers), Member State Digital Services Coordinators (DSA national enforcement), National competent authorities (AI)
