# AIOS Fase 1b — Real-Data Sensors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Give the AIOS its first eyes on real data — read-only (L0) tools that read the marketing content tables (`servizi`, `topics`) from Supabase and Instagram profile/post metrics from the Graph API.

**Architecture:** A new `aios.sources` package. Each source is a plain class/function with an injectable I/O dependency (a psycopg connection for Supabase, an injectable HTTP fetcher for Instagram) so it is unit-testable without live access. Thin factory functions wrap each capability as a kernel `Tool(readonly=True, action_type=None)` — read-only tools bypass the autonomy ladder, so they always execute and need no approval. Nothing here writes anywhere.

**Tech Stack:** Python 3.12, pytest, psycopg3 (already a dep), stdlib `urllib` for HTTP (no new dependency). Instagram Graph API v21.0, IG business account id `17841429842127461`.

**Config (env vars):** `AIOS_DATABASE_URL` (Supabase Postgres DSN), `AIOS_IG_TOKEN` (Graph API token), `AIOS_IG_USER_ID` (default `17841429842127461`).

**Live testing:** Supabase content is verified live by the controller via MCP. Instagram live test is skipped unless `AIOS_IG_TOKEN` is set; unit tests use a fake fetcher so logic is covered offline.

---

## File Structure

```
aios/src/aios/sources/
├── __init__.py        # exports
├── content.py         # read_servizi(conn), read_topics(conn)
├── instagram.py       # InstagramClient(token, ig_user_id, version, fetch)
└── tools.py           # content_tools(conn), instagram_tools(client) -> list[Tool]
aios/tests/
├── test_sources_content.py     # integration, skip without AIOS_DATABASE_URL
├── test_sources_instagram.py   # unit, fake fetcher (offline)
└── test_sources_tools.py       # tools are readonly + execute via Kernel
```

---

### Task 1: Supabase content source

**Files:**
- Create: `aios/src/aios/sources/__init__.py` (empty for now, or `# sources package`)
- Create: `aios/src/aios/sources/content.py`
- Test: `aios/tests/test_sources_content.py`

- [ ] **Step 1: Write `aios/src/aios/sources/content.py`**

```python
from __future__ import annotations

from typing import Any

import psycopg


def _rows(conn: "psycopg.Connection", sql: str) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(sql)
        cols = [c.name for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def read_servizi(conn: "psycopg.Connection") -> list[dict[str, Any]]:
    return _rows(conn, 'select id, "Servizio", "Categoria", "Descrizione", '
                       '"Risultati_KPI", "Agevolazione", "URL", "Stato", "Data" '
                       'from public.servizi order by id')


def read_topics(conn: "psycopg.Connection") -> list[dict[str, Any]]:
    return _rows(conn, 'select id, "Tema", "Descrizione", "Pillar", "Stato", "Data" '
                       'from public.topics order by id')
```

- [ ] **Step 2: Write the integration test `aios/tests/test_sources_content.py`**

```python
import os

import pytest

DSN = os.environ.get("AIOS_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="AIOS_DATABASE_URL not set")


def test_read_servizi_and_topics():
    import psycopg
    from aios.sources.content import read_servizi, read_topics
    with psycopg.connect(DSN) as conn:
        servizi = read_servizi(conn)
        topics = read_topics(conn)
    assert isinstance(servizi, list) and len(servizi) > 0
    assert "Servizio" in servizi[0] and "Stato" in servizi[0]
    assert isinstance(topics, list) and len(topics) > 0
    assert "Tema" in topics[0]
```

- [ ] **Step 3: Run** `cd aios && .venv/bin/pytest tests/test_sources_content.py -q` — without `AIOS_DATABASE_URL` it must report **1 skipped** (not failed).

- [ ] **Step 4: Full suite** `cd aios && .venv/bin/pytest -q` — all pass, 1 skipped.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/sources/__init__.py aios/src/aios/sources/content.py aios/tests/test_sources_content.py
git commit -m "feat(aios): supabase content source (servizi/topics)"
```

---

### Task 2: Instagram client

**Files:**
- Create: `aios/src/aios/sources/instagram.py`
- Test: `aios/tests/test_sources_instagram.py`

- [ ] **Step 1: Write `aios/src/aios/sources/instagram.py`**

```python
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Callable

GRAPH = "https://graph.facebook.com"

# A fetcher takes a full URL and returns parsed JSON. Default uses urllib;
# tests inject a fake so no network is needed.
Fetcher = Callable[[str], dict[str, Any]]


def _urllib_fetch(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=20) as resp:  # noqa: S310 (trusted host)
        return json.loads(resp.read().decode("utf-8"))


class InstagramError(RuntimeError):
    pass


class InstagramClient:
    def __init__(self, token: str, ig_user_id: str = "17841429842127461",
                 version: str = "v21.0", fetch: Fetcher = _urllib_fetch) -> None:
        self._token = token
        self._uid = ig_user_id
        self._version = version
        self._fetch = fetch

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        q = dict(params)
        q["access_token"] = self._token
        url = f"{GRAPH}/{self._version}/{path}?{urllib.parse.urlencode(q)}"
        data = self._fetch(url)
        if isinstance(data, dict) and "error" in data:
            raise InstagramError(str(data["error"]))
        return data

    def account(self) -> dict[str, Any]:
        return self._get(self._uid,
                         {"fields": "username,followers_count,media_count"})

    def recent_media(self, limit: int = 10) -> list[dict[str, Any]]:
        data = self._get(f"{self._uid}/media", {
            "fields": "id,caption,media_type,permalink,timestamp,"
                      "like_count,comments_count",
            "limit": str(limit),
        })
        return data.get("data", [])
```

- [ ] **Step 2: Write the unit test `aios/tests/test_sources_instagram.py`**

```python
import pytest

from aios.sources.instagram import InstagramClient, InstagramError


def make_client(responses):
    """responses: dict mapping a substring of the URL -> json payload."""
    def fake_fetch(url):
        for needle, payload in responses.items():
            if needle in url:
                return payload
        raise AssertionError(f"no fake response for {url}")
    return InstagramClient(token="T", ig_user_id="999", fetch=fake_fetch)


def test_account_parses_fields():
    c = make_client({"/v21.0/999?": {"username": "k2ai",
                                      "followers_count": 1200, "media_count": 42}})
    acc = c.account()
    assert acc["followers_count"] == 1200 and acc["username"] == "k2ai"


def test_recent_media_returns_list():
    c = make_client({"/999/media?": {"data": [
        {"id": "1", "like_count": 10, "comments_count": 2},
        {"id": "2", "like_count": 5, "comments_count": 0},
    ]}})
    media = c.recent_media(limit=2)
    assert [m["id"] for m in media] == ["1", "2"]


def test_token_is_sent_in_url():
    seen = {}
    def fake_fetch(url):
        seen["url"] = url
        return {"username": "x", "followers_count": 0, "media_count": 0}
    InstagramClient(token="SECRET", ig_user_id="999", fetch=fake_fetch).account()
    assert "access_token=SECRET" in seen["url"]


def test_graph_error_raises():
    c = make_client({"/v21.0/999?": {"error": {"message": "bad token"}}})
    with pytest.raises(InstagramError):
        c.account()
```

- [ ] **Step 3: Run** `cd aios && .venv/bin/pytest tests/test_sources_instagram.py -q` — expect 4 passed.

- [ ] **Step 4: Full suite** `cd aios && .venv/bin/pytest -q` — all pass.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/sources/instagram.py aios/tests/test_sources_instagram.py
git commit -m "feat(aios): instagram graph api client (injectable fetcher)"
```

---

### Task 3: Wrap sources as kernel read-only tools

**Files:**
- Create: `aios/src/aios/sources/tools.py`
- Modify: `aios/src/aios/sources/__init__.py` (export the factories)
- Test: `aios/tests/test_sources_tools.py`

- [ ] **Step 1: Write `aios/src/aios/sources/tools.py`**

```python
from __future__ import annotations

from typing import Any

from aios.tools import Tool
from aios.sources.content import read_servizi, read_topics


def content_tools(conn: Any) -> list[Tool]:
    return [
        Tool(name="leggi_servizi", action_type=None, readonly=True,
             run=lambda **_: read_servizi(conn)),
        Tool(name="leggi_topics", action_type=None, readonly=True,
             run=lambda **_: read_topics(conn)),
    ]


def instagram_tools(client: Any) -> list[Tool]:
    return [
        Tool(name="leggi_profilo_ig", action_type=None, readonly=True,
             run=lambda **_: client.account()),
        Tool(name="leggi_post_ig", action_type=None, readonly=True,
             run=lambda limit=10, **_: client.recent_media(limit=limit)),
    ]
```

- [ ] **Step 2: Write `aios/tests/test_sources_tools.py`**

```python
from aios.kernel import Kernel, ExecOutcome
from aios.sources.tools import content_tools, instagram_tools


class _FakeConn:
    pass


class _FakeIG:
    def account(self):
        return {"username": "k2ai", "followers_count": 7}
    def recent_media(self, limit=10):
        return [{"id": "1"}][:limit]


def test_content_tools_are_readonly_and_run_via_kernel(monkeypatch):
    import aios.sources.tools as t
    monkeypatch.setattr(t, "read_servizi", lambda conn: [{"Servizio": "X"}])
    monkeypatch.setattr(t, "read_topics", lambda conn: [{"Tema": "Y"}])
    k = Kernel()
    for tool in t.content_tools(_FakeConn()):
        k.register_tool(tool)
    res = k.execute("leggi_servizi", actor="marketing", args={})
    assert res.outcome == ExecOutcome.EXECUTED
    assert res.result == [{"Servizio": "X"}]


def test_instagram_tools_run_via_kernel():
    k = Kernel()
    for tool in instagram_tools(_FakeIG()):
        k.register_tool(tool)
    assert k.execute("leggi_profilo_ig", actor="marketing", args={}).result["followers_count"] == 7
    assert k.execute("leggi_post_ig", actor="marketing", args={"limit": 1}).result == [{"id": "1"}]
```

- [ ] **Step 3: Update `aios/src/aios/sources/__init__.py`**

```python
from aios.sources.content import read_servizi, read_topics
from aios.sources.instagram import InstagramClient, InstagramError
from aios.sources.tools import content_tools, instagram_tools

__all__ = [
    "read_servizi", "read_topics",
    "InstagramClient", "InstagramError",
    "content_tools", "instagram_tools",
]
```

- [ ] **Step 4: Run** `cd aios && .venv/bin/pytest tests/test_sources_tools.py -q` — expect 2 passed.

- [ ] **Step 5: Full suite** `cd aios && .venv/bin/pytest -q` — all pass.

- [ ] **Step 6: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/sources/tools.py aios/src/aios/sources/__init__.py aios/tests/test_sources_tools.py
git commit -m "feat(aios): register data sources as kernel read-only tools"
```

---

## Self-Review

**Spec coverage:** Marketing data sources (spec §5 "Fonti dati": IG Graph API insight, Supabase content table) → Tasks 1-2. Read-only L0 tools (spec §5 "L0: leggere insight, leggere contenuti") → Task 3.

**Placeholder scan:** none — all code complete.

**Type consistency:** `Tool(readonly=True, action_type=None, run=...)` matches the kernel's read-only path (always EXECUTED, audited "read"). `InstagramClient` fetcher is injectable for offline tests; default uses stdlib urllib (no new dep). `read_servizi`/`read_topics` quote the mixed-case column names exactly as they exist in Supabase.

**Live verification (controller):** after Task 1, verify `read_servizi`/`read_topics` return real rows against KAI. After the user provides `AIOS_IG_TOKEN`, run `test_sources_instagram` live path / a manual smoke against the real Graph API. Until then the IG live call is unverified (unit-tested only) — note this in the report.
