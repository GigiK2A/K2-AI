# Backend Audit
Date: 2026-05-16
Auditor: Senior Backend Engineer (audit-only, no code changes)
Scope: customer-facing backend — `kai-website/server.js` (Node) + `kai-website/kbot/backend/app/` (FastAPI). K2-Board excluded.

---

## Endpoint inventory

Routing dispatcher: `server.js:2548-2768`.

| Method | Path | Service | Auth | Rate limit | Validation | Notes |
|---|---|---|---|---|---|---|
| GET | `/api/health`, `/healthz` | Node server.js:2573 | none | none | n/a | Shallow: only `process.uptime()` + sentry flag. No DB ping, no Anthropic ping, no FastAPI subprocess ping. |
| POST | `/api/admin/alert` | Node server.js:2587/2440 | `INTERNAL_API_KEY` header (timing-safe) | 30/min per IP | manual (severity in {P0..P3}, event length 200, body 8KB) | OK |
| POST | `/api/newsletter/subscribe` | Node 2599/1258 | none | 3/5min per IP + 1/h per email | email regex + length | OK; reveals nothing on duplicate (200 ok) |
| GET | `/api/newsletter/confirm` | Node 2607/1376 | token query (≥32 chars) | none | min length only | No rate-limit on token brute force. Token is 64-hex from `crypto.randomBytes(32)`, brute force impractical. Acceptable. |
| POST/OPTIONS | `/api/newsletter/publish[/:pathToken]` | Node 2615/1408 | `INTERNAL_API_KEY` header OR path-token (timing-safe) | none | DOMPurify sanitize + length caps | High-value endpoint. **No rate-limit** — a leaked key can DoS Supabase / overwrite issues. |
| GET | `/api/newsletter/issues` | Node 2626/1516 | none | none | limit clamped 1..200 | Publicly readable archive — fine. |
| GET | `/api/newsletter/issue?slug=` | Node 2634/1542 | none | none | slug presence only | OK |
| POST | `/api/newsletter/admin/cleanup-tests/:pathToken` | Node 2642/1570 | path-token only | none | hardcoded slug LIKE pattern | OK (destructive but scoped) |
| POST/GET | `/api/report/pdf`, `/api/report/docx` | Node 2651/2335/2356 | none | 5/min per IP | none on body | **Anonymous Puppeteer / DOCX rendering allowed**. Free amplification: 5 calls/min/IP. POST accepts arbitrary 2MB `reportData` (rendered into PDF). Considered DoS-acceptable given 5/min cap. |
| ANY | `/api/kbot/*` | Proxy → FastAPI :8000 (server.js:2681 + `proxyKbotPython`) | depends on FastAPI handler | 20/min per IP at proxy | FastAPI Pydantic | See FastAPI table below |
| POST | `/api/stripe/webhook` | Proxy → FastAPI | Stripe signature | NO rate-limit (intentional) | Stripe SDK | OK |
| POST | `/api/intake/contact` | Proxy → `api.k2-ai.it` (`api/intake/contact.ts`) | none | 3/5min per IP + 1/h per email | length + email regex | **Error leaks raw exception**: `contact.ts:79` `return sendJson(res, 500, { detail: message })` — `message` is `error.message`, exposes Resend internals or stack. |
| GET | `/suite-ai/services[/:id]` | Node 2704/1701 | none | none | id in fixed map | OK |
| ANY | `/kbot/session`, `/kbot/message`, `/kbot/report` | Proxy → FastAPI (server.js:2712) | FastAPI | NO rate limit at proxy | FastAPI | **Inconsistent**: same logical endpoint reachable at `/api/kbot/*` (rate-limited) AND `/kbot/*` (unlimited). Rate-limit bypass. |
| ANY | `/api/*` (catch-all) | Proxy → `https://api.k2-ai.it` (server.js:2722/1142) | passthrough | none | none | Anything under `/api/` not matched above is forwarded to K2-Board. Could expose internal endpoints if the K2-Board API misroutes. |
| ANY | `/app/*` | Proxy → Next.js standalone (port 4174) | Next.js | none | none | Premium K-BOT UI |

### FastAPI K-BOT backend (`kai-website/kbot/backend/app/`)

All endpoints prefixed with `/api/kbot` except webhook.

| Method | Path | File:line | Auth | Rate limit | Validation | Notes |
|---|---|---|---|---|---|---|
| GET | `/health` | main.py:30 | none | none | n/a | Shallow `{ok, service, sentry}`. No DB ping. |
| POST | `/api/kbot/session` | session.py:29 | optional Bearer JWT (Supabase) | 20/min | Pydantic `CreateSessionBody` | Issues anon `link_token` via `secrets.token_urlsafe(32)` |
| GET | `/api/kbot/session/{id}` | session.py:59 | optional | none | path param | Owner enforcement |
| GET | `/api/kbot/sessions` | session.py:71 | required (`require_user`) | none | n/a | Lists user's sessions |
| POST | `/api/kbot/session/{id}/link-user` | session.py:95 | required | none | Pydantic | Claims anon session with link_token (H-6) |
| POST | `/api/kbot/message` | message.py:97 | optional + ownership | 30/min | Pydantic `MessageBody` | **No Anthropic timeout**, see C-1 |
| POST | `/api/kbot/upload` | upload.py:163 | optional + ownership | 10/min | Pydantic, 3MB per file | Bucket auto-create on first call; no per-session file count cap |
| POST | `/api/kbot/fetch-url` | fetch_url.py:31 | optional + ownership | 10/min | Pydantic | SSRF protections present (good) |
| POST | `/api/kbot/checkout` | checkout.py:47 | optional + ownership | **NONE** | Pydantic | **No rate-limit on Stripe Checkout creation** |
| POST | `/api/kbot/report` | report.py:26 | optional + ownership | **NONE** | Pydantic | Pure deterministic, low cost |
| POST | `/api/kbot/generate-pdf` | generate_pdf.py:41 | INTERNAL_API_KEY OR owner+(paid OR test_mode) | **NONE** | Pydantic | Heavy (Playwright + LLM). Edge proxy `/api/kbot/*` caps at 20/min but webhook can call repeatedly (idempotency check protects). |
| GET | `/api/kbot/status?id=` | status.py:11 | none | NONE | min_length=8 | **Session UUID exposes status + pdf_url to anyone who knows the id** — public bucket, but information disclosure |
| POST | `/api/stripe/webhook` | webhook.py:34 | Stripe signature | NONE | constructed from raw body | OK |

---

## Findings

### Critical (production blocker)

**C-1: No Anthropic SDK timeout configured (R1 confirmed).**
- `server.js:439` `new Anthropic({ apiKey })` — no `timeout` / `maxRetries`.
- `kbot/backend/app/api/message.py:132` `anthropic.Anthropic(api_key=…)` — same.
- `kbot/backend/app/api/upload.py:83`, `lib/analysis.py:170` — same.
- Anthropic SDK default is **10 minutes**. If the model hangs, Railway request worker blocks for 10 min, holding a Python uvicorn worker. Combined with no concurrency cap, a small burst of slow turns stalls all K-BOT users.
- Risk: customer abandons chat, support ticket "K-BOT non risponde". Already flagged in audit plan as R1.
- Fix: pass `timeout=60` (seconds) on every `Anthropic()` constructor, and surface 504/503 to the user with retry CTA.

**C-2: Rate-limit bypass via clean `/kbot/*` paths (server.js:2712-2720).**
- `/api/kbot/*` is rate-limited 20/min/IP (server.js:2672-2679).
- `/kbot/session`, `/kbot/message`, `/kbot/report` are proxied to the SAME FastAPI backend at server.js:2712 **with no rate-limit**.
- Slowapi rate-limit inside FastAPI uses `get_remote_address`, which sees `127.0.0.1` (the Node proxy) → effectively disabled / shared bucket.
- A single bad actor pasting `/kbot/message` instead of `/api/kbot/message` blows past the rate-limit and hammers Anthropic.
- Fix: Either remove these clean-path rewrites (FE already calls `/api/kbot/...`), or apply the same rate-limit there.

**C-3: SlowAPI rate-limit broken behind proxy (R4 confirmed and worse than documented).**
- `kbot/backend/app/lib/limiter.py:10` uses `get_remote_address` which inspects `request.client.host`. The Node proxy at `server.js:150` forwards headers but the source IP seen by FastAPI is always `127.0.0.1`.
- **Effect**: every authenticated and unauthenticated FastAPI rate-limit is a single global bucket. With 30/min on message, a single user spamming exhausts the limit for everyone.
- Fix: configure `Limiter(key_func=lambda r: r.headers.get("x-forwarded-for","").split(",")[0].strip() or get_remote_address(r))`. Already addressed at the Node edge (20/min per real IP) — but FastAPI's own per-route values (30/min message, 10/min upload, 10/min fetch-url, 20/min session) are not effective on per-IP basis.

**C-4: Anonymous Stripe Checkout endpoint, no rate-limit (`/api/kbot/checkout`, checkout.py:47).**
- No `@limiter.limit` decorator.
- Anyone with a session_id can mint Stripe Checkout Sessions repeatedly. Each call creates a server-side Stripe resource and consumes Stripe API quota.
- Edge proxy 20/min/IP gives some protection, but `/kbot/checkout` clean path is **not rate-limited** (C-2).
- Fix: add `@limiter.limit("5/minute")` + fix key_func.

### High (fix before launch)

**H-1: Exception messages leaked to clients.**
- `server.js:1814`: `sendJson(res, 500, { error: 'Errore AI: ${aiErr.message}' })`. Anthropic SDK error messages may include URL paths, request IDs, model names. Acceptable but reflects no-effort error UX.
- `server.js:2151`: `sendJson(res, 500, { error: 'Upload PDF fallito: ${uploadError.message}' })` — Supabase Storage internals leaked.
- `api/intake/contact.ts:79`: `return sendJson(res, 500, { detail: message })` where `message = error.message` — leaks Resend SDK errors, stack hints.
- `fetch_url.py:71`: `HTTPException(status_code=502, detail=f"Impossibile raggiungere l'URL: {exc}")` — leaks httpx exception text (could include resolved private IPs in pre-validation race window).
- `kbot/backend/app/api/message.py:142`: `HTTPException(status_code=502, detail=f"upstream error: {exc}")` — exposes Anthropic error verbatim.
- `kbot/backend/app/api/upload.py:197`: similar.
- Fix: log full error to Sentry / structured log; return generic message to client.

**H-2: K-BOT widget endpoint `/api/intake/kbot-chat` is undocumented and externally-dependent.**
- `src/js/chat.js:41` POSTs to `/api/intake/kbot-chat`. **No handler exists** in `server.js` and **no file in `api/intake/`**.
- Falls through to the catch-all `proxyApiRequest` (server.js:2722) which forwards to `https://api.k2-ai.it` (K2-Board, excluded from this audit).
- The home-page widget therefore depends on a separate service for chat. If that service is down → widget broken with generic "Errore di connessione" (`chat.js:406`).
- This is **inconsistent with the premium K-BOT** which uses local FastAPI `/api/kbot/message`. Two LLM code paths, two failure modes.
- Fix: verify api.k2-ai.it `/api/intake/kbot-chat` is supported, OR migrate the widget to the internal FastAPI route.

**H-3: ~520 LOC of dead code in `server.js` (handleKbotApi never dispatched).**
- `handleKbotApi(req, res, rawPath)` defined at server.js:2479, never invoked. The dispatcher at line 2668-2682 sends `/api/kbot/*` directly to FastAPI.
- Functions `handleKbotSession` (1711), `handleKbotChat` (1749, **with hardcoded `KBOT_MODEL` and broken error leak**), `handleKbotUpload` (1908), `handleKbotTeaser` (1975), `handleKbotContact` (2047), `handleKbotGenerateReport` (2064), `handleKbotStructuredReport` (2174), `handleKbotReport` (2238), `handleKbotStatus` (2256) — all dead.
- Risk: code drift, security review burden, duplicate maintenance, and **if someone wires the dispatcher accidentally, exposes endpoints that don't enforce auth/ownership** (e.g. `handleKbotChat` has no link_token check).
- Fix: delete the dead block.

**H-4: Public `/api/kbot/status` allows session UUID enumeration.**
- `status.py:11`: only `min_length=8`. No auth, no link_token. Anyone with a session UUID gets `{ status, pdf_url }` which leaks if a session is paid + the public Supabase Storage URL.
- The bucket is intentionally public, but discovering paid status of arbitrary IDs is information disclosure. Combined with predictable storage path `kbot-{id}-{ts}.pdf`, the URL is effectively unguarded.
- Fix: require `link_token` (anon) or owner JWT.

**H-5: `/api/report/pdf` and `/api/report/docx` accept arbitrary user-supplied report data anonymously.**
- `server.js:2342` `const reportData = mockReportData || (isPlainObject(reportDataInput) ? reportDataInput : generateReportData({}))` — any anon caller can POST 2MB of JSON and trigger Puppeteer.
- Rate limit 5/min/IP exists, but Puppeteer cold-start can cost 1-2GB RAM. A botnet hitting from 50 IPs (5×50 = 250 PDFs/min) will OOM Railway.
- Fix: require either `mockReportId` (controlled set) or a valid kbot session_id; cap concurrency at process level.

**H-6: `proxyApiRequest` catch-all forwards anything `/api/*` to external host (server.js:2722).**
- Falls back to `https://api.k2-ai.it` for any unmatched `/api/` path. If a typo introduces a new local route, requests transparently bypass to K2-Board.
- Risk: header forwarding includes Authorization (cookies stripped via `shouldForwardRequestHeader`, but Authorization is forwarded). Auth tokens could be replayed cross-service.
- Fix: explicit allow-list of proxied paths, 404 for unknown `/api/*`.

**H-7: In-memory rate-limit single-process (R4 — partial fix, full risk).**
- `server.js:233-255` documents the limitation. Railway today: 1 replica, so OK. The moment you scale to 2 replicas, every per-IP/email limit halves and the contact-form 1/h-per-email guard breaks.
- Fix at scale-out time: Redis (Upstash free tier) or Supabase counter table.

**H-8: Newsletter publish endpoint has no rate-limit.**
- `server.js:2615-2624` and handler at 1408. Auth-only (INTERNAL_API_KEY or path-token). Both keys live in env. If leaked, infinite write loop on Supabase `newsletter_issues` until quota hit.
- Fix: 60/h IP rate-limit.

### Medium (fix soon)

**M-1: Frontend `kbot-react-entry.tsx` uses session_id `00000000-0000-0000-0000-000000000000` for `/api/kbot/status` warmup.** Doesn't break anything but is a code smell and triggers a 404 log every page load.

**M-2: `validate_url` in `url_fetcher.py:96` does a non-cached `getaddrinfo` per request and again at each redirect.** Susceptible to DNS-rebinding race: the resolved IP at validation may differ from the IP actually connected by httpx. Mitigated by re-validation per hop but `httpx` doesn't reuse the resolved address.
- Fix: resolve once, pass the resolved IP to httpx via `connect_to` or use `httpx.Transport` with a `local_address` pin.

**M-3: Storage bucket creation race (upload.py:50 `_ensure_bucket`).** First call creates the bucket with `public=True`. If two requests race on a brand-new deploy, both may attempt creation; the second hits a duplicate error and the code handles it — OK. But the bucket is **public-by-default** which means every uploaded file (PDFs, base64-decoded user docs) is world-readable via signed-less public URL.
- Fix: change bucket to private, generate signed URLs server-side. Same for `kbot-reports` (server.js:2144 `public: true`).

**M-4: No graceful shutdown.** server.js spawns FastAPI + Next.js subprocesses (`startKbotPythonBackend`, `startKbotStandalone`). On SIGTERM Node exits and orphans the children (or they get killed by the container).
- Fix: SIGTERM handler that proxies signal to children with timeout, then exits.

**M-5: Long-running connections, no global timeout on Node http server.** `server.requestTimeout` and `keepAliveTimeout` are defaults. Slowloris-style attack possible (slowloris already largely mitigated by Railway's edge, but defense-in-depth missing).

**M-6: `handleKbotChat` in dead-code references `KBOT_MODEL = 'claude-haiku-4-5-20251001'` (server.js:36) — a model name that may already be deprecated.** If the dead path is ever reactivated it will 4xx silently. Tracking.

**M-7: CORS misconfig risk.** FastAPI `CORSMiddleware` allows `allow_origins=CORS_ORIGINS` (server-side list) + `allow_credentials=True` + `allow_methods=["*"]` + `allow_headers=["*"]`. The list correctly excludes `*` (settings.py:65). However Bearer tokens travel via Authorization header, not cookies, so allow_credentials is mostly cosmetic. OK.

**M-8: `_extract_token` accepts a raw token without "Bearer " prefix (auth.py:107).** Tolerant parsing — accepts `Authorization: <jwt>` without the scheme. Low risk but non-standard.

**M-9: Sentry not verified active in production.** `lib/logger.js:27` `if (SENTRY_DSN)` — silently no-op if missing. Audit checklist already flagged this. **REQUIRES MANUAL VERIFICATION** in Railway env.

**M-10: `handleKbotPython` proxy forwards `Host: 127.0.0.1:8000` header (server.js:150).** FastAPI's `request.base_url` in webhook handler then returns `http://127.0.0.1:8000/...` (webhook.py:30 `_internal_pdf_url`). This is intentional (server-to-server) but means **`x-internal-key` is sent in cleartext on the loopback interface** — OK on a single container, but if the webhook is ever externalized this becomes a leak.

**M-11: Supabase `single()` and PostgREST error handling inconsistent.**
- Most queries use `.single()`. If a row is missing returns PGRST116. The newsletter handler at server.js:1312 handles this, but `handleKbotChat` (dead), `handleKbotTeaser` (server.js:1982), and others assume `error || !session` → 404 unconditionally — fine.
- **REQUIRES MANUAL VERIFICATION**: do all queries on the live system hit RLS-allowing service-role? Service-role bypasses RLS, so yes.

### Low (nice to have)

**L-1: Health endpoint is "200 if process up", not "200 if dependencies healthy".** Document this so uptime monitors don't false-positive.

**L-2: `clientIp` (server.js:257) trusts `X-Forwarded-For` without validating proxy chain.** Acceptable behind Railway's TLS edge, but if direct internet access is ever permitted, this allows IP spoofing for rate-limit evasion.

**L-3: `readJsonBody` (server.js:1081) silently rejects bodies >16KB with generic `'Body too large'` error.** Caller catches but the response is whatever the caller chooses; some handlers (`handleNewsletterPublish`) override the cap to 4MB. Inconsistent.

**L-4: Anthropic API key check happens per-request via `createAnthropicClient()` (server.js:434-440)** instead of at boot. Startup never fails-fast if `ANTHROPIC_API_KEY` is missing.

**L-5: Server logs use `console.error` heavily** (e.g. server.js:1313 `console.warn('Newsletter lookup warning:', error)`) — not structured JSON. The `lib/logger.js` exists but isn't used consistently.

**L-6: `slowapi`'s `RateLimitExceeded` handler returns plain text `Too Many Requests` with status 429.** The frontend chat.js:390 only checks `res.status === 429` and shows generic text. OK but error body not consumed; could include `Retry-After`.

**L-7: PostHog and Sentry calls are best-effort but synchronous in some paths (e.g. `track_server` in message.py:148).** A slow PostHog endpoint adds latency to user-facing turn. PostHog client should be configured non-blocking.

---

## R-series risks (verification of plan)

| ID | Description | Status |
|---|---|---|
| R1 | Anthropic down → K-BOT fails | **CONFIRMED**. No SDK timeout, no fallback message variation. See C-1. |
| R2 | Stripe webhook secret missing | **HANDLED** — `webhook.py:39` returns 503 if missing. Stripe will retry; revenue tracking will be broken silently. |
| R3 | Supabase Auth email confirm OFF | Not in scope (frontend/auth config). |
| R4 | Rate-limit multi-instance | **WORSE THAN DOCUMENTED**. SlowAPI inside FastAPI already broken on **single** instance because remote_address = 127.0.0.1 from Node proxy. See C-3. |

---

## Production readiness score

**Backend: 5.5 / 10**

Breakdown:
- Routing structure: 7/10 — monolith but coherent, dead-code drag
- Validation: 7/10 — Pydantic on FastAPI good, server.js mixed
- Error handling: 4/10 — multiple leaks of internal errors, no Sentry capture wrappers
- Security headers / CSP: 9/10 — strong work
- Auth + session ownership: 8/10 — link_token model is good, dead-code path bypasses it
- Rate-limiting: 4/10 — broken at FastAPI layer, missing on checkout/publish/clean-paths
- External dep resilience: 3/10 — no Anthropic timeout, no Resend retry, no Stripe replay-resistance beyond signature check
- Observability: 6/10 — Sentry plumbed but unverified, logs partial
- Production hardening: 5/10 — no graceful shutdown, shallow health, in-memory rate-limit, monolith subprocess spawning

Verdict: **Not production-ready as-is for sustained traffic >10 RPS**. Acceptable for current single-customer pilot if C-1/C-2/C-3 are fixed and H-2 verified.

---

## Recommended fix priority

1. **C-1**: Anthropic SDK timeout=60s in all 4 client construction sites (server.js:439, message.py:132, upload.py:83, analysis.py:170).
2. **C-3**: Fix SlowAPI `key_func` to read `X-Forwarded-For` so per-route rate-limits actually apply per-user.
3. **C-2**: Remove `/kbot/*` clean paths or rate-limit them identically.
4. **H-2**: Verify `https://api.k2-ai.it/api/intake/kbot-chat` is supported in production and add a /healthz dependency check.
5. **H-3**: Delete ~520 LOC of dead K-BOT handlers in server.js (1604-2266 minus utilities used elsewhere). Reduces audit surface and removes auth-less duplicate paths.
6. **H-1**: Wrap all 5xx returns in a `genericServerError(res, err, ctx)` that captures to Sentry and returns `{ error: 'Errore temporaneo' }`.
7. **C-4 / H-8**: Add `@limiter.limit` on `/api/kbot/checkout` and IP rate-limit on `/api/newsletter/publish`.
8. **H-4**: Require link_token or owner JWT on `/api/kbot/status`.
9. **H-5**: Restrict `/api/report/pdf`/`docx` to known session_id or mockReportId.
10. **H-6**: Convert `proxyApiRequest` catch-all to an explicit allow-list.
11. **M-3**: Move `kbot-uploads` / `kbot-reports` buckets to private + signed URLs.
12. **M-4**: SIGTERM handler in server.js to forward to children.
13. **M-9 / L-4**: Verify Sentry DSN set in Railway; fail-fast on missing critical env vars at boot.
14. **R4** (long-term): Redis-backed rate-limiter for horizontal scaling.

---

## Things verified OK

- Stripe webhook signature verification (`webhook.py:43-51`) — solid, with proper 400 on mismatch and idempotency check at line 68.
- SSRF protection in `url_fetcher.py` — comprehensive: scheme allow-list, blocked-hosts regex, blocked ports, IPv4+IPv6 private-range check via `ipaddress`, per-redirect-hop re-validation.
- Newsletter HTML sanitization via DOMPurify with strict tag/attr allow-list (`server.js:17-26`).
- Session link_token model (H-6 hardening) — atomic claim with `secrets.compare_digest`, single-use (token nulled on claim) — `sessions.py:69-89`.
- Stripe success_token (H-7) — opaque, no session UUID in success URL (`checkout.py:73-76`).
- CSP — strict on marketing pages (`server.js:105`), relaxed appropriately for Next.js /app/ at line 329.
- HSTS only emitted in production (`server.js:342`).
- Path-token timing-safe comparison via `crypto.timingSafeEqual` (`server.js:1439`, `1580`).
- Stripe webhook explicitly excluded from rate-limit (`server.js:2672`) — correct.
- Pydantic v2 `populate_by_name = True` everywhere → supports both snake_case and camelCase from frontend.
- File upload size caps: 3MB per file (FastAPI upload.py:24), 24MB total body (dead path server.js:1911), 16KB JSON default (server.js:1081), 4MB newsletter publish (server.js:1425).
- Idempotency on Stripe webhook + on PDF generation (`webhook.py:68`, `generate_pdf.py:67`).
- Sentry plumbing present, fail-safe — never crashes the host (`logger.js:75-78`).
- CORS configured with explicit origin allow-list, never `*`+credentials (`settings.py:62-66`).
- JWT validation prefers JWKS (asymmetric ES256/RS256), falls back to legacy HS256 (`auth.py:50-87`).

---

## Items requiring manual verification

- **MV-1**: Is `SENTRY_DSN` set in Railway prod env? Logger silently no-ops without it.
- **MV-2**: Is `STRIPE_WEBHOOK_SECRET` set and matches the live Stripe webhook? If absent, 503 returned silently → revenue tracking broken (R2).
- **MV-3**: Does `https://api.k2-ai.it/api/intake/kbot-chat` exist and is it the same backend audited here, or a separate Vercel deployment? (H-2)
- **MV-4**: Are `kbot-uploads` and `kbot-reports` Supabase buckets currently `public=true` in prod? (M-3)
- **MV-5**: Is `NEWSLETTER_PUBLISH_PATH_TOKEN` rotated since the leak documented at server.js:46?
- **MV-6**: Verify Railway runs a single replica (in-memory rate-limit only works if scale=1).
