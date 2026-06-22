"""Binder WebBoost on-page — cabla `audit_seo_onpage` (k2a_agevolazioni, già vendorizzato).

Il 8e non scaricava pagine: qui aggiunge un fetcher stdlib (urllib) + parser HTML stdlib,
estrae title/meta/H1/testo/immagini dalla pagina REALE e calcola lo score on-page
deterministico col tool. Sovrascrive `diagnosi.seo_onpage` (score + valutazione + findings):
il punteggio non è più fabbricato dall'LLM.

Limite onesto: i **volumi keyword** (ricerche/mese) restano esterni per natura
(Semrush/GSC) → NON inventati qui. Solo l'on-page (densità, title, meta, H1, alt,
leggibilità) è calcolabile dalla pagina.

Fetch fallito / no url / no keyword → lascia l'output LLM + nota onesta nel meta
(nessuna sovrascrittura con numeri non verificati).
"""
from __future__ import annotations

import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))

_UA = "Mozilla/5.0 (compatible; K2A-WebBoost/1.0; +https://k2-ai.it)"
_TIMEOUT = 8
_MAX_BYTES = 2_000_000


class _Extract(HTMLParser):
    """Estrae title, meta description, H1, conteggio immagini/alt e testo visibile."""

    def __init__(self) -> None:
        super().__init__()
        self._title_parts: list[str] = []
        self._in_title = False
        self.meta_description = ""
        self.h1: list[str] = []
        self._in_h1 = False
        self._h1_buf: list[str] = []
        self.n_immagini = 0
        self.n_immagini_con_alt = 0
        self._text_parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta" and a.get("name", "").lower() == "description":
            self.meta_description = a.get("content", "") or self.meta_description
        elif tag == "h1":
            self._in_h1 = True
            self._h1_buf = []
        elif tag == "img":
            self.n_immagini += 1
            if (a.get("alt") or "").strip():
                self.n_immagini_con_alt += 1
        elif tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False
            t = "".join(self._h1_buf).strip()
            if t:
                self.h1.append(t)
        elif tag in ("script", "style") and self._skip > 0:
            self._skip -= 1

    def handle_data(self, data):
        if self._in_title:
            self._title_parts.append(data)
        if self._in_h1:
            self._h1_buf.append(data)
        if self._skip == 0 and data.strip():
            self._text_parts.append(data.strip())

    @property
    def title(self) -> str:
        return "".join(self._title_parts).strip()

    @property
    def testo(self) -> str:
        return " ".join(self._text_parts)


def fetch_html(url: str, timeout: int = _TIMEOUT) -> Optional[str]:
    if not url or not str(url).startswith(("http://", "https://")):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (url validata sopra)
            raw = r.read(_MAX_BYTES)
            enc = r.headers.get_content_charset() or "utf-8"
        return raw.decode(enc, errors="replace")
    except Exception:
        return None


def audit_html(html: str, keyword: str, url: str = ""):
    """Puro (testabile senza rete): HTML + keyword → output `audit_seo_onpage`."""
    from k2a_agevolazioni.seo import SeoOnPageInput, audit_seo_onpage

    p = _Extract()
    p.feed(html or "")
    inp = SeoOnPageInput(
        keyword=keyword, title=p.title, meta_description=p.meta_description,
        testo=p.testo, h1=p.h1, n_immagini=p.n_immagini,
        n_immagini_con_alt=p.n_immagini_con_alt, url=url,
    )
    return audit_seo_onpage(inp)


_IMPATTO = {0: "alto", 1: "medio"}        # banda: 0 critico → alto, 1 buono → medio


def _findings_da_controlli(out) -> list[dict]:
    """Costruisce i findings dai controlli reali del tool (no LLM). Enum schema-validi."""
    finds: list[dict] = []
    for c in out.controlli:
        if c.valutazione == "ottimo":
            continue
        banda = 1 if c.valutazione == "buono" else 0
        if banda == 0:
            priorita = "P1" if c.peso >= 3 else "P2"
        else:
            priorita = "P3" if c.peso >= 3 else "P4"
        finds.append({
            "id": str(c.id),
            "problema": f"{c.label}: {c.valore}",
            "perche_conta": c.label,
            "impatto": _IMPATTO.get(banda, "medio"),
            "sforzo": "rapido",
            "priorita": priorita,
        })
    return finds


def bind_seo_onpage(deliverable: dict, out) -> dict:
    """Sovrascrive diagnosi.seo_onpage con lo score/valutazione/findings deterministici."""
    so = deliverable.setdefault("diagnosi", {}).setdefault("seo_onpage", {})
    so["score"] = round(out.punteggio_0_100)
    so["valutazione_sintetica"] = f"{out.classe}: {out.giudizio}"[:300]
    finds = _findings_da_controlli(out)
    if finds:
        so["findings"] = finds
    return {"score": so["score"], "classe": out.classe,
            "criticita": list(out.criticita), "n_findings": len(finds)}


def apply_web(deliverable: dict, inputs: dict) -> tuple[dict, Optional[dict]]:
    """Cabla l'on-page SEO. Fetcha l'url del form, calcola lo score col tool, binda."""
    if not isinstance(deliverable, dict):
        return deliverable, None
    inputs = inputs or {}
    url = (inputs.get("url") or "").strip()
    seeds = inputs.get("keywords_seed") or []
    keyword = next((str(k).strip() for k in seeds if str(k).strip()), None) if isinstance(seeds, list) else None
    nota_volumi = "volumi keyword esterni (Semrush/GSC) — non valutati on-page, non inventati"
    if not url or not keyword:
        return deliverable, {"verificato": False, "nota_volumi": nota_volumi,
                             "note": "seo_onpage non verificato: url o keyword_seed assenti nel form"}
    html = fetch_html(url)
    if not html:
        return deliverable, {"verificato": False, "url": url, "nota_volumi": nota_volumi,
                             "note": "seo_onpage non verificato: pagina non raggiungibile/fetch fallito"}
    out = audit_html(html, keyword, url)
    bind_meta = bind_seo_onpage(deliverable, out)
    return deliverable, {"verificato": True, "url": url, "keyword": keyword,
                         "provenance": "audit_seo_onpage (pagina reale fetchata, stdlib)",
                         "nota_volumi": nota_volumi, **bind_meta}
