# KBot Production Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aggiungere Clerk auth, Stripe one-time payment, Supabase memory, rate limiting, analytics, feedback e UI polish al kbot report premium.

**Architecture:** Clerk gestisce l'identità (Google/Apple/email) e porta `has_paid` nel JWT. Stripe sblocca i download via webhook → Clerk metadata. Supabase sostituisce `chat_memory.json` per utenti loggati. Tutti i moduli nuovi sono file separati importati da `main.py`.

**Tech Stack:** `@clerk/nextjs`, `stripe` (Python + JS), `supabase-py`, `PyJWT[crypto]`, FastAPI middleware, Next.js 16 middleware

---

## File Map

**Nuovi file backend:**
- `backend/app/auth.py` — verifica JWT Clerk, estrae `clerk_user_id` e `has_paid`
- `backend/app/rate_limit.py` — rate limiter in-memory per IP e user
- `backend/app/supabase_client.py` — client Supabase + funzioni memoria conversazioni
- `backend/app/analytics.py` — `track_event()` fire-and-forget
- `backend/app/stripe_routes.py` — checkout session + webhook handler

**Nuovi file frontend:**
- `src/middleware.ts` — Clerk middleware: protegge route report
- `src/components/auth/AuthGate.tsx` — gate: non loggato → SignIn
- `src/components/report/FeedbackWidget.tsx` — stelle + campo testo post-report
- `supabase/migrations/001_init.sql` — crea tabelle conversations, analytics_events, feedback

**File modificati:**
- `backend/app/main.py` — import nuovi moduli, nuovi endpoint, clerk_user_id in chat
- `backend/requirements.txt` — aggiunge supabase, stripe, PyJWT[crypto]
- `backend/.env` — aggiunge tutte le nuove variabili
- `src/app/layout.tsx` — wrappa con ClerkProvider
- `src/app/page.tsx` — passa token Clerk in header, AuthGate, FeedbackWidget
- `src/lib/api.ts` — header Authorization, checkout, feedback
- `src/types/chat.ts` — FeedbackPayload type
- `src/components/layout/ChatLayout.tsx` — aggiunge UserButton Clerk
- `src/components/chat/MessageBubble.tsx` — payment gate sui download
- `.env.local` — variabili frontend Clerk + Stripe

---

## Task 1: Setup dipendenze e variabili d'ambiente

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/.env`
- Modify: `.env.local`

- [ ] **Step 1: Installa dipendenze Python**

```bash
cd backend
source .venv/bin/activate
pip install supabase==2.15.0 stripe==12.3.0 "PyJWT[crypto]==2.10.1"
pip freeze | grep -E "supabase|stripe|PyJWT" >> requirements.txt
```

Verifica che `requirements.txt` contenga le 3 righe:
```
PyJWT[crypto]==2.10.1
stripe==12.3.0
supabase==2.15.0
```

- [ ] **Step 2: Installa dipendenze npm**

```bash
cd /Volumes/PARASSITA/kbot
npm install @clerk/nextjs@latest @stripe/stripe-js@latest
```

- [ ] **Step 3: Aggiungi variabili backend** in `backend/.env`:

```env
# Clerk
CLERK_SECRET_KEY=sk_test_...
CLERK_JWKS_URL=https://YOUR_CLERK_FRONTEND_API/.well-known/jwks.json

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...

# Supabase
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Frontend URL (per redirect Stripe e link email)
FRONTEND_URL=http://localhost:3000
RESEND_API_KEY=re_...
REPORT_FROM_EMAIL=report@k2-ai.it
```

- [ ] **Step 4: Aggiungi variabili frontend** in `.env.local`:

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add supabase, stripe, PyJWT dependencies"
```

---

## Task 2: Supabase — schema DB

**Files:**
- Create: `supabase/migrations/001_init.sql`

- [ ] **Step 1: Crea la directory e il file SQL**

```bash
mkdir -p /Volumes/PARASSITA/kbot/supabase/migrations
```

Crea `supabase/migrations/001_init.sql`:

```sql
-- Memoria conversazioni report premium (per utenti Clerk loggati)
CREATE TABLE IF NOT EXISTS conversations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id   TEXT NOT NULL,
  conversation_id TEXT NOT NULL,
  role            TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content         TEXT NOT NULL,
  context_files   JSONB DEFAULT '[]',
  ts              TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS conversations_user_conv_ts
  ON conversations (clerk_user_id, conversation_id, ts);

-- Analytics eventi
CREATE TABLE IF NOT EXISTS analytics_events (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type    TEXT NOT NULL,
  clerk_user_id TEXT,
  session_id    TEXT,
  payload       JSONB DEFAULT '{}',
  ts            TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS analytics_events_type_ts
  ON analytics_events (event_type, ts);

-- Feedback report
CREATE TABLE IF NOT EXISTS feedback (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id TEXT,
  report_id     TEXT,
  rating        INT CHECK (rating BETWEEN 1 AND 5),
  comment       TEXT,
  ts            TIMESTAMPTZ DEFAULT now()
);
```

- [ ] **Step 2: Esegui la migrazione su Supabase**

Vai su Supabase Dashboard → SQL Editor, incolla il contenuto di `001_init.sql` ed esegui.

Oppure via CLI se configurato:
```bash
supabase db push
```

- [ ] **Step 3: Commit**

```bash
git add supabase/
git commit -m "feat: supabase schema — conversations, analytics_events, feedback"
```

---

## Task 3: Backend — auth.py (verifica JWT Clerk)

**Files:**
- Create: `backend/app/auth.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Scrivi il test che fallisce**

Crea `backend/tests/test_auth.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from app.auth import extract_clerk_user, ClerkUser


def test_extract_clerk_user_no_token():
    result = extract_clerk_user(None)
    assert result is None


def test_extract_clerk_user_invalid_token():
    result = extract_clerk_user("invalid.token.here")
    assert result is None


def test_extract_clerk_user_valid_token():
    mock_payload = {
        "sub": "user_abc123",
        "public_metadata": {"has_paid": True},
    }
    with patch("app.auth._decode_token", return_value=mock_payload):
        result = extract_clerk_user("valid.jwt.token")
    assert result is not None
    assert result.clerk_user_id == "user_abc123"
    assert result.has_paid is True


def test_extract_clerk_user_no_payment():
    mock_payload = {
        "sub": "user_xyz",
        "public_metadata": {},
    }
    with patch("app.auth._decode_token", return_value=mock_payload):
        result = extract_clerk_user("valid.jwt.token")
    assert result is not None
    assert result.has_paid is False
```

- [ ] **Step 2: Esegui il test — deve fallire**

```bash
cd backend && source .venv/bin/activate
pytest tests/test_auth.py -v
```
Expected: `ModuleNotFoundError: No module named 'app.auth'`

- [ ] **Step 3: Implementa `backend/app/auth.py`**

```python
from __future__ import annotations

import os
from dataclasses import dataclass

import jwt
from jwt import PyJWKClient


@dataclass
class ClerkUser:
    clerk_user_id: str
    has_paid: bool


_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        url = os.getenv("CLERK_JWKS_URL", "")
        if not url:
            raise RuntimeError("CLERK_JWKS_URL non configurato")
        _jwks_client = PyJWKClient(url, cache_keys=True)
    return _jwks_client


def _decode_token(token: str) -> dict | None:
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_exp": True},
        )
    except Exception:
        return None


def extract_clerk_user(token: str | None) -> ClerkUser | None:
    if not token:
        return None
    payload = _decode_token(token)
    if not payload:
        return None
    clerk_user_id = payload.get("sub")
    if not clerk_user_id:
        return None
    meta = payload.get("public_metadata") or payload.get("publicMetadata") or {}
    has_paid = bool(meta.get("has_paid", False))
    return ClerkUser(clerk_user_id=clerk_user_id, has_paid=has_paid)


def extract_token_from_header(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization[7:]
```

- [ ] **Step 4: Esegui i test — devono passare**

```bash
pytest tests/test_auth.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/app/auth.py backend/tests/test_auth.py
git commit -m "feat: Clerk JWT verification — extract_clerk_user, ClerkUser dataclass"
```

---

## Task 4: Backend — supabase_client.py

**Files:**
- Create: `backend/app/supabase_client.py`
- Test: `backend/tests/test_supabase_client.py`

- [ ] **Step 1: Scrivi il test che fallisce**

Crea `backend/tests/test_supabase_client.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from app.supabase_client import (
    get_conversation_memory_db,
    append_conversation_memory_db,
)


def _mock_supabase(rows=None):
    mock = MagicMock()
    mock.table.return_value.select.return_value.eq.return_value.eq.return_value \
        .order.return_value.limit.return_value.execute.return_value.data = rows or []
    mock.table.return_value.insert.return_value.execute.return_value.data = [{}]
    return mock


def test_get_conversation_memory_db_empty():
    with patch("app.supabase_client._client", _mock_supabase([])):
        result = get_conversation_memory_db("user_1", "conv_1")
    assert result == []


def test_get_conversation_memory_db_returns_rows():
    rows = [
        {"role": "user", "content": "ciao", "context_files": [], "ts": "2026-01-01"},
        {"role": "assistant", "content": "risposta", "context_files": [], "ts": "2026-01-01"},
    ]
    with patch("app.supabase_client._client", _mock_supabase(rows)):
        result = get_conversation_memory_db("user_1", "conv_1")
    assert len(result) == 2
    assert result[0]["role"] == "user"


def test_append_conversation_memory_db():
    mock = _mock_supabase()
    with patch("app.supabase_client._client", mock):
        append_conversation_memory_db("user_1", "conv_1", "user", "testo", [])
    mock.table.return_value.insert.assert_called_once()
```

- [ ] **Step 2: Esegui il test — deve fallire**

```bash
pytest tests/test_supabase_client.py -v
```
Expected: `ModuleNotFoundError: No module named 'app.supabase_client'`

- [ ] **Step 3: Implementa `backend/app/supabase_client.py`**

```python
from __future__ import annotations

import os
from datetime import datetime, timezone

from supabase import create_client, Client

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY mancante")
        _client = create_client(url, key)
    return _client


def get_conversation_memory_db(clerk_user_id: str, conversation_id: str, limit: int = 40) -> list[dict]:
    try:
        client = _get_client()
        result = (
            client.table("conversations")
            .select("role, content, context_files, ts")
            .eq("clerk_user_id", clerk_user_id)
            .eq("conversation_id", conversation_id)
            .order("ts", desc=False)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def append_conversation_memory_db(
    clerk_user_id: str,
    conversation_id: str,
    role: str,
    content: str,
    context_files: list[str],
) -> None:
    try:
        client = _get_client()
        client.table("conversations").insert({
            "clerk_user_id": clerk_user_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content[:12000],
            "context_files": context_files,
            "ts": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception:
        pass
```

- [ ] **Step 4: Esegui i test — devono passare**

```bash
pytest tests/test_supabase_client.py -v
```
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/app/supabase_client.py backend/tests/test_supabase_client.py
git commit -m "feat: Supabase conversation memory — get/append functions"
```

---

## Task 5: Backend — rate_limit.py

**Files:**
- Create: `backend/app/rate_limit.py`
- Test: `backend/tests/test_rate_limit.py`

- [ ] **Step 1: Scrivi il test che fallisce**

Crea `backend/tests/test_rate_limit.py`:

```python
import time
import pytest
from app.rate_limit import RateLimiter


def test_rate_limiter_allows_under_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    assert limiter.is_allowed("key1") is True
    assert limiter.is_allowed("key1") is True
    assert limiter.is_allowed("key1") is True


def test_rate_limiter_blocks_over_limit():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    limiter.is_allowed("key2")
    limiter.is_allowed("key2")
    assert limiter.is_allowed("key2") is False


def test_rate_limiter_different_keys_independent():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    limiter.is_allowed("keyA")
    assert limiter.is_allowed("keyA") is False
    assert limiter.is_allowed("keyB") is True


def test_rate_limiter_seconds_until_reset_positive_when_blocked():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    limiter.is_allowed("key3")
    limiter.is_allowed("key3")
    secs = limiter.seconds_until_reset("key3")
    assert secs > 0
    assert secs <= 60
```

- [ ] **Step 2: Esegui il test — deve fallire**

```bash
pytest tests/test_rate_limit.py -v
```
Expected: `ModuleNotFoundError: No module named 'app.rate_limit'`

- [ ] **Step 3: Implementa `backend/app/rate_limit.py`**

```python
from __future__ import annotations

import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._store: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = self._store[key]
        self._store[key] = [t for t in timestamps if t > window_start]
        if len(self._store[key]) >= self.max_requests:
            return False
        self._store[key].append(now)
        return True

    def seconds_until_reset(self, key: str) -> int:
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = [t for t in self._store[key] if t > window_start]
        if not timestamps:
            return 0
        oldest = min(timestamps)
        return max(0, int(self.window_seconds - (now - oldest)) + 1)


# Istanze globali
anon_limiter = RateLimiter(max_requests=20, window_seconds=3600)   # 20/ora per IP
user_limiter = RateLimiter(max_requests=30, window_seconds=3600)   # 30/ora per user
```

- [ ] **Step 4: Esegui i test — devono passare**

```bash
pytest tests/test_rate_limit.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/app/rate_limit.py backend/tests/test_rate_limit.py
git commit -m "feat: in-memory rate limiter — 20req/h anon, 30req/h authenticated"
```

---

## Task 6: Backend — analytics.py

**Files:**
- Create: `backend/app/analytics.py`

- [ ] **Step 1: Implementa `backend/app/analytics.py`**

```python
from __future__ import annotations

import asyncio
from typing import Any

from app.supabase_client import _get_client


async def _insert_event(event_type: str, payload: dict, clerk_user_id: str | None, session_id: str | None) -> None:
    try:
        client = _get_client()
        client.table("analytics_events").insert({
            "event_type": event_type,
            "clerk_user_id": clerk_user_id,
            "session_id": session_id,
            "payload": payload,
        }).execute()
    except Exception:
        pass


def track_event(
    event_type: str,
    payload: dict[str, Any] | None = None,
    clerk_user_id: str | None = None,
    session_id: str | None = None,
) -> None:
    """Fire-and-forget: non blocca mai la risposta HTTP."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_insert_event(event_type, payload or {}, clerk_user_id, session_id))
        else:
            loop.run_until_complete(_insert_event(event_type, payload or {}, clerk_user_id, session_id))
    except Exception:
        pass
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/analytics.py
git commit -m "feat: analytics track_event — fire-and-forget Supabase insert"
```

---

## Task 7: Backend — stripe_routes.py

**Files:**
- Create: `backend/app/stripe_routes.py`
- Test: `backend/tests/test_stripe_routes.py`

- [ ] **Step 1: Scrivi il test che fallisce**

Crea `backend/tests/test_stripe_routes.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_checkout_requires_auth():
    res = client.post("/api/stripe/checkout")
    assert res.status_code == 401


def test_checkout_returns_url():
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/test_session"

    mock_user = MagicMock()
    mock_user.clerk_user_id = "user_test"
    mock_user.has_paid = False

    with patch("app.stripe_routes.stripe.checkout.Session.create", return_value=mock_session), \
         patch("app.auth.extract_clerk_user", return_value=mock_user):
        res = client.post(
            "/api/stripe/checkout",
            headers={"Authorization": "Bearer fake_token"},
        )
    assert res.status_code == 200
    assert res.json()["url"] == "https://checkout.stripe.com/test_session"
```

- [ ] **Step 2: Esegui il test — deve fallire**

```bash
pytest tests/test_stripe_routes.py -v
```
Expected: FAIL (route non esiste)

- [ ] **Step 3: Implementa `backend/app/stripe_routes.py`**

```python
from __future__ import annotations

import os

import stripe
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.auth import extract_clerk_user, extract_token_from_header

router = APIRouter()


def _get_stripe():
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    return stripe


@router.post("/api/stripe/checkout")
async def create_checkout(authorization: str | None = Header(None)):
    token = extract_token_from_header(authorization)
    user = extract_clerk_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Login richiesto")
    if user.has_paid:
        raise HTTPException(status_code=400, detail="Hai già accesso ai download")

    price_id = os.getenv("STRIPE_PRICE_ID", "")
    if not price_id:
        raise HTTPException(status_code=500, detail="Stripe non configurato")

    _get_stripe()
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{frontend_url}?payment=success",
        cancel_url=f"{frontend_url}?payment=cancelled",
        metadata={"clerk_user_id": user.clerk_user_id},
    )
    return JSONResponse({"url": session.url})


@router.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        _get_stripe()
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except stripe.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Firma webhook non valida")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        clerk_user_id = session.get("metadata", {}).get("clerk_user_id")
        if clerk_user_id:
            import httpx, asyncio
            clerk_secret = os.getenv("CLERK_SECRET_KEY", "")
            async with httpx.AsyncClient() as c:
                await c.patch(
                    f"https://api.clerk.com/v1/users/{clerk_user_id}/metadata",
                    headers={"Authorization": f"Bearer {clerk_secret}"},
                    json={"public_metadata": {"has_paid": True}},
                )

    return JSONResponse({"received": True})
```

- [ ] **Step 4: Aggiungi `httpx` alle dipendenze**

```bash
cd backend && source .venv/bin/activate
pip install httpx==0.28.1
pip freeze | grep httpx >> requirements.txt
```

- [ ] **Step 5: Registra il router in `main.py`**

In `backend/app/main.py`, dopo gli import esistenti aggiungi:

```python
from app.stripe_routes import router as stripe_router
```

Dopo `app = FastAPI(...)` e il middleware CORS, aggiungi:

```python
app.include_router(stripe_router)
```

- [ ] **Step 6: Esegui i test — devono passare**

```bash
pytest tests/test_stripe_routes.py -v
```
Expected: 2 PASSED

- [ ] **Step 7: Commit**

```bash
git add backend/app/stripe_routes.py backend/tests/test_stripe_routes.py backend/requirements.txt backend/app/main.py
git commit -m "feat: Stripe checkout + webhook — sblocca has_paid in Clerk metadata"
```

---

## Task 8: Backend — integra auth + rate limiting + Supabase in main.py

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Aggiungi import in cima a `main.py`**

Subito dopo i `from fastapi import ...` esistenti:

```python
from fastapi import Header
from app.auth import extract_clerk_user, extract_token_from_header, ClerkUser
from app.rate_limit import anon_limiter, user_limiter
from app.supabase_client import get_conversation_memory_db, append_conversation_memory_db
from app.analytics import track_event
```

- [ ] **Step 2: Modifica `ChatRequest` — aggiungi campo opzionale clerk token**

Il token viene dall'header `Authorization`, NON dal body. Nessuna modifica a `ChatRequest`.

- [ ] **Step 3: Modifica endpoint `chat` — aggiungi `Authorization` header**

Cambia la firma di `def chat(body: ChatRequest)` in:

```python
@app.post("/api/chat")
def chat(body: ChatRequest, request: Request, authorization: str | None = Header(None)):
```

In `main.py`, modifica la riga degli import FastAPI da:
```python
from fastapi import FastAPI, File, HTTPException, UploadFile
```
a:
```python
from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
```

- [ ] **Step 4: Aggiungi rate limiting + auth all'inizio del corpo di `chat()`**

Subito dopo `if not body.input.strip(): ...` aggiungi:

```python
    # Auth e rate limiting
    token = extract_token_from_header(authorization)
    clerk_user: ClerkUser | None = extract_clerk_user(token)
    clerk_user_id = clerk_user.clerk_user_id if clerk_user else None

    if body.mode == "report":
        if not clerk_user:
            raise HTTPException(status_code=401, detail="Login richiesto per il report premium")
        rate_key = clerk_user_id
        if not user_limiter.is_allowed(rate_key):
            secs = user_limiter.seconds_until_reset(rate_key)
            raise HTTPException(status_code=429, detail=f"Limite messaggi raggiunto. Riprova tra {secs} secondi.")
    else:
        ip = request.client.host if request.client else "unknown"
        if not anon_limiter.is_allowed(ip):
            secs = anon_limiter.seconds_until_reset(ip)
            raise HTTPException(status_code=429, detail=f"Limite messaggi raggiunto. Riprova tra {secs} secondi.")
```

- [ ] **Step 5: Rimuovi il gate `paid` e sostituisci con logica reale**

Sostituisci:
```python
    if body.mode == "report" and not body.paid:
        raise HTTPException(status_code=402, detail="Report premium bloccato: pagamento richiesto.")
```
Con (già gestito dallo step 4 — rimuovi semplicemente quella riga).

- [ ] **Step 6: Usa Supabase memory se utente loggato**

Dopo il blocco di auth, sostituisci le due righe:
```python
    history = get_conversation_memory(conversation_id)
    history_context = "\n".join(...)
```
Con:
```python
    if clerk_user_id and body.mode == "report":
        history = get_conversation_memory_db(clerk_user_id, conversation_id)
    else:
        history = get_conversation_memory(conversation_id)
    history_context = "\n".join(
        [f"{h.get('role', 'user')}: {str(h.get('content', ''))[:700]}" for h in history[-12:]]
    )
```

- [ ] **Step 7: Usa Supabase memory per append — sostituisci le ultime due righe**

Sostituisci:
```python
    append_conversation_memory(conversation_id, "user", body.input, body.context_files)
    append_conversation_memory(conversation_id, "assistant", answer, body.context_files)
```
Con:
```python
    if clerk_user_id and body.mode == "report":
        append_conversation_memory_db(clerk_user_id, conversation_id, "user", body.input, body.context_files)
        append_conversation_memory_db(clerk_user_id, conversation_id, "assistant", answer, body.context_files)
    else:
        append_conversation_memory(conversation_id, "user", body.input, body.context_files)
        append_conversation_memory(conversation_id, "assistant", answer, body.context_files)
```

- [ ] **Step 8: Aggiungi track_event nei punti chiave**

Dopo la riga `report_pdf = generate_report_pdf(...)` o `_run_hospitality_html_pipeline(...)`, aggiungi:
```python
                        if report_pdf:
                            track_event("report_generated", {"type": "generic"}, clerk_user_id, conversation_id)
```

Dopo `_run_hospitality_html_pipeline(...)`:
```python
                    if report_pdf:
                        track_event("report_generated", {"type": "hospitality"}, clerk_user_id, conversation_id)
```

- [ ] **Step 9: Proteggi i download endpoints con verifica `has_paid`**

Modifica `download_report_pdf` e `download_report_html`:

```python
@app.get("/api/reports/{report_id}/download")
def download_report_pdf(report_id: str, authorization: str | None = Header(None)):
    token = extract_token_from_header(authorization)
    user = extract_clerk_user(token)
    if not user or not user.has_paid:
        raise HTTPException(status_code=402, detail="Pagamento richiesto per scaricare il report")
    # ... resto invariato ...
```

Stessa modifica su `download_report_html`.

Aggiungi `track_event("download", {"format": "pdf"}, ...)` / `{"format": "html"}` prima del return.

- [ ] **Step 10: Riavvia backend e verifica**

```bash
cd backend && source .venv/bin/activate
lsof -ti:8000 | xargs kill -9 2>/dev/null; uvicorn app.main:app --reload --port 8000
```

Test rapido:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"input":"ciao","mode":"report","paid":true,"conversation_id":"test"}' 
# Expected: 401 Login richiesto
```

- [ ] **Step 11: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: auth + rate limiting + Supabase memory + analytics in chat endpoint"
```

---

## Task 9: Feedback endpoint

**Files:**
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_feedback.py`

- [ ] **Step 1: Scrivi il test che fallisce**

Crea `backend/tests/test_feedback.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_feedback_requires_auth():
    res = client.post("/api/feedback", json={"report_id": "r1", "rating": 5})
    assert res.status_code == 401


def test_feedback_invalid_rating():
    mock_user = MagicMock()
    mock_user.clerk_user_id = "user_1"
    with patch("app.auth.extract_clerk_user", return_value=mock_user):
        res = client.post(
            "/api/feedback",
            json={"report_id": "r1", "rating": 6},
            headers={"Authorization": "Bearer token"},
        )
    assert res.status_code == 422


def test_feedback_saves_ok():
    mock_user = MagicMock()
    mock_user.clerk_user_id = "user_1"
    mock_sb = MagicMock()
    mock_sb.table.return_value.insert.return_value.execute.return_value.data = [{}]
    with patch("app.auth.extract_clerk_user", return_value=mock_user), \
         patch("app.supabase_client._client", mock_sb):
        res = client.post(
            "/api/feedback",
            json={"report_id": "r1", "rating": 4, "comment": "ottimo"},
            headers={"Authorization": "Bearer token"},
        )
    assert res.status_code == 200
    assert res.json()["ok"] is True
```

- [ ] **Step 2: Esegui il test — deve fallire**

```bash
pytest tests/test_feedback.py -v
```
Expected: FAIL (route non esiste)

- [ ] **Step 3: Aggiungi `FeedbackRequest` e endpoint a `main.py`**

Aggiungi il modello dopo gli altri modelli Pydantic:

```python
class FeedbackRequest(BaseModel):
    report_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None
```

Aggiungi `Field` agli import pydantic: `from pydantic import BaseModel, EmailStr, Field`

Aggiungi l'endpoint:

```python
@app.post("/api/feedback")
def submit_feedback(body: FeedbackRequest, authorization: str | None = Header(None)):
    token = extract_token_from_header(authorization)
    user = extract_clerk_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Login richiesto")
    try:
        from app.supabase_client import _get_client
        _get_client().table("feedback").insert({
            "clerk_user_id": user.clerk_user_id,
            "report_id": body.report_id,
            "rating": body.rating,
            "comment": body.comment,
        }).execute()
    except Exception:
        pass
    track_event("feedback", {"rating": body.rating, "report_id": body.report_id}, user.clerk_user_id)
    return {"ok": True}
```

- [ ] **Step 4: Esegui i test — devono passare**

```bash
pytest tests/test_feedback.py -v
```
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/tests/test_feedback.py
git commit -m "feat: /api/feedback endpoint — rating + comment, Supabase storage"
```

---

## Task 10: Frontend — Clerk setup

**Files:**
- Modify: `src/app/layout.tsx`
- Create: `src/middleware.ts`

- [ ] **Step 1: Aggiorna `src/app/layout.tsx`**

```tsx
import type { Metadata } from "next";
import "./globals.css";
import { ClerkProvider } from "@clerk/nextjs";

export const metadata: Metadata = {
  title: "K2-AI Bot",
  description: "Assistente AI premium per lead generation e report professionali",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <ClerkProvider>
      <html lang="it">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  );
}
```

- [ ] **Step 2: Crea `src/middleware.ts`**

```ts
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/api/chat(.*)",   // il gate auth è nel backend, non qui
  "/api/skills(.*)",
  "/api/upload(.*)",
  "/api/leads(.*)",
  "/api/report-access(.*)",
  "/api/stripe/webhook(.*)",  // webhook Stripe non richiede auth Clerk
]);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) {
    await auth.protect();
  }
  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)", "/(api|trpc)(.*)"],
};
```

- [ ] **Step 3: Verifica TypeScript**

```bash
cd /Volumes/PARASSITA/kbot && npx tsc --noEmit
```
Expected: nessun errore

- [ ] **Step 4: Commit**

```bash
git add src/app/layout.tsx src/middleware.ts
git commit -m "feat: Clerk provider in layout + Next.js middleware"
```

---

## Task 11: Frontend — AuthGate e token negli API call

**Files:**
- Create: `src/components/auth/AuthGate.tsx`
- Modify: `src/lib/api.ts`
- Modify: `src/app/page.tsx`

- [ ] **Step 1: Crea `src/components/auth/AuthGate.tsx`**

```tsx
"use client";

import { SignInButton, useUser } from "@clerk/nextjs";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { isLoaded, isSignedIn } = useUser();

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center py-20 text-[var(--text-muted)] text-sm">
        Caricamento...
      </div>
    );
  }

  if (!isSignedIn) {
    return (
      <div className="k2-panel mx-auto mt-12 max-w-sm rounded-2xl p-8 text-center">
        <p className="mb-2 text-lg font-semibold">Report Premium</p>
        <p className="mb-6 text-sm text-[var(--text-soft)]">
          Accedi per usare il report premium. La chat è gratuita, i download richiedono un pagamento one-time.
        </p>
        <SignInButton mode="modal">
          <button className="w-full rounded-xl bg-[var(--teal)] py-3 text-sm font-semibold text-black">
            Accedi o registrati
          </button>
        </SignInButton>
      </div>
    );
  }

  return <>{children}</>;
}
```

- [ ] **Step 2: Modifica `src/lib/api.ts` — aggiungi `authToken` a `sendChat`**

Aggiorna la firma di `sendChat`:

```ts
export async function sendChat(
  input: string,
  mode: Mode,
  paid: boolean,
  conversationId: string,
  contextFiles: string[],
  authToken?: string | null,
): Promise<{ ... }> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify({ input, mode, paid, conversation_id: conversationId, context_files: contextFiles }),
  });
  // ... resto invariato
}
```

Aggiungi `startCheckout`:

```ts
export async function startCheckout(authToken: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/stripe/checkout`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${authToken}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Errore checkout");
  return data.url as string;
}

export async function submitFeedback(
  reportId: string,
  rating: number,
  comment: string,
  authToken: string,
): Promise<void> {
  await fetch(`${API_BASE}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
    body: JSON.stringify({ report_id: reportId, rating, comment }),
  });
}
```

- [ ] **Step 3: Modifica `src/app/page.tsx` — usa Clerk token + AuthGate**

Aggiungi import in cima:
```tsx
import { useAuth, useUser } from "@clerk/nextjs";
import { AuthGate } from "@/components/auth/AuthGate";
import { startCheckout, submitFeedback } from "@/lib/api";
```

Dentro `HomePage()`, aggiungi dopo gli useState:
```tsx
const { getToken } = useAuth();
const { user } = useUser();
const hasPaid = Boolean((user?.publicMetadata as { has_paid?: boolean })?.has_paid);
```

In `handleSubmit`, prima di `sendChat`:
```tsx
const authToken = mode === "report" ? await getToken() : null;
const res = await sendChat(prompt, mode, paid, activeConversation.id, filesForContext.map((f) => f.fileId), authToken);
```

Wrappa il contenuto del report mode con `<AuthGate>`:
```tsx
{mode === "report" && !paymentLink ? (
  <PremiumLock paymentLink={paymentLink} />
) : mode === "report" ? (
  <AuthGate>
    <AnimatePresence>
      {activeConversation.messages.map((m) => (
        <MessageBubble key={m.id} message={m} onCheckout={async () => {
          const token = await getToken();
          if (token) { const url = await startCheckout(token); window.location.href = url; }
        }} />
      ))}
    </AnimatePresence>
    {loading && <LoadingState />}
  </AuthGate>
) : (
  <AnimatePresence>
    {activeConversation.messages.map((m) => (
      <MessageBubble key={m.id} message={m} />
    ))}
  </AnimatePresence>
)}
```

- [ ] **Step 4: Verifica TypeScript**

```bash
npx tsc --noEmit
```
Expected: nessun errore (tranne eventuali prop `onCheckout` mancante — fix nel task successivo)

- [ ] **Step 5: Commit**

```bash
git add src/components/auth/ src/lib/api.ts src/app/page.tsx
git commit -m "feat: Clerk AuthGate, token negli API call, startCheckout"
```

---

## Task 12: Frontend — MessageBubble payment gate + FeedbackWidget

**Files:**
- Modify: `src/components/chat/MessageBubble.tsx`
- Create: `src/components/report/FeedbackWidget.tsx`
- Modify: `src/types/chat.ts`

- [ ] **Step 1: Aggiorna `src/types/chat.ts` — aggiungi `FeedbackPayload`**

Aggiungi dopo `ChatApiResponse`:

```ts
export type FeedbackPayload = {
  reportId: string;
  rating: number;
  comment: string;
};
```

- [ ] **Step 2: Crea `src/components/report/FeedbackWidget.tsx`**

```tsx
"use client";

import { useState } from "react";
import { Star } from "lucide-react";

export function FeedbackWidget({
  reportId,
  onSubmit,
}: {
  reportId: string;
  onSubmit: (rating: number, comment: string) => Promise<void>;
}) {
  const [rating, setRating] = useState(0);
  const [hover, setHover] = useState(0);
  const [comment, setComment] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  if (submitted) {
    return <p className="mt-3 text-xs text-[var(--text-muted)]">Grazie per il feedback!</p>;
  }

  return (
    <div className="mt-4 rounded-xl border border-[var(--line)] p-3">
      <p className="mb-2 text-xs text-[var(--text-soft)]">Come valuteresti questo report?</p>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => setRating(star)}
            onMouseEnter={() => setHover(star)}
            onMouseLeave={() => setHover(0)}
          >
            <Star
              size={18}
              className={(hover || rating) >= star ? "fill-[var(--teal)] text-[var(--teal)]" : "text-[var(--line)]"}
            />
          </button>
        ))}
      </div>
      {rating > 0 && (
        <>
          <textarea
            className="mt-2 w-full rounded-lg border border-[var(--line)] bg-transparent px-2 py-1.5 text-xs text-[var(--text-main)] placeholder:text-[var(--text-muted)] focus:outline-none"
            placeholder="Cosa miglioreresti? (opzionale)"
            rows={2}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          <button
            onClick={async () => {
              setLoading(true);
              await onSubmit(rating, comment);
              setSubmitted(true);
              setLoading(false);
            }}
            disabled={loading}
            className="mt-1.5 rounded-lg bg-[var(--teal)] px-3 py-1.5 text-xs font-semibold text-black disabled:opacity-50"
          >
            {loading ? "Invio..." : "Invia feedback"}
          </button>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Aggiorna `src/components/chat/MessageBubble.tsx` — payment gate + feedback**

Aggiorna la firma del componente:

```tsx
export function MessageBubble({
  message,
  onCheckout,
  onFeedback,
}: {
  message: ChatMessage;
  onCheckout?: () => Promise<void>;
  onFeedback?: (reportId: string, rating: number, comment: string) => Promise<void>;
}) {
```

Sostituisci il blocco dei bottoni download con:

```tsx
{(message.reportPdfDownloadUrl || message.reportHtmlUrl) && (
  <div className="mt-3 flex flex-wrap gap-2">
    {message.reportHtmlUrl && (
      <a href={`${API_BASE}${message.reportHtmlUrl}`} target="_blank" rel="noreferrer"
        className="inline-flex rounded-lg bg-[var(--teal)] px-3 py-2 text-xs font-semibold text-black">
        Apri report
      </a>
    )}
    {message.reportHtmlDownloadUrl && (
      message.hasPaid ? (
        <a href={`${API_BASE}${message.reportHtmlDownloadUrl}`} download
          className="inline-flex rounded-lg border border-[var(--teal)] px-3 py-2 text-xs font-semibold text-[var(--teal)]">
          Scarica HTML
        </a>
      ) : (
        <button onClick={onCheckout}
          className="inline-flex rounded-lg border border-[var(--teal)] px-3 py-2 text-xs font-semibold text-[var(--teal)]">
          Paga per scaricare HTML
        </button>
      )
    )}
    {message.reportPdfDownloadUrl && (
      message.hasPaid ? (
        <a href={`${API_BASE}${message.reportPdfDownloadUrl}`} target="_blank" rel="noreferrer" download={message.reportPdfFilename ?? undefined}
          className="inline-flex rounded-lg border border-[var(--line)] px-3 py-2 text-xs font-semibold text-[var(--text-soft)]">
          Scarica PDF
        </a>
      ) : (
        <button onClick={onCheckout}
          className="inline-flex rounded-lg border border-[var(--line)] px-3 py-2 text-xs font-semibold text-[var(--text-soft)]">
          Paga per scaricare PDF
        </button>
      )
    )}
  </div>
)}
{message.reportPdfUrl && onFeedback && (
  <FeedbackWidget
    reportId={message.reportPdfUrl.split("/").pop() ?? ""}
    onSubmit={(rating, comment) =>
      onFeedback(message.reportPdfUrl!.split("/").pop() ?? "", rating, comment)
    }
  />
)}
```

Aggiungi import `FeedbackWidget`:
```tsx
import { FeedbackWidget } from "@/components/report/FeedbackWidget";
```

- [ ] **Step 4: Aggiorna `ChatMessage` type — aggiungi `hasPaid`**

In `src/types/chat.ts` aggiungi a `ChatMessage`:
```ts
hasPaid?: boolean;
```

- [ ] **Step 5: Aggiorna `page.tsx` — passa `hasPaid` e `onFeedback` al MessageBubble**

`hasPaid` e `useUser` sono già stati aggiunti in Task 11 Step 3. Qui serve solo usarli nel mapping.

Nel mapping MessageBubble dentro AuthGate:
```tsx
<MessageBubble
  key={m.id}
  message={{ ...m, hasPaid }}
  onCheckout={async () => {
    const token = await getToken();
    if (token) { const url = await startCheckout(token); window.location.href = url; }
  }}
  onFeedback={async (reportId, rating, comment) => {
    const token = await getToken();
    if (token) await submitFeedback(reportId, rating, comment, token);
  }}
/>
```

- [ ] **Step 6: Verifica TypeScript**

```bash
npx tsc --noEmit
```
Expected: nessun errore

- [ ] **Step 7: Commit**

```bash
git add src/components/chat/MessageBubble.tsx src/components/report/FeedbackWidget.tsx src/types/chat.ts src/app/page.tsx
git commit -m "feat: payment gate sui download, FeedbackWidget post-report"
```

---

## Task 13: UI — UserButton header + nota privacy + badge Premium

**Files:**
- Modify: `src/components/layout/ChatLayout.tsx`
- Modify: `src/app/page.tsx`

- [ ] **Step 1: Aggiungi `UserButton` all'header in `ChatLayout.tsx`**

```tsx
import { UserButton } from "@clerk/nextjs";

// Aggiungi `isReportMode?: boolean` alle props
// Nel JSX, all'interno del div con `hidden items-center gap-2 md:flex`:
{isReportMode && <span className="inline-flex items-center gap-1 rounded-full bg-[var(--teal)]/10 border border-[var(--teal)]/30 px-2 py-1 text-xs text-[var(--teal)]"><Sparkles size={12} /> Premium</span>}
<UserButton afterSignOutUrl="/" />
```

Rimuovi il vecchio badge Premium hard-coded (riga `{mode === "report" && ...}`).

- [ ] **Step 2: Aggiungi nota privacy sotto la prima risposta report**

In `page.tsx`, dopo il primo messaggio assistant in report mode, mostra:

```tsx
{mode === "report" && activeConversation.messages.length <= 2 && (
  <p className="text-xs text-[var(--text-muted)] text-center px-4">
    Le tue conversazioni vengono salvate per continuare da dove hai lasciato. I documenti generati non vengono conservati sui nostri server.
  </p>
)}
```

- [ ] **Step 3: Commit**

```bash
git add src/components/layout/ChatLayout.tsx src/app/page.tsx
git commit -m "feat: UserButton header, nota privacy, badge Premium aggiornato"
```

---

## Task 14: Email notifiche post-report (Resend)

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/requirements.txt`
- Modify: `backend/.env`

- [ ] **Step 1: Installa Resend**

```bash
cd backend && source .venv/bin/activate
pip install resend==2.10.0
pip freeze | grep resend >> requirements.txt
```

Aggiorna i valori in `backend/.env` per la produzione (già aggiunti in Task 1):
```env
RESEND_API_KEY=re_...           # da Resend dashboard
REPORT_FROM_EMAIL=report@k2-ai.it
FRONTEND_URL=https://www.k2-ai.it  # aggiorna da localhost:3000 a prod URL
```

- [ ] **Step 2: Aggiungi funzione `send_report_ready_email` in `main.py`**

```python
def send_report_ready_email(clerk_user_id: str, report_url: str) -> None:
    import resend, httpx
    resend.api_key = os.getenv("RESEND_API_KEY", "")
    if not resend.api_key:
        return
    try:
        # Recupera email utente da Clerk API
        clerk_secret = os.getenv("CLERK_SECRET_KEY", "")
        r = httpx.get(
            f"https://api.clerk.com/v1/users/{clerk_user_id}",
            headers={"Authorization": f"Bearer {clerk_secret}"},
            timeout=5,
        )
        email = r.json().get("email_addresses", [{}])[0].get("email_address", "")
        if not email:
            return
        resend.Emails.send({
            "from": os.getenv("REPORT_FROM_EMAIL", "report@k2-ai.it"),
            "to": [email],
            "subject": "Il tuo report K2-AI è pronto",
            "html": f"""
            <p>Il tuo report è stato generato con successo.</p>
            <p><a href="{report_url}">Clicca qui per accedere al report</a></p>
            <p>Accedi con il tuo account per scaricare i file.</p>
            """,
        })
    except Exception:
        pass
```

- [ ] **Step 3: Chiama `send_report_ready_email` dopo ogni report generato**

In `main.py`, dentro `chat()`, dopo ogni `track_event("report_generated", ...)`:

```python
if report_pdf and clerk_user_id:
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    send_report_ready_email(clerk_user_id, f"{frontend_url}?report={report_pdf['url'].split('/')[-1]}")
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/main.py backend/requirements.txt backend/.env
git commit -m "feat: email notifica post-report via Resend"
```

---

## Task 15: Test finale end-to-end

- [ ] **Step 1: Avvia backend**

```bash
cd backend && source .venv/bin/activate
lsof -ti:8000 | xargs kill -9 2>/dev/null
uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 2: Avvia frontend**

```bash
cd /Volumes/PARASSITA/kbot
npm run dev
```

- [ ] **Step 3: Verifica flusso completo**

Apri `http://localhost:3000`:

1. **Lead mode** — invia messaggio senza login → funziona ✓
2. **Report mode, non loggato** → vedi AuthGate con "Accedi" ✓
3. **Report mode, loggato** → chat funziona, bottoni download mostrano "Paga per scaricare" ✓
4. **Checkout** — clicca "Paga" → redirect Stripe sandbox ✓
5. **Post-pagamento** (simula webhook con Stripe CLI) → `has_paid = true` → download sbloccati ✓
6. **Rate limit** — invia 31 messaggi report → 429 al 31° ✓
7. **Feedback** — dopo report → widget stelle visibile, submit funziona ✓

Simula webhook Stripe:
```bash
stripe listen --forward-to localhost:8000/api/stripe/webhook
stripe trigger checkout.session.completed
```

- [ ] **Step 4: Esegui tutti i test backend**

```bash
cd backend && pytest tests/ -v
```
Expected: tutti PASSED

- [ ] **Step 5: Commit finale**

```bash
git add -A
git commit -m "feat: kbot production upgrade — Clerk, Stripe, Supabase, rate limiting, analytics, feedback, email"
```

---

## Variabili d'Ambiente — Checklist Finale

Prima di considerare completo, verifica che tutte queste variabili siano impostate:

| Variabile | Dove | Valore di esempio |
|-----------|------|-------------------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | `.env.local` | `pk_test_...` |
| `CLERK_SECRET_KEY` | `.env.local` + `backend/.env` | `sk_test_...` |
| `CLERK_JWKS_URL` | `backend/.env` | `https://...clerk.accounts.dev/.well-known/jwks.json` |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | `.env.local` | `pk_test_...` |
| `STRIPE_SECRET_KEY` | `backend/.env` | `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | `backend/.env` | `whsec_...` |
| `STRIPE_PRICE_ID` | `backend/.env` | `price_...` |
| `SUPABASE_URL` | `backend/.env` | `https://xxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | `backend/.env` | `eyJ...` |
| `RESEND_API_KEY` | `backend/.env` | `re_...` |
| `REPORT_FROM_EMAIL` | `backend/.env` | `report@k2-ai.it` |
| `FRONTEND_URL` | `backend/.env` | `https://www.k2-ai.it` |
