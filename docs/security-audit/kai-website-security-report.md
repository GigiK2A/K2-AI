# K2-AI Website — Security Audit Report

- Date: 2026-05-15
- Auditor: AI Security Review (Claude)
- Scope: `/Volumes/PARASSITA/K-AI/kai-website/`
- Components reviewed: `server.js` (2436 LOC), `api/**/*.ts`, `src/js/*.js`, `vite.config.js`, `vercel.json`, `Dockerfile`, `railway.toml`, `package.json`, `kbot/backend/app/api/webhook.py`

## Executive Summary

The K2-AI marketing site mixes three deploy targets (Vercel functions in `api/`, the Node `server.js` running on Railway/Docker, and a FastAPI Python backend behind it). According to project memory (`feedback_railway_deploy.md`), **the live deployment is Railway → `server.js`**, so most user traffic hits `server.js`, not the Vercel TypeScript handlers. This split surface is the single biggest architectural risk: the two implementations have drifted in their security controls (CSP, auth gates, rate limiting).

Top issues:

- **HIGH — Hardcoded path-token bypass for newsletter publishing/admin** in `server.js` (`NEWSLETTER_PUBLISH_PATH_TOKEN`). A static secret committed to source bypasses `INTERNAL_API_KEY` for publish and admin cleanup. Anyone with repo read access (or a leaked build artifact) can publish arbitrary stored-XSS HTML to subscribers and to `/newsletter-entry`.
- **HIGH — Stored XSS sink** in `src/js/newsletter-entry.js`: `htmlNode.innerHTML = item.html` renders newsletter HTML verbatim. Combined with the CSP weakness in `server.js` (`script-src 'self' 'unsafe-inline'`, vs strict `'self'` in `vercel.json`), a compromised publish endpoint yields full JS execution on `www.k2-ai.it`.
- **HIGH — Unauthenticated `/api/intake/contact` and `/api/newsletter/subscribe`** with no rate limiting; only a honeypot. These power Resend emails and DB inserts and enable spam-relay / cost-amplification / inbox flood against `KBOT_NOTIFY_EMAIL`.
- **HIGH — Cost-amplification on unauthenticated K-BOT endpoints**: `/api/kbot/session`, `/api/kbot/chat`, `/api/kbot/upload`, `/api/kbot/teaser`, `/api/kbot/generate-pdf`, `/api/report/pdf`, `/api/report/docx` are anonymous and trigger paid Anthropic API calls and/or heavy Puppeteer PDF/DOCX generation. No global rate limit.
- **MEDIUM — `/api/kbot/cleanup` is unauthenticated by default**: if neither `CLEANUP_SECRET_KEY` nor `CRON_SECRET` is set, the bearer check is skipped (`if (acceptedKey) { … }`) and any caller can wipe sessions and files.
- **MEDIUM — CSP drift**: `server.js` allows `'unsafe-inline'` for scripts and styles (and `connect-src https: wss:` wildcard), while `vercel.json` enforces strict `'self'`. Because Railway is the live host, the looser policy is what reaches users.
- **MEDIUM — Generated PDFs are uploaded with `public: true`** on a Supabase bucket (`kbot-reports`) and surfaced through `getPublicUrl`. URLs are guessable by `sessionId` + `Date.now()`; if leaked through any log/referrer they expose PII paid reports.
- **LOW — Container runs as root** (no `USER` directive in `Dockerfile`).

The rest of the surface is reasonable: Stripe webhook signature is verified in the live path (`kbot/backend/app/api/webhook.py`); Supabase service-role key is server-only; static-file path traversal is mitigated; HSTS and the main security headers are emitted.

## Attack Surface

Routes exposed by `server.js` (Railway prod) and `api/` (Vercel):

| Path | Method | Handler / file | Auth | Notes |
|---|---|---|---|---|
| `/` and `*.html` | GET | `server.js:serveFile` | none | Static dist serving |
| `/api/newsletter/subscribe` | POST | `server.js:handleNewsletterSubscribe` | none + email validation | Sends Resend confirmation; no rate limit |
| `/api/newsletter/confirm` | GET | `server.js:handleNewsletterConfirm` | token in query (≥32 chars) | Single-use, OK |
| `/api/newsletter/publish` | POST | `server.js:handleNewsletterPublish` | `INTERNAL_API_KEY` header OR hardcoded path token | **HIGH — static path token bypass** |
| `/api/newsletter/publish/<token>` | POST | same | hardcoded path token | **HIGH** |
| `/api/newsletter/admin/cleanup-tests/<token>` | POST | `server.js:handleNewsletterCleanupTests` | hardcoded path token | **HIGH** |
| `/api/newsletter/issues` | GET | `server.js:handleNewsletterIssues` | none | Public archive listing |
| `/api/newsletter/issue?slug=` | GET | `server.js:handleNewsletterIssue` | none | Returns raw HTML; rendered as innerHTML in client |
| `/api/report/pdf` | GET/POST | `server.js:handleReportPdf` | none | Heavy Puppeteer rendering, DoS surface |
| `/api/report/docx` | GET/POST | `server.js:handleReportDocx` | none | Heavy docx generation |
| `/api/kbot/*` and `/api/stripe/webhook` | * | `proxyKbotPython` → 127.0.0.1:8000 | depends on Python backend | Stripe sig verified server-side in Python |
| `/kbot/session`, `/kbot/message`, `/kbot/report` | * | `proxyKbotPython` (rewritten) | same | |
| `/suite-ai/services[/:id]` | GET | `server.js:handleSuiteAiServices` | none | Static catalogue |
| `/api/*` (other) | * | `proxyApiRequest` → `https://api.k2-ai.it` | passthrough | Forwards Authorization header upstream |
| `/app/*` | * | proxy to kbot standalone Next.js | none | Internal Next app |
| `/api/intake/contact` (Vercel) | POST | `api/intake/contact.ts` | honeypot only | **No rate limit** |
| `/api/kbot/checkout` (Vercel) | POST | `api/kbot/checkout.ts` | none, validates session row | Creates Stripe Checkout session |
| `/api/kbot/cleanup` (Vercel cron) | GET/POST | `api/kbot/cleanup.ts` | `CLEANUP_SECRET_KEY` or `CRON_SECRET` if set; otherwise none | **MEDIUM default-open** |
| `/api/stripe-webhook` (Vercel) | POST | `api/stripe-webhook.ts` | Stripe signature | OK; but likely unused in prod (Railway proxies to Python) |
| `/api/newsletter/publish` (Vercel) | POST | `api/newsletter/publish.ts` | `INTERNAL_API_KEY` header strict | OK (no path-token bypass in this variant) |

## Findings

### Critical

None confirmed. The closest is the combined risk of (a) hardcoded newsletter publish token + (b) `innerHTML` injection of newsletter HTML + (c) loose CSP on the Node server — together they constitute a usable stored-XSS chain. Classified as HIGH because it requires repo / build-artifact access OR a guessed 48-char hex token.

### High

**H-1 — Hardcoded `NEWSLETTER_PUBLISH_PATH_TOKEN` in source**
File: `kai-website/server.js:24`
```js
const NEWSLETTER_PUBLISH_PATH_TOKEN = 'c7f1b5cb492f8d744b041ce9507f246c8339367313de315a';
```
Used at lines 1278–1284 (publish) and 1411–1414 (cleanup-tests) to bypass `INTERNAL_API_KEY`. A static secret committed to a git repo is not a secret. Anyone with read access to the repository or to a built Docker image (it is baked into `server.js` shipped to the container) can:
- POST `/api/newsletter/publish/c7f1b5cb…` with arbitrary `html` and have it stored in `newsletter_issues`.
- POST `/api/newsletter/admin/cleanup-tests/c7f1b5cb…` to delete issues.

Fix: remove the path-token bypass entirely; require `INTERNAL_API_KEY` (and rotate the currently-leaked value in `.env`).

**H-2 — Stored XSS sink in newsletter renderer**
File: `kai-website/src/js/newsletter-entry.js:31`
```js
htmlNode.innerHTML = item.html || ''
```
`item.html` is server-stored text from the publish endpoint. Combined with H-1 it gives a turnkey stored-XSS on `https://www.k2-ai.it/newsletter-entry?slug=…`. Even without H-1, any future leak of `INTERNAL_API_KEY` or compromise of the n8n publishing workflow yields persistent XSS.

Fix options:
- Sanitize server-side at publish time (DOMPurify in Node, or an HTML allowlist) before storing.
- Sanitize client-side before injection.
- Or render newsletter content inside a `sandboxed` iframe with `srcdoc` + no `allow-scripts`.

**H-3 — CSP allows `'unsafe-inline'` on production host**
File: `kai-website/server.js:72-78`
```js
'Content-Security-Policy': "default-src 'self'; … script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; … connect-src 'self' https: wss:; …"
```
This is the policy users actually receive (Railway is live per `MEMORY.md`). It disables script-injection mitigation that `vercel.json` (`script-src 'self'`) carefully sets. Any innerHTML sink (H-2 or any future one) executes inline `<script>` payloads.

Fix: align with `vercel.json`. Remove `'unsafe-inline'` for `script-src` (move any required inline scripts to `'self'` files; use nonces for genuinely-inline ones). Tighten `connect-src` to the actual hosts in use.

**H-4 — Contact form has no rate limiting and acts as a Resend relay**
File: `kai-website/api/intake/contact.ts` (Vercel) and equivalent path through `proxyApiRequest` in `server.js`.
Only a honeypot field (`website`) is checked. After that, every well-formed POST triggers a Resend email to `KBOT_NOTIFY_EMAIL`. An attacker can:
- Flood the operator inbox.
- Burn Resend quota (3k/month free tier → tiny budget).
- Pivot the `reply-to: <attacker-controlled-email>` to send spear-phishing-flavored bodies looking like they originate from K2-AI.

Fix: add IP-based and email-based rate limiting (e.g., 5/min/IP, 20/hr/email) at the edge (Vercel/Cloudflare) or in-process; consider Turnstile/hCaptcha on the form.

**H-5 — Newsletter subscribe has no rate limiting and reveals enumeration**
File: `kai-website/server.js:1117-1221`, `kai-website/api/newsletter/subscribe.ts`.
Distinct responses: `{ ok: true, already: true }` vs `{ ok: true, resent: true }` vs `{ ok: true }` allow address enumeration (which addresses are already subscribed). No rate cap on per-IP signups → unlimited Resend invitations to arbitrary recipients (Resend bills for sent volume; this is an outbound spam vector).

Fix: unify response shape (`{ ok: true }`), rate limit per IP and per email, optionally require captcha.

**H-6 — Cost-amplification on unauthenticated K-BOT and report endpoints**
Files: `server.js` handlers `handleKbotSession`, `handleKbotChat`, `handleKbotUpload`, `handleKbotTeaser`, `handleKbotGenerateReport`, `handleReportPdf`, `handleReportDocx`.
All accept anonymous requests, persist data to Supabase, and invoke paid Anthropic API and/or Puppeteer rendering (60s function budget). A few hundred concurrent requests can:
- Burn the Anthropic budget (`KBOT_MODEL=claude-haiku-4-5`, `REPORT_MODEL=claude-sonnet-4-6`).
- Saturate Railway CPU through Puppeteer/Chromium spawns (`puppeteer-core` + `@sparticuz/chromium`).
- Fill `kbot-reports` Supabase bucket (public) with attacker-controlled PDFs.

Fix: token bucket / IP-based limiter, anonymous session quota (e.g., 3 message/session, 10 sessions/IP/hr), captcha before LLM call, and require an auth header on `/api/report/pdf` and `/api/report/docx`.

### Medium

**M-1 — `/api/kbot/cleanup` defaults open**
File: `kai-website/api/kbot/cleanup.ts:17-28`
```ts
const acceptedKey = cleanupKey || cronSecret
if (acceptedKey) {
  // check Authorization / x-cleanup-key
  if (incomingKey !== acceptedKey) return 401
}
// else: fall through, anyone can call
```
If both env vars are unset, the endpoint deletes K-BOT sessions and Supabase Storage files with no auth. Fail-closed instead.

Fix: `if (!acceptedKey) return 401;` then verify.

**M-2 — `kbot-reports` Supabase bucket is publicly readable**
File: `kai-website/server.js:1964-1982`
```js
const REPORTS_BUCKET = 'kbot-reports';
// …
await supabase.storage.createBucket(REPORTS_BUCKET, { public: true });
// …
const { data: publicData } = supabase.storage.from(REPORTS_BUCKET).getPublicUrl(fileName);
```
File names: `kbot-${sessionId}-${Date.now()}.pdf`. Session IDs are UUIDs (hard to brute), but URLs leak via referrer, mail clients, browser history. Treat paid reports as PII (they may contain bilancio data, contract content from uploads).

Fix: use signed URLs with short TTL (`createSignedUrl`), keep the bucket private.

**M-3 — Proxy forwards `Authorization` header to internal services**
File: `kai-website/server.js:109-133` (`proxyKbotPython`) and `157-183` (`proxyKbotStandalone`).
All `req.headers` are forwarded as-is. If the internal Python or Next process trusts headers like `x-forwarded-user`, `authorization`, or `cookie`, a client can spoof them. Currently this is hypothetical (Python backend uses Supabase + Stripe sig), but the proxy should strip hop-by-hop and auth-style headers it does not need.

Fix: forward only a small allow-list (content-type, content-length, accept, idempotency-key). Drop `authorization`, `cookie`, `x-forwarded-*`, custom internal keys.

**M-4 — `proxyApiRequest` blindly forwards client headers to `https://api.k2-ai.it`**
File: `kai-website/server.js:1001-1056`. Same concern as M-3; an internal API that trusts `x-internal-key` from upstream could be tricked by a malicious client header.

**M-5 — `handleKbotChat` returns raw upstream error text**
File: `kai-website/server.js:1639-1642`
```js
console.error('Anthropic API error in handleKbotChat:', aiErr);
return sendJson(res, 500, { error: `Errore AI: ${aiErr instanceof Error ? aiErr.message : String(aiErr)}` });
```
Anthropic SDK errors can include the model name, partial request ID, sometimes header fragments. Low value, low risk, but it is a defense-in-depth issue.

Fix: log internally, return a generic `{ error: 'Errore AI' }` to the client.

**M-6 — CSP `connect-src https: wss:` in `server.js` is unrestricted**
File: `kai-website/server.js:73`. With XHR/fetch open to any HTTPS endpoint, an injected script can exfiltrate easily. Tighten to the small set of hosts actually needed (`https://api.k2-ai.it`, `https://*.stripe.com`).

**M-7 — Newsletter publish path uses path token, not Authorization**
Path tokens leak via referrer, browser history, server access logs, and CDN logs in a way Authorization headers do not. Even if H-1 is fixed (hardcoded constant), the publish endpoint should never accept a token in the URL.

**M-8 — Anthropic API key trust scope**
`createAnthropicClient()` reads `ANTHROPIC_API_KEY` at request time. Anonymous endpoints can drive arbitrary prompts to Anthropic. A prompt-injection attack against the K-BOT system prompt could try to use the model for nuisance generation. Cost cap is the main mitigation; LLM-side guardrails (Anthropic per-key limits) should also be set.

**M-9 — `pdf-parse` and Chromium/Puppeteer DoS surface**
`pdf-parse@^2.4.5` historically had ReDoS in PDF text extraction; combined with `@sparticuz/chromium@^148` and `puppeteer-core@^24.42` the report-generation path runs untrusted-content rendering. The 60s Vercel timeout and 4MB per-file upload cap are partial mitigation; still classify the surface as medium until upstream CVEs are tracked.

### Low

**L-1 — Container runs as root** — `Dockerfile` has no `USER` directive; the Node process runs as UID 0 with full filesystem access. Add `USER node` (Debian-slim base ships with that user).

**L-2 — HSTS only emitted in production** — `applySecurityHeaders` (server.js:202-204) guards HSTS on `NODE_ENV === 'production'`. Acceptable, just call it out.

**L-3 — `connect-src` in Vite preview includes private LAN IPs** — `vite.config.js:14`. Fine for dev, but make sure preview is not exposed to the internet.

**L-4 — Inconsistent X-Frame-Options vs `frame-ancestors`** — `server.js` uses `X-Frame-Options: SAMEORIGIN` and `frame-ancestors 'self'`; `vercel.json` uses `DENY` + `'none'`. Pick one stance.

**L-5 — `escapeHtml` does not escape backticks** — currently safe because no template literal output paths exist; document the limitation.

### Informational

- **I-1** — No CSRF tokens. Mitigation: same-origin JSON POST with `'Content-Type: application/json'` triggers CORS preflight, and CORS on the only state-changing endpoint reachable cross-origin (newsletter subscribe) is locked to `https://www.k2-ai.it`. Acceptable for the threat model.
- **I-2** — `/admin` directory exists (`src/admin/`) but is empty; `vite.config.js` `blockSensitiveFallbacks` returns 404 for `/admin` in dev. Fine.
- **I-3** — Stripe webhook signature is verified in `kbot/backend/app/api/webhook.py:44-51` (the live path) and in `api/stripe-webhook.ts:33-37` (unused-on-Railway). Both correct.
- **I-4** — `internal_context` field on `/api/intake/contact` flows into outgoing email body. It is HTML-escaped, but be aware the operator's mailbox sees user-supplied text in a context where Outlook/Gmail may auto-link or auto-preview.
- **I-5** — `console.log/error` calls do not log secrets. `console.error('Newsletter insert error:', error)` etc. log Supabase error objects only.
- **I-6** — `.env` is in `.gitignore` and is not tracked. The plaintext `INTERNAL_API_KEY` visible on disk is expected for local dev; ensure that value differs from production and is rotated regularly.

## GDPR Compliance Gaps

- **G-1** — Newsletter signup stores email + name + IP-derived source without an explicit consent record (no checkbox event, no consent text version, no IP/timestamp tuple). Italian Garante guidance requires opt-in proof. Add a `consent_version`, `consent_text`, and store timestamp at insert.
- **G-2** — K-BOT sessions store rich PII (uploaded bilancio PDFs, business descriptions, emails, phone-like data) in `kbot_sessions.collected_data` and PDF reports in a public bucket. The 30/90-day TTL in `cleanup.ts` is reasonable but: (a) cleanup is best-effort (M-1 weakens it), (b) the public bucket means once-leaked stays leaked. Document the retention in the privacy policy and switch to signed URLs.
- **G-3** — `/api/intake/contact` forwards user-typed `internal_context` via email and writes nothing to DB; the receiving inbox (`KBOT_NOTIFY_EMAIL`) becomes a personal-data store outside the documented systems. Add a note in the privacy policy or shift to a DB-first model.
- **G-4** — Cookie banner / consent state — not reviewed here. Verify `/cookie.html` covers PostHog tracking and that PostHog is gated on consent (it appears initialized only if `VITE_POSTHOG_KEY` is set, but not on user consent — check the actual init path in `kbot-react-entry.tsx`).
- **G-5** — No documented data-export / deletion flow. Users contacting `info@k2-ai.it` is fine for Italian art. 15-22 GDPR rights, but a documented SLA in the privacy page is required.
- **G-6** — PII in logs: `console.error('Newsletter insert error:', error)` includes the Supabase error object which may echo the offending email under unique-constraint paths. Low risk, but explicit PII redaction in logs is GDPR-friendlier.

## NIS2 Considerations

K2A S.R.L.S. is below the NIS2 size thresholds, so direct obligations likely do not apply. Still:

- **N-1** — No structured incident log. Add a minimal table or external sink (e.g., Better Stack, Logtail) for `console.error` events.
- **N-2** — Supply-chain: 14 prod dependencies, including heavy ones (`@react-pdf/renderer`, `puppeteer-core`, `@sparticuz/chromium`, `three`, `react@19`). Pin versions in `package-lock.json` (already done), enable Dependabot/Renovate, and add a CI step that fails on `npm audit --production` highs.
- **N-3** — Backups: customer-submitted leads currently live in (a) operator mailbox, (b) Supabase `kbot_sessions`. Confirm Supabase point-in-time recovery is enabled on the EU project.
- **N-4** — Document the recovery RPO/RTO for `kbot_sessions` and `newsletter_subscribers`. The retention windows (30/90 days) imply RPO ≤ 24h is fine.

## Dependency Risks

From `package.json`:

| Package | Version | Notes |
|---|---|---|
| `@anthropic-ai/sdk` | ^0.92.0 | Recent. Verify on each upgrade. |
| `@react-pdf/renderer` | ^4.5.1 | Heavy, but no recent known CVEs. |
| `@sparticuz/chromium` | ^148.0.0 | Chromium pin — track upstream CVEs aggressively. |
| `@supabase/supabase-js` | ^2.104.1 | Recent line; OK. |
| `docx` | ^9.6.1 | Generates DOCX; low-CVE history. |
| `pdf-parse` | ^2.4.5 | Watch for ReDoS in PDF text extraction. |
| `posthog-js` | ^1.371.2 | Frontend tracking — gate on consent. |
| `puppeteer-core` | ^24.42.0 | Spawn Chromium → DoS surface. |
| `react` / `react-dom` | ^19.2.5 | Recent. |
| `resend` | ^6.12.2 | Mailer; trust verified. |
| `stripe` | ^22.0.2 | Pinned to `'2026-03-25.dahlia'` API. |
| `three` | ^0.184.0 | Frontend 3D, isolated. |
| Override `svix` | ^1.92.2 | Stripe webhook lib's transitive sig lib — fine. |

Action items: enable `npm audit` in CI, add Dependabot, watch `@sparticuz/chromium` for Chromium 0-days, consider replacing `pdf-parse` with `pdfjs-dist` text extraction (Mozilla-maintained, better security posture).

## Recommended Remediation Priority

Priority 1 (do this week)
1. Remove `NEWSLETTER_PUBLISH_PATH_TOKEN` from `server.js`. Require `INTERNAL_API_KEY` only. Rotate the current value. (H-1)
2. Sanitize newsletter HTML at publish-time or render in a sandboxed iframe. (H-2)
3. Add IP-based rate limiting (Cloudflare or an in-process token bucket) to `/api/intake/contact`, `/api/newsletter/subscribe`, `/api/kbot/*`, `/api/report/*`. (H-4, H-5, H-6)
4. Make `/api/kbot/cleanup` fail-closed when no secret is configured. (M-1)

Priority 2 (this month)
5. Replace `kbot-reports` public bucket with private bucket + signed URLs. (M-2)
6. Align `server.js` CSP with `vercel.json`: drop `'unsafe-inline'` for scripts; tighten `connect-src`. (H-3, M-6)
7. Restrict proxy header forwarding to an allow-list; drop `Authorization`, `Cookie`, `x-internal-*`. (M-3, M-4)
8. Genericize K-BOT error responses; do not echo Anthropic SDK errors. (M-5)
9. Unify newsletter-subscribe response shape (no enumeration). (H-5 follow-up)

Priority 3 (this quarter)
10. Add `USER node` to the `Dockerfile`. (L-1)
11. Add a structured retention/consent record on `newsletter_subscribers` and `kbot_sessions`. (G-1, G-2)
12. Add Dependabot + `npm audit` in CI. (N-2)
13. Document data-subject-request flow in `/privacy.html`. (G-5)
14. Replace `pdf-parse` with `pdfjs-dist`-based extractor or sandbox PDF processing in a child process. (M-9)
