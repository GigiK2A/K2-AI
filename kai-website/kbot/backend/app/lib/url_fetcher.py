"""URL fetching and HTML content extraction for K-BOT sessions."""
from __future__ import annotations

import asyncio
import ipaddress
import json
import re
import socket
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

import httpx

FETCH_TIMEOUT = 10.0
MAX_RESPONSE_BYTES = 500_000
MAX_MAIN_CONTENT_CHARS = 6_000
FULL_CONTENT_HTML_THRESHOLD = 20_000
MAX_SUMMARY_CHARS = 1_500
MAX_REDIRECTS = 5

# Multi-page crawl limits (audit SEO needs more than just the homepage).
MAX_ADDITIONAL_PAGES = 6
ADDITIONAL_PAGE_TIMEOUT = 6.0
ADDITIONAL_PAGE_BYTES = 300_000

# Ports we allow (in addition to None/default per scheme).
# Block well-known service ports (SSH, SMTP, Redis, ES, Mongo, PG, MySQL...).
_BLOCKED_PORTS = {
    22, 23, 25, 110, 143, 465, 587, 993, 995,  # SSH/Telnet/SMTP/IMAP/POP3
    3306, 5432, 6379, 9200, 9300, 27017, 27018, 27019,  # DBs
    11211,  # memcached
    2375, 2376,  # docker
    5984, 6443,  # couchdb / k8s
}

_BLOCKED_HOSTS = re.compile(
    r"^(localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|"
    r"10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|"
    r"192\.168\.\d+\.\d+|169\.254\.\d+\.\d+|"
    # IPv6 literals (bracket-stripped by hostname): ::1, ::, fe80::*, fc00::*, fd00::*
    r"::1?|fe[89ab][0-9a-f]:.*|f[cd][0-9a-f]{2}:.*)$",
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


def _ip_is_disallowed(ip_str: str) -> bool:
    """Return True if the IP (v4 or v6) is private/loopback/link-local/reserved/multicast."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def validate_url(url: str) -> None:
    """Raise UrlFetchError if the URL is not safe to fetch.

    Blocks non-http(s) schemes, internal hostnames, IPv4/IPv6 private
    ranges, link-local and loopback addresses, and well-known
    non-HTTP service ports (SSH, SMTP, Redis, Postgres, ...).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UrlFetchError("L'URL deve iniziare con http:// o https://")
    host = parsed.hostname or ""
    if not host:
        raise UrlFetchError("URL senza host")
    if _BLOCKED_HOSTS.match(host):
        raise UrlFetchError(f"Host non consentito: {host}")

    # Port check — block known non-HTTP service ports.
    try:
        port = parsed.port
    except ValueError as exc:
        raise UrlFetchError(f"Porta non valida: {exc}") from exc
    if port is not None and port in _BLOCKED_PORTS:
        raise UrlFetchError(f"Porta non consentita: {port}")

    # If the host is already an IP literal, validate it directly.
    if _ip_is_disallowed(host):
        raise UrlFetchError(f"Host non consentito: {host}")

    # Resolve via getaddrinfo (covers IPv4 + IPv6) and reject any disallowed address.
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return  # let httpx fail naturally on a real fetch
    for info in infos:
        sockaddr = info[4]
        ip_str = sockaddr[0]
        # Strip zone id if present (e.g. "fe80::1%eth0")
        if "%" in ip_str:
            ip_str = ip_str.split("%", 1)[0]
        if _ip_is_disallowed(ip_str):
            raise UrlFetchError(f"Host non consentito (IP {ip_str}): {host}")


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
    additional = data.get("additional_pages") or []
    if additional:
        pages_line = "; ".join(
            f"{p.get('url', '')} (title=«{p.get('title', '')[:60]}», H1=«{p.get('h1', '')[:60]}»)"
            for p in additional[:6]
        )
        parts.append(f"Pagine interne crawlate ({len(additional)}): {pages_line}")
    summary = "\n".join(parts)
    return summary[:MAX_SUMMARY_CHARS]


async def _discover_internal_links(html: str, base_url: str) -> List[str]:
    """Extract distinct internal links from the homepage HTML, in order of appearance."""
    base_host = urlparse(base_url).hostname or ""
    if not base_host:
        return []
    seen: set = set()
    out: List[str] = []
    for m in re.finditer(r'<a[^>]+href=["\']([^"\'#]+)["\']', html, re.IGNORECASE):
        raw = m.group(1).strip()
        if not raw or raw.startswith(("mailto:", "tel:", "javascript:", "data:")):
            continue
        full = urljoin(base_url, raw)
        parsed = urlparse(full)
        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.hostname != base_host:
            continue
        # Drop the homepage itself + fragment-only links.
        norm = f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/'}"
        if norm.rstrip("/") == base_url.rstrip("/"):
            continue
        # Skip common asset paths.
        if re.search(r"\.(png|jpe?g|gif|webp|svg|ico|css|js|pdf|zip|mp4|mp3)(\?|$)", parsed.path, re.IGNORECASE):
            continue
        if norm not in seen:
            seen.add(norm)
            out.append(norm)
        if len(out) >= MAX_ADDITIONAL_PAGES * 2:  # over-collect, will trim after fetch
            break
    return out


async def _try_sitemap(base_url: str, client: httpx.AsyncClient) -> List[str]:
    """If /sitemap.xml is present, return up to MAX_ADDITIONAL_PAGES * 2 URLs from it."""
    parsed = urlparse(base_url)
    sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"
    try:
        validate_url(sitemap_url)
        resp = await client.get(sitemap_url, timeout=ADDITIONAL_PAGE_TIMEOUT)
        if resp.status_code != 200 or "xml" not in resp.headers.get("content-type", "").lower():
            return []
        body = resp.text[:200_000]
    except Exception:
        return []
    urls: List[str] = []
    base_host = parsed.hostname or ""
    for m in re.finditer(r"<loc>\s*([^<\s]+)\s*</loc>", body, re.IGNORECASE):
        u = m.group(1).strip()
        try:
            ph = urlparse(u)
            if ph.hostname == base_host and ph.scheme in ("http", "https") and u.rstrip("/") != base_url.rstrip("/"):
                urls.append(u)
        except Exception:
            continue
        if len(urls) >= MAX_ADDITIONAL_PAGES * 2:
            break
    return urls


async def _fetch_page_compact(url: str, client: httpx.AsyncClient) -> Dict[str, Any] | None:
    """Fetch one internal page and return only structural SEO fields."""
    try:
        validate_url(url)
        resp = await client.get(url, timeout=ADDITIONAL_PAGE_TIMEOUT)
        if resp.status_code != 200:
            return None
        if "text/html" not in resp.headers.get("content-type", "").lower():
            return None
        html = resp.text[:ADDITIONAL_PAGE_BYTES]
    except Exception:
        return None
    clean = _strip_noise(html)
    h1_match = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", clean, re.IGNORECASE)
    h1 = _STRIP_TAGS.sub("", h1_match.group(1)).strip() if h1_match else ""
    word_count = len(_STRIP_TAGS.sub(" ", clean).split())
    return {
        "url": url,
        "title": _get_tag_content(clean, "title"),
        "meta_description": _get_meta(clean, "description"),
        "canonical": _get_canonical(clean),
        "h1": h1[:200],
        "word_count": word_count,
    }


async def _crawl_additional_pages(html: str, base_url: str) -> List[Dict[str, Any]]:
    """Discover internal links (sitemap > homepage anchors) and fetch them in parallel."""
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=ADDITIONAL_PAGE_TIMEOUT,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; K2-AI-Bot/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml",
        },
    ) as client:
        candidates = await _try_sitemap(base_url, client)
        if not candidates:
            candidates = await _discover_internal_links(html, base_url)
        if not candidates:
            return []
        candidates = candidates[: MAX_ADDITIONAL_PAGES * 2]
        results = await asyncio.gather(
            *[_fetch_page_compact(u, client) for u in candidates],
            return_exceptions=True,
        )
    pages: List[Dict[str, Any]] = []
    for r in results:
        if isinstance(r, dict) and r.get("url"):
            pages.append(r)
        if len(pages) >= MAX_ADDITIONAL_PAGES:
            break
    return pages


async def fetch_url_content(url: str) -> Dict[str, Any]:
    """Fetch URL and extract content. Returns data dict with 'summary' key added.

    Manually follows redirects, re-validating the destination at every hop
    to prevent SSRF via a public URL that 30x's to a private/internal address.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; K2-AI-Bot/1.0)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "it,en;q=0.9",
    }
    current_url = url
    async with httpx.AsyncClient(
        follow_redirects=False,
        timeout=FETCH_TIMEOUT,
        headers=headers,
    ) as client:
        for _hop in range(MAX_REDIRECTS + 1):
            validate_url(current_url)  # re-validate at every hop
            async with client.stream("GET", current_url) as resp:
                # Redirect? Pull Location and continue the loop.
                if resp.is_redirect:
                    location = resp.headers.get("location")
                    if not location:
                        raise UrlFetchError(f"Redirect senza Location: {current_url}")
                    # Resolve relative redirects against the current URL.
                    next_url = str(resp.url.join(location))
                    current_url = next_url
                    continue

                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    raise UrlFetchError(f"HTTP {e.response.status_code}: {current_url}") from e
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
                break
        else:
            raise UrlFetchError(f"Troppi redirect (>{MAX_REDIRECTS}): {url}")

    data = extract_html_content(html, current_url, content_type)
    # Multi-page crawl: best-effort, swallow errors — non bloccare il caller.
    try:
        data["additional_pages"] = await _crawl_additional_pages(html, current_url)
    except Exception:
        data["additional_pages"] = []
    data["summary"] = build_url_summary(data)
    return data
