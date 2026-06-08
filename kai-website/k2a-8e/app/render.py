"""Render HTML + PDF (ReportLab) dal deliverable conforme a output-schema."""
from __future__ import annotations

import html
from pathlib import Path

_FONTE_LABEL = {"override_locale": "Normattiva", "akn_bulk_xml": "Normattiva",
                "normattiva": "Normattiva"}


def _fonte(f: str) -> str:
    return _FONTE_LABEL.get(str(f), str(f or "Normattiva"))


def _cit_html(citazioni: list[dict]) -> str:
    if not citazioni:
        return ""
    rows = "".join(
        f"<li><b>{html.escape(str(c.get('riferimento') or c.get('campo','')))}</b>: "
        f"{html.escape(_fonte(c.get('fonte','')))} — "
        f"<i>{html.escape(str(c.get('vigenza','')))}</i></li>"
        for c in citazioni
    )
    return f"<h2>Fonti</h2><ul>{rows}</ul>"


def render_html(deliverable: dict, blueprint: dict, citazioni: list[dict]) -> str:
    titolo = html.escape(deliverable.get("meta", {}).get("servizio", "Deliverable K2-AI"))
    az = html.escape(deliverable.get("meta", {}).get("azienda", ""))
    parts = [f"<h1>{titolo}</h1><p><b>{az}</b></p>"]
    s = deliverable.get("sintesi", {})
    parts.append(f"<h2>Sintesi</h2><p>Score compliance: {html.escape(str(s.get('score_compliance','')))}</p>")
    for v in deliverable.get("voci", []):
        parts.append(f"<h2>{html.escape(str(v.get('titolo','')))}</h2>")
        parts.append(f"<p>{html.escape(str(v.get('contenuto','')))}</p>")
    parts.append(_cit_html(citazioni))
    parts.append(f"<hr><p style='font-size:11px;color:#555'>{html.escape(deliverable.get('disclaimer',''))}</p>")
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{titolo}</title></head><body>{''.join(parts)}</body></html>"


_SKIP_KEYS = {"meta", "metadata", "disclaimer", "files", "file_generati"}


def _humanize(key: str) -> str:
    return key.replace("_", " ").capitalize()


def render_generic_pdf(deliverable: dict, blueprint: dict, citazioni: list[dict], pdf_path: Path) -> None:
    """Render generico per QUALSIASI output-schema: cammina il dict e impagina
    ogni sezione top-level (oggetti, liste, scalari) in modo leggibile."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, textColor="#555555")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)

    meta = deliverable.get("meta") or deliverable.get("metadata") or {}
    titolo = blueprint.get("pacchetto", {}).get("nome_commerciale") or meta.get("servizio") or "Deliverable K2-AI"
    story = [Paragraph(str(titolo), styles["Title"])]
    if meta.get("azienda"):
        story.append(Paragraph(str(meta["azienda"]), styles["Heading3"]))
    story.append(Spacer(1, 4 * mm))

    def emit(val, level=0):
        st = styles["BodyText"]
        if isinstance(val, dict):
            for k, v in val.items():
                if v in (None, "", [], {}):
                    continue
                story.append(Paragraph(f"<b>{html.escape(_humanize(str(k)))}</b>", styles["Heading4" if level else "Heading3"]))
                emit(v, level + 1)
        elif isinstance(val, list):
            for item in val[:30]:
                if isinstance(item, (dict, list)):
                    emit(item, level + 1)
                    story.append(Spacer(1, 1 * mm))
                else:
                    story.append(Paragraph("• " + html.escape(str(item)), st))
        else:
            story.append(Paragraph(html.escape(str(val)), st))

    for key, val in deliverable.items():
        if key in _SKIP_KEYS or val in (None, "", [], {}):
            continue
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(_humanize(key), styles["Heading2"]))
        emit(val, 1)

    if citazioni:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("Fonti", styles["Heading2"]))
        for c in citazioni:
            story.append(Paragraph(
                f"• <b>{html.escape(str(c.get('riferimento') or c.get('campo', '')))}</b>: "
                f"{html.escape(_fonte(c.get('fonte', '')))} — {html.escape(str(c.get('vigenza', '')))}",
                styles["BodyText"]))

    disc = deliverable.get("disclaimer") or blueprint.get("disclaimer")
    if disc:
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(str(disc), small))

    doc.build(story)


def render_pdf(deliverable: dict, blueprint: dict, citazioni: list[dict], pdf_path: Path) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem

    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, textColor="#555555")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)

    meta = deliverable.get("meta", {})
    story = [Paragraph(meta.get("servizio", "Deliverable K2-AI"), styles["Title"])]
    if meta.get("azienda"):
        story.append(Paragraph(meta["azienda"], styles["Heading3"]))
    story.append(Spacer(1, 4 * mm))

    s = deliverable.get("sintesi", {})
    story.append(Paragraph("Sintesi", styles["Heading2"]))
    story.append(Paragraph(f"Score compliance: <b>{s.get('score_compliance','')}/100</b>", styles["BodyText"]))
    story.append(Spacer(1, 3 * mm))

    for v in deliverable.get("voci", []):
        story.append(Paragraph(str(v.get("titolo", "")), styles["Heading2"]))
        story.append(Paragraph(str(v.get("contenuto", "")), styles["BodyText"]))
        story.append(Spacer(1, 3 * mm))

    if citazioni:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("Fonti", styles["Heading2"]))
        story.append(ListFlowable(
            [ListItem(Paragraph(f"<b>{c.get('riferimento') or c.get('campo','')}</b>: {_fonte(c.get('fonte',''))} — <i>{c.get('vigenza','')}</i>",
                                styles["BodyText"])) for c in citazioni],
            bulletType="bullet"))

    if deliverable.get("disclaimer"):
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(deliverable["disclaimer"], small))

    doc.build(story)
