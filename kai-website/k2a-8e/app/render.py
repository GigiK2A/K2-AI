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


def _doc_titolo(deliverable: dict, blueprint: dict) -> tuple[str, str]:
    meta = deliverable.get("meta") or deliverable.get("metadata") or {}
    titolo = (blueprint.get("pacchetto", {}).get("nome_commerciale")
              or meta.get("servizio") or "Deliverable K2-AI")
    azienda = str(meta.get("azienda") or meta.get("cliente") or "")
    return str(titolo), azienda


def _build_pdf(pdf_path: Path, titolo: str, azienda: str, sottotitolo: str, story: list) -> None:
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Spacer
    from reportlab.lib.units import mm
    from .styling import MARGIN, PAGE_W, PAGE_H, cover_band, footer

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    frame = Frame(MARGIN, 18 * mm, PAGE_W - 2 * MARGIN, PAGE_H - 18 * mm - 22 * mm, id="body")

    def on_first(canvas, doc):
        cover_band(canvas, titolo, azienda, sottotitolo)
        footer(canvas, doc)

    doc = BaseDocTemplate(str(pdf_path), pagesize=(PAGE_W, PAGE_H),
                          leftMargin=MARGIN, rightMargin=MARGIN, topMargin=18 * mm, bottomMargin=22 * mm)
    doc.addPageTemplates([
        PageTemplate(id="first", frames=[frame], onPage=on_first),
        PageTemplate(id="later", frames=[frame], onPage=footer),
    ])
    # prima pagina: spazio per la banda copertina (46mm dall'alto)
    story = [Spacer(1, 32 * mm)] + story
    doc.build(story)


def _fonti_block(citazioni: list[dict], S: dict) -> list:
    from reportlab.platypus import Paragraph, Spacer
    from .styling import semaforo_dot  # noqa
    out = [Spacer(1, 4), Paragraph("Fonti normative", S["h2"])]
    for c in citazioni:
        out.append(Paragraph(
            f"• <b>{html.escape(str(c.get('riferimento') or c.get('campo', '')))}</b> — "
            f"{html.escape(_fonte(c.get('fonte', '')))}"
            + (f" · <i>{html.escape(str(c.get('vigenza','')))}</i>" if c.get('vigenza') else ""),
            S["bullet"]))
    return out


def render_pdf(deliverable: dict, blueprint: dict, citazioni: list[dict], pdf_path: Path) -> None:
    """Render stilizzato per LegalBoost (voci-shape)."""
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import mm
    from .styling import styles, ScoreBadge, mappa_table, SEMAFORO, MUTED, PAGE_W, MARGIN

    S = styles()
    titolo, azienda = _doc_titolo(deliverable, blueprint)
    sint = deliverable.get("sintesi", {})
    score = sint.get("score_compliance")
    story = []

    # Sintesi: badge score + mappa rischi
    head = [[ScoreBadge(score, "Compliance"),
             Paragraph("<b>Sintesi esecutiva</b><br/>Quadro dei rischi e priorità d'azione per l'azienda.", S["body"])]]
    t = Table(head, colWidths=[30 * mm, PAGE_W - 2 * MARGIN - 30 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (1, 0), (1, 0), 8)]))
    story += [t, Spacer(1, 4)]
    if sint.get("mappa_rischi"):
        story += [mappa_table(sint["mappa_rischi"], S), Spacer(1, 6)]

    # Voci
    for v in deliverable.get("voci", []):
        story.append(Paragraph(html.escape(str(v.get("titolo", ""))), S["h1"]))
        if v.get("contenuto"):
            story.append(Paragraph(html.escape(str(v["contenuto"])), S["body"]))
        for r in v.get("rischi", []):
            col = "#" + SEMAFORO.get(str(r.get("gravita", "media")).lower(), MUTED).hexval()[2:]
            av = " · <i>consulenza raccomandata</i>" if r.get("serve_avvocato") else ""
            story.append(Paragraph(
                f'<font color="{col}">▸</font> <b>{html.escape(str(r.get("gravita","")).capitalize())}</b>: '
                f'{html.escape(str(r.get("descrizione","")))}{av}', S["bullet"]))
        for a in v.get("azioni", []):
            story.append(Paragraph(f"✓ {html.escape(str(a))}", S["bullet"]))
        story.append(Spacer(1, 3))

    # Piano azione
    if deliverable.get("piano_azione"):
        story.append(Paragraph("Piano d'azione", S["h1"]))
        for p in deliverable["piano_azione"]:
            hand = " · <i>handoff avvocato</i>" if p.get("handoff_avvocato") else ""
            story.append(Paragraph(f"<b>{p.get('priorita','')}.</b> {html.escape(str(p.get('azione','')))}{hand}", S["bullet"]))

    if citazioni:
        story += _fonti_block(citazioni, S)
    if deliverable.get("disclaimer"):
        story += [Spacer(1, 6), Paragraph(html.escape(str(deliverable["disclaimer"])), S["small"])]

    _build_pdf(pdf_path, titolo, azienda, "Diagnosi legale-compliance · K2-AI", story)


def render_generic_pdf(deliverable: dict, blueprint: dict, citazioni: list[dict], pdf_path: Path) -> None:
    """Render stilizzato generico per QUALSIASI output-schema."""
    from reportlab.platypus import Paragraph, Spacer
    from .styling import styles, ScoreBadge, semaforo_dot, MUTED

    S = styles()
    titolo, azienda = _doc_titolo(deliverable, blueprint)
    story = []

    def is_semaforo_list(v):
        return isinstance(v, list) and v and isinstance(v[0], dict) and "semaforo" in v[0]

    def emit(val, level=0):
        if isinstance(val, dict):
            for k, v in val.items():
                if v in (None, "", [], {}):
                    continue
                if isinstance(v, (dict, list)):
                    story.append(Paragraph(html.escape(_humanize(str(k))), S["h3"] if level else S["h2"]))
                    emit(v, level + 1)
                else:
                    story.append(Paragraph(f"<b>{html.escape(_humanize(str(k)))}:</b> {html.escape(str(v))}", S["bullet"]))
        elif is_semaforo_list(val):
            for it in val:
                area = it.get("area") or it.get("nome") or it.get("titolo") or ""
                extra = " ".join(f"{html.escape(_humanize(kk))}: {html.escape(str(vv))}"
                                 for kk, vv in it.items() if kk not in ("area", "nome", "titolo", "semaforo") and vv not in (None, "", [], {}))
                story.append(Paragraph(
                    f'{semaforo_dot(it.get("semaforo"))} <b>{html.escape(str(area))}</b>'
                    + (f' — {extra}' if extra else ''), S["bullet"]))
        elif isinstance(val, list):
            for item in val[:40]:
                if isinstance(item, dict):
                    title = item.get("titolo") or item.get("nome") or item.get("descrizione") or item.get("area") or ""
                    if title:
                        story.append(Paragraph(f"<b>{html.escape(str(title))}</b>", S["h3"]))
                    for kk, vv in item.items():
                        if kk in ("titolo", "nome") or vv in (None, "", [], {}):
                            continue
                        if isinstance(vv, (dict, list)):
                            emit(vv, level + 1)
                        else:
                            story.append(Paragraph(f"<b>{html.escape(_humanize(kk))}:</b> {html.escape(str(vv))}", S["bullet"]))
                    story.append(Spacer(1, 2))
                else:
                    story.append(Paragraph("• " + html.escape(str(item)), S["bullet"]))
        else:
            story.append(Paragraph(html.escape(str(val)), S["body"]))

    # Score in testa se presente in sintesi/executive_summary
    for sec in ("sintesi", "executive_summary"):
        block = deliverable.get(sec)
        if isinstance(block, dict):
            for sk in ("score_fiscale", "score_compliance", "score_globale", "score"):
                if isinstance(block.get(sk), int):
                    story.append(ScoreBadge(block[sk], sk.replace("score_", "").replace("score", "Score")))
                    story.append(Spacer(1, 3))
                    break

    for key, val in deliverable.items():
        if key in _SKIP_KEYS or val in (None, "", [], {}):
            continue
        story.append(Paragraph(_humanize(key), S["h1"]))
        emit(val, 1)
        story.append(Spacer(1, 2))

    if citazioni:
        story += _fonti_block(citazioni, S)
    disc = deliverable.get("disclaimer") or blueprint.get("disclaimer")
    if disc:
        from reportlab.platypus import Spacer as _Sp
        story += [_Sp(1, 6), Paragraph(html.escape(str(disc)), S["small"])]

    _build_pdf(pdf_path, titolo, azienda, "Diagnosi professionale · K2-AI", story)
