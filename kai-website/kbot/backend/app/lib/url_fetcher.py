"""URL fetching and HTML content extraction for K-BOT sessions."""
from __future__ import annotations

import ipaddress
import json
import re
import socket
from typing import Any, Dict, List
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
    for tag in ("main", "article"):
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
        async with client.stream("GET", url) as resp:
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise UrlFetchError(f"HTTP {e.response.status_code}: {url}") from e
            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type:
                raise UrlFetchError(f"Il server ha risposto con {content_type}, non HTML")
            chunks = []
            size = 0
            async for chunk in resp.aiter_bytes(4096):
                chunks.append(chunk)
                size += len(chunk)
                if size >= MAX_RESPONSE_BYTES:
                    break
            html = (b"".join(chunks))[:MAX_RESPONSE_BYTES].decode("utf-8", errors="replace")

    data = extract_html_content(html, url, content_type)
    data["summary"] = build_url_summary(data)
    return data
