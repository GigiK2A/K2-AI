"""HTML rendering (Jinja2) + PDF rendering (WeasyPrint).

Sync entrypoint, niente headless browser. WeasyPrint rispetta print CSS
(@page, page-break, named pages, running elements) — affidabile su Linux/Railway.
"""
from __future__ import annotations

import base64
import logging
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


_TWO_SIDE_TYPES = {"two_column", "narrative_split", "conclusions"}

_CONCLUSIONS_FALLBACK_HTML = (
    "<p>I dati raccolti in sessione non sono stati sufficienti a generare conclusioni "
    "specifiche. Prossimi passi consigliati:</p>"
    "<ol>"
    "<li>Fornire dati di baseline (Google Search Console, Analytics) per ancorare proiezioni reali.</li>"
    "<li>Identificare 2-3 priorità operative tra le criticità descritte nei blocchi precedenti.</li>"
    "<li>Pianificare verifica KPI a 30/60/90 giorni con strumenti dedicati.</li>"
    "</ol>"
)

_CONCLUSIONS_RIGHT_FALLBACK = {
    "heading": "3 azioni immediate (settimana 1)",
    "milestones": [
        {
            "label": "Audit dati",
            "tone": "neutral",
            "items": ["Collega Google Search Console", "Esporta lista keyword/posizioni attuali"],
        },
        {
            "label": "Quick win",
            "tone": "warning",
            "items": ["Identifica 3 quick win on-page tra le criticità rilevate"],
        },
        {
            "label": "KPI 30/60/90gg",
            "tone": "neutral",
            "items": ["Definisci target su 3 KPI misurabili con baseline esplicita"],
        },
    ],
}


def _normalize_conclusions_right(right: dict) -> dict:
    """Mappa varianti comuni di nomi-chiavi emessi da Sonnet → schema milestones.

    Sonnet può scrivere right.actions / right.steps / right.immediate / right.tasks /
    right.next_steps invece di right.milestones. Senza questo mapping il template
    renderizza solo l'heading e la colonna destra appare vuota.
    """
    if not isinstance(right, dict):
        return _CONCLUSIONS_RIGHT_FALLBACK.copy()
    out = dict(right)
    # Heading aliases.
    if not out.get("heading"):
        for k in ("title", "subtitle", "label"):
            if out.get(k):
                out["heading"] = out[k]
                break
    # Milestones already present and valid → keep.
    milestones = out.get("milestones")
    if isinstance(milestones, list) and milestones and any(isinstance(m, dict) for m in milestones):
        return out
    # Try common variants.
    for alt_key in ("actions", "steps", "immediate", "tasks", "next_steps", "todos", "priorities", "weekly_actions"):
        candidate = out.get(alt_key)
        if isinstance(candidate, list) and candidate:
            converted: list = []
            for item in candidate:
                if isinstance(item, dict):
                    label = item.get("label") or item.get("title") or item.get("name") or item.get("action") or ""
                    items_list = item.get("items") or item.get("steps") or item.get("details") or []
                    if not items_list and item.get("description"):
                        items_list = [item["description"]]
                    tone = item.get("tone") or item.get("variant") or "neutral"
                    converted.append({"label": str(label), "items": [str(x) for x in items_list], "tone": tone})
                elif isinstance(item, str):
                    converted.append({"label": item, "items": [], "tone": "neutral"})
            if converted:
                out["milestones"] = converted
                return out
    # Plain list under right.items → bullet group.
    items = out.get("items")
    if isinstance(items, list) and items:
        out["milestones"] = [{"label": out.get("heading") or "Azioni", "items": [str(x) for x in items], "tone": "neutral"}]
        return out
    # body_html / body present → kept as-is (template gestisce fallback).
    if out.get("body_html") or out.get("body"):
        if out.get("body") and not out.get("body_html"):
            out["body_html"] = f"<p>{out['body']}</p>"
        return out
    # Nessuna shape utilizzabile → fallback testuale onesto.
    fallback = _CONCLUSIONS_RIGHT_FALLBACK.copy()
    if out.get("heading"):
        fallback["heading"] = out["heading"]
    return fallback


def _block_has_content(block: dict) -> bool:
    """True se il blocco ha contenuto sostanziale (non solo titolo vuoto)."""
    btype = block.get("type")
    # Conta tutti i valori "ricchi" del blocco escludendo type/title.
    for key, val in block.items():
        if key in ("type", "title"):
            continue
        if isinstance(val, str) and val.strip():
            return True
        if isinstance(val, (list, dict)) and val:
            if isinstance(val, dict):
                # left/right: ricorsione leggera
                for sub_val in val.values():
                    if isinstance(sub_val, str) and sub_val.strip():
                        return True
                    if isinstance(sub_val, (list, dict)) and sub_val:
                        return True
            else:
                return True
    return False


def _normalize_blocks(blocks: list) -> list:
    """Difensiva: garantisce shape stabile prima del render Jinja.

    1. Forza left/right come dict (vuoti se mancanti) sui blocchi a 2 colonne.
    2. Garantisce che conclusions abbia body_html non vuoto.
    3. Scarta blocchi non-dict o completamente vuoti (solo titolo).
    """
    safe: list = []
    for b in blocks or []:
        if not isinstance(b, dict):
            continue
        btype = b.get("type")
        if btype in _TWO_SIDE_TYPES:
            for side in ("left", "right"):
                val = b.get(side)
                if not isinstance(val, dict):
                    b[side] = {}
            # conclusions: body_html OBBLIGATORIO + normalizzazione right.
            if btype == "conclusions":
                if not b["left"].get("body_html"):
                    body = b["left"].get("body") or b.get("body_html") or b.get("body")
                    b["left"]["body_html"] = body or _CONCLUSIONS_FALLBACK_HTML
                # Mappa varianti right.* → milestones così la colonna "azioni
                # immediate" non resta vuota anche se Sonnet usa altri nomi.
                b["right"] = _normalize_conclusions_right(b["right"])
        # Skip blocchi vuoti (solo titolo, niente contenuto).
        if not _block_has_content(b):
            log.warning("Block %r skipped: no content beyond title", btype)
            continue
        safe.append(b)
    # Garanzia: l'ultimo blocco è sempre conclusions con contenuto.
    if not safe or safe[-1].get("type") != "conclusions":
        safe.append({
            "type": "conclusions",
            "title": "Conclusioni e Prossimi Passi",
            "left": {"body_html": _CONCLUSIONS_FALLBACK_HTML},
            "right": {},
        })
    return safe


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

    blocks = _normalize_blocks(analysis.get("blocks") or [])
    footer = analysis.get("footer") or {
        "line1": f"Report generato il {today} · Dati forniti dall'utente · Stime basate su skill verticali K2-AI",
        "code": code_default,
    }
    # Disclaimer obbligatorio: trasparenza sulle stime di mercato.
    footer["disclaimer"] = (
        "Le stime di traffico, volume keyword e proiezioni sono basate su benchmark di mercato. "
        "I dati reali possono variare. Verificare con Google Search Console e strumenti di analisi dedicati."
    )
    # nosemgrep: python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2 -- autoescape enabled in _env (select_autoescape html/xml); all variables are server-controlled
    return template.render(
        css=_load_css(),
        meta=meta,
        blocks=blocks,
        footer=footer,
        logo=_load_logo_data_uri(),
    )


def _html_to_pdf_bytes(html: str) -> bytes:
    """HTML → A4 PDF via WeasyPrint (sync, no headless browser).

    WeasyPrint rispetta print CSS (@page, page-break-*, named pages, running
    elements) molto meglio di Chromium headless. Niente più footer isolato
    su pagina vuota: page-break-before:avoid e break-inside:avoid vengono
    applicati correttamente.
    """
    from weasyprint import HTML

    pdf = HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf(
        # Margini delegati al CSS @page rules — pdf engine rispetta @page :first.
        presentational_hints=False,
        optimize_images=True,
    )
    return pdf


def render_pdf(analysis: Dict[str, Any], *, session_id: str) -> bytes:
    """Sync entrypoint: analysis JSON → PDF bytes (WeasyPrint sync)."""
    html = render_html(analysis, session_id=session_id)
    return _html_to_pdf_bytes(html)
