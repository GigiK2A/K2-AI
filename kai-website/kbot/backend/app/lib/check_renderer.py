"""Renderer D1 PREMIUM — trasforma il risultato di un Check express (calcolo
deterministico) in un PDF deliverable coerente con il design system K2-AI.

NESSUN LLM: layout fisso, dati dal calcolo. Versione compatta (1-2 pagine) della
stessa famiglia visiva dei report 8e: palette, tipografia (DMSans + Syne), header
brandizzato, KPI card, tabelle premium, CTA finale.
"""
from __future__ import annotations

import html
import io
import re
from datetime import date
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

_ASSETS = Path(__file__).resolve().parents[1] / "assets"
_FONTS = _ASSETS / "fonts"

# ---- palette (allineata al design system 8e) ----
CARBON = colors.HexColor("#0B0D0E")
TEAL = colors.HexColor("#00BFA6")
TEAL_DK = colors.HexColor("#039F8B")
WARM = colors.HexColor("#F7F8F6")
TEXT = colors.HexColor("#1F2430")
TEXT_GRAY = colors.HexColor("#4B5563")
LINE = colors.HexColor("#E5E7EB")
NEUTRAL = colors.HexColor("#6B7280")
CARD = colors.HexColor("#FBFCFB")
TEAL_SOFT = colors.HexColor("#E6F7F4")

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

F_BODY, F_BOLD, F_TITLE = "Helvetica", "Helvetica-Bold", "Helvetica-Bold"


def _register_fonts() -> None:
    global F_BODY, F_BOLD, F_TITLE
    try:
        for name, fn in [("DMSans", "DMSans-Regular.ttf"), ("DMSans-Bold", "DMSans-SemiBold.ttf"),
                         ("Syne", "Syne-Bold.ttf")]:
            p = _FONTS / fn
            if p.exists():
                pdfmetrics.registerFont(TTFont(name, str(p)))
        names = pdfmetrics.getRegisteredFontNames()
        if "DMSans" in names:
            F_BODY, F_BOLD = "DMSans", "DMSans-Bold"
        if "Syne" in names:
            F_TITLE = "Syne"
    except Exception:
        pass


_register_fonts()

_DISCLAIMER = (
    "Documento generato da K2-AI tramite calcolo deterministico sui dati forniti. Ha "
    "finalità di supporto decisionale e non sostituisce la consulenza di un professionista "
    "abilitato; gli esiti vanno verificati in relazione al contesto e agli obblighi applicabili. "
    "Per un'analisi approfondita è possibile richiedere un report specialistico tramite la piattaforma."
)


def _styles() -> dict:
    ss = getSampleStyleSheet()
    def S(name, **kw):
        return ParagraphStyle(name, parent=ss["Normal"], **kw)
    return {
        "h2": S("h2", fontName=F_TITLE, fontSize=12.5, textColor=CARBON, leading=16, spaceBefore=10, spaceAfter=4),
        "body": S("body", fontName=F_BODY, fontSize=9.5, textColor=TEXT, leading=14),
        "cell": S("cell", fontName=F_BODY, fontSize=9, textColor=TEXT, leading=12),
        "cellb": S("cellb", fontName=F_BOLD, fontSize=9, textColor=TEXT, leading=12),
        "small": S("small", fontName=F_BODY, fontSize=7.5, textColor=NEUTRAL, leading=10.5),
        "kpi_num": S("kpi_num", fontName=F_TITLE, fontSize=20, textColor=CARBON, leading=22),
        "kpi_lbl": S("kpi_lbl", fontName=F_BOLD, fontSize=7, textColor=NEUTRAL, leading=9),
    }


def _human(k: str) -> str:
    return html.escape(str(k).replace("_", " ").replace("pct", "%").replace("eur", "€").strip().capitalize())


def _fmt(v: Any) -> str:
    if isinstance(v, bool):
        return "Sì" if v else "No"
    if isinstance(v, float):
        return html.escape(f"{v:,.2f}".replace(",", "·").replace(".", ",").replace("·", "."))
    if isinstance(v, int):
        return html.escape(f"{v:,}".replace(",", "."))
    return html.escape(str(v))


def _is_money(key: str) -> bool:
    return any(t in key.lower() for t in ("eur", "€", "importo", "massimale", "plafond", "valore", "costo"))


# ---- header brandizzato (band scura) ----
def _header_band(label: str, S) -> Table:
    logo = _ASSETS / "logo-k2ai.png"
    left = []
    if logo.exists():
        try:
            img = Image(str(logo)); img._restrictSize(28 * mm, 9 * mm); img.hAlign = "LEFT"
            left.append(img)
        except Exception:
            pass
    left.append(Spacer(1, 3))
    left.append(Paragraph(f'<font name="{F_TITLE}" size="16" color="white">{html.escape(label)}</font>',
                          ParagraphStyle("t", leading=19)))
    left.append(Paragraph(f'<font name="{F_BODY}" size="8.5" color="#9AA6A3">Check express · '
                          f'{date.today().isoformat()}</font>', ParagraphStyle("s", leading=12)))
    badge = Paragraph(f'<font name="{F_BOLD}" size="7.5" color="{("#0B0D0E")}">CALCOLO DETERMINISTICO</font>',
                      ParagraphStyle("b", leading=10))
    bt = Table([[badge]])
    bt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TEAL), ("ROUNDEDCORNERS", [6, 6, 6, 6]),
                            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7)]))
    band = Table([[left, [bt]]], colWidths=[CONTENT_W - 42 * mm, 42 * mm])
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARBON),
        ("VALIGN", (0, 0), (0, 0), "MIDDLE"), ("VALIGN", (1, 0), (1, 0), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14), ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LINEABOVE", (0, 0), (-1, 0), 4, TEAL),
    ]))
    return band


def _kpi_card(value, label, S):
    inner = [Paragraph(_fmt(value), S["kpi_num"]), Paragraph(_human(label).upper(), S["kpi_lbl"])]
    t = Table([[inner]])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white), ("BOX", (0, 0), (-1, -1), 0.7, LINE),
        ("LINEABOVE", (0, 0), (-1, 0), 2, TEAL),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("ROUNDEDCORNERS", [4, 4, 4, 4])]))
    return t


def _kpi_row(pairs, S):
    """Griglia di card per i valori scalari principali (max 3 per riga)."""
    cards = [_kpi_card(v, k, S) for k, v in pairs]
    per, gap = 3, 4
    cw = (CONTENT_W - gap * (per - 1)) / per
    rows, row = [], []
    for c in cards:
        row.append(c)
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


def _kv_table(d: dict, S) -> Table | None:
    rows = [[Paragraph(_human(k), S["cell"]), Paragraph(_fmt(v), S["cellb"])]
            for k, v in d.items() if not isinstance(v, (dict, list)) and v is not None and v != ""]
    if not rows:
        return None
    t = Table(rows, colWidths=[CONTENT_W * 0.55, CONTENT_W * 0.45], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("TEXTCOLOR", (0, 0), (0, -1), TEXT_GRAY),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, CARD]),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def _table_of_dicts(rows: list, S) -> Table:
    cols = list({k for x in rows for k in x if not isinstance(x[k], (dict, list))})
    head = [Paragraph(f'<font name="{F_BOLD}" size="8" color="{"#0B0D0E"}">{_human(c)}</font>', S["cell"]) for c in cols]
    data = [head] + [[Paragraph(_fmt(x.get(c, "")), S["cell"]) for c in cols] for x in rows]
    t = Table(data, colWidths=[CONTENT_W / max(len(cols), 1)] * len(cols), hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL_SOFT), ("LINEBELOW", (0, 0), (-1, 0), 1.0, TEAL),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD]),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def _render_value(key: str, val: Any, S, story: list, depth=0) -> None:
    if isinstance(val, dict):
        story.append(Paragraph(_human(key), S["h2"]))
        t = _kv_table(val, S)
        if t:
            story.append(t)
        for k, v in val.items():
            if isinstance(v, (dict, list)):
                _render_value(k, v, S, story, depth + 1)
    elif isinstance(val, list) and val:
        story.append(Paragraph(_human(key), S["h2"]))
        if all(isinstance(x, dict) for x in val):
            story.append(_table_of_dicts(val, S))
        else:
            for x in val:
                story.append(Paragraph("• " + _fmt(x), S["body"]))


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE); canvas.setLineWidth(0.6)
    canvas.line(MARGIN, 13 * mm, PAGE_W - MARGIN, 13 * mm)
    canvas.setFillColor(NEUTRAL); canvas.setFont(F_BODY, 7.5)
    canvas.drawString(MARGIN, 9 * mm, "K2-AI · Check express · documento riservato")
    canvas.drawRightString(PAGE_W - MARGIN, 9 * mm, f"pag. {doc.page}")
    canvas.restoreState()


def render_check_pdf(service_id: str, label: str, inputs: dict, result: Any) -> bytes:
    """Compone il PDF D1 premium del check. Ritorna i byte del PDF."""
    S = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=15 * mm, bottomMargin=18 * mm, title=f"{label} — K2-AI")
    story: list = [_header_band(label, S), Spacer(1, 10)]

    # KPI card per i valori scalari principali del risultato
    if isinstance(result, dict):
        scalars = [(k, v) for k, v in result.items()
                   if isinstance(v, (int, float)) and not isinstance(v, bool)][:6]
        money = [(k, v) for k, v in scalars if _is_money(k)] or scalars
        if money:
            story.append(Paragraph("Sintesi", S["h2"]))
            story.append(_kpi_row(money[:6], S))
            story.append(Spacer(1, 8))

    if inputs:
        story.append(Paragraph("Dati analizzati", S["h2"]))
        t = _kv_table(inputs, S)
        if t:
            story.append(t)
        for k, v in inputs.items():
            if isinstance(v, (dict, list)):
                _render_value(k, v, S, story)
        story.append(Spacer(1, 4))

    story.append(Paragraph("Esito dell'analisi", S["h2"]))
    if isinstance(result, dict):
        t = _kv_table(result, S)
        if t:
            story.append(t)
        for k, v in result.items():
            if isinstance(v, (dict, list)):
                _render_value(k, v, S, story)
    else:
        story.append(Paragraph(_fmt(result), S["body"]))

    # CTA / disclaimer
    story.append(Spacer(1, 12))
    cta = Table([[Paragraph(_DISCLAIMER, S["small"])]], colWidths=[CONTENT_W])
    cta.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), WARM), ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                             ("LINEABOVE", (0, 0), (-1, 0), 2, TEAL),
                             ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                             ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    story.append(cta)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
