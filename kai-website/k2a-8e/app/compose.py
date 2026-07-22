"""COMPOSE — planner di struttura + componenti consulenziali premium (review deliverable).

Il report NON segue un template fisso: `build_report_plan` decide PRIMA la struttura
ottimale per il caso (quali componenti, in che ordine) in base ai dati realmente presenti
nel pacchetto consulenziale; poi i componenti la rendono. Due report di ambiti diversi
hanno strutture diverse — stessa identità grafica K2-AI.

Componenti (tutti grounded-by-construction: leggono SOLO dati già derivati dai motori,
niente numeri inventati; un componente senza dati sufficienti NON compare):
  - diagnosis_one_pager  (#2)  pagina-diagnosi CEO: tutto il report in <1 minuto
  - evidence_ledger      (#3)  FATTI / EVIDENZE / IPOTESI / RACCOMANDAZIONI + confidenza
  - decision_matrix      (#9)  matrice decisionale opzioni × costo/tempo/rischio + semafori
  - why_not_section      (#8)  perché NON abbiamo scelto le altre opzioni
  - final_recommendation (#7)  RACCOMANDAZIONE FINALE (consigliata/sconsigliata/condizioni)
  - kpi_governance       (#10) KPI dashboard operativa (target/frequenza/responsabile/azione)
  - timeline_page        (#11) timeline grafica 30-60-90 con milestone
"""
from __future__ import annotations

import html
import re

from reportlab.lib import colors
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle

from . import styling as ST
from .styling import html_escape

# ── estrazione dati dal pacchetto ────────────────────────────────────────────────────────


def _pack(deliverable) -> dict:
    p = (deliverable or {}).get("consulenza_operativa")
    return p if isinstance(p, dict) else {}


def _ins(deliverable) -> list:
    return [i for i in (_pack(deliverable).get("insight_derivati") or []) if isinstance(i, dict)]


def _diag(deliverable) -> dict:
    d = _pack(deliverable).get("ipotesi_diagnostica")
    return d if isinstance(d, dict) else {}


def _conf_options(deliverable) -> dict:
    c = _pack(deliverable).get("confronto_soluzioni")
    return c if isinstance(c, dict) else {}


def _recs(deliverable) -> list:
    return [r for r in (_pack(deliverable).get("raccomandazioni_operative") or [])
            if isinstance(r, dict)]


_CONF_IT = {"A": "Alta", "B": "Media", "C": "Bassa",
            "alta": "Alta", "media": "Media", "bassa": "Bassa"}


def _conf_it(level) -> str:
    return _CONF_IT.get(str(level or "").strip(), "Media")


def _first_sentence(text: str, maxlen: int = 240) -> str:
    t = str(text or "").strip()
    if not t:
        return ""
    m = re.split(r"(?<=[.!?])\s+", t, maxsplit=1)
    s = m[0] if m else t
    return s[:maxlen]


def _fmt_val(i: dict) -> str:
    from .render import _scalar_str  # lazy: evita import circolare a load-time
    v = _scalar_str(i.get("valore"))
    unita = str(i.get("unita") or "").strip()
    return f"{v} {unita}".strip()


def _recommended_letter(deliverable) -> str | None:
    """Lettera dell'opzione raccomandata, dedotta dalla conclusione motivata
    (le opzioni sono titolate 'A — …'). Deterministico; None se non deducibile."""
    conf = _conf_options(deliverable)
    concl = str(conf.get("conclusione_motivata") or "")
    m = re.search(r"\b([A-D])\b", concl)
    return m.group(1) if m else None


def _opt_letter(o: dict) -> str:
    m = re.match(r"\s*([A-D])\b", str(o.get("opzione") or ""))
    return m.group(1) if m else ""


# ── celle/box di supporto ────────────────────────────────────────────────────────────────


def _box(label: str, value: str, S, tone=None, sem: str | None = None) -> Table:
    """Cella della pagina-diagnosi: etichetta piccola + valore + semaforo opzionale."""
    tone = tone or ST.CARBON
    sem_txt = f"{ST.semaforo_dot(sem)} " if sem else ""
    inner = [
        Paragraph(f'<font name="{ST.F_MONO}" size="7.5" color="{ST.hx(ST.GOLD_DK)}">'
                  f'{html_escape(label).upper()}</font>', S["kv"]),
        Spacer(1, 3),
        Paragraph(f'{sem_txt}<font name="{ST.F_BODY}" size="9.3" color="{ST.hx(tone)}">'
                  f'{value}</font>', S["kv"]),
    ]
    t = Table([[inner]], colWidths=[(ST.CONTENT_W - 6) / 2])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.7, ST.LINE),
        ("LINEABOVE", (0, 0), (-1, 0), 2, ST.GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _ptable(headers: list, rows_html: list, S, widths=None) -> Table:
    """Tabella stile premium che accetta celle GIÀ formattate (markup incluso) — la
    ST.premium_table ri-escapa le celle e romperebbe grassetti/semafori."""
    head = [Paragraph(f'<font name="{ST.F_BOLD}" size="8.5" color="{ST.hx(ST.CARBON)}">'
                      f'{html_escape(h)}</font>', S["kv"]) for h in headers]
    data = [head] + [[Paragraph(c, S["kv"]) for c in r] for r in rows_html]
    n = len(headers)
    cw = widths or [ST.CONTENT_W / n] * n
    t = Table(data, colWidths=cw, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ST.WARM),
        ("LINEBELOW", (0, 0), (-1, 0), 1.0, ST.GOLD),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, ST.LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ST.WARM]),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _grid(cells: list, S) -> Table:
    rows, row = [], []
    for c in cells:
        row.append(c)
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        row.append("")
        rows.append(row)
    t = Table(rows, colWidths=[(ST.CONTENT_W - 6) / 2 + 3] * 2, hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                           ("TOPPADDING", (0, 0), (-1, -1), 3),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


# ── #2 · Pagina-diagnosi (CEO one-pager) ─────────────────────────────────────────────────


def diagnosis_one_pager(deliverable, S) -> list:
    """Tutto il report in meno di un minuto: problema, causa, sintomi, escluse,
    confidenza, decisione, urgenza, impatto, rischio — in box con semafori."""
    ins = _ins(deliverable)
    diag = _diag(deliverable)
    pack = _pack(deliverable)
    conf = _conf_options(deliverable)
    recs = _recs(deliverable)

    ipotesi = [i for i in (diag.get("ipotesi") or []) if isinstance(i, dict)]
    escluse = [e for e in (diag.get("ipotesi_escluse") or []) if isinstance(e, dict)]
    alti = [i for i in ins if str(i.get("gravita")) == "alta"]
    decisione = pack.get("decisione_sintesi") if isinstance(pack.get("decisione_sintesi"), dict) else {}

    # problema principale: insight più grave, o domanda decisionale
    problema = ""
    if alti:
        problema = f"{alti[0].get('titolo', '')}: {_fmt_val(alti[0])}"
    elif decisione.get("domanda_decisionale"):
        problema = str(decisione["domanda_decisionale"])
    elif ins:
        problema = f"{ins[0].get('titolo', '')}: {_fmt_val(ins[0])}"

    causa = ""
    if ipotesi:
        p = ipotesi[0].get("probabilita")
        causa = str(ipotesi[0].get("causa") or "")
        if isinstance(p, (int, float)):
            causa += f" (~{int(p)}%)"

    raccomandazione = (_first_sentence(conf.get("conclusione_motivata"))
                       or _first_sentence(decisione.get("sintesi"))
                       or (str(recs[0].get("titolo")) if recs else ""))

    # senza almeno problema + (causa o decisione) la pagina non ha senso → non compare
    if not problema or not (causa or raccomandazione):
        return []

    cells = [_box("Problema principale", html_escape(problema), S,
                  tone=ST.RED if alti else ST.CARBON)]
    if causa:
        conf_lv = _conf_it(ipotesi[0].get("confidence")) if ipotesi else "Media"
        cells.append(_box("Causa più probabile", html_escape(causa)
                          + f' <font size="7.5" color="#8A7A55">· confidenza {conf_lv}</font>', S))
    if ins:
        sintomi = " · ".join(str(i.get("titolo") or "") for i in ins[:3] if i.get("titolo"))
        if sintomi:
            cells.append(_box("Sintomi osservati", html_escape(sintomi), S))
    if escluse:
        esc = " · ".join(str(e.get("causa") or "") for e in escluse[:3] if e.get("causa"))
        cells.append(_box("Cause escluse", html_escape(esc), S, tone=ST.NEUTRAL))
    if raccomandazione:
        cells.append(_box("Decisione raccomandata", f"<b>{html_escape(raccomandazione)}</b>", S,
                          tone=ST.GOLD_DK))
    urgente = bool(pack.get("decisioni_entro_7_giorni"))
    cells.append(_box("Urgenza", "Alta — decisioni entro 7 giorni" if urgente
                      else "Ordinaria — pianificabile", S,
                      sem="rosso" if urgente else "verde"))
    imp = next((i for i in alti if "€" in str(i.get("unita") or "")),
               next((i for i in ins if "€" in str(i.get("unita") or "")), None))
    if imp:
        cells.append(_box("Impatto economico stimato",
                          html_escape(f"{imp.get('titolo', '')}: {_fmt_val(imp)}"), S))
    sem_risk = "rosso" if len(alti) >= 2 else ("giallo" if alti else "verde")
    cells.append(_box("Rischio complessivo",
                      {"rosso": "Alto", "giallo": "Medio", "verde": "Contenuto"}[sem_risk], S,
                      sem=sem_risk))

    return [ST.layer_band("executive", "Diagnosi in 60 secondi",
                          "la pagina che un CEO legge per prima", S),
            Spacer(1, 6), _grid(cells, S), Spacer(1, 8)]


# ── #3 · FATTI / EVIDENZE / IPOTESI / RACCOMANDAZIONI ────────────────────────────────────


def evidence_ledger(deliverable, S) -> list:
    ins = _ins(deliverable)
    diag = _diag(deliverable)
    recs = _recs(deliverable)
    ipotesi = [i for i in (diag.get("ipotesi") or []) if isinstance(i, dict)]
    if not ins and not ipotesi:
        return []
    out = [Paragraph("Fatti, evidenze e ipotesi — cosa sappiamo e con quanta certezza", S["h2"]),
           Paragraph("Ogni elemento porta il suo livello di confidenza: i FATTI sono dati "
                     "forniti o calcolati; le IPOTESI sono inferenze da verificare.", S["small"]),
           Spacer(1, 4)]

    fatti = [i for i in ins if str(i.get("confidence", "A")).upper() == "A"]
    evide = [i for i in ins if str(i.get("confidence", "")).upper() == "B"]

    def _line(mark: str, text: str, conf: str, tone) -> Paragraph:
        return Paragraph(
            f'<font color="{ST.hx(tone)}">{mark}</font>&nbsp;&nbsp;{text}'
            f'&nbsp;<font size="7.5" color="#8A7A55">· {conf}</font>', S["bullet"])

    if fatti:
        out.append(Paragraph("FATTI", S["h3"]))
        for i in fatti[:6]:
            out.append(_line("✓", f"<b>{html_escape(str(i.get('titolo', '')))}</b>: "
                             f"{html_escape(_fmt_val(i))}", "Alta", ST.GREEN))
        out.append(Spacer(1, 3))
    if evide:
        out.append(Paragraph("EVIDENZE DERIVATE", S["h3"]))
        for i in evide[:6]:
            out.append(_line("✓", f"<b>{html_escape(str(i.get('titolo', '')))}</b>: "
                             f"{html_escape(_fmt_val(i))}", "Media", ST.GOLD_DK))
        out.append(Spacer(1, 3))
    if ipotesi:
        out.append(Paragraph("IPOTESI", S["h3"]))
        for i in ipotesi[:4]:
            p = i.get("probabilita")
            ptxt = f" (~{int(p)}%)" if isinstance(p, (int, float)) else ""
            out.append(_line("◐", f"{html_escape(str(i.get('causa', '')))}{ptxt}",
                             _conf_it(i.get("confidence")), ST.AMBER))
        out.append(Spacer(1, 3))
    # IPOTESI ANCORA DA VERIFICARE (review #6): ciò che serve per confermare/escludere —
    # dai dati mancanti dichiarati e dal singolo dato critico della diagnosi.
    pack = _pack(deliverable)
    da_verificare = list(pack.get("dati_da_raccogliere") or [])
    if diag.get("manca"):
        da_verificare = [str(diag["manca"])] + da_verificare
    da_verificare = [d for d in da_verificare if str(d).strip()]
    if da_verificare:
        out.append(Paragraph("IPOTESI ANCORA DA VERIFICARE", S["h3"]))
        for d in da_verificare[:5]:
            out.append(_line("?", html_escape(str(d)), "da confermare", ST.NEUTRAL))
        out.append(Spacer(1, 3))
    if recs:
        out.append(Paragraph("RACCOMANDAZIONI", S["h3"]))
        for r in recs[:4]:
            out.append(_line("✓", f"<b>{html_escape(str(r.get('titolo', '')))}</b>",
                             "dalla diagnosi", ST.GOLD_DK))
        out.append(Spacer(1, 3))
    # INCERTEZZA DICHIARATA (review #7): diagnosi PRELIMINARE quando restano ipotesi aperte
    # o dati mancanti — mai fingere precisione.
    if da_verificare or any(str(i.get("s", "aperta")).lower() == "aperta" for i in ipotesi):
        out.append(ST.insight_box(
            "Valutazione basata sulle informazioni raccolte in consulenza: è una DIAGNOSI "
            "PRELIMINARE. Alcune ipotesi potranno essere confermate, ridimensionate o escluse "
            "una volta disponibili i dati economici e operativi ancora da raccogliere.",
            "Diagnosi preliminare", S))
    out.append(Spacer(1, 8))
    return out


# ── #9 · Matrice decisionale con semafori ────────────────────────────────────────────────

_RISK_SEM = (("alto", "rosso"), ("critic", "rosso"), ("medio", "giallo"), ("median", "giallo"),
             ("basso", "verde"), ("contenut", "verde"), ("nessun", "verde"))


def _risk_sem(text: str) -> str:
    t = str(text or "").lower()
    for k, sem in _RISK_SEM:
        if k in t:
            return sem
    return "giallo"


def decision_matrix(deliverable, S) -> list:
    conf = _conf_options(deliverable)
    opzioni = [o for o in (conf.get("opzioni") or []) if isinstance(o, dict)]
    if len(opzioni) < 2:
        return []
    racc = _recommended_letter(deliverable)
    out = [Paragraph("Matrice decisionale", S["h2"]),
           Paragraph("Le opzioni a confronto su costo, tempo e rischio. La decisione "
                     "raccomandata è motivata nella sezione successiva.", S["small"]),
           Spacer(1, 4)]
    headers = ["Opzione", "Costi", "Tempi", "Rischio", "Complessità", "Decisione"]
    rows = []
    for o in opzioni:
        letter = _opt_letter(o)
        if racc and letter == racc:
            dec = f"{ST.semaforo_dot('verde')} <b>Consigliata</b>"
        elif "non intervenire" in str(o.get("opzione", "")).lower():
            dec = f"{ST.semaforo_dot('giallo')} Riserva"
        else:
            dec = f"{ST.semaforo_dot('giallo')} Alternativa"
        rows.append([
            f"<b>{html_escape(str(o.get('opzione', ''))[:60])}</b>",
            html_escape(str(o.get("costi", ""))[:70]),
            html_escape(str(o.get("tempi", ""))[:45]),
            f"{ST.semaforo_dot(_risk_sem(o.get('rischi')))} "
            + html_escape(str(o.get("rischi", ""))[:60]),
            html_escape(str(o.get("complessita", ""))[:30]),
            dec,
        ])
    w = ST.CONTENT_W
    out.append(_ptable(headers, rows, S,
                       widths=[w * .24, w * .20, w * .13, w * .20, w * .10, w * .13]))
    out.append(Spacer(1, 8))
    return out


# ── #8 · Perché NON le altre opzioni ─────────────────────────────────────────────────────


def why_not_section(deliverable, S) -> list:
    conf = _conf_options(deliverable)
    opzioni = [o for o in (conf.get("opzioni") or []) if isinstance(o, dict)]
    racc = _recommended_letter(deliverable)
    scartate = [o for o in opzioni if o.get("quando_evitarla")
                and (not racc or _opt_letter(o) != racc)]
    perche_non = [r.get("perche_non_altre") for r in _recs(deliverable) if r.get("perche_non_altre")]
    if not scartate and not perche_non:
        return []
    out = [Paragraph("Perché non abbiamo scelto le altre opzioni", S["h2"]),
           Paragraph("Un'opzione scartata senza motivo è una domanda aperta: qui il perché.",
                     S["small"]), Spacer(1, 4)]
    for o in scartate[:4]:
        out.append(Paragraph(f"<b>Perché non «{html_escape(str(o.get('opzione', ''))[:70])}»:</b> "
                             f"{html_escape(str(o.get('quando_evitarla', '')))}", S["bullet"]))
        out.append(Spacer(1, 2))
    for t in perche_non[:3]:
        out.append(Paragraph(f'<font color="{ST.hx(ST.GOLD_DK)}">•</font> '
                             f"{html_escape(str(t))}", S["bullet"]))
    out.append(Spacer(1, 8))
    return out


# ── #7 · RACCOMANDAZIONE FINALE ──────────────────────────────────────────────────────────


def final_recommendation(deliverable, S) -> list:
    pack = _pack(deliverable)
    conf = _conf_options(deliverable)
    recs = _recs(deliverable)
    diag = _diag(deliverable)
    decisione = pack.get("decisione_sintesi") if isinstance(pack.get("decisione_sintesi"), dict) else {}

    consigliata = (str(conf.get("conclusione_motivata") or "").strip()
                   or str(decisione.get("sintesi") or "").strip())
    if not consigliata and recs:
        r0 = recs[0]
        consigliata = str(r0.get("titolo") or "")
        if r0.get("perche"):
            consigliata += f" — {r0['perche']}"
    if not consigliata:
        return []

    out = [Paragraph("Raccomandazione finale", S["h2"]), Spacer(1, 3),
           ST.insight_box(consigliata, "Decisione consigliata", S), Spacer(1, 5)]

    racc = _recommended_letter(deliverable)
    opzioni = [o for o in (conf.get("opzioni") or []) if isinstance(o, dict)]
    sconsigliate = [o for o in opzioni if racc and _opt_letter(o) != racc and o.get("quando_evitarla")]
    if sconsigliate:
        out.append(Paragraph(f"<b>Decisione sconsigliata (oggi):</b> "
                             f"{html_escape(str(sconsigliate[0].get('opzione', ''))[:70])} — "
                             f"{html_escape(str(sconsigliate[0].get('quando_evitarla', '')))}",
                             S["bullet"]))
        out.append(Spacer(1, 3))

    # condizioni per cambiare decisione — derivate da dati mancanti + ipotesi escluse
    condizioni = []
    for d in (pack.get("dati_da_raccogliere") or [])[:3]:
        condizioni.append(f"i dati su «{d}» raccontassero un quadro diverso")
    for e in (diag.get("ipotesi_escluse") or [])[:2]:
        if isinstance(e, dict) and e.get("causa"):
            condizioni.append(f"emergessero nuove evidenze su «{e['causa']}»")
    if condizioni:
        out.append(Paragraph("<b>Cosa ci farebbe cambiare raccomandazione:</b> se "
                             + "; se ".join(html_escape(c) for c in condizioni[:4]) + ".",
                             S["bullet"]))
        out.append(Spacer(1, 3))

    racc_opt = next((o for o in opzioni if racc and _opt_letter(o) == racc), None)
    if racc_opt and racc_opt.get("rischi"):
        out.append(Paragraph(f"<b>Rischi residui della scelta:</b> "
                             f"{html_escape(str(racc_opt['rischi']))}", S["bullet"]))
        out.append(Spacer(1, 3))

    immediate = (pack.get("decisioni_entro_7_giorni")
                 or next((f.get("azioni") for f in (pack.get("piano_30_60_90") or [])
                          if isinstance(f, dict) and f.get("azioni")), []))
    if immediate:
        out.append(ST.action_box(list(immediate)[:4], "Azioni immediate", S))
    out.append(Spacer(1, 8))
    return out


# ── #10 · KPI governance (dashboard operativa) ───────────────────────────────────────────


def kpi_governance(deliverable, S) -> list:
    kpis = [k for k in (_pack(deliverable).get("kpi_da_misurare") or []) if isinstance(k, dict)]
    if not kpis:
        return []
    out = [Paragraph("KPI da presidiare — governance operativa", S["h2"]),
           Paragraph("Responsabile e target sono campi da assegnare in azienda: il report "
                     "prepara la struttura, la governance la riempie.", S["small"]),
           Spacer(1, 4)]
    headers = ["KPI", "Perché misurarlo", "Frequenza", "Responsabile", "Azione se fuori soglia"]
    rows = []
    for k in kpis[:8]:
        rows.append([
            f"<b>{html_escape(str(k.get('kpi', ''))[:55])}</b>",
            html_escape(str(k.get("perche", ""))[:110]),
            html_escape(str(k.get("frequenza") or "Settimanale")),
            html_escape(str(k.get("responsabile") or "Da assegnare")),
            html_escape(str(k.get("azione_fuori_soglia") or "Riesame della diagnosi")),
        ])
    w = ST.CONTENT_W
    out.append(_ptable(headers, rows, S,
                       widths=[w * .20, w * .34, w * .12, w * .14, w * .20]))
    out.append(Spacer(1, 8))
    return out


# ── #11 · Timeline grafica 30-60-90 ──────────────────────────────────────────────────────


def timeline_page(deliverable, S) -> list:
    piano = [f for f in (_pack(deliverable).get("piano_30_60_90") or []) if isinstance(f, dict)]
    fasi = [f for f in piano if f.get("azioni")]
    if not fasi:
        return []
    out = [Paragraph("Roadmap di attuazione", S["h2"]), Spacer(1, 4)]
    cards = [{"fase": str(f.get("orizzonte") or ""),
              "descrizione": "; ".join(map(str, (f.get("azioni") or [])[:2]))} for f in fasi[:4]]
    out.append(ST.roadmap(cards, S))
    out.append(Spacer(1, 5))
    items = []
    for f in fasi:
        for a in (f.get("azioni") or []):
            items.append({"orizzonte": str(f.get("orizzonte") or ""), "azione": str(a)})
    out += ST.timeline_ops(items, S)
    out.append(Spacer(1, 8))
    return out


# ── PLANNER + assemblaggio ───────────────────────────────────────────────────────────────

_COMPONENTS = (
    ("diagnosis_one_pager", diagnosis_one_pager),
    ("evidence_ledger", evidence_ledger),
    ("decision_matrix", decision_matrix),
    ("why_not", why_not_section),
    ("final_recommendation", final_recommendation),
    ("kpi_governance", kpi_governance),
    ("timeline", timeline_page),
)


def build_report_plan(deliverable) -> dict:
    """La struttura del report PRIMA di comporlo: quali componenti premium hanno dati
    sufficienti per esistere in QUESTO caso. Introspezione per test/telemetria."""
    S = ST.styles()
    plan = {}
    for name, fn in _COMPONENTS:
        try:
            plan[name] = bool(fn(deliverable, S))
        except Exception:
            plan[name] = False
    plan["_tipo"] = str(_pack(deliverable).get("_tipo") or "")
    return plan


def premium_front(deliverable, S) -> list:
    """Componenti di apertura (subito prima dell'Executive Summary): pagina-diagnosi."""
    try:
        out = diagnosis_one_pager(deliverable, S)
        return out + [PageBreak()] if out else []
    except Exception:
        return []


def premium_back(deliverable, S) -> list:
    """Componenti decisionali di chiusura (dopo l'analisi, prima dell'appendice):
    evidenze/confidenza → matrice decisionale → perché-non → raccomandazione finale →
    KPI governance → roadmap. Ogni componente esiste solo se i dati lo sostengono."""
    out: list = []
    try:
        blocks = []
        for fn in (evidence_ledger, decision_matrix, why_not_section,
                   final_recommendation, kpi_governance, timeline_page):
            try:
                blocks += fn(deliverable, S)
            except Exception:
                continue
        if blocks:
            out = [PageBreak(),
                   ST.layer_band("decision", "Livello 3 — Decisione",
                                 "matrice, raccomandazione e governance", S),
                   Spacer(1, 6)] + blocks
    except Exception:
        return []
    return out
