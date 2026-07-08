"""Design System PDF K2-AI — premium, consulenziale, coerente per tutti i report.

Palette sobria, tipografia moderna (DMSans + Syne), e una libreria di componenti
riutilizzabili: copertina, indice editoriale, executive summary, dashboard KPI,
insight/action box, risk card, roadmap, tabelle premium, header/footer, CTA finale.
"""
from __future__ import annotations

import logging
import os
import re

from reportlab.graphics.shapes import Circle, Drawing, Line, Rect, String, Wedge
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, Paragraph, Spacer, Table, TableStyle

# ===================== PALETTE (premium, sobria) =========================
CARBON = colors.HexColor("#1A1714")      # nero caldo — titoli/header (warm black)
GOLD = colors.HexColor("#A8884F")        # ORO/BRONZO — accento (design editoriale K2A)
GOLD_DK = colors.HexColor("#8A6D3B")     # oro scuro per testo su chiaro
WARM = colors.HexColor("#FBFAF7")        # bianco caldo — sfondi
TEXT = colors.HexColor("#1F1B16")        # testo principale (near-black caldo)
TEXT_GRAY = colors.HexColor("#6B6256")   # testo secondario (taupe)
LINE = colors.HexColor("#E7E2D8")        # linee/bordi (warm line)
NEUTRAL = colors.HexColor("#8C8475")     # grigio neutro caldo
# Funzionali (uso parco)
GREEN = colors.HexColor("#16A34A")
AMBER = colors.HexColor("#F59E0B")
RED = colors.HexColor("#DC2626")
BLUE = colors.HexColor("#2563EB")
CARD = colors.HexColor("#FBF9F4")    # card su fondo caldo
CREAM = colors.HexColor("#F5F1E8")   # cream/beige — callout (come il riferimento)
COVER_SUB = colors.HexColor("#B8AE9C")   # testo tenue su copertina scura (taupe)

SEMAFORO = {"verde": GREEN, "giallo": AMBER, "rosso": RED,
            "bassa": GREEN, "media": AMBER, "alta": RED,
            "basso": GREEN, "medio": AMBER, "alto": RED}
TONE = {"positivo": GREEN, "attenzione": AMBER, "critico": RED, "info": BLUE, "neutro": NEUTRAL}

log = logging.getLogger(__name__)

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN
_ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
_LOGO = os.path.join(_ASSETS, "logo-k2ai.png")
_FONTS = os.path.join(_ASSETS, "fonts")

# ===================== TIPOGRAFIA (DMSans + Syne) ========================
F_BODY, F_BOLD, F_ITALIC, F_TITLE, F_MONO = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-Bold", "Courier"


def _register_fonts() -> None:
    global F_BODY, F_BOLD, F_ITALIC, F_TITLE, F_MONO
    pairs = [("DMSans", "DMSans-Regular.ttf"), ("DMSans-Bold", "DMSans-SemiBold.ttf"),
             ("DMSans-Italic", "DMSans-Italic.ttf"), ("Syne", "Syne-Bold.ttf"),
             ("SyneSemi", "Syne-SemiBold.ttf"), ("DMMono", "DMMono-Regular.ttf")]
    try:
        for name, fn in pairs:
            p = os.path.join(_FONTS, fn)
            if os.path.exists(p):
                pdfmetrics.registerFont(TTFont(name, p))
            else:
                log.warning("Font brand mancante: %s (%s) — fallback a Helvetica", name, p)
        pdfmetrics.registerFontFamily("DMSans", normal="DMSans", bold="DMSans-Bold",
                                      italic="DMSans-Italic", boldItalic="DMSans-Bold")
        if "DMSans" in pdfmetrics.getRegisteredFontNames():
            F_BODY, F_BOLD, F_ITALIC = "DMSans", "DMSans-Bold", "DMSans-Italic"
        if "Syne" in pdfmetrics.getRegisteredFontNames():
            F_TITLE = "Syne"
        if "DMMono" in pdfmetrics.getRegisteredFontNames():
            F_MONO = "DMMono"
    except Exception:
        log.warning("Registrazione font brand fallita — fallback a Helvetica", exc_info=True)


_register_fonts()


def hx(c) -> str:
    return "#" + c.hexval()[2:]


def fix_spacing(s: str) -> str:
    """Ripristina lo spazio dopo la punteggiatura quando il modello lo omette
    ('CCN:current' → 'CCN: current', 'liquidità;senza' → 'liquidità; senza',
    'scadenze,liberare' → 'scadenze, liberare', 'madre.Investimento' →
    'madre. Investimento'). Deterministico, su TUTTA la prosa (passa da html_escape,
    usato da action_box/kpi_table/risk_card/heatmap e dal render generico).
    Guardie: numeri (1,16 · 3.6 · 9:30 · art.90), sigle (S.R.L.), URL (://) restano
    intatti — le regole scattano SOLO quando alla punteggiatura segue una LETTERA."""
    s = re.sub(r"([;:])(?=[A-Za-zÀ-ÿ])", r"\1 ", s)                 # ; : + lettera
    s = re.sub(r",(?=[A-Za-zÀ-ÿ])", ", ", s)                        # , + lettera (non 1,16)
    s = re.sub(r"([a-zà-ÿ]{2})\.(?=[A-ZÀ-Ÿ][a-zà-ÿ])", r"\1. ", s)  # fine-frase minuscola.Maiuscola
    return s


def html_escape(s) -> str:
    import html as _h
    # fix_spacing PRIMA dell'escape: sul testo grezzo (nessuna entità ancora) — dopo
    # l'escape un '&amp;' finirebbe con ';' e la regola ';+lettera' romperebbe l'entità.
    return _h.escape(fix_spacing(str(s if s is not None else "")))


def styles() -> dict:
    base = getSampleStyleSheet()
    def S(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)
    return {
        # gerarchia
        "title": S("title", fontName=F_TITLE, fontSize=24, textColor=CARBON, leading=27, spaceAfter=4),
        "h1": S("h1", fontName=F_TITLE, fontSize=15, textColor=CARBON, leading=19,
                spaceBefore=14, spaceAfter=6),
        "h2": S("h2", fontName=F_BOLD, fontSize=11.5, textColor=GOLD_DK, leading=15,
                spaceBefore=9, spaceAfter=3),
        "h3": S("h3", fontName=F_BOLD, fontSize=10, textColor=TEXT, leading=13,
                spaceBefore=6, spaceAfter=2),
        "body": S("body", fontName=F_BODY, fontSize=10, textColor=TEXT, leading=15, spaceAfter=5),
        "bullet": S("bullet", fontName=F_BODY, fontSize=10, textColor=TEXT, leading=14,
                    leftIndent=12, spaceAfter=3),
        "lead": S("lead", fontName=F_BODY, fontSize=11, textColor=TEXT, leading=17, spaceAfter=6),
        "kv": S("kv", fontName=F_BODY, fontSize=9, textColor=TEXT_GRAY, leading=12),
        "kvb": S("kvb", fontName=F_BOLD, fontSize=9, textColor=TEXT, leading=12),
        "small": S("small", fontName=F_BODY, fontSize=8, textColor=NEUTRAL, leading=11),
        "note": S("note", fontName=F_ITALIC, fontSize=8, textColor=NEUTRAL, leading=11),
        "toc": S("toc", fontName=F_BODY, fontSize=11, textColor=TEXT, leading=21),
        # KPI card
        "kpi_num": S("kpi_num", fontName=F_TITLE, fontSize=26, textColor=CARBON, leading=28),
        "kpi_lbl": S("kpi_lbl", fontName=F_BOLD, fontSize=7.5, textColor=NEUTRAL, leading=10),
        "kpi_sub": S("kpi_sub", fontName=F_BODY, fontSize=8, textColor=TEXT_GRAY, leading=11),
    }


# ===================== COMPONENTI ========================================
def badge(text: str, tone=GOLD, fg=colors.white) -> Table:
    """Pill colorata (categoria/stato/priorità)."""
    p = Paragraph(f'<font name="{F_BOLD}" size="7.5" color="{hx(fg)}">{html_escape(str(text).upper())}</font>',
                  ParagraphStyle("b", leading=10))
    t = Table([[p]], hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), tone),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("ROUNDEDCORNERS", [7, 7, 7, 7])]))
    return t


def kpi_card(value, label: str, sub: str = "", tone=None, S=None) -> Table:
    """Card KPI: numero grande + etichetta + sotto-nota, bordo morbido."""
    S = S or styles()
    col = tone or CARBON
    inner = [
        Paragraph(f'<font color="{hx(col)}">{html_escape(value)}</font>', S["kpi_num"]),
        Paragraph(html_escape(label).upper(), S["kpi_lbl"]),
    ]
    if sub:
        inner.append(Spacer(1, 1))
        inner.append(Paragraph(html_escape(sub), S["kpi_sub"]))
    t = Table([[inner]])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.7, LINE),
        ("LINEABOVE", (0, 0), (-1, 0), 2.2, col),
        ("TOPPADDING", (0, 0), (-1, -1), 11), ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return t


def kpi_dashboard(cards: list[dict], S=None, per_row=3) -> Table:
    """Griglia di KPI card. cards = [{value,label,sub?,tone?}]."""
    S = S or styles()
    cells = [kpi_card(c.get("value", "—"), c.get("label", ""), c.get("sub", ""),
                      c.get("tone"), S) for c in cards]
    gap = 4
    cw = (CONTENT_W - gap * (per_row - 1)) / per_row
    rows, row = [], []
    for cell in cells:
        row.append(cell)
        if len(row) == per_row:
            rows.append(row); row = []
    if row:
        while len(row) < per_row:
            row.append("")
        rows.append(row)
    t = Table(rows, colWidths=[cw] * per_row, hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), gap),
                           ("TOPPADDING", (0, 0), (-1, -1), gap / 2), ("BOTTOMPADDING", (0, 0), (-1, -1), gap / 2)]))
    return t


def insight_box(text: str, label="Insight della piattaforma", S=None) -> Table:
    """Box intuizione con barra teal a sinistra e sfondo tenue."""
    S = S or styles()
    body = [Paragraph(f'<font name="{F_BOLD}" size="8.5" color="{hx(GOLD_DK)}">'
                      f'{html_escape(label).upper()}</font>', S["small"]),
            Spacer(1, 2),
            Paragraph(html_escape(text), S["body"])]
    t = Table([["", body]], colWidths=[3, CONTENT_W - 3])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GOLD),
        ("BACKGROUND", (1, 0), (1, -1), CREAM),
        ("LEFTPADDING", (1, 0), (1, -1), 12), ("RIGHTPADDING", (1, 0), (1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def action_box(actions: list, label="Azioni consigliate", S=None) -> Table:
    """Box azioni numerate. MULTI-RIGA → si spezza tra pagine se lungo (una tabella
    a cella singola non si spezzerebbe e darebbe LayoutError su liste lunghe)."""
    S = S or styles()
    rows = [[Paragraph(f'<font name="{F_BOLD}" size="9" color="{hx(CARBON)}">'
                       f'{html_escape(label).upper()}</font>', S["kv"])]]
    for i, a in enumerate(actions, 1):
        txt = a if isinstance(a, str) else (a.get("azione") or a.get("descrizione") or str(a))
        rows.append([Paragraph(
            f'<font name="{F_BOLD}" color="{hx(GOLD_DK)}">{i:02d}</font>&nbsp;&nbsp;{html_escape(txt)}',
            S["bullet"])])
    t = Table(rows, colWidths=[CONTENT_W], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD),
        ("BOX", (0, 0), (-1, -1), 0.7, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (0, 0), 10), ("TOPPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 3), ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
    ]))
    return t


def roadmap(phases: list, S=None) -> Table:
    """Timeline a fasi (card affiancate con numero)."""
    S = S or styles()
    cells = []
    for i, ph in enumerate(phases, 1):
        if isinstance(ph, dict):
            title = ph.get("fase") or ph.get("titolo") or ph.get("nome") or f"Fase {i}"
            desc = ph.get("descrizione") or ph.get("obiettivo") or ph.get("azione") or ""
        else:
            title, desc = str(ph), ""
        inner = [Paragraph(f'<font name="{F_TITLE}" size="13" color="{hx(GOLD_DK)}">{i:02d}</font>', S["kv"]),
                 Spacer(1, 2),
                 Paragraph(f'<font name="{F_BOLD}" size="9.5" color="{hx(CARBON)}">{html_escape(title)}</font>', S["kv"])]
        if desc:
            inner.append(Spacer(1, 2))
            inner.append(Paragraph(html_escape(str(desc))[:160], S["kpi_sub"]))
        cells.append([inner])
    n = max(1, len(cells))
    per = min(4, n)
    gap = 4
    cw = (CONTENT_W - gap * (per - 1)) / per
    rows, row = [], []
    for c in cells:
        row.append(Table([c], colWidths=[cw], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.white), ("BOX", (0, 0), (-1, -1), 0.7, LINE),
            ("LINEABOVE", (0, 0), (-1, 0), 2, GOLD),
            ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("ROUNDEDCORNERS", [4, 4, 4, 4])])))
        if len(row) == per:
            rows.append(row); row = []
    if row:
        while len(row) < per:
            row.append("")
        rows.append(row)
    t = Table(rows, colWidths=[cw] * per, hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), gap),
                           ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return t


def premium_table(headers: list, rows: list, S=None, widths=None, align_right=None) -> Table:
    """Tabella premium: header teal tenue, righe alternate, padding ampio."""
    S = S or styles()
    align_right = align_right or []
    head = [Paragraph(f'<font name="{F_BOLD}" size="8.5" color="{hx(CARBON)}">{html_escape(h)}</font>', S["kv"])
            for h in headers]
    data = [head]
    for r in rows:
        data.append([Paragraph(html_escape(c), S["body"]) for c in r])
    n = len(headers)
    cw = widths or [CONTENT_W / n] * n
    t = Table(data, colWidths=cw, hAlign="LEFT", repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), CREAM),
        ("LINEBELOW", (0, 0), (-1, 0), 1.0, GOLD),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD]),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for c in align_right:
        style.append(("ALIGN", (c, 0), (c, -1), "RIGHT"))
    t.setStyle(TableStyle(style))
    return t


# --- Gauge score (donut) -------------------------------------------------
class Gauge(Flowable):
    def __init__(self, score, label="Score", size=36 * mm):
        super().__init__()
        try:
            self.score = max(0, min(100, int(score)))
        except Exception:
            self.score = None
        self.label = label
        self.width = self.height = size

    def draw(self):
        s = self.width
        val = self.score if self.score is not None else 0
        col = GREEN if val >= 70 else AMBER if val >= 45 else RED
        cx = cy = s / 2
        r = s / 2 - 4
        d = Drawing(s, s)
        d.add(Circle(cx, cy, r, strokeColor=LINE, strokeWidth=7, fillColor=None))
        ang = 90 - (val / 100.0 * 360)
        d.add(Wedge(cx, cy, r, ang, 90, yradius=r, strokeColor=col, strokeWidth=7,
                    fillColor=None, annular=True, radius1=r - 0.01))
        d.add(String(cx, cy - 1, str(val if self.score is not None else "—"),
                     fontName=F_TITLE, fontSize=18, fillColor=CARBON, textAnchor="middle"))
        d.add(String(cx, cy - 13, self.label.upper(), fontName=F_BOLD, fontSize=6,
                     fillColor=NEUTRAL, textAnchor="middle"))
        d.drawOn(self.canv, 0, 0)


# --- Mappa di posizionamento 2x2 a BANDE (no falsa precisione) ----------------
# Rende la mappa strategica come grafico vero invece che coordinate testuali, MA a
# bande qualitative (basso/medio/alto): l'azienda e i competitor sono piazzati per
# banda, niente "0,75" sul grafico (rispetta il C3 del grounding contract: a bande,
# mai falsa precisione). Onesto e leggibile.
def _to_band(v) -> int:
    """coordinata 0-1 o stringa qualitativa → banda 0(basso)/1(medio)/2(alto)."""
    if isinstance(v, str):
        t = v.strip().lower()
        if any(k in t for k in ("alt", "high")):
            return 2
        if any(k in t for k in ("bass", "low")):
            return 0
        return 1
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 1
    if f > 1:  # se per errore è 0-100
        f /= 100.0
    return 0 if f < 0.4 else (2 if f > 0.7 else 1)


class QuadrantMap(Flowable):
    """Mappa 2x2 a bande: azienda (verde) + competitor (grigi), piazzati per banda."""
    def __init__(self, azienda, competitor, asse_x="", asse_y="", width=150 * mm, height=95 * mm):
        super().__init__()
        self.azienda = azienda          # (nome, bx, by)
        self.competitor = competitor    # [(nome, bx, by), ...]
        self.asse_x, self.asse_y = asse_x, asse_y
        self.width, self.height = width, height

    def draw(self):
        c = self.canv
        pad_l, pad_b = 26, 24
        pw = self.width - pad_l - 8
        ph = self.height - pad_b - 14
        ox, oy = pad_l, pad_b
        d = Drawing(self.width, self.height)
        # cornice + griglia 3x3 (le 2 linee di banda)
        d.add(Rect(ox, oy, pw, ph, strokeColor=LINE, strokeWidth=1, fillColor=None))
        for i in (1, 2):
            d.add(Line(ox + pw * i / 3, oy, ox + pw * i / 3, oy + ph, strokeColor=LINE, strokeWidth=0.5))
            d.add(Line(ox, oy + ph * i / 3, ox + pw, oy + ph * i / 3, strokeColor=LINE, strokeWidth=0.5))
        # etichette assi
        d.add(String(ox + pw / 2, oy - 16, (self.asse_x or "Asse X").upper()[:60],
                     fontName=F_BOLD, fontSize=6.5, fillColor=NEUTRAL, textAnchor="middle"))
        d.add(String(ox - 16, oy + ph / 2, (self.asse_y or "Asse Y").upper()[:42],
                     fontName=F_BOLD, fontSize=6.5, fillColor=NEUTRAL, textAnchor="middle", angle=90))
        for i, lab in enumerate(("basso", "medio", "alto")):
            d.add(String(ox + pw * (i + 0.5) / 3, oy - 7, lab, fontName=F_BODY, fontSize=5.5,
                         fillColor=NEUTRAL, textAnchor="middle"))
            d.add(String(ox - 6, oy + ph * (i + 0.5) / 3 - 2, lab, fontName=F_BODY, fontSize=5.5,
                         fillColor=NEUTRAL, textAnchor="end"))

        def cell_xy(bx, by, jitter=0.0):
            return ox + pw * (bx + 0.5) / 3 + jitter, oy + ph * (by + 0.5) / 3

        # competitor (grigi) — jitter se più d'uno nella stessa cella
        seen: dict = {}
        for nome, bx, by in self.competitor:
            k = (bx, by); n = seen.get(k, 0); seen[k] = n + 1
            x, y = cell_xy(bx, by, jitter=(n - 0.5) * 10 if n else 0)
            d.add(Circle(x, y, 3.5, strokeColor=NEUTRAL, strokeWidth=0.5, fillColor=WARM))
            d.add(String(x, y + 6, str(nome)[:22], fontName=F_BODY, fontSize=5.5,
                         fillColor=NEUTRAL, textAnchor="middle"))
        # azienda (verde, evidenziata)
        if self.azienda:
            nome, bx, by = self.azienda
            x, y = cell_xy(bx, by)
            d.add(Circle(x, y, 5.5, strokeColor=GREEN, strokeWidth=1.2, fillColor=GREEN))
            d.add(String(x, y + 9, str(nome)[:24], fontName=F_BOLD, fontSize=6.5,
                         fillColor=CARBON, textAnchor="middle"))
        d.drawOn(c, 0, 0)


def quadrant_map(mappa: dict, S=None):
    """Costruisce QuadrantMap dal blocco 'mappa' del deliverable (struttura libera).
    Ritorna None se non trova posizioni usabili → il chiamante tiene il testo."""
    if not isinstance(mappa, dict):
        return None

    def _xy(o):
        if not isinstance(o, dict):
            return None
        x = o.get("coordinata_x", o.get("x", o.get("asse_x", o.get("ampiezza"))))
        y = o.get("coordinata_y", o.get("y", o.get("asse_y", o.get("segmentazione"))))
        if x is None and y is None:
            return None
        return _to_band(x), _to_band(y)

    az = mappa.get("posizione_azienda") or mappa.get("azienda") or mappa.get("cliente")
    az_xy = _xy(az) if isinstance(az, dict) else None
    azienda = (az.get("nome") or az.get("label") or "La tua azienda", *az_xy) if az_xy else None

    comps = mappa.get("posizione_competitor") or mappa.get("competitor") or mappa.get("competitors") or []
    competitor = []
    for cdict in comps if isinstance(comps, list) else []:
        cxy = _xy(cdict)
        if cxy:
            competitor.append((cdict.get("nome") or cdict.get("label") or "Competitor", *cxy))

    if not azienda and not competitor:
        return None
    da = mappa.get("descrizione_assi") or {}
    ax = (da.get("asse_x") if isinstance(da, dict) else "") or mappa.get("asse_x", "") or "Ampiezza offerta"
    ay = (da.get("asse_y") if isinstance(da, dict) else "") or mappa.get("asse_y", "") or "Segmentazione cliente"
    return QuadrantMap(azienda, competitor, asse_x=str(ax), asse_y=str(ay))


# --- Barre di punteggio (Porter, scoring 1-5) → visual, non testo ------------
class _Bar(Flowable):
    """Barra orizzontale 0..max con valore. Punteggio a rubrica (1-5), non falsa
    precisione: è una scala discreta dichiarata."""
    def __init__(self, score, max_score=5, width=70 * mm, height=9):
        super().__init__()
        self.score = score
        self.max = max_score or 5
        self.width, self.height = width, height

    def draw(self):
        try:
            val = max(0, min(self.max, float(self.score)))
        except (TypeError, ValueError):
            val = 0
        frac = val / self.max if self.max else 0
        col = GREEN if frac >= 0.66 else AMBER if frac >= 0.33 else RED
        d = Drawing(self.width, self.height)
        d.add(Rect(0, 0, self.width, self.height, rx=2, ry=2, strokeColor=None, fillColor=WARM))
        if frac > 0:
            d.add(Rect(0, 0, self.width * frac, self.height, rx=2, ry=2, strokeColor=None, fillColor=col))
        d.add(String(self.width - 2, self.height / 2 - 3,
                     f"{int(val) if val == int(val) else round(val,1)}/{self.max}",
                     fontName=F_BOLD, fontSize=6.5, fillColor=NEUTRAL, textAnchor="end"))
        d.drawOn(self.canv, 0, 0)


def score_bars(items: list, S=None, *, label_key="forza", score_key="scoring",
               desc_key="motivazione", max_score=5, title="") -> Table:
    """Lista {label, score, desc} → tabella con barre orizzontali (es. forze di Porter)."""
    S = S or styles()
    rows = []
    for it in items:
        if not isinstance(it, dict):
            continue
        lab = it.get(label_key) or it.get("voce") or it.get("nome") or it.get("label") or ""
        sc = it.get(score_key, it.get("punteggio", it.get("valore")))
        desc = it.get(desc_key) or it.get("descrizione") or ""
        left = [Paragraph(f"<b>{html_escape(str(lab))}</b>", S["kvb"])]
        if desc:
            left.append(Paragraph(html_escape(str(desc))[:240], S["small"]))
        rows.append([left, _Bar(sc, max_score)])
    if not rows:
        return Spacer(0, 0)
    t = Table(rows, colWidths=[CONTENT_W * 0.58, CONTENT_W * 0.42], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (0, -1), 0), ("RIGHTPADDING", (1, 0), (1, -1), 0),
    ]))
    return t


def semaforo_dot(stato: str) -> str:
    col = SEMAFORO.get(str(stato).lower(), NEUTRAL)
    # '•' (U+2022): presente nei font imbarcati — '●' usciva come glifo tofu nel PDF
    return f'<font color="{hx(col)}" size="12">•</font> {html_escape(str(stato).capitalize())}'


def heatmap(items: list, S, area_key="area", sem_key="semaforo") -> Table:
    """Griglia aree colorate per semaforo (mappa rischi)."""
    S = S or styles()
    chips = []
    for it in items:
        sem = str(it.get(sem_key, "")).lower()
        col = SEMAFORO.get(sem, NEUTRAL)
        area = str(it.get(area_key) or it.get("nome") or it.get("titolo") or "")
        chip = Table([[Paragraph(f'<font name="{F_BOLD}" color="white" size="8.5">{html_escape(area)}</font>',
                                 S["kv"])]])
        chip.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), col),
                                  ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                                  ("ROUNDEDCORNERS", [4, 4, 4, 4])]))
        chips.append(chip)
    per, gap = 3, 4
    cw = (CONTENT_W - gap * (per - 1)) / per
    rows, row = [], []
    for c in chips:
        row.append(c)
        if len(row) == per:
            rows.append(row); row = []
    if row:
        while len(row) < per:
            row.append("")
        rows.append(row)
    t = Table(rows, colWidths=[cw] * per, hAlign="LEFT")
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), gap),
                           ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return t


def risk_card(descr: str, gravita: str, S, extra: str = "") -> Table:
    """Card rischio: barra colorata per gravità + badge + testo."""
    S = S or styles()
    col = SEMAFORO.get(str(gravita).lower(), NEUTRAL)
    body = [Paragraph(
        f'<font name="{F_BOLD}" color="{hx(col)}">{html_escape(str(gravita).capitalize())}</font>&nbsp;&nbsp;'
        f'{html_escape(descr)}' + (f'<br/><font size="8" color="{hx(NEUTRAL)}">{html_escape(extra)}</font>' if extra else ''),
        S["body"])]
    t = Table([["", body]], colWidths=[3, CONTENT_W - 3])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), col),
        ("BACKGROUND", (1, 0), (1, -1), CARD),
        ("LEFTPADDING", (1, 0), (1, -1), 10), ("RIGHTPADDING", (1, 0), (1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROUNDEDCORNERS", [3, 3, 3, 3]),
    ]))
    return t


def kpi_table(items: list, S) -> Table:
    """Tabella indicatori: nome · valore · benchmark · semaforo."""
    S = S or styles()
    cols = ["nome", "valore", "benchmark", "semaforo"]
    label = {"nome": "Indicatore", "valore": "Valore", "benchmark": "Benchmark", "semaforo": "Stato"}
    present = [c for c in cols if any(c in it for it in items)]
    headers = [label[c] for c in present]
    rows = []
    for it in items:
        r = []
        for c in present:
            v = it.get(c, "")
            r.append(semaforo_dot(v) if c == "semaforo" else html_escape(v))
        rows.append(r)
    # usa premium_table ma con semaforo come Paragraph rich → costruisco a mano
    head = [Paragraph(f'<font name="{F_BOLD}" size="8.5" color="{hx(CARBON)}">{h}</font>', S["kv"]) for h in headers]
    data = [head] + [[Paragraph(cell, S["body"]) for cell in r] for r in rows]
    n = len(present)
    widths = [CONTENT_W * w for w in ([0.42, 0.18, 0.28, 0.12] if n == 4 else [1.0 / n] * n)][:n]
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), CREAM),
        ("LINEBELOW", (0, 0), (-1, 0), 1.0, GOLD),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD]),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def section_number(num: int, title: str, S=None) -> Table:
    """Divisore di sezione: numero teal + titolo Syne sulla stessa linea + rule sotto."""
    S = S or styles()
    st = ParagraphStyle("secn", fontName=F_TITLE, fontSize=14.5, textColor=CARBON, leading=18)
    sn = ParagraphStyle("secnum", fontName=F_TITLE, fontSize=14.5, textColor=GOLD, leading=18)
    cell = [[Paragraph(f"{num:02d}", sn), Paragraph(html_escape(title), st)]]
    t = Table(cell, colWidths=[10 * mm, CONTENT_W - 10 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LINEBELOW", (0, 0), (-1, -1), 1.0, GOLD),
                           ("LEFTPADDING", (0, 0), (0, 0), 0), ("LEFTPADDING", (1, 0), (1, 0), 2),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t


# ===================== REDESIGN v16 — decision support ==================
# Coerente col report premium K-BOT (stessa struttura), palette 8e (oro/carbon).

_LAYER_TONE = {
    "executive": GOLD,
    "analysis": TEXT_GRAY, "analisi": TEXT_GRAY,
    "appendix": NEUTRAL, "appendice": NEUTRAL,
}


def layer_band(layer: str, title: str, subtitle: str = "", S=None) -> Table:
    """Banda di livello di lettura (Executive / Analisi / Appendice) — full width."""
    S = S or styles()
    accent = _LAYER_TONE.get(str(layer).lower(), TEXT_GRAY)
    bg = CREAM if str(layer).lower() == "executive" else WARM
    inner = [Paragraph(f'<font name="{F_MONO}" size="8.5" color="{hx(accent)}">'
                       f'{html_escape(title).upper()}</font>', S["kv"])]
    if subtitle:
        inner.append(Paragraph(f'<font name="{F_BODY}" size="8.5" color="{hx(NEUTRAL)}">'
                               f'{html_escape(subtitle)}</font>', S["kv"]))
    t = Table([["", inner]], colWidths=[3, CONTENT_W - 3], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), accent),
        ("BACKGROUND", (1, 0), (1, -1), bg),
        ("LEFTPADDING", (1, 0), (1, -1), 12), ("RIGHTPADDING", (1, 0), (1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def decision_board(cells: list[dict], title="Decision Board", S=None) -> Table:
    """Board decisionale finale: header carbon + celle (label + valore colorato).
    cells = [{label, value, tone?}]. L'ultima cella evidenziata se tone verde/rosso."""
    S = S or styles()
    cells = [c for c in cells if isinstance(c, dict)][:6]
    if not cells:
        return Spacer(0, 0)
    head = Paragraph(f'<font name="{F_MONO}" size="9" color="white">{html_escape(title).upper()}</font>', S["kv"])
    head_row = Table([[head]], colWidths=[CONTENT_W])
    head_row.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CARBON),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                                  ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    n = len(cells)
    cw = CONTENT_W / n
    row = []
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("BACKGROUND", (0, 0), (-1, -1), colors.white),
             ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
             ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
             ("LINEAFTER", (0, 0), (-2, -1), 0.5, LINE)]
    for i, c in enumerate(cells):
        tone = c.get("tone") or NEUTRAL
        stack = [Paragraph(f'<font name="{F_MONO}" size="7.5" color="{hx(NEUTRAL)}">'
                           f'{html_escape(c.get("label", "")).upper()}</font>', S["kv"]),
                 Spacer(1, 3),
                 Paragraph(f'<font name="{F_BOLD}" size="11" color="{hx(tone if tone != NEUTRAL else CARBON)}">'
                           f'{html_escape(c.get("value", ""))}</font>', S["kv"])]
        row.append(stack)
        if tone == GREEN:
            style.append(("BACKGROUND", (i, 0), (i, 0), colors.HexColor("#F1F7F0")))
        elif tone == RED:
            style.append(("BACKGROUND", (i, 0), (i, 0), colors.HexColor("#FBF2F1")))
    grid = Table([row], colWidths=[cw] * n)
    grid.setStyle(TableStyle(style))
    wrap = Table([[head_row], [grid]], colWidths=[CONTENT_W])
    wrap.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, CARBON),
                              ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                              ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return wrap


_SEV_TONE = {"critical": RED, "critica": RED, "alta": RED, "high": colors.HexColor("#C2410C"),
             "media": AMBER, "medium": AMBER, "bassa": NEUTRAL, "low": NEUTRAL}


def severity_matrix(items: list, S=None) -> Table:
    """Matrice priorità: Problema | Severity | Effort | ROI (severity colorata)."""
    S = S or styles()
    rows_in = [it for it in items if isinstance(it, dict)]
    if not rows_in:
        return Spacer(0, 0)
    head = [Paragraph(f'<font name="{F_BOLD}" size="8.5" color="{hx(CARBON)}">{h}</font>', S["kv"])
            for h in ("Problema", "Severity", "Effort", "ROI")]
    data = [head]
    for it in rows_in[:12]:
        sev = str(it.get("severity") or it.get("gravita") or it.get("livello") or "")
        col = _SEV_TONE.get(sev.lower(), NEUTRAL)
        prob = str(it.get("problema") or it.get("problem") or it.get("titolo") or it.get("descrizione") or "")
        effort = str(it.get("effort") or it.get("sforzo") or "")
        roi = str(it.get("roi") or it.get("ritorno") or "")
        rc = SEMAFORO.get(roi.lower(), TEXT)
        data.append([
            Paragraph(f'<b>{html_escape(prob)}</b>', S["body"]),
            Paragraph(f'<font name="{F_BOLD}" color="{hx(col)}">{html_escape(sev.capitalize())}</font>', S["body"]),
            Paragraph(html_escape(effort), S["body"]),
            Paragraph(f'<font color="{hx(rc)}">{html_escape(roi.capitalize())}</font>', S["body"]),
        ])
    widths = [CONTENT_W * w for w in (0.46, 0.20, 0.17, 0.17)]
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), CREAM),
        ("LINEBELOW", (0, 0), (-1, 0), 1.0, GOLD),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD]),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


# ===================== COPERTINA + PAGINE FISSE ==========================
def _kicker(canvas, x, y, text, size=7.5, color=GOLD_DK, spacing=1.4, right=None):
    """Etichetta uppercase con letter-spacing (look editoriale del riferimento).
    Usa un text object (charSpace non è sul Canvas in tutte le versioni)."""
    t = str(text).upper()
    canvas.saveState()
    canvas.setFillColor(color)
    try:
        if right is not None:
            w = canvas.stringWidth(t, F_BOLD, size) + spacing * max(0, len(t) - 1)
            x = right - w
        to = canvas.beginText(x, y)
        to.setFont(F_BOLD, size)
        to.setCharSpace(spacing)
        to.setFillColor(color)
        to.textOut(t)
        canvas.drawText(to)
    except Exception:
        canvas.setFont(F_BOLD, size)
        if right is not None:
            canvas.drawRightString(right, y, t)
        else:
            canvas.drawString(x, y, t)
    canvas.restoreState()


def _cover_meta(canvas, x, y, label, value, max_width=None):
    _kicker(canvas, x, y + 4.5 * mm, label, size=7, color=GOLD_DK, spacing=1.2)
    canvas.setFillColor(TEXT); canvas.setFont(F_BOLD, 10.5)
    text = str(value)
    if max_width:
        while text and canvas.stringWidth(text, F_BOLD, 10.5) > max_width:
            text = text[:-1]
        if text != str(value):
            text = text[:-1].rstrip() + "…" if len(text) > 1 else "…"
    canvas.drawString(x, y, text)


def cover_page(canvas, *, modulo, titolo, sottotitolo, azienda="", periodo="",
               versione="1.0", codice="", categoria="DIAGNOSI", valore="", data=""):
    """Copertina white-editorial (design riferimento K2A): fondo bianco caldo, logo +
    kicker in alto, titolone Syne, deck, e strip fatti in basso. Accenti oro."""
    # fondo bianco caldo + barra oro sottile in alto
    canvas.setFillColor(WARM); canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    canvas.setFillColor(GOLD); canvas.rect(0, PAGE_H - 3 * mm, PAGE_W, 3 * mm, stroke=0, fill=1)
    # logo su chip scuro (il PNG è bianco) in alto a sinistra + kicker a destra
    top = PAGE_H - 20 * mm
    try:
        from reportlab.lib.utils import ImageReader
        if os.path.exists(_LOGO):
            logo = ImageReader(_LOGO); iw, ih = logo.getSize()
            lh = 7 * mm; lw = lh * iw / ih
            canvas.setFillColor(CARBON); canvas.roundRect(MARGIN - 3, top - 2 * mm, lw + 6, lh + 4, 2.5, stroke=0, fill=1)
            canvas.drawImage(logo, MARGIN, top - 1 * mm, width=lw, height=lh, mask=[0, 12, 0, 12, 0, 12])
    except Exception:
        pass
    _kicker(canvas, 0, top + 1 * mm, f"{categoria} · {periodo or data or '2026'}",
            size=7.5, color=GOLD_DK, spacing=1.6, right=PAGE_W - MARGIN)

    # blocco editoriale (kicker modulo + titolone + deck) ~ a metà alta
    by = PAGE_H * 0.60
    _kicker(canvas, MARGIN, by + 9 * mm, modulo, size=9, color=GOLD_DK, spacing=2.0)
    # titolone Syne, wrap manuale su 2 righe
    canvas.setFillColor(CARBON); canvas.setFont(F_TITLE, 34)
    words = str(titolo).split(); lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if canvas.stringWidth(t, F_TITLE, 34) <= CONTENT_W and len(lines) < 1:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur); lines = [l for l in lines if l][:2]
    for i, ln in enumerate(lines):
        canvas.drawString(MARGIN, by - i * 13 * mm, ln)
    ty = by - (len(lines) - 1) * 13 * mm
    if sottotitolo:
        canvas.setFillColor(TEXT_GRAY); canvas.setFont(F_BODY, 13)
        canvas.drawString(MARGIN, ty - 9 * mm, str(sottotitolo)[:80])
    if valore:
        canvas.setFillColor(NEUTRAL); canvas.setFont(F_BODY, 10)
        canvas.drawString(MARGIN, ty - 16 * mm, str(valore)[:104])

    # strip fatti in basso (Cliente/Periodo/Versione/Documento) — come il riferimento
    my = 34 * mm
    canvas.setStrokeColor(LINE); canvas.setLineWidth(0.8)
    canvas.line(MARGIN, my + 13 * mm, PAGE_W - MARGIN, my + 13 * mm)
    col_w = CONTENT_W / 4
    metas = [("Cliente", azienda or "—"), ("Periodo", periodo or "—"),
             ("Versione", f"v{versione}"), ("Documento", codice or data or "2026")]
    for i, (lb, va) in enumerate(metas):
        canvas.setStrokeColor(GOLD); canvas.setLineWidth(1.2)
        canvas.line(MARGIN + i * col_w, my + 9 * mm, MARGIN + i * col_w, my - 1 * mm)
        _cover_meta(canvas, MARGIN + i * col_w + 4 * mm, my, lb, va,
                    max_width=col_w - 8 * mm)
    # footer
    _kicker(canvas, MARGIN, 14 * mm, "K2-AI · K2A S.R.L.S. · documento riservato e confidenziale",
            size=7, color=NEUTRAL, spacing=0.8)
    canvas.setFillColor(NEUTRAL); canvas.setFont(F_BODY, 7.5)
    canvas.drawRightString(PAGE_W - MARGIN, 14 * mm, "k2-ai.it")


def page_header(canvas, report_name: str):
    y = PAGE_H - 12 * mm
    xname = MARGIN
    try:
        from reportlab.lib.utils import ImageReader
        if os.path.exists(_LOGO):
            logo = ImageReader(_LOGO); iw, ih = logo.getSize()
            lh = 5.5 * mm; lw = lh * iw / ih
            canvas.setFillColor(CARBON)
            canvas.roundRect(MARGIN - 3, y - 1.6 * mm, lw + 6, lh + 3.2, 2, stroke=0, fill=1)
            canvas.drawImage(logo, MARGIN, y, width=lw, height=lh, mask=[0, 12, 0, 12, 0, 12])
            xname = MARGIN + lw + 6
    except Exception:
        pass
    canvas.setFillColor(NEUTRAL); canvas.setFont(F_BODY, 8)
    canvas.drawRightString(PAGE_W - MARGIN, y + 1.4 * mm, report_name)
    canvas.setStrokeColor(LINE); canvas.setLineWidth(0.6)
    canvas.line(MARGIN, y - 3 * mm, PAGE_W - MARGIN, y - 3 * mm)


def footer(canvas, doc, report_name="K2-AI"):
    canvas.saveState()
    canvas.setStrokeColor(LINE); canvas.setLineWidth(0.6)
    canvas.line(MARGIN, 14 * mm, PAGE_W - MARGIN, 14 * mm)
    canvas.setFillColor(NEUTRAL); canvas.setFont(F_BODY, 7.5)
    canvas.drawString(MARGIN, 9.5 * mm, f"{report_name} · K2-AI · riservato")
    canvas.drawCentredString(PAGE_W / 2, 9.5 * mm, "Documento confidenziale")
    canvas.drawRightString(PAGE_W - MARGIN, 9.5 * mm, f"pag. {max(1, doc.page - 1)}")
    canvas.restoreState()
