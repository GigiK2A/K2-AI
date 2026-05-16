# Frontend & UX/UI Audit
Date: 2026-05-16
Scope: `kai-website/src/*.html` (18), `kai-website/src/suite-ai/*.html` (20), `kai-website/src/{js,css}/*`, `kai-website/kbot/src/app/*` + components.
Method: static code review of all customer-facing surfaces, no browser execution.

---

## Page inventory

| Path | Title (browser tab) | Purpose | Status | Notes |
|------|---------------------|---------|--------|-------|
| `/index.html` | Sistemi AI operativi per PMI \| K2-AI — Prototipo in 14gg | Homepage, hero, evidence, method, K-BOT gateway, FAQ | Live | v2 positioning OK in title/H1; **Clerk reference** at L340 (Supabase is real stack) |
| `/metodo.html` | Metodo K2-AI \| Dal problema al sistema AI in 4 fasi | 4-step methodology | Live | Schema HowTo present |
| `/laboratorio.html` | (laboratorio) | Internal case studies | Live, populated (5 cases) | Trust signal OK |
| `/casi-studio.html` | (legacy) | Near-duplicate of laboratorio; canonical → `/laboratorio` | Legacy with proper canonical | Only H1 differs. Could be replaced by 301 |
| `/k-bot.html` | K-BOT \| Report AI professionali… | K-BOT marketing | Live | OG description says "12 settori" but body says "49 skill" — minor inconsistency |
| `/per-te.html` | (per-te) | Profile-based landing | Live, 1285 LOC | Wrapper for funnel by profile |
| `/suite-ai.html` | Suite AI overview | Hub for 20 pillar | Live | |
| `/suite-ai/agenti-email-crm.html` | Agenti AI email e CRM per PMI \| K2-AI | Pillar P01 | Live | 4 dead `href="#"` "Leggi:" links L193-196 |
| `/suite-ai/automazioni-amministrative.html` | Pillar P02 | | Live | 4 dead `href="#"` L191-194 |
| `/suite-ai/ai-legale-contratti.html` | P03 | | Live | 4 dead `href="#"` |
| `/suite-ai/ai-ingegneria-progettazione.html` | P04 | | Live | 4 dead `href="#"` |
| `/suite-ai/microapp-documenti-tecnici.html` | P05 | | Live | 4 dead `href="#"` |
| `/suite-ai/ai-customer-service-ticket.html` | P06 | | Live | 4 dead `href="#"` |
| `/suite-ai/rag-knowledge-base.html` | P07 | | Live | 4 dead `href="#"` |
| `/suite-ai/ai-compliance-audit.html` | P08 | | Live | 4 dead `href="#"` |
| `/suite-ai/ai-controllo-gestione-reporting.html` | P09 | | Live | 4 dead `href="#"` |
| `/suite-ai/integrazione-gestionali-erp.html` | P10 | | Live | 4 dead `href="#"` |
| `/suite-ai/ai-marketing-contenuti.html` | P11 | | Live | |
| `/suite-ai/diagnosi-strategica-pmi.html` | P12 | | **Branding regression risk** | Uses banned v1 frame "diagnosi strategica"; copy contains "advisor e consulenti" (`L97`, `L149`) |
| `/suite-ai/agevolazioni-finanza-agevolata.html` | P13 | | Live | |
| `/suite-ai/ai-edilizia-appalti-pubblici.html` | P14 | | Live | |
| `/suite-ai/ai-hr-recruiting.html` | P15 | | Live | |
| `/suite-ai/ai-real-estate-tokenizzazione.html` | P16 | | Live | Mentions "advisor, family office, fondi" L69, L129 (acceptable — describing target users, not K2 services) |
| `/suite-ai/ai-data-analytics-bi.html` | P17 | | Live | |
| `/suite-ai/ai-ux-design-system.html` | P18 | | Live | |
| `/suite-ai/ai-efficienza-energetica.html` | P19 | | Live | |
| `/suite-ai/ai-hospitality-revenue.html` | P20 | | Live | |
| `/contatti.html` | Contatti K2-AI \| Risposta in 24 ore… | Contact form + newsletter | Live | `<a href="#">K2-AI Italia</a>` L113 (dead LinkedIn link) |
| `/newsletter.html` | Archivio Newsletter \| K2-AI | List of issues | Live | |
| `/newsletter-entry.html` | (single issue) | Detail | Live | Only 70 LOC |
| `/newsletter-ok.html` | confirm OK | Confirm | Live | |
| `/newsletter-error.html` | error | Error | Live | |
| `/privacy.html` | Privacy | Legal | Live | |
| `/cookie.html` | Cookie | Legal | Live | |
| `/note-legali.html` | Note legali | Legal | Live | Holds P.IVA, REA |
| `/analisi.html` | Analisi K2-AI \| Diagnosi AI… | **Orphan** | Not in nav, canonical self-references | CLAUDE.md flags this as orphaned. Still appears in `src/public/sitemap.xml` |
| `/workshop.html` | (legacy) | Pre-v2 page | Canonical → `/suite-ai` (good) | Should be deleted from `src/`; server handles 301 |
| `/report-preview.html` | (React entry) | Report preview internal | Live | 17 LOC entrypoint for `report-preview-entry.tsx` |
| `/app` (K-BOT premium, Next.js) | `/app/sign-in`, `/app/sign-up`, `/app/` chat, `/app/dashboard` | Premium chat + auth | Live | Subdomain via proxy in `server.js` |

---

## Findings by severity

### CRITICAL (UX broken or blocking conversions / brand regression)

**C1 — Homepage K-BOT block claims "Clerk" auth but real stack is Supabase**
`kai-website/src/index.html:340` → `Accesso sicuro con Clerk e dashboard personale.`
K-BOT premium uses Supabase Auth (`kai-website/kbot/src/components/auth/AuthForm.tsx`). Mentioning a third-party brand the product doesn't use is a credibility/legal/security-disclosure issue. Replace with "Accesso sicuro con account dedicato" or "Autenticazione email/password".

**C2 — `Diagnosi strategica PMI` pillar contradicts CLAUDE.md positioning**
`kai-website/src/suite-ai/diagnosi-strategica-pmi.html` — entire page exists and is shipped, despite CLAUDE.md §1 banning v1 terms ("diagnosi strategica") and §6 disallowing "advisor". Body uses "Advisor e consulenti" L97 and "advisor" L149. The page slug itself is v1 framing.
Either retire (301 → `/suite-ai/ai-controllo-gestione-reporting.html` or remove from sitemap) or rewrite under a v2-compliant slug. Confirm with Luca before action.

**C3 — Pillar pages missing "Per te" in nav (20 pages)**
All 20 `kai-website/src/suite-ai/*.html` nav lists (e.g. `agenti-email-crm.html:44-51`) omit the `<li><a href="/per-te">Per te</a></li>` item present on every other page. Breaks navigation consistency and removes a major funnel entry from the SEO entry pages with the highest impressions volume. Same omission in the mobile overlay (L60-68 of each pillar).

**C4 — 40 dead `<a href="#">` "Leggi: …" links across pillar pages**
10 pillar HTMLs each contain 4 dead links (sample: `agenti-email-crm.html:193-196`, `automazioni-amministrative.html:191-194`, `ai-compliance-audit.html:159-162`). These render as `tag` chips inviting users to "Leggi" articles that don't exist — clicks scroll to top. Either remove the entire `tag-list` block until cluster articles ship, or replace with `aria-disabled` non-link spans.

**C5 — K-BOT premium welcome message + suggestion chips push v1 framing**
`kai-website/kbot/kbot/src/app/page.tsx:28` WELCOME_MESSAGE: `"…sono K-BOT, l'analista K2-AI. Costruiamo insieme un report operativo concreto — valutazione di un investimento, strategia di marketing, audit SEO, diagnosi di bilancio…"`. The phrase "diagnosi di bilancio" is exactly the v1 trigger that the audit plan flagged as risk R10 — still live.
`page.tsx:20-25` `REPORT_SUGGESTIONS` includes `"Diagnosi finanziaria del mio bilancio"` — identical issue (R9). After cold-start guard was added server-side, the front-end chips still anchor the user to the deprecated frame.

### HIGH (visible quality issue / accessibility)

**H1 — Footer copyright frozen at "© 2025 K2-AI" on every page (37 pages)**
Today is 2026-05-16. Found on 37 HTML files; sample: `index.html:534`, `per-te.html:1274`, `kbot/src/app/page.tsx` n/a (footer is in marketing only). Update to "© 2026 K2-AI" or dynamic year via JS.

**H2 — Contact page LinkedIn link is dead**
`kai-website/src/contatti.html:113` → `<a href="#" class="contact-link">K2-AI Italia</a>`. Shown as a real contact channel in the trust section; the JSON-LD even references `https://www.linkedin.com/company/k2-ai/` (`contatti.html:29`). Either point href to the LinkedIn URL or remove the row.

**H3 — Supabase Auth errors leak raw provider strings to user**
`kai-website/kbot/src/components/auth/AuthForm.tsx:66` → `setError(err instanceof Error ? err.message : "Accesso non riuscito.")`. Supabase returns English messages like "Invalid login credentials" and "User already registered". Two problems:
- Italian site shows English error text.
- Cannot differentiate "account does not exist" vs "wrong password" — audit-plan risk R8.
Map known Supabase error codes (`invalid_credentials`, `user_already_exists`, `email_not_confirmed`, `weak_password`) to Italian copy with actionable CTA (e.g. "Email non riconosciuta — registrati →"). Note: Supabase intentionally collapses both cases under `invalid_credentials` for enumeration protection — message should reflect that ambiguity honestly ("Email o password non corrette") rather than guess.

**H4 — Sign-up success message is conditional/confusing**
`kai-website/kbot/src/components/auth/AuthForm.tsx:60` → `"Account creato. Se Supabase richiede conferma email, controlla la posta; altrimenti puoi entrare subito."` This is implementation language ("Se Supabase richiede…") leaking to end users. Pick the actual state (confirmation is currently OFF per audit plan §R3) and write deterministic copy: `"Account creato. Puoi accedere subito."` Or, if you enable email confirm, `"Ti abbiamo inviato un'email di conferma — controlla la posta."`.

**H5 — K-BOT widget error state is generic and has no retry**
`kai-website/src/js/chat.js:406` → on any non-2xx (≠429) or thrown error: `"Errore di connessione. Riprova."` — plain text, no retry button, no distinction between offline, server 5xx, or rate limit non-429 (e.g. Anthropic timeout). Audit-plan checklist asks for retry button + status-specific message. Currently the user has to manually re-type the question.

**H6 — Pages lack `<main>` landmark**
Only `index.html:96` opens a `<main>` element. `contatti.html`, `metodo.html`, all 20 pillar pages, `laboratorio.html`, `suite-ai.html`, `k-bot.html` go `nav → section → footer` with no `<main>` wrapper. Screen readers and Lighthouse a11y both penalize.

**H7 — Composer (K-BOT premium) icon-only buttons missing aria-labels**
`kai-website/kbot/src/components/chat/Composer.tsx`:
- L151 paperclip button: only `title="Allega file"`, no `aria-label`.
- L158 globe URL button: only `title="Analizza un URL"`.
- L169 send button: only an `ArrowUp` icon, no text, no aria-label, no title.
- L105 close button (X icon for URL mode) — no aria-label.
Add `aria-label="Allega file"`, `aria-label="Analizza URL"`, `aria-label="Invia messaggio"`, `aria-label="Chiudi"`.

**H8 — Zero images use `loading="lazy"`**
Searched all 38 HTML files for `loading="lazy"` → 0 matches across 70 `<img>` tags. Most are the logo (above the fold, OK), but `per-te.html` and laboratorio cards may host below-fold images. Add `loading="lazy"` to all non-hero images.

**H9 — `analisi.html` is orphaned but still in sitemap**
CLAUDE.md §4 explicitly flags this as orphaned. Page has self-canonical `https://www.k2-ai.it/analisi.html` (L10) → confirmed by `src/public/sitemap.xml` still listing it. Either delete the file + drop from sitemap, or 301 to `/k-bot`.

### MEDIUM

**M1 — Inconsistent ".html" suffix in nav links**
Pillar pages use `.html` suffix in nav (e.g. `agenti-email-crm.html:46` → `/metodo.html`, `/laboratorio.html`, `/suite-ai.html`, `/newsletter.html`, `/contatti.html`), while root pages use clean URLs (e.g. `index.html:68` → `/metodo`, `/laboratorio`). Server probably rewrites both, but inconsistency hurts SEO canonicalization and shows different URLs in browser status bar on hover.

**M2 — K-BOT marketing page numbers disagree internally**
`k-bot.html:8` description "Skill verticali su 12 settori"; L25 twitter description "49 skill verticali"; L92 card "49 Skill verticali"; L259 "le 49 skill". The "12" in the SEO meta is wrong and shows in SERPs.

**M3 — Privacy/Cookie policy links from K-BOT premium use `.html` while marketing uses clean URLs**
`AuthForm.tsx:186` → `href="/privacy.html"`; `L202` → `href="/note-legali.html"`. Marketing nav uses `/privacy`, `/note-legali`. Both probably resolve, but consistency would help and avoid 301 redirects.

**M4 — `casi-studio.html` is a near-duplicate of `laboratorio.html`**
Only H1 differs ("I primi clienti siamo stati noi." vs "Prima testiamo su di noi."). Canonical is correctly set to `/laboratorio` (L10), so SEO-safe, but maintaining two HTML files with identical body is fragile — any change must be applied twice. Recommend reducing `casi-studio.html` to a meta-redirect or deleting the file (server.js handles 301).

**M5 — K-BOT widget on homepage is non-interactive "preview"**
`index.html:363-391` shows a `chat-widget` element with static fake messages; the actual CTA is a "Inizia gratis →" button to `https://kbot-premium-production.up.railway.app/sign-up`. Two issues:
- Hardcoded Railway preview subdomain (L385) instead of `/app/sign-up`. Brittle if the Railway slug changes.
- User likely assumes they can chat in-place; clicking sends them off-site. Marking it as "Anteprima" / "Demo" would manage expectations.

**M6 — 5° esito paid (19€ Tier0) is not implemented**
CLAUDE.md §8 specifies adding a 5th paid outcome to K-BOT chat (Stripe payment link → PDF). `chat.js` (511 LOC) has no Stripe trigger, no `STRIPE_TIER0_PAYMENT_LINK` reference, no 19€ CTA. Roadmap item still open.

**M7 — Form contatti success state hides whole form (good) but never offers a "new message" path**
`contact-form.js:71-82` sets every form element to `hidden`, shows the success message. There is no "Invia un'altra richiesta" button — if the user mis-typed an email or wants to follow up, they must reload. Acceptable for v1, but a small `Reset` link in the success state would improve UX.

**M8 — Newsletter form sr-only labels good — but contact form labels are visible-only**
`contact-form.js`/contatti.html uses normal `<label>` linked via `for=` (good). Newsletter form (`contatti.html:231-247`) uses `sr-only` labels + `placeholder` as visible label — borderline a11y, OK but means placeholder text doubles as label (cannot tab-clear).

**M9 — K-BOT premium contact form / sign-up does NOT honeypot or rate-limit client side**
Marketing contact form has honeypot (`contatti.html:129-132`). K-BOT premium sign-up does not — relies entirely on Supabase Auth rate limit. Newsletter has no honeypot either. With public form endpoints, expect bot signups within weeks of launch.

**M10 — K-BOT premium handleSubmit shows raw error in chat**
`kbot/src/app/page.tsx:290` → `setError(e instanceof Error ? e.message : "Errore imprevisto")`. The error string from `sendMessage()` can include backend detail (e.g. fetch error, 5xx body). Bubble through a friendly mapper.

### LOW / polish

**L1 — `aria-label="K2-AI"` on logo links is redundant with the `<img alt="K2-AI">` inside**
e.g. `index.html:63-65`. Either drop the alt and keep aria-label, or vice versa; doubling them yields some screen readers reading "K2-AI K2-AI link".

**L2 — `nav.js:7` active-link match is fragile**
`path.includes(href.replace('.html', ''))` will mark `/metodo` active when path is `/metodo-anything`. Use exact match or regex anchored at end. Low impact, low traffic for `/metodo*` collisions.

**L3 — `home-3d.css` is 1937 LOC** — only loaded on homepage (verified `index.html:37`), but worth tree-shaking for unused selectors before the next Lighthouse pass.

**L4 — `LinkedIn` href "#" on contatti.html appears as a real link with hover styles** — at minimum add `aria-disabled="true"` and `style="pointer-events:none"`, or remove until a real URL exists.

**L5 — Suite-ai pillar pages quote tone is consistent, but mascot icons (🏨 📊 ⚖️ 🏗️ 🛒 🔍) on `k-bot.html:153-181` create inconsistency** — they're the only place emojis appear in nav/services blocks. Suite-ai pillar cards use `card-number` text labels. Pick one direction.

**L6 — `K-BOT widget` on homepage `chat-input-area` is a single `<a>` button** (`index.html:384-386`) but visually mimics a chat textbox. Mobile users who tap to type will be redirected away.

**L7 — `<details>` FAQ summary on homepage uses `name="home-faq"` for accordion grouping (HTML 2024 `details name` attribute)** — works in Chrome/Safari ≥120 but is silently ignored on older mobile WebViews. Acceptable since enhancement degrades to multiple-open.

**L8 — `chat.js:432-437` strips `/contatti` mentions from assistant replies** — clever, but if the model emits `/contatti.html` inside a sentence ("ti scrivo a /contatti.html domani") the sentence becomes ungrammatical. Edge case.

---

## Accessibility findings

- No `<main>` landmark on most pages (H6).
- Icon-only buttons in K-BOT premium composer lack `aria-label` (H7).
- Color: dark theme with `--text-primary: #f5f5f5` on `--bg: #080808` → contrast ≈ 18:1 (well above WCAG AAA). `--text-muted: #8f8f8f` on `--bg` → 5.04:1 (passes AA for body but NOT for ≥18pt heading needs; OK for small body). Brand teal `#14b8a6` text on `#050505` ≈ 7.8:1 (AAA). Generally good.
- Focus visible: not asserted in `base.css`; no `:focus-visible` selector found in `base.css`. **REQUIRES VISUAL VERIFICATION** that the browser default focus ring is not suppressed by a global `outline:0`.
- `hamburger` button has `aria-expanded` and `aria-controls` correctly wired (`nav.js:18,26,41,42`).
- Skip-to-content link: NOT present on any page.
- `<details>` FAQ items have proper `<summary>` (✓ keyboard accessible).
- Form labels: `for`/`id` paired correctly on contatti.html and AuthForm.tsx.
- Newsletter inputs use `sr-only` labels (acceptable).
- K-BOT widget input field (`chat-input`) has no `<label>` on `k-bot.html` — REQUIRES VISUAL VERIFICATION inside the chat widget DOM.

---

## Mobile-specific findings

- iOS notch / safe-area cover correctly handled via `body::before` strip in `base.css:151-161` (recent commit, verified).
- `overflow-x: clip` lock applied at `html, body` (`base.css:127-133`) — prevents horizontal scroll from rogue elements.
- `overflow-wrap: anywhere` applied globally (`base.css:137-140`) — protects long URLs/strings on narrow screens.
- `--pad-x` drops to 24px and `--section-py` to 80px on `max-width: 768px` (`base.css:103-108`).
- Hamburger menu opens an `.nav-overlay` with close-on-link-click (`nav.js:59-61`) and Escape handler (L64-66). Good.
- K-BOT premium composer is `sticky bottom-0` (`Composer.tsx:64`) — iOS keyboard behavior **REQUIRES VISUAL VERIFICATION** (sticky + keyboard known to be glitchy on iOS Safari < 17).
- Send button (`chat.js:328-335`) has explicit `touchend` handler with `preventDefault` — good for iOS double-fire prevention.
- 70 `<img>` tags, 0 with `loading="lazy"` (H8) — extra cost on mobile.

---

## Copy / messaging issues

- **"Clerk" mention** on `index.html:340` (C1).
- **"diagnosi di bilancio" / "Diagnosi finanziaria del mio bilancio"** in K-BOT premium welcome + chips (C5).
- **`diagnosi-strategica-pmi.html`** entire page uses banned v1 framing (C2).
- **K-BOT marketing description** says "12 settori" in meta description (`k-bot.html:8`) and "49 skill" everywhere else (M2).
- **AuthForm `setMessage`** at L60 leaks implementation lingo ("Se Supabase richiede conferma…") (H4).
- **Tone**: spot-check on `agenti-email-crm.html`, `index.html`, `metodo.html`, `k-bot.html` is on-brand: direct, quantified, italiano-first. No banned buzzwords ("rivoluzionario", "trasformazione digitale", "journey") found.
- **CTA "Apri K-BOT"** is consistent on every page (`nav-cta` class). Good.
- **"Scrivici"** vs **"Parla con noi"** vs **"Richiedi una proposta"** — three CTA labels for the same action (contact form). Minor.
- **Microlegal note** below contact form is clear and links Privacy (`contatti.html:210-212`) — good.

---

## v1 vs v2 positioning regressions

| Term | Location | Severity | Status |
|------|----------|----------|--------|
| "advisor finanziari", "AdvisorBoost", "StrategyBoost" (banned per CLAUDE.md §1) | None found in customer-facing HTML | — | OK |
| "diagnosi strategica" | `suite-ai/diagnosi-strategica-pmi.html` (slug + body) | CRITICAL | C2 — needs decision |
| "diagnosi di bilancio" | `kbot/src/app/page.tsx:28` (welcome) | CRITICAL | C5 |
| "Diagnosi finanziaria del mio bilancio" | `kbot/src/app/page.tsx:24` (suggestion chip) | CRITICAL | C5 |
| "Diagnosi finanziaria" / "Diagnosi finanziarie" | `k-bot.html:8` meta, L94 card body ("diagnosi finanziaria PMI"), `kbot-bridge.js` (none) | MEDIUM | Soft regression — appears mixed with v2 framing |
| "Advisor" as service descriptor for K2 | `suite-ai/diagnosi-strategica-pmi.html:97`, `:149` | HIGH | Part of C2 |
| "advisor" as user persona (acceptable) | `ai-real-estate-tokenizzazione.html:69,129` ("supporto per advisor, family office, fondi") | LOW | Describes the customer base of the user, not K2's positioning. Acceptable. |
| v2 positioning string | `index.html:104` hero, JSON-LD on home + 5 other pages, `metodo.html`, `k-bot.html` | — | Present and consistent. |

---

## Things verified OK

- v2 positioning string "Sistemi AI operativi per PMI italiane" present in homepage hero, schema.org JSON-LD, OG/Twitter meta on every key page.
- Schema.org Organization + ProfessionalService + WebSite JSON-LD ship on home, contatti, cookie, privacy, laboratorio, casi-studio, metodo, workshop.
- Schema.org Service + BreadcrumbList + FAQPage on pillar pages (sample: agenti-email-crm.html L33-35).
- `<link rel="canonical">` present on every page surveyed (correctly self-or-redirect).
- HSTS/CSP/security headers handled in `server.js` (separate backend audit). Marketing pages defer to those.
- PostHog analytics anonymous mode (memory persistence, no cookie banner needed), DNT respected (`analytics.js:32`). `kbot_open`, `kbot_message_sent` events fired (`chat.js:297,360`). `contact_submit` fired on success (`contact-form.js:234`).
- Contact form: honeypot field present (`contatti.html:129-132`), inline error / success state, prefill from K-BOT session, source_page tracking.
- Newsletter: double opt-in flow (newsletter-entry/ok/error pages exist), `aria-live` for status message (`contatti.html:249`).
- K-BOT widget: rate-limit message on 429 (`chat.js:390-394`).
- K-BOT premium LoadingState: progressive UX — dots for first 8s, then real progress bar with 9 contextual steps (`LoadingState.tsx`). Strong.
- iOS Safari overflow guard and notch coverage in `base.css` recent commits.
- Mobile hamburger with Escape, click-outside, resize-close, aria-expanded — clean implementation in `nav.js`.
- Three.js bundle (`home-3d.js` 531 LOC) only loaded on `/index.html` — confirmed only entry-point (`grep` returned 1 match).
- Fonts preloaded (`woff2`) on every page; `font-display: swap` set on all `@font-face` rules.
- Empty state for `/per-te` profile selector (`per-te.html:667-670`) — graceful.

---

## Frontend readiness score

**6.5 / 10**

Justification:
- **Foundations (8/10)**: design system, typography scale, mobile fixes, analytics, schema markup, font loading, sticky composer, iOS notch — all done well.
- **Polish (5/10)**: 40+ dead links across pillar pages, 37 stale copyright, broken LinkedIn link, missing `<main>`, no lazy-loading. These are 30-minute fixes individually but they compound to feel sloppy on a careful inspection.
- **Brand consistency (5/10)**: C1 (Clerk), C2 (diagnosi-strategica pillar), C5 (welcome message + chips) all violate CLAUDE.md's explicit rules. Two of the three were already flagged in `PRODUCTION_AUDIT_PLAN.md` (R9, R10) and remain unresolved.
- **Conversion path (7/10)**: CTAs are consistent ("Apri K-BOT →"), contact form is robust, K-BOT widget functional with prefill-to-contact bridge. The 5° paid Tier0 (CLAUDE.md §8) is not yet wired (M6).
- **Accessibility (6/10)**: keyboard navigation OK, focus visible unverified, missing `<main>`, icon-only buttons miss aria-label, no skip-link, contrast generally fine.
- **K-BOT premium (7/10)**: solid loading state, multi-conversation, file/URL ingest, but auth error UX is the weakest surface and welcome copy regresses v2.

Priority order for a ship-readiness sprint:
1. C5 + C1 + C2 (brand integrity — must fix before any paid traffic).
2. C3 + C4 (visible broken links in SEO entry pages).
3. H1, H2 (copyright + LinkedIn).
4. H3, H4 (auth error UX).
5. H5, H6, H7, H8 (a11y + widget UX).
6. M-series during normal sprints.
