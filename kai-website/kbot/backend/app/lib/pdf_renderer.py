"""K2-AI report PDF — renderer ReportLab nativo (no HTML).

Sostituisce il vecchio renderer Jinja2+WeasyPrint che soffriva di bug
ricorrenti su page-break, footer isolato, layout colonne. ReportLab dà
controllo deterministico pixel-perfect: tabelle con `repeatRows`,
KeepTogether per blocchi atomici, BaseDocTemplate con frame body +
header (page 1) + footer (ogni pagina) via canvas onPage handlers.

Schema input (compatibile col precedente):
- analysis = {"meta": {...}, "blocks": [...], "footer": {...}}
- Block types supportati: executive_summary, executive_dashboard,
  kpi_grid, two_column, narrative_split, data_table, benchmark_table,
  severity_matrix, financial_impact, recommendations, decision_board,
  section_break, source_legend, action_list, risk_mitigation,
  conclusions, narrative.

Redesign v16: struttura a 3 livelli di lettura (Executive / Analisi /
Appendice) + scoring universale + severity + tag affidabilità dato +
impatto economico + decision board. Vedi lib/skills/report-premium-design.
"""
from __future__ import annotations

import base64
import logging
import re
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Flowable,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

log = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"


def _register_fonts() -> Dict[str, str]:
    """Registra TTF Syne/DMSans/DMMono in ReportLab. Fallback Helvetica/Courier.

    Ritorna mapping logical-name → fontName effettivo (per styling). Idempotente.
    """
    mapping = {
        "title": "Helvetica-Bold",     # Syne-Bold
        "title_sb": "Helvetica-Bold",  # Syne-SemiBold
        "title_r": "Helvetica",         # Syne-Regular
        "body": "Helvetica",            # DMSans
        "body_sb": "Helvetica-Bold",   # DMSans-SemiBold
        "body_it": "Helvetica-Oblique", # DMSans-Italic
        "mono": "Courier",              # DMMono
    }
    pairs = [
        ("title", "Syne-Bold", "Syne-Bold.ttf"),
        ("title_sb", "Syne-SemiBold", "Syne-SemiBold.ttf"),
        ("title_r", "Syne-Regular", "Syne-Regular.ttf"),
        ("body", "DMSans-Regular", "DMSans-Regular.ttf"),
        ("body_sb", "DMSans-SemiBold", "DMSans-SemiBold.ttf"),
        ("body_it", "DMSans-Italic", "DMSans-Italic.ttf"),
        ("mono", "DMMono-Regular", "DMMono-Regular.ttf"),
    ]
    registered = {n for n in pdfmetrics.getRegisteredFontNames()}
    for logical, rl_name, fname in pairs:
        if rl_name in registered:
            mapping[logical] = rl_name
            continue
        path = FONTS_DIR / fname
        if not path.exists():
            log.warning("Font missing %s — fallback to %s", fname, mapping[logical])
            continue
        try:
            pdfmetrics.registerFont(TTFont(rl_name, str(path)))
            mapping[logical] = rl_name
        except Exception as exc:
            log.warning("Font register failed %s: %s — fallback %s", rl_name, exc, mapping[logical])
    return mapping


_FONTS = _register_fonts()

# Palette Editorial Light — warm grays + gold accent, semantic colors per stato.
WHITE = colors.HexColor("#FFFFFF")
SURFACE = colors.HexColor("#FFFFFF")
SURFACE_2 = colors.HexColor("#F7F7F5")   # grigio superficie (card, righe alt)
BG_PAGE = colors.HexColor("#FFFFFF")
BORDER = colors.HexColor("#E8E8E4")      # grigio bordo
TEXT_MUTED = colors.HexColor("#888880")  # grigio testo muto (label, note)
TEXT_SOFT = colors.HexColor("#666660")   # grigio body secondario
TEXT = colors.HexColor("#1A1A1A")        # nero testo principale
TEXT_DEEP = colors.HexColor("#0A0A0A")   # nero titoli
PRIMARY = TEXT_DEEP
PRIMARY_LIGHT = TEXT_MUTED
# Accento allineato al DESIGN SYSTEM UNICO K2-AI (teal premium #00BFA6), ex oro.
# Coerenza famiglia: stesso accento dei report 8e (boost) e dei check D1.
GOLD = colors.HexColor("#00BFA6")        # teal premium (accento famiglia unica)
GOLD_LIGHT = colors.HexColor("#7FDED1")  # teal chiaro (riempimenti tenui)
ACCENT = GOLD
ACCENT_WARM = colors.HexColor("#D4821A") # ambra warning
RED = colors.HexColor("#C0392B")          # rosso alert / criticità
RED_BG = colors.HexColor("#FBF7F7")       # red tint background
RED_BORDER = colors.HexColor("#E8C8C4")
GREEN = colors.HexColor("#27765C")        # verde ok / forza
GREEN_BG = colors.HexColor("#F7FBF8")     # green tint background
GREEN_BORDER = colors.HexColor("#C4DECF")
YELLOW = ACCENT_WARM
YELLOW_BG = colors.HexColor("#FBF7EE")
YELLOW_BORDER = colors.HexColor("#E8D8B8")
INFO = colors.HexColor("#3B4A6B")
INFO_BG = colors.HexColor("#F4F5F8")

# Severity scale (matrice priorità) — 4 livelli con tint dedicati.
SEV_HIGH = colors.HexColor("#B4551E")      # arancione forte (High)
SEV_HIGH_BG = colors.HexColor("#FBF2EC")
# Critical → RED/RED_BG ; Medium → ACCENT_WARM/YELLOW_BG ; Low → TEXT_MUTED/SURFACE_2

# Tag affidabilità dato (Livello 3 / inline) — 4 stati.
TAG_META = {
    "verified": (GREEN, "Dato verificato"),
    "inference": (ACCENT_WARM, "Inferenza AI"),
    "benchmark": (INFO, "Benchmark"),
    "assumption": (RED, "Assunzione"),
}

PAGE_W, PAGE_H = A4
MARGIN_X = 20 * mm                       # spec: 20mm L/R
MARGIN_TOP = 18 * mm + 28                 # 18mm + 28pt running header
MARGIN_TOP_REST = MARGIN_TOP              # header uguale su tutte le pagine
MARGIN_BOTTOM = 16 * mm + 30              # 16mm + 30pt footer (2-line)

CONTENT_W = PAGE_W - 2 * MARGIN_X

# Stili paragrafo.
_styles = getSampleStyleSheet()


def _make_styles() -> Dict[str, ParagraphStyle]:
    """Typography Editorial Light: Syne titoli, DM Sans corpo, DM Mono dati."""
    return {
        "h1": ParagraphStyle(
            "h1", parent=_styles["Heading1"],
            fontName=_FONTS["title"], fontSize=28, leading=34,
            textColor=TEXT_DEEP, spaceAfter=4 * mm, spaceBefore=0,
        ),
        "h2": ParagraphStyle(
            "h2", parent=_styles["Heading2"],
            fontName=_FONTS["title_sb"], fontSize=14, leading=18,
            textColor=TEXT_DEEP, spaceAfter=3 * mm, spaceBefore=2 * mm,
        ),
        "h3": ParagraphStyle(
            "h3", parent=_styles["Heading3"],
            fontName=_FONTS["title_sb"], fontSize=11, leading=15,
            textColor=TEXT_DEEP, spaceAfter=2 * mm, spaceBefore=1.5 * mm,
        ),
        "body": ParagraphStyle(
            "body", parent=_styles["BodyText"],
            fontName=_FONTS["body"], fontSize=9.5, leading=14,
            textColor=TEXT, spaceAfter=2.5 * mm,
        ),
        "body_soft": ParagraphStyle(
            "body_soft", parent=_styles["BodyText"],
            fontName=_FONTS["body"], fontSize=9, leading=13,
            textColor=TEXT_SOFT, spaceAfter=2 * mm,
        ),
        "small": ParagraphStyle(
            "small", parent=_styles["BodyText"],
            fontName=_FONTS["body"], fontSize=7.5, leading=10.5,
            textColor=TEXT_MUTED, spaceAfter=1.5 * mm,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value", parent=_styles["BodyText"],
            fontName=_FONTS["title"], fontSize=22, leading=26,
            textColor=TEXT_DEEP, alignment=TA_LEFT, spaceAfter=1 * mm,
        ),
        "kpi_value_unverified": ParagraphStyle(
            "kpi_value_unv", parent=_styles["BodyText"],
            fontName=_FONTS["title"], fontSize=22, leading=26,
            textColor=ACCENT_WARM, alignment=TA_LEFT, spaceAfter=1 * mm,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label", parent=_styles["BodyText"],
            fontName=_FONTS["mono"], fontSize=7.5, leading=10,
            textColor=TEXT_MUTED, spaceAfter=2 * mm,
        ),
        "kpi_note": ParagraphStyle(
            "kpi_note", parent=_styles["BodyText"],
            fontName=_FONTS["body"], fontSize=8.5, leading=11.5,
            textColor=TEXT_MUTED, spaceAfter=1.5 * mm,
        ),
        "kpi_disclaimer": ParagraphStyle(
            "kpi_disclaimer", parent=_styles["BodyText"],
            fontName=_FONTS["body_it"], fontSize=7.5, leading=10.5,
            textColor=ACCENT_WARM, spaceAfter=1.5 * mm,
        ),
        "score_huge": ParagraphStyle(
            "score_huge", parent=_styles["BodyText"],
            fontName=_FONTS["title"], fontSize=36, leading=40,
            textColor=TEXT_DEEP, alignment=TA_CENTER,
        ),
        "score_max": ParagraphStyle(
            "score_max", parent=_styles["BodyText"],
            fontName=_FONTS["mono"], fontSize=10, leading=12,
            textColor=TEXT_MUTED, alignment=TA_CENTER, spaceAfter=2 * mm,
        ),
        "badge": ParagraphStyle(
            "badge", parent=_styles["BodyText"],
            fontName=_FONTS["mono"], fontSize=7.5, leading=10,
            textColor=TEXT, alignment=TA_CENTER,
        ),
        "table_th": ParagraphStyle(
            "table_th", parent=_styles["BodyText"],
            fontName=_FONTS["mono"], fontSize=8, leading=10,
            textColor=WHITE, alignment=TA_LEFT,
        ),
        "table_td": ParagraphStyle(
            "table_td", parent=_styles["BodyText"],
            fontName=_FONTS["body"], fontSize=9, leading=12,
            textColor=TEXT, alignment=TA_LEFT,
        ),
        "table_td_bold": ParagraphStyle(
            "table_td_bold", parent=_styles["BodyText"],
            fontName=_FONTS["body_sb"], fontSize=9, leading=12,
            textColor=TEXT_DEEP, alignment=TA_LEFT,
        ),
        "col_title_ok": ParagraphStyle(
            "col_title_ok", parent=_styles["BodyText"],
            fontName=_FONTS["title_sb"], fontSize=8, leading=11,
            textColor=GREEN, alignment=TA_LEFT, spaceAfter=2 * mm,
        ),
        "col_title_alert": ParagraphStyle(
            "col_title_alert", parent=_styles["BodyText"],
            fontName=_FONTS["title_sb"], fontSize=8, leading=11,
            textColor=RED, alignment=TA_LEFT, spaceAfter=2 * mm,
        ),
        "sprint_number": ParagraphStyle(
            "sprint_n", parent=_styles["BodyText"],
            fontName=_FONTS["title"], fontSize=28, leading=32,
            textColor=BORDER, alignment=TA_CENTER,
        ),
        "sprint_title": ParagraphStyle(
            "sprint_t", parent=_styles["BodyText"],
            fontName=_FONTS["title_sb"], fontSize=11, leading=14,
            textColor=TEXT_DEEP, spaceAfter=1 * mm,
        ),
        "sprint_meta": ParagraphStyle(
            "sprint_m", parent=_styles["BodyText"],
            fontName=_FONTS["mono"], fontSize=7.5, leading=10,
            textColor=TEXT_MUTED, spaceAfter=1 * mm,
        ),
    }


def _logo_path() -> Optional[Path]:
    p = ASSETS_DIR / "logo-k2ai.png"
    return p if p.exists() else None


def _today_it() -> str:
    months = [
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
    ]
    d = datetime.now(timezone.utc)
    return f"{d.day} {months[d.month - 1]} {d.year}"


# ---------------------------------------------------------------------------
# HTML→Paragraph conversion (compatibilità body_html prodotto da Sonnet)
# ---------------------------------------------------------------------------

_TAG_STRIP = re.compile(r"<(?!/?(?:b|strong|i|em|u|br)\b)[^>]+>", re.IGNORECASE)
_LIST_ITEM = re.compile(r"<li[^>]*>(.*?)</li>", re.IGNORECASE | re.DOTALL)
_OL_RE = re.compile(r"<ol[^>]*>(.*?)</ol>", re.IGNORECASE | re.DOTALL)
_UL_RE = re.compile(r"<ul[^>]*>(.*?)</ul>", re.IGNORECASE | re.DOTALL)
_P_SPLIT = re.compile(r"</?p[^>]*>", re.IGNORECASE)


def _html_to_paragraphs(html: str, style: ParagraphStyle, bullet_style: Optional[ParagraphStyle] = None) -> List[Flowable]:
    """Converte body_html semplice → list di Paragraph ReportLab.

    Sonnet emette body_html con tag base: <p>, <strong>, <em>, <br>,
    <ul><li>, <ol><li>. ReportLab Paragraph supporta direttamente <b>,
    <i>, <br/>, <a>. Normalizziamo + estraiamo liste.
    """
    if not html:
        return []
    bullet_style = bullet_style or style
    out: List[Flowable] = []

    # Estrai liste ordinate / non-ordinate prima, in ordine di apparizione.
    work = html
    # Replace <strong>/<em> con <b>/<i>
    work = re.sub(r"</?strong>", lambda m: "</b>" if m.group(0).startswith("</") else "<b>", work, flags=re.IGNORECASE)
    work = re.sub(r"</?em>", lambda m: "</i>" if m.group(0).startswith("</") else "<i>", work, flags=re.IGNORECASE)

    # Spezza in segmenti: list block vs prosa libera.
    segments: List[tuple] = []  # ("para"|"ol"|"ul", content)
    pos = 0
    pattern = re.compile(r"<(ol|ul)[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
    for m in pattern.finditer(work):
        if m.start() > pos:
            segments.append(("para", work[pos:m.start()]))
        segments.append((m.group(1).lower(), m.group(2)))
        pos = m.end()
    if pos < len(work):
        segments.append(("para", work[pos:]))

    for kind, content in segments:
        if kind == "para":
            # Split paragraphs on </p> + <br><br>.
            chunks = _P_SPLIT.split(content)
            for chunk in chunks:
                txt = _clean_inline(chunk)
                if txt:
                    out.append(_safe_paragraph(txt, style))
        else:
            items = _LIST_ITEM.findall(content)
            for i, it in enumerate(items, 1):
                txt = _clean_inline(it)
                if not txt:
                    continue
                marker = f"{i}." if kind == "ol" else "•"
                out.append(_safe_paragraph(f"<b>{marker}</b>&nbsp;&nbsp;{txt}", bullet_style))
    return out


def _clean_inline(txt: str) -> str:
    """Rimuove tag non-supportati, lascia <b>/<i>/<br>, normalizza whitespace."""
    if not txt:
        return ""
    txt = _TAG_STRIP.sub("", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    # Escape & ma preserva entità note + bilancia tag inline → XML valido
    txt = txt.replace("&nbsp;", " ")
    txt = _AMP_NOT_ENTITY.sub("&amp;", txt)
    txt = _balance_inline_tags(txt)
    return txt


_AMP_NOT_ENTITY = re.compile(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)")
_INLINE_TAGS = ("b", "i", "u")


def _balance_inline_tags(s: str) -> str:
    """Chiude tag <b>/<i>/<u> sbilanciati (ReportLab XML strict).

    Sonnet emette markup tipo '<b>PILLAR 1: Automazione…' senza chiusura
    quando il body_html è troncato → Paragraph.__init__ alza ValueError.
    """
    for tag in _INLINE_TAGS:
        opens = len(re.findall(rf"<{tag}\b[^>]*>", s, re.IGNORECASE))
        closes = len(re.findall(rf"</{tag}\s*>", s, re.IGNORECASE))
        if opens > closes:
            s = s + f"</{tag}>" * (opens - closes)
        elif closes > opens:
            s = f"<{tag}>" * (closes - opens) + s
    return s


def _safe_paragraph(txt: str, style: ParagraphStyle) -> Paragraph:
    """Paragraph con fallback plain-text se il parser XML fallisce.

    ReportLab Paragraph.__init__ alza ValueError su XML malformato anche
    dopo _clean_inline (es. entity sconosciute, control chars residui).
    Fallback: strip totale markup + escape & → Paragraph minimale.
    """
    try:
        return Paragraph(txt, style)
    except Exception:
        plain = re.sub(r"<[^>]+>", "", txt or "").replace("&", "&amp;")
        return Paragraph(plain or " ", style)


# ---------------------------------------------------------------------------
# Pill / badge rendering via Table cells with rounded corners
# ---------------------------------------------------------------------------

def _badge_pill(label: str, variant: str = "neutral") -> Table:
    """Pillola colorata stile badge."""
    palette = {
        "ok": (GREEN_BG, GREEN, GREEN_BORDER),
        "success": (GREEN_BG, GREEN, GREEN_BORDER),
        "warning": (YELLOW_BG, YELLOW, YELLOW_BORDER),
        "alert": (RED_BG, RED, RED_BORDER),
        "critical": (RED_BG, RED, RED_BORDER),
        "info": (INFO_BG, INFO, INFO),
        "neutral": (SURFACE_2, TEXT_SOFT, BORDER),
    }
    bg, fg, brd = palette.get(variant.lower(), palette["neutral"])
    # Solo glifi presenti in Helvetica standard: "•" sì; ●⚠✕ⓘ rendono tofu.
    icon_map = {"ok": "•", "success": "•", "warning": "•", "alert": "•", "critical": "•", "info": "•", "neutral": "•"}
    icon = icon_map.get(variant.lower(), "•")
    style = ParagraphStyle(
        "pill_text", fontName="Helvetica-Bold", fontSize=8.5, leading=10,
        textColor=fg, alignment=TA_LEFT,
    )
    p = Paragraph(f"{icon}&nbsp;&nbsp;{label}", style)
    t = Table([[p]], colWidths=[26 * mm], rowHeights=[7 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.5, brd),
        ("ROUNDEDCORNERS", [3, 3, 3, 3]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5 * mm),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


# ---------------------------------------------------------------------------
# Block renderers — ogni tipo restituisce list[Flowable]
# ---------------------------------------------------------------------------

class GaugeArc(Flowable):
    """Gauge semi-circolare nativo Canvas — sostituisce SVG via Pango."""
    def __init__(self, value: int, max_val: int = 100, width: float = 42 * mm, height: float = 26 * mm):
        super().__init__()
        self.value = max(0, min(value, max_val))
        self.max_val = max_val
        self.width = width
        self.height = height

    def wrap(self, avail_w, avail_h):
        return self.width, self.height

    def draw(self):
        c = self.canv
        cx = self.width / 2
        cy = 3 * mm
        radius = (self.width - 6 * mm) / 2
        # Track (grigio chiaro)
        c.setStrokeColor(BORDER)
        c.setLineWidth(4.2 * mm)
        c.setLineCap(1)  # round
        c.arc(cx - radius, cy - radius, cx + radius, cy + radius, 0, 180)
        # Filled arc
        pct = self.value / self.max_val
        # Color stop by pct
        if pct < 0.4:
            fill = RED
        elif pct < 0.7:
            fill = YELLOW
        else:
            fill = GREEN
        c.setStrokeColor(fill)
        end_angle = 180 * pct
        c.arc(cx - radius, cy - radius, cx + radius, cy + radius, 180 - end_angle, end_angle)
        # Score number
        c.setFillColor(PRIMARY)
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(cx, cy + radius * 0.45, str(self.value))
        c.setFillColor(TEXT_MUTED)
        c.setFont("Helvetica", 8)
        c.drawCentredString(cx, cy + radius * 0.10, f"/ {self.max_val}")


def _render_block_title(title: str, s: Dict[str, ParagraphStyle]) -> Flowable:
    """Titolo sezione Editorial Light: Syne SemiBold 14pt + linea muta 0.75pt sotto."""
    t = Table([[Paragraph(title, s["h2"])]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.75, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
    ]))
    return t


def _section(title_flow: Flowable, content_flows: List[Flowable]) -> List[Flowable]:
    """Wrap titolo + primo flowable in KeepTogether per evitare heading orfani.

    Pattern problema osservato: heading 'Conclusioni' a fondo pagina, corpo
    spinto a pagina successiva. ReportLab non sa che il titolo va col corpo.
    Fix: KeepTogether([title, first_content_flow]) lega solo i primi due —
    NON l'intero blocco (sennò row too large su contenuti corposi).
    """
    if not content_flows:
        return [title_flow]
    head = KeepTogether([title_flow, content_flows[0]])
    return [head] + content_flows[1:]


def _render_executive_summary(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    body_html = block.get("body_html") or block.get("body") or ""
    para_flows = _html_to_paragraphs(body_html, s["body"])
    gauge = block.get("gauge") or {}
    if gauge.get("value") is not None:
        try:
            g_value = int(gauge.get("value") or 0)
            g_max = int(gauge.get("max") or 100)
        except (TypeError, ValueError):
            g_value, g_max = 0, 100
        # Tabella: prosa sinistra, gauge destra.
        left_cell = para_flows or [Paragraph(_clean_inline(body_html), s["body"])]
        right_cell = [GaugeArc(g_value, g_max)]
        tbl = Table(
            [[left_cell, right_cell]],
            colWidths=[CONTENT_W * 0.66 - 18 * mm, CONTENT_W * 0.34 - 4 * mm],
        )
        tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        flows: List[Flowable] = _section(_render_block_title(block.get("title") or "Executive Summary", s), [tbl])
    else:
        flows = _section(_render_block_title(block.get("title") or "Executive Summary", s), para_flows)

    # Badges: lista verticale full-width — UNA badge per riga, icona + label
    # estesa con eventuale descrizione inline. Document-style, no grid.
    # Bug v13/v14: pill stretto e 3-col tagliavano "Fondamenta Tecniche Solide".
    badges = block.get("badges") or []
    if badges:
        # NB: usare solo glifi presenti in DMSans. ●■✕▸◆ rendono come tofu (□);
        # "•" (U+2022) sì. La variante è comunicata dal COLORE, non dalla forma.
        icon_map = {"ok": "•", "success": "•", "warning": "•", "alert": "•", "critical": "•", "neutral": "•", "info": "•"}
        color_map = {"ok": GREEN, "success": GREEN, "warning": ACCENT_WARM, "alert": RED, "critical": RED, "neutral": TEXT_MUTED, "info": INFO}
        badge_style = ParagraphStyle(
            "badge_line", parent=s["body"],
            fontName=_FONTS["body_sb"], fontSize=9, leading=13,
            textColor=TEXT_DEEP, alignment=TA_LEFT, spaceAfter=4,
        )
        flows.append(Spacer(1, 3 * mm))
        for b in badges[:9]:
            if not isinstance(b, dict):
                continue
            variant = (b.get("variant") or "neutral").lower()
            label = _clean_inline(b.get("label") or "")
            desc = _clean_inline(b.get("description") or "")
            icon = icon_map.get(variant, "•")
            color = color_map.get(variant, TEXT_MUTED)
            if desc:
                html = (
                    f'<font color="{color.hexval()}" size="11">{icon}</font>'
                    f'&nbsp;&nbsp;<b>{label}.</b>&nbsp;{desc}'
                )
            else:
                html = (
                    f'<font color="{color.hexval()}" size="11">{icon}</font>'
                    f'&nbsp;&nbsp;<b>{label}</b>'
                )
            flows.append(_safe_paragraph(html, badge_style))
    return _wrap_in_card(flows)


def _render_kpi_grid(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    """KPI documento — lista verticale full-width, una riga per KPI.

    Cambio v15: report = documento, non infografica. Niente 3-col cards.
    Ogni KPI = una riga della tabella con 3 sub-celle: LABEL | VALUE | NOTE.
    Larghezza piena pagina, scroll verticale naturale.
    """
    items = block.get("items") or block.get("kpis") or block.get("cards") or []
    valid_items = [i for i in items[:14] if isinstance(i, dict)]
    if not valid_items:
        return []
    # Pesi colonne: label 25% / value 25% / note 50%. value compatto, note descrittiva.
    col_w = [CONTENT_W * 0.25, CONTENT_W * 0.25, CONTENT_W * 0.50]
    rows: List[List[Flowable]] = []
    for item in valid_items:
        label = (item.get("label") or "").upper()
        value = str(item.get("value") or "")
        note = item.get("note") or item.get("description") or ""
        sub = item.get("sub") or item.get("subtitle") or ""
        verified = item.get("verified")
        value_style = s["kpi_value_unverified"] if verified is False else s["kpi_value"]
        value_html = _clean_inline(value)
        if verified is False and value_html:
            value_html = f"† {value_html}"
        # Cella label: piccola, mono
        label_para = _safe_paragraph(_clean_inline(label), s["kpi_label"])
        # Cella value: grande, syne bold (o ambra se non verified)
        value_para = _safe_paragraph(value_html, value_style)
        # Cella note: sub + note unificati su 2 paragrafi
        note_flows: List[Flowable] = []
        if sub:
            note_flows.append(_safe_paragraph(_clean_inline(sub), s["body_soft"]))
        if note:
            note_style = s["kpi_disclaimer"] if verified is False else s["small"]
            note_flows.append(_safe_paragraph(_clean_inline(note), note_style))
        if not note_flows:
            note_flows = [_safe_paragraph("", s["small"])]
        rows.append([label_para, value_para, note_flows])
    tbl = Table(rows, colWidths=col_w)
    style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 14),
        ("LEFTPADDING", (1, 0), (1, -1), 0),
        ("RIGHTPADDING", (1, 0), (1, -1), 14),
        ("LEFTPADDING", (2, 0), (2, -1), 14),
        ("RIGHTPADDING", (2, 0), (2, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        # Separatori orizzontali sottili tra KPI (no box esterno, no inner vertical grid)
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDER),
        # Linea top oro 1pt prima del primo KPI (unico accento gold)
        ("LINEABOVE", (0, 0), (-1, 0), 1, GOLD),
    ]
    tbl.setStyle(TableStyle(style_cmds))
    return _wrap_in_card(_section(_render_block_title(block.get("title") or "Metriche", s), [tbl]))


class _VariantMarker:
    """Placeholder per passare variant info attraverso le celle KPI."""
    def __init__(self, variant: str):
        self.variant = variant


def _render_data_table(block: dict, s: Dict[str, ParagraphStyle], *, max_width: Optional[float] = None, bare: bool = False) -> List[Flowable]:
    table_data = block.get("table") or {}
    cols = table_data.get("columns") or []
    rows = table_data.get("rows") or []
    if not cols or not rows:
        return []
    # Build flowable cells
    header_row = [Paragraph(_clean_inline(str(c)), s["table_th"]) for c in cols]
    body_rows = []
    for r in rows:
        if not isinstance(r, list):
            continue
        body_row = []
        for i, cell in enumerate(r):
            text = _clean_inline(str(cell))
            style = s["table_td_bold"] if i == 0 else s["table_td"]
            body_row.append(Paragraph(text, style))
        # Pad to col count
        while len(body_row) < len(cols):
            body_row.append(Paragraph("", s["table_td"]))
        body_rows.append(body_row)
    n_cols = len(cols)
    avail_w = max_width if max_width is not None else CONTENT_W
    col_w = avail_w / n_cols
    tbl = Table([header_row] + body_rows, colWidths=[col_w] * n_cols, repeatRows=1)
    style_cmds: List[Any] = [
        # Header riga: sfondo nero TEXT_DEEP, mono uppercase white
        ("BACKGROUND", (0, 0), (-1, 0), TEXT_DEEP),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), _FONTS["mono"]),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        # Bordi solo orizzontali 0.5pt
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER),
    ]
    # Righe alternate bianco/F7F7F5
    for i in range(1, len(body_rows) + 1):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), SURFACE_2))
    tbl.setStyle(TableStyle(style_cmds))
    content: List[Flowable] = []
    intro = block.get("intro") or block.get("description")
    if intro:
        content.append(Paragraph(_clean_inline(intro), s["body_soft"]))
        content.append(Spacer(1, 2 * mm))
    content.append(tbl)
    note = block.get("note") or block.get("footer_note")
    if note:
        content.append(Spacer(1, 2 * mm))
        content.append(Paragraph(f"<i>{_clean_inline(note)}</i>", s["small"]))
    if bare:
        # Nested mode: no block title wrap, no card divider (caller controlla larghezza)
        return content
    title_flow = _render_block_title(block.get("title") or "", s)
    return _wrap_in_card(_section(title_flow, content))


_FRAME_AVAIL_H = PAGE_H - MARGIN_TOP_REST - MARGIN_BOTTOM  # ~739.84pt
_TWO_COL_SAFETY = 60  # reserve title/spacer/divider


def _measure_flow_height(flows: List[Flowable], width: float) -> float:
    """Stima altezza totale flows + spaceBefore/spaceAfter (non inclusi in wrap()).

    KeepTogether richiede recursion sui figli perché .wrap diretto può fallire
    fuori dal doc.build context. Paragraph.wrap() ritorna SOLO l'altezza del
    box di testo, escluso spaceAfter/spaceBefore dello style — su 30 paragrafi
    con spaceAfter=7pt il delta è 200pt → stack mode mai triggered. Aggiungo
    esplicitamente i margin dello style.
    """
    total = 0.0
    for f in flows:
        try:
            if isinstance(f, KeepTogether):
                inner = getattr(f, "_content", None) or getattr(f, "_flowables", None) or []
                h = _measure_flow_height(list(inner), width)
            else:
                _, h = f.wrap(width, _FRAME_AVAIL_H * 4)
                # Aggiungi spaceBefore/spaceAfter dello style se Paragraph
                style = getattr(f, "style", None)
                if style is not None:
                    h += getattr(style, "spaceBefore", 0) or 0
                    h += getattr(style, "spaceAfter", 0) or 0
        except Exception:
            h = 0
        total += h
    return total


def _two_col_or_stack(
    left_flows: List[Flowable],
    right_flows: List[Flowable],
    inner_w: float,
    *,
    left_bg: Optional[colors.Color] = None,
    right_bg: Optional[colors.Color] = None,
) -> List[Flowable]:
    """Side-by-side via Table when fits; stacked fallback when too tall.

    ReportLab non spezza una Table cell con flowables nidificati: se un lato
    supera l'altezza del frame, esplode con 'row too large'. Misurando prima
    e fallback a stack vertico salviamo il rendering.

    Opzionale: bg per lato (verde/rosso tinted) applicato come BACKGROUND sulle
    celle quando side-by-side; in stack-mode wrappa ogni lato in un Table
    single-cell con bg + width esplicito.
    """
    if not left_flows and not right_flows:
        return []
    avail = _FRAME_AVAIL_H - _TWO_COL_SAFETY
    # Padding outer Table 12pt × 2 = 24pt sottratto dal cell content width
    cell_w = inner_w - 24
    lh = _measure_flow_height(left_flows, cell_w)
    rh = _measure_flow_height(right_flows, cell_w)
    if max(lh, rh) > avail:
        # Stack mode: emit flat flows senza Table wrap — necessario perché un
        # singolo Table cell non si spezza fra pagine (cella troppo alta su
        # contenuti lunghi). bg per lato sacrificato ma il PDF si compone.
        out: List[Flowable] = list(left_flows)
        if left_flows and right_flows:
            out.append(Spacer(1, 4 * mm))
        out.extend(right_flows)
        return out
    # Side-by-side fits: prepend CondPageBreak che forza nuova pagina se lo
    # spazio residuo è insufficiente (bug: blocco iniziato mid-page non si
    # spezza, fallisce layout). Buffer +30pt per padding + safety.
    needed_h = max(lh, rh) + 30
    tbl = Table([[left_flows, right_flows]], colWidths=[inner_w, inner_w])
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 12),
        ("RIGHTPADDING", (0, 0), (0, 0), 12),
        ("LEFTPADDING", (1, 0), (1, 0), 12),
        ("RIGHTPADDING", (1, 0), (1, 0), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]
    if left_bg is not None:
        style.append(("BACKGROUND", (0, 0), (0, 0), left_bg))
    if right_bg is not None:
        style.append(("BACKGROUND", (1, 0), (1, 0), right_bg))
    tbl.setStyle(TableStyle(style))
    return [CondPageBreak(needed_h), tbl]


def _make_side_panel(flows: List[Flowable], width: float, bg: Optional[colors.Color]) -> Flowable:
    """Wrap flows in single-cell Table con colWidths esplicito + bg opzionale.

    Stack-mode helper: previene nested Table senza width esplicito → 'row too
    large' bug (cell height = inf).
    """
    t = Table([[flows]], colWidths=[width])
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]
    if bg is not None:
        style.append(("BACKGROUND", (0, 0), (-1, -1), bg))
    t.setStyle(TableStyle(style))
    return t


def _bullet_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    """Bullet point oro + testo body. Uso • (U+2022) per visibilità reale —
    · (U+00B7 middle dot) renderizzava troppo piccolo in DM Mono."""
    return _safe_paragraph(
        f'<font color="#00BFA6" size="11"><b>•</b></font>&nbsp;&nbsp;{_clean_inline(text)}',
        style,
    )


def _render_two_column(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    """Two-column → STACK verticale full-width (documento, no infografica).

    Cambio v15: ex side-by-side verde/rosso, ora due sezioni distinte verticali:
    1. PUNTI DI FORZA (heading verde + ul/contenuto + linea sotto)
    2. CRITICITÀ (heading rosso + ul/contenuto)
    Ogni sezione occupa full width per leggibilità tipo report McKinsey.
    """
    left = block.get("left") or {}
    right = block.get("right") or {}

    def render_side_stacked(side: dict, is_left: bool) -> List[Flowable]:
        out: List[Flowable] = []
        title_style = s["col_title_ok"] if is_left else s["col_title_alert"]
        if side.get("heading"):
            heading_upper = _clean_inline(side["heading"]).upper()
            out.append(_safe_paragraph(heading_upper, title_style))
        if side.get("body_html"):
            parsed = _html_to_paragraphs(side["body_html"], s["body"])
            out.extend(parsed)
        if side.get("body"):
            out.append(_safe_paragraph(_clean_inline(side["body"]), s["body"]))
        badges = side.get("badges") or []
        for b in badges:
            if not isinstance(b, dict):
                continue
            label = _clean_inline(b.get("label") or "")
            desc = _clean_inline(b.get("description") or "")
            # Inline: label bold + desc plain, no pill colorato
            line = f"<b>{label}.</b> {desc}" if desc else f"<b>{label}</b>"
            out.append(_safe_paragraph(line, s["body"]))
        if side.get("table"):
            tbl_d = side["table"]
            if tbl_d.get("columns") and tbl_d.get("rows"):
                rendered = _render_data_table(
                    {"table": tbl_d, "title": ""}, s,
                    max_width=CONTENT_W, bare=True,
                )
                out.extend(rendered)
        callout = side.get("callout")
        if callout and isinstance(callout, dict):
            label = callout.get("label") or ""
            body = callout.get("body") or ""
            label_html = f"<b>{_clean_inline(label)}:</b> " if label else ""
            cb = _safe_paragraph(f"{label_html}{_clean_inline(body)}", s["body"])
            cbt = Table([[cb]], colWidths=[CONTENT_W - 24])
            cbt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), SURFACE_2),
                ("LINEBEFORE", (0, 0), (0, -1), 2.5, GOLD),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]))
            out.append(Spacer(1, 2 * mm))
            out.append(cbt)
        return out

    body: List[Flowable] = []
    left_flows = render_side_stacked(left, is_left=True)
    right_flows = render_side_stacked(right, is_left=False)
    body.extend(left_flows)
    if left_flows and right_flows:
        body.append(Spacer(1, 5 * mm))
        # Linea separatrice fra le due sezioni
        sep = Table([[""]], colWidths=[CONTENT_W], rowHeights=[0.5])
        sep.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER)]))
        body.append(sep)
        body.append(Spacer(1, 5 * mm))
    body.extend(right_flows)
    return _wrap_in_card(_section(_render_block_title(block.get("title") or "", s), body))


def _render_action_list(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    """Action list — vertical document style (no numero decorativo grande).

    Cambio v15: prima era Table 2 col (numero 28pt sx + content dx). Ora:
    `01. Title` inline + meta riga sotto + body riga sotto. Full width.
    Più documento, meno infografica.
    """
    actions = block.get("actions") or block.get("items") or []
    if not actions:
        return []
    flows: List[Flowable] = []
    for i, a in enumerate(actions[:12], 1):
        if not isinstance(a, dict):
            continue
        title = a.get("title") or a.get("action") or a.get("label") or ""
        body = a.get("description") or a.get("body") or ""
        priority = a.get("priority") or ""
        impact = a.get("impact") or ""
        effort = a.get("effort") or a.get("complexity") or ""
        meta = "  ·  ".join(filter(None, [
            f"PRIORITÀ {priority.upper()}" if priority else None,
            f"IMPATTO {impact.upper()}" if impact else None,
            f"EFFORT {effort.upper()}" if effort else None,
        ]))
        # Titolo: '01. Title' su una riga, syne semibold
        num_label = f'<font color="#00BFA6">{i:02d}.</font>&nbsp;&nbsp;{_clean_inline(title)}'
        flows.append(_safe_paragraph(num_label, s["sprint_title"]))
        if meta:
            flows.append(_safe_paragraph(meta, s["sprint_meta"]))
        if body:
            flows.append(_safe_paragraph(_clean_inline(body), s["body"]))
        if i < min(len(actions), 12):
            # Separator sottile fra azioni
            sep = Table([[""]], colWidths=[CONTENT_W], rowHeights=[0.5])
            sep.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER)]))
            flows.append(Spacer(1, 4))
            flows.append(sep)
            flows.append(Spacer(1, 6))
    return _wrap_in_card(_section(_render_block_title(block.get("title") or "Azioni", s), flows))


def _render_risk_mitigation(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    risks = block.get("risks") or block.get("items") or []
    if not risks:
        return []
    rows = [[Paragraph("RISCHIO", s["table_th"]), Paragraph("LIVELLO", s["table_th"]), Paragraph("MITIGAZIONE", s["table_th"])]]
    for r in risks[:10]:
        if not isinstance(r, dict):
            continue
        risk = r.get("risk") or r.get("title") or r.get("label") or ""
        level = r.get("level") or r.get("severity") or ""
        mit = r.get("mitigation") or r.get("action") or ""
        rows.append([
            Paragraph(_clean_inline(risk), s["table_td_bold"]),
            Paragraph(_clean_inline(level), s["table_td"]),
            Paragraph(_clean_inline(mit), s["table_td"]),
        ])
    col_w = (CONTENT_W) / 3
    tbl = Table(rows, colWidths=[col_w, col_w * 0.5, col_w * 1.5], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, BORDER),
    ]))
    return _wrap_in_card(_section(_render_block_title(block.get("title") or "Rischi", s), [tbl]))


class _CircleNumber(Flowable):
    """Cerchio nero pieno con numero bianco al centro (Syne Bold 10pt)."""
    def __init__(self, num: int, diameter: float = 16, color=TEXT_DEEP):
        super().__init__()
        self.num = num
        self.d = diameter
        self.color = color

    def wrap(self, aw, ah):
        return self.d, self.d

    def draw(self):
        c = self.canv
        c.setFillColor(self.color)
        c.circle(self.d / 2, self.d / 2, self.d / 2, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont(_FONTS["title_sb"], 9)
        # Approx center text
        c.drawCentredString(self.d / 2, self.d / 2 - 3, str(self.num))


_LI_SPLIT = re.compile(r"<li[^>]*>(.*?)</li>", re.IGNORECASE | re.DOTALL)


def _parse_ol_items(html: str) -> List[str]:
    """Estrae plain text dei <li> ignorando wrapping <ol>/<ul>."""
    return [_clean_inline(m) for m in _LI_SPLIT.findall(html or "")]


def _render_conclusions(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    """Conclusions Editorial: sinistra problemi con cerchio nero, destra azioni
    con callout border-left oro."""
    left = block.get("left") or {}
    right = block.get("right") or {}

    # Conclusions verticale: problemi (full width) → azioni (full width callout)
    circle_w = 20
    circle_text_w = CONTENT_W - circle_w - 8  # gap 8pt fra circle e testo

    left_heading = _clean_inline(left.get("heading") or "")
    left_flows: List[Flowable] = []
    if left_heading:
        left_flows.append(_safe_paragraph(left_heading.upper(), s["col_title_alert"]))
    problems = _parse_ol_items(left.get("body_html") or "")
    if not problems and left.get("body"):
        problems = [_clean_inline(left["body"])]
    for i, prob in enumerate(problems[:5], 1):
        if not prob:
            continue
        row = Table(
            [[_CircleNumber(i), _safe_paragraph(prob, s["body"])]],
            colWidths=[circle_w, circle_text_w],
        )
        row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 8),
            ("RIGHTPADDING", (1, 0), (1, 0), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        left_flows.append(row)
        if i < min(len(problems), 5):
            sep = Table([[""]], colWidths=[CONTENT_W], rowHeights=[0.5])
            sep.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER)]))
            left_flows.append(sep)
            left_flows.append(Spacer(1, 4))

    # Destra: azioni in callout full-width (sfondo SURFACE_2, border-left oro)
    right_inner: List[Flowable] = []
    if right.get("heading"):
        right_inner.append(_safe_paragraph(_clean_inline(right["heading"]).upper(), s["col_title_alert"]))
    milestones = right.get("milestones") or []
    for idx, m in enumerate(milestones[:6]):
        if not isinstance(m, dict):
            continue
        label = m.get("label") or ""
        items = m.get("items") or []
        if label:
            right_inner.append(_safe_paragraph(_clean_inline(label), s["sprint_title"]))
        for it in items[:6]:
            right_inner.append(_bullet_paragraph(str(it), s["body"]))
        if m.get("body_html"):
            right_inner.extend(_html_to_paragraphs(m["body_html"], s["body"]))
        if idx < len(milestones) - 1:
            right_inner.append(Spacer(1, 6))
    if not right_inner:
        right_inner = [_safe_paragraph("Nessuna azione specifica disponibile.", s["body_soft"])]

    # Callout full width
    callout_panel = Table([[right_inner]], colWidths=[CONTENT_W - 24])
    callout_panel.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SURFACE_2),
        ("LINEBEFORE", (0, 0), (0, -1), 2.5, GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    body: List[Flowable] = list(left_flows)
    if left_flows and right_inner:
        body.append(Spacer(1, 6 * mm))
    body.append(callout_panel)
    return _wrap_in_card(_section(_render_block_title(block.get("title") or "Conclusioni e Prossimi Passi", s), body))


def _render_narrative(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    body_html = block.get("body_html") or block.get("body") or ""
    flows = _html_to_paragraphs(body_html, s["body"])
    if not flows:
        return []
    return _wrap_in_card(_section(_render_block_title(block.get("title") or "", s), flows))


def _render_narrative_split(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    return _render_two_column(block, s)


# ---------------------------------------------------------------------------
# Card wrapper — bianco con shadow leggero, padding
# ---------------------------------------------------------------------------

def _wrap_in_card(flows: List[Flowable]) -> List[Flowable]:
    """Sezione con sfondo bianco visuale: applica un thin top-line accent
    sotto il titolo (gestito da _render_block_title) + spacer fra blocchi.

    Storia: il vecchio wrapper Table+KeepTogether causava 'row too large'
    quando il contenuto della card superava l'altezza pagina (ReportLab
    non sa spezzare una Table cell con flowables nidificati). Ora flowables
    flat → spezzano normalmente fra pagine.
    """
    if not flows:
        return []
    return flows + [Spacer(1, 6 * mm), _SectionDivider()]


class _SectionDivider(Flowable):
    """Linea sottile orizzontale come separatore tra sezioni — adatta ad avail_w.

    Bug fix: wrap NON deve ritornare width fissato (CONTENT_W). Quando il
    divider è nidificato in una cella stretta (es. two_column inner_w),
    ritornare CONTENT_W fa esplodere la cella → cell height infinito.
    """
    def __init__(self, color=BORDER):
        super().__init__()
        self.color = color
        self.height = 0.8 * mm
        self._draw_w = 0

    def wrap(self, avail_w, avail_h):
        self._draw_w = avail_w
        return avail_w, self.height

    def draw(self):
        c = self.canv
        c.setStrokeColor(self.color)
        c.setLineWidth(0.4)
        c.line(0, 0, self._draw_w, 0)


# ---------------------------------------------------------------------------
# Redesign v16 — blocchi decision-support (3 livelli lettura + scoring)
# ---------------------------------------------------------------------------

class _MiniBar(Flowable):
    """Barra orizzontale piena (subscore) — track grigio + fill colorato."""
    def __init__(self, pct: float, color, width: float = 40 * mm, height: float = 5):
        super().__init__()
        self.pct = max(0.0, min(pct, 1.0))
        self.color = color
        self.width = width
        self.h = height

    def wrap(self, aw, ah):
        return self.width, self.h

    def draw(self):
        c = self.canv
        r = self.h / 2
        c.setFillColor(BORDER)
        c.roundRect(0, 0, self.width, self.h, r, stroke=0, fill=1)
        w = max(self.h, self.width * self.pct)
        c.setFillColor(self.color)
        c.roundRect(0, 0, w, self.h, r, stroke=0, fill=1)


class _TrendMark(Flowable):
    """Freccia trend disegnata (no glifi font a rischio tofu): up/flat/down."""
    def __init__(self, trend: str, size: float = 8):
        super().__init__()
        self.trend = (trend or "flat").lower()
        self.s = size

    def wrap(self, aw, ah):
        return self.s, self.s

    def draw(self):
        c = self.canv
        s = self.s
        if self.trend in ("up", "rising", "su"):
            c.setFillColor(GREEN)
            c.setStrokeColor(GREEN)
            p = c.beginPath(); p.moveTo(0, 0); p.lineTo(s, 0); p.lineTo(s / 2, s); p.close()
            c.drawPath(p, stroke=0, fill=1)
        elif self.trend in ("down", "falling", "giu", "giù"):
            c.setFillColor(RED)
            p = c.beginPath(); p.moveTo(0, s); p.lineTo(s, s); p.lineTo(s / 2, 0); p.close()
            c.drawPath(p, stroke=0, fill=1)
        else:
            c.setStrokeColor(TEXT_MUTED)
            c.setLineWidth(1.4)
            c.line(0, s / 2, s, s / 2)


def _tag_html(tag: str, size: int = 11) -> str:
    """Snippet inline `<font>•</font>` colorato per lo stato affidabilità."""
    meta = TAG_META.get((tag or "").lower())
    if not meta:
        return ""
    color = meta[0]
    return f'<font color="{color.hexval()}" size="{size}">•</font>&nbsp;&nbsp;'


def _pct(value, max_val) -> float:
    try:
        v = float(value); m = float(max_val or 100)
        return max(0.0, min(v / m, 1.0)) if m else 0.0
    except (TypeError, ValueError):
        return 0.0


def _render_section_break(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    """Banda divisoria di LIVELLO (Executive / Analisi / Appendice tecnica).

    Full-width, border-left accento, mono uppercase. Non è una card.
    """
    layer = (block.get("layer") or "").lower()
    title = block.get("title") or ""
    subtitle = block.get("subtitle") or ""
    tone_map = {
        "executive": (GOLD, colors.HexColor("#F0FBF9")),
        "analysis": (TEXT_SOFT, SURFACE_2),
        "analisi": (TEXT_SOFT, SURFACE_2),
        "appendix": (TEXT_MUTED, SURFACE_2),
        "appendice": (TEXT_MUTED, SURFACE_2),
    }
    accent, bg = tone_map.get(layer, (TEXT_SOFT, SURFACE_2))
    label_style = ParagraphStyle(
        "layer_label", fontName=_FONTS["mono"], fontSize=8.5, leading=11,
        textColor=accent,
    )
    sub_style = ParagraphStyle(
        "layer_sub", fontName=_FONTS["body"], fontSize=8.5, leading=11,
        textColor=TEXT_MUTED,
    )
    cells = [[Paragraph(title.upper(), label_style)]]
    if subtitle:
        cells.append([Paragraph(subtitle, sub_style)])
    inner = Table(cells, colWidths=[CONTENT_W - 12])
    inner.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    band = Table([[inner]], colWidths=[CONTENT_W])
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, accent),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return [Spacer(1, 3 * mm), band, Spacer(1, 4 * mm)]


def _render_executive_dashboard(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    """Cruscotto direzionale — Livello 1. Gauge + subscore + top3 + verdetto."""
    flows: List[Flowable] = _section(
        _render_block_title(block.get("title") or "Cruscotto direzionale", s), [Spacer(1, 1)]
    )

    gauge = block.get("gauge") or {}
    g_val = gauge.get("value")
    status = block.get("status") or {}
    priority = block.get("priority") or {}
    color_map = {"ok": GREEN, "success": GREEN, "warning": ACCENT_WARM,
                 "alert": RED, "critical": RED, "neutral": TEXT_MUTED, "info": INFO}

    # Colonna sinistra: gauge + status pill + priorità
    left_cell: List[Flowable] = []
    if g_val is not None:
        try:
            gv = int(g_val); gm = int(gauge.get("max") or 100)
        except (TypeError, ValueError):
            gv, gm = 0, 100
        left_cell.append(GaugeArc(gv, gm))
    if status.get("label"):
        sc = color_map.get((status.get("variant") or "neutral").lower(), TEXT_MUTED)
        st_style = ParagraphStyle("dash_status", fontName=_FONTS["body_sb"], fontSize=9,
                                  leading=12, textColor=sc, alignment=TA_CENTER)
        sdot = color_map.get((status.get("variant") or "neutral").lower(), TEXT_MUTED)
        left_cell.append(Spacer(1, 2 * mm))
        left_cell.append(_safe_paragraph(
            f'<font color="{sdot.hexval()}">•</font>&nbsp;&nbsp;{_clean_inline(status["label"])}', st_style))
    if priority.get("label"):
        pc = color_map.get((priority.get("variant") or "neutral").lower(), TEXT_MUTED)
        pr_style = ParagraphStyle("dash_prio", fontName=_FONTS["body"], fontSize=8,
                                  leading=11, textColor=TEXT_MUTED, alignment=TA_CENTER)
        left_cell.append(_safe_paragraph(
            f'Priorità: <font color="{pc.hexval()}"><b>{_clean_inline(priority["label"])}</b></font>', pr_style))
    if not left_cell:
        left_cell = [Spacer(1, 1)]

    # Colonna destra: subscore rows (label | value | bar | trend)
    subs = [x for x in (block.get("subscores") or []) if isinstance(x, dict)][:6]
    right_cell: List[Flowable] = []
    if subs:
        sub_lbl = ParagraphStyle("sub_lbl", fontName=_FONTS["body"], fontSize=8.5,
                                 leading=11, textColor=TEXT_SOFT)
        sub_val = ParagraphStyle("sub_val", fontName=_FONTS["mono"], fontSize=9,
                                 leading=11, textColor=TEXT_DEEP, alignment=TA_RIGHT)
        hdr = ParagraphStyle("sub_hdr", fontName=_FONTS["mono"], fontSize=7.5,
                             leading=10, textColor=TEXT_MUTED)
        right_cell.append(Paragraph("SUBSCORE STANDARD", hdr))
        right_cell.append(Spacer(1, 2 * mm))
        bar_w = CONTENT_W * 0.62 - 34 * mm - 30
        rows = []
        for sub in subs:
            pct = _pct(sub.get("value"), sub.get("max") or 100)
            color = GREEN if pct >= 0.7 else (ACCENT_WARM if pct >= 0.45 else RED)
            rows.append([
                Paragraph(_clean_inline(sub.get("label") or ""), sub_lbl),
                Paragraph(str(sub.get("value") or ""), sub_val),
                _MiniBar(pct, color, width=max(20 * mm, bar_w)),
                _TrendMark(sub.get("trend") or "flat"),
            ])
        st = Table(rows, colWidths=[CONTENT_W * 0.62 - 34 * mm - 22 * mm - 22,
                                    18, max(20 * mm, bar_w), 12])
        st.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (1, -1), 6),
            ("RIGHTPADDING", (2, 0), (2, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        right_cell.append(st)
    if not right_cell:
        right_cell = [Spacer(1, 1)]

    top = Table([[left_cell, right_cell]],
                colWidths=[CONTENT_W * 0.36, CONTENT_W * 0.64])
    top.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 10),
        ("LEFTPADDING", (1, 0), (1, 0), 14),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    flows.append(top)

    # Top 3 criticità / opportunità
    problems = [p for p in (block.get("problems") or []) if str(p).strip()][:4]
    opportunities = [o for o in (block.get("opportunities") or []) if str(o).strip()][:4]
    if problems or opportunities:
        head_alert = ParagraphStyle("tt_alert", fontName=_FONTS["body_sb"], fontSize=8,
                                    leading=11, textColor=RED, spaceAfter=2 * mm)
        head_ok = ParagraphStyle("tt_ok", fontName=_FONTS["body_sb"], fontSize=8,
                                 leading=11, textColor=GREEN, spaceAfter=2 * mm)

        def _bullets(items, color):
            out: List[Flowable] = []
            for it in items:
                out.append(_safe_paragraph(
                    f'<font color="{color.hexval()}">•</font>&nbsp;&nbsp;{_clean_inline(str(it))}', s["body"]))
            return out or [Spacer(1, 1)]

        pl = [Paragraph("TOP 3 CRITICITÀ", head_alert)] + _bullets(problems, RED)
        ol = [Paragraph("TOP 3 OPPORTUNITÀ", head_ok)] + _bullets(opportunities, GREEN)
        grid = Table([[pl, ol]], colWidths=[CONTENT_W / 2, CONTENT_W / 2])
        grid.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOX", (0, 0), (0, 0), 0.5, BORDER),
            ("BOX", (1, 0), (1, 0), 0.5, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        flows.append(Spacer(1, 5 * mm))
        flows.append(grid)

    # Verdetto
    verdict = block.get("verdict") or {}
    vtext = verdict.get("text") or verdict.get("body")
    if vtext:
        vc = color_map.get((verdict.get("variant") or "neutral").lower(), TEXT_DEEP)
        decision = verdict.get("decision") or ""
        html = f'<b>Verdetto:</b> {_clean_inline(vtext)}'
        if decision:
            html += f' <font color="{vc.hexval()}"><b>{_clean_inline(decision)}</b></font>'
        panel = Table([[_safe_paragraph(html, s["body"])]], colWidths=[CONTENT_W - 24])
        panel.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SURFACE_2),
            ("LINEBEFORE", (0, 0), (0, -1), 2.5, vc),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        flows.append(Spacer(1, 4 * mm))
        flows.append(panel)
    return _wrap_in_card(flows)


def _render_benchmark_table(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    """Benchmark vs settore — KPI | Azienda | Settore | Delta (delta colorato)."""
    rows_in = [r for r in (block.get("rows") or []) if isinstance(r, (dict, list))]
    if not rows_in:
        return []
    cols = block.get("columns") or ["KPI", "Azienda", "Settore", "Delta"]
    header = [Paragraph(_clean_inline(str(c)), s["table_th"]) for c in cols[:4]]
    tone_color = {"ok": GREEN, "success": GREEN, "alert": RED, "critical": RED,
                  "warning": ACCENT_WARM, "neutral": TEXT_MUTED}
    _BM_CAP = 14
    body_rows = []
    for r in rows_in[:_BM_CAP]:
        if isinstance(r, dict):
            kpi = r.get("kpi") or r.get("label") or ""
            company = r.get("company") or r.get("azienda") or ""
            sector = r.get("sector") or r.get("settore") or ""
            delta = r.get("delta") or ""
            tone = (r.get("tone") or "neutral").lower()
        else:
            kpi = r[0] if len(r) > 0 else ""
            company = r[1] if len(r) > 1 else ""
            sector = r[2] if len(r) > 2 else ""
            delta = r[3] if len(r) > 3 else ""
            tone = "neutral"
        dc = tone_color.get(tone, TEXT_MUTED)
        delta_style = ParagraphStyle("bm_delta", fontName=_FONTS["mono"], fontSize=9,
                                     leading=12, textColor=dc, alignment=TA_RIGHT)
        num_r = ParagraphStyle("bm_num", fontName=_FONTS["mono"], fontSize=9,
                               leading=12, textColor=TEXT, alignment=TA_RIGHT)
        num_m = ParagraphStyle("bm_numm", fontName=_FONTS["mono"], fontSize=9,
                               leading=12, textColor=TEXT_MUTED, alignment=TA_RIGHT)
        body_rows.append([
            Paragraph(_clean_inline(str(kpi)), s["table_td_bold"]),
            Paragraph(_clean_inline(str(company)), num_r),
            Paragraph(_clean_inline(str(sector)), num_m),
            Paragraph(f"<b>{_clean_inline(str(delta))}</b>", delta_style),
        ])
    col_w = [CONTENT_W * 0.40, CONTENT_W * 0.20, CONTENT_W * 0.20, CONTENT_W * 0.20]
    tbl = Table([header] + body_rows, colWidths=col_w, repeatRows=1)
    style_cmds: List[Any] = [
        ("BACKGROUND", (0, 0), (-1, 0), TEXT_DEEP),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER),
    ]
    for i in range(1, len(body_rows) + 1):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), SURFACE_2))
    tbl.setStyle(TableStyle(style_cmds))
    content: List[Flowable] = []
    intro = block.get("intro")
    if intro:
        content.append(Paragraph(_clean_inline(intro), s["body_soft"]))
        content.append(Spacer(1, 2 * mm))
    content.append(tbl)
    if len(rows_in) > _BM_CAP:
        extra = len(rows_in) - _BM_CAP
        content.append(Spacer(1, 2 * mm))
        content.append(Paragraph(
            f'<font color="{TEXT_MUTED.hexval()}">… e altri {extra} '
            f'element{"o" if extra == 1 else "i"} (vedi versione integrale)</font>', s["small"]))
    note = block.get("note")
    if note:
        content.append(Spacer(1, 2 * mm))
        content.append(Paragraph(f"<i>{_clean_inline(note)}</i>", s["small"]))
    return _wrap_in_card(_section(_render_block_title(block.get("title") or "Benchmark vs settore", s), content))


def _render_severity_matrix(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    """Matrice priorità — Problema | Severity | Effort | ROI, severity a pill."""
    items = [x for x in (block.get("items") or block.get("rows") or []) if isinstance(x, dict)]
    if not items:
        return []
    sev_palette = {
        "critical": (RED_BG, RED), "critica": (RED_BG, RED), "alta": (SEV_HIGH_BG, SEV_HIGH),
        "high": (SEV_HIGH_BG, SEV_HIGH), "medium": (YELLOW_BG, ACCENT_WARM),
        "media": (YELLOW_BG, ACCENT_WARM), "low": (SURFACE_2, TEXT_MUTED), "bassa": (SURFACE_2, TEXT_MUTED),
    }
    roi_color = {"alto": GREEN, "high": GREEN, "medio": TEXT_SOFT, "medium": TEXT_SOFT,
                 "basso": TEXT_MUTED, "low": TEXT_MUTED}
    header = [Paragraph(t, s["table_th"]) for t in ("PROBLEMA", "SEVERITY", "EFFORT", "ROI")]
    rows = [header]
    sev_cell_variants: List[tuple] = [None]
    _SM_CAP = 12
    for it in items[:_SM_CAP]:
        sev = (it.get("severity") or it.get("level") or "").strip()
        bg, fg = sev_palette.get(sev.lower(), (SURFACE_2, TEXT_MUTED))
        sev_style = ParagraphStyle("sev_pill", fontName=_FONTS["body_sb"], fontSize=8.5,
                                   leading=11, textColor=fg, alignment=TA_CENTER)
        effort = it.get("effort") or ""
        roi = it.get("roi") or ""
        rc = roi_color.get(str(roi).lower(), TEXT_SOFT)
        roi_style = ParagraphStyle("roi_c", fontName=_FONTS["body_sb"], fontSize=9,
                                   leading=12, textColor=rc)
        rows.append([
            Paragraph(_clean_inline(it.get("problem") or it.get("title") or it.get("label") or ""), s["table_td_bold"]),
            Paragraph(_clean_inline(sev) or "—", sev_style),
            Paragraph(_clean_inline(str(effort)), s["table_td"]),
            Paragraph(_clean_inline(str(roi)), roi_style),
        ])
        sev_cell_variants.append((bg, fg))
    col_w = [CONTENT_W * 0.46, CONTENT_W * 0.20, CONTENT_W * 0.17, CONTENT_W * 0.17]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    style_cmds: List[Any] = [
        ("BACKGROUND", (0, 0), (-1, 0), TEXT_DEEP),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER),
    ]
    for i, variant in enumerate(sev_cell_variants):
        if variant is None:
            continue
        bg, _fg = variant
        style_cmds.append(("BACKGROUND", (1, i), (1, i), bg))
    tbl.setStyle(TableStyle(style_cmds))
    content: List[Flowable] = []
    intro = block.get("intro")
    if intro:
        content.append(Paragraph(_clean_inline(intro), s["body_soft"]))
        content.append(Spacer(1, 2 * mm))
    content.append(tbl)
    if len(items) > _SM_CAP:
        extra = len(items) - _SM_CAP
        content.append(Spacer(1, 2 * mm))
        content.append(Paragraph(
            f'<font color="{TEXT_MUTED.hexval()}">… e altri {extra} '
            f'element{"o" if extra == 1 else "i"} (vedi versione integrale)</font>', s["small"]))
    return _wrap_in_card(_section(_render_block_title(block.get("title") or "Matrice priorità", s), content))


def _render_financial_impact(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    """Impatto economico — 2 pannelli: costo inazione (rosso) vs upside (verde)."""
    inaction = block.get("inaction") or {}
    action = block.get("action") or {}
    if not (inaction or action):
        return []

    def _panel(data: dict, accent, bg, border, default_label: str) -> List[Flowable]:
        lbl = ParagraphStyle("fi_lbl", fontName=_FONTS["body_sb"], fontSize=8,
                             leading=11, textColor=accent, spaceAfter=2 * mm)
        big = ParagraphStyle("fi_big", fontName=_FONTS["title"], fontSize=24,
                             leading=27, textColor=accent, spaceAfter=1 * mm)
        note = ParagraphStyle("fi_note", fontName=_FONTS["body"], fontSize=8.5,
                              leading=12, textColor=accent)
        inner: List[Flowable] = [Paragraph((data.get("label") or default_label).upper(), lbl)]
        if data.get("value"):
            inner.append(Paragraph(_clean_inline(str(data["value"])), big))
        if data.get("note"):
            inner.append(Paragraph(_clean_inline(data["note"]), note))
        cell = Table([[inner]], colWidths=[CONTENT_W / 2 - 6])
        cell.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("BOX", (0, 0), (-1, -1), 0.5, border),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        return [cell]

    left = _panel(inaction, RED, RED_BG, RED_BORDER, "Se non agisci")
    right = _panel(action, GREEN, GREEN_BG, GREEN_BORDER, "Se agisci")
    grid = Table([[left, right]], colWidths=[CONTENT_W / 2, CONTENT_W / 2])
    grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 6),
        ("LEFTPADDING", (1, 0), (1, 0), 6),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    return _wrap_in_card(_section(
        _render_block_title(block.get("title") or "Impatto economico", s), [grid]))


def _render_recommendations(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    """Azioni raccomandate per orizzonte temporale (0-30gg / 1-3m / 3-12m)."""
    horizons = [h for h in (block.get("horizons") or []) if isinstance(h, dict)]
    if not horizons:
        return []
    tone_color = {"alert": RED, "critical": RED, "warning": ACCENT_WARM,
                  "ok": GREEN, "success": GREEN, "neutral": TEXT_SOFT, "info": INFO}
    default_tones = [RED, ACCENT_WARM, GREEN]
    flows: List[Flowable] = []
    intro = block.get("intro")
    if intro:
        flows.append(Paragraph(_clean_inline(intro), s["body_soft"]))
        flows.append(Spacer(1, 2 * mm))
    for idx, h in enumerate(horizons[:5]):
        color = tone_color.get((h.get("tone") or "").lower(), default_tones[idx % 3])
        lbl_style = ParagraphStyle("rec_lbl", fontName=_FONTS["mono"], fontSize=8,
                                   leading=11, textColor=color)
        items = [str(x) for x in (h.get("items") or []) if str(x).strip()]
        item_flows: List[Flowable] = []
        for it in items[:8]:
            item_flows.append(_bullet_paragraph(_clean_inline(it), s["body"]))
        if not item_flows:
            item_flows = [Spacer(1, 1)]
        row = Table([[Paragraph((h.get("label") or "").upper(), lbl_style), item_flows]],
                    colWidths=[32 * mm, CONTENT_W - 32 * mm])
        row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 10),
            ("LEFTPADDING", (1, 0), (1, 0), 10),
            ("RIGHTPADDING", (1, 0), (1, 0), 0),
            ("LINEBEFORE", (1, 0), (1, 0), 2, color),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        flows.append(row)
        if idx < min(len(horizons), 5) - 1:
            flows.append(Spacer(1, 3 * mm))
    return _wrap_in_card(_section(
        _render_block_title(block.get("title") or "Azioni raccomandate", s), flows))


def _render_decision_board(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    """Decision Board — riga finale decisionale (N celle, ultima evidenziata)."""
    cells = [c for c in (block.get("cells") or block.get("items") or []) if isinstance(c, dict)]
    if not cells:
        return []
    cells = cells[:6]
    color_map = {"ok": GREEN, "success": GREEN, "warning": ACCENT_WARM,
                 "alert": RED, "critical": RED, "neutral": TEXT_DEEP, "info": INFO}
    lbl_style = ParagraphStyle("db_lbl", fontName=_FONTS["mono"], fontSize=7.5,
                               leading=10, textColor=TEXT_MUTED, alignment=TA_LEFT)
    row_cells: List[List[Flowable]] = []
    n = len(cells)
    col_w = CONTENT_W / n
    style_cmds: List[Any] = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("LINEAFTER", (0, 0), (-2, -1), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]
    for i, c in enumerate(cells):
        vc = color_map.get((c.get("variant") or "neutral").lower(), TEXT_DEEP)
        val_style = ParagraphStyle(f"db_val_{i}", fontName=_FONTS["body_sb"], fontSize=11,
                                   leading=14, textColor=vc)
        stack = [Paragraph(_clean_inline(c.get("label") or ""), lbl_style), Spacer(1, 1.5 * mm),
                 _safe_paragraph(_clean_inline(str(c.get("value") or "")), val_style)]
        row_cells.append(stack)
        variant = (c.get("variant") or "").lower()
        if variant in ("ok", "success"):
            style_cmds.append(("BACKGROUND", (i, 0), (i, 0), GREEN_BG))
        elif variant in ("alert", "critical"):
            style_cmds.append(("BACKGROUND", (i, 0), (i, 0), RED_BG))
    tbl = Table([row_cells], colWidths=[col_w] * n)
    tbl.setStyle(TableStyle(style_cmds))

    head_style = ParagraphStyle("db_head", fontName=_FONTS["mono"], fontSize=9,
                                leading=12, textColor=WHITE)
    head = Table([[Paragraph((block.get("title") or "DECISION BOARD").upper(), head_style)]],
                 colWidths=[CONTENT_W])
    head.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEXT_DEEP),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    wrapper = Table([[head], [tbl]], colWidths=[CONTENT_W])
    wrapper.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, TEXT_DEEP),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [Spacer(1, 4 * mm), KeepTogether([wrapper]), Spacer(1, 6 * mm), _SectionDivider()]


def _render_source_legend(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    """Legenda affidabilità dato + elenco fatti/inferenze/benchmark/assunzioni."""
    flows: List[Flowable] = _section(
        _render_block_title(block.get("title") or "Affidabilità dei dati", s), [Spacer(1, 1)])
    # Legenda 4 stati su una riga
    leg_style = ParagraphStyle("leg", fontName=_FONTS["body"], fontSize=8.5,
                               leading=12, textColor=TEXT_SOFT)
    legend_parts = []
    for tag, (color, label) in TAG_META.items():
        legend_parts.append(f'<font color="{color.hexval()}" size="11">•</font>&nbsp;{label}')
    flows.append(_safe_paragraph("&nbsp;&nbsp;&nbsp;".join(legend_parts), leg_style))
    flows.append(Spacer(1, 3 * mm))
    items = [x for x in (block.get("items") or []) if isinstance(x, dict)]
    _CAP = 20
    for it in items[:_CAP]:
        tag_html = _tag_html(it.get("tag") or "", 11)
        text = _clean_inline(it.get("text") or "")
        note = _clean_inline(it.get("note") or "")
        html = f'{tag_html}{text}'
        if note:
            html += f' <font color="{TEXT_MUTED.hexval()}">— {note}</font>'
        flows.append(_safe_paragraph(html, s["body"]))
    if len(items) > _CAP:
        extra = len(items) - _CAP
        flows.append(Spacer(1, 1 * mm))
        flows.append(_safe_paragraph(
            f'<font color="{TEXT_MUTED.hexval()}">… e altri {extra} '
            f'element{"o" if extra == 1 else "i"} (vedi versione integrale)</font>',
            s["small"]))
    return _wrap_in_card(flows)


# ---------------------------------------------------------------------------
# Block dispatcher
# ---------------------------------------------------------------------------

_BLOCK_RENDERERS = {
    "executive_summary": _render_executive_summary,
    "executive_dashboard": _render_executive_dashboard,
    "kpi_grid": _render_kpi_grid,
    "data_table": _render_data_table,
    "benchmark_table": _render_benchmark_table,
    "severity_matrix": _render_severity_matrix,
    "financial_impact": _render_financial_impact,
    "recommendations": _render_recommendations,
    "decision_board": _render_decision_board,
    "section_break": _render_section_break,
    "source_legend": _render_source_legend,
    "two_column": _render_two_column,
    "narrative_split": _render_narrative_split,
    "action_list": _render_action_list,
    "risk_mitigation": _render_risk_mitigation,
    "conclusions": _render_conclusions,
    "narrative": _render_narrative,
}


def _render_blocks(blocks: List[dict], s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    out: List[Flowable] = []
    for b in blocks:
        if not isinstance(b, dict):
            continue
        btype = b.get("type") or "narrative"
        renderer = _BLOCK_RENDERERS.get(btype, _render_narrative)
        try:
            rendered = renderer(b, s)
        except Exception:
            log.exception("Block render failed for type=%s", btype)
            continue
        out.extend(rendered)
    return out


# ---------------------------------------------------------------------------
# Header / footer canvas handlers
# ---------------------------------------------------------------------------

def _draw_running_header(c: Canvas, doc: BaseDocTemplate) -> None:
    """Running header 28pt su OGNI pagina — sfondo F7F7F5, bordo bottom oro 1pt.

    Sinistra: 'K²-AI' (Syne Bold 16pt) + nome report (DM Mono 8pt muto)
    Destra: sezione corrente (DM Mono 8pt oro upper) + 'Pag. N' (DM Mono 8pt nero)
    """
    title = getattr(doc, "_report_title", "Report Premium")
    section = getattr(doc, "_current_section", "")
    page_num = c.getPageNumber()

    header_h = 28  # pt
    y_top = PAGE_H
    y_bottom = y_top - header_h

    c.saveState()
    c.setFillColor(SURFACE_2)
    c.rect(0, y_bottom, PAGE_W, header_h, stroke=0, fill=1)
    # Bordo bottom oro 1pt
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(0, y_bottom, PAGE_W, y_bottom)

    # Sinistra: brand + report name
    c.setFillColor(TEXT_DEEP)
    c.setFont(_FONTS["title"], 16)
    c.drawString(MARGIN_X, y_bottom + 9, "K²-AI")
    c.setFillColor(TEXT_MUTED)
    c.setFont(_FONTS["mono"], 8)
    title_short = (title[:60] + "…") if len(title) > 60 else title
    c.drawString(MARGIN_X + 60, y_bottom + 10, title_short)

    # Destra: sezione (oro upper) + pag. N (nero)
    page_label = f"PAG. {page_num:02d}"
    c.setFillColor(TEXT_DEEP)
    c.setFont(_FONTS["mono"], 8)
    c.drawRightString(PAGE_W - MARGIN_X, y_bottom + 10, page_label)
    if section:
        c.setFillColor(GOLD)
        sec_upper = section.upper()[:42]
        page_label_w = c.stringWidth(page_label, _FONTS["mono"], 8)
        c.drawRightString(PAGE_W - MARGIN_X - page_label_w - 10, y_bottom + 10, sec_upper)
    c.restoreState()


def _draw_footer(c: Canvas, doc: BaseDocTemplate) -> None:
    """Footer 2 righe: top contatti+codice; bottom disclaimer full-width.

    Bug v13: codice centrato + disclaimer destro overlap (no truncation
    sufficiente). Layout split su 2 righe risolve + dà più spazio.
    """
    footer = getattr(doc, "_report_footer", {}) or {}
    code = footer.get("code") or ""
    disclaimer = footer.get("disclaimer") or ""

    footer_h = 30
    c.saveState()
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(MARGIN_X, footer_h, PAGE_W - MARGIN_X, footer_h)

    c.setFillColor(TEXT_MUTED)
    # Riga 1 (top): contatti sinistra, codice destra
    c.setFont(_FONTS["body"], 7.5)
    c.drawString(MARGIN_X, footer_h - 11, "k2-ai.it  ·  info@k2-ai.it")
    if code:
        c.setFont(_FONTS["mono"], 7.5)
        c.drawRightString(PAGE_W - MARGIN_X, footer_h - 11, code)
    # Riga 2 (bottom): disclaimer full-width, italic.
    # Misura la larghezza REALE (non stimata) e, se eccede, wrappa su 2 righe
    # spezzando sugli spazi; solo se nemmeno 2 righe bastano riduce il font —
    # mai troncare il testo legale con "…".
    if disclaimer:
        font, size = _FONTS["body_it"], 7.0
        avail = PAGE_W - 2 * MARGIN_X
        if c.stringWidth(disclaimer, font, size) <= avail:
            c.setFont(font, size)
            c.drawString(MARGIN_X, footer_h - 23, disclaimer)
        else:
            # Prova a comporlo su 2 righe; riduci il corpo finché entrambe stanno.
            lines: List[str] = []
            for trial in (7.0, 6.5, 6.0, 5.5):
                lines = _wrap_by_width(c, disclaimer, font, trial, avail)
                if len(lines) <= 2:
                    size = trial
                    break
            else:
                # Testo ancora troppo lungo: tieni le prime 2 righe al corpo minimo
                # (nessun troncamento di parole — solo overflow oltre la 2ª riga).
                size = 5.5
                lines = lines[:2]
            c.setFont(font, size)
            # 2 righe strette dentro l'altezza footer: y=footer_h-19 e footer_h-27
            base_y = footer_h - 19 if len(lines) > 1 else footer_h - 23
            for i, ln in enumerate(lines[:2]):
                c.drawString(MARGIN_X, base_y - i * (size + 1.5), ln)
    c.restoreState()


def _on_first_page(c: Canvas, doc: BaseDocTemplate) -> None:
    _draw_running_header(c, doc)
    _draw_footer(c, doc)


def _on_later_pages(c: Canvas, doc: BaseDocTemplate) -> None:
    _draw_running_header(c, doc)
    _draw_footer(c, doc)


def _wrap_text(text: str, max_chars: int) -> List[str]:
    """Word-wrap raw text (no paragraph reflow needed for short strings)."""
    words = text.split()
    lines: List[str] = []
    cur = ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_chars:
            cur = cur + " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _wrap_by_width(c: Canvas, text: str, font: str, size: float, max_w: float) -> List[str]:
    """Word-wrap misurando la larghezza reale (canvas.stringWidth), non i caratteri."""
    words = text.split()
    lines: List[str] = []
    cur = ""
    for w in words:
        candidate = w if not cur else cur + " " + w
        if c.stringWidth(candidate, font, size) <= max_w:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# Block normalization — pre-process JSON Sonnet (compat con vecchio renderer)
# ---------------------------------------------------------------------------

_TWO_SIDE_TYPES = {"two_column", "narrative_split", "conclusions"}

# Fallback DOMINIO-NEUTRO: vale per qualsiasi verticale (ingegneria, legale,
# fiscale, hospitality, ...). NON usare gergo SEO (GSC, keyword, on-page): il
# K-BOT serve tutti i settori, non solo il marketing.
_CONCLUSIONS_FALLBACK_HTML = (
    "<p>I dati raccolti in sessione non sono ancora sufficienti per conclusioni "
    "dettagliate. Prossimi passi consigliati:</p>"
    "<ol>"
    "<li>Raccogliere i dati di baseline del processo (volumi, tempi e costi attuali).</li>"
    "<li>Identificare 2-3 priorità operative ad alto impatto.</li>"
    "<li>Verificare i risultati a 30/60/90 giorni con indicatori misurabili.</li>"
    "</ol>"
)

_CONCLUSIONS_RIGHT_FALLBACK = {
    "heading": "3 azioni immediate (settimana 1)",
    "milestones": [
        {"label": "Raccolta dati", "tone": "neutral", "items": ["Definire le metriche di partenza (volumi, tempi, costi)", "Centralizzare le fonti dati rilevanti"]},
        {"label": "Primo intervento", "tone": "warning", "items": ["Selezionare 1 processo pilota ad alto impatto"]},
        {"label": "Misurazione 30/60/90", "tone": "neutral", "items": ["Definire 2-3 KPI con baseline esplicita"]},
    ],
}


def _normalize_conclusions_right(right: dict) -> dict:
    if not isinstance(right, dict):
        return dict(_CONCLUSIONS_RIGHT_FALLBACK)
    out = dict(right)
    if not out.get("heading"):
        for k in ("title", "subtitle", "label"):
            if out.get(k):
                out["heading"] = out[k]
                break
    milestones = out.get("milestones")
    if isinstance(milestones, list) and milestones and any(isinstance(m, dict) for m in milestones):
        return out
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
    items = out.get("items")
    if isinstance(items, list) and items:
        out["milestones"] = [{"label": out.get("heading") or "Azioni", "items": [str(x) for x in items], "tone": "neutral"}]
        return out
    if out.get("body_html") or out.get("body"):
        return out
    fallback = dict(_CONCLUSIONS_RIGHT_FALLBACK)
    if out.get("heading"):
        fallback["heading"] = out["heading"]
    return fallback


def _block_has_content(block: dict) -> bool:
    for key, val in block.items():
        if key in ("type", "title"):
            continue
        if isinstance(val, str) and val.strip():
            return True
        if isinstance(val, dict):
            for sub_val in val.values():
                if isinstance(sub_val, str) and sub_val.strip():
                    return True
                if isinstance(sub_val, (list, dict)) and sub_val:
                    return True
        if isinstance(val, list) and val:
            return True
    return False


def _normalize_blocks(blocks: list) -> list:
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
            if btype == "conclusions":
                if not b["left"].get("body_html"):
                    body = b["left"].get("body") or b.get("body_html") or b.get("body")
                    b["left"]["body_html"] = body or _CONCLUSIONS_FALLBACK_HTML
                b["right"] = _normalize_conclusions_right(b["right"])
        if not _block_has_content(b):
            log.warning("Block %r skipped: no content", btype)
            continue
        safe.append(b)
    _terminal = {"conclusions", "decision_board", "source_legend"}
    if not safe or safe[-1].get("type") not in _terminal:
        safe.append({
            "type": "conclusions",
            "title": "Conclusioni e Prossimi Passi",
            "left": {"body_html": _CONCLUSIONS_FALLBACK_HTML},
            "right": dict(_CONCLUSIONS_RIGHT_FALLBACK),
        })
    return safe


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_pdf(analysis: Dict[str, Any], *, session_id: str) -> bytes:
    """Genera PDF da analysis JSON via ReportLab nativo.

    Mantiene la firma del vecchio renderer per compat con generate_pdf.py.
    """
    buf = BytesIO()
    meta = dict(analysis.get("meta") or {})
    today = _today_it()
    code_default = f"K2AI-{session_id[:4].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    title = meta.get("title") or "Report operativo K2-AI"
    kicker = meta.get("kicker") or "Report Premium"
    meta_lines = meta.get("client_meta_lines") or [
        meta.get("client") or "K2-AI",
        f"Generato il {today}",
        f"Codice: {code_default}",
    ]

    footer = analysis.get("footer") or {}
    footer.setdefault("line1", f"Report generato il {today} · Stime basate su skill verticali K2-AI")
    footer.setdefault("code", code_default)
    footer.setdefault("disclaimer",
        "Le stime e le proiezioni contenute nel report sono basate sui dati forniti in sessione "
        "e su benchmark di mercato. I valori reali possono variare in base al contesto specifico. "
        "Si raccomanda una verifica con i dati gestionali interni prima di decisioni operative."
    )

    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
        title=title, author="K2-AI",
    )
    # Stash report meta on the doc object so canvas handlers can access.
    doc._report_title = title
    doc._report_kicker = kicker
    doc._report_meta_lines = meta_lines
    doc._report_footer = footer

    frame_p1 = Frame(
        MARGIN_X, MARGIN_BOTTOM,
        CONTENT_W, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        showBoundary=0,
    )
    frame_rest = Frame(
        MARGIN_X, MARGIN_BOTTOM,
        CONTENT_W, PAGE_H - MARGIN_TOP_REST - MARGIN_BOTTOM,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        showBoundary=0,
    )
    doc.addPageTemplates([
        PageTemplate(id="first", frames=[frame_p1], onPage=_on_first_page),
        PageTemplate(id="later", frames=[frame_rest], onPage=_on_later_pages),
    ])

    styles = _make_styles()
    blocks = _normalize_blocks(analysis.get("blocks") or [])
    story = _render_blocks(blocks, styles)
    if not story:
        story = [Paragraph("Nessun contenuto disponibile.", styles["body"])]

    # Force page-template switch after first frame fill
    def _next_template_first():
        from reportlab.platypus.doctemplate import NextPageTemplate
        return NextPageTemplate("later")

    final_story: List[Flowable] = [_next_template_first()]
    final_story.extend(story)
    try:
        doc.build(final_story)
    except Exception:
        log.exception("PDF build failed")
        raise
    return buf.getvalue()


def render_html(analysis: Dict[str, Any], *, session_id: str) -> str:  # pragma: no cover - legacy compat
    """Stub: il renderer ora produce PDF nativo, niente HTML intermedio."""
    return "<!-- render_html legacy stub, use render_pdf -->"


def _html_to_pdf_bytes(html: str) -> bytes:
    """Legacy shim per export.py (render-message-pdf single-bubble).

    Estrae testo da HTML semplice (heading/p/li/strong/em) e produce un PDF
    minimale con Paragraph ReportLab. Non sostituisce render_pdf — è solo
    per il vecchio endpoint message-export.
    """
    buf = BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=15 * mm, bottomMargin=15 * mm,
    )
    frame = Frame(MARGIN_X, 15 * mm, CONTENT_W, PAGE_H - 30 * mm,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="plain", frames=[frame])])
    styles = _make_styles()

    # Strip outer html/body
    work = re.sub(r"</?(?:html|body|head|meta|title)[^>]*>", "", html, flags=re.IGNORECASE)
    # Split on h1-h4 + p + ul/ol
    flows: List[Flowable] = []
    head_re = re.compile(r"<(h[1-4])[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
    last = 0
    for m in head_re.finditer(work):
        if m.start() > last:
            chunk = work[last:m.start()]
            flows.extend(_html_to_paragraphs(chunk, styles["body"]))
        level = m.group(1).lower()
        style = styles["h1"] if level == "h1" else styles["h2"] if level == "h2" else styles["h3"]
        flows.append(Paragraph(_clean_inline(m.group(2)), style))
        last = m.end()
    if last < len(work):
        flows.extend(_html_to_paragraphs(work[last:], styles["body"]))
    if not flows:
        flows = [Paragraph("(documento vuoto)", styles["body"])]
    doc.build(flows)
    return buf.getvalue()
