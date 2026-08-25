"""Tests for url_fetcher utilities (no network calls)."""
import asyncio

import pytest
from app.lib.url_fetcher import (
    validate_url,
    extract_html_content,
    build_url_summary,
    UrlFetchError,
    _safe_get,
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


def test_validate_url_rejects_ipv6_loopback():
    with pytest.raises(UrlFetchError, match="non consentito"):
        validate_url("http://[::1]/admin")


def test_validate_url_rejects_ipv6_link_local():
    with pytest.raises(UrlFetchError, match="non consentito"):
        validate_url("http://[fe80::1]/")


def test_validate_url_rejects_ipv6_unique_local():
    with pytest.raises(UrlFetchError, match="non consentito"):
        validate_url("http://[fd00::1]/")


def test_validate_url_rejects_aws_imds_ipv4():
    with pytest.raises(UrlFetchError, match="non consentito"):
        validate_url("http://169.254.169.254/latest/meta-data/")


def test_validate_url_rejects_ssh_port():
    with pytest.raises(UrlFetchError, match="Porta non consentita"):
        validate_url("http://example.com:22/")


def test_validate_url_rejects_postgres_port():
    with pytest.raises(UrlFetchError, match="Porta non consentita"):
        validate_url("http://example.com:5432/")


def test_validate_url_rejects_redis_port():
    with pytest.raises(UrlFetchError, match="Porta non consentita"):
        validate_url("http://example.com:6379/")


def test_validate_url_accepts_standard_http_port():
    assert validate_url("http://example.com:80/") is None


def test_validate_url_accepts_standard_https_port():
    assert validate_url("https://example.com:443/") is None


def test_validate_url_accepts_custom_high_port():
    # Custom app ports (e.g. 8080) should still be allowed.
    assert validate_url("http://example.com:8080/") is None


# --- Crawl multi-pagina: i redirect NON aggirano validate_url ------------------
# Il client del crawl usava follow_redirects=True: validate_url veniva applicata
# all'URL pubblico di partenza e poi ignorata al 30x. Una pagina same-host che
# rimandava su 169.254.169.254 o su un host interno diventava SSRF, con title/H1
# della risposta interna rimandati al chiamante dentro il summary.


class _FakeResponse:
    def __init__(self, status_code, headers=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.is_redirect = status_code in (301, 302, 303, 307, 308)
        self.text = ""

    @property
    def url(self):
        import httpx
        return httpx.URL(self._url)


class _FakeClient:
    """Client che risponde 302 verso `location` e poi 200 su qualsiasi cosa."""

    def __init__(self, location):
        self.location = location
        self.requested = []

    async def get(self, url, timeout=None):
        self.requested.append(url)
        if len(self.requested) == 1:
            resp = _FakeResponse(302, {"location": self.location})
            resp._url = url
            return resp
        resp = _FakeResponse(200, {"content-type": "text/html"})
        resp._url = url
        return resp


def test_crawl_redirect_verso_ip_interno_viene_bloccato():
    client = _FakeClient("http://169.254.169.254/latest/meta-data/")
    assert asyncio.run(_safe_get("https://example.com/p1", client, "example.com")) is None
    # la richiesta verso l'IP interno non è mai partita
    assert client.requested == ["https://example.com/p1"]


def test_crawl_redirect_same_host_passa_comunque_da_validate_url():
    """Anche restando sullo stesso host il redirect è ri-validato a ogni hop:
    porta di servizio bloccata, IP privato dietro lo stesso nome, ecc."""
    client = _FakeClient("https://example.com:22/shell")
    with pytest.raises(UrlFetchError, match="Porta non consentita"):
        asyncio.run(_safe_get("https://example.com/p1", client, "example.com"))
    assert client.requested == ["https://example.com/p1"]


def test_crawl_redirect_fuori_dominio_viene_ignorato():
    client = _FakeClient("https://altro-sito.example/pagina")
    assert asyncio.run(_safe_get("https://example.com/p1", client, "example.com")) is None
    assert client.requested == ["https://example.com/p1"]


def test_crawl_redirect_same_host_viene_seguito():
    client = _FakeClient("https://example.com/p2")
    resp = asyncio.run(_safe_get("https://example.com/p1", client, "example.com"))
    assert resp is not None and resp.status_code == 200
    assert client.requested == ["https://example.com/p1", "https://example.com/p2"]


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
    body_text = "Paragrafo. " * 2000
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
    assert len(summary) <= 1500
    assert "Example" in summary
