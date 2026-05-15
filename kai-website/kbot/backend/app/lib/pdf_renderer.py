"""HTML rendering (Jinja2) + PDF rendering (Playwright/Chromium).

Synchronous wrapper that spawns a headless Chromium instance per call.
For low traffic this is acceptable; for high volume consider a long-lived browser.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

log = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
# nosemgrep: python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2 -- autoescape enabled via select_autoescape for html/xml; rendering controlled PDF templates only
_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)
_CSS_CACHE: Optional[str] = None
_LOGO_DATA_URI: Optional[str] = None


def _load_css() -> str:
    global _CSS_CACHE
    if _CSS_CACHE is None:
        _CSS_CACHE = (TEMPLATES_DIR / "report.css").read_text(encoding="utf-8")
    return _CSS_CACHE


def _load_logo_data_uri() -> str:
    """Read the official K2-AI logo and return as `data:image/png;base64,...`."""
    global _LOGO_DATA_URI
    if _LOGO_DATA_URI is None:
        logo_path = ASSETS_DIR / "logo-k2ai.png"
        if not logo_path.exists():
            log.warning("Logo file missing at %s — using fallback text", logo_path)
            _LOGO_DATA_URI = ""
        else:
            data = logo_path.read_bytes()
            _LOGO_DATA_URI = "data:image/png;base64," + base64.b64encode(data).decode("ascii")
    return _LOGO_DATA_URI


def _today_it() -> str:
    months = [
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
    ]
    d = datetime.now(timezone.utc)
    return f"{d.day} {months[d.month - 1]} {d.year}"


def render_html(analysis: Dict[str, Any], *, session_id: str) -> str:
    """Render the Jinja2 template with the LLM analysis payload (block-based)."""
    template = _env.get_template("report.html.j2")
    meta = dict(analysis.get("meta") or {})
    meta.setdefault("kicker", "Report Premium")
    meta.setdefault("title", "Report operativo K2-AI")
    today = _today_it()
    code_default = f"K2AI-{session_id[:4].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    if not meta.get("client_meta_lines"):
        meta["client_meta_lines"] = [
            f"Generato il {today}",
            f"Codice: {code_default}",
        ]

    blocks = analysis.get("blocks") or []
    footer = analysis.get("footer") or {
        "line1": f"Report generato il {today} · Dati forniti dall'utente · Stime basate su skill verticali K2-AI",
        "code": code_default,
    }
    # nosemgrep: python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2 -- autoescape enabled in _env (select_autoescape html/xml); all variables are server-controlled
    return template.render(
        css=_load_css(),
        meta=meta,
        blocks=blocks,
        footer=footer,
        logo=_load_logo_data_uri(),
    )


async def _html_to_pdf_bytes(html: str) -> bytes:
    """Use Playwright headless Chromium to render HTML → A4 PDF bytes."""
    from playwright.async_api import async_playwright

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp.write(html)
        tmp_path = tmp.name

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto(f"file://{tmp_path}", wait_until="networkidle")
                # Force-expand any collapsible widget so it prints fully open.
                await page.evaluate(
                    """() => {
                      document.querySelectorAll('details').forEach(d => d.setAttribute('open', ''));
                      document.querySelectorAll('[aria-expanded="false"]').forEach(el => el.setAttribute('aria-expanded', 'true'));
                      document.querySelectorAll('[hidden]').forEach(el => el.removeAttribute('hidden'));
                      document.querySelectorAll('.collapse,.accordion,.collapsed').forEach(el => {
                        el.classList.add('show', 'open', 'expanded');
                        el.classList.remove('collapsed', 'closed');
                        el.style.maxHeight = 'none';
                        el.style.height = 'auto';
                        el.style.overflow = 'visible';
                      });
                    }"""
                )
                # No top/bottom margins; @page rules in CSS define them.
                pdf = await page.pdf(
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                    margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                )
                return pdf
            finally:
                await browser.close()
    finally:
        try:
            Path(tmp_path).unlink()
        except OSError:
            pass


def render_pdf(analysis: Dict[str, Any], *, session_id: str) -> bytes:
    """Sync entrypoint: analysis JSON → PDF bytes."""
    html = render_html(analysis, session_id=session_id)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_html_to_pdf_bytes(html))
    # Inside an event loop (e.g. FastAPI handler): schedule into a fresh thread.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(asyncio.run, _html_to_pdf_bytes(html))
        return fut.result(timeout=120)
