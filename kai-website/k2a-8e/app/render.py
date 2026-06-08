"""Render PDF premium K2-AI: copertina full-page, indice, header/footer, e
rendering a componenti (gauge, heatmap, card rischi, tabelle KPI)."""
from __future__ import annotations

import html
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from . import styling as ST

_FONTE_LABEL = {"override_locale": "Normattiva", "akn_bulk_xml": "Normattiva", "normattiva": "Normattiva"}
_SKIP_KEYS = {"meta", "metadata", "disclaimer", "files", "file_generati"}


def _fonte(f) -> str:
    return _FONTE_LABEL.get(str(f), str(f or "Normattiva"))


def _humanize(key: str) -> str:
    return str(key).replace("_", " ").capitalize()


class _Heading(Paragraph):
    """Heading che si registra nell'indice (TOC)."""
    def __init__(self, text, style, key):
        super().__init__(text, style)
        self._toc_text = text
        self._toc_key = key


class _Doc(BaseDocTemplate):
    """Doc con copertina (pag.1), header+footer sulle interne, TOC."""
    def __init__(self, path, titolo, azienda, sottotitolo, report_name):
        self.titolo, self.azienda, self.sottotitolo = titolo, azienda, sottotitolo
        self.report_name = report_name
        super().__init__(str(path), pagesize=(ST.PAGE_W, ST.PAGE_H),
                         leftMargin=ST.MARGIN, rightMargin=ST.MARGIN,
                         topMargin=22 * mm, bottomMargin=22 * mm)
        cover_frame = Frame(0, 0, ST.PAGE_W, ST.PAGE_H, id="cover",
                            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        content_frame = Frame(ST.MARGIN, 18 * mm, ST.CONTENT_W, ST.PAGE_H - 22 * mm - 18 * mm, id="content")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover_frame], onPage=self._on_cover),
            PageTemplate(id="content", frames=[content_frame], onPage=self._on_content),
        ])

    def _on_cover(self, canvas, doc):
        from datetime import date
        ST.cover_page(canvas, self.titolo, self.azienda, self.sottotitolo, "2026")

    def _on_content(self, canvas, doc):
        ST.page_header(canvas, self.report_name)
        ST.footer(canvas, doc)

    def afterFlowable(self, flowable):
        if isinstance(flowable, _Heading):
            self.notify("TOCEntry", (0, flowable._toc_text, self.page - 1, flowable._toc_key))
            self.canv.bookmarkPage(flowable._toc_key)


def _build(pdf_path: Path, titolo, azienda, sottotitolo, report_name, content: list):
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = _Doc(pdf_path, titolo, azienda, sottotitolo, report_name)

    from reportlab.platypus import NextPageTemplate
    toc = TableOfContents()
    toc.levelStyles = [ST.styles()["toc"]]
    # pag.1 = copertina (onPage) → switch a 'content' → indice → contenuto
    story = [NextPageTemplate("content"), PageBreak(),
             Paragraph("Indice", ST.styles()["h1"]), Spacer(1, 3), toc, PageBreak()]
    story += content
    doc.multiBuild(story)


def _fonti(citazioni, S):
    out = [Spacer(1, 4), _Heading("Fonti normative", S["h2"], "fonti")]
    for c in citazioni:
        out.append(Paragraph(
            f'• <b>{html.escape(str(c.get("riferimento") or c.get("campo", "")))}</b> — '
            f'{html.escape(_fonte(c.get("fonte", "")))}'
            + (f' · <i>{html.escape(str(c.get("vigenza","")))}</i>' if c.get("vigenza") else ""),
            S["bullet"]))
    return out


def _disclaimer(deliverable, blueprint, S):
    disc = deliverable.get("disclaimer") or blueprint.get("disclaimer")
    if not disc:
        return []
    box = Table([[Paragraph(html.escape(str(disc)), S["small"])]], colWidths=[ST.CONTENT_W])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ST.LIGHT),
                             ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                             ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return [Spacer(1, 8), box]


# ========================= LegalBoost (dedicato) =========================
def render_pdf(deliverable: dict, blueprint: dict, citazioni: list, pdf_path: Path) -> None:
    S = ST.styles()
    titolo = (blueprint.get("pacchetto", {}).get("nome_commerciale") or "LegalBoost")
    azienda = str((deliverable.get("meta") or {}).get("azienda") or "")
    sint = deliverable.get("sintesi", {})
    story = []

    # Executive: gauge + frase
    head = [[ST.Gauge(sint.get("score_compliance"), "Compliance"),
             Paragraph("<b>Sintesi esecutiva</b><br/><br/>Quadro dei principali rischi legali-compliance "
                       "e priorità d'azione per l'azienda. Il punteggio sintetizza il livello di conformità "
                       "complessivo rilevato.", S["lead"])]]
    t = Table(head, colWidths=[36 * mm, ST.CONTENT_W - 36 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, 0), 10)]))
    story += [_Heading("Sintesi e mappa rischi", S["h1"], "sintesi"), t, Spacer(1, 5)]
    if sint.get("mappa_rischi"):
        story += [ST.heatmap(sint["mappa_rischi"], S), Spacer(1, 6)]

    for v in deliverable.get("voci", []):
        story.append(_Heading(html.escape(str(v.get("titolo", ""))), S["h1"], f"v_{v.get('id','')}"))
        if v.get("contenuto"):
            story.append(Paragraph(html.escape(str(v["contenuto"])), S["body"]))
        if v.get("rischi"):
            story.append(Paragraph("Rischi rilevati", S["h3"]))
            for r in v["rischi"]:
                extra = "consulenza legale raccomandata" if r.get("serve_avvocato") else ""
                story.append(ST.risk_card(str(r.get("descrizione", "")), r.get("gravita", "media"), S, extra))
                story.append(Spacer(1, 2))
        if v.get("azioni"):
            story.append(Paragraph("Azioni consigliate", S["h3"]))
            for a in v["azioni"]:
                story.append(Paragraph(f'<font color="{ST.hx(ST.ACCENT)}">✓</font> {html.escape(str(a))}', S["bullet"]))
        story.append(Spacer(1, 4))

    if deliverable.get("piano_azione"):
        story.append(_Heading("Piano d'azione", S["h1"], "piano"))
        rows = [[Paragraph("<b>#</b>", S["kv"]), Paragraph("<b>Azione</b>", S["kv"]), Paragraph("<b>Handoff</b>", S["kv"])]]
        for p in deliverable["piano_azione"]:
            rows.append([Paragraph(str(p.get("priorita", "")), S["body"]),
                         Paragraph(html.escape(str(p.get("azione", ""))), S["body"]),
                         Paragraph("Avvocato" if p.get("handoff_avvocato") else "—", S["body"])])
        pt = Table(rows, colWidths=[10 * mm, ST.CONTENT_W - 40 * mm, 30 * mm])
        pt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), ST.LIGHT),
                                ("LINEBELOW", (0, 0), (-1, 0), 0.6, ST.ACCENT),
                                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ST.CARDBG]),
                                ("LINEBELOW", (0, 1), (-1, -1), 0.3, ST.LINE),
                                ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                                ("LEFTPADDING", (0, 0), (-1, -1), 6), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(pt)

    if citazioni:
        story += _fonti(citazioni, S)
    story += _disclaimer(deliverable, blueprint, S)
    _build(pdf_path, titolo, azienda, "Diagnosi legale-compliance", titolo, story)


# ========================= Generico (a componenti) =======================
def _is_list_of_dicts(v):
    return isinstance(v, list) and v and all(isinstance(x, dict) for x in v)


def _has(items, *keys):
    return items and all(any(k in it for k in keys) for it in items[:2])


def render_generic_pdf(deliverable: dict, blueprint: dict, citazioni: list, pdf_path: Path) -> None:
    S = ST.styles()
    titolo = (blueprint.get("pacchetto", {}).get("nome_commerciale")
              or (deliverable.get("meta") or deliverable.get("metadata") or {}).get("servizio") or "Deliverable K2-AI")
    azienda = str((deliverable.get("meta") or deliverable.get("metadata") or {}).get("azienda")
                  or (deliverable.get("meta") or deliverable.get("metadata") or {}).get("cliente") or "")
    story = []

    # Score in testa (gauge) se presente
    for sec in ("sintesi", "executive_summary"):
        b = deliverable.get(sec)
        if isinstance(b, dict):
            for sk in ("score_fiscale", "score_compliance", "score_globale", "score"):
                if isinstance(b.get(sk), int):
                    story += [ST.Gauge(b[sk], sk.replace("score_", "").replace("score", "Score")), Spacer(1, 4)]
                    break

    def render_value(v, level=0):
        # lista di aree con semaforo → heatmap
        if _is_list_of_dicts(v) and _has(v, "semaforo"):
            story.append(ST.heatmap(v, S)); story.append(Spacer(1, 4)); return
        # lista KPI/indici → tabella
        if _is_list_of_dicts(v) and _has(v, "valore", "benchmark"):
            story.append(ST.kpi_table(v, S)); story.append(Spacer(1, 4)); return
        # lista rischi → card
        if _is_list_of_dicts(v) and _has(v, "descrizione", "gravita"):
            for it in v:
                tipo = it.get("tipo", "")
                extra = " ".join(str(it.get(k)) for k in ("norma_rif", "tipo") if it.get(k))
                story.append(ST.risk_card(str(it.get("descrizione", "")), it.get("gravita", "media"), S, extra))
                story.append(Spacer(1, 2))
            return
        if isinstance(v, dict):
            for k, vv in v.items():
                if vv in (None, "", [], {}):
                    continue
                if isinstance(vv, (dict, list)):
                    story.append(Paragraph(html.escape(_humanize(k)), S["h3"] if level else S["h2"]))
                    render_value(vv, level + 1)
                else:
                    story.append(Paragraph(f"<b>{html.escape(_humanize(k))}:</b> {html.escape(str(vv))}", S["bullet"]))
        elif isinstance(v, list):
            for item in v[:40]:
                if isinstance(item, dict):
                    title = item.get("titolo") or item.get("nome") or item.get("area") or ""
                    if title:
                        story.append(Paragraph(f"<b>{html.escape(str(title))}</b>", S["h3"]))
                    if item.get("contenuto"):
                        story.append(Paragraph(html.escape(str(item["contenuto"])), S["body"]))
                    # sub-liste note (rischi/azioni)
                    for sub in ("rischi", "rischi_opportunita", "azioni", "norme_citate", "fonti"):
                        if item.get(sub):
                            render_value(item[sub], level + 1)
                    for kk, vv in item.items():
                        if kk in ("titolo", "nome", "area", "contenuto", "rischi", "rischi_opportunita",
                                  "azioni", "norme_citate", "fonti") or vv in (None, "", [], {}):
                            continue
                        if isinstance(vv, (dict, list)):
                            render_value(vv, level + 1)
                        else:
                            story.append(Paragraph(f"<b>{html.escape(_humanize(kk))}:</b> {html.escape(str(vv))}", S["bullet"]))
                    story.append(Spacer(1, 2))
                elif isinstance(item, str):
                    story.append(Paragraph(f'<font color="{ST.hx(ST.ACCENT)}">•</font> {html.escape(item)}', S["bullet"]))
        else:
            story.append(Paragraph(html.escape(str(v)), S["body"]))

    for key, val in deliverable.items():
        if key in _SKIP_KEYS or val in (None, "", [], {}):
            continue
        story.append(_Heading(_humanize(key), S["h1"], f"s_{key}"))
        render_value(val, 1)
        story.append(Spacer(1, 3))

    if citazioni:
        story += _fonti(citazioni, S)
    story += _disclaimer(deliverable, blueprint, S)
    _build(pdf_path, titolo, azienda, "Diagnosi professionale", titolo, story)


# render HTML semplice (debug)
def render_html(deliverable: dict, blueprint: dict, citazioni: list) -> str:
    import json
    return "<pre>" + html.escape(json.dumps(deliverable, ensure_ascii=False, indent=2)) + "</pre>"
