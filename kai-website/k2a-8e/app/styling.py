"""Stile premium per i PDF K2-AI: palette, stili, copertina full-page, header/
footer, componenti (gauge score, heatmap rischi, card rischio, tabella KPI,
checklist azioni)."""
from __future__ import annotations

import os

from reportlab.graphics.shapes import Drawing, Circle, String, Rect, Wedge
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, Paragraph, Spacer, Table, TableStyle

# --- Palette K2-AI -------------------------------------------------------
DARK = colors.HexColor("#0d0f12")        # copertina / header
PRIMARY = colors.HexColor("#1d7d70")     # teal scuro
ACCENT = colors.HexColor("#2a9d8f")      # teal
INK = colors.HexColor("#1f2937")         # testo
MUTED = colors.HexColor("#64748b")       # grigio
SOFT = colors.HexColor("#94a3b8")
LIGHT = colors.HexColor("#f1faf7")       # sfondo chiaro teal
CARDBG = colors.HexColor("#f8fafc")
LINE = colors.HexColor("#e2e8f0")
VERDE = colors.HexColor("#16a34a")
GIALLO = colors.HexColor("#d97706")
ROSSO = colors.HexColor("#dc2626")
SEMAFORO = {"verde": VERDE, "giallo": GIALLO, "rosso": ROSSO,
            "bassa": VERDE, "media": GIALLO, "alta": ROSSO}

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN
_LOGO = os.path.join(os.path.dirname(__file__), "..", "assets", "logo-k2ai.png")


def hx(c) -> str:
    return "#" + c.hexval()[2:]


def html_escape(s) -> str:
    import html as _h
    return _h.escape(str(s if s is not None else ""))


def styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("k1", parent=base["Heading1"], fontSize=15, textColor=PRIMARY,
                             spaceBefore=12, spaceAfter=5, leading=18),
        "h2": ParagraphStyle("k2", parent=base["Heading2"], fontSize=11.5, textColor=ACCENT,
                             spaceBefore=8, spaceAfter=3, leading=14),
        "h3": ParagraphStyle("k3", parent=base["Heading3"], fontSize=10, textColor=INK,
                             spaceBefore=5, spaceAfter=2, leading=13),
        "body": ParagraphStyle("kb", parent=base["BodyText"], fontSize=9.5, textColor=INK,
                               leading=14.5, spaceAfter=4),
        "bullet": ParagraphStyle("kbl", parent=base["BodyText"], fontSize=9.5, textColor=INK,
                                 leading=13, leftIndent=10, spaceAfter=2),
        "kv": ParagraphStyle("kkv", fontSize=9, textColor=MUTED, leading=12),
        "small": ParagraphStyle("ks", fontSize=7.5, textColor=MUTED, leading=10.5),
        "toc": ParagraphStyle("ktoc", fontSize=10.5, textColor=INK, leading=20),
        "lead": ParagraphStyle("klead", fontSize=10.5, textColor=INK, leading=16, spaceAfter=6),
    }


# --- Gauge score (donut) -------------------------------------------------
class Gauge(Flowable):
    def __init__(self, score, label="Score", size=34 * mm):
        super().__init__()
        try:
            self.score = max(0, min(100, int(score)))
        except Exception:
            self.score = None
        self.label = label
        self.width = size
        self.height = size

    def draw(self):
        s = self.size = self.width
        val = self.score if self.score is not None else 0
        col = VERDE if val >= 70 else GIALLO if val >= 45 else ROSSO
        cx = cy = s / 2
        r = s / 2 - 3
        d = Drawing(s, s)
        # anello di sfondo
        d.add(Circle(cx, cy, r, strokeColor=LINE, strokeWidth=6, fillColor=None))
        # arco proporzionale al punteggio
        ang = 90 - (val / 100.0 * 360)
        d.add(Wedge(cx, cy, r, ang, 90, yradius=r, strokeColor=col, strokeWidth=6,
                    fillColor=None, annular=True, radius1=r - 0.01))
        d.add(String(cx, cy - 2, str(val if self.score is not None else "—"),
                     fontName="Helvetica-Bold", fontSize=16, fillColor=col, textAnchor="middle"))
        d.add(String(cx, cy - 12, self.label.upper(), fontName="Helvetica", fontSize=6,
                     fillColor=MUTED, textAnchor="middle"))
        d.drawOn(self.canv, 0, 0)


def semaforo_dot(stato: str) -> str:
    col = SEMAFORO.get(str(stato).lower(), MUTED)
    return f'<font color="{hx(col)}">●</font>'


def heatmap(items: list[dict], style: dict, area_key="area", sem_key="semaforo") -> Table:
    """Griglia aree con celle colorate per semaforo (dashboard rischi)."""
    cells, row = [], []
    for it in items:
        sem = str(it.get(sem_key, "")).lower()
        col = SEMAFORO.get(sem, SOFT)
        area = str(it.get(area_key) or it.get("nome") or "")
        chip = Table([[Paragraph(f'<font color="white"><b>{html_escape(area)}</b></font>', style["kv"])]],
                     colWidths=[(CONTENT_W - 3 * 4) / 3])
        chip.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), col),
                                  ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 7), ("ROUNDEDCORNERS", [3, 3, 3, 3])]))
        row.append(chip)
        if len(row) == 3:
            cells.append(row); row = []
    if row:
        while len(row) < 3:
            row.append("")
        cells.append(row)
    t = Table(cells, colWidths=[CONTENT_W / 3] * 3, hAlign="LEFT")
    t.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                           ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    return t


def risk_card(descr: str, gravita: str, style: dict, extra: str = "") -> Table:
    """Card rischio con barra colorata a sinistra per gravità."""
    col = SEMAFORO.get(str(gravita).lower(), MUTED)
    body = [Paragraph(f'<b><font color="{hx(col)}">{html_escape(str(gravita).capitalize())}</font></b> · '
                      f'{html_escape(descr)}' + (f' <font color="#64748b">{html_escape(extra)}</font>' if extra else ''),
                      style["body"])]
    t = Table([["", body]], colWidths=[2.5, CONTENT_W - 2.5])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), col),
        ("BACKGROUND", (1, 0), (1, -1), CARDBG),
        ("LEFTPADDING", (1, 0), (1, -1), 8), ("RIGHTPADDING", (1, 0), (1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def kpi_table(items: list[dict], style: dict) -> Table:
    """Tabella KPI/indici: nome · valore · benchmark · semaforo."""
    cols = ["nome", "valore", "benchmark", "semaforo"]
    header = ["Indicatore", "Valore", "Benchmark", ""]
    present = [c for c in cols if any(c in it for it in items)]
    head = [Paragraph(f"<b>{header[cols.index(c)] or ''}</b>", style["kv"]) for c in present]
    rows = [head]
    for it in items:
        r = []
        for c in present:
            v = it.get(c, "")
            if c == "semaforo":
                r.append(Paragraph(semaforo_dot(v), style["body"]))
            else:
                r.append(Paragraph(html_escape(v), style["body"]))
        rows.append(r)
    n = len(present)
    widths = [CONTENT_W * w for w in ([0.4, 0.2, 0.3, 0.1] if n == 4 else [1.0 / n] * n)][:n]
    t = Table(rows, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, ACCENT),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARDBG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# --- Copertina full-page + header + footer ------------------------------
def cover_page(canvas, titolo: str, azienda: str, sottotitolo: str, data: str = ""):
    """Disegna l'intera prima pagina come copertina."""
    canvas.setFillColor(DARK)
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    # accenti teal
    canvas.setFillColor(ACCENT)
    canvas.rect(0, PAGE_H - 6 * mm, PAGE_W, 6 * mm, stroke=0, fill=1)
    canvas.rect(MARGIN, PAGE_H * 0.46, 38 * mm, 1.4 * mm, stroke=0, fill=1)
    # logo grande centrato in alto
    try:
        from reportlab.lib.utils import ImageReader
        if os.path.exists(_LOGO):
            logo = ImageReader(_LOGO); iw, ih = logo.getSize()
            lh = 34 * mm; lw = lh * iw / ih
            canvas.drawImage(logo, (PAGE_W - lw) / 2, PAGE_H - 52 * mm, width=lw, height=lh,
                             mask=[0, 12, 0, 12, 0, 12])
    except Exception:
        pass
    # titolo
    canvas.setFillColor(ACCENT); canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(MARGIN, PAGE_H * 0.52, "DIAGNOSI PROFESSIONALE")
    canvas.setFillColor(colors.white); canvas.setFont("Helvetica-Bold", 34)
    canvas.drawString(MARGIN, PAGE_H * 0.46 + 5 * mm, titolo[:30])
    if sottotitolo:
        canvas.setFillColor(colors.HexColor("#9fb3ad")); canvas.setFont("Helvetica", 12)
        canvas.drawString(MARGIN, PAGE_H * 0.42, sottotitolo[:80])
    # blocco "preparato per"
    if azienda:
        canvas.setFillColor(SOFT); canvas.setFont("Helvetica", 9)
        canvas.drawString(MARGIN, PAGE_H * 0.30 + 6 * mm, "PREPARATO PER")
        canvas.setFillColor(colors.white); canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(MARGIN, PAGE_H * 0.30, azienda[:50])
    if data:
        canvas.setFillColor(SOFT); canvas.setFont("Helvetica", 9)
        canvas.drawString(MARGIN, PAGE_H * 0.30 - 7 * mm, data)
    # footer copertina
    canvas.setStrokeColor(colors.HexColor("#22303a")); canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 20 * mm, PAGE_W - MARGIN, 20 * mm)
    canvas.setFillColor(SOFT); canvas.setFont("Helvetica", 7.5)
    canvas.drawString(MARGIN, 15 * mm, "K2-AI · K2A S.R.L.S. · documento riservato")
    canvas.drawRightString(PAGE_W - MARGIN, 15 * mm, "k2-ai.it")


def page_header(canvas, report_name: str):
    """Header running su pagine interne: logo piccolo + nome report + linea."""
    y = PAGE_H - 12 * mm
    try:
        from reportlab.lib.utils import ImageReader
        if os.path.exists(_LOGO):
            logo = ImageReader(_LOGO); iw, ih = logo.getSize()
            lh = 6 * mm; lw = lh * iw / ih
            # box scuro dietro al logo (sfondo nero del logo)
            canvas.setFillColor(DARK)
            canvas.roundRect(MARGIN - 2, y - 1.5 * mm, lw + 4, lh + 3, 2, stroke=0, fill=1)
            canvas.drawImage(logo, MARGIN, y, width=lw, height=lh, mask=[0, 12, 0, 12, 0, 12])
            xname = MARGIN + lw + 5
    except Exception:
        xname = MARGIN
    canvas.setFillColor(MUTED); canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE_W - MARGIN, y + 1.5 * mm, report_name)
    canvas.setStrokeColor(LINE); canvas.setLineWidth(0.5)
    canvas.line(MARGIN, y - 3 * mm, PAGE_W - MARGIN, y - 3 * mm)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE); canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 14 * mm, PAGE_W - MARGIN, 14 * mm)
    canvas.setFillColor(MUTED); canvas.setFont("Helvetica", 7.5)
    canvas.drawString(MARGIN, 9.5 * mm, "K2-AI · documento riservato")
    canvas.drawRightString(PAGE_W - MARGIN, 9.5 * mm, f"pag. {doc.page - 1}")
    canvas.restoreState()
