# Churn Prediction, Retention & Win-Back Strategy

## Churn Prediction Workflow

### Step 1: Data Assembly

**Objective**: Assemble diverse data sources into a single **prediction dataset** with one row per customer and columns for features + churn label.

#### RFM (Recency, Frequency, Monetary)
- **Recency (R)**: Days since last purchase (0-365)
  - Interpretation: R=1 = active yesterday; R=180 = inactive 6 months
  - Churn signal: R > 90 days typically indicates risk
- **Frequency (F)**: Number of purchases in last 12 months (0-100+)
  - Interpretation: F=1 = one-time buyer; F=24 = weekly buyer
  - Churn signal: F=1 is highest risk; F declining month-over-month = churn risk
- **Monetary (M)**: Total value (€) spent in last 12 months (0-100,000+)
  - Interpretation: Higher M = higher CLV = bigger loss if churned
  - Churn signal: M declining despite F stable = category shift or lower-margin purchases

**RFM Segmentation Example**:
```
RFM Score = (Recency quartile) + (Frequency quartile) + (Monetary quartile)
Score ranges 3-15, higher = more valuable

Quintiles:
111 = At-risk (low R, F, M)
555 = Champions (high R, F, M)
311 = New customers (low R, medium F, high M) - monitor!
531 = Loyal (high R, high F, low M) - retain on margins
```

#### Engagement Metrics
- **Email engagement**: Opens in last 30 days, clicks in last 30 days, unsubscribe rate trend
- **Website activity**: Sessions in last 30 days, pages visited, time-on-site trend
- **App activity** (if applicable): Daily active users, session duration, feature adoption
- **Support tickets**: Number opened, resolution satisfaction, complaint sentiment
- **Social engagement**: Follows, comments, mentions trend

#### Transaction Data
- **Product affinity**: Top categories purchased, product diversity (SKU count)
- **Pricing sensitivity**: % of purchases at full price vs discount, promo code usage frequency
- **Return rate**: % of orders returned, reason codes (quality issue, wrong item, changed mind)
- **Payment method**: Credit card, debit, PayPal, etc. (failed payments = churn risk)

#### Demographic & Contextual
- **Customer tenure**: Months since first purchase (0-240+)
  - Signal: Customers in months 6-12 have highest churn risk (post-purchase honeymoon ends)
- **Cohort**: Acquisition month/year (controls for seasonality and acquisition quality)
- **Region**: Geographic location (some regions have higher churn due to competitors, logistics)
- **Loyalty program status**: Enrolled member vs non-member (members typically 20-40% lower churn)
- **Customer service interactions**: Complaints filed, support quality score, resolution time

#### Lifecycle Stage Context
- **Onboarding completion**: User completed onboarding checklist (SaaS key signal)
- **Feature adoption**: Activated 5+ features of 15 available (SaaS/product)
- **Usage depth**: Weekly active user vs monthly vs quarterly (engagement pattern)
- **Renewal approaching**: Days until contract renewal (short window to intervene)

### Step 2: Feature Engineering

**Objective**: Transform raw data into predictive features that capture churn signals.

#### Lag Variables (Time-series patterns)
```
30-day lookback:
  - Spend_30d: Total spent in last 30 days
  - Purchases_30d: Transaction count
  - Opens_30d: Email opens
  
60-day lookback:
  - Spend_60d: Total spent
  - Frequency_60d: Purchase count
  
90-day lookback (long-term trend):
  - Spend_90d: Total spent
```

#### Trend Indicators (Month-over-month change)
```
Spend trend:
  - MoM_spend_change = (Spend_30d - Spend_60d) / Spend_60d
  - Signal: If -50%, customer spending declining (churn risk)

Purchase frequency trend:
  - MoM_freq_change = (Purchases_30d - Purchases_60d) / Purchases_60d
  - Signal: If declining, engagement dropping
```

#### Aggregations (Composite signals)
```
Engagement score (0-100):
  - Email_weight (0.3) + Website_weight (0.3) + Support_weight (0.2) + Loyalty_weight (0.2)

Spend volatility:
  - Standard deviation of monthly spend (high volatility = unpredictable, lower lifetime value)

Diversification:
  - Count of unique product categories (low = single-category risk, higher churn)
```

#### Seasonality Adjustments
```
Retail example:
- November-December spend typically 3x higher (holiday season)
- January-February typically 50% lower
- Adjust expected spending by month to detect true anomalies:
  - If customer should spend €500 in December but only €100 = red flag
```

#### Example Engineered Feature Set
```
Customer ID | R | F | M | Spend_30d | Spend_trend | Opens_30d | Purchase_diversity | 
            | Tenure_months | Churn_label | Pred_prob
    123456  | 45| 6 |€1200| €150    | -20%       | 5        | 4 categories | 
            | 24          | 0 (no churn) | 0.15
    
    234567  | 120|1 |€50 | €0     | -100%      | 0        | 1 category   | 
            | 8           | 1 (churned)  | 0.92
```

---

### Step 3: Model Selection & Training

#### Baseline: Logistic Regression
- **Pros**: Interpretable coefficients (which features matter most?), fast training, low false positive rate
- **Cons**: Assumes linear relationships (doesn't capture interactions well)
- **Use case**: When interpretability is critical (regulatory, business explanation)

**Sample coefficients** (direction of churn risk):
```
Recency (+0.8):      Each 30 days of inactivity → 80% higher churn risk
Frequency (-0.5):    Each additional purchase → 50% lower churn risk
Monetary (-0.3):     Each €100 higher spend → 30% lower churn risk
Engagement (-0.6):   Each additional email open → 60% lower churn risk
Tenure (-0.2):       Each additional month as customer → 20% lower churn risk
```

#### Advanced: Random Forest
- **Pros**: Captures non-linear patterns, feature interactions, robust to outliers
- **Cons**: Harder to interpret ("why did it predict churn?"), prone to overfitting
- **Use case**: When accuracy is paramount and dataset size is large (10K+ customers)

**Feature importance example**:
```
1. Recency (35%) - most predictive
2. Spend trend (-20% change) (25%)
3. Engagement score (20%)
4. Tenure (15%)
5. Category diversity (5%)
```

#### Advanced: XGBoost / Gradient Boosting
- **Pros**: Highest predictive accuracy, handles imbalanced classes well (churn is typically 5-10% of population)
- **Cons**: Computationally intensive, slow inference at scale
- **Use case**: High-stakes retention (B2B enterprise accounts where churn = €1M+ impact)

#### Deep Learning (Neural Networks)
- **Pros**: Can model very complex temporal patterns (e.g., customer who goes quiet for 3 months then surges = low churn; vs. customer with steady decline = high churn)
- **Cons**: Requires large data (100K+ customers), long training time, black-box
- **Use case**: Massive e-commerce/subscription platforms with 1M+ customers

### Step 4: Model Evaluation

#### Train-Test Split
```
80% training (optimize model) : 20% test (evaluate real-world performance)
Temporal split (recommended): 
  - Train on data from months 1-10
  - Test on month 11-12 (simulates real-world forward prediction)
```

#### Key Metrics

**Precision** (False Positive Rate)
- Definition: Of customers predicted to churn, how many actually churn?
- Formula: TP / (TP + FP)
- Why it matters: If precision is 40%, you waste 60% of retention budget on false positives
- Target: > 50% (at least half of targeted customers actually churn without intervention)

**Recall** (True Positive Rate)
- Definition: Of customers who actually churn, how many did you identify?
- Formula: TP / (TP + FN)
- Why it matters: If recall is 30%, you miss 70% of churners
- Target: > 70% (catch most of the at-risk customers)

**F1 Score**
- Definition: Harmonic mean of precision and recall
- Formula: 2 × (Precision × Recall) / (Precision + Recall)
- Use case: When you want balanced precision-recall trade-off

**AUC-ROC (Area Under the Receiver Operating Characteristic Curve)**
- Definition: Probability the model ranks a random churner higher than a random non-churner
- Range: 0.5 (random) to 1.0 (perfect)
- Target: > 0.80
- Example: AUC=0.85 means 85% of the time, the model correctly ranks a churner as higher-risk than a non-churner

**Lift Chart**
- Definition: Compare model deciles vs random baseline
- Example:
```
Decile 1 (top 10% highest churn risk): 25% actual churn rate (5x baseline 5%)
Decile 2: 18% actual churn rate (3.6x baseline)
Decile 3: 12% actual churn rate (2.4x baseline)
Decile 10 (lowest 10% risk): 2% actual churn rate (0.4x baseline)
```
- Interpretation: By targeting top 20% deciles, you capture 43% of total churners while contacting only 20% of population → 2.15x efficient

**Confusion Matrix**
```
                Predicted Churn    Predicted Retain
Actual Churn         TP (50)           FN (30)
Actual Retain        FP (100)          TN (820)

Precision = 50 / (50 + 100) = 33% (ouch, lots of false positives)
Recall = 50 / (50 + 30) = 63%
F1 = 43%
```

### Step 5: Calibration Check

**Objective**: Ensure predicted churn probability matches actual churn rate

**Example**:
```
Customers with predicted churn probability 0.7 should actually churn ~70% of the time

If they actually churn 40%, the model is miscalibrated (overstating risk)
→ Action: Use isotonic regression to recalibrate predictions

If they actually churn 90%, the model is underestimating (understating risk)
→ Action: Retrain on recent data (distribution may have shifted)
```

---

## Churn Drivers Taxonomy

### Usage Decline
- **Signal**: Recency increasing, engagement frequency decreasing
- **Root cause**: Feature underutilization (for SaaS), product fatigue, alternative solutions found
- **Intervention**: Usage-based email ("Here's a feature you haven't tried yet"), educational webinar, in-app prompts

### Competitive Switching
- **Signal**: Customer mentions competitor in support ticket, customer browses competitor website (intent data if available)
- **Root cause**: Competitor offering better value, lower price, more features
- **Intervention**: Competitive counter-offer (price match, feature unlock), customer loyalty incentive

### Service Failure
- **Signal**: Customer submitted complaint ticket, low support satisfaction score, refund request
- **Root cause**: Product quality issue, poor customer service, unmet expectations
- **Intervention**: Root cause analysis (RCA) with customer, service recovery (replacement, discount, refund), proactive follow-up

### Price Sensitivity
- **Signal**: Customer pauses subscription, downgrades to lower tier, primarily purchases discounted items
- **Root cause**: Budget constraint, ROI not justified, market price reduction elsewhere
- **Intervention**: Flexible payment plan (monthly vs annual discount), value demonstration (business case), budget-friendly tier

### Natural Lifecycle
- **Signal**: New customer with no engagement from day 1, very short tenure (< 3 months)
- **Root cause**: Wrong product-market fit, impulse purchase, customer use-case doesn't align with product capability
- **Intervention**: Early-stage intervention (onboarding, feature tour), qualify fit at signup

---

## Early Warning System (Traffic Light Indicators)

**Objective**: Daily/weekly automated flags for accounts exceeding churn risk threshold

### Green (Low Risk, Monitor)
- Spend trend: Neutral or positive
- Engagement: Active in last 7 days
- Recency: < 30 days since purchase
- Tenure: > 12 months
- Support satisfaction: > 4/5
- Recommended action: Standard nurture email, no intervention

### Yellow (Elevated Risk, Engage)
- Spend trend: Declining 20-50% MoM
- Engagement: Active in last 30 days but declining from prior 90 days
- Recency: 30-60 days
- Tenure: 6-12 months
- Support satisfaction: 2-3/5
- Recommended action: Targeted re-engagement email, feature unlock offer, success manager outreach

### Red (High Risk, Urgent)
- Spend trend: Declining > 50% MoM or €0 for 60+ days
- Engagement: Inactive > 60 days
- Recency: > 90 days
- Support tickets: Recent complaint with unresolved issue
- Tenure: Early-stage (3-6 months)
- Recommended action: Immediate phone call, save offer (discount/service upgrade/tier promotion), win-back campaign kickoff

### Traffic Light Dashboard Example
```
High Risk (Red) Accounts This Month:
ID    | Customer Name      | Risk Score | Spend Trend | Last Activity | Churn Probability | Action
1001  | Acme Corp          | 92         | -65%        | 87d ago       | 0.91              | Phone outreach + save offer
1002  | Beta Solutions     | 88         | -40%        | 45d ago       | 0.87              | Re-engagement email + feature unlock
1003  | Creative Studios   | 85         | -35%        | 52d ago       | 0.81              | CSM check-in call

Yellow Risk (Medium) Accounts:
2001  | Delta Tech         | 72         | -25%        | 35d ago       | 0.68              | Engagement email campaign
2002  | Epsilon Design     | 68         | -15%        | 42d ago       | 0.62              | Loyalty program promotion

Total Red: 47 accounts (0.3% of base)
Total Yellow: 342 accounts (2.1% of base)
Total Green: 15,611 accounts (97.6% of base)
```

---

## Intervention Strategies

### Tiered Approach by Segment

#### Segment 1: High-Value At-Risk (Red tier, CLV > €10,000)
**Goal**: Prevent loss of high-lifetime-value customers

- **Intervention**: Personal outreach (dedicated account manager phone call within 24 hours)
- **Offer**: Custom save offer based on churn reason
  - Usage decline → Feature training, advanced feature unlock
  - Price sensitivity → Volume discount, annual payment incentive
  - Service failure → Root cause resolution, service recovery credit (€500-5,000), proactive monitoring
- **Follow-up**: Weekly check-in for 30 days post-intervention
- **Success rate**: 40-60% retention (high-touch personalized approach)

#### Segment 2: Medium-Value At-Risk (Yellow tier, CLV €1,000-10,000)
**Goal**: Re-engage via targeted campaigns

- **Intervention**: Automated email campaigns + CS manager awareness (but not necessarily direct phone)
- **Campaign sequence**:
  - Day 0: "We miss you" email (highlight 3 relevant use cases)
  - Day 3: Special offer email (10-15% discount or free upgrade)
  - Day 7: Content email (webinar, industry report, case study)
  - Day 14: Final save offer (deeper discount, VIP status trial)
- **Success rate**: 15-25% retention (lower touch, higher volume)

#### Segment 3: New/Low-Value At-Risk (Red tier, CLV < €1,000, tenure < 6 months)
**Goal**: Qualify or gracefully off-board

- **Intervention**: Engagement surveys + guided product tours
  - "What prevented you from using [feature]?"
  - "What would help you succeed?"
- **Offer**: Free trial extension, feature unlock, or onboarding session
- **Accept churn**: If customer is poor fit, document as graceful churn
- **Success rate**: 10-20% retention (may not be right customer)

### Save Offer Mechanics

**Structure of a save offer**:
```
Subject: "Here's what we can do for you, [Name]"

Hi [Name],

We've noticed your account activity has slowed recently. 
Before you go, we want to make this right.

SPECIAL SAVE OFFER (Valid 7 days):
├── 20% discount on annual plan (€500/year → €400/year)
├── 1-hour personalized onboarding call with our success team
├── Priority support tier (upgrade to Premium support)
└── 30-day money-back guarantee

Why you loved us before:
- You created 5 campaigns that generated €50K in revenue
- You achieved 35% email open rate (5% above industry average)

What might help:
- Are you time-constrained? (Time management tips)
- Looking for specific features? (Roadmap + early access)
- Budget concerns? (Payment plan options)

Let's jump on a call: [Calendar link]

[CTA Button: "Claim My Offer"]
```

**Offer mechanics**:
- **Discount depth**: 10-25% typical (deeper for high-value customers)
- **Validity window**: 7-30 days (creates urgency)
- **Add extra value**: Not just discount (training, support upgrade, feature unlock)
- **Personalization**: Reference specific accomplishments ("You created 5 campaigns")

---

## Win-Back Framework

### Win-Back Strategy Overview

**Objective**: Reactivate customers who have already churned (not just at-risk, but already gone)

**Timing windows**:
- **30-day window** (highest success, ~20% reactivation rate)
- **60-day window** (medium success, ~10% reactivation rate)
- **90-day window** (lower success, ~5% reactivation rate)
- **180-day window** (very low success, ~2% reactivation rate, cost-prohibitive unless CLV high)

### Win-Back Campaign Sequence

#### Phase 1: Immediate Win-Back (Days 1-14 post-churn)

**Day 1: Pause Notification**
```
Subject: "We noticed you cancelled your subscription"

Hi [Name],

We've processed your cancellation request.

Before you fully disconnect, here's what you'll lose:
- €200 in stored credits (expires in 30 days)
- Your custom workflows (will be deleted in 60 days)
- Access to customer data export (available now, disappears at day 60)

If you change your mind: [Reactivate button] (gets you back within seconds)

Questions? Reply to this email or call us at [number]
```
**Purpose**: Highlight switching costs; reduce cancellation follow-through

**Day 3: Value Recapitulation**
```
Subject: "Here's what [Name] accomplished with us"

In your 18 months with us, you:
✓ Created 47 campaigns
✓ Achieved €250K in attributed revenue
✓ Improved email open rate from 18% to 35%

Our team is ready to help you beat your targets next year.

Special reactivation offer: 30% off for 3 months [CTA]
```
**Purpose**: Remind of past success; activate emotional connection

**Day 7: Competitive Displacement Check**
```
Subject: "Moving to [Competitor]? Consider this..."

If you're switching to [Competitor X]:
- We'll match their pricing on annual plan
- We have [Specific advantage] they lack
- 90-day free trial if you come back

Or, if it's a budget issue:
- Monthly plan at 50% off
- Quarterly billing (no long-term commitment)

Let's chat: [Calendar]
```
**Purpose**: Identify real reason for churn; offer targeted solution

**Day 14: Final Save Offer**
```
Subject: "Last chance: 50% off + free consultation"

We want you back. Here's our final offer (expires in 48 hours):

✓ 50% discount on any plan (first 3 months)
✓ 90-minute business strategy session with our VP of Success
✓ 6 months of priority support
✓ 30-day money-back guarantee (no questions asked)

This is a true "win-back" offer, only available to past customers like you.

Claim it now: [CTA]
```
**Purpose**: Create urgency; final intervention before moving to phase 2

---

#### Phase 2: Sustained Win-Back (Days 15-60 post-churn)

**Weekly check-in emails**:
```
Subject: "[Name], your €200 credit expires in X days"

Your account has €200 in unused credits (expires on [date]).

No commitment needed—just login and explore. Your data is still there.

[Reactivate Button]
```

**Soft re-engagement content**:
- Blog articles on trends in [customer's industry]
- Case studies from similar companies
- Product updates (new features since they left)
- Community highlights (what other customers are achieving)

**Goal**: Low-pressure re-introduction without aggressive selling

---

#### Phase 3: Long-Term Win-Back (Days 61-180)

**Less frequent but still targeted**:
- Monthly industry insights email
- Quarterly re-engagement offer (lower discount: 20% off vs 50% off)
- VIP reactivation event (annual customer summit, invite past customers)

**Cost-benefit analysis**: Only pursue if CLV > €10,000 (phone outreach) or CLV > €1,000 (email campaigns)

---

### Win-Back Economics

**Scenario: SaaS with €100/month product, €50K annual recurring revenue (ARR)**

```
BASELINE (No win-back program):
Monthly churn: 50 customers × €100 = €5,000 ARR loss
Annual churn cost: €60,000

WIN-BACK PROGRAM INVESTMENT:
Win-back campaign cost per customer: €50 (email sequence, call time)
Win-back success rate: 15% (7.5 of 50 churned customers reactivate)
Reactivation revenue: 7.5 × €100 × 12 months = €9,000 annual ARR

ROI:
Cost: 50 × €50 = €2,500/month program cost
Benefit: 7.5 × €100 × 12 = €9,000 annual incremental ARR
Monthly benefit: €750

Net benefit (Year 1): (€9,000 - €2,500) = €6,500 (but spread across 12 months)
Payback period: €2,500 ÷ (€9,000 ÷ 12) = ~3.3 months ✓ Profitable
```

---

## A/B Testing Retention Campaigns

**Test framework**:

```
Variable: Email subject line
Control: "We miss you"
Variant A: "Here's what you're missing"
Variant B: "Your credits expire soon"

Sample size: 1,000 customers (split 333 each)
Duration: 7 days

Results:
Control:    142 opens, 8 clicks, 1 conversion (0.3% conversion)
Variant A:  168 opens, 12 clicks, 2 conversions (0.6% conversion) [2x lift]
Variant B:  154 opens, 14 clicks, 3 conversions (0.9% conversion) [3x lift] ← WINNER

Recommendation: Deploy Variant B to remaining at-risk base of 10,000 customers
Projected lift: 10,000 × 0.9% = 90 reactivations vs 30 for control = 60 additional customers saved
Revenue impact: 60 × €100 × 12 months = €72,000 annual ARR
```

---

## Voluntary vs Involuntary Churn

### Involuntary Churn (Payment Failures)
**Definition**: Customer wants to stay but payment method fails (card expired, insufficient funds, 3D Secure block)

**Rate**: Typically 5-10% of total churn (often highest in months 1-3 post-signup)

**Prevention**:
- Pre-expiration card update reminders (email 60 days before card expiration)
- Soft decline handling (don't cancel immediately; retry over 30 days with escalating notifications)
- Payment method diversification (allow 2-3 backup cards)
- Dunning logic:
```
Day 1: Soft decline → Retry next day
Day 2: Payment failure → Send SMS/email "Update your payment"
Day 5: Another retry → Email "Your account is suspended"
Day 10: Final notice → "Account will be deleted in 5 days"
Day 15: Cancellation
```

**Expected recovery**: 40-60% of customers update payment method if nudged properly (vs 0% if auto-cancelled)

### Voluntary Churn
**Definition**: Customer actively chooses to cancel

**Strategies**:
- Cancellation confirmation survey ("Why are you leaving?") → informs strategy
- Pause subscription (7-30 days free) vs immediate cancellation (recovers 10-20%)
- Discount offer at cancellation page (10-15% recover)

---

## SaaS-Specific Metrics

### Net Revenue Retention (NRR)
**Formula**: (MRR_start + Expansion - Downgrades - Churn) / MRR_start × 100

**Example**:
```
Month 1:
- Starting MRR: €100,000 (100 accounts × €1,000)
- New expansion (upsells): €5,000 (5 accounts upgraded to higher tier)
- Downgrades: -€2,000 (2 accounts downgraded)
- Churn: -€8,000 (4 accounts cancelled)
- Ending MRR: €95,000

NRR = (€95,000 + €5,000 - €2,000 - €8,000) / €100,000 = 0.90 or 90%
```

**Interpretation**:
- NRR < 100% = losing money from existing customers (negative compounding)
- NRR = 100-110% = flat (churn offset by expansion)
- NRR > 110% = healthy growth (expansion outpaces churn) ← Target

### Gross Revenue Retention (GRR)
**Formula**: (MRR_start - Downgrades - Churn) / MRR_start × 100

**Example**:
```
GRR = (€100,000 - €2,000 - €8,000) / €100,000 = 0.90 or 90%
(Note: GRR excludes expansion; NRR includes it)
```

**Use case**: GRR measures core product stickiness (before upsell); NRR measures overall business health

---

## Churn Prediction Checklist

- [ ] **Data assembled**: RFM + engagement + transaction + demographic + contextual data ready
- [ ] **Features engineered**: Lag variables, trends, aggregations, seasonality adjustments created
- [ ] **Model selected**: Chosen appropriate model (logistic regression for interpretability, XGBoost for accuracy, etc.)
- [ ] **Training-test split**: Temporal split implemented (train on months 1-10, test on months 11-12)
- [ ] **Model evaluated**: Precision > 50%, Recall > 70%, AUC > 0.8 achieved
- [ ] **Calibration checked**: Predicted probabilities match actual churn rates
- [ ] **Early warning system deployed**: Traffic light indicators (green/yellow/red) configured
- [ ] **Intervention playbooks created**: Save offers, re-engagement sequences drafted per segment
- [ ] **Win-back sequence designed**: Post-churn emails (day 1, 3, 7, 14) prepared
- [ ] **A/B test framework**: Variables to test identified (subject line, offer, timing)
- [ ] **Monitoring dashboards**: Daily churn risk count, weekly conversion rate by segment, monthly NRR tracked
- [ ] **Team training**: Sales/CS trained on intervention tactics, success metrics, escalation procedures

---

**Key Takeaway**: Predictive churn models reduce involuntary churn by 20-30% and voluntary churn by 10-25% through early identification and timely, personalized intervention. Expected ROI: 200-400% if executed systematically.
