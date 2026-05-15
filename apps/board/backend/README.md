# K2-Board backend (Sprint 1)

FastAPI + Supabase Postgres skeleton for the rebuilt K2-Board.
Replaces `ai-board/` — single store, no Notion, no multi-agent theatre.

## Stack

- Python 3.12
- FastAPI + uvicorn
- Pydantic v2 + pydantic-settings
- Supabase service-role client (REST)
- Session-cookie auth (`itsdangerous` + bcrypt)
- Deploy: Docker → Railway, hostname `board.k2-ai.it`

## Layout

```
app/
  main.py             FastAPI app factory + router wiring + /health
  settings.py         pydantic-settings env loader
  auth.py             /api/auth/{login,logout,me} + require_auth dep
  deps.py             dependency re-exports
  db/client.py        lazy Supabase service-role client
  db/migrations/      SQL — Sprint 1: 001_initial_board.sql
  models/             Pydantic v2 schemas per resource
  api/                CRUD routers + /api/overview aggregate
  lib/logger.py       structured JSON logging
tests/test_health.py  boot + auth-gated smoke tests
```

## Resources

- `contacts` — anagrafica
- `leads`    — pipeline commerciale
- `tasks`    — todo
- `approvals`— draft AI in attesa
- `memos`    — memoria fact-based
- `meetings` — sync Google Calendar (Sprint successivo)
- `revenue_events` — sync Stripe (Sprint successivo)

Each exposes `GET /, POST /, GET /{id}, PATCH /{id}, DELETE /{id}` under `/api/<resource>`.

The dashboard aggregate lives at `GET /api/overview`.

## Local dev

```bash
cd apps/board/backend
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env  # then fill in SUPABASE_* + BOARD_PASSWORD_HASH

# Generate a bcrypt hash for BOARD_PASSWORD_HASH:
.venv/bin/python -c "import bcrypt; print(bcrypt.hashpw(b'YOURPW', bcrypt.gensalt()).decode())"

# Generate a session secret:
.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(48))"

.venv/bin/uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs.

## Run tests

```bash
.venv/bin/python -m pytest tests/ -v
```

Tests do **not** hit Supabase — they only verify boot, auth gating, and that
all expected routes are wired into the OpenAPI schema.

## Apply DB migration

The migration file is not auto-applied. Paste
`app/db/migrations/001_initial_board.sql` into the Supabase SQL editor and run.
It is idempotent (`create table if not exists`, `do $$ ... duplicate_object`)
so it can be re-run safely.

After applying, verify:

```sql
select tablename, rowsecurity from pg_tables
where schemaname='public'
  and tablename in ('contacts','leads','tasks','approvals','memos','meetings','revenue_events');
-- rowsecurity must be `t` for every row.
```

## Deploy (Railway)

```bash
railway up --detach
```

`railway.toml` uses the `Dockerfile` builder and health-checks `/health`.

## What is NOT in Sprint 1

- Frontend (Next.js + Tailwind PWA) — Sprint 2
- Giuseppina AI agent + Anthropic tool calling — Sprint 3+
- Stripe webhook + Google Calendar sync jobs — Sprint 4
- K-BOT → lead automatic ingest — Sprint 4
