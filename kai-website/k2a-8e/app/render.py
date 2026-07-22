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
from . import normalize as NORM

_FONTE_LABEL = {"override_locale": "Normattiva", "akn_bulk_xml": "Normattiva", "normattiva": "Normattiva",
                "eur_lex": "EUR-Lex (norma UE — riferimento, testo non nel corpus)",
                "codice_noto": "codice/testo unico noto (riferimento — verificare il testo vigente)"}
_SKIP_KEYS = {"meta", "metadata", "disclaimer", "files", "file_generati", "input", "allegati",
              "executive_summary", "sintesi", "report_ops",
              "consulenza_operativa"}   # resa da _consulting_blocks, non dal loop generico


def _fonte(f) -> str:
    return _FONTE_LABEL.get(str(f), str(f or "Normattiva"))


def _humanize(key: str) -> str:
    return str(key).replace("_", " ").strip().capitalize()


_ND_TOKENS = {"n/d", "nd", "n.d.", "n.d", "non disponibile", "na", "n/a", "none", "null", "-", "—"}


def _scalar_str(v) -> str:
    """Scalare → testo da stampare: bool in Sì/No (mai 'True' raw in un report pagato),
    numeri in formato italiano (migliaia col punto, decimali con virgola). I placeholder
    'N/D' non compaiono MAI nel report (#6 review): diventano 'Parametro da definire'
    (personalizzabile — l'Excel lo espone come cella editabile)."""
    v = NORM.unwrap_value(v)   # sballa {type,$value}/{value}/JSON-stringato prima di stampare
    if isinstance(v, (dict, list)):
        return NORM.to_text(v)   # mai stampare un dict/list grezzo come str(v)
    if v is None or (isinstance(v, str) and v.strip().lower() in _ND_TOKENS):
        return "Parametro da definire"
    if isinstance(v, bool):
        return "Sì" if v else "No"
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, int) and 1900 <= v <= 2100:
        return str(v)                     # anno: mai '2.024'
    if isinstance(v, int) and abs(v) >= 1000:
        return f"{v:,}".replace(",", ".")
    if isinstance(v, float):
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(v)


_EMOJI = re.compile(r"[\U0001F000-\U0001FAFF☀-➿←-⇿⬀-⯿️�]")


_fix_spacing = ST.fix_spacing  # normalizzatore punteggiatura condiviso (def in styling.py)


def _rich(s) -> str:
    """Prosa → markup reportlab: escape, **grassetto** reale, via le emoji non
    renderizzabili. I modelli a volte scrivono markdown/emoji: qui si normalizza."""
    s = NORM.unwrap_value(s)                 # sballa involucri {type,$value}/{value}/JSON
    if isinstance(s, (dict, list)):
        s = NORM.to_text(s)                  # mai far arrivare un dict a str()
    s = _fix_spacing(str(s if s is not None else ""))
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s, flags=re.S)
    s = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", s)  # *corsivo*
    s = re.sub(r"^\s*[-•]\s+", "", s)  # bullet residui a inizio riga
    # #6 review: 'N/D' non compare mai in prosa — diventa un campo dichiarato da definire.
    s = re.sub(r"\bN/?D\b\.?", "da definire", s)
    s = _strip_akn(s)
    s = _EMOJI.sub("", s)
    return s


def _strip_akn(s: str) -> str:
    """Rimuove il markup Akoma Ntoso/Normattiva trapelato dal testo di legge: ((171)) =
    ancora di nota (rumore → via); ((testo)) = testo modificato da norma successiva →
    tieni il testo, togli i doppi-tondi editoriali (non sono legge; sporcano il PDF,
    visto su FiscoBoost nella sezione «Testi normativi verbatim»)."""
    s = re.sub(r"\(\(\s*\d+\s*\)\)", "", s)       # ancore di nota ((171)), ((237))
    s = re.sub(r"\(\(([^()]*?)\)\)", r"\1", s)     # ((testo)) → testo
    return s.replace("((", "").replace("))", "")   # sweep dei doppi-tondi residui/annidati


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
    # La promessa "riferimenti normativi verbatim / tracciabilità" si fa SOLO nei report
    # legale-compliance (LegalBoost/FiscoBoost) DOVE il testo di legge verbatim È la sostanza.
    # Su un report di strategia/marketing (ambito "professionale") con una citazione
    # incidentale (es. un solo rimando GDPR) l'asserzione è un over-promise: fa leggere come
    # "verificati/tracciabili" anche numeri e COMPETITOR che il modello ha prodotto senza
    # fonte (vedi report StrategyBoost reale: 5 competitor nominati senza web search).
    strong = has_citations and ambito == "legale-compliance"
    fonti = ("parametri di settore e — dove applicabile — riferimenti normativi riportati "
             "verbatim dalla fonte ufficiale, per garantire tracciabilità e affidabilità delle valutazioni"
             if strong else
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


def _risk_chip(score: int, S) -> Table:
    """Livello di rischio del CASO al posto del gauge numerico (report legali): uno 'score
    45/100' su un caso legale è un numero muto/black-box (non è un audit di compliance). La
    banda deriva dallo score (più basso = più rischio) e si legge subito."""
    band, tone = (("BASSO", ST.GREEN) if score >= 70 else
                  ("MEDIO-ALTO", ST.AMBER) if score >= 45 else ("ALTO", ST.RED))
    inner = [Paragraph(f'<font name="{ST.F_BOLD}" size="8" color="{ST.hx(ST.GOLD_DK)}">'
                       f'LIVELLO DI RISCHIO DEL CASO</font>', S["kv"]), Spacer(1, 4),
             Paragraph(f'<font name="{ST.F_BOLD}" size="17" color="{ST.hx(tone)}">{band}</font>', S["body"]),
             Spacer(1, 2),
             Paragraph('<font size="7" color="#8A7A55">valutazione qualitativa, non un punteggio</font>', S["kv"])]
    t = Table([[inner]], colWidths=[38 * mm])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, tone), ("LINEABOVE", (0, 0), (-1, 0), 3, tone),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return t


def _split_lead(text: str, target: int = 560) -> tuple[str, str]:
    """Divide la sintesi in (lead accanto al gauge, resto a piena larghezza) SENZA
    troncare: taglia sul confine di frase più vicino a `target`, fallback su spazio.
    Se il testo sta sotto la soglia, il resto è vuoto."""
    text = (text or "").strip()
    if len(text) <= target:
        return text, ""
    window = text[:target]
    cut = max(window.rfind(". "), window.rfind("! "), window.rfind("? "), window.rfind("\n"))
    if cut < target * 0.5:                # nessun confine di frase utile → spezza su parola
        cut = window.rfind(" ")
    if cut <= 0:
        cut = target - 1
    return text[:cut + 1].strip(), text[cut + 1:].strip()


def _exec_summary(deliverable, S, ambito: str = "") -> list:
    """Executive Summary visuale: gauge score (o banda di rischio, sui legali) + sintesi +
    evidenze + azioni. La sintesi NON viene mai troncata: il lead sta accanto al gauge,
    l'eventuale eccedenza continua a piena larghezza sotto."""
    out = [_Heading("Executive Summary", S["h1"], "exec")]
    score = _find_score(deliverable)
    # Problema 6: se c'è una DECISIONE da prendere (pacchetto consulenziale con
    # decisione_sintesi), l'Executive Summary PARTE da quella, non dal primo alert.
    pack = deliverable.get("consulenza_operativa")
    decisione = pack.get("decisione_sintesi") if isinstance(pack, dict) else None
    # ORDINE CONSULENZIALE (#1 review deliverable): il management capisce il PERCHÉ prima
    # del cosa — problema → causa → raccomandazione; le azioni vengono DOPO (in coda).
    # NB: nei report DECISIONALI (M&A: c'è decisione_sintesi) il lead resta la decisione
    # (è già il "perché" condensato) — la struttura vale per i report diagnostici.
    _structured = ""
    if isinstance(pack, dict) and not (isinstance(decisione, dict) and decisione.get("sintesi")):
        from . import compose as CMP
        _ins_l = CMP._ins(deliverable)
        _alti = [i for i in _ins_l if str(i.get("gravita")) == "alta"]
        _ipo = [i for i in (CMP._diag(deliverable).get("ipotesi") or []) if isinstance(i, dict)]
        _parts = []
        if _alti:
            _parts.append(f"Il problema: {_alti[0].get('titolo', '')} ({CMP._fmt_val(_alti[0])}).")
        if _ipo:
            _p = _ipo[0].get("probabilita")
            _ptxt = f" (~{int(_p)}% di probabilità)" if isinstance(_p, (int, float)) else ""
            _parts.append(f"La causa più probabile: {_ipo[0].get('causa', '')}{_ptxt}.")
        _racc = CMP._first_sentence((CMP._conf_options(deliverable) or {}).get("conclusione_motivata"))
        if _racc:
            _parts.append(f"La raccomandazione: {_racc}")
        if len(_parts) >= 2:
            _structured = " ".join(_parts)
    if _structured:
        summary = _structured
    elif isinstance(decisione, dict) and decisione.get("sintesi"):
        summary = (decisione.get("domanda_decisionale", "") + " "
                   + decisione["sintesi"]).strip()
    else:
        # to_text: sballa eventuali wrapper {type,$value} e rende slice-safe la sintesi.
        summary = NORM.to_text(_find_text(deliverable, "sintesi", "executive", "summary", "esecutiv")) \
            or ("Sintesi dei principali risultati dell'analisi, delle criticità rilevate e delle "
                "priorità d'azione individuate per l'azienda.")
    lead, rest = _split_lead(summary, 560)
    # riga: gauge (o banda di rischio sui legali) + lead della sintesi
    if ambito == "legale-compliance" and score:
        left = _risk_chip(score[1], S)
    else:
        left = ST.Gauge(score[1], "Score") if score else Paragraph("", S["body"])
    right = Paragraph(_rich(lead), S["lead"])
    row = Table([[left, right]], colWidths=[40 * mm, ST.CONTENT_W - 40 * mm])
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, 0), 10)]))
    out += [row, Spacer(1, 6)]
    # eccedenza della sintesi → paragrafi a piena larghezza (continua, non tronca)
    for para in re.split(r"\n{2,}", rest):
        para = para.strip()
        if para:
            out.append(Paragraph(_rich(para), S["lead"]))
    if rest:
        out.append(Spacer(1, 6))
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
        # QA owner 8 lug: i target numerici nelle azioni (CAC, break-even mese, n. contratti,
        # importi-obiettivo) si leggevano come KPI quasi-definitivi. Se le azioni contengono
        # cifre → caption esplicita che sono ipotesi di scenario, non consuntivi. Niente
        # caption sulle azioni puramente qualitative (nessuna cifra = niente falso allarme).
        if any(re.search(r"\d", str(a)) for a in azioni):
            out.append(Spacer(1, 3))
            out.append(Paragraph(
                '<font size="8" color="#8A7A55"><b>SCENARIO ASSUNTIVO</b> · le soglie e i '
                "target citati (KPI, tempi, importi-obiettivo) sono ipotesi da validare sui "
                "dati reali, non valori consuntivi.</font>", S["bullet"]))
    return out


def _suppress_render(deliverable) -> set:
    """Sezioni-render che il pacchetto consulenziale chiede di NON mostrare (Problema 6:
    sezioni dinamiche — se il ragionamento le rende ridondanti, non compaiono).
    Vuoto per i report senza pacchetto → comportamento invariato."""
    pack = deliverable.get("consulenza_operativa")
    if isinstance(pack, dict):
        return set(pack.get("_suppress_render") or [])
    return set()


def _kpi_dashboard(deliverable, S, ambito: str = "") -> list:
    """Dashboard sintetica: card per score, rischio, priorità (derivati)."""
    cards = []
    score = _find_score(deliverable)
    # Sui report legali NON si mostra lo 'score X/100' (numero muto su un caso): la banda di
    # rischio è già nell'executive summary. Le altre card (rischio/priorità testuali) restano.
    if score and ambito != "legale-compliance":
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


def _decision_board(deliverable, S, ambito: str = "") -> list:
    """Board decisionale finale (Livello 2): derivata deterministicamente da
    score + segnali (urgenza/priorità/rischio/investimento/ROI) già nel deliverable.
    Chiude il report con 'cosa decidere'. Nessun dato inventato: solo estratti."""
    score = _find_score(deliverable)

    def find_kv(*hints, maxlen=28):
        res = [None]
        def walk(x):
            if isinstance(x, dict):
                for k, v in x.items():
                    if isinstance(v, str) and 0 < len(v) <= maxlen and any(h in k.lower() for h in hints) and not res[0]:
                        res[0] = v
                    walk(v)
            elif isinstance(x, list):
                for v in x[:20]:
                    walk(v)
        walk(deliverable)
        return res[0]

    cells: list = []
    # Sui legali niente 'Score generale X/100' (numero muto su un caso): resta la Decisione
    # testuale e i segnali qualitativi.
    if score and ambito != "legale-compliance":
        sc = score[1]
        tone = ST.GREEN if sc >= 70 else ST.AMBER if sc >= 45 else ST.RED
        cells.append({"label": "Score generale", "value": f"{sc}/100", "tone": tone})
    for hints, label, semaforo in [
        (("urgenz",), "Urgenza", True),
        (("priorit",), "Priorità", True),
        (("rischio", "risk"), "Rischio", True),
        (("investiment", "budget", "costo_intervent"), "Investimento", False),
        (("roi", "ritorno", "payback", "recupero"), "ROI atteso", False),
    ]:
        val = find_kv(*hints)
        if val and len(cells) < 6:
            tone = ST.SEMAFORO.get(val.lower(), ST.NEUTRAL) if semaforo else ST.NEUTRAL
            cells.append({"label": label, "value": val.capitalize()[:18], "tone": tone})
    if score and len(cells) < 6:
        sc = score[1]
        dec = "Procedere" if sc >= 70 else ("Procedere con cautela" if sc >= 45 else "Intervento urgente")
        tone = ST.GREEN if sc >= 70 else ST.AMBER if sc >= 45 else ST.RED
        cells.append({"label": "Decisione", "value": dec, "tone": tone})
    if len(cells) < 3:
        return []
    return [Spacer(1, 10), ST.decision_board(cells, S=S)]


# ===================== appendice normativa + disclaimer ==================
def _appendix(citazioni, deliverable, blueprint, S) -> list:
    """Blocco Livello 3 — appendice tecnica: fonti, testi normativi, disclaimer.
    Preceduto dalla banda di livello solo se c'è contenuto reale."""
    inner: list = []
    if citazioni:
        inner += _fonti(citazioni, S) + _testi_normativi(citazioni, S)
    inner += _disclaimer_inline(deliverable, blueprint, S)
    if not inner:
        return []
    band = ST.layer_band("appendix", "Livello 3 — Appendice tecnica",
                         "fonti, testi normativi, note metodologiche", S)
    return [Spacer(1, 8), band] + inner
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
        t = _strip_akn(str(c.get("testo", "")))   # via il markup Akoma Ntoso ((...)) trapelato
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


# Trigger di ALTA CRITICITÀ (hard-stop): profili penali, violazioni dati, autorità,
# stampa, conservazione prove. Se il caso ne tocca ≥2 distinti, il report APRE con un
# avviso di intervento professionale urgente (l'AI non deve "continuare l'analisi" come
# se fosse un caso ordinario).
_HARD_STOP_RE = re.compile(
    r"\b(reato|penale|querela|denuncia|data breach|violazione dei dati|indagine|"
    r"perquisizione|sequestro|giornalist|autorit[àa] giudiziaria|procura della repubblica|"
    r"ispezione|diffida|whistleblow|conservazione (?:delle )?prove|sanzione penale|"
    r"minacce? legali|misura cautelare|garante)\b", re.I)


def _hard_stop_banner(deliverable, S) -> list:
    """Avviso di apertura per i casi ad ALTA CRITICITÀ (≥2 trigger distinti): l'utente deve
    capire SUBITO che serve un avvocato ora, non a valle di un report ordinario."""
    import json as _json
    hits = {m.group(1).lower() for m in _HARD_STOP_RE.finditer(_json.dumps(deliverable, ensure_ascii=False))}
    if len(hits) < 2:
        return []
    txt = ("<b>ATTENZIONE — CASO AD ALTA CRITICITÀ.</b> Il caso presenta elementi (profili "
           "penali, violazioni di dati, coinvolgimento di autorità o esigenze di conservazione "
           "delle prove) che richiedono l'intervento IMMEDIATO di un avvocato. Questo documento "
           "è un primo orientamento e NON sostituisce l'assistenza legale: usalo come base di "
           "lavoro col professionista, non come decisione autonoma.")
    box = Table([[Paragraph(txt, S["small"])]], colWidths=[ST.CONTENT_W])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ST.WARM),
                             ("BOX", (0, 0), (-1, -1), 1.2, ST.RED),
                             ("LINEABOVE", (0, 0), (-1, 0), 3, ST.RED),
                             ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                             ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    return [box, Spacer(1, 8)]


def _build(pdf_path: Path, cover_meta, report_name, body_blocks, deliverable, ambito,
           has_citations: bool = False, preliminare: bool = False, alert: bool = False):
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    S = ST.styles()
    doc = _Doc(pdf_path, cover_meta, report_name)
    toc = TableOfContents()
    toc.levelStyles = [S["toc"]]
    story = [NextPageTemplate("content"), PageBreak()]
    if alert:
        story += _hard_stop_banner(deliverable, S)
    if preliminare:
        story += _preliminary_banner(S)
    story += _methodology(S, ambito, has_citations)
    story += [PageBreak(), _Heading("Indice del report", S["h1"], "indice"), Spacer(1, 4), toc, PageBreak()]
    # Pagina-diagnosi CEO (#2, review deliverable): tutto il report in <1 minuto,
    # PRIMA dell'Executive Summary. Presente solo se il pacchetto ha i dati.
    from . import compose as CMP
    story += CMP.premium_front(deliverable, S)
    story += [ST.layer_band("executive", "Livello 1 — Executive",
                            "lettura 30 secondi · per chi decide", S), Spacer(1, 6)]
    story += _exec_summary(deliverable, S, ambito)
    if "kpi_dashboard" not in _suppress_render(deliverable):
        story += _kpi_dashboard(deliverable, S, ambito)
    story += [Spacer(1, 8), ST.layer_band("analysis", "Livello 2 — Analisi",
                                          "5-10 minuti · per il management", S), Spacer(1, 6)]
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


# semaforo → (livello, urgenza, avvocato) per la matrice decisionale legale.
_SEMAFORO_MATRIX = {
    "rosso": ("Alto", "Alta", "Sì, subito"),
    "giallo": ("Medio", "Media", "Consigliato"),
    "verde": ("Basso", "Bassa", "Facoltativo"),
}


def _decision_matrix(mappa_rischi, S) -> list:
    """Matrice decisionale (report legali): la mappa rischi come TABELLA azionabile —
    Area | Livello | Urgenza | Avvocato — derivata SOLO dal semaforo reale (nessun
    accostamento inventato). Sostituisce la heatmap: stessi dati + colonne per decidere."""
    rows = []
    for m in mappa_rischi or []:
        if not isinstance(m, dict):
            continue
        area = str(m.get("area") or "").strip()
        if not area:
            continue
        liv, urg, avv = _SEMAFORO_MATRIX.get(str(m.get("semaforo", "")).lower(),
                                             ("Medio", "Media", "Consigliato"))
        rows.append([area, liv, urg, avv])
    if not rows:
        return []
    t = ST.premium_table(["Area di rischio", "Livello", "Urgenza", "Avvocato"], rows, S,
                         widths=[ST.CONTENT_W - 78 * mm, 26 * mm, 26 * mm, 26 * mm])
    return [Spacer(1, 4), Paragraph("Matrice decisionale", S["h3"]), Spacer(1, 2), t, Spacer(1, 2),
            Paragraph('<font size="7" color="#8A7A55">Livello e urgenza derivano dal rischio per '
                      "area; le azioni di dettaglio sono nel Piano d'azione.</font>", S["bullet"]),
            Spacer(1, 6)]


def _allegati_block(allegati, S) -> list:
    """Allegati operativi (report legali su quesito): documenti per l'avvocato + checklist
    prove + timeline eventi — dati derivati dal caso, NON template legali (diffide ecc.).
    Vuoto se non forniti."""
    if not isinstance(allegati, dict):
        return []
    docs = [str(d).strip() for d in (allegati.get("elenco_documenti") or []) if str(d).strip()]
    prove = [str(p).strip() for p in (allegati.get("checklist_prove") or []) if str(p).strip()]
    tl = [t for t in (allegati.get("timeline") or []) if isinstance(t, dict) and str(t.get("evento") or "").strip()]
    if not (docs or prove or tl):
        return []
    out = [_Heading("Allegati operativi", S["h1"], "allegati")]
    if prove:
        out += [ST.action_box(prove[:8], "Checklist — prove da raccogliere e conservare subito", S), Spacer(1, 4)]
    if docs:
        out += [ST.action_box(docs[:8], "Documenti da consegnare al legale", S), Spacer(1, 4)]
    if tl:
        rows = [[str(t.get("quando") or "—"), str(t.get("evento") or "").strip()] for t in tl[:10]]
        out += [Paragraph("Timeline degli eventi", S["h3"]),
                ST.premium_table(["Quando", "Evento"], rows, S, widths=[38 * mm, ST.CONTENT_W - 38 * mm]),
                Spacer(1, 4)]
    return out


def _ops_blocks(deliverable: dict, S) -> list:
    """Blocchi operativi UNIVERSALI (tutti i boost), da `deliverable['report_ops']`:
    dashboard semaforo rischi (4 livelli), matrice Impatto/Probabilità, timeline a 4
    orizzonti, checklist operativa, template compilabili. Ogni blocco è opzionale: si
    rende solo se ci sono dati. Vuoto se la pass ops non ha girato (offline/errore)."""
    ops = deliverable.get("report_ops")
    if not isinstance(ops, dict):
        return []
    out: list = []

    sem = [x for x in (ops.get("semaforo_rischi") or []) if isinstance(x, dict) and str(x.get("area") or "").strip()]
    if sem:
        out += [_Heading("Dashboard rischi", S["h1"], "ops-semaforo"),
                Paragraph("Semaforo per area: livello, conseguenza attesa e urgenza d'intervento.", S["body"]),
                Spacer(1, 3), ST.semaforo_board(sem, S), Spacer(1, 6)]

    mat = [x for x in (ops.get("matrice_rischi") or []) if isinstance(x, dict) and str(x.get("rischio") or "").strip()]
    if mat:
        out += [_Heading("Matrice Impatto / Probabilità", S["h1"], "ops-matrice"),
                ST.impact_matrix(mat, S), Spacer(1, 6)]

    tl = [x for x in (ops.get("timeline_operativa") or []) if isinstance(x, dict) and str(x.get("azione") or "").strip()]
    tl_flow = ST.timeline_ops(tl, S) if tl else []
    if tl_flow:
        out += [_Heading("Timeline operativa", S["h1"], "ops-timeline")] + tl_flow + [Spacer(1, 4)]

    chk = [x for x in (ops.get("checklist") or []) if isinstance(x, dict) and str(x.get("azione") or "").strip()]
    if chk:
        out += [_Heading("Checklist operativa", S["h1"], "ops-checklist"),
                ST.checklist_table(chk, S), Spacer(1, 6)]

    tpl = [x for x in (ops.get("template") or []) if isinstance(x, dict) and str(x.get("corpo") or "").strip()]
    if tpl:
        out.append(_Heading("Template pronti all'uso", S["h1"], "ops-template"))
        out.append(Paragraph("Fac-simili compilabili: sostituisci i segnaposto tra parentesi "
                             "quadre. Orientativi, da verificare prima dell'invio.", S["body"]))
        out.append(Spacer(1, 4))
        for t in tpl[:3]:
            out += [ST.template_box(t, S), Spacer(1, 6)]
    return out


# ========================= LegalBoost (dedicato) =========================
def render_pdf(deliverable: dict, blueprint: dict, citazioni: list, pdf_path: Path,
               preliminare: bool = False, allegati: dict | None = None) -> None:
    S = ST.styles()
    cover_meta, report_name = _cover_meta(deliverable, blueprint, "LegalBoost",
                                          "Diagnosi legale e compliance",
                                          "Quadro dei rischi legali e priorità d'azione per la tua impresa.")
    sint = deliverable.get("sintesi", {})
    voci = list(deliverable.get("voci", []))
    # De-dup struttura (bug O): il blueprint LegalBoost ha le voci `sintesi_mappa_rischi`
    # e `piano_azione_handoff`, ma il render emette GIÀ una sezione sintesi (heatmap) e
    # una piano d'azione (tabella) → prima uscivano doppie ("01+02 · Sintesi…",
    # "10+11 · Piano d'azione"). Qui si FONDONO: la prosa della voce sintesi entra nella
    # sezione 01, la tabella del piano si aggancia alla voce piano (niente heading extra).
    voce_sintesi = next((v for v in voci if v.get("id") == "sintesi_mappa_rischi"), None)
    piano_ids = {"piano_azione_handoff"}

    # Titolo sezione 01 dalla voce sintesi: in modalità quesito è "Risposta al tuo quesito",
    # in audit resta "Sintesi e mappa rischi" (default se la voce manca il titolo).
    sez01 = str((voce_sintesi or {}).get("titolo") or "Sintesi e mappa rischi").strip()
    body = [_Heading(f"01 · {sez01}", S["h1"], "legal-1")]
    if voce_sintesi and voce_sintesi.get("contenuto"):
        body.append(Paragraph(_rich(str(voce_sintesi["contenuto"])), S["body"]))
    if sint.get("mappa_rischi"):
        body += _decision_matrix(sint["mappa_rischi"], S)

    def _piano_table():
        rows = [[str(p.get("priorita", "")), str(p.get("azione", "")),
                 "Avvocato" if p.get("handoff_avvocato") else "—"]
                for p in deliverable.get("piano_azione") or []]
        return ST.premium_table(["#", "Azione", "Handoff"], rows, S,
                                widths=[12 * mm, ST.CONTENT_W - 42 * mm, 30 * mm]) if rows else None

    piano_reso = False
    n = 2
    for v in voci:
        if v is voce_sintesi:
            continue  # già fusa nella sezione 01
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
        if v.get("id") in piano_ids:
            t = _piano_table()
            if t:
                body += [Spacer(1, 4), t]
            piano_reso = True
        body.append(Spacer(1, 4))

    if not piano_reso and deliverable.get("piano_azione"):
        body.append(_Heading(f"{n:02d} · Piano d'azione", S["h1"], f"legal-{n}"))
        t = _piano_table()
        if t:
            body.append(t)
    body += _allegati_block(allegati, S)
    body += _ops_blocks(deliverable, S)
    body += _decision_board(deliverable, S, "legale-compliance")
    body += _appendix(citazioni, deliverable, blueprint, S)
    _build(pdf_path, cover_meta, report_name, body, deliverable, "legale-compliance",
           has_citations=bool(citazioni), preliminare=preliminare, alert=True)


# ========================= Generico (a componenti) =======================
def _is_list_of_dicts(v):
    return isinstance(v, list) and v and all(isinstance(x, dict) for x in v)


def _effectively_empty(v):
    """True se la sezione non ha NIENTE da stampare: vuota, o un dict/list i cui
    valori sono tutti (ricorsivamente) vuoti. Serve a saltare una sezione required
    ma svuotata (es. FinanceBoost PARTIAL: `riclassificazione` con anni/SP/CE = [])
    che altrimenti stamperebbe un heading nudo. `0` e `False` NON sono vuoti."""
    if v in (None, "", [], {}):
        return True
    if isinstance(v, dict):
        return all(_effectively_empty(x) for x in v.values())
    if isinstance(v, list):
        return all(_effectively_empty(x) for x in v)
    return False


def _voce_has_text(voce: dict) -> bool:
    """True se una voce (voci-shape) ha TESTO reale da stampare. Guarda SOLO i campi che
    portano contenuto (prosa + descrizioni/azioni/findings), NON lo scaffolding enum
    (tipo/gravita/fonte/status/id) che il placeholder degradato riempie sempre."""
    parts = [str(voce.get("contenuto") or "")]
    for it in (voce.get("rischi_opportunita") or []) + (voce.get("rischi") or []):
        parts.append(str(it.get("descrizione") or it.get("testo") or "") if isinstance(it, dict) else str(it))
    for it in (voce.get("azioni") or []):
        parts.append(it if isinstance(it, str) else str(it.get("azione") or it.get("descrizione") or ""))
    for it in (voce.get("findings") or []):
        parts.append(it if isinstance(it, str) else str(it.get("descrizione") or it.get("titolo") or ""))
    return any(p.strip() for p in parts)


def _has(items, *keys):
    return items and all(any(k in it for k in keys) for it in items[:2])


# ── Sezioni consulenziali (pacchetto operations, spec §6-§10, §14) ────────────
_CONF_META = {"A": (ST.GREEN, "dato verificato"),
              "B": (ST.AMBER, "inferenza supportata"),
              "C": (ST.NEUTRAL, "ipotesi da validare")}


def _conf_chip(level) -> str:
    """Badge inline del livello di certezza (§14): [A]/[B]/[C] colorato + legenda."""
    lv = str(level or "").strip().upper()
    if lv not in _CONF_META:
        return ""
    color, label = _CONF_META[lv]
    return (f' <font name="{ST.F_BOLD}" size="8" color="{ST.hx(color)}">[{lv}]</font>'
            f'<font size="8" color="#8A7A55"> {label}</font>')


def _evidence_lines(node, S) -> list:
    out = []
    for ev in (node.get("evidenze") or [])[:4]:
        out.append(Paragraph(f'<font size="8" color="#8A7A55">Evidenza: '
                             f'{html.escape(NORM.to_text(ev))}</font>', S["bullet"]))
    return out


def _neutral_box(lines: list[str], title: str, S, border=None):
    inner = [Paragraph(f'<font name="{ST.F_BOLD}" size="9" color="{ST.hx(ST.GOLD_DK)}">'
                       f'{html.escape(title)}</font>', S["body"])]
    for line in lines:
        inner.append(Paragraph(_rich(line), S["small"]))
    box = Table([[inner]], colWidths=[ST.CONTENT_W])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ST.WARM),
                             ("BOX", (0, 0), (-1, -1), 0.8, border or ST.LINE),
                             ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                             ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return box


_RACI_TONE = {"A": ST.GOLD_DK, "R": ST.GREEN, "C": ST.AMBER, "I": ST.NEUTRAL}


def _raci_table(raci: dict, S):
    """Matrice RACI come tabella colorata: attività x ruoli proposti."""
    ruoli = [str(r) for r in (raci.get("ruoli") or [])]
    rows = [[Paragraph("<b>Attività</b>", S["small"])]
            + [Paragraph(f"<b>{html.escape(r.replace(' (proposto)', ''))}</b>", S["kv"])
               for r in ruoli]]
    for item in (raci.get("attivita") or []):
        marks = item.get("assegnazioni") or {}
        row = [Paragraph(html.escape(str(item.get("attivita", ""))), S["small"])]
        for r in ruoli:
            m = str(marks.get(r.replace(" (proposto)", ""), "") or "")
            color = _RACI_TONE.get(m, ST.CARBON)
            row.append(Paragraph(f'<font name="{ST.F_BOLD}" color="{ST.hx(color)}">'
                                 f'{html.escape(m)}</font>', S["kv"]))
        rows.append(row)
    first_w = 44 * mm
    col_w = (ST.CONTENT_W - first_w) / max(len(ruoli), 1)
    t = Table(rows, colWidths=[first_w] + [col_w] * len(ruoli), repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ST.WARM),
        ("GRID", (0, 0), (-1, -1), 0.4, ST.LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


_FASE_LABEL = {"osservazione": "OSSERVAZIONE", "cause": "CAUSE",
               "conseguenze": "CONSEGUENZE", "priorita": "PRIORITÀ",
               "intervento": "INTERVENTO", "risultato_atteso": "RISULTATO ATTESO"}


def _causal_chain_block(c: dict, S) -> list:
    """Catena causa-effetto come flusso verticale: fase → testo → ↓."""
    out = [Paragraph(f"<b>{html.escape(str(c.get('titolo', 'Catena delle cause')))}</b>"
                     + _conf_chip(c.get("confidence")), S["h3"])]
    nodi = [n for n in (c.get("catena") or []) if n.get("testo")]
    rows = []
    for i, n in enumerate(nodi):
        label = _FASE_LABEL.get(str(n.get("fase")), str(n.get("fase", "")).upper())
        cell = [Paragraph(f'<font name="{ST.F_BOLD}" size="8" color="{ST.hx(ST.GOLD_DK)}">'
                          f'{label}</font>', S["kv"]),
                Paragraph(_rich(n["testo"]), S["small"])]
        rows.append([cell])
        if i < len(nodi) - 1:
            rows.append([Paragraph(f'<font size="11" color="{ST.hx(ST.GOLD_DK)}">▼</font>',
                                   S["kv"])])
    t = Table(rows, colWidths=[ST.CONTENT_W])
    style = [("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    for r in range(0, len(rows), 2):          # box solo sulle celle-fase, non sulle frecce
        style += [("BACKGROUND", (0, r), (0, r), ST.WARM),
                  ("BOX", (0, r), (0, r), 0.6, ST.LINE)]
    t.setStyle(TableStyle(style))
    out += [t, Spacer(1, 6)]
    return out


def _diagnosis_block(diag: dict, S) -> list:
    """IPOTESI DIAGNOSTICA (Problemi 3,7,8): ipotesi pesate + ipotesi ESCLUSE.
    Il ragionamento PRIMA delle azioni."""
    out = [Paragraph("Ipotesi diagnostica", S["h2"])]
    if diag.get("domanda"):
        out.append(Paragraph(f"<b>{html.escape(str(diag['domanda']))}</b>", S["body"]))
    if diag.get("sintesi"):
        out.append(Paragraph(_rich(diag["sintesi"]) + _conf_chip(diag.get("confidence")),
                             S["body"]))
        out.append(Spacer(1, 4))
    # barre di probabilità per ipotesi
    ipo = [h for h in (diag.get("ipotesi") or []) if h.get("probabilita")]
    if ipo:
        out.append(Paragraph("Ipotesi principali (stima dal peso delle evidenze)", S["h3"]))
        maxp = max(h["probabilita"] for h in ipo) or 100
        for h in ipo:
            p = int(h["probabilita"])
            filled = max(1, round(p / maxp * 22))
            bar = "█" * filled
            out.append(Paragraph(
                f'<font name="{ST.F_BOLD}" color="{ST.hx(ST.GOLD_DK)}">{p:>3}%</font> '
                f'<font color="{ST.hx(ST.GOLD)}">{bar}</font> {_rich(h.get("causa", ""))}'
                + _conf_chip(h.get("confidence")), S["bullet"]))
            for e in (h.get("evidenze") or [])[:3]:
                out.append(Paragraph(f'<font size="7.5" color="#8A7A55">— {html.escape(NORM.to_text(e))}'
                                     "</font>", S["bullet"]))
        out.append(Spacer(1, 4))
    # ipotesi escluse (perché NON è quello) — la firma del ragionamento consulenziale
    escl = diag.get("ipotesi_escluse") or []
    if escl:
        out.append(Paragraph("Ipotesi escluse (e perché)", S["h3"]))
        for e in escl:
            out.append(Paragraph(
                f'<font color="{ST.hx(ST.RED)}">✗</font> <b>{html.escape(str(e.get("causa","")))}:</b> '
                f'{_rich(e.get("perche_esclusa", ""))}', S["bullet"]))
        out.append(Spacer(1, 6))
    return out


def _kpi_to_measure_block(kpis: list, S) -> list:
    """KPI SPECIFICI del problema da iniziare a misurare (Problema 5)."""
    if not kpis:
        return []
    out = [Paragraph("KPI da iniziare a misurare (specifici di questo problema)", S["h3"])]
    for k in kpis:
        out.append(Paragraph(
            f'<font color="{ST.hx(ST.GOLD_DK)}">•</font> <b>{html.escape(str(k.get("kpi","")))}</b> '
            f'<font size="8" color="#8A7A55">— {html.escape(str(k.get("perche","")))}</font>',
            S["bullet"]))
    out.append(Paragraph('<font size="8" color="#8A7A55">Nessuno di questi è oggi disponibile: '
                         'sono i numeri da rilevare per trasformare la diagnosi in misura.</font>',
                         S["bullet"]))
    out.append(Spacer(1, 6))
    return out


def _finance_reasoning_blocks(pack: dict, S) -> list:
    """Sezioni del pacchetto finanza: insight, catene, forecast, simulazioni,
    confronto soluzioni, raccomandazioni 4-perché, sezioni di valore §13."""
    out: list = []

    ins = pack.get("insight_derivati") or []
    if ins:
        out.append(Paragraph("Cosa dicono i tuoi numeri (analisi derivata)", S["h2"]))
        for i in ins:
            unita = f" {i.get('unita', '')}" if i.get("unita") else ""
            tone = ST.RED if i.get("gravita") == "alta" else (
                ST.AMBER if i.get("gravita") == "media" else ST.GOLD_DK)
            out.append(Paragraph(
                f'<font name="{ST.F_BOLD}" color="{ST.hx(tone)}">'
                f'{html.escape(str(i.get("titolo", "")))}: '
                f'{html.escape(_scalar_str(i.get("valore")))}{html.escape(unita)}</font>'
                + _conf_chip(i.get("confidence")), S["body"]))
            out.append(Paragraph(_rich(i.get("spiegazione", "")), S["small"]))
            out.append(Paragraph(f'<font size="7.5" color="#8A7A55">Calcolo: '
                                 f'{html.escape(str(i.get("formula", "")))}</font>', S["bullet"]))
            out.append(Spacer(1, 3))
        out.append(Spacer(1, 4))

    # Ordine di ragionamento (Problema 7): dopo le evidenze, le IPOTESI (con escluse),
    # poi le catene causali, poi i KPI da misurare, e SOLO alla fine le azioni.
    if isinstance(pack.get("ipotesi_diagnostica"), dict):
        out += _diagnosis_block(pack["ipotesi_diagnostica"], S)

    for c in (pack.get("analisi_sistemica") or []):
        out += _causal_chain_block(c, S)

    out += _kpi_to_measure_block(pack.get("kpi_da_misurare") or [], S)

    fc = pack.get("forecast_13_settimane")
    if isinstance(fc, dict) and fc.get("scenari"):
        out.append(Paragraph("Forecast di cassa a 13 settimane (simulazione)", S["h2"]))
        header = [Paragraph("<b>Scenario</b>", S["kv"])] + [
            Paragraph(f"<b>S{w}</b>", S["kv"]) for w in (1, 3, 5, 7, 9, 11, 13)] + [
            Paragraph("<b>1ª sett. negativa</b>", S["kv"])]
        rows = [header]
        for nome, sc in fc["scenari"].items():
            weeks = {r["settimana"]: r["saldo"] for r in sc.get("settimane", [])}
            cells = [Paragraph(html.escape(nome.capitalize()), S["kv"])]
            for w in (1, 3, 5, 7, 9, 11, 13):
                v = weeks.get(w)
                tone = ST.RED if (v is not None and v < 0) else ST.CARBON
                cells.append(Paragraph(f'<font color="{ST.hx(tone)}">'
                                       f'{html.escape(_scalar_str(v))}</font>', S["kv"]))
            neg = sc.get("prima_settimana_negativa")
            cells.append(Paragraph("—" if neg is None else f"settimana {neg}", S["kv"]))
            rows.append(cells)
        t = Table(rows, colWidths=[26 * mm] + [(ST.CONTENT_W - 26 * mm - 30 * mm) / 7] * 7
                  + [30 * mm], repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), ST.WARM),
                               ("GRID", (0, 0), (-1, -1), 0.4, ST.LINE),
                               ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                               ("TOPPADDING", (0, 0), (-1, -1), 4),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        out += [t, Spacer(1, 3)]
        out.append(_neutral_box([f"• {h}" for h in (fc.get("ipotesi") or [])]
                                + ([str(fc.get("nota"))] if fc.get("nota") else []),
                                "Ipotesi della simulazione (esplicite)", S))
        out.append(Spacer(1, 6))

    sims = pack.get("simulazioni") or []
    if sims:
        out.append(Paragraph("Simulazioni what-if sui rischi principali", S["h2"]))
        for s in sims:
            out.append(Paragraph(f"<b>{html.escape(str(s.get('domanda', '')))}</b>", S["h3"]))
            out.append(Paragraph(f"→ {_rich(s.get('risultato', ''))} "
                                 f'<font size="7.5" color="#8A7A55">(calcolo: '
                                 f'{html.escape(str(s.get("calcolo", "")))})</font>', S["body"]))
            if s.get("implicazione"):
                out.append(Paragraph(_rich(s["implicazione"]), S["small"]))
            out.append(Spacer(1, 3))
        out.append(Spacer(1, 4))

    conf = pack.get("confronto_soluzioni") or {}
    if conf.get("opzioni"):
        out.append(Paragraph("Confronto delle soluzioni", S["h2"]))
        if conf.get("nota"):
            out.append(Paragraph(f'<font size="8" color="#8A7A55">'
                                 f'{html.escape(str(conf["nota"]))}</font>', S["bullet"]))
        for o in conf["opzioni"]:
            out.append(Paragraph(f"<b>{html.escape(str(o.get('opzione', '')))}</b>", S["h3"]))
            if o.get("descrizione"):
                out.append(Paragraph(_rich(o["descrizione"]), S["small"]))
            for label, key, tone in (("Vantaggi", "vantaggi", ST.GREEN),
                                     ("Svantaggi", "svantaggi", ST.RED)):
                for v in (o.get(key) or []):
                    out.append(Paragraph(f'<font color="{ST.hx(tone)}">•</font> {_rich(v)}',
                                         S["bullet"]))
            detail = " · ".join(f"{_humanize(k)}: {o[k]}" for k in
                                ("costi", "rischi", "tempi", "complessita", "dipendenze")
                                if o.get(k))
            if detail:
                out.append(Paragraph(f'<font size="8" color="#8A7A55">{html.escape(detail)}'
                                     "</font>", S["bullet"]))
            for label, key in (("Quando sceglierla", "quando_sceglierla"),
                               ("Quando evitarla", "quando_evitarla")):
                if o.get(key):
                    out.append(Paragraph(f"<b>{label}:</b> {_rich(o[key])}", S["bullet"]))
            out.append(Spacer(1, 4))
        if conf.get("conclusione_motivata"):
            out.append(_neutral_box([str(conf["conclusione_motivata"])],
                                    "Conclusione motivata", S, border=ST.GOLD_DK))
        out.append(Spacer(1, 6))

    recs = pack.get("raccomandazioni_operative") or []
    if recs:
        out.append(Paragraph("Raccomandazioni — il perché e il come", S["h2"]))
        for r in recs:
            out.append(Paragraph(f"<b>{html.escape(str(r.get('titolo', '')))}</b>", S["h3"]))
            for label, key in (("Perché", "perche"), ("Perché ora", "perche_ora"),
                               ("Perché questa", "perche_questa"),
                               ("Perché non un'altra", "perche_non_altre")):
                if r.get(key):
                    out.append(Paragraph(f"<b>{label}:</b> {_rich(r[key])}", S["bullet"]))
            op = r.get("operativo") or {}
            det = " · ".join(f"{_humanize(k)}: {v}" for k, v in op.items()
                             if isinstance(v, str) and v)
            if det:
                out.append(Paragraph(f'<font size="8" color="#8A7A55">{html.escape(det)}'
                                     "</font>", S["bullet"]))
            if op.get("kpi_generati"):
                out.append(Paragraph(f'<font size="8" color="#8A7A55">KPI generati: '
                                     f'{html.escape(", ".join(op["kpi_generati"]))}</font>',
                                     S["bullet"]))
            for sg in (r.get("soglie") or []):
                out.append(Paragraph(
                    f'<font size="8" color="#8A7A55">Soglia «{html.escape(str(sg.get("valore")))}» '
                    f'[{html.escape(str(sg.get("classificazione")))}]'
                    + (f" — {html.escape(str(sg.get('nota')))}" if sg.get("nota") else "")
                    + "</font>", S["bullet"]))
            out.append(Spacer(1, 4))

    for titolo, key in (("Errori che l'azienda sta probabilmente commettendo",
                         "errori_probabili"),
                        ("Opportunità non sfruttate", "opportunita_non_sfruttate"),
                        ("Decisioni da prendere entro 7 giorni", "decisioni_entro_7_giorni"),
                        ("Domande che il management dovrebbe porsi",
                         "domande_per_il_management")):
        items = pack.get(key) or []
        if items:
            out.append(Paragraph(titolo, S["h2"]))
            for it in items:
                out.append(Paragraph(f'<font color="{ST.hx(ST.GOLD_DK)}">•</font> {_rich(it)}',
                                     S["bullet"]))
            out.append(Spacer(1, 4))

    cov = pack.get("copertura_dati") or {}
    if cov.get("dati_non_sfruttati"):
        out.append(_neutral_box(
            [f"• {d}" for d in cov["dati_non_sfruttati"]],
            "Dati forniti non ancora sfruttati (per trasparenza)", S))
        out.append(Spacer(1, 4))
    return out


def _consulting_blocks(deliverable, S) -> list:
    """Renderizza il pacchetto consulenziale (consulenza_operativa) come sezioni
    dedicate: AS-IS, criticità, TO-BE, stati, RACI, governance, SLA, requisiti,
    opzioni tecnologiche comparate, piano 30-60-90, dati da raccogliere."""
    pack = deliverable.get("consulenza_operativa")
    if not isinstance(pack, dict):
        return []
    _TITOLI = {"finanza_liquidita": "Analisi sistemica — diagnosi, scenari e decisioni",
               "operations_commesse": "Modello operativo — diagnosi e riorganizzazione",
               "marketing_canali": "Analisi dei canali — diagnosi e riequilibrio",
               "hr_persone": "Persone e organizzazione — diagnosi e leve",
               "legale_compliance": "Presidio legale — gap, priorità e percorso",
               "strategia_crescita": "Strategia di crescita — canali, margini e scenari",
               "ma_acquisizione": "Valutazione dell'acquisizione — multipli, rischi e decisione",
               "diagnosi_efficienza": "Diagnosi — ragionamento, ipotesi e cause"}
    titolo_sezione = _TITOLI.get(str(pack.get("_tipo")),
                                 "Analisi consulenziale — diagnosi e decisioni")
    out: list = [PageBreak(),
                 _Heading(titolo_sezione, S["h1"], "consulenza"),
                 Spacer(1, 4),
                 Paragraph("Sezione consulenziale costruita sui dati forniti: le proposte "
                           "sono marcate come tali e ogni affermazione porta il suo livello "
                           "di certezza [A] verificato · [B] inferenza · [C] ipotesi.", S["small"]),
                 Spacer(1, 6)]
    out += _finance_reasoning_blocks(pack, S)

    asis = pack.get("processo_as_is") or {}
    if asis:
        out.append(Paragraph("Processo AS-IS — come lavora oggi l'azienda"
                             + _conf_chip(asis.get("confidence")), S["h2"]))
        if asis.get("sintesi_dal_racconto"):
            out.append(Paragraph(_rich(asis["sintesi_dal_racconto"]), S["body"]))
        if asis.get("strumenti_in_uso"):
            out.append(Paragraph("<b>Strumenti in uso dichiarati:</b> "
                                 + html.escape(", ".join(map(str, asis["strumenti_in_uso"]))),
                                 S["bullet"]))
        for k, v in (asis.get("dati_dichiarati") or {}).items():
            out.append(Paragraph(f"<b>{html.escape(_humanize(str(k)))}:</b> {_rich(_scalar_str(v))}",
                                 S["bullet"]))
        out += _evidence_lines(asis, S)
        if asis.get("nota"):
            out.append(_neutral_box([asis["nota"]], "Nota", S))
        out.append(Spacer(1, 6))

    crit = pack.get("criticita_rilevate") or []
    if crit:
        out.append(Paragraph("Criticità e colli di bottiglia", S["h2"]))
        for c in crit[:10]:
            extra = ("certezza " + str(c.get("confidence", ""))
                     + " · " + "; ".join(map(str, (c.get("evidenze") or [])[:2])))
            out.append(ST.risk_card(str(c.get("criticita", "")), c.get("gravita", "media"), S, extra))
            out.append(Spacer(1, 2))
        out.append(Spacer(1, 4))

    tobe = pack.get("processo_to_be") or {}
    if tobe.get("principi"):
        out.append(Paragraph("Processo TO-BE — modello proposto"
                             + _conf_chip(tobe.get("confidence")), S["h2"]))
        out.append(ST.action_box(list(tobe["principi"]), "Principi del nuovo modello", S))
        out.append(Spacer(1, 6))

    stati = pack.get("stati_commessa") or []
    if stati:
        out.append(Paragraph("Stati standard della commessa (proposta)", S["h2"]))
        rows = [[Paragraph(f"<b>{h}</b>", S["kv"]) for h in ("Stato", "Definizione",
                                                             "Ingresso", "Uscita")]]
        for s in stati:
            rows.append([Paragraph(html.escape(str(s.get(k, ""))), S["kv"])
                         for k in ("stato", "definizione", "ingresso", "uscita")])
        t = Table(rows, colWidths=[26 * mm, ST.CONTENT_W - 26 * mm - 84 * mm, 42 * mm, 42 * mm],
                  repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), ST.WARM),
                               ("GRID", (0, 0), (-1, -1), 0.4, ST.LINE),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("TOPPADDING", (0, 0), (-1, -1), 4),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        out += [t, Spacer(1, 6)]

    raci = pack.get("matrice_raci") or {}
    if raci.get("attivita"):
        out.append(Paragraph("Matrice RACI (ruoli proposti)", S["h2"]))
        out.append(_raci_table(raci, S))
        if raci.get("nota"):
            out.append(Paragraph(f'<font size="8" color="#8A7A55">{html.escape(str(raci["nota"]))}'
                                 "</font>", S["bullet"]))
        out.append(Spacer(1, 6))

    gov = pack.get("governance") or {}
    if gov:
        out.append(Paragraph("Governance" + _conf_chip(gov.get("confidence")), S["h2"]))
        for k, v in gov.items():
            if k in ("confidence", "evidenze") or not isinstance(v, str):
                continue
            out.append(Paragraph(f"<b>{html.escape(_humanize(k))}:</b> {_rich(v)}", S["bullet"]))
        out.append(Spacer(1, 6))

    sla = pack.get("sla_interni") or {}
    if sla.get("soglie"):
        out.append(Paragraph("SLA interni e regole di escalation", S["h2"]))
        rows = [[Paragraph("<b>Attività</b>", S["kv"]), Paragraph("<b>Soglia proposta</b>", S["kv"])]]
        for s in sla["soglie"]:
            rows.append([Paragraph(html.escape(str(s.get("attivita", ""))), S["kv"]),
                         Paragraph(html.escape(str(s.get("soglia_proposta", ""))), S["kv"])])
        t = Table(rows, colWidths=[ST.CONTENT_W - 52 * mm, 52 * mm], repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), ST.WARM),
                               ("GRID", (0, 0), (-1, -1), 0.4, ST.LINE),
                               ("TOPPADDING", (0, 0), (-1, -1), 4),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        out += [t, Paragraph(f'<font size="8" color="#8A7A55"><b>NOTA:</b> '
                             f'{html.escape(str(sla.get("nota", "")))}</font>', S["bullet"]),
                Spacer(1, 6)]

    req = pack.get("requisiti_funzionali") or []
    if req:
        out.append(Paragraph("Requisiti funzionali dello strumento", S["h2"]))
        out.append(ST.action_box(list(req), "Cosa deve saper fare", S))
        out.append(Spacer(1, 6))

    opz = pack.get("opzioni_tecnologiche") or {}
    if opz.get("opzioni"):
        out.append(Paragraph("Alternative tecnologiche — confronto", S["h2"]))
        if opz.get("nota"):
            out.append(Paragraph(f'<font size="8" color="#8A7A55">{html.escape(str(opz["nota"]))}'
                                 "</font>", S["bullet"]))
            out.append(Spacer(1, 3))
        for o in opz["opzioni"]:
            out.append(Paragraph(f"<b>{html.escape(str(o.get('opzione', '')))}</b>", S["h3"]))
            for label, key in (("Vantaggi", "vantaggi"), ("Svantaggi", "svantaggi")):
                for v in (o.get(key) or []):
                    tone = ST.GREEN if key == "vantaggi" else ST.RED
                    out.append(Paragraph(f'<font color="{ST.hx(tone)}">•</font> {_rich(v)}',
                                         S["bullet"]))
            detail = " · ".join(f"{_humanize(k)}: {o[k]}" for k in
                                ("complessita", "rischio_migrazione", "scalabilita") if o.get(k))
            if detail:
                out.append(Paragraph(f'<font size="8" color="#8A7A55">{html.escape(detail)}</font>',
                                     S["bullet"]))
            out.append(Spacer(1, 3))
        if opz.get("raccomandazione_condizionata"):
            out.append(_neutral_box([str(opz["raccomandazione_condizionata"])],
                                    "Raccomandazione condizionata", S, border=ST.GOLD_DK))
        out.append(Spacer(1, 6))

    piano = pack.get("piano_30_60_90") or []
    if piano:
        out.append(Paragraph("Piano 30-60-90 giorni", S["h2"]))
        for fase in piano:
            out.append(Paragraph(f"<b>{html.escape(str(fase.get('orizzonte', '')))}</b>", S["h3"]))
            for a in (fase.get("azioni") or []):
                out.append(Paragraph(f'<font color="{ST.hx(ST.GOLD_DK)}">•</font> {_rich(a)}',
                                     S["bullet"]))
        out.append(Spacer(1, 6))

    dati = pack.get("dati_da_raccogliere") or []
    if dati:
        out.append(_neutral_box([f"• {d}" for d in dati], "Dati da raccogliere "
                                "(per completare la misurazione)", S))
        out.append(Spacer(1, 4))
    return out


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

    # Dedup KPI (#5): un KPI (nome+valore) si descrive integralmente UNA volta;
    # nelle sezioni successive diventa un richiamo sintetico, non un'altra tabella.
    seen_kpi: set = set()

    def _dedup_kpi_items(items):
        fresh, dupes = [], []
        for it in items:
            key = (str(it.get("nome", "")).strip().lower(), str(it.get("valore", "")))
            if key[0] and key in seen_kpi:
                dupes.append(str(it.get("nome", "")))
            else:
                if key[0]:
                    seen_kpi.add(key)
                fresh.append(it)
        return fresh, dupes

    def _dupes_note(dupes):
        if dupes:
            body.append(Paragraph(
                f'<font size="8" color="#8A7A55">Già riportati sopra (non ripetuti): '
                f'{html.escape(", ".join(dupes))}.</font>', S["bullet"]))

    def render_value(v, level=0, skip_keys=()):
        # kpi_table PRIMA della heatmap: gli indici hanno {nome, valore, benchmark, semaforo}
        # e la heatmap stampa SOLO nome+colore → card colorate senza numero in un report
        # pagato (bug prod 8 lug). La heatmap resta per le liste solo-semaforo (mappa_aree).
        if _is_list_of_dicts(v) and _has(v, "valore", "benchmark"):
            fresh, dupes = _dedup_kpi_items(v)
            if fresh:
                body.append(ST.kpi_table(fresh, S)); body.append(Spacer(1, 4))
            _dupes_note(dupes)
            return
        if _is_list_of_dicts(v) and _has(v, "semaforo"):
            fresh, dupes = _dedup_kpi_items(v)
            if fresh:
                body.append(ST.heatmap(fresh, S)); body.append(Spacer(1, 4))
            _dupes_note(dupes)
            return
        # matrice priorità: criticità con severity/gravità + effort + ROI → tabella colorata
        if (_is_list_of_dicts(v) and _has(v, "severity", "gravita", "livello")
                and _has(v, "effort", "sforzo", "roi", "ritorno")):
            body.append(ST.severity_matrix(v, S)); body.append(Spacer(1, 4)); return
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
                # lista di SCALARI (anni: [2024], valori: [690000]) → inline sulla stessa
                # riga, NON heading+ricorsione (che li perdeva: heading 'Anni' vuoto,
                # 'Voce:' senza numeri — bug prod 8 lug).
                if isinstance(vv, list) and vv and all(
                        isinstance(x, (int, float, str)) and not isinstance(x, bool) for x in vv):
                    joined = ", ".join(_scalar_str(x) for x in vv)
                    body.append(Paragraph(f"<b>{html.escape(_humanize(k))}:</b> {_rich(joined)}", S["bullet"]))
                elif isinstance(vv, (dict, list)):
                    body.append(Paragraph(html.escape(_humanize(k)), S["h3"] if level else S["h2"]))
                    render_value(vv, level + 1, skip_keys)
                else:
                    body.append(Paragraph(f"<b>{html.escape(_humanize(k))}:</b> {_rich(_scalar_str(vv))}", S["bullet"]))
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
                        if isinstance(vv, list) and vv and all(
                                isinstance(x, (int, float, str)) and not isinstance(x, bool) for x in vv):
                            joined = ", ".join(_scalar_str(x) for x in vv)
                            body.append(Paragraph(f"<b>{html.escape(_humanize(kk))}:</b> {_rich(joined)}", S["bullet"]))
                        elif isinstance(vv, (dict, list)):
                            render_value(vv, level + 1, skip_keys)
                        else:
                            body.append(Paragraph(f"<b>{html.escape(_humanize(kk))}:</b> {_rich(_scalar_str(vv))}", S["bullet"]))
                    body.append(Spacer(1, 2))
                elif item is not None and not isinstance(item, (dict, list)):
                    # anche gli scalari nudi (numeri) si stampano — prima solo str → i
                    # numeri in lista sparivano silenziosamente
                    body.append(Paragraph(f'<font color="{ST.hx(ST.GOLD_DK)}">•</font> {_rich(_scalar_str(item))}', S["bullet"]))
        else:
            body.append(Paragraph(html.escape(str(v)), S["body"]))

    # sezioni top-level → divisori numerati (salta exec/score già nell'header)
    n = 1
    for key, val in deliverable.items():
        if key in _SKIP_KEYS or _effectively_empty(val):
            continue
        # score scalari già mostrati nella dashboard → salta se top-level int 'score'
        if isinstance(val, (int, float)) and "score" in key.lower():
            continue
        # VOCI-SHAPE (es. FiscoBoost, stesso schema di LegalBoost): OGNI voce è una SEZIONE
        # numerata col suo titolo reale, non tutte schiacciate sotto un unico "01 · Voci".
        if key == "voci" and _is_list_of_dicts(val) and _has(val, "titolo", "id"):
            for voce in val:
                # salta la voce SENZA testo reale: è il placeholder degradato (#89 no-dead-end
                # su una voce non prodotta) — contenuto/descrizioni vuoti, riempiti solo di
                # scaffolding enum (tipo='rischio', gravita='bassa', fonte='normattiva') e di un
                # id-codice. Altrimenti stampa un heading nudo ('02 · K2AI-2026 / Bassa rischio').
                if not _voce_has_text(voce):
                    continue
                titolo = str(voce.get("titolo") or voce.get("nome") or _humanize(str(voce.get("id", "Sezione"))))
                body.append(_Heading(f"{n:02d} · {html.escape(titolo)}", S["h1"], f"section-{n}")); n += 1
                body.append(Spacer(1, 2))
                if voce.get("contenuto"):
                    body.append(Paragraph(_rich(str(voce["contenuto"])), S["body"]))
                for sub in ("rischi", "rischi_opportunita", "azioni", "norme_citate", "fonti", "findings"):
                    if voce.get(sub):
                        if sub in ("azioni",) and isinstance(voce[sub], list) and all(isinstance(x, str) for x in voce[sub]):
                            body.append(ST.action_box(list(voce[sub]), "Azioni consigliate", S))
                        else:
                            render_value(voce[sub], 1)
                body.append(Spacer(1, 4))
            continue
        body.append(_Heading(f"{n:02d} · {_humanize(key)}", S["h1"], f"section-{n}")); n += 1
        body.append(Spacer(1, 2))
        # Sezioni-PROIEZIONE (scenari, forecast, sensitivity): i numeri sono per natura
        # ipotesi di scenario, non consuntivi — nota esplicita sotto il titolo, così un
        # 'ricavi proiettati 2.250.000' non si legge come dato verificato (QA prod 8 lug:
        # KPI/target di scenario presentati come quasi-definitivi).
        if re.search(r"scenari|proiezion|sensitivity|forecast|previsional", key.lower()):
            body.append(Paragraph(
                "<b>SCENARIO ASSUNTIVO</b> — <i>proiezioni indicative su ipotesi "
                "dichiarate (da confermare sui dati consuntivi): non sono dati verificati.</i>",
                S["bullet"]))
            body.append(Spacer(1, 2))
        render_value(val, 1)
        body.append(Spacer(1, 4))

    body += _consulting_blocks(deliverable, S)   # pacchetto operations (AS-IS/TO-BE/RACI…)
    _supp = _suppress_render(deliverable)         # Problema 6: sezioni dinamiche
    if "ops_blocks" not in _supp:
        body += _ops_blocks(deliverable, S)
    if "decision_board" not in _supp:
        body += _decision_board(deliverable, S)
    # Livello 3 — Decisione (review deliverable): evidenze/confidenza, matrice decisionale,
    # perché-non, raccomandazione finale, KPI governance, roadmap grafica. Componenti
    # DINAMICI: esistono solo se il pacchetto ha i dati (struttura per-caso, non template).
    from . import compose as CMP
    body += CMP.premium_back(deliverable, S)
    body += _appendix(citazioni, deliverable, blueprint, S)
    _build(pdf_path, cover_meta, report_name, body, deliverable, "professionale",
           has_citations=bool(citazioni), preliminare=preliminare)


def render_html(deliverable: dict, blueprint: dict, citazioni: list) -> str:
    import json
    return "<pre>" + html.escape(json.dumps(deliverable, ensure_ascii=False, indent=2)) + "</pre>"
