"""Renderer D1 — trasforma il risultato di un Check express (calcolo deterministico)
in un PDF deliverable scaricabile. NESSUN LLM: layout fisso, dati dal calcolo.

Rende i 15 servizi "consumo" prodotti veri (non solo JSON). Brand K2-AI (logo + palette).
"""
from __future__ import annotations

import html
import io
from datetime import date
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

_ASSETS = Path(__file__).resolve().parents[1] / "assets"
PRIMARY = colors.HexColor("#1d7d70")
DARK = colors.HexColor("#0d0f12")
SURFACE_2 = colors.HexColor("#F7F7F5")
BORDER = colors.HexColor("#E8E8E4")
MUTED = colors.HexColor("#6b7280")

_DISCLAIMER = (
    "Documento generato automaticamente da K2-AI tramite calcolo deterministico su "
    "dati forniti dall'utente. Ha valore orientativo e non sostituisce la consulenza "
    "di un professionista abilitato. Verificare gli esiti con un consulente qualificato."
)


def _styles() -> dict:
    ss = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=ss["Title"], fontSize=20, textColor=DARK,
                             spaceAfter=2, leading=24),
        "sub": ParagraphStyle("sub", parent=ss["Normal"], fontSize=10, textColor=MUTED,
                              spaceAfter=10),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12, textColor=PRIMARY,
                             spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("body", parent=ss["Normal"], fontSize=9.5, textColor=DARK,
                               leading=13),
        "small": ParagraphStyle("small", parent=ss["Normal"], fontSize=7.5, textColor=MUTED,
                                leading=10),
        "cell": ParagraphStyle("cell", parent=ss["Normal"], fontSize=9, textColor=DARK, leading=12),
        "cellb": ParagraphStyle("cellb", parent=ss["Normal"], fontSize=9, textColor=DARK,
                                leading=12, fontName="Helvetica-Bold"),
    }


def _human(k: str) -> str:
    return html.escape(str(k).replace("_", " ").replace("pct", "%").strip().capitalize())


def _fmt(v: Any) -> str:
    # ESCAPE: i valori finiscono in reportlab Paragraph (mini-markup XML). Senza
    # escape, un input utente con '<' o '&' romperebbe il parser o inietterebbe markup.
    if isinstance(v, bool):
        return "Sì" if v else "No"
    if isinstance(v, float):
        return f"{v:,.2f}".replace(",", "·").replace(".", ",").replace("·", ".")
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    return html.escape(str(v))


def _kv_table(d: dict, S: dict, content_w: float) -> Table:
    rows = [[Paragraph(_human(k), S["cell"]), Paragraph(_fmt(v), S["cellb"])]
            for k, v in d.items() if not isinstance(v, (dict, list))]
    if not rows:
        return None
    t = Table(rows, colWidths=[content_w * 0.55, content_w * 0.45])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, -1), SURFACE_2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _render_value(key: str, val: Any, S: dict, content_w: float, story: list) -> None:
    if isinstance(val, dict):
        story.append(Paragraph(_human(key), S["h2"]))
        t = _kv_table(val, S, content_w)
        if t:
            story.append(t)
        for k, v in val.items():
            if isinstance(v, (dict, list)):
                _render_value(k, v, S, content_w, story)
    elif isinstance(val, list):
        if not val:
            return
        story.append(Paragraph(_human(key), S["h2"]))
        if all(isinstance(x, dict) for x in val):
            cols = list({k for x in val for k in x if not isinstance(x[k], (dict, list))})
            head = [Paragraph(_human(c), S["cellb"]) for c in cols]
            data = [head] + [[Paragraph(_fmt(x.get(c, "")), S["cell"]) for c in cols] for x in val]
            t = Table(data, colWidths=[content_w / max(len(cols), 1)] * len(cols))
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SURFACE_2]),
                ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(t)
        else:
            for x in val:
                story.append(Paragraph("• " + _fmt(x), S["body"]))


def render_check_pdf(service_id: str, label: str, inputs: dict, result: Any) -> bytes:
    """Compone il PDF D1 del check. Ritorna i byte del PDF."""
    S = _styles()
    buf = io.BytesIO()
    content_w = A4[0] - 36 * mm
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title=f"{label} — K2-AI")
    story: list = []
    logo = _ASSETS / "logo-k2ai.png"
    if logo.exists():
        try:
            img = Image(str(logo)); img._restrictSize(34 * mm, 12 * mm)
            img.hAlign = "LEFT"; story.append(img); story.append(Spacer(1, 6))
        except Exception:
            pass
    story.append(Paragraph(label, S["h1"]))
    story.append(Paragraph(f"Check express · K2-AI · {date.today().isoformat()}", S["sub"]))

    if inputs:
        story.append(Paragraph("Dati analizzati", S["h2"]))
        t = _kv_table(inputs, S, content_w)
        if t:
            story.append(t)
        for k, v in inputs.items():
            if isinstance(v, (dict, list)):
                _render_value(k, v, S, content_w, story)

    story.append(Spacer(1, 4))
    story.append(Paragraph("Esito", S["h2"]))
    if isinstance(result, dict):
        t = _kv_table(result, S, content_w)
        if t:
            story.append(t)
        for k, v in result.items():
            if isinstance(v, (dict, list)):
                _render_value(k, v, S, content_w, story)
    else:
        story.append(Paragraph(_fmt(result), S["body"]))

    story.append(Spacer(1, 14))
    story.append(Paragraph(_DISCLAIMER, S["small"]))
    doc.build(story)
    return buf.getvalue()
