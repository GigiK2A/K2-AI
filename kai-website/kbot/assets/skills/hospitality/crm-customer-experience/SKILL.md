---
name: crm-customer-experience
description: >
  CRM e Customer Experience operativi per professionisti marketing. CRM tipologie
  (operational/analytical/collaborative), vendor landscape (Salesforce, HubSpot,
  Dynamics), Customer Data Platform (CDP) vs CRM vs DMP, single customer view,
  GDPR. Customer journey mapping: personas, stages, touchpoints, moments of truth,
  service blueprint. Loyalty program design: tier structures, earning/redemption
  economics, liability/breakage, gamification. Churn prediction: RFM+ML models,
  early warning system, retention interventions, win-back framework, SaaS NRR/GRR.
  CX measurement: NPS inner/outer loop, CSAT, CES, SERVQUAL 5 gap model, VoC
  programs, text analytics. Usa per: "CRM strategy", "journey map", "loyalty
  program design", "churn prediction", "win-back campaign", "NPS methodology",
  "service blueprint", "CX KPI".
---

# CRM e Customer Experience

## Introduzione

Questo skill copre la progettazione e ottimizzazione end-to-end di Customer Relationship Management (CRM) e Customer Experience (CX) per organizzazioni che operano in retail, e-commerce, SaaS, B2B e servizi. Combina strategie di architettura dati (data warehouse, CDP), design dell'esperienza cliente (journey mapping, service blueprint), strategie di fidelizzazione (loyalty program), analitiche predittive (churn prediction, win-back) e misurazione della soddisfazione (NPS, CSAT, CES, SERVQUAL).

Ogni sezione fornisce framework operativi, checklist di implementazione, formule, tabelle comparative per settore, e best practices da applicare con Salesforce, HubSpot, Microsoft Dynamics, Zoho, Pipedrive, Oracle, SAP.

---

## Routing Table

| Tema | File | Utilizzo primario |
|---|---|---|
| **CRM Architecture & Strategy** | `references/crm-architecture-strategy.md` | Selezione vendor, data model, single customer view, GDPR, implementation roadmap |
| **Customer Journey Mapping** | `references/customer-journey-mapping.md` | Personas, stages, touchpoints, moments of truth, service blueprint, omnichannel |
| **Loyalty Program Design** | `references/loyalty-program-design.md` | Tier structure, earning/redemption mechanics, economics, gamification, measurement |
| **Churn & Retention** | `references/churn-retention-winback.md` | Churn prediction models, early warning, retention interventions, win-back strategy |
| **CX Measurement & VoC** | `references/cx-measurement-voc.md` | NPS/CSAT/CES/SERVQUAL, VoC programs, text analytics, linking CX to financial outcomes |

---

## Operative Instructions

### 1. Diagnosi CRM Iniziale (Checklist)
- **Maturità attuale**: Valutare se operational (sales force automation), analytical (predictive analytics), o collaborative (multi-channel) CRM
- **Stato dati**: Audit qualità dati (completezza, duplicati, outliers), single customer view esistente?
- **Stack tecnologico**: Quali sistemi oggi? Grado di integrazione?
- **Gap organizzativo**: Readiness team, skill attuali, training needs
- **Business case**: Revenue impact, cost avoidance, customer lifetime value (CLV) target
- **Compliance**: GDPR, CCPA, data retention policy

**Deliverable**: CRM Assessment Report (2-3 pagine, incluso vendor scorecard)

### 2. Customer Journey Mapping (Workflow)
1. **Persona Definition**: Creare 3-5 primary personas (demographic, behavioral, jobs-to-be-done)
2. **Stage Identification**: Awareness → Consideration → Decision → Service → Loyalty → Advocacy
3. **Touchpoint Mapping**: Per stage, definire owned (sito, email, CRM), paid (ads, sponsorship), earned (social, reviews)
4. **Emotion Mapping**: Assegnare sentiment (positive 😊, neutral 😐, negative 😞) a ogni touchpoint
5. **Pain Point Identification**: Friction, delays, unclear info, support gaps
6. **Moments of Truth**: Identificare Zero MoT (ricerca online), First MoT (homepage/vetrina), Second MoT (product experience), Third MoT (advocacy)
7. **Service Blueprint**: Estendere con line of visibility, backstage processes, support infrastructure

**Deliverable**: Customer Journey Map (visual + tabulare), Pain Point Register, Opportunity List

### 3. Loyalty Program Design (Step-by-Step)
1. **Program Strategy**: Transactional (points-based), experiential (status tiers), emotional (community), or hybrid?
2. **Tier Definition**: Scegliere tier structure (e.g., Silver/Gold/Platinum), progression velocity, requalification rules
3. **Earning Mechanics**: Base earn rate (es: 1€ = 1 punto), accelerators (category multipliers, bonus events), caps
4. **Redemption Catalog**: Definire reward options, redemption thresholds, point values
5. **Economics Model**: Projection di member vs non-member spend uplift, CLV per tier, program profitability
6. **Gamification Layer** (optional): Badges, streaks, challenges per boost engagement
7. **Measurement Framework**: Active rate, tier migration, retention lift, CLV uplift, promo response

**Deliverable**: Loyalty Program Specification, Economics Model (Excel), Member Segment Profile

### 4. Churn Prediction & Retention (ML Workflow)
1. **Data Assembly**: Raccogliere RFM (Recency, Frequency, Monetary), engagement metrics, transaction history, demographic data, contextual signals
2. **Feature Engineering**: Lag variables (30/60/90 days), aggregations, trend indicators, seasonality adjustments
3. **Model Training**: Logistic regression baseline → random forest → XGBoost/gradient boosting → neural net per complexity
4. **Model Evaluation**: Precision/recall, F1, AUC-ROC, lift chart, calibration check
5. **Early Warning System**: Traffic light rules (green/yellow/red) per attivare interventions
6. **Intervention Design**: Save offers (discount, service upgrade, tier promotion), content (educational, community), relationship (account manager)
7. **Win-Back Framework**: Reactivation windows (30/60/90/180 days post-churn), win-back offer economics, sequence testing

**Deliverable**: Churn Model Card, Early Warning Dashboard, Retention Campaign Playbook

### 5. CX Measurement & Voice of Customer (VoC) Setup
1. **NPS Program**: Deploy transactional + relational NPS surveys, segment by persona/journey stage, establish Inner/Outer Loop (feedback → action → communication of improvement)
2. **CSAT & CES**: Post-purchase/post-support CSAT (5-point scale), post-interaction CES (7-point effort scale)
3. **SERVQUAL Assessment**: Conduct gap analysis across 5 dimensions (Reliability, Assurance, Tangibles, Empathy, Responsiveness)
4. **VoC Collection**: Surveys, text analytics (sentiment, topic modeling, NPS driver analysis), social listening, review mining, support ticket analysis
5. **Dashboard Design**: Executive dashboard (NPS trend, segment performance, key driver index), operational dashboard (response rate, time-to-resolution, effort)
6. **Financial Linkage**: Map CX metrics → retention lift → CLV → enterprise value

**Deliverable**: CX Metrics Framework, VoC Program Charter, Dashboard Specification

---

## Quick Reference: Key Formulas & Metrics

### CX Metrics

- **NPS** = (% Promotori 9-10) − (% Detrattori 0-6)
  - Segmentation: NPS per persona, touchpoint, journey stage
  - Inner Loop: Feedback → Prioritize → Resolve → Measure → Communicate

- **CSAT** = (Risposte 4-5 / Totale risposte) × 100
  - Scala: 5-punti (1=Molto insoddisfatto, 5=Molto soddisfatto) o 1-10
  - Touchpoint-specific: post-acquisto, post-support, post-delivery

- **CES** = Media scala 7-punti (1=Molto facile, 7=Molto difficile)
  - Predictor più forte di retention rispetto a CSAT/NPS
  - Applicare post-transazione (acquisto, support resolution)

- **SERVQUAL Gap Model**: Measured Service Quality = Σ(Perceived − Expected) per 5 dimensioni
  - Gap 1: Customer Expectations vs Management Perception
  - Gap 2: Management Perception vs Service Quality Specifications
  - Gap 3: Specifications vs Delivery
  - Gap 4: Delivery vs External Communication
  - Gap 5: Expected vs Perceived (= CX Gap)

### Customer Lifetime Value & Retention

- **CLV** ≈ (ARPU × Gross Margin %) / (Churn Rate / 12) 
  - o più preciso: CLV = Σ[(Revenue_t × Gross Margin %) / (1 + Discount_rate)^t] − CAC

- **Churn Rate** = (Clienti persi in periodo) / (Clienti inizio periodo) × 100

- **Retention Rate** = 1 − Churn Rate

- **NRR (Net Revenue Retention, SaaS)** = [(MRR inizio + Espansione − Downgrade − Churn) / MRR inizio] × 100
  - Healthy target: > 110% (compounding growth)

- **GRR (Gross Revenue Retention, SaaS)** = [(MRR inizio − Downgrade − Churn) / MRR inizio] × 100
  - Baseline without new customer acquisition

### Loyalty Program Economics

- **Member vs Non-Member Spend Uplift**: 15-30% tipico
- **Top Tier CLV Lift**: 30-50% vs base tier
- **Redemption Rate**: Target 25-40% (equilibrio fra member value perception e program margin)
- **Breakage Rate**: 15-25% tipico (points expiring, never redeemed)
- **Active Rate**: % active members engaging in earning/redemption (target > 50% annuale)
- **Tier Migration**: % members moving up/down (indicate program health, tier attainability)

### Churn Prediction Model Metrics

- **Precision** = TP / (TP + FP) → minimize false positives (wasted save offers)
- **Recall** = TP / (TP + FN) → minimize missed churners (revenue loss)
- **F1** = 2 × (Precision × Recall) / (Precision + Recall) → balanced trade-off
- **AUC-ROC**: Target > 0.8 (0.5 = random, 1.0 = perfect)
- **Lift Chart**: Compare model deciles vs random baseline (target: top 20% decile has 3-5x baseline churn rate)

---

## Cross-Skill References

- **marketing-analytics**: Predictive churn modeling, CLV analysis, RFM segmentation, attribution modeling
- **digital-marketing-performance**: Campaign execution, A/B testing retention campaigns, email automation, programmatic advertising
- **marketing-strategico**: Segmentation strategy, brand positioning, pricing strategy, competitive analysis
- **programmazione-controllo**: KPI definition, financial forecasting (CLV, CAC), ROI measurement

---

## Industry Variations

### E-Commerce / Retail
- Journey: Browse → Add to Cart → Checkout → Post-Purchase → Repeat
- Key metrics: Conversion rate, AOV (Average Order Value), repeat purchase rate, return frequency
- Loyalty mechanics: Points per € spent, free shipping tiers, exclusive product access
- Churn signals: Last purchase date decay, browse frequency drop, email unsubscribe

### SaaS
- Journey: Freemium/Trial → Activation → Growth → Mature → Renewal
- Key metrics: CAC payback period, NRR/GRR, expansion revenue, net dollar retention
- Churn drivers: Feature underutilization, competitive switching, insufficient support, pricing sensitivity
- Retention tactics: In-app guidance, onboarding series, usage-based upsell, success manager engagement

### B2B / Enterprise
- Journey: Awareness → Evaluation → Negotiation → Implementation → Expansion → Renewal
- Key personas: Economic buyer, user buyer, influencer, coach
- Sales cycle: 6-18 months, multi-stakeholder approvals
- Churn prevention: Executive sponsorship, business review cadence, health score monitoring

### Hospitality / Subscription Services
- Journey: Awareness → Booking/Signup → First Experience → Repeat → Membership Upgrade
- Loyalty focus: Status tiers, experiential benefits, community/exclusivity
- Churn signals: Usage decline, service complaint, lack of engagement, competitor trial

---

**Ultimo aggiornamento**: Aprile 2026  
**Target audience**: Marketing professionals, product managers, CX leaders (Bocconi BEMACS background)
