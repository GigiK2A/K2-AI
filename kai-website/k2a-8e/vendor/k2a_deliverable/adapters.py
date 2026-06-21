"""ADAPTER di formato — documento reale → `instance` dict per il linter.

DEPENDENCY-FREE a runtime: docx via stdlib `zipfile`+`xml.etree`, html via stdlib
`html.parser`. `python-docx` NON è usato qui (solo dev/test per autorare le fixture).

L'instance prodotto è lo stesso dict consumato da `linter.lint` (vedi linter.py
docstring). L'adapter è uno strato a monte: non tocca gli `_impl` esistenti.

------------------------------------------------------------------------------
CONVENZIONE MARKER HTML (contratto che l'output reale del Check dovrà rispettare)
------------------------------------------------------------------------------
Per rendere deterministica l'estrazione dall'HTML single-page del Check, il
template di output deve marcare gli elementi semantici così (backlog #21b-res:
allineare il generatore reale a questi marker):

  - gauge score 0-100 .... elemento con  data-k2a="gauge"   (o class contiene "k2a-gauge")
  - card semaforo ........ ogni card con  class="... semaforo-card ..."
  - criticità ............ ogni blocco con class="... criticita ..."
  - CTA tier successivo .. elemento con  data-k2a="cta"      (o heading "prossimo passo")
  - disclaimer ........... elemento con  data-k2a="disclaimer"

Le dipendenze esterne (src/href http(s) verso host) sono vietate dal vincolo
"nessuna dipendenza esterna": l'adapter le rileva e popola `dipendenze_esterne`.
"""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
import zipfile
from html.parser import HTMLParser

# ------------------------------------------------------------------ namespaces docx
_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
_NS = {"w": _W, "wp": _WP}


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (text or "").strip().lower())
    return s.strip("_") or "voce"


# --------------------------------------------- mapping id canonico (#21b-res)
# Attivo SOLO quando il blueprint dichiara `validazione_strict: true` (es.
# FinanceBoost). Per gli altri blueprint l'id resta None (comportamento legacy:
# R06/R07 "non_valutata", guard D-025). Sotto strict invece ogni heading reale
# viene mappato all'id canonico della voce di blueprint piu' affine, cosi' che
# voci mancanti / EXTRA / DUPLICATE diventino rilevabili sul file reale.

def _norm_heading(text: str) -> str:
    """minuscolo, senza accenti, spazi compattati, senza numerazione di testa."""
    import unicodedata
    s = unicodedata.normalize("NFKD", str(text or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\s+", " ", s).strip().lower()
    # toglie "01 ", "1. ", "1) ", "1 - ", "1: " in testa
    s = re.sub(r"^\d+\s*[\.\)\-:–—]?\s*", "", s)
    return s


def _canonical_id(heading: str, bp_voci: list) -> str | None:
    """Ritorna l'id della voce di blueprint che il `heading` reale rappresenta,
    oppure None se nessuna corrisponde con sufficiente confidenza."""
    h = _norm_heading(heading)
    if not h:
        return None
    h_words = [w for w in re.split(r"[^a-z0-9]+", h) if len(w) >= 4]
    best = None
    for v in bp_voci:
        vid = v.get("id")
        if not vid:
            continue
        for cand in (_norm_heading(v.get("titolo", "")), _norm_heading(str(vid).replace("_", " "))):
            if not cand:
                continue
            if h == cand:
                return vid  # match esatto: priorita' massima
            c_words = [w for w in re.split(r"[^a-z0-9]+", cand) if len(w) >= 4]
            # tutte le parole significative del titolo nell'heading (o viceversa)
            if c_words and all(w in h for w in c_words):
                best = best or vid
            elif h_words and all(w in cand for w in h_words):
                best = best or vid
    return best


# ------------------------------------------------------------------ euristica prezzi

# pattern importo: €1.999 / EUR 1.999 / 1.999 € / 299 EUR ...
_PRICE_AMOUNT = re.compile(r"(?:€|eur|euro)\s?[0-9][0-9\.\, ]*|[0-9][0-9\.\, ]*\s?(?:€|eur|euro)", re.I)
# contesto pricing-servizio (NON cifre di bilancio)
_PRICE_CTX = re.compile(
    r"\b(mese|mensile|abbonament\w*|pacchett\w*|prezzo|tariff\w*|consulenz\w*|"
    r"call|retainer|da\s?€|a partire da|listino|canone|one[- ]?shot)\b",
    re.I,
)


def _is_pricing_text(text: str) -> bool:
    """True se il testo contiene un importo € in contesto pricing-servizio.
    Euristica RISTRETTA: serve sia un importo sia una keyword di pricing vicina,
    così le cifre di bilancio (€650.375 in tabella/contesto contabile) non contano.
    """
    if not text:
        return False
    for m in _PRICE_AMOUNT.finditer(text):
        a, b = m.start(), m.end()
        window = text[max(0, a - 60): b + 60]
        if _PRICE_CTX.search(window):
            return True
    return False


# ============================================================ DOCX → instance

def _docx_text(el: ET.Element) -> str:
    return "".join(t.text or "" for t in el.iter(f"{{{_W}}}t"))


def _heading_level(p: ET.Element) -> int | None:
    """ritorna 1/2 se il paragrafo usa stile Heading1/Heading2, altrimenti None."""
    ppr = p.find(f"{{{_W}}}pPr")
    if ppr is None:
        return None
    st = ppr.find(f"{{{_W}}}pStyle")
    if st is None:
        return None
    val = st.get(f"{{{_W}}}val", "") or ""
    m = re.match(r"(?:Heading|Titolo)\s*([12])$", val, re.I)
    return int(m.group(1)) if m else None


def docx_to_instance(path: str, twin_json_path: str | None = None, blueprint: dict | None = None) -> dict:
    """Estrae un instance dict da un .docx reale (stdlib only)."""
    with zipfile.ZipFile(path) as z:
        doc_xml = z.read("word/document.xml")
        media = [n for n in z.namelist() if n.startswith("word/media/")]
        charts = [n for n in z.namelist() if n.startswith("word/charts/") and n.endswith(".xml")]

    root = ET.fromstring(doc_xml)
    body = root.find(f"{{{_W}}}body")
    body = body if body is not None else root

    # iterazione lineare dei figli del body: paragrafi (con heading) e tabelle
    voci: list[dict] = []
    tabelle: list[str] = []
    elementi_grafici: list[str] = []
    cur: dict | None = None
    last_heading_text = ""
    body_text_parts: list[str] = []  # testo FUORI dalle tabelle (per prezzi)

    for child in list(body):
        tag = child.tag.split("}")[-1]
        if tag == "p":
            lvl = _heading_level(child)
            txt = _docx_text(child)
            # drawing dentro il paragrafo → grafico
            for dr in child.iter(f"{{{_W}}}drawing"):
                label = None
                docpr = dr.find(f".//{{{_WP}}}docPr")
                if docpr is not None:
                    label = docpr.get("title") or docpr.get("descr")
                elementi_grafici.append(label or last_heading_text or "grafico")
            if lvl in (1, 2):
                last_heading_text = txt
                cur = {
                    # id=None: niente canonicalizzazione euristica (D-025; mapping → #21b-res).
                    # R01/R04 risultano "non_valutata" finché un mapping non fornisce id canonici.
                    "id": None,
                    "titolo": txt,
                    "contenuti": [],
                    "cta": bool(re.search(r"prossimo\s+passo|\bcall\b|prenota", txt, re.I)),
                    "pagine": None,  # page-count non disponibile (no renderer) -> R02/R03 saltate
                }
                voci.append(cur)
            else:
                if txt:
                    body_text_parts.append(txt)
                    if cur is not None:
                        cur["contenuti"].append(txt)
                        if re.search(r"prossimo\s+passo|\bcall\b|prenota|call gratuita", txt, re.I):
                            cur["cta"] = True
        elif tag == "tbl":
            # label = heading più vicino precedente, fallback = prima cella
            label = last_heading_text
            if not label:
                first_t = child.find(f".//{{{_W}}}t")
                label = (first_t.text if first_t is not None else "") or "tabella"
            tabelle.append(label)

    # grafici da media/charts (parti referenziate non inline)
    for _ in charts:
        elementi_grafici.append(last_heading_text or "grafico")
    # immagini in media non già contate come drawing: usa il numero di media come floor
    if len(media) > sum(1 for _ in elementi_grafici):
        for _ in range(len(media) - len(elementi_grafici)):
            elementi_grafici.append("immagine")

    # mapping id canonico (#21b-res): SOLO sotto `validazione_strict`. Le voci non
    # mappate prendono un id-sentinella "__extra__:<slug>" cosi' il linter le segnala
    # come voci extra (struttura libera) invece di saltare R06/R07.
    if blueprint and blueprint.get("validazione_strict"):
        bp_voci = blueprint.get("voci", []) or []
        for v in voci:
            cid = _canonical_id(v.get("titolo", ""), bp_voci)
            v["id"] = cid if cid else "__extra__:" + _slug(v.get("titolo", ""))

    body_text = "\n".join(body_text_parts)
    ha_disclaimer = bool(
        re.search(r"disclaimer|documento\s+.*\bAI\b|richiede\s+(?:la\s+)?firma|non sostituisce", body_text, re.I)
    )
    ha_cta = any(v.get("cta") for v in voci)
    prezzi_hardcoded = _is_pricing_text(body_text)

    json_output_valido = _validate_twin(twin_json_path, blueprint)

    return {
        "formato": "docx",
        "voci": voci,
        "tabelle": tabelle,
        "elementi_grafici": elementi_grafici,
        # artefatti=None: l'estrazione mono-file non può attestare il bundle (xlsx/dashboard/json
        # gemelli) -> R06 "artefatti" risulta non_valutata (guard D-025). #21b-res: manifest multi-file.
        "artefatti": None,
        "ha_disclaimer": ha_disclaimer,
        "ha_cta": ha_cta,
        "prezzi_hardcoded": prezzi_hardcoded,
        "peso_kb": int(os.path.getsize(path) / 1024),
        "json_output_valido": json_output_valido,
        # pagine: app.xml inaffidabile + nessun renderer -> None (R02/R03 spente). #21b backlog.
        "pagine": None,
    }


def _validate_twin(twin_json_path: str | None, blueprint: dict | None):
    """Valida il twin JSON vs blueprint.contratto_dati. None se non valutabile."""
    if not twin_json_path or not blueprint:
        return None
    contratto = blueprint.get("contratto_dati")
    if not contratto:
        return None
    # contratto_dati è un path relativo alla cartella blueprints (es.
    # 'analisi-bilancio-pmi/schemas/output-schema.json'); risolvibile via K2A_BLUEPRINTS_DIR.
    import json
    from pathlib import Path

    base = os.environ.get("K2A_BLUEPRINTS_DIR")
    base = Path(base).expanduser() if base else Path.home() / "Code" / "k2a-skills" / "blueprints"
    schema_path = (base / contratto)
    if not schema_path.is_file():
        # fallback: risali alla root del repo skill (blueprints/..)
        alt = base.parent / contratto
        schema_path = alt if alt.is_file() else schema_path
    if not schema_path.is_file():
        return None
    try:
        from jsonschema import Draft202012Validator
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        data = json.loads(Path(twin_json_path).read_text(encoding="utf-8"))
        errs = list(Draft202012Validator(schema).iter_errors(data))
        return not errs
    except Exception:
        return False


# ============================================================ HTML → instance

class _HtmlExtract(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.headings: list[tuple[str, list[str]]] = []  # (tag, text-parts)
        self._cur_h: str | None = None
        self.gauge = False
        self.n_semaforo = 0
        self.n_criticita = 0
        self.cta = False
        self.disclaimer = False
        self.ext_deps = False
        self.text_parts: list[str] = []
        self._host_re = re.compile(r"^https?://", re.I)

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        cls = (d.get("class") or "").lower()
        dk = (d.get("data-k2a") or "").lower()
        if tag in ("h1", "h2"):
            self._cur_h = tag
            self.headings.append((tag, []))
        if dk == "gauge" or "k2a-gauge" in cls:
            self.gauge = True
        if "semaforo-card" in cls:
            self.n_semaforo += 1
        if "criticita" in cls:
            self.n_criticita += 1
        if dk == "cta":
            self.cta = True
        if dk == "disclaimer":
            self.disclaimer = True
        for attr in ("src", "href"):
            v = d.get(attr)
            if v and self._host_re.match(v):
                self.ext_deps = True

    def handle_endtag(self, tag):
        if tag in ("h1", "h2"):
            self._cur_h = None

    def handle_data(self, data):
        s = data.strip()
        if not s:
            return
        self.text_parts.append(s)
        if self.headings and self._cur_h:
            self.headings[-1][1].append(s)


def html_to_instance(path: str) -> dict:
    html = open(path, encoding="utf-8").read()
    p = _HtmlExtract()
    p.feed(html)

    voci = []
    for tag, parts in p.headings:
        title = " ".join(parts).strip()
        if title:
            # id=None come per il docx: R01/R04 "non_valutata" senza mapping canonico (D-025).
            voci.append({"id": None, "titolo": title, "contenuti": [], "cta": False, "pagine": None})

    full_text = " ".join(p.text_parts)
    ha_disclaimer = p.disclaimer or bool(re.search(r"disclaimer|non sostituisce", full_text, re.I))
    ha_cta = p.cta or bool(re.search(r"prossimo\s+passo|prenota|call gratuita", full_text, re.I))

    return {
        "formato": "html-single-page",
        "voci": voci,
        "peso_kb": int(os.path.getsize(path) / 1024),
        "dipendenze_esterne": p.ext_deps,
        "ha_gauge": p.gauge,
        "n_card_semaforo": p.n_semaforo,
        "n_criticita": p.n_criticita,
        "ha_cta": ha_cta,
        "ha_disclaimer": ha_disclaimer,
        "prezzi_hardcoded": _is_pricing_text(full_text),
        "pagine": None,
    }
