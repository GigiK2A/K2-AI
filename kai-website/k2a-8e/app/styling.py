"""Stile condiviso per i PDF K2-AI: palette, stili paragrafo, componenti
(copertina, badge score, semaforo, footer)."""
from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, Paragraph, Spacer, Table, TableStyle

# --- Palette K2-AI -------------------------------------------------------
PRIMARY = colors.HexColor("#1d7d70")     # teal scuro (brand)
ACCENT = colors.HexColor("#2a9d8f")      # teal
INK = colors.HexColor("#1f2937")         # testo
MUTED = colors.HexColor("#64748b")       # grigio
LIGHT = colors.HexColor("#f1faf7")       # sfondo chiaro
LINE = colors.HexColor("#d7e6e2")
VERDE = colors.HexColor("#16a34a")
GIALLO = colors.HexColor("#d97706")
ROSSO = colors.HexColor("#dc2626")
SEMAFORO = {"verde": VERDE, "giallo": GIALLO, "rosso": ROSSO,
            "bassa": VERDE, "media": GIALLO, "alta": ROSSO}

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm


def styles() -> dict:
    base = getSampleStyleSheet()
    s = {
        "title": ParagraphStyle("k2_title", parent=base["Title"], fontSize=26,
                                textColor=colors.white, leading=30, alignment=TA_LEFT),
        "subtitle": ParagraphStyle("k2_sub", fontSize=12, textColor=colors.HexColor("#d7f0ea"),
                                   leading=16),
        "h1": ParagraphStyle("k2_h1", parent=base["Heading1"], fontSize=15, textColor=PRIMARY,
                             spaceBefore=10, spaceAfter=4, leading=18),
        "h2": ParagraphStyle("k2_h2", parent=base["Heading2"], fontSize=12, textColor=ACCENT,
                             spaceBefore=7, spaceAfter=3, leading=15),
        "h3": ParagraphStyle("k2_h3", parent=base["Heading3"], fontSize=10.5, textColor=INK,
                             spaceBefore=5, spaceAfter=2, leading=13),
        "body": ParagraphStyle("k2_body", parent=base["BodyText"], fontSize=9.5, textColor=INK,
                               leading=14, spaceAfter=3),
        "bullet": ParagraphStyle("k2_bullet", parent=base["BodyText"], fontSize=9.5, textColor=INK,
                                 leading=13, leftIndent=8, spaceAfter=1),
        "small": ParagraphStyle("k2_small", fontSize=7.5, textColor=MUTED, leading=10),
        "kv": ParagraphStyle("k2_kv", fontSize=9, textColor=MUTED, leading=12),
    }
    return s


class ScoreBadge(Flowable):
    """Cerchio col punteggio + etichetta."""
    def __init__(self, score, label="Score", size=26 * mm):
        super().__init__()
        self.score = score; self.label = label; self.size = size
        self.width = size; self.height = size

    def draw(self):
        c = self.canv
        try:
            val = int(self.score)
        except Exception:
            val = None
        col = VERDE if (val or 0) >= 70 else GIALLO if (val or 0) >= 45 else ROSSO
        r = self.size / 2
        c.setStrokeColor(col); c.setLineWidth(3)
        c.circle(r, r, r - 2, stroke=1, fill=0)
        c.setFillColor(col); c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(r, r - 1, str(val if val is not None else "—"))
        c.setFillColor(MUTED); c.setFont("Helvetica", 6.5)
        c.drawCentredString(r, r - 9, self.label.upper())


def hx(c) -> str:
    """'#rrggbb' per i tag <font color=...> di ReportLab."""
    return "#" + c.hexval()[2:]


def semaforo_dot(stato: str) -> str:
    """Pallino HTML colorato (per inline nei Paragraph)."""
    col = SEMAFORO.get(str(stato).lower(), MUTED)
    return f'<font color="{hx(col)}">●</font>'


def mappa_table(items: list[dict], style: dict, area_key="area", sem_key="semaforo") -> Table:
    """Tabella aree con semaforo colorato."""
    rows = [[Paragraph("<b>Area</b>", style["kv"]), Paragraph("<b>Stato</b>", style["kv"])]]
    for it in items:
        sem = str(it.get(sem_key, "")).lower()
        rows.append([
            Paragraph(html_escape(it.get(area_key, "")), style["body"]),
            Paragraph(f'{semaforo_dot(sem)} {sem.capitalize()}', style["body"]),
        ])
    t = Table(rows, colWidths=[(PAGE_W - 2 * MARGIN) * 0.7, (PAGE_W - 2 * MARGIN) * 0.3])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def html_escape(s) -> str:
    import html as _h
    return _h.escape(str(s if s is not None else ""))


import os
DARK = colors.HexColor("#0d0f12")
_LOGO = os.path.join(os.path.dirname(__file__), "..", "assets", "logo-k2ai.png")


def cover_band(canvas, title: str, azienda: str, sottotitolo: str = ""):
    """Banda scura in alto (si fonde col logo K2-AI) + accento teal + logo ufficiale."""
    h = 46 * mm
    canvas.setFillColor(DARK)
    canvas.rect(0, PAGE_H - h, PAGE_W, h, stroke=0, fill=1)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, PAGE_H - h, PAGE_W, 2.5 * mm, stroke=0, fill=1)

    # Logo ufficiale (sfondo nero → si fonde nella banda scura), in alto a destra.
    try:
        from reportlab.lib.utils import ImageReader
        if os.path.exists(_LOGO):
            logo = ImageReader(_LOGO)
            iw, ih = logo.getSize()
            lh = 22 * mm
            lw = lh * iw / ih
            canvas.drawImage(logo, PAGE_W - MARGIN - lw, PAGE_H - 30 * mm, width=lw, height=lh,
                             mask=[0, 12, 0, 12, 0, 12])  # rende il nero ~trasparente
    except Exception:
        pass

    # Titolo + azienda a sinistra (il logo, in alto a destra, è l'unico marchio).
    canvas.setFillColor(ACCENT)
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.drawString(MARGIN, PAGE_H - 14 * mm, "DIAGNOSI K2-AI")
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 24)
    canvas.drawString(MARGIN, PAGE_H - 28 * mm, title[:40])
    canvas.setFillColor(colors.HexColor("#9fb3ad"))
    canvas.setFont("Helvetica", 12)
    if azienda:
        canvas.drawString(MARGIN, PAGE_H - 36 * mm, azienda[:60])
    if sottotitolo:
        canvas.setFont("Helvetica", 8)
        canvas.drawString(MARGIN, PAGE_H - 41 * mm, sottotitolo[:90])


def footer(canvas, doc, brand="K2-AI · documento riservato"):
    canvas.saveState()
    canvas.setStrokeColor(LINE); canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 14 * mm, PAGE_W - MARGIN, 14 * mm)
    canvas.setFillColor(MUTED); canvas.setFont("Helvetica", 7.5)
    canvas.drawString(MARGIN, 9 * mm, brand)
    canvas.drawRightString(PAGE_W - MARGIN, 9 * mm, f"pag. {doc.page}")
    canvas.restoreState()
