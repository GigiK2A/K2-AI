# REF: E-Commerce, Firma Digitale, ISP Liability, NIS2 Cybersecurity

## E-Commerce & Consumer Protection

### Directive 2000/31/CE (E-Commerce Directive) & D.Lgs. 70/2003 (Italian transposition)

#### Key Concepts

- **Information Society Service**: Any service provided at a distance, for remuneration, by electronic means, at data subject request (e.g., website shopping, SaaS, digital goods)
- **Electronic Contracts**: Offer + acceptance via electronic means = binding contract (same legal effect as paper)
- **Consumer**: Natural person acting outside their professional activity

#### Hosting Provider Safe Harbor (Art. 14 Directive, Art. 14 D.Lgs. 70/2003)

**ISP/hosting providers** not liable for illegal content stored if:
1. No actual knowledge of illegality
2. Upon notification (takedown notice), acts expeditiously to disable access/remove
3. User not acting on provider's behalf

**Caveat**: This safe harbor applies to "mere conduit" (Art. 12) or "caching" (Art. 13). For "hosting" (Art. 14), the provider:
- Must not benefit financially from illegal activity
- Must respond to legal removal orders
- Cannot knowingly permit illegal content

**DSA (Reg. 2022/2065) update**: Safe harbor now requires proactive monitoring + systemic risk mitigation (Art. 20-22).

---

### Codice Consumo (D.Lgs. 206/2005) – Italian Consumer Code

#### Contract Conclusion & Information Requirements (Art. 49-67)

**Pre-contractual info** (Art. 49):
- Identity supplier + contact details
- Essential characteristics of goods/services
- Price (all-inclusive, incl. taxes/shipping)
- Payment, delivery terms
- Right of withdrawal
- Warranty, complaints procedure
- Complaint redress

**Acceptance**: Merchant must provide **clear, prominent button** "confirm order" or similar; no automatic renewal without affirmative consent.

#### Right of Withdrawal – "Right to Change Mind" (Art. 52-59)

- **14-day withdrawal period** (from contract conclusion or delivery, whichever later for goods)
- Consumer can withdraw **without reason**, no penalty
- **Exceptions** (Art. 52(3)):
  - Sealed goods if unsealed post-delivery (except for examination)
  - Perishable goods
  - Custom-made/personalized goods
  - Digital content already downloaded/accessed (if consumer consented to immediate delivery)
  - Services already performed (if initiated with consumer consent)
  
**Procedure**:
- Consumer notifies within 14 days (written form sufficient: email, form on site)
- Merchant must confirm receipt
- Consumer bears return costs (seller can waive)
- Refund issued within 14 days of withdrawal (minus direct costs of return)

**Pre-contractual Right of Withdrawal Renunciation**: Merchant can ask consumer to waive right BEFORE contract but only if explicit separate signature/acceptance (Art. 53-54).

#### Price Transparency & Hidden Charges (Art. 6-10, 49)

- Final price **must include all taxes, shipping, ancillary charges** upfront
- No hidden fees
- Breach = unfair term, voidable contract

#### Unfair Contract Terms (Art. 33-37)

**Black List** (Art. 33): Terms automatically void if:
- Exclude/limit seller liability for death, personal injury
- Irreversibly exclude consumer rights (e.g., "no refund ever")
- Bind consumer unilaterally without reciprocal binding on seller
- Enable supplier to unilaterally terminate without just cause

**Grey List** (Art. 34): Terms subject to fairness test:
- Broad discretion seller (price changes, delivery, etc.)
- Automatic renewal
- Non-cancellation clauses

**Remedies**: Consumer can challenge in court; AGCM (Italian Antitrust Authority) can fine for systematic unfair terms.

#### Distance Contracts – Specific Rules (Art. 55-67)

- **Confirmation in writing or durable medium** (email, PDF)
- Right withdrawal applies (14 days)
- Clear payment, delivery, cancellation procedures
- Consumer protection does **not diminish** by cross-border distance

#### Dispute Resolution (Art. 140-141-bis)

- **ADR (Alternative Dispute Resolution)**: Consumer can resort to out-of-court mediation (arbitrato, conciliazione)
- **ODR (Online Dispute Resolution)**: Platform ORIAS (https://webgate.ec.europa.eu/odr/) for cross-border complaints
- **Judicial courts**: Jurisdiction consumer's place of residence (if merchant targeted consumer there)

---

## Firma Digitale / Firma Elettronica / Firma Qualificata

### Regulation eIDAS 910/2014

#### Definitions & Legal Status

| Firma | Definizione | Valore Legale | Requisiti |
|-------|------------|---------------|-----------|
| **Firma Elettronica** | Electronic data appended to/associated with document, data identifying signatory | Probative value (allegabile in giudizio); peso determinato da giudice | No specifici requisiti; firma manuale scansionata, OTP, PIN, click "I agree" count |
| **Firma Digitale Avanzata (FdA)** | Firma elettronica qualificata se usa certificato qualificato + dispositivo sicuro | Presunzione legale di autenticità + integrità (Art. 26(2)(a)) | Certificato qualificato, standard ETSI, dispositivo qualificato (smart card, USB token) |
| **Firma Digitale Qualificata (FdQ)** | Firma digitale basata certificato qualificato di sottoscrizione, realizzata via dispositivo qualificato | Equivalenza legale firma autografa (Art. 25(2)): "advanced electronic signature created using a qualified certificate" | Rilascio da TSP (Trust Service Provider) qualificato, sospensione/revoca centralizzata |

#### Legal Value (Art. 25-26)

- **Art. 25(1)**: Electronic signature riconosciuto legalmente; non discriminabile perché "semplice" firma elettronica
- **Art. 25(2)**: Advanced electronic signature (qualificata) = **same legal effect as handwritten signature** per documenti pubblici/privati
- **Art. 26(2)(a)**: Firma qualificata = presunzione legale di autenticità sottoscrittore + integrità documento (refutabile solo con controprova)

#### Trust Service Providers (TSPs) – Regulation (Art. 2, 17-36)

**TSP**: Provider erogante:
- Qualified certificates issuance
- Timestamping (marcatura temporale)
- Electronic seals (sigilli elettronici)
- Preservation long-term electronic signatures (qualified preservation)
- Web authentication

**Requirements**:
- Registered with national supervisory body (ACAB – Autorità di Certificazione Accreditata in Italia = AgID)
- Audit annuale ISO 27001 + eIDAS-specifico
- Liability insurance
- Transparency report (no unilateral suspension senza just cause)

#### Italy: Digital Signature Infrastructure

- **CNS (Carta Nazionale dei Servizi)**: Smart card with qualified certificate; used in PA + e-banking
- **CRS (Certificato di Firma Remota)**: Remote signing via web; TSP holds key, signer authenticates (PIN/OTP)
- **Qualified timestamps** (marcature temporali): Issued by TSP; prove document existed at specific time
- **Smartcards**: Ubikey, Aruba, etc. (private sector adoption)

#### Contract Signing & Compliance

**Valid e-signatures for contracts**:
1. Firma semplice (click "I agree" + email confirmation): Probative value, disputes on witness
2. Firma avanzata (OTP, PIN): Presume autenticità if non-refuted
3. Firma qualificata (certificato qualificato, dispositivo qualificato): Presumzione iuris et de iure (only refutable by contradicting quale sottoscrittore)

**Recommended practice** (B2B/B2C):
- Use firma qualificata for high-value contracts (real estate, M&A, employment)
- Firma avanzata for commercial agreements
- Firma semplice for ToS acceptance, newsletters

**Timestamp requirement**: If disputes about **when** document signed → include qualified timestamp (Art. 36 eIDAS).

---

## ISP Liability & Intermediary Responsibility

### D.Lgs. 70/2003 (Transposition Directive 2000/31/CE)

#### Three Categories of ISP

| Categoria | Servizio | Safe Harbor Condition |
|-----------|---------|----------------------|
| **Mere Conduit** (Art. 12) | Transmission dati (ISP, backbone provider) | No involvement; automatic, temporary, cache pass-through; no knowledge content |
| **Caching** (Art. 13) | Temporary copy (CDN, cache server) | Non-intentional; automatic; user can delete; provider complies takedown notices |
| **Hosting** (Art. 14) | Storage data (web hosting, cloud storage, social media) | No knowledge illegality; expeditious removal upon notification (notice-and-takedown) |

**Key principle**: ISP not liable for user-generated content **if** they don't knowingly contribute + comply with takedown orders.

#### Notice-and-Takedown (Art. 14-bis D.Lgs. 70/2003, Art. 19-22 DSA Reg. 2022/2065)

**Process**:
1. **Notification**: Right holder (copyright owner, defamation victim, etc.) notifies ISP of illegal content (DMCA-style)
   - Must be: Specific (exact URL), identify claimant, specify infringement (copyright, defamation, etc.)
   - ISP provides notification form + contact (contact point, email)
2. **ISP response**: "Expeditious" removal (2-5 days typical; law no set timeframe)
   - Remove/disable access content
   - Notify uploader (user) + right holder
3. **Counter-notification** (optional): User can claim removal erroneous
   - ISP can restore if no court order, unless right holder files lawsuit

**Limitations**:
- Over-removal risk: ISP removes too hastily (chilling effect on speech)
- Abuse: False DMCA notices (penalties under US DMCA 17 USC 512(f), but weaker in EU)
- **DSA improvement**: Art. 20(2) requires ISP assess **legality** of takedown notice (not blind compliance)

#### Liability for Moderation Decisions (Art. 15-17 DSA)

Recent DSA clarifies ISP **not liable** for moderation decisions (removal, shadow-banning, etc.) if:
- Decision taken in good faith (bona fide)
- Proportionate to infringement
- Respect due process (explain to user why removal, allow appeal)

Conversely, ISP **can be liable** if:
- Systematically remove legal content (overreach)
- Refuse to remove clearly illegal content (passivity)
- Discriminate between users (unfair enforcement)

---

## NIS2 – Cybersecurity for Critical Infrastructure

### Directive 2022/2555/EU & D.Lgs. 138/2024 (Italian Implementation)

**NIS2** (Network & Information Systems Directive 2) strengthens cybersecurity for operators of essential services + digital service providers.

#### Scope: Covered Entities

**Essential Service Operators** (Art. 2(2)):
- Energy (electricity, gas, oil, heating)
- Transport (air, rail, water, road)
- Banking + financial market infrastructure
- Healthcare (hospitals, pharmacies)
- Drinking water + waste water
- Digital infrastructure (data centers, DNS, TLD registries, public clouds)
- Public administration
- Space

**Digital Service Providers** (DSPs):
- Online marketplaces
- Search engines
- Social media platforms
- Cloud services (IaaS, PaaS, SaaS)
- Messaging apps
- Video platforms
- **Exemption**: SMEs + microenterprises not core to digital infrastructure

#### Security Obligations (Art. 21-26 NIS2)

| Obligation | Requirement |
|-----------|------------|
| **Risk Management** (Art. 21) | Identify, assess, manage cybersecurity risks; technical + organizational measures proportionate to risk |
| **Incident Response** (Art. 23) | Procedure to detect, investigate, respond to incidents; testing drills |
| **Business Continuity** (Art. 24) | Backup systems, disaster recovery; ensure service availability |
| **Supply Chain Security** (Art. 25) | Assess + manage cybersecurity risks from suppliers + third parties |
| **Reporting Incidents** (Art. 23) | **Significant incidents** → notify authority **within 24 hours** (D.Lgs. 138/2024: ACN - Autorità Cybersicurezza Nazionale) |
| **Annual Attestation** (Art. 26) | Annual statement compliance with NIS2 obligations |
| **Board Accountability** | Management/board accountable for cybersecurity (not delegable to IT alone) |

#### Incident Reporting Thresholds (D.Lgs. 138/2024 Art. 19-20)

**Significant incident** = impact serious on service:
- Availability: Service unavailable >4 hours
- Integrity: Data compromise affecting users
- Confidentiality: Unauthorized access to restricted data
- Or **minor incident** if crosses severity thresholds (ACBN defines)

**Report to**:
- **ACN** (Autorità Cybersicurezza Nazionale) + relevant sectoral authority
- **CSIRT Italia** (coordinamento nazionale)
- Affected users (if personal data compromised → GDPR Art. 33-34 applies too)

#### Penalties (D.Lgs. 138/2024, Art. 51-52)

| Violation | Fine |
|-----------|------|
| Non-compliance security measures | €10k - €5.6M (or up to 10% EU turnover) |
| Failure incident notification (24hr) | €10k - €3.5M |
| False/late reporting | €10k - €2M |
| Obstruction investigation | €10k - €1.4M |

Penalties proportionate severity + size entity.

#### Practical Compliance (NIS2)

**Actions**:
1. **Asset Inventory**: Identify critical systems, data, dependencies
2. **Risk Assessment**: NIST CSF, ISO 27001, threat modeling
3. **Controls Implementation**: Firewall, endpoint protection, encryption, MFA, IDS/IPS, SIEM
4. **Incident Response Plan**: Playbook, contact details, test quarterly
5. **Third-Party Risk**: Audit suppliers, SLAs, contractual cybersecurity obligations
6. **Training**: Annual staff cybersecurity awareness
7. **Documentation**: Keep evidence compliance (audit logs, policy, incident records)
8. **Board Reporting**: Cybersecurity status to management/board quarterly

---

## Data Act & Data Governance Act (Brief Overview)

### Data Act (Regulation 2024/1937, in progress/final 2024)

**Objective**: Enable data sharing between enterprises for competitive benefit while protecting IP/privacy.

#### Key Concepts

- **Industrial data**: Data generated by devices/systems (IoT, manufacturing, vehicles)
- **B2B data access**: Companies can request access competitor/supplier data if non-sensitive
- **Fairness**: Terms/conditions for data access cannot be unfairly restrictive
- **Right to erasure**: Data subject retains right erasure (GDPR Art. 17) even in B2B context

#### Obligations (Provisioning)

- Provide data in machine-readable format
- Reasonable fee (reflect cost, not prohibitive)
- Contractual fairness (no discrimination, no tying)
- Non-sensitive data only (personal data excluded; trade secrets protected)

---

### Data Governance Act (Regulation 2022/868, **in force since Sept 2023**)

**Objective**: Enable beneficial reuse data while respecting privacy + IP.

#### Key Mechanisms

| Mechanism | Purpose |
|-----------|---------|
| **Data Altruism** (Art. 5-10) | Non-profit organizations re-use personal data donors for public interest (health research, climate, etc.) |
| **B2B Data Sharing** (Art. 11-21) | Intermediaries help businesses share industrial data securely |
| **Public Sector Re-use** (Art. 22-42) | Member States encourage public body data sharing with private sector (research, innovation) |

#### Intermediaries – Conditions (Art. 11)

Intermediary organizations must:
- Be independent from data holders + data requesters
- Neutral terms/conditions for data sharing
- Transparent pricing
- Document data sources + audit trails
- No unlock personal data without separate legal basis (GDPR)

---

## Practical Checklist: E-Commerce + ISP + Cybersecurity

### E-Commerce Compliance (Codice Consumo)

**Pre-Sale**:
- [ ] Website displays all mandatory info (identity, address, T&C, price inclusive taxes)
- [ ] Clear privacy policy (GDPR Art. 13-14)
- [ ] No dark patterns (DSA Art. 25)
- [ ] Return/withdrawal info prominently displayed

**Contract Formation**:
- [ ] Order confirmation email within 1 business day
- [ ] "Confirm order" button (not pre-checked, not duplicate)
- [ ] Clear price breakdown (product + shipping + any fees)

**Post-Sale**:
- [ ] Support contacts (phone, email, chat)
- [ ] Withdrawal period honored (14 days, except exceptions)
- [ ] Complaint redress procedure
- [ ] Dispute resolution (ADR/ODR info provided)

### ISP Notice-and-Takedown Preparedness

**Policies**:
- [ ] Published T&C on content removal process
- [ ] Notification mechanism (form, email, process)
- [ ] Response timeline committed (e.g., "within 48 hours")
- [ ] Counter-notification procedure explained
- [ ] Archive removal notices (for audit trail)

**Processes**:
- [ ] Intake form captures: Reporter identity, infringement type, URL, jurisdiction, supporting docs
- [ ] Assessment: Reviewer evaluates legality (not automatic removal)
- [ ] Decision: Remove, reject, or escalate (if ambiguous)
- [ ] Notification: User notified removal + reason + appeal option
- [ ] Appeals: User can contest; company reviews independently

### NIS2 Cybersecurity Program (D.Lgs. 138/2024)

**Governance**:
- [ ] Designate CISO or security officer
- [ ] Board-level cybersecurity oversight
- [ ] Annual risk assessment + mitigation plan
- [ ] Incident response plan (documented, tested)

**Technical Controls**:
- [ ] Firewalls, IDS/IPS, endpoint protection
- [ ] Encryption (data in transit, at rest)
- [ ] MFA for critical accounts
- [ ] SIEM + logging (retain 90+ days)
- [ ] Backup + disaster recovery (test quarterly)

**Operational**:
- [ ] Vendor risk assessment (security questionnaires, audits)
- [ ] SLAs with vendors (uptime, SLA breach remedies)
- [ ] Staff training (annual phishing simulation + cybersecurity awareness)
- [ ] Incident reporting to ACN (within 24hr significant incident)
- [ ] Documentation (policies, risk register, incident log, training records)

**Audit & Compliance**:
- [ ] Annual self-assessment vs. NIS2 requirements
- [ ] Third-party audit (ISO 27001, SOC 2, etc.)
- [ ] Regulatory inspections (ACN may audit)
- [ ] Board reporting (quarterly cybersecurity dashboard)

---

**References:**
- Directive 2000/31/CE (e-commerce)
- D.Lgs. 206/2005 (Codice Consumo)
- D.Lgs. 70/2003 (ISP liability)
- Regulation 910/2014 (eIDAS – firma digitale)
- Directive 2022/2555/EU + D.Lgs. 138/2024 (NIS2)
- Regulation 2022/868 (Data Governance Act)
- Regulation 2024/1937 (Data Act)

**Authorities:**
- AGCM (Autorità Garante Concorrenza Mercato)
- Garante Privacy (GDPR/DPA)
- AgID (Agenzia per l'Italia Digitale – eIDAS)
- ACN/CSIRT Italia (cybersecurity)
