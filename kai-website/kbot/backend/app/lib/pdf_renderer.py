"""K2-AI report PDF — renderer ReportLab nativo (no HTML).

Sostituisce il vecchio renderer Jinja2+WeasyPrint che soffriva di bug
ricorrenti su page-break, footer isolato, layout colonne. ReportLab dà
controllo deterministico pixel-perfect: tabelle con `repeatRows`,
KeepTogether per blocchi atomici, BaseDocTemplate con frame body +
header (page 1) + footer (ogni pagina) via canvas onPage handlers.

Schema input (compatibile col precedente):
- analysis = {"meta": {...}, "blocks": [...], "footer": {...}}
- Block types supportati: executive_summary, kpi_grid, two_column,
  narrative_split, data_table, action_list, risk_mitigation,
  conclusions, narrative.
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
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
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

# Palette K2-AI (allineata al vecchio CSS).
PRIMARY = colors.HexColor("#0F2544")
PRIMARY_LIGHT = colors.HexColor("#1A3A6B")
ACCENT = colors.HexColor("#C2410C")
ACCENT_WARM = colors.HexColor("#D97706")
BG_PAGE = colors.HexColor("#F0F2F5")
SURFACE = colors.HexColor("#FFFFFF")
SURFACE_2 = colors.HexColor("#F8FAFC")
BORDER = colors.HexColor("#E2E8F0")
TEXT = colors.HexColor("#1A1A2E")
TEXT_SOFT = colors.HexColor("#475569")
TEXT_MUTED = colors.HexColor("#64748B")
GREEN = colors.HexColor("#16A34A")
GREEN_BG = colors.HexColor("#DCFCE7")
GREEN_BORDER = colors.HexColor("#86EFAC")
YELLOW = colors.HexColor("#CA8A04")
YELLOW_BG = colors.HexColor("#FEF9C3")
YELLOW_BORDER = colors.HexColor("#FDE68A")
RED = colors.HexColor("#DC2626")
RED_BG = colors.HexColor("#FEE2E2")
RED_BORDER = colors.HexColor("#FCA5A5")
INFO = colors.HexColor("#1D4ED8")
INFO_BG = colors.HexColor("#DBEAFE")
WHITE = colors.HexColor("#FFFFFF")

PAGE_W, PAGE_H = A4
MARGIN_X = 14 * mm
MARGIN_TOP = 28 * mm  # banner space page 1
MARGIN_TOP_REST = 14 * mm
MARGIN_BOTTOM = 22 * mm  # footer space

CONTENT_W = PAGE_W - 2 * MARGIN_X

# Stili paragrafo.
_styles = getSampleStyleSheet()


def _make_styles() -> Dict[str, ParagraphStyle]:
    return {
        "h1": ParagraphStyle(
            "h1", parent=_styles["Heading1"],
            fontName="Helvetica-Bold", fontSize=18, leading=22,
            textColor=PRIMARY, spaceAfter=4 * mm, spaceBefore=0,
        ),
        "h2": ParagraphStyle(
            "h2", parent=_styles["Heading2"],
            fontName="Helvetica-Bold", fontSize=13, leading=16,
            textColor=TEXT, spaceAfter=3 * mm, spaceBefore=2 * mm,
            borderPadding=0,
        ),
        "h3": ParagraphStyle(
            "h3", parent=_styles["Heading3"],
            fontName="Helvetica-Bold", fontSize=10.5, leading=14,
            textColor=TEXT, spaceAfter=2 * mm, spaceBefore=1.5 * mm,
        ),
        "body": ParagraphStyle(
            "body", parent=_styles["BodyText"],
            fontName="Helvetica", fontSize=10, leading=14.5,
            textColor=TEXT, spaceAfter=2.5 * mm,
        ),
        "body_soft": ParagraphStyle(
            "body_soft", parent=_styles["BodyText"],
            fontName="Helvetica", fontSize=9.5, leading=13.5,
            textColor=TEXT_SOFT, spaceAfter=2 * mm,
        ),
        "small": ParagraphStyle(
            "small", parent=_styles["BodyText"],
            fontName="Helvetica", fontSize=8.5, leading=11.5,
            textColor=TEXT_MUTED, spaceAfter=1.5 * mm,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value", parent=_styles["BodyText"],
            fontName="Helvetica-Bold", fontSize=22, leading=26,
            textColor=PRIMARY, alignment=TA_LEFT, spaceAfter=1 * mm,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label", parent=_styles["BodyText"],
            fontName="Helvetica", fontSize=7.5, leading=10,
            textColor=TEXT_MUTED, spaceAfter=2 * mm,
        ),
        "kpi_note": ParagraphStyle(
            "kpi_note", parent=_styles["BodyText"],
            fontName="Helvetica", fontSize=9, leading=12.5,
            textColor=TEXT_SOFT, spaceAfter=1.5 * mm,
        ),
        "score_huge": ParagraphStyle(
            "score_huge", parent=_styles["BodyText"],
            fontName="Helvetica-Bold", fontSize=36, leading=40,
            textColor=PRIMARY, alignment=TA_CENTER,
        ),
        "score_max": ParagraphStyle(
            "score_max", parent=_styles["BodyText"],
            fontName="Helvetica", fontSize=10, leading=12,
            textColor=TEXT_MUTED, alignment=TA_CENTER, spaceAfter=2 * mm,
        ),
        "badge": ParagraphStyle(
            "badge", parent=_styles["BodyText"],
            fontName="Helvetica-Bold", fontSize=8.5, leading=11,
            textColor=TEXT, alignment=TA_CENTER,
        ),
        "table_th": ParagraphStyle(
            "table_th", parent=_styles["BodyText"],
            fontName="Helvetica-Bold", fontSize=8.5, leading=11,
            textColor=WHITE, alignment=TA_LEFT,
        ),
        "table_td": ParagraphStyle(
            "table_td", parent=_styles["BodyText"],
            fontName="Helvetica", fontSize=9, leading=12.5,
            textColor=TEXT_SOFT, alignment=TA_LEFT,
        ),
        "table_td_bold": ParagraphStyle(
            "table_td_bold", parent=_styles["BodyText"],
            fontName="Helvetica-Bold", fontSize=9, leading=12.5,
            textColor=TEXT, alignment=TA_LEFT,
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
                    out.append(Paragraph(txt, style))
        else:
            items = _LIST_ITEM.findall(content)
            for i, it in enumerate(items, 1):
                txt = _clean_inline(it)
                if not txt:
                    continue
                marker = f"{i}." if kind == "ol" else "•"
                out.append(Paragraph(f"<b>{marker}</b>&nbsp;&nbsp;{txt}", bullet_style))
    return out


def _clean_inline(txt: str) -> str:
    """Rimuove tag non-supportati, lascia <b>/<i>/<br>, normalizza whitespace."""
    if not txt:
        return ""
    txt = _TAG_STRIP.sub("", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    # Escape & ma preserva entità note
    txt = txt.replace("&nbsp;", " ")
    return txt


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
    icon_map = {"ok": "●", "success": "●", "warning": "⚠", "alert": "✕", "critical": "✕", "info": "ⓘ", "neutral": "●"}
    icon = icon_map.get(variant.lower(), "●")
    style = ParagraphStyle(
        "pill_text", fontName="Helvetica-Bold", fontSize=8.5, leading=10,
        textColor=fg, alignment=TA_LEFT,
    )
    p = Paragraph(f"{icon}&nbsp;&nbsp;{label}", style)
    t = Table([[p]], colWidths=[None], rowHeights=[7 * mm])
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
    """Titolo blocco con barra orange accent sotto."""
    t = Table([[Paragraph(title, s["h2"])]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1.2, ACCENT),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
    ]))
    return t


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
        flows: List[Flowable] = [_render_block_title(block.get("title") or "Executive Summary", s), tbl]
    else:
        flows = [_render_block_title(block.get("title") or "Executive Summary", s)] + para_flows

    # Badges
    badges = block.get("badges") or []
    if badges:
        cells = []
        row = []
        for b in badges[:8]:
            if isinstance(b, dict):
                row.append(_badge_pill(b.get("label") or "", b.get("variant") or "neutral"))
            if len(row) == 3:
                cells.append(row)
                row = []
        if row:
            while len(row) < 3:
                row.append("")
            cells.append(row)
        if cells:
            badge_tbl = Table(cells, colWidths=[CONTENT_W * 0.32] * 3)
            badge_tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            flows.append(Spacer(1, 3 * mm))
            flows.append(badge_tbl)
    return _wrap_in_card(flows)


def _render_kpi_grid(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    items = block.get("items") or block.get("kpis") or block.get("cards") or []
    if not items:
        return []
    cols = 3 if len(items) >= 6 else 2
    cells: List[List[List[Flowable]]] = []
    row: List[List[Flowable]] = []
    for item in items[:12]:
        if not isinstance(item, dict):
            continue
        label = (item.get("label") or "").upper()
        value = str(item.get("value") or "")
        note = item.get("note") or item.get("description") or ""
        variant = item.get("variant") or "neutral"
        sub = item.get("sub") or ""
        cell = [
            Paragraph(label, s["kpi_label"]),
            Paragraph(value, s["kpi_value"]),
        ]
        if sub:
            cell.append(Paragraph(_clean_inline(sub), s["kpi_note"]))
        if note:
            cell.append(Paragraph(_clean_inline(note), s["small"]))
        # Salva variant per styling sotto
        cell.append(_VariantMarker(variant))
        row.append(cell)
        if len(row) == cols:
            cells.append(row)
            row = []
    if row:
        while len(row) < cols:
            row.append([])
        cells.append(row)
    if not cells:
        return []
    col_w = (CONTENT_W) / cols
    tbl_data = [[c[:-1] if c else "" for c in r] for r in cells]
    tbl = Table(tbl_data, colWidths=[col_w] * cols)
    style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
    ]
    # Border top variant color per cell
    for r_idx, r in enumerate(cells):
        for c_idx, cell in enumerate(r):
            if cell:
                marker = cell[-1]
                v = getattr(marker, "variant", "neutral").lower()
                color_map = {"ok": GREEN, "success": GREEN, "warning": ACCENT_WARM, "alert": RED, "critical": RED, "neutral": PRIMARY}
                style_cmds.append(("LINEABOVE", (c_idx, r_idx), (c_idx, r_idx), 2.0, color_map.get(v, PRIMARY)))
    tbl.setStyle(TableStyle(style_cmds))
    return _wrap_in_card([_render_block_title(block.get("title") or "Metriche", s), tbl])


class _VariantMarker:
    """Placeholder per passare variant info attraverso le celle KPI."""
    def __init__(self, variant: str):
        self.variant = variant


def _render_data_table(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
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
    col_w = (CONTENT_W) / n_cols
    tbl = Table([header_row] + body_rows, colWidths=[col_w] * n_cols, repeatRows=1)
    style_cmds: List[Any] = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, BORDER),
    ]
    # Zebra striping
    for i in range(1, len(body_rows) + 1):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), SURFACE_2))
    tbl.setStyle(TableStyle(style_cmds))
    flows: List[Flowable] = [_render_block_title(block.get("title") or "", s)]
    intro = block.get("intro") or block.get("description")
    if intro:
        flows.append(Paragraph(_clean_inline(intro), s["body_soft"]))
        flows.append(Spacer(1, 2 * mm))
    flows.append(tbl)
    note = block.get("note") or block.get("footer_note")
    if note:
        flows.append(Spacer(1, 2 * mm))
        flows.append(Paragraph(f"<i>{_clean_inline(note)}</i>", s["small"]))
    return _wrap_in_card(flows)


_FRAME_AVAIL_H = PAGE_H - MARGIN_TOP_REST - MARGIN_BOTTOM  # ~739.84pt
_TWO_COL_SAFETY = 60  # reserve title/spacer/divider


def _measure_flow_height(flows: List[Flowable], width: float) -> float:
    total = 0.0
    for f in flows:
        try:
            _, h = f.wrap(width, _FRAME_AVAIL_H * 4)
        except Exception:
            h = 0
        total += h
    return total


def _two_col_or_stack(
    left_flows: List[Flowable],
    right_flows: List[Flowable],
    inner_w: float,
) -> List[Flowable]:
    """Side-by-side via Table when fits; stacked fallback when too tall.

    ReportLab non spezza una Table cell con flowables nidificati: se un lato
    supera l'altezza del frame, esplode con 'row too large'. Misurando prima
    e fallback a stack vertico salviamo il rendering.
    """
    if not left_flows and not right_flows:
        return []
    avail = _FRAME_AVAIL_H - _TWO_COL_SAFETY
    cell_w = inner_w - 3 * mm
    lh = _measure_flow_height(left_flows, cell_w)
    rh = _measure_flow_height(right_flows, cell_w)
    if max(lh, rh) > avail:
        out: List[Flowable] = list(left_flows)
        if left_flows and right_flows:
            out.append(Spacer(1, 4 * mm))
        out.extend(right_flows)
        return out
    tbl = Table([[left_flows, right_flows]], colWidths=[inner_w, inner_w])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 3 * mm),
        ("LEFTPADDING", (1, 0), (1, 0), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [tbl]


def _render_two_column(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    left = block.get("left") or {}
    right = block.get("right") or {}

    def render_side(side: dict) -> List[Flowable]:
        out: List[Flowable] = []
        if side.get("heading"):
            out.append(Paragraph(_clean_inline(side["heading"]), s["h3"]))
        if side.get("body_html"):
            out.extend(_html_to_paragraphs(side["body_html"], s["body_soft"], bullet_style=s["body_soft"]))
        if side.get("body"):
            out.append(Paragraph(_clean_inline(side["body"]), s["body_soft"]))
        badges = side.get("badges") or []
        for b in badges:
            if not isinstance(b, dict):
                continue
            row = Table(
                [[_badge_pill(b.get("label") or "", b.get("variant") or "neutral"), Paragraph(_clean_inline(b.get("description") or ""), s["body_soft"])]],
                colWidths=[28 * mm, None],
            )
            row.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5 * mm),
            ]))
            out.append(row)
        if side.get("table"):
            tbl_d = side["table"]
            if tbl_d.get("columns") and tbl_d.get("rows"):
                rendered = _render_data_table({"table": tbl_d, "title": ""}, s)
                for r in rendered:
                    if not (hasattr(r, "_card_wrap") and r._card_wrap):
                        out.append(r)
        callout = side.get("callout")
        if callout and isinstance(callout, dict):
            tone = callout.get("tone") or "info"
            bg = INFO_BG if tone == "info" else YELLOW_BG if tone == "warning" else RED_BG
            brd = INFO if tone == "info" else YELLOW if tone == "warning" else RED
            label = callout.get("label") or ""
            body = callout.get("body") or ""
            label_html = f"<b>{_clean_inline(label)}:</b> " if label else ""
            cb = Paragraph(f"{label_html}{_clean_inline(body)}", s["body_soft"])
            cbt = Table([[cb]], colWidths=[None])
            cbt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("LINEBEFORE", (0, 0), (0, -1), 2.5, brd),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ]))
            out.append(Spacer(1, 2 * mm))
            out.append(cbt)
        return out

    left_flows = render_side(left)
    right_flows = render_side(right)
    inner_w = (CONTENT_W - 6 * mm) / 2
    body = _two_col_or_stack(left_flows, right_flows, inner_w)
    return _wrap_in_card([_render_block_title(block.get("title") or "", s)] + body)


def _render_action_list(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    actions = block.get("actions") or block.get("items") or []
    if not actions:
        return []
    rows = []
    for i, a in enumerate(actions[:12], 1):
        if not isinstance(a, dict):
            continue
        title = a.get("title") or a.get("action") or a.get("label") or ""
        body = a.get("description") or a.get("body") or ""
        priority = a.get("priority") or ""
        impact = a.get("impact") or ""
        effort = a.get("effort") or a.get("complexity") or ""
        meta = " · ".join(filter(None, [
            f"Priorità: {priority}" if priority else None,
            f"Impatto: {impact}" if impact else None,
            f"Effort: {effort}" if effort else None,
        ]))
        num_para = Paragraph(f"<b>{i}</b>", ParagraphStyle("n", parent=s["body"], fontSize=14, fontName="Helvetica-Bold", textColor=ACCENT, alignment=TA_CENTER))
        content = [Paragraph(f"<b>{_clean_inline(title)}</b>", s["body"])]
        if body:
            content.append(Paragraph(_clean_inline(body), s["body_soft"]))
        if meta:
            content.append(Paragraph(meta, s["small"]))
        rows.append([num_para, content])
    if not rows:
        return []
    tbl = Table(rows, colWidths=[12 * mm, None])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, BORDER),
        ("BACKGROUND", (0, 0), (0, -1), SURFACE_2),
    ]))
    return _wrap_in_card([_render_block_title(block.get("title") or "Azioni", s), tbl])


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
    return _wrap_in_card([_render_block_title(block.get("title") or "Rischi", s), tbl])


def _render_conclusions(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    left = block.get("left") or {}
    right = block.get("right") or {}
    left_flows: List[Flowable] = []
    if left.get("heading"):
        left_flows.append(Paragraph(_clean_inline(left["heading"]), s["h3"]))
    if left.get("body_html"):
        left_flows.extend(_html_to_paragraphs(left["body_html"], s["body_soft"], bullet_style=s["body_soft"]))
    elif left.get("body"):
        left_flows.append(Paragraph(_clean_inline(left["body"]), s["body_soft"]))
    right_flows: List[Flowable] = []
    if right.get("heading"):
        right_flows.append(Paragraph(_clean_inline(right["heading"]), s["h3"]))
    milestones = right.get("milestones") or []
    for m in milestones[:6]:
        if not isinstance(m, dict):
            continue
        tone = (m.get("tone") or "neutral").lower()
        bar_color = {"alert": RED, "warning": ACCENT_WARM, "ok": GREEN, "success": GREEN}.get(tone, PRIMARY)
        label = m.get("label") or ""
        items = m.get("items") or []
        cell: List[Flowable] = []
        if label:
            cell.append(Paragraph(f"<b>{_clean_inline(label)}</b>", s["body"]))
        for it in items[:6]:
            cell.append(Paragraph(f"• {_clean_inline(str(it))}", s["body_soft"]))
        if m.get("body_html"):
            cell.extend(_html_to_paragraphs(m["body_html"], s["body_soft"]))
        if not cell:
            continue
        mt = Table([[cell]], colWidths=[None])
        mt.setStyle(TableStyle([
            ("LINEBEFORE", (0, 0), (0, -1), 2.5, bar_color),
            ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
            ("TOPPADDING", (0, 0), (-1, -1), 1.5 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5 * mm),
            ("BACKGROUND", (0, 0), (-1, -1), SURFACE_2),
        ]))
        right_flows.append(mt)
        right_flows.append(Spacer(1, 2 * mm))
    if not right_flows:
        right_flows = [Paragraph("Nessuna azione specifica disponibile.", s["body_soft"])]
    inner_w = (CONTENT_W - 6 * mm) / 2
    body = _two_col_or_stack(left_flows, right_flows, inner_w)
    return _wrap_in_card([_render_block_title(block.get("title") or "Conclusioni e Prossimi Passi", s)] + body)


def _render_narrative(block: dict, s: Dict[str, ParagraphStyle]) -> List[Flowable]:
    body_html = block.get("body_html") or block.get("body") or ""
    flows = _html_to_paragraphs(body_html, s["body"])
    if not flows:
        return []
    return _wrap_in_card([_render_block_title(block.get("title") or "", s)] + flows)


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
    """Linea sottile orizzontale come separatore tra sezioni."""
    def __init__(self, width: float = CONTENT_W, color=BORDER):
        super().__init__()
        self.width = width
        self.color = color
        self.height = 0.8 * mm

    def wrap(self, avail_w, avail_h):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setStrokeColor(self.color)
        c.setLineWidth(0.4)
        c.line(0, 0, self.width, 0)


# ---------------------------------------------------------------------------
# Block dispatcher
# ---------------------------------------------------------------------------

_BLOCK_RENDERERS = {
    "executive_summary": _render_executive_summary,
    "kpi_grid": _render_kpi_grid,
    "data_table": _render_data_table,
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

def _draw_banner_page1(c: Canvas, doc: BaseDocTemplate) -> None:
    """Banner full-bleed solo pagina 1 — gradiente navy via rect + accent stripe."""
    title = getattr(doc, "_report_title", "Report Premium")
    kicker = getattr(doc, "_report_kicker", "REPORT PREMIUM")
    client_meta_lines: List[str] = getattr(doc, "_report_meta_lines", []) or []

    # Banner full bleed top
    banner_h = 26 * mm
    c.saveState()
    c.setFillColor(PRIMARY)
    c.rect(0, PAGE_H - banner_h, PAGE_W, banner_h, stroke=0, fill=1)
    # Stripe accent
    c.setFillColor(ACCENT)
    c.rect(0, PAGE_H - banner_h - 1.5, PAGE_W, 1.5, stroke=0, fill=1)
    # Logo
    logo = _logo_path()
    if logo:
        try:
            c.drawImage(str(logo), MARGIN_X, PAGE_H - banner_h + 5 * mm,
                        width=18 * mm, height=14 * mm,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            pass
    # Kicker + title
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGIN_X + 22 * mm, PAGE_H - 8 * mm, kicker.upper())
    c.setFont("Helvetica-Bold", 14)
    title_lines = _wrap_text(title, 78)
    y = PAGE_H - 13 * mm
    for line in title_lines[:2]:
        c.drawString(MARGIN_X + 22 * mm, y, line)
        y -= 5 * mm
    # Right meta
    c.setFont("Helvetica", 8.5)
    y = PAGE_H - 8 * mm
    for line in client_meta_lines[:3]:
        c.drawRightString(PAGE_W - MARGIN_X, y, line)
        y -= 4 * mm
    c.restoreState()


def _draw_footer(c: Canvas, doc: BaseDocTemplate) -> None:
    """Footer full-bleed bottom — su ogni pagina."""
    footer = getattr(doc, "_report_footer", {}) or {}
    page_num = c.getPageNumber()
    total_pages = getattr(doc, "_total_pages", 0) or "?"
    code = footer.get("code") or ""
    line1 = footer.get("line1") or "Report generato da K2-AI"
    disclaimer = footer.get("disclaimer") or ""

    footer_h = 18 * mm
    c.saveState()
    c.setFillColor(PRIMARY)
    c.rect(0, 0, PAGE_W, footer_h, stroke=0, fill=1)

    # Logo small
    logo = _logo_path()
    if logo:
        try:
            c.drawImage(str(logo), MARGIN_X, 4 * mm,
                        width=10 * mm, height=8 * mm,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            pass
    # Footer text
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGIN_X + 13 * mm, footer_h - 4 * mm, line1)
    c.setFont("Helvetica", 7)
    info_parts = ["k2-ai.it", "info@k2-ai.it"]
    if code:
        info_parts.append(code)
    c.drawString(MARGIN_X + 13 * mm, footer_h - 7.5 * mm, " · ".join(info_parts))

    # Disclaimer (smaller, italic) — wrap su 2 righe contenuto nei margini
    if disclaimer:
        c.setFont("Helvetica-Oblique", 6.5)
        c.setFillColor(colors.HexColor("#CBD5E1"))
        # 6.5pt @ Helvetica-Oblique ≈ 1.5mm/char avg. Disponibile da
        # MARGIN_X+13mm a PAGE_W-MARGIN_X-25mm (riservato per Pag. N).
        avail_mm = (PAGE_W - 2 * MARGIN_X - 13 * mm - 25 * mm) / mm
        max_chars = int(avail_mm / 1.45)  # margine sicurezza
        disc_lines = _wrap_text(disclaimer, max_chars)
        y = footer_h - 11 * mm
        for line in disc_lines[:2]:
            c.drawString(MARGIN_X + 13 * mm, y, line)
            y -= 3 * mm

    # Page number right
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(PAGE_W - MARGIN_X, footer_h - 6 * mm, f"Pag. {page_num}")
    c.restoreState()


def _on_first_page(c: Canvas, doc: BaseDocTemplate) -> None:
    _draw_banner_page1(c, doc)
    _draw_footer(c, doc)


def _on_later_pages(c: Canvas, doc: BaseDocTemplate) -> None:
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


# ---------------------------------------------------------------------------
# Block normalization — pre-process JSON Sonnet (compat con vecchio renderer)
# ---------------------------------------------------------------------------

_TWO_SIDE_TYPES = {"two_column", "narrative_split", "conclusions"}

_CONCLUSIONS_FALLBACK_HTML = (
    "<p>I dati raccolti in sessione non sono stati sufficienti a generare conclusioni "
    "specifiche. Prossimi passi consigliati:</p>"
    "<ol>"
    "<li>Fornire dati di baseline (GSC, Analytics) per ancorare proiezioni reali.</li>"
    "<li>Identificare 2-3 priorità operative.</li>"
    "<li>Verificare KPI a 30/60/90 giorni con strumenti dedicati.</li>"
    "</ol>"
)

_CONCLUSIONS_RIGHT_FALLBACK = {
    "heading": "3 azioni immediate (settimana 1)",
    "milestones": [
        {"label": "Audit dati", "tone": "neutral", "items": ["Collega Google Search Console", "Esporta keyword/posizioni"]},
        {"label": "Quick win", "tone": "warning", "items": ["Identifica 3 quick win on-page"]},
        {"label": "KPI 30/60/90", "tone": "neutral", "items": ["Definisci 3 KPI con baseline esplicita"]},
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
    if not safe or safe[-1].get("type") != "conclusions":
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
        "Le stime di traffico, volume keyword e proiezioni sono basate su benchmark di mercato. "
        "I dati reali possono variare. Verificare con Google Search Console e strumenti di analisi dedicati."
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
