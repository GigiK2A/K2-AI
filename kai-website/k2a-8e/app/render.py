"""Render PDF premium K2-AI — struttura consulenziale coerente per tutti i report:
copertina → metodologia → indice editoriale → executive summary → dashboard KPI →
analisi a componenti → appendice normativa verbatim → CTA finale.

Il contenuto resta quello del deliverable (per output-schema); qui si cura solo la
veste: gerarchia, componenti, leggibilità, identità visiva."""
from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from . import styling as ST

_FONTE_LABEL = {"override_locale": "Normattiva", "akn_bulk_xml": "Normattiva", "normattiva": "Normattiva"}
_SKIP_KEYS = {"meta", "metadata", "disclaimer", "files", "file_generati", "input", "allegati",
              "executive_summary", "sintesi"}


def _fonte(f) -> str:
    return _FONTE_LABEL.get(str(f), str(f or "Normattiva"))


def _humanize(key: str) -> str:
    return str(key).replace("_", " ").strip().capitalize()


_EMOJI = re.compile(r"[\U0001F000-\U0001FAFF☀-➿←-⇿⬀-⯿️�]")


def _rich(s) -> str:
    """Prosa → markup reportlab: escape, **grassetto** reale, via le emoji non
    renderizzabili. I modelli a volte scrivono markdown/emoji: qui si normalizza."""
    s = html.escape(str(s if s is not None else ""))
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s, flags=re.S)
    s = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", s)  # *corsivo*
    s = re.sub(r"^\s*[-•]\s+", "", s)  # bullet residui a inizio riga
    s = _EMOJI.sub("", s)
    return s


class _Heading(Paragraph):
    """Heading di sezione che si registra nell'indice (TOC)."""
    def __init__(self, text, style, key):
        super().__init__(text, style)
        self._toc_text = text
        self._toc_key = key


class _Doc(BaseDocTemplate):
    def __init__(self, path, cover_meta, report_name):
        self.cover_meta = cover_meta
        self.report_name = report_name
        super().__init__(str(path), pagesize=(ST.PAGE_W, ST.PAGE_H),
                         leftMargin=ST.MARGIN, rightMargin=ST.MARGIN,
                         topMargin=22 * mm, bottomMargin=22 * mm)
        cover = Frame(0, 0, ST.PAGE_W, ST.PAGE_H, id="cover",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        content = Frame(ST.MARGIN, 18 * mm, ST.CONTENT_W, ST.PAGE_H - 22 * mm - 18 * mm, id="content")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover], onPage=self._on_cover),
            PageTemplate(id="content", frames=[content], onPage=self._on_content),
        ])

    def _on_cover(self, canvas, doc):
        ST.cover_page(canvas, **self.cover_meta)

    def _on_content(self, canvas, doc):
        ST.page_header(canvas, self.report_name)
        ST.footer(canvas, doc, self.report_name)

    def afterFlowable(self, flowable):
        if isinstance(flowable, _Heading):
            self.notify("TOCEntry", (0, flowable._toc_text, self.page - 1, flowable._toc_key))
            self.canv.bookmarkPage(flowable._toc_key)


# ===================== blocchi fissi (metodologia, CTA) ==================
def _methodology(S, ambito: str, has_citations: bool = False) -> list:
    # La promessa "riferimenti normativi verbatim" si fa SOLO se ci sono citazioni
    # grounded reali (LegalBoost/FiscoBoost). Asserirla su un report di strategia
    # senza una sola citazione è un over-promise (e induce a fidarsi di fatti
    # normativi che il modello ha inventato — vedi report StrategyBoost reale).
    fonti = ("parametri di settore e — dove applicabile — riferimenti normativi riportati "
             "verbatim dalla fonte ufficiale, per garantire tracciabilità e affidabilità delle valutazioni"
             if has_citations else
             "parametri di settore, distinguendo le evidenze verificate dalle inferenze qualitative")
    txt = (
        "Questo documento è stato prodotto da K2-AI, sistema di intelligenza artificiale "
        "specializzato nell'analisi tecnica, strategica e operativa per imprese e professionisti. "
        f"L'analisi {ambito} integra i dati forniti e {fonti}.\n\n"
        "La struttura del report segue una logica consulenziale: una sintesi esecutiva leggibile anche "
        "da non tecnici, una dashboard sintetica degli indicatori chiave, l'analisi di dettaglio con "
        "criticità e opportunità, le raccomandazioni operative prioritizzate e una roadmap dei prossimi "
        "passi. Le valutazioni hanno finalità di supporto decisionale e possono essere approfondite da "
        "professionisti qualificati in relazione al contesto specifico."
    )
    out = [_Heading("Nota metodologica", S["h1"], "metodo")]
    for para in txt.split("\n\n"):
        out.append(Paragraph(html.escape(para), S["lead"]))
    out.append(Spacer(1, 4))
    out.append(ST.insight_box(
        "Il valore del report non è solo nei numeri, ma nella loro lettura prioritizzata: "
        "cosa guardare prima, dove intervenire e con quale urgenza.", "Come leggere questo documento", S))
    return out


_CTA = (
    "Documento generato da K2-AI, sistema di intelligenza artificiale specializzato nell'analisi "
    "tecnica, strategica e operativa per imprese, professionisti e organizzazioni.\n\n"
    "Il presente report è stato redatto sulla base dei dati disponibili al momento della generazione "
    "e ha finalità di supporto decisionale. Le valutazioni prodotte dall'AI vanno interpretate come "
    "analisi preliminari avanzate e possono essere integrate, validate o approfondite da professionisti "
    "qualificati in relazione al contesto specifico, agli obblighi normativi applicabili e alle decisioni "
    "operative da assumere.\n\n"
    "Per una valutazione personalizzata, aggiornamenti del report o un piano operativo dettagliato, è "
    "possibile richiedere un approfondimento specialistico tramite la piattaforma."
)


def _cta(S) -> list:
    inner = [Paragraph(f'<font name="{ST.F_BOLD}" size="9" color="{ST.hx(ST.GOLD_DK)}">'
                       f'K2-AI · ANALISI INTELLIGENTE PER LE IMPRESE</font>', S["kv"]), Spacer(1, 4)]
    for para in _CTA.split("\n\n"):
        inner.append(Paragraph(html.escape(para), S["small"]))
        inner.append(Spacer(1, 2))
    box = Table([[inner]], colWidths=[ST.CONTENT_W])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ST.WARM),
        ("BOX", (0, 0), (-1, -1), 0.7, ST.LINE),
        ("LINEABOVE", (0, 0), (-1, 0), 2, ST.GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return [Spacer(1, 10), box]


# ===================== estrattori (score/evidenze/azioni) ================
def _find_score(d):
    """Cerca ricorsivamente un punteggio 0-100 (chiave con 'score')."""
    best = None
    def walk(x, key=""):
        nonlocal best
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, k)
        elif isinstance(x, list):
            for v in x[:20]:
                walk(v, key)
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            if "score" in key.lower() and 0 <= x <= 100 and best is None:
                best = (key, int(x))
    walk(d)
    return best


def _find_text(d, *hints):
    """Prima stringa lunga sotto una chiave che contiene uno degli hint."""
    res = None
    def walk(x):
        nonlocal res
        if res:
            return
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(v, str) and len(v) > 80 and any(h in k.lower() for h in hints):
                    res = v; return
                walk(v)
        elif isinstance(x, list):
            for v in x[:20]:
                walk(v)
    walk(d)
    return res


def _collect_list(d, *hints, limit=5):
    """Raccoglie elementi (titolo/descrizione) da liste con chiave fra gli hint."""
    out = []
    def walk(x):
        if len(out) >= limit:
            return
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(v, list) and any(h in k.lower() for h in hints):
                    for it in v:
                        if len(out) >= limit:
                            break
                        if isinstance(it, dict):
                            out.append(str(it.get("titolo") or it.get("descrizione")
                                           or it.get("azione") or it.get("nome") or "").strip())
                        elif isinstance(it, str):
                            out.append(it.strip())
                walk(v)
        elif isinstance(x, list):
            for v in x[:20]:
                walk(v)
    walk(d)
    return [o for o in out if o][:limit]


def _exec_summary(deliverable, S) -> list:
    """Executive Summary visuale: gauge score + sintesi + evidenze + azioni."""
    out = [_Heading("Executive Summary", S["h1"], "exec")]
    score = _find_score(deliverable)
    summary = (_find_text(deliverable, "sintesi", "executive", "summary", "esecutiv")
               or "Sintesi dei principali risultati dell'analisi, delle criticità rilevate e delle "
                  "priorità d'azione individuate per l'azienda.")
    # riga: gauge + testo sintesi
    left = ST.Gauge(score[1], "Score") if score else Paragraph("", S["body"])
    right = Paragraph(_rich(summary[:520]), S["lead"])
    row = Table([[left, right]], colWidths=[40 * mm, ST.CONTENT_W - 40 * mm])
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, 0), 10)]))
    out += [row, Spacer(1, 6)]
    # evidenze + azioni
    evid = _collect_list(deliverable, "critic", "evidenz", "rischi", "finding", "problem")
    azioni = _collect_list(deliverable, "azion", "raccomand", "quick", "intervent", "piano")
    if evid:
        out.append(Paragraph("Evidenze principali", S["h3"]))
        for i, e in enumerate(evid, 1):
            out.append(Paragraph(f'<font name="{ST.F_BOLD}" color="{ST.hx(ST.GOLD_DK)}">{i:02d}</font>'
                                 f'&nbsp;&nbsp;{_rich(e)}', S["bullet"]))
        out.append(Spacer(1, 4))
    if azioni:
        out.append(ST.action_box(azioni, "Azioni consigliate", S))
    return out


def _kpi_dashboard(deliverable, S) -> list:
    """Dashboard sintetica: card per score, rischio, priorità (derivati)."""
    cards = []
    score = _find_score(deliverable)
    if score:
        sc = score[1]
        tone = ST.GREEN if sc >= 70 else ST.AMBER if sc >= 45 else ST.RED
        cards.append({"value": f"{sc}/100", "label": "Score generale", "tone": tone,
                      "sub": "Buono" if sc >= 70 else "Sufficiente con criticità" if sc >= 45 else "Critico"})
    # cerca rischio/priorità/stato testuali
    def find_kv(*hints):
        res = [None]
        def walk(x):
            if isinstance(x, dict):
                for k, v in x.items():
                    if isinstance(v, str) and 0 < len(v) <= 24 and any(h in k.lower() for h in hints) and not res[0]:
                        res[0] = (k, v)
                    walk(v)
            elif isinstance(x, list):
                for v in x[:20]:
                    walk(v)
        walk(deliverable)
        return res[0]
    for hints, lbl in [(("rischio", "risk"), "Livello di rischio"),
                       (("priorit",), "Priorità"),
                       (("urgenz",), "Urgenza"),
                       (("stato", "status"), "Stato"),
                       (("impatto",), "Impatto")]:
        kv = find_kv(*hints)
        if kv and len(cards) < 6:
            val = kv[1]
            tone = ST.SEMAFORO.get(val.lower(), ST.NEUTRAL)
            cards.append({"value": val.capitalize()[:14], "label": lbl, "tone": tone})
    if len(cards) < 2:
        return []
    return [_Heading("Dashboard", S["h1"], "dashboard"),
            ST.kpi_dashboard(cards, S), Spacer(1, 6)]


# ===================== appendice normativa + disclaimer ==================
def _fonti(citazioni, S):
    out = [Spacer(1, 4), _Heading("Fonti normative", S["h2"], "fonti")]
    for c in citazioni:
        out.append(Paragraph(
            f'• <b>{html.escape(str(c.get("riferimento") or c.get("campo", "")))}</b> — '
            f'{html.escape(_fonte(c.get("fonte", "")))}'
            + (f' · <i>{html.escape(str(c.get("vigenza", "")))}</i>' if c.get("vigenza") else ""),
            S["bullet"]))
    return out


def _testi_normativi(citazioni, S):
    norm = [c for c in citazioni if c.get("testo")]
    if not norm:
        return []
    out = [Spacer(1, 6), _Heading("Testi normativi (verbatim)", S["h2"], "verbatim")]
    for c in norm:
        t = str(c.get("testo", ""))
        lines = t.split("\n")
        head = lines[0].lstrip("# ").strip() if lines else (c.get("riferimento") or "")
        body = ("\n".join(lines[1:]).strip() or t).replace("**", "")
        if len(body) > 2200:
            body = body[:2200].rstrip() + " […]"
        out.append(Paragraph(f'<b>{html.escape(head)}</b>', S["body"]))
        out.append(Paragraph(html.escape(body).replace("\n", "<br/>"), S["small"]))
        out.append(Spacer(1, 4))
    out.append(Paragraph("<i>Testi riportati verbatim dalla fonte normativa (snapshot di grounding "
                         "K2-AI), non rielaborati né riassunti dal modello.</i>", S["note"]))
    return out


# ===================== build (scaffolding premium) =======================
def _cover_meta(deliverable, blueprint, default_titolo, sottotitolo, valore):
    meta = deliverable.get("meta") or deliverable.get("metadata") or {}
    modulo = blueprint.get("pacchetto", {}).get("nome_commerciale") or default_titolo
    azienda = str(meta.get("azienda") or meta.get("cliente") or meta.get("committente") or "")
    data_doc = str(meta.get("data") or meta.get("generated_at") or date.today().isoformat())
    periodo = str(meta.get("periodo") or meta.get("mese") or meta.get("anno") or data_doc[:7])
    versione = str(meta.get("versione") or meta.get("version") or "1.0").replace("v", "")
    codice = str(meta.get("codice") or meta.get("code") or meta.get("id")
                 or f"K2AI-{re.sub(r'[^A-Z0-9]', '', modulo.upper())[:10]}-{data_doc.replace('-', '')[:8]}")
    return {
        "modulo": modulo, "titolo": modulo.replace("Boost", "").strip() or modulo,
        "sottotitolo": sottotitolo, "azienda": azienda, "periodo": periodo,
        "versione": versione or "1.0", "codice": codice, "categoria": "Diagnosi professionale",
        "valore": valore, "data": data_doc,
    }, modulo


def _preliminary_banner(S):
    """Avviso in testa al documento quando è un REPORT PRELIMINARE (dati parziali):
    l'utente deve capire subito che alcune voci sono stime da confermare."""
    txt = ("<b>REPORT PRELIMINARE</b> — basato sui dati finora disponibili. Le voci "
           "mancanti sono trattate come stime esplicite («valori indicativi: ipotesi da "
           "confermare»). Completa i dati richiesti per la versione definitiva, senza ripagare.")
    box = Table([[Paragraph(txt, S["small"])]], colWidths=[ST.CONTENT_W])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ST.WARM),
                             ("BOX", (0, 0), (-1, -1), 1, ST.LINE),
                             ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                             ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return [box, Spacer(1, 8)]


def _build(pdf_path: Path, cover_meta, report_name, body_blocks, deliverable, ambito,
           has_citations: bool = False, preliminare: bool = False):
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    S = ST.styles()
    doc = _Doc(pdf_path, cover_meta, report_name)
    toc = TableOfContents()
    toc.levelStyles = [S["toc"]]
    story = [NextPageTemplate("content"), PageBreak()]
    if preliminare:
        story += _preliminary_banner(S)
    story += _methodology(S, ambito, has_citations)
    story += [PageBreak(), _Heading("Indice del report", S["h1"], "indice"), Spacer(1, 4), toc, PageBreak()]
    story += _exec_summary(deliverable, S)
    story += _kpi_dashboard(deliverable, S)
    story += body_blocks
    story += _cta(S)
    doc.multiBuild(story)


def _disclaimer_inline(deliverable, blueprint, S):
    disc = deliverable.get("disclaimer") or blueprint.get("disclaimer")
    if not disc:
        return []
    box = Table([[Paragraph(html.escape(str(disc)), S["small"])]], colWidths=[ST.CONTENT_W])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ST.WARM),
                             ("BOX", (0, 0), (-1, -1), 0.5, ST.LINE),
                             ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                             ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return [Spacer(1, 6), box]


# ========================= LegalBoost (dedicato) =========================
def render_pdf(deliverable: dict, blueprint: dict, citazioni: list, pdf_path: Path,
               preliminare: bool = False) -> None:
    S = ST.styles()
    cover_meta, report_name = _cover_meta(deliverable, blueprint, "LegalBoost",
                                          "Diagnosi legale e compliance",
                                          "Quadro dei rischi legali e priorità d'azione per la tua impresa.")
    sint = deliverable.get("sintesi", {})
    body = [_Heading("01 · Sintesi e mappa rischi", S["h1"], "legal-1")]
    if sint.get("mappa_rischi"):
        body += [Spacer(1, 4), ST.heatmap(sint["mappa_rischi"], S), Spacer(1, 6)]

    n = 2
    for v in deliverable.get("voci", []):
        body.append(_Heading(f"{n:02d} · {str(v.get('titolo', ''))}", S["h1"], f"legal-{n}")); n += 1
        if v.get("contenuto"):
            body.append(Paragraph(_rich(str(v["contenuto"])), S["body"]))
        if v.get("rischi"):
            body.append(Paragraph("Rischi rilevati", S["h3"]))
            for r in v["rischi"]:
                extra = "consulenza legale raccomandata" if r.get("serve_avvocato") else ""
                body.append(ST.risk_card(str(r.get("descrizione", "")), r.get("gravita", "media"), S, extra))
                body.append(Spacer(1, 2))
        if v.get("azioni"):
            body.append(Spacer(1, 2)); body.append(ST.action_box(list(v["azioni"]), "Azioni consigliate", S))
        body.append(Spacer(1, 4))

    if deliverable.get("piano_azione"):
        body.append(_Heading(f"{n:02d} · Piano d'azione", S["h1"], f"legal-{n}"))
        rows = [[str(p.get("priorita", "")), str(p.get("azione", "")),
                 "Avvocato" if p.get("handoff_avvocato") else "—"] for p in deliverable["piano_azione"]]
        body.append(ST.premium_table(["#", "Azione", "Handoff"], rows, S,
                                      widths=[12 * mm, ST.CONTENT_W - 42 * mm, 30 * mm]))
    if citazioni:
        body += _fonti(citazioni, S) + _testi_normativi(citazioni, S)
    body += _disclaimer_inline(deliverable, blueprint, S)
    _build(pdf_path, cover_meta, report_name, body, deliverable, "legale-compliance",
           has_citations=bool(citazioni), preliminare=preliminare)


# ========================= Generico (a componenti) =======================
def _is_list_of_dicts(v):
    return isinstance(v, list) and v and all(isinstance(x, dict) for x in v)


def _has(items, *keys):
    return items and all(any(k in it for k in keys) for it in items[:2])


def render_generic_pdf(deliverable: dict, blueprint: dict, citazioni: list, pdf_path: Path,
                       preliminare: bool = False) -> None:
    S = ST.styles()
    cover_meta, report_name = _cover_meta(deliverable, blueprint, "Deliverable K2-AI",
                                          "Diagnosi professionale",
                                          "Analisi tecnica e operativa con priorità d'intervento.")
    body = []

    # coordinate da NON stampare quando la mappa è resa come quadrante (no falsa
    # precisione "0,75" — C3 del grounding contract): si tiene il razionale, non il numero.
    _COORD_KEYS = {"coordinata_x", "coordinata_y", "x", "y", "ampiezza", "segmentazione",
                   "posizione_azienda", "posizione_competitor"}

    def render_value(v, level=0, skip_keys=()):
        if _is_list_of_dicts(v) and _has(v, "semaforo"):
            body.append(ST.heatmap(v, S)); body.append(Spacer(1, 4)); return
        if _is_list_of_dicts(v) and _has(v, "valore", "benchmark"):
            body.append(ST.kpi_table(v, S)); body.append(Spacer(1, 4)); return
        if _is_list_of_dicts(v) and _has(v, "descrizione", "gravita"):
            for it in v:
                extra = " · ".join(str(it.get(k)) for k in ("norma_rif", "tipo") if it.get(k))
                body.append(ST.risk_card(str(it.get("descrizione", "")), it.get("gravita", "media"), S, extra))
                body.append(Spacer(1, 2))
            return
        # liste con punteggio a rubrica (es. forze di Porter) → barre, non testo
        if _is_list_of_dicts(v) and _has(v, "scoring"):
            body.append(ST.score_bars(v, S)); body.append(Spacer(1, 4)); return
        # liste di azioni/raccomandazioni stringa → action box
        if isinstance(v, list) and v and all(isinstance(x, str) for x in v) and len(v) <= 12:
            body.append(ST.action_box(v, "Punti chiave", S)); body.append(Spacer(1, 3)); return
        if isinstance(v, dict):
            # MAPPA DI POSIZIONAMENTO → quadrante 2x2 a bande (grafico, non testo).
            q = ST.quadrant_map(v)
            if q is not None:
                body.append(Spacer(1, 4)); body.append(q); body.append(Spacer(1, 6))
                # razionali (perché ognuno sta lì) SENZA i decimali inventati
                for label, obj in (("La tua azienda", v.get("posizione_azienda")),):
                    if isinstance(obj, dict) and obj.get("razionale"):
                        body.append(Paragraph(f"<b>{label}:</b> {_rich(str(obj['razionale']))}", S["bullet"]))
                for cdict in (v.get("posizione_competitor") or []):
                    if isinstance(cdict, dict) and cdict.get("razionale"):
                        nome = cdict.get("nome") or "Competitor"
                        body.append(Paragraph(f"<b>{html.escape(str(nome))}:</b> {_rich(str(cdict['razionale']))}", S["bullet"]))
                skip_keys = set(skip_keys) | _COORD_KEYS
            for k, vv in v.items():
                if vv in (None, "", [], {}) or k in skip_keys:
                    continue
                if isinstance(vv, (dict, list)):
                    body.append(Paragraph(html.escape(_humanize(k)), S["h3"] if level else S["h2"]))
                    render_value(vv, level + 1, skip_keys)
                else:
                    body.append(Paragraph(f"<b>{html.escape(_humanize(k))}:</b> {_rich(str(vv))}", S["bullet"]))
        elif isinstance(v, list):
            for item in v[:40]:
                if isinstance(item, dict):
                    title = item.get("titolo") or item.get("nome") or item.get("area") or ""
                    if title:
                        body.append(Paragraph(f"<b>{html.escape(str(title))}</b>", S["h3"]))
                    if item.get("contenuto"):
                        body.append(Paragraph(_rich(str(item["contenuto"])), S["body"]))
                    for sub in ("rischi", "rischi_opportunita", "azioni", "norme_citate", "fonti", "findings"):
                        if item.get(sub):
                            render_value(item[sub], level + 1, skip_keys)
                    for kk, vv in item.items():
                        if kk in ("titolo", "nome", "area", "contenuto", "rischi", "rischi_opportunita",
                                  "azioni", "norme_citate", "fonti", "findings") or vv in (None, "", [], {}) or kk in skip_keys:
                            continue
                        if isinstance(vv, (dict, list)):
                            render_value(vv, level + 1, skip_keys)
                        else:
                            body.append(Paragraph(f"<b>{html.escape(_humanize(kk))}:</b> {_rich(str(vv))}", S["bullet"]))
                    body.append(Spacer(1, 2))
                elif isinstance(item, str):
                    body.append(Paragraph(f'<font color="{ST.hx(ST.GOLD_DK)}">•</font> {_rich(item)}', S["bullet"]))
        else:
            body.append(Paragraph(html.escape(str(v)), S["body"]))

    # sezioni top-level → divisori numerati (salta exec/score già nell'header)
    n = 1
    for key, val in deliverable.items():
        if key in _SKIP_KEYS or val in (None, "", [], {}):
            continue
        # score scalari già mostrati nella dashboard → salta se top-level int 'score'
        if isinstance(val, (int, float)) and "score" in key.lower():
            continue
        body.append(_Heading(f"{n:02d} · {_humanize(key)}", S["h1"], f"section-{n}")); n += 1
        body.append(Spacer(1, 2))
        render_value(val, 1)
        body.append(Spacer(1, 4))

    if citazioni:
        body += _fonti(citazioni, S) + _testi_normativi(citazioni, S)
    body += _disclaimer_inline(deliverable, blueprint, S)
    _build(pdf_path, cover_meta, report_name, body, deliverable, "professionale",
           has_citations=bool(citazioni), preliminare=preliminare)


def render_html(deliverable: dict, blueprint: dict, citazioni: list) -> str:
    import json
    return "<pre>" + html.escape(json.dumps(deliverable, ensure_ascii=False, indent=2)) + "</pre>"
