# K-BOT URL & Image Analysis — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add transversal URL fetching and image (Claude Vision) analysis to K-BOT so any session can analyze web pages or screenshots regardless of skill/topic.

**Architecture:** New `app/lib/url_fetcher.py` handles all HTML extraction logic. `POST /api/kbot/fetch-url` stores results in `session.collected_data.analyzed_urls[]`. `handleKbotUpload` gains Claude Vision for images, storing descriptions in `extractedSummary`. `buildSystemPromptV2` and `message.py` both read from these session fields. Frontend (`Composer.tsx` + `page.tsx`) adds a URL chip input and auto-detects URLs pasted into the textarea.

**Tech Stack:** Python 3.11+, FastAPI, httpx (already in requirements), Anthropic SDK (already used), Next.js 14, TypeScript

---

## File Map

| Action | Path |
|--------|------|
| Create | `backend/app/lib/url_fetcher.py` |
| Modify | `backend/app/lib/prompts.py` |
| Create | `backend/app/api/fetch_url.py` |
| Modify | `backend/app/api/upload.py` |
| Modify | `backend/app/api/message.py` |
| Modify | `backend/app/main.py` |
| Create | `backend/tests/test_url_fetcher.py` |
| Modify | `src/lib/api.ts` |
| Modify | `src/components/chat/Composer.tsx` |
| Modify | `src/app/page.tsx` |

---

## Task 1: `url_fetcher.py` — HTML extraction utility

**Files:**
- Create: `backend/app/lib/url_fetcher.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_url_fetcher.py`

- [ ] **Step 1.1: Add pytest to requirements**

In `backend/requirements.txt`, append:
```
pytest>=8.0
pytest-mock>=3.14
```

- [ ] **Step 1.2: Write failing tests**

Create `backend/tests/__init__.py` (empty).

Create `backend/tests/test_url_fetcher.py`:
```python
"""Tests for url_fetcher utilities (no network calls)."""
import pytest
from app.lib.url_fetcher import (
    validate_url,
    extract_html_content,
    build_url_summary,
    UrlFetchError,
)


def test_validate_url_accepts_https():
    assert validate_url("https://example.com") is None


def test_validate_url_accepts_http():
    assert validate_url("http://example.com") is None


def test_validate_url_rejects_localhost():
    with pytest.raises(UrlFetchError, match="non consentito"):
        validate_url("http://localhost:8080/admin")


def test_validate_url_rejects_internal_ip():
    with pytest.raises(UrlFetchError, match="non consentito"):
        validate_url("http://192.168.1.1/api")


def test_validate_url_rejects_non_http():
    with pytest.raises(UrlFetchError, match="deve iniziare"):
        validate_url("ftp://example.com/file.txt")


def test_extract_metadata_only():
    html = """<html><head>
    <title>Esempio Sito</title>
    <meta name="description" content="Desc test">
    <link rel="canonical" href="https://esempio.it/">
    <meta property="og:title" content="OG Title">
    </head><body><h1>Titolo Principale</h1><p>Testo</p></body></html>"""
    result = extract_html_content(html, "https://esempio.it/", content_type="text/html")
    assert result["title"] == "Esempio Sito"
    assert result["meta_description"] == "Desc test"
    assert result["canonical"] == "https://esempio.it/"
    assert result["og"]["title"] == "OG Title"
    assert result["headings"][0] == {"level": "h1", "text": "Titolo Principale"}


def test_extract_full_content_for_long_page():
    body_text = "Paragrafo. " * 300
    html = f"""<html><head><title>Articolo</title></head>
    <body><main><p>{body_text}</p></main></body></html>"""
    result = extract_html_content(html, "https://blog.it/post", content_type="text/html")
    assert result["extraction_type"] == "full-content"
    assert len(result["main_content"]) <= 6100


def test_extract_schema_types():
    html = """<html><head><title>T</title>
    <script type="application/ld+json">{"@type":"Organization","name":"K2"}</script>
    </head><body></body></html>"""
    result = extract_html_content(html, "https://k2-ai.it/", content_type="text/html")
    assert "Organization" in result["schema_types"]


def test_build_url_summary_truncates():
    data = {
        "url": "https://example.com",
        "title": "Example",
        "meta_description": "A test site",
        "canonical": "https://example.com",
        "headings": [{"level": "h1", "text": "Example"}],
        "schema_types": [],
        "og": {},
        "main_content": "x" * 5000,
        "word_count": 800,
        "extraction_type": "full-content",
    }
    summary = build_url_summary(data)
    assert len(summary) <= 1600
    assert "Example" in summary
```

- [ ] **Step 1.3: Run tests to verify they fail**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot/backend
.venv/bin/python -m pytest tests/test_url_fetcher.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError` or `ImportError` for `url_fetcher`.

- [ ] **Step 1.4: Implement `url_fetcher.py`**

Create `backend/app/lib/url_fetcher.py`:
```python
"""URL fetching and HTML content extraction for K-BOT sessions."""
from __future__ import annotations

import ipaddress
import json
import re
import socket
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

FETCH_TIMEOUT = 10.0
MAX_RESPONSE_BYTES = 500_000
MAX_MAIN_CONTENT_CHARS = 6_000
FULL_CONTENT_HTML_THRESHOLD = 20_000
MAX_SUMMARY_CHARS = 1_500

_BLOCKED_HOSTS = re.compile(
    r"^(localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|::1|"
    r"10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|"
    r"192\.168\.\d+\.\d+|169\.254\.\d+\.\d+)$",
    re.IGNORECASE,
)

_STRIP_TAGS = re.compile(r"<[^>]+>")
_MULTI_SPACE = re.compile(r"\s{2,}")
_SCRIPT_STYLE = re.compile(
    r"<(script|style|nav|footer|header|aside)[^>]*>[\s\S]*?</\1>",
    re.IGNORECASE,
)
_TAG_ATTR = re.compile(r'[\w-]+="[^"]*"', re.IGNORECASE)


class UrlFetchError(ValueError):
    pass


def validate_url(url: str) -> None:
    """Raise UrlFetchError if the URL is not safe to fetch."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UrlFetchError("L'URL deve iniziare con http:// o https://")
    host = parsed.hostname or ""
    if _BLOCKED_HOSTS.match(host):
        raise UrlFetchError(f"Host non consentito: {host}")
    # Resolve and check IP
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise UrlFetchError(f"Host non consentito: {host}")
    except (socket.gaierror, ValueError):
        pass  # Can't resolve — allow, let httpx fail naturally


def _strip_noise(html: str) -> str:
    html = _SCRIPT_STYLE.sub(" ", html)
    return html


def _get_tag_content(html: str, tag: str) -> str:
    m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", html, re.IGNORECASE | re.DOTALL)
    return _STRIP_TAGS.sub("", m.group(1)).strip() if m else ""


def _get_meta(html: str, name: str) -> str:
    m = re.search(
        rf'<meta[^>]+(?:name|property)=["\'](?:og:)?{re.escape(name)}["\'][^>]+content=["\']([^"\']*)["\']',
        html,
        re.IGNORECASE,
    )
    if not m:
        m = re.search(
            rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:name|property)=["\'](?:og:)?{re.escape(name)}["\']',
            html,
            re.IGNORECASE,
        )
    return m.group(1).strip() if m else ""


def _get_canonical(html: str) -> str:
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if not m:
        m = re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']', html, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _get_headings(html: str) -> List[Dict[str, str]]:
    headings = []
    for m in re.finditer(r"<(h[1-3])[^>]*>(.*?)</\1>", html, re.IGNORECASE | re.DOTALL):
        text = _STRIP_TAGS.sub("", m.group(2)).strip()
        if text:
            headings.append({"level": m.group(1).lower(), "text": text[:200]})
    return headings[:20]


def _get_schema_types(html: str) -> List[str]:
    types: List[str] = []
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>', html, re.IGNORECASE):
        try:
            obj = json.loads(m.group(1))
            t = obj.get("@type")
            if isinstance(t, str):
                types.append(t)
            elif isinstance(t, list):
                types.extend(t)
        except Exception:
            pass
    return list(set(types))


def _extract_main_text(html: str) -> str:
    for tag in ("main", "article", '[role="main"]'):
        m = re.search(rf"<{tag}[^>]*>([\s\S]*?)</{tag}>", html, re.IGNORECASE)
        if m:
            text = _STRIP_TAGS.sub(" ", m.group(1))
            text = _MULTI_SPACE.sub(" ", text).strip()
            if len(text) > 200:
                return text[:MAX_MAIN_CONTENT_CHARS]
    # Fallback: strip all tags from body
    body_m = re.search(r"<body[^>]*>([\s\S]*?)</body>", html, re.IGNORECASE)
    raw = body_m.group(1) if body_m else html
    text = _STRIP_TAGS.sub(" ", raw)
    text = _MULTI_SPACE.sub(" ", text).strip()
    return text[:MAX_MAIN_CONTENT_CHARS]


def extract_html_content(html: str, url: str, content_type: str = "text/html") -> Dict[str, Any]:
    """Parse HTML and return structured content dict."""
    clean = _strip_noise(html)
    title = _get_tag_content(clean, "title")
    meta_description = _get_meta(clean, "description")
    canonical = _get_canonical(clean)
    headings = _get_headings(clean)
    schema_types = _get_schema_types(html)  # use original for JSON-LD
    og = {
        "title": _get_meta(clean, "og:title") or _get_meta(clean, "title"),
        "description": _get_meta(clean, "og:description") or _get_meta(clean, "description"),
        "image": _get_meta(clean, "og:image"),
    }

    is_long = len(html) > FULL_CONTENT_HTML_THRESHOLD
    extraction_type = "full-content" if is_long else "metadata-only"
    main_content = _extract_main_text(clean) if is_long else ""
    word_count = len(main_content.split()) if main_content else 0

    return {
        "url": url,
        "title": title,
        "meta_description": meta_description,
        "canonical": canonical,
        "headings": headings,
        "schema_types": schema_types,
        "og": og,
        "main_content": main_content,
        "word_count": word_count,
        "extraction_type": extraction_type,
    }


def build_url_summary(data: Dict[str, Any]) -> str:
    """Build compact string for injection into system prompt."""
    parts = [f"URL: {data['url']}"]
    if data.get("title"):
        parts.append(f"Titolo: {data['title']}")
    if data.get("meta_description"):
        parts.append(f"Descrizione: {data['meta_description']}")
    if data.get("canonical") and data["canonical"] != data["url"]:
        parts.append(f"Canonical: {data['canonical']}")
    if data.get("headings"):
        h_str = " | ".join(f"{h['level'].upper()}: {h['text']}" for h in data["headings"][:6])
        parts.append(f"Intestazioni: {h_str}")
    if data.get("schema_types"):
        parts.append(f"Schema.org: {', '.join(data['schema_types'])}")
    if data.get("og", {}).get("image"):
        parts.append(f"OG image: {data['og']['image']}")
    if data.get("main_content"):
        parts.append(f"Contenuto ({data.get('word_count', 0)} parole):\n{data['main_content'][:800]}")
    summary = "\n".join(parts)
    return summary[:MAX_SUMMARY_CHARS]


async def fetch_url_content(url: str) -> Dict[str, Any]:
    """Fetch URL and extract content. Returns data dict with 'summary' key added."""
    validate_url(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; K2-AI-Bot/1.0)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "it,en;q=0.9",
    }
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=FETCH_TIMEOUT,
        headers=headers,
    ) as client:
        resp = await client.get(url)
        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type:
            raise UrlFetchError(f"Il server ha risposto con {content_type}, non HTML")
        html = resp.text[:MAX_RESPONSE_BYTES]

    data = extract_html_content(html, url, content_type)
    data["summary"] = build_url_summary(data)
    return data
```

- [ ] **Step 1.5: Run tests**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot/backend
.venv/bin/python -m pytest tests/test_url_fetcher.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 1.6: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot
git add backend/app/lib/url_fetcher.py backend/tests/ backend/requirements.txt
git commit -m "feat(kbot): add url_fetcher utility with SSRF protection and adaptive HTML extraction"
```

---

## Task 2: Extend `prompts.py` — inject analyzed URLs into system prompt

**Files:**
- Modify: `backend/app/lib/prompts.py`

- [ ] **Step 2.1: Add URL context block to `build_system_prompt_v2`**

In `backend/app/lib/prompts.py`, after the `uploaded_files` block (around line 55-68), add:

```python
    analyzed_urls = collected.get("analyzed_urls") or []
    url_context = ""
    if analyzed_urls:
        url_lines = []
        for u in analyzed_urls[-3:]:  # last 3 only
            summary = str(u.get("summary") or u.get("url") or "").strip()
            if summary:
                url_lines.append(f"- {summary[:600]}")
        if url_lines:
            url_context = "\nURL ANALIZZATI DALL'UTENTE:\n" + "\n".join(url_lines) + "\n"
```

Then in `base_prompt`, add `{url_context}` right after `{service_context}`:

Replace the line:
```python
    base_prompt = f"""Sei K-BOT, il consulente AI di K2-AI per PMI italiane.
Il tuo ruolo: capire il problema operativo dell'utente con domande naturali, raccogliere il contesto necessario, poi produrre un riepilogo strutturato.
{service_context}
```

With:
```python
    base_prompt = f"""Sei K-BOT, il consulente AI di K2-AI per PMI italiane.
Il tuo ruolo: capire il problema operativo dell'utente con domande naturali, raccogliere il contesto necessario, poi produrre un riepilogo strutturato.
{service_context}{url_context}
```

- [ ] **Step 2.2: Verify build manually**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot/backend
.venv/bin/python -c "
from app.lib.prompts import build_system_prompt_v2
session = {'collected_data': {'analyzed_urls': [{'url': 'https://test.it', 'summary': 'URL: https://test.it\nTitolo: Test'}]}}
prompt = build_system_prompt_v2([], session)
assert 'URL: https://test.it' in prompt, 'URL context missing from prompt'
print('OK — URL context injected')
"
```

Expected: `OK — URL context injected`

- [ ] **Step 2.3: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot
git add backend/app/lib/prompts.py
git commit -m "feat(kbot): inject analyzed_urls into system prompt context"
```

---

## Task 3: `fetch_url.py` — new POST /api/kbot/fetch-url endpoint

**Files:**
- Create: `backend/app/api/fetch_url.py`
- Modify: `backend/app/main.py`

- [ ] **Step 3.1: Create `fetch_url.py`**

Create `backend/app/api/fetch_url.py`:
```python
"""POST /api/kbot/fetch-url — fetch a URL and store extracted content in the session."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..lib import sessions
from ..lib.auth import AuthUser, optional_user
from ..lib.url_fetcher import UrlFetchError, fetch_url_content

router = APIRouter()
log = logging.getLogger(__name__)

MAX_URLS_PER_SESSION = 5


class FetchUrlBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    url: str

    class Config:
        populate_by_name = True


@router.post("/fetch-url")
async def post_fetch_url(
    body: FetchUrlBody, user: Optional[AuthUser] = Depends(optional_user)
):
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    owner = session.get("user_id")
    if owner and (not user or user.id != owner):
        raise HTTPException(status_code=403, detail="not your session")

    collected = dict(session.get("collected_data") or {})
    existing_urls: list = list(collected.get("analyzed_urls") or [])

    # Check cache — if same URL already fetched this session, return it
    for entry in existing_urls:
        if entry.get("url") == body.url:
            return {
                "ok": True,
                "url": body.url,
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "cached": True,
            }

    if len(existing_urls) >= MAX_URLS_PER_SESSION:
        raise HTTPException(
            status_code=422,
            detail=f"Massimo {MAX_URLS_PER_SESSION} URL per sessione",
        )

    try:
        data = await fetch_url_content(body.url)
    except UrlFetchError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        log.warning("fetch_url failed for %s: %s", body.url, exc)
        raise HTTPException(status_code=502, detail=f"Impossibile raggiungere l'URL: {exc}")

    existing_urls.append(data)
    collected["analyzed_urls"] = existing_urls
    sessions.update_session(body.sessionId, {"collected_data": collected})

    return {
        "ok": True,
        "url": body.url,
        "title": data.get("title", ""),
        "summary": data.get("summary", ""),
        "cached": False,
    }
```

- [ ] **Step 3.2: Register route in `main.py`**

In `backend/app/main.py`, add the import and router:

```python
from .api import session, message, upload, report, checkout, generate_pdf, status, webhook, fetch_url
```

And add after the last `app.include_router` line:
```python
app.include_router(fetch_url.router, prefix="/api/kbot", tags=["fetch-url"])
```

- [ ] **Step 3.3: Smoke test the endpoint**

Start the backend:
```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot/backend
.venv/bin/uvicorn app.main:app --port 8001 --reload &
sleep 2
```

Test SSRF protection (must return 422):
```bash
curl -s -X POST http://localhost:8001/api/kbot/fetch-url \
  -H "Content-Type: application/json" \
  -d '{"session_id":"fake","url":"http://localhost:9999/"}' | python3 -m json.tool
```
Expected: `{"detail": "session not found"}` (hits session check before URL validation — correct).

Test with missing session:
```bash
curl -s -X POST http://localhost:8001/api/kbot/fetch-url \
  -H "Content-Type: application/json" \
  -d '{"session_id":"nonexistent-uuid","url":"http://192.168.1.1/"}' | python3 -m json.tool
```
Expected: `{"detail": "session not found"}`

Stop test server: `pkill -f "uvicorn app.main:app --port 8001"`

- [ ] **Step 3.4: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot
git add backend/app/api/fetch_url.py backend/app/main.py
git commit -m "feat(kbot): add POST /api/kbot/fetch-url endpoint with session caching"
```

---

## Task 4: Extend `upload.py` — Claude Vision for images

**Files:**
- Modify: `backend/app/api/upload.py`

- [ ] **Step 4.1: Add `_analyze_image_with_vision` function to `upload.py`**

At the top of `backend/app/api/upload.py`, add the import:
```python
import anthropic as _anthropic
```

Add this function before the `@router.post("/upload")` decorator:
```python
_VISION_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def _analyze_image_vision(data: bytes, mime: str, name: str) -> str:
    """Call Claude Vision to describe the image. Returns description string."""
    from ..settings import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
    import base64

    b64 = base64.b64encode(data).decode("utf-8")
    client = _anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=800,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime,
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            f'Analizza questa immagine "{name}" e descrivi in dettaglio: '
                            "testo visibile, struttura e layout, elementi chiave (titoli, CTA, grafici, form, tabelle). "
                            "Sii preciso e completo. Rispondi in italiano."
                        ),
                    },
                ],
            }
        ],
    )
    return response.content[0].text.strip() if response.content else ""
```

- [ ] **Step 4.2: Call vision in `_extract_text` for images**

In `_extract_text`, add a branch for images before the final `return "", ..., "none"`:

Replace the end of `_extract_text`:
```python
    return "", "Nessun testo estraibile dal file.", "none"
```

With:
```python
    if mime in _VISION_MIMES or any(name.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp")):
        try:
            description = _analyze_image_vision(content, mime or "image/jpeg", name)
            if description:
                return "", description, "claude-vision"
        except Exception as exc:
            log.warning("vision analysis failed for %s: %s", name, exc)

    return "", "Nessun testo estraibile dal file.", "none"
```

- [ ] **Step 4.3: Verify image path manually**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot/backend
.venv/bin/python -c "
from app.api.upload import _VISION_MIMES
print('Vision MIME set:', _VISION_MIMES)
print('OK')
"
```

Expected: prints MIME set without error.

- [ ] **Step 4.4: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot
git add backend/app/api/upload.py
git commit -m "feat(kbot): add Claude Vision analysis for uploaded images"
```

---

## Task 5: Extend `message.py` — auto-detect and fetch URLs in chat

**Files:**
- Modify: `backend/app/api/message.py`

- [ ] **Step 5.1: Add URL auto-detection helper**

At the top of `backend/app/api/message.py`, add imports:
```python
import re as _re
from ..lib.url_fetcher import fetch_url_content, UrlFetchError
```

Add this function before the `@router.post("/message")` decorator:
```python
_URL_RE = _re.compile(r"https?://[^\s<>\"']{6,}", _re.IGNORECASE)
_MAX_AUTO_URLS = 2  # max URLs to auto-fetch per message turn


def _extract_urls(text: str) -> list[str]:
    return list(dict.fromkeys(_URL_RE.findall(text or "")))[:_MAX_AUTO_URLS]


async def _auto_fetch_urls(text: str, collected: dict) -> dict:
    """Detect URLs in text, fetch any not already in session, return updated collected."""
    urls = _extract_urls(text)
    if not urls:
        return collected
    existing = {u.get("url") for u in (collected.get("analyzed_urls") or [])}
    new_entries = list(collected.get("analyzed_urls") or [])
    for url in urls:
        if url in existing:
            continue
        if len(new_entries) >= 5:
            break
        try:
            data = await fetch_url_content(url)
            new_entries.append(data)
            existing.add(url)
        except (UrlFetchError, Exception):
            pass  # silent — don't block the chat turn
    collected = dict(collected)
    collected["analyzed_urls"] = new_entries
    return collected
```

- [ ] **Step 5.2: Call `_auto_fetch_urls` in `post_message`**

In `post_message`, after the line:
```python
    merged_messages = sessions.append_messages(session, new_msgs)
```

Add:
```python
    # Auto-fetch any URLs the user just pasted
    last_user_text = new_msgs[-1]["content"] if new_msgs else ""
    collected = await _auto_fetch_urls(last_user_text, collected)
```

And change the function signature from `def post_message` to `async def post_message`:
```python
@router.post("/message")
async def post_message(body: MessageBody, user: Optional[AuthUser] = Depends(optional_user)):
```

- [ ] **Step 5.3: Verify import is clean**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot/backend
.venv/bin/python -c "from app.api.message import post_message; print('OK')"
```

Expected: `OK`

- [ ] **Step 5.4: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot
git add backend/app/api/message.py
git commit -m "feat(kbot): auto-detect and fetch URLs pasted into chat messages"
```

---

## Task 6: Frontend — `api.ts` — add `fetchUrl` function

**Files:**
- Modify: `src/lib/api.ts`

- [ ] **Step 6.1: Add `AnalyzedUrl` type and `fetchUrl` function**

In `src/lib/api.ts`, after the `UploadedFile` interface, add:

```typescript
export interface AnalyzedUrl {
  url: string;
  title: string;
  summary: string;
  cached: boolean;
}

export async function fetchUrl(
  sessionId: string,
  url: string,
  token?: string | null,
): Promise<AnalyzedUrl> {
  const res = await fetch(`${API_BASE}/api/kbot/fetch-url`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(token),
    },
    body: JSON.stringify({ session_id: sessionId, url }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Errore sconosciuto" }));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}
```

- [ ] **Step 6.2: Verify TypeScript compiles**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot
npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 6.3: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot
git add src/lib/api.ts
git commit -m "feat(kbot-ui): add fetchUrl API function and AnalyzedUrl type"
```

---

## Task 7: Frontend — `Composer.tsx` — URL chip input + auto-detect

**Files:**
- Modify: `src/components/chat/Composer.tsx`

- [ ] **Step 7.1: Replace `Composer.tsx` with URL-aware version**

Replace the full content of `src/components/chat/Composer.tsx`:

```tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, Globe, Paperclip, X } from "lucide-react";
import { UploadedFile } from "@/types/chat";

const URL_RE = /https?:\/\/[^\s<>"']{6,}/i;

export function Composer({
  value,
  onChange,
  onSubmit,
  disabled,
  suggestions,
  onPickFiles,
  files,
  onFetchUrl,
  fetchingUrl,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  suggestions: string[];
  onPickFiles: (files: File[]) => void;
  files: UploadedFile[];
  onFetchUrl?: (url: string) => void;
  fetchingUrl?: boolean;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const [urlMode, setUrlMode] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const urlRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = `${Math.min(el.scrollHeight, 170)}px`;
  }, [value]);

  useEffect(() => {
    if (urlMode) urlRef.current?.focus();
  }, [urlMode]);

  function handlePaste(e: React.ClipboardEvent<HTMLTextAreaElement>) {
    const pasted = e.clipboardData.getData("text");
    const match = URL_RE.exec(pasted);
    if (match && onFetchUrl) {
      // Let the paste happen, then trigger fetch
      setTimeout(() => onFetchUrl(match[0]), 0);
    }
  }

  function handleUrlSubmit() {
    const trimmed = urlInput.trim();
    if (!trimmed || !onFetchUrl) return;
    onFetchUrl(trimmed);
    setUrlInput("");
    setUrlMode(false);
  }

  return (
    <div className="sticky bottom-0 mt-4 border-t border-[var(--line)] bg-[linear-gradient(180deg,rgba(5,5,5,0.2),rgba(5,5,5,0.95))] pt-3">
      <div className="mb-2 flex gap-2 overflow-x-auto pb-1">
        {suggestions.map((s) => (
          <button
            key={s}
            onClick={() => onChange(s)}
            className="rounded-full border border-[var(--line)] px-3 py-1 text-xs text-[var(--text-soft)] hover:border-[var(--line-strong)] whitespace-nowrap"
          >
            {s}
          </button>
        ))}
      </div>

      {urlMode && (
        <div className="mb-2 flex items-center gap-2 rounded-xl border border-[var(--line)] bg-[#0a0a0a] px-3 py-2">
          <Globe size={14} className="shrink-0 text-[var(--teal)]" />
          <input
            ref={urlRef}
            type="url"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") { e.preventDefault(); handleUrlSubmit(); }
              if (e.key === "Escape") { setUrlMode(false); setUrlInput(""); }
            }}
            placeholder="Incolla URL da analizzare…"
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-[var(--text-muted)]"
            disabled={fetchingUrl}
          />
          {fetchingUrl ? (
            <span className="text-xs text-[var(--text-soft)]">Analisi…</span>
          ) : (
            <>
              <button
                onClick={handleUrlSubmit}
                disabled={!urlInput.trim()}
                className="rounded-lg bg-[var(--teal)] px-2 py-1 text-xs font-medium text-black disabled:opacity-40"
              >
                Analizza
              </button>
              <button onClick={() => { setUrlMode(false); setUrlInput(""); }}>
                <X size={14} className="text-[var(--text-soft)]" />
              </button>
            </>
          )}
        </div>
      )}

      <div className="k2-panel rounded-2xl p-2">
        {files.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2 px-1">
            {files.map((f) => (
              <span
                key={f.path}
                className="rounded-full border border-[var(--line)] px-2 py-1 text-xs text-[var(--text-soft)]"
              >
                {f.name}
              </span>
            ))}
          </div>
        )}
        <textarea
          ref={ref}
          rows={1}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          onPaste={handlePaste}
          placeholder="Scrivi la tua richiesta…"
          className="k2-focus max-h-[170px] w-full resize-none rounded-xl border border-transparent bg-transparent px-3 py-2 text-sm leading-6"
        />
        <div className="mt-2 flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <input
              ref={fileRef}
              type="file"
              multiple
              accept="image/*,.pdf,.txt,.md,.csv,.json,.xml"
              className="hidden"
              onChange={(e) => {
                const selected = Array.from(e.target.files ?? []);
                if (selected.length) onPickFiles(selected);
                e.currentTarget.value = "";
              }}
            />
            <button
              onClick={() => fileRef.current?.click()}
              title="Allega file"
              className="rounded-lg border border-[var(--line)] p-2 text-[var(--text-soft)] hover:border-[var(--line-strong)]"
            >
              <Paperclip size={15} />
            </button>
            {onFetchUrl && (
              <button
                onClick={() => setUrlMode((v) => !v)}
                title="Analizza un URL"
                className={`rounded-lg border p-2 text-[var(--text-soft)] hover:border-[var(--line-strong)] ${
                  urlMode ? "border-[var(--teal)] text-[var(--teal)]" : "border-[var(--line)]"
                }`}
              >
                <Globe size={15} />
              </button>
            )}
          </div>
          <button
            onClick={onSubmit}
            disabled={disabled || !value.trim()}
            className="rounded-xl bg-[var(--teal)] p-2 text-black disabled:opacity-50"
          >
            <ArrowUp size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 7.2: Verify TypeScript compiles**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot
npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 7.3: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot
git add src/components/chat/Composer.tsx
git commit -m "feat(kbot-ui): add URL chip input and paste auto-detect to Composer"
```

---

## Task 8: Frontend — `page.tsx` — wire up URL fetch flow

**Files:**
- Modify: `src/app/page.tsx`

- [ ] **Step 8.1: Add state and handler for URL fetching**

In `src/app/page.tsx`:

1. Add import for `fetchUrl` at the top:
```typescript
import { sendMessage, uploadFiles, startCheckout, fetchUrl, type UploadedFile, type AnalyzedUrl } from "@/lib/api";
```

2. Inside the component, add state after existing state declarations:
```typescript
const [fetchingUrl, setFetchingUrl] = useState(false);
const [analyzedUrls, setAnalyzedUrls] = useState<AnalyzedUrl[]>([]);
```

3. Add handler function (after existing handlers):
```typescript
const handleFetchUrl = useCallback(
  async (url: string) => {
    if (!session || fetchingUrl) return;
    setFetchingUrl(true);
    try {
      const result = await fetchUrl(session.id, url, token ?? null);
      setAnalyzedUrls((prev) => {
        const exists = prev.some((u) => u.url === url);
        return exists ? prev : [...prev, result];
      });
      // Inject a system-like confirmation into the conversation
      const confirmMsg: ChatMessage = {
        id: uid(),
        role: "assistant",
        content: `Ho analizzato **${result.title || url}** — il contenuto è disponibile per la nostra conversazione. Cosa vuoi sapere?`,
        ts: new Date().toISOString(),
      };
      setConversation((prev) => ({ ...prev, messages: [...prev.messages, confirmMsg] }));
    } catch (err: unknown) {
      const errMsg: ChatMessage = {
        id: uid(),
        role: "assistant",
        content: `Non riesco ad analizzare l'URL: ${err instanceof Error ? err.message : "errore sconosciuto"}.`,
        ts: new Date().toISOString(),
      };
      setConversation((prev) => ({ ...prev, messages: [...prev.messages, errMsg] }));
    } finally {
      setFetchingUrl(false);
    }
  },
  [session, fetchingUrl, token],
);
```

4. Pass new props to `<Composer>`:
```tsx
<Composer
  value={input}
  onChange={setInput}
  onSubmit={handleSend}
  disabled={loading || fetchingUrl}
  suggestions={suggestions}
  onPickFiles={handlePickFiles}
  files={uploadedFiles}
  onFetchUrl={handleFetchUrl}
  fetchingUrl={fetchingUrl}
/>
```

- [ ] **Step 8.2: Verify TypeScript compiles**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot
npx tsc --noEmit 2>&1 | head -30
```

Expected: no errors.

- [ ] **Step 8.3: Build to verify no runtime errors**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot
npm run build 2>&1 | tail -20
```

Expected: successful build, no TypeScript or module errors.

- [ ] **Step 8.4: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot
git add src/app/page.tsx
git commit -m "feat(kbot-ui): wire up URL fetch flow in page.tsx with loading state and confirmation message"
```

---

## Task 9: Integration smoke test (manual)

- [ ] **Step 9.1: Start backend**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot/backend
.venv/bin/uvicorn app.main:app --port 8000 --reload
```

- [ ] **Step 9.2: Start frontend**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot
npm run dev
```

- [ ] **Step 9.3: Manual flow check**

1. Open `http://localhost:3000` (or the kbot Next.js dev port)
2. Create a new session
3. Click the Globe button → URL input appears
4. Paste `https://www.k2-ai.it/` → click "Analizza"
5. Verify: loading state shows, then confirmation message appears
6. Send a message: "Cosa pensi del SEO di questo sito?"
7. Verify: Claude responds with analysis that references k2-ai.it content

- [ ] **Step 9.4: Test auto-detect**

1. In the chat textarea, paste a full URL (e.g. `https://www.k2-ai.it/suite-ai`)
2. Verify: fetch is triggered automatically after paste
3. Send message: "Analizza questa pagina"
4. Verify: response references the page content

- [ ] **Step 9.5: Test image upload**

1. Upload a screenshot of a website (PNG/JPG)
2. Verify: after upload, the file shows with `extractionMethod: "claude-vision"` in session
3. Send message: "Cosa vedi in questo screenshot?"
4. Verify: Claude describes the image content

- [ ] **Step 9.6: Final commit**

```bash
cd /Volumes/PARASSITA/K-AI/apps/website/kbot
git add .
git commit -m "chore: kbot url+image analysis feature complete — smoke tested"
```
