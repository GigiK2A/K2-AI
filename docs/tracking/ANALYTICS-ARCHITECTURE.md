# K2-AI — Analytics architecture

> Anonymous tracking via PostHog Cloud EU. No cookies, no localStorage, no PII
> in event properties. Storage in UE, retention 12 mesi (PostHog default).
> Honoriamo l'header `Do Not Track`.

## Data flow

```
  ┌─────────────────────────┐           ┌─────────────────────────┐
  │  Marketing site         │           │  K-BOT Next.js (/app)   │
  │  (Vite, vanilla JS)     │           │                          │
  │  src/js/analytics.js    │           │  src/lib/analytics.ts   │
  └────────────┬────────────┘           └────────────┬────────────┘
               │ posthog-js (browser, memory persistence)            │
               ▼                                                     ▼
                       ┌──────────────────────────────┐
                       │   PostHog Cloud EU           │
                       │   eu.i.posthog.com           │
                       │   GDPR — UE storage          │
                       └──────────────┬───────────────┘
                                      ▲
                                      │ python posthog SDK (server-side)
                                      │
                       ┌──────────────┴───────────────┐
                       │  K-BOT FastAPI backend       │
                       │  app/lib/analytics.py        │
                       └──────────────────────────────┘
                                      │
                                      │ HogQL query API (read-only, hourly cron)
                                      ▼
                       ┌──────────────────────────────┐
                       │  ai-board                    │
                       │  agents/scheduler_tasks/     │
                       │    posthog_sync.py           │
                       │  services/posthog_ingest.py  │
                       └──────────────┬───────────────┘
                                      │ insert
                                      ▼
                       ┌──────────────────────────────┐
                       │  Supabase                    │
                       │  analytics_snapshots         │
                       └──────────────┬───────────────┘
                                      │ select latest
                                      ▼
                       ┌──────────────────────────────┐
                       │  ai-board /analytics         │
                       │  (Jinja, tailwind dashboard) │
                       └──────────────────────────────┘
```

## Privacy & GDPR

- **Anonymous by default.** PostHog client uses `persistence: 'memory'` → no
  cookies, no localStorage; the `distinct_id` is a UUID that resets on every
  page reload. No user identification.
- **Server-side `distinct_id` = K-BOT session UUID.** Never a user id, email,
  or IP. The session UUID is already anonymous and aligns server and client
  events for the same K-BOT session.
- **No PII in properties.** We never send chat content, file contents,
  emails, names, IPs, or contact-form payloads. Properties are limited to:
  event names, counts, lengths, identifiers (`profile_id`, `mode`,
  `extraction_method`), domains (for URL fetches).
- **No session recording**, no autocapture.
- **Cookie banner not required** for the anonymous setup. If we ever enable
  cookie persistence or `identify()`, banner + Italian consent flow needed.
- **Storage in UE** (`eu.i.posthog.com`), retention 12 months (PostHog
  default plan).
- **DNT honored** via `respect_dnt: true`.

## Tracked events

### Marketing site (`kai-website`)

| Event              | Properties                                | Trigger |
|--------------------|-------------------------------------------|---------|
| `$pageview`        | auto (URL, referrer)                      | Page load (PostHog auto) |
| `profile_click`    | `profile_id` (P01..P20), `href`           | Any `[data-track-profile]` link click — set on the suite-ai service cards |
| `cta_click`        | `label`, `href`                           | Any `[data-track-cta]` element click |
| `kbot_open`        | `surface` (`home_widget` \| `k-bot_page`) | When the chat widget on `/` or `/k-bot` initializes |
| `kbot_message_sent`| `length`, `surface`                       | User submits a chat message via the legacy chat widget |
| `contact_submit`   | —                                          | Contact form HTTP 2xx response |
| `newsletter_signup`| `source`, `already`                       | Newsletter `/api/newsletter/subscribe` OK |

### K-BOT Next.js (`kbot/`)

| Event                  | Properties             | Trigger |
|------------------------|------------------------|---------|
| `$pageview`            | auto                   | Every navigation |
| `kbot_open`            | `surface: 'kbot_app'`  | Authenticated user mounts the chat surface |
| `kbot_message_sent`    | `length`, `mode`       | User submits a message |
| `kbot_report_requested`| `mode`                 | User clicks "genera report" (before Stripe checkout) |

### K-BOT backend (`kbot/backend`, server-side)

`distinct_id` = K-BOT session UUID.

| Event              | Properties                                     | Handler |
|--------------------|------------------------------------------------|---------|
| `session_created`  | `service_id`, `mode`, `authed`                 | `api/session.py::create_session` |
| `message_processed`| `role`, `tokens_in`, `tokens_out`, `model`     | `api/message.py::post_message` |
| `url_fetched`      | `domain`                                        | `api/fetch_url.py::post_fetch_url` |
| `file_uploaded`    | `extraction_method`, `mime`, `size_bytes`      | `api/upload.py::upload` |
| `report_generated` | `tier` (`paid` \| `test`), `test_mode`         | `api/generate_pdf.py::generate_pdf` |

## Setup steps

### 1. Create the PostHog project

1. Go to [eu.posthog.com](https://eu.posthog.com) and create an account.
   **Important**: pick the **EU** region (Frankfurt).
2. Create a project named `k2-ai`.
3. From Project settings, grab:
   - **Project API key** (`phc_…`) — used by the browser and the
     server-side Python SDK to write events.
   - **Project ID** — numeric, used by the read API.
4. In **Personal API keys**, create a new key with scopes:
   - `query:read`
   - `project:read`
   Copy the key (`phx_…`). This is used **only by ai-board** to read events
   back out for the dashboard.

### 2. Wire env vars

**`kai-website/.env.local`** (browser, write):
```
VITE_POSTHOG_KEY=phc_xxxxxxxxxxxxxxxx
VITE_POSTHOG_HOST=https://eu.i.posthog.com
```

**`kai-website/kbot/.env.local`** (Next.js client, write):
```
NEXT_PUBLIC_POSTHOG_KEY=phc_xxxxxxxxxxxxxxxx
NEXT_PUBLIC_POSTHOG_HOST=https://eu.i.posthog.com
```

**`kai-website/kbot/backend/.env.local`** (server, write):
```
POSTHOG_API_KEY=phc_xxxxxxxxxxxxxxxx
POSTHOG_HOST=https://eu.i.posthog.com
```

**`ai-board/.env`** (read, query API):
```
POSTHOG_PERSONAL_API_KEY=phx_xxxxxxxxxxxxxxxx
POSTHOG_PROJECT_ID=12345
POSTHOG_HOST=https://eu.i.posthog.com
SCHEDULER_POSTHOG_SYNC_CRON=0 * * * *
```

### 3. Apply the Supabase migration

```
psql $SUPABASE_DATABASE_URL -f ai-board/db/migrations/006_analytics_snapshots.sql
```

(or paste in the Supabase SQL editor)

### 4. Restart services

- Marketing site: `npm run build && npm run preview` (or Railway redeploy).
- K-BOT Next.js: redeploy.
- K-BOT backend: redeploy (the SDK is loaded lazily; missing key is a no-op).
- ai-board: restart so the scheduler picks up the new `posthog_sync` job.

### 5. Verify

- Open the site, click a suite-ai pillar. In PostHog → Activity, you should
  see `profile_click` within a few seconds.
- Wait one hour (or trigger the job manually) → check
  `select * from analytics_snapshots order by ts desc limit 1;` in Supabase.
- Visit `/analytics` on ai-board — last snapshot's rollup should be visible.

## Failure modes

All analytics calls are best-effort:

- Browser: `analytics.js` and `analytics.ts` no-op when keys are missing,
  swallow init/capture exceptions.
- Backend: `analytics.py` is a no-op without `POSTHOG_API_KEY`. Capture
  failures are silenced (logged at warning level only).
- ai-board: `posthog_sync` returns False on missing config / network errors
  and logs a warning. The dashboard renders an "no data" notice when no
  snapshot exists.

Analytics MUST NEVER break a chat turn, a report generation, or a page load.
