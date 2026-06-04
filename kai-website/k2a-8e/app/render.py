"""Render HTML + PDF (ReportLab). Le citazioni portano fonte + vigenza."""
from __future__ import annotations

import html
from pathlib import Path


def _citazioni_html(citazioni: list[dict]) -> str:
    if not citazioni:
        return ""
    rows = "".join(
        f"<li><b>{html.escape(str(c.get('campo','')))}</b>: "
        f"{html.escape(str(c.get('fonte','')))} — "
        f"<i>{html.escape(str(c.get('vigenza','')))}</i></li>"
        for c in citazioni
    )
    return f"<h2>Fonti</h2><ul>{rows}</ul>"


def render_html(instance: dict, blueprint: dict) -> str:
    titolo = html.escape(blueprint.get("titolo", "Deliverable K2-AI"))
    sezioni = instance.get("sezioni", {})
    voci = blueprint.get("voci", [])
    body = []
    for v in voci:
        vid = v.get("id") or v.get("titolo")
        body.append(f"<h2>{html.escape(str(v.get('titolo', vid)))}</h2>")
        body.append(f"<p>{html.escape(str(sezioni.get(vid, '')))}</p>")
    disclaimer = html.escape(instance.get("disclaimer", ""))
    return (
        f"<!doctype html><html><head><meta charset='utf-8'><title>{titolo}</title></head>"
        f"<body><h1>{titolo}</h1>{''.join(body)}"
        f"{_citazioni_html(instance.get('citazioni', []))}"
        f"<hr><p style='font-size:11px;color:#555'>{disclaimer}</p></body></html>"
    )


def render_pdf(instance: dict, blueprint: dict, pdf_path: Path) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem,
    )

    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, textColor="#555555")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                            topMargin=20 * mm, bottomMargin=20 * mm)
    story = [Paragraph(blueprint.get("titolo", "Deliverable K2-AI"), styles["Title"]),
             Spacer(1, 6 * mm)]

    sezioni = instance.get("sezioni", {})
    for v in blueprint.get("voci", []):
        vid = v.get("id") or v.get("titolo")
        story.append(Paragraph(str(v.get("titolo", vid)), styles["Heading2"]))
        story.append(Paragraph(str(sezioni.get(vid, "")), styles["BodyText"]))
        story.append(Spacer(1, 3 * mm))

    citazioni = instance.get("citazioni", [])
    if citazioni:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("Fonti", styles["Heading2"]))
        items = [
            ListItem(Paragraph(
                f"<b>{c.get('campo','')}</b>: {c.get('fonte','')} — <i>{c.get('vigenza','')}</i>",
                styles["BodyText"]))
            for c in citazioni
        ]
        story.append(ListFlowable(items, bulletType="bullet"))

    if instance.get("disclaimer"):
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(instance["disclaimer"], small))

    doc.build(story)
