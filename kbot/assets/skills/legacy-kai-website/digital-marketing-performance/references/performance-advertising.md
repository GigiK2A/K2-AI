# Performance Advertising: Google Ads, Meta, TikTok, LinkedIn & Programmatic

## Parte 1: Google Ads - Campaign Types & Structure

### Google Ads Campaign Ecosystem

| Tipo Campaign | Best For | Avg CPC | Reach | Setup Difficulty |
|---|---|---|---|---|
| **Search Ads** | Keywords, intent-driven | €0.50-€5.00 | 50-70M searches/mese (US) | Basso |
| **Display Network** | Brand awareness, retargeting | €0.10-€0.50 | 2M sites, 90% internet users | Basso |
| **Shopping Ads** | E-commerce, product catalog | €0.30-€2.00 | Product keywords only | Medio |
| **Performance Max** | Revenue maximization, ML-driven | Varia | Display + Search + YouTube + Maps | Medio-Alto |
| **YouTube Ads** | Video awareness, brand lift | €0.10-€3.00 | 2B monthly users | Basso |
| **App Campaigns** | App installs, user acquisition | €0.50-€10.00 | Varia per audience | Medio |

### Search Ads Deep Dive

**Account Structure (Best Practice):**

```
Account
├── Search Campaign 1: "Brand Keywords"
│   ├── Ad Group: "Brand Exact"
│   │   └── Keyword: [brand], [brand name], [brand abbreviation]
│   │   └── Ad Copy A: "Official Brand - Shop Now"
│   │   └── Ad Copy B: "Brand + 20% Discount"
│   └── Ad Group: "Brand Phrase"
│       └── Keyword: "brand" (phrase match)
│
├── Search Campaign 2: "High-Intent Non-Brand"
│   ├── Ad Group: "Product Keyword 1"
│   │   └── Keyword: "digital marketing course", "learn digital marketing"
│   │   └── Ad Copy: Focus on course quality, price, certification
│   └── Ad Group: "Product Keyword 2"
│       └── Keyword: "SEO training Roma", "SEM course"
│
└── Search Campaign 3: "Competitor Keywords"
    └── Ad Group: "Competitors"
        └── Keyword: "competitor brand", "ahrefs alternative"
        └── Ad Copy: Direct comparison, USP emphasis
```

**Search Campaign Settings:**

| Setting | Best Practice | Notes |
|---------|---|---|
| **Bidding strategy** | Manual CPC (starting) → tCPA/tROAS (scale) | Automatic bidding needs 30-50 conversions |
| **Daily budget** | €20-50 minimum (Search) | Higher = better data, more clicks |
| **Ad rotation** | Rotate evenly (testing) → Optimize for conversions (after 100+ conv) | Rotate = fair A/B test, Optimize = best performer |
| **Ad schedule** | All hours initially, optimize after 2 weeks | Pause low-performing hours (e.g., 2-5am) |
| **Geo-targeting** | City/region if local, national if nationwide | Local businesses = zip code/city radius |
| **Device bidding** | Monitor desktop vs. mobile performance | Often mobile CTR higher but lower CPA (volume play) |

---

### Display Network Ads

**Use Case:** Remarketing, brand awareness, low-intent audience

**Key Metrics:**

| Metrica | Target | Interpretation |
|---------|--------|---|
| **CTR** | 0.5-2% (molto basso) | Low-intent, awareness drive |
| **CPC** | €0.10-€0.50 | Cost-efficient |
| **CPM (1000 impressions)** | €5-€20 | Pay per impression, not click |
| **CPA** | Varia, rely su ROAS | Measure conversion, not CTR |

**Display Campaign Structure:**

```
Display Campaign: "Remarketing - Product Viewers"
├── Ad Group: "Product Page Viewers"
│   ├── Audience: Remarketing list (visited product page)
│   ├── Display Ad (responsive): 
│   │   - Headline 1: "Back to [Product Name]"
│   │   - Headline 2: "Still thinking? Get 15% off"
│   │   - Description: "Limited time offer. Complete your purchase today."
│   │   - Images: Product image, hero, benefit
│   └── CPM bid: €8/1000 impressions
│
└── Ad Group: "Cart Abandoners"
    └── Audience: Remarketing list (cart abandoned)
    └── Display Ad: "Complete your order - Free shipping"
    └── CPM bid: €12/1000 impressions (higher bid for hot audience)
```

---

### Shopping Ads (E-Commerce)

**Requirement:** Merchant Center product feed (Datasheet con product name, price, image, URL)

**Structure:**

```
Shopping Campaign: "All Products"
├── Ad Group: "All Products" (implied by Merchant Center)
│   ├── Product feed: 100,000 products
│   └── Products appear as carousel in SERP

Esempio SERP:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Shopping Ads Carousel]
[Product A] €25  ⭐⭐⭐ (50 reviews)
[Product B] €19  ⭐⭐⭐⭐ (120 reviews)
[Product C] €30  ⭐⭐⭐⭐⭐ (220 reviews)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Shopping Campaign Settings:**

- Merchant Center linked
- Product feed updated daily
- Bid strategy: Maximize Conversion Value (tROAS best for e-commerce)
- Negative keywords: "cheap", "discount site", "clone" (filter low-intent)

**Benchmark Shopping Ads (E-Commerce):**

| Metrica | Benchmark |
|---------|---|
| CTR | 1-3% (product feed quality dependent) |
| CPC | €0.30-€2.00 |
| ROAS | 3-5x (e-commerce standard) |
| Conversion Rate | 2-5% (product quality + UX) |

---

### Performance Max Campaigns

**Definition:** AI-driven, Google optimizes across channels (Search, Display, YouTube, Shopping, Gmail, Maps)

**Best For:** Revenue maximization when conversion data sufficient (100+ monthly conversions)

**Setup:**

```
Performance Max Campaign:
├── Campaign goal: Revenue (define value per conversion)
├── Conversion tracking: Pixel + API setup
├── Audience (optional): 
│   ├── Remarketing list (converters, product viewers)
│   ├── In-market audience (high-intent searchers)
│   └── Custom audience (lookalike of best customers)
├── Assets (Google auto-generates combinations):
│   ├── Headlines: 3-5 text variations
│   ├── Descriptions: 2-3 variations
│   ├── Images: 3-5 product/lifestyle images
│   ├── Logo: Brand logo for consistency
│   └── Videos: Optional, 15-30 sec
├── Bidding: tROAS (target 3-5x for e-commerce)
└── Daily budget: €50+ (needs volume for ML to optimize)
```

**Performance Max Advantages:**
- Automatic audience optimization
- Cross-channel optimization (Google balances where ROI best)
- Simplified campaign management (1 campaign vs 5 separate)

**Benchmark Performance Max:**
- Learning phase: 2-3 weeks (avoid changing too much)
- Stabilization: 4+ weeks to see full performance

---

## Parte 2: Meta Ads (Facebook, Instagram)

### Meta Ads Campaign Structure

**Hierarchy:**
```
Campaign (objective: Awareness, Consideration, Conversion)
├── Ad Set 1 (audience targeting, budget, schedule)
│   ├── Ad 1a (copy, image, CTA)
│   └── Ad 1b (copy, video, CTA)
└── Ad Set 2 (different audience)
    ├── Ad 2a
    └── Ad 2b
```

### Campaign Objectives & KPIs

| Objective | Goal | Best KPI | Avg Cost | Use Case |
|-----------|------|----------|----------|----------|
| **Awareness** | Impressions, reach | Cost per thousand impressions (CPM) | €3-€10 CPM | Brand awareness, video views |
| **Consideration** | Landing page views, content engagement | Cost per engagement (CPE) | €0.50-€3 | Demo signups, whitepaper download |
| **Conversions** | Sales, leads, app installs | Cost per conversion (CPA) | €5-€50 | Purchase, form submit, app install |
| **Catalog Sales** | E-commerce products | Return on ad spend (ROAS) | €0.50-€3 CPC | Direct product sales |

### Audience Types & Targeting

| Audience Type | Reach | Precision | Best For | Setup |
|---|---|---|---|---|
| **Core Audience** | 1M-10M | High | Specific interests + demographics | Age, interests (e.g., "Digital Marketing", "Entrepreneurs") |
| **Custom Audience** | 100K-5M | Highest | Existing customers, email list | Upload email list (hashed), pixel-tracked users |
| **Lookalike Audience** | 1M-10M | High | Find new customers like best ones | Create from custom audience (1% look-alike = most similar) |
| **Broad Audience** | 100M+ | Low | Testing, awareness | Demographics only (age, gender, location) |

**Audience Targeting Example (B2B SaaS):**

```
Core Audience:
- Age: 25-55
- Location: Italy
- Interests: "B2B Marketing", "Marketing Technology", "Business Software"
- Behaviors: "Business decision makers", "Page visitors (last 180 days)"
- Exclusion: Existing customers (custom audience)

Expected Reach: ~2M people
Estimated CPM (daily budget €20): €8-12
Daily reach: ~2,000-2,500 impressions
```

### Creative Strategy (Ad Copy + Visual)

**Ad Copy Framework:**

```
AWARENESS:
Hook (first 3 words): "Stop wasting money on..."
Curiosity: "Here's the secret most agencies won't tell you"
Proof: "10,000+ companies increased ROI by 40%"
CTA: "Learn the strategy" → link

CONSIDERATION:
Problem: "Struggling with low conversion rates?"
Solution: "Our proven framework converts 3x more"
Social proof: "97% of clients see results in 30 days"
CTA: "Get free strategy call" → form

CONVERSION:
Urgency: "Only 5 spots left for this month"
Benefit: "Save €2000/month on ad spend"
Proof: "€8,000 average first month ROI"
CTA: "Get started" → purchase page
```

**Visual Creative Specs:**

| Format | Dimensions | File Size | Best Practices |
|--------|---|---|---|
| **Single Image** | 1200×628px | <4MB | 20% text rule (no >20% text overlay), high contrast |
| **Video** | 1:1 (square), 16:9, 9:16 | <4GB | First 3 seconds critical (stop scroll), captions, loop |
| **Carousel** | 1200×628px per card | <4MB | 3-5 cards, each tell part of story |
| **Reels (15-90s)** | 1:1 to 9:16 | <4GB | Trending audio, quick cuts, entertainment-first |

**Meta Creative Performance:**

```
New ad creative lifespan:
Week 1: High CTR, good impression (novelty)
Week 2-3: CTR decline (audience saturation)
Week 4+: Ad fatigue (CPM up 30-50%, CTR down)

Strategy:
- Test 3-5 new creatives weekly
- Pause performers <0.5% CTR (or <target ROAS)
- Refresh top performers every 3-4 weeks
- Save winning creatives for future campaigns
```

---

## Parte 3: TikTok Ads

### TikTok Ads Ecosystem

**Key Advantage:** Native, in-feed ads (blend with organic content)

**Campaign Types:**

| Tipo | Objective | Best For | CPM | Minimum Budget |
|------|-----------|----------|-----|---|
| **Awareness** | Video views | Brand awareness, virality | €1-€5 | €100 |
| **Traffic** | Website clicks | E-commerce, landing page | €0.50-€3 | €100 |
| **Conversions** | Purchase, form submit | Direct sales | €2-€10 | €100 |
| **App Installs** | Mobile app download | User acquisition | €2-€8 | €100 |

### TikTok Creative Best Practices

```
Winning TikTok Ad Formula:
1. First 3 frames (CRITICAL): Hook attention (unexpected visual, text, sound)
2. Audio: Trending sound >70% of winners use trending audio
3. Pacing: Quick cuts, fast transitions (Gen Z expects 1-2sec per scene)
4. Text overlay: Bold, contrasting, 1-2 key messages
5. Authenticity: Unpolished > over-produced (vs Facebook)
6. CTA: Soft CTA in video (no explicit "Buy now")
7. Length: 9-15 seconds ideal (TikTok scroll velocity)

Example TikTok Ad Script:
[0-1s] Unexpected problem hook: "POV: You're losing €500/day"
[1-3s] Problem visualization: Show ads manager with red numbers
[3-6s] Solution intro: "What if I told you..."
[6-9s] Demo/proof: Quick product walkthrough
[9-15s] CTA: "Try free [link in bio]" + trending audio
```

### TikTok Pixel & Conversion Tracking

```
TikTok Pixel setup:
1. Install pixel code on website (like Facebook Pixel)
2. Track standard events: Purchase, Add to Cart, InitiateCheckout
3. Use pixel data for conversion campaign optimization
4. Lookalike audiences from Pixel converters

Conversion Rate (TikTok e-commerce): 0.5-2%
(Lower than Instagram due to younger, less commercial-intent audience)
```

---

## Parte 4: LinkedIn Ads (B2B)

### LinkedIn Ads Targeting & Cost

**Unique to LinkedIn:** Job title, company, company size, industry targeting

**Targeting Capabilities:**

| Elemento | Targeting Options | Example |
|----------|---|---|
| **Job Title** | Text match, exact | "Digital Marketing Manager", "CMO", "VP Marketing" |
| **Function** | 15+ functions | Marketing, Sales, IT, Finance |
| **Industry** | 50+ industries | Technology, Financial Services, Healthcare |
| **Company** | Specific company, competitor list | "Acme Corp", "Acme's employees" |
| **Company Size** | 1-10, 11-50, 51-200, 201-500, 501-1000, 1000+ | B2B target often "201-1000" |
| **Seniority** | Entry, intermediate, manager, director, C-suite | C-level CPC highest |

### LinkedIn Campaign Types

| Campaign Type | Goal | CPC | Best For |
|---|---|---|---|
| **Sponsored Content** | Post engagement, website clicks, lead gen | €5-€12 | Thought leadership, case studies |
| **Sponsored InMail** | Direct message in LinkedIn inbox | €10-€20 | High-intent offers, event invites |
| **Conversation Ads** | Video, CTA buttons in LinkedIn feed | €3-€8 | Brand awareness, quick responses |
| **Retargeting** | Website visitors, page engagers | €2-€6 | Lower cost, high intent |

### LinkedIn Lead Gen Ads (Native Form)

**Advantage:** Form pre-fills with LinkedIn profile data (higher conversion than website form)

```
Setup:
1. Create Lead Gen Ad campaign
2. LinkedIn form pre-populates with user:
   - First name
   - Last name
   - Email
   - Company
   - Job title
3. Add optional fields: Phone, company size, etc.
4. Form conversion rate: 10-25% (vs 3-5% on website form)

CTA button options:
- "Learn more"
- "Download now"
- "Register"
- "Get demo"
- "Sign up"
```

### LinkedIn Benchmarks (B2B)

| Metric | Benchmark | Notes |
|--------|-----------|---|
| **CPM (Cost per 1000 impressions)** | €10-€20 | High CPM vs Facebook (€3-€8) |
| **CPC (Cost per click)** | €5-€12 | Targeting precision = high cost |
| **CTR** | 0.5-1.5% | Lower than Facebook, but higher-quality audience |
| **Lead Gen Form Conversion** | 10-25% | LinkedIn pre-fill benefit |
| **Lead Gen Web Form Conversion** | 3-5% | Benchmark for comparison |
| **CPA (Lead)** | €50-€200 | Depends on form length, industry |

**LinkedIn vs Facebook (B2B E-commerce):**

```
Scenario: Software company, target CMOs in Italy

Facebook:
- Reach: 200K users (broad, interest-based)
- CPM: €4-€6
- Lead cost: €50-€80 (lots of low-quality leads)

LinkedIn:
- Reach: 50K users (precise, job-title based)
- CPM: €15-€20
- Lead cost: €80-€120 (fewer, higher quality leads)

Recommendation: Use LinkedIn for B2B, Facebook for B2C/SMB
```

---

## Parte 5: Programmatic Advertising (DSP/SSP/RTB)

### Programmatic Ecosystem

```
Advertiser (brand)
    ↓
DSP (Demand-Side Platform: DV360, Trade Desk, Adobe DMP)
    ↓ (bid in real-time)
    ↑ (auction happens <100ms)
    ↑
SSP (Supply-Side Platform: Google Ad Manager, OpenX, Rubicon)
    ↓
Publisher Website
    ↓
User sees ad

Flow:
1. Publisher page loads
2. Ad slot available, SSP triggers auction
3. DSP bids (automated, per-impression)
4. Highest bid wins, ad served <100ms
5. User sees ad
```

### DSP vs SSP vs DMP vs CDP

| Platform | Role | Ejemplos | Function |
|----------|------|---------|----------|
| **DSP** (Demand-Side Platform) | Buyer side | DV360 (Google), The Trade Desk, Adobe | Advertisers bid for ad inventory, optimize campaigns |
| **SSP** (Supply-Side Platform) | Seller side | Google Ad Manager, OpenX, Rubicon Project | Publishers monetize inventory, manage auctions |
| **DMP** (Data Management Platform) | Data | BlueKai, Neustar | Collects/segments 3rd-party audience data (declining post-3rd cookie) |
| **CDP** (Customer Data Platform) | Data | Segment, Tealium, mParticle | 1st-party customer data, privacy-safe (post-3rd cookie era) |

### RTB (Real-Time Bidding) Mechanics

```
Timeline (milliseconds):

0ms: User visits publisher.com
5ms: Browser loads ad tag (SSP code)
10ms: SSP triggers auction, sends bid request to DSPs
15ms: DSP (Trade Desk) receives bid request
20ms: DSP's algorithm evaluates:
      - User cookies/audience segments
      - Page context (topic, brand safety)
      - Campaign objectives (reach, conversion, brand lift)
      - Budget remaining
25ms: DSP submits bid (e.g., "€0.50")
30ms: SSP collects 50+ bids from DSPs
35ms: SSP picks highest bid (auction cleared at €0.45)
40ms: Winner ad called from ad server
45ms: Ad loads in browser
50ms: User sees ad

Total: <100ms (100 milliseconds)
```

### Header Bidding

**Traditional Waterfall Problem:**

```
Before Header Bidding:
1. SSP 1 (e.g., Google Ad Manager): Bid €0.50, loses, next
2. SSP 2 (Rubicon): Bid €0.48, loses, next
3. SSP 3 (OpenX): Bid €0.30, wins
→ Not optimal (higher bidders didn't get chance)

With Header Bidding:
1. ALL SSPs bid simultaneously (in header of page)
2. SSPs compete: Google (€0.50), Rubicon (€0.48), OpenX (€0.30)
3. Highest bid wins (Google €0.50)
→ Publisher gets better yield
→ Advertiser pays efficient price
```

**Publishers see 20-50% yield increase with header bidding**

---

### Brand Safety & Viewability

#### Brand Safety Categories

| Category | Risk Level | Publisher Controls | Example |
|----------|---|---|---|
| **Content type** | High | Whitelist safe topics | Luxury brand avoids "scandal", "crime" sites |
| **Inappropriate content** | High | Blacklist unsafe | Alcohol ads blocked on parenting sites |
| **Domain/URL** | Medium | Domain verification | Check sitelist before buying |
| **Contextual keywords** | Medium | Keyword exclusion | "COVID-19" blocked for health brands (2020-2021) |
| **Fraudulent traffic** | High | IVT (Invalid Traffic) filtering | MRC certified verification |

#### Viewability Standards (MRC - Media Rating Council)

```
Display Ads:
- 50% pixels visible on screen
- For 1 second continuous

Video Ads (pre-roll, mid-roll):
- 50% pixels visible
- For 2 seconds continuous

Benchmark (industry):
- Display average viewability: 40-60% (many ads never seen)
- Video average viewability: 45-70%
- Target: >60% for premium inventory

Cost implications:
- Premium inventory (>70% viewability): CPM +30-50%
- Standard inventory (40-60%): Baseline CPM
- Low viewability (<40%): CPM -50% (often fraud)
```

---

### Programmatic Audience Targeting

**Audience Segments (1st vs 3rd Party):**

```
1st-party data (publisher owns):
- Logged-in users
- Email subscribers
- Purchase history
- CRM data

3rd-party data (DMP/data providers):
- Demographic (age, gender, income estimate)
- Interest (sports, travel, tech interest)
- Behavioral (page visits across sites)
- Intent (searched for "car insurance")
- Lookalike (similar to high-value users)

Impact of 3rd-party cookie phase-out (2024+):
- Less targeting precision
- CPM for behavioral campaigns -20-30%
- Shift to 1st-party, contextual, cohort-based targeting
```

---

## Parte 6: Retargeting Strategies

### Retargeting Audience Definition

```
Retargeting Segmentation:

1. Cart Abandoners (last 7 days)
   - Added product to cart, not purchased
   - Audience size: 5-15% of visitors
   - Conversion potential: 10-20% (highest)
   - Bid strategy: Higher CPC (hot audience)

2. Product Viewers (last 30 days)
   - Viewed product page, no cart add
   - Audience size: 20-40% of visitors
   - Conversion potential: 3-8%
   - Bid strategy: Medium CPC

3. Website Visitors (last 180 days)
   - Visited homepage, any page
   - Audience size: 40-70% of visitors
   - Conversion potential: 1-3% (cold)
   - Bid strategy: Lower CPC/CPM

4. Engaged Visitors (video watchers, blog readers)
   - Watched video >30s or read blog >2min
   - Audience size: 10-20% of visitors
   - Conversion potential: 3-5%
   - Bid strategy: Medium-high CPC
```

### Retargeting Campaign Structure

**Google Ads Remarketing:**

```
Display Remarketing Campaign:
├── Remarketing audience 1: Cart abandoners (last 7 days)
│   ├── Ad Group: Cart abandon
│   │   └── Remarketing ad: [Product image] "Back to [Product]. Use CODE15 for 15% off"
│   │   └── CPM bid: €12/1000 impressions
│   └── Duration: 7 days in audience
│
├── Remarketing audience 2: Product viewers (last 30 days)
│   └── Ad: "Interested in [Product]? Compare with competitors."
│   └── CPM bid: €8/1000 impressions
│
└── Exclusion: Existing customers (custom audience)
    └─ Don't remarket to people already purchased
```

**Meta Retargeting:**

```
Facebook Remarketing Campaign:
├── Audience: Website visitors (last 30 days)
│   └─ Pixel tracked on website
│   └─ Exclude customers (past 30 days)
├── Ad: Carousel showing products, testimonial, guarantee
├── CPM: €3-€6
└── Placement: Feed + Stories + Reels
```

---

## Parte 7: Attribution Modeling & Cross-Device Challenges

### Attribution Models Explained

```
Scenario: Customer's journey over 7 days

Day 1: Display ad (interest)
Day 3: Organic search (high intent)
Day 5: Email click
Day 7: Purchase

Revenue: €100

Different attribution models assign credit differently:

╔════════════════╦══════╦══════════╦══════╗
║ Model          ║ Ad 1 ║ Organic  ║ Email║
╠════════════════╬══════╬══════════╬══════╣
║ Last-click     ║ €0   ║ €0       ║ €100 ║ (only last = skewed)
║ First-click    ║ €100 ║ €0       ║ €0   ║ (only first = unvalued)
║ Linear         ║ €33  ║ €33      ║ €33  ║ (equal = oversimplify)
║ Time-decay     ║ €15  ║ €30      ║ €55  ║ (recent = weighted)
║ Position 40/20/40║ €40  ║ €20      ║ €40  ║ (first+last = logical)
║ Data-driven*   ║ €25  ║ €35      ║ €40  ║ (ML-trained = precise)
╚════════════════╩══════╩══════════╩══════╝

*Data-driven requires 15,000+ conversions, Google trained model
```

### Cross-Device Attribution Challenges

```
User's multi-device journey:

Day 1 (Desktop, home):
└─ Sees display ad on news site

Day 3 (Mobile, commute):
└─ Googles "product review"

Day 5 (Tablet, office):
└─ Clicks email, views product

Day 7 (Mobile, home):
└─ Completes purchase

CHALLENGE: Different devices, different cookies
- Desktop cookie ≠ Mobile cookie ≠ Tablet cookie
- Attribution platforms struggle to link journey

Solutions:
1. User ID: Login required, Facebook ID, Google ID
2. Cross-device graph: Google/Apple/Facebook's device linking
3. Probabilistic: IP + demographic matching (less accurate)
4. Offline: CRM match (email address) to online events

Limitation: 40-60% of conversions unmapped without user login
```

---

## Parte 8: ROAS Benchmarks per Industry

### ROAS (Return on Ad Spend) by Vertical

```
Industry benchmarks (source: various agencies, actuals vary by market):

╔═══════════════════════════════╦════════════╦════════════╗
║ Industry                      ║ Target ROAS║ Notes      ║
╠═══════════════════════════════╬════════════╬════════════╣
║ E-commerce (general)          ║ 3-5x       ║ Baseline   ║
║ E-commerce (premium/luxury)   ║ 4-8x       ║ Higher AOV ║
║ E-commerce (repeat purchases) ║ 5-10x      ║ LTV driven ║
║ SaaS (free trial)             ║ 4-6x       ║ High LTV   ║
║ SaaS (annual plans)           ║ 6-10x      ║ Very high LTV ║
║ B2B (lead gen)                ║ 5-8x       ║ w/ sales follow ║
║ Retail (in-store conversion)  ║ 4-7x       ║ Offline revenue ║
║ Service business (local)      ║ 3-6x       ║ Lower margin ║
║ Direct mail (low volume)      ║ 2-3x       ║ High CAC    ║
║ Affiliate marketing           ║ 5-15x      ║ Variable    ║
╚═══════════════════════════════╩════════════╩════════════╝

Formula to define target:
Target ROAS = (Desired Profit Margin % × Revenue) / Ad Spend

Example:
- Revenue target: €100,000/month
- Gross margin: 60% (€60,000)
- Ad budget: €15,000
- Target ROAS = (0.60 × €100,000) / €15,000 = 4.0x

Meaning: For every €1 spent on ads, generate €4 revenue
```

### ROAS Calculation & Forecasting

```
Formula:
ROAS = Total Revenue from Ads / Total Ad Spend

Example:
Campaign spend: €5,000
Attributed revenue: €20,000
ROAS = €20,000 / €5,000 = 4.0x

Breakdown by channel:
Search: €2,000 spend → €10,000 revenue = 5.0x ROAS ✓
Display: €1,500 spend → €4,500 revenue = 3.0x ROAS
Social: €1,500 spend → €5,500 revenue = 3.7x ROAS
Average: 4.0x ROAS

Forecast next month:
If budget = €7,000 and maintain 4.0x ROAS
Expected revenue = €7,000 × 4.0 = €28,000
(Assumes consistent performance, market conditions)
```

---

## Summary: Performance Advertising Roadmap (3 Months)

| Month | Activity | Platform | Owner |
|-------|----------|----------|-------|
| Month 1 | Audit existing campaigns (QS, CTR, ROAS) | All | Digital manager |
| | Setup conversion tracking (pixel, API) | Google, Meta, TikTok | Analytics |
| | Implement basic audiences (remarketing, lookalike) | Meta, Google | Audience manager |
| Month 2 | Launch Search + Display testing | Google Ads | SEM specialist |
| | Setup Shopping campaign with Merchant Center | Google | E-commerce ops |
| | Create Meta + TikTok awareness + conversion | Meta, TikTok | Social manager |
| | A/B test creative, audience, placement | All platforms | Creative |
| Month 3 | Optimize bids toward ROAS target | All | SEM/Social manager |
| | Implement attribution modeling | Analytics | Data analyst |
| | Monthly performance review + roadmap | All | Digital manager |
| Ongoing | Monitor ROAS, adjust budget allocation | All | Weekly monitoring |
