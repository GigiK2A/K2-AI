"""Resolver Normattiva — il ROUTE dei fatti C2 normativi (handoff Luca §3).

Interroga il corpus FTS5 di Luca (`normattiva.db`: 62.491 articoli + 41.696 norme
integrali) per dare al motore 8e le CITAZIONI VERBATIM che il Grounding Contract
pretende sui Boost normativi (Safety/Build/TLC/Agevolazioni/Legal/Fisco). Senza
questo, il ROUTE di quei fatti degrada a "da verificare" (onesto ma vuoto) e il CAGE
C2 (`norma_non_citata`, §2) non ha una fonte contro cui grounddare.

Deterministico, read-only, no LLM. Il path del DB viene da env `NORMATTIVA_DB_PATH`;
se l'env manca o il file non c'è → `available()` è False e il motore degrada come
prima (nessun crash, nessuna invenzione). Lo schema è quello del server MCP di Luca:
  chunks(id, file, testo, source) + chunks_fts(file, testo)  [FTS5]
Il nome-file codifica gli estremi: `decreto_legislativo_2001_231_art_25-septies.md`.
"""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

_DB_ENV = "NORMATTIVA_DB_PATH"

# tipo (dal nome-file) → label di citazione. Il corpus usa sia forme estese sia
# abbreviate (es. 'decreto_presidente_repubblica' e 'dpr'): mappate entrambe. I tipi
# non mappati si umanizzano (la label è cosmetica; gli estremi restano corretti).
_TIPO_LABEL = {
    "legge": "L.", "l": "L.",
    "decreto_legislativo": "D.Lgs", "dlgs": "D.Lgs", "d_lgs": "D.Lgs",
    "decreto_legge": "D.L.", "dl": "D.L.",
    "decreto_ministeriale": "D.M.", "dm": "D.M.",
    "decreto_presidente_repubblica": "D.P.R.", "dpr": "D.P.R.",
    "decreto_presidente_consiglio_ministri": "D.P.C.M.", "dpcm": "D.P.C.M.",
    "regio_decreto": "R.D.", "rd": "R.D.",
    "regio_decreto_legge": "R.D.L.", "rdl": "R.D.L.",
    "codice": "Codice", "costituzione": "Cost.",
}

# nome-file → estremi: <tipo>_<anno>_<numero>_art_<articolo>.md
_FN_RE = re.compile(
    r"^(?P<tipo>[a-z_]+?)_(?P<anno>\d{4})_(?P<numero>[0-9A-Za-z-]+?)_art_(?P<articolo>[0-9A-Za-z._-]+)\.md$"
)


def _db_path() -> Optional[Path]:
    p = os.environ.get(_DB_ENV)
    if not p:
        return None
    path = Path(p)
    return path if path.is_file() else None


# SUPPLEMENTO bundlato (8 lug 2026): DB piccolo (~3MB) impacchettato NELL'IMMAGINE con le
# norme aggiunte che NON sono ancora nel corpus canonico su volume (es. L.633/1941 diritto
# d'autore + alcuni DL). Serve a portare quelle norme in prod SENZA ri-seedare 1.8GB sul
# volume (che richiederebbe accesso al release canonico). find_by_estremi interroga PRIMA
# il corpus principale, POI il supplemento. Quando il corpus canonico verrà ri-seedato col
# completo, il supplemento diventa ridondante (nessun doppio: si ferma al primo hit).
_SUPP_PATH = Path(__file__).resolve().parent.parent / "data" / "normattiva_supplement.db"


def _supp_path() -> Optional[Path]:
    return _SUPP_PATH if _SUPP_PATH.is_file() else None


def available() -> bool:
    """True se il corpus PRINCIPALE è raggiungibile (semantica storica: in prod il volume
    c'è sempre). Il supplemento bundlato NON conta qui — è un fallback interno a
    find_by_estremi, non un corpus autonomo — così `available()` resta l'indicatore del
    corpus completo e i chiamanti a monte non cambiano comportamento."""
    return _db_path() is not None


def _estremi(filename: str) -> dict:
    name = os.path.basename(str(filename))
    m = _FN_RE.match(name)
    if not m:
        return {"file": name}
    d = m.groupdict()
    return {"tipo": d["tipo"], "anno": int(d["anno"]), "numero": d["numero"],
            "articolo": d["articolo"], "file": name}


def citazione(estremi: dict) -> str:
    """Estremi → stringa di citazione leggibile (es. 'D.Lgs 231/2001, art. 25-septies')."""
    tipo = estremi.get("tipo")
    if not tipo:
        return str(estremi.get("file", "")).removesuffix(".md").replace("_", " ")
    label = _TIPO_LABEL.get(tipo, tipo.replace("_", " ").capitalize())
    numero, anno = estremi.get("numero"), estremi.get("anno")
    base = f"{label} {numero}/{anno}".strip() if numero and anno else label
    art = estremi.get("articolo")
    return f"{base}, art. {art}" if art else base


def _fts_query(query: str) -> str:
    """Senza operatori espliciti, unisce le parole in AND (come il server di Luca)."""
    q = (query or "").strip()
    if not q:
        return q
    if not re.search(r'["*^]|\bAND\b|\bOR\b|\bNOT\b|NEAR\(', q):
        tokens = [t for t in re.split(r"\s+", q) if t]
        q = " AND ".join(tokens) if tokens else q
    return q


def search(query: str, limit: int = 5) -> list[dict]:
    """FTS5 sul corpus → lista di articoli con testo VERBATIM + estremi + citazione.

    Ritorna [] se il corpus non è disponibile o la query FTS è invalida (degrado
    onesto: nessun crash, nessun fatto inventato). Ogni voce:
    {tipo, anno, numero, articolo, file, citazione, snippet, testo, rank}.
    """
    db = _db_path()
    if not db or not query or not query.strip():
        return []
    q = _fts_query(query)
    try:
        con = sqlite3.connect(f"file:{db}?immutable=1", uri=True, timeout=20)
    except sqlite3.Error:
        return []
    try:
        con.execute("PRAGMA busy_timeout=20000")
        rows = con.execute(
            "SELECT file, testo, snippet(chunks_fts, 1, '«', '»', '…', 16), rank "
            "FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY rank LIMIT ?",
            (q, max(1, int(limit))),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()

    out: list[dict] = []
    for file, testo, snippet, rank in rows:
        e = _estremi(file)
        out.append({**e, "citazione": citazione(e), "snippet": snippet,
                    "testo": testo, "rank": round(rank, 4) if rank is not None else None})
    return out


# ── Lookup per ESTREMI (anno, numero) — per VERIFICARE un riferimento di legge ──
# Il nome-file codifica anno e numero; il tokenizer FTS5 spezza su '_', quindi una
# MATCH column-scoped `file:<anno> AND file:<numero>` usa l'indice FTS (~0.5s) invece
# di uno scan LIKE su 62k righe (~5 min). Niente indice extra sul DB di Luca.

# tipo canonico → varianti del prefisso-file nel corpus (forme estese E abbreviate).
# NB legge↔decreto_legislativo (8 lug 2026): lo scraper del corpus (scarica_articoli.py)
# salva i DECRETI LEGISLATIVI col prefisso file 'legge_YYYY_N' (convenzione voluta: mappa
# `"decreto.legislativo": "legge"`). Così un D.Lgs citato ('D.Lgs 206/2005', Codice del
# Consumo) NON si agganciava al chunk 'legge_2005_206' → find_by_estremi rifiutava sul tipo
# → grounding REFUSE sui parere legali (bug prod). I due tipi sono resi RECIPROCAMENTE
# compatibili: il corpus non li distingue, quindi il filtro non deve. Restano DISTINTI DM /
# DPCM / DPR / RD → la guardia originale (un 'DM 143/2013' inventato NON aggancia la
# 'L. 143/2013' omonima) è preservata.
_TIPO_ALIASES = {
    "decreto_ministeriale": {"decreto_ministeriale", "dm"},
    "decreto_legislativo": {"decreto_legislativo", "dlgs", "d_lgs", "legge", "l"},
    "decreto_legge": {"decreto_legge", "dl"},
    "decreto_presidente_repubblica": {"decreto_presidente_repubblica", "dpr"},
    "decreto_presidente_consiglio_ministri": {"decreto_presidente_consiglio_ministri", "dpcm"},
    "legge": {"legge", "l", "decreto_legislativo", "dlgs", "d_lgs"},
    "regio_decreto": {"regio_decreto", "rd"},
}
# label testuale (es. 'D.Lgs', 'DM') normalizzata → tipo canonico.
_LABEL_TO_TIPO = {
    "dm": "decreto_ministeriale", "dlgs": "decreto_legislativo",
    "dl": "decreto_legge", "dpr": "decreto_presidente_repubblica",
    "dpcm": "decreto_presidente_consiglio_ministri",
    "l": "legge", "legge": "legge", "rd": "regio_decreto",
}
# Riferimento normativo nel testo (mirror della regex C2 del CAGE in grounding.py, che
# accetta anni a 2-4 cifre). L'anno può essere a 2 cifre ('D.Lgs 81/08', 'L. 300/70'):
# va espanso a 4 cifre per matchare i filename del corpus (_FN_RE = \d{4}).
_NORM_REF_RE = re.compile(
    r"\b(d\.?\s?m\.?|d\.?\s?l\.?|d\.?\s?p\.?r\.?|d\.?\s?lgs\.?|legge|l\.)\s*(?:n\.?\s*)?(\d{1,4})\s*[/\-]\s*(\d{2,4})"
    # articolo DOPO gli estremi ("L. 300/1970, art. 4", "D.Lgs 231/2001, art. 25-septies"):
    # senza catturarlo, l'enrich agganciava il PRIMO chunk della legge nel corpus (es.
    # art. 1 dello Statuto al posto dell'art. 4 sulla videosorveglianza) → citazione
    # verbatim con articolo SBAGLIATO in un parere legale.
    r"(?:\s*,?\s*artt?\.?\s*(\d+(?:\s*-\s*[a-z]+)?))?",
    re.I)

# articolo PRIMA degli estremi ("art. 4 della L. 300/1970", "ex art. 13 del D.Lgs 81/2008"):
# cercato in una finestra corta subito a monte del riferimento.
_ART_BEFORE_RE = re.compile(r"artt?\.?\s*(\d+(?:\s*-\s*[a-z]+)?)\s*(?:,\s*)?(?:del(?:la|lo)?\s+|di\s+)?$", re.I)


def _norm_art(a) -> str:
    """Articolo normalizzato per confronto loose: '25-septies' ≡ '25 - septies' ≡ '25septies'."""
    return re.sub(r"[^0-9a-z]", "", str(a or "").lower())


def _norm_label(label: str) -> str:
    return re.sub(r"[.\s]", "", label or "").lower()


def _expand_year(y: int) -> int:
    """Anno a 2 cifre → 4 cifre, pivot deterministico 30: 00-30 → 2000-2030, 31-99 →
    1931-1999. Copre i casi reali (81/08→2008 TUS, 300/70→1970 Statuto, 231/01→2001,
    206/05→2005) senza datetime (deterministico). Gli anni già a 4 cifre passano intatti."""
    if y >= 100:
        return y
    return 2000 + y if y <= 30 else 1900 + y


def extract_norm_refs(text: str) -> list[dict]:
    """Estrae i riferimenti di legge da un testo (es. 'DPR 380/2001', 'D.Lgs 81/08',
    'art. 4 della L. 300/1970'). Anni a 2 cifre espansi a 4 (pivot 30) per matchare il
    corpus. Cattura anche l'ARTICOLO (dopo o prima degli estremi) quando indicato, così
    l'enrich cita il chunk giusto. Ritorna [{tipo, numero, anno, articolo?, label}]."""
    text = text or ""
    refs, seen = [], set()
    for m in _NORM_REF_RE.finditer(text):
        tipo = _LABEL_TO_TIPO.get(_norm_label(m.group(1)))
        numero, anno = m.group(2), _expand_year(int(m.group(3)))
        articolo = m.group(4)
        if not articolo:
            b = _ART_BEFORE_RE.search(text[max(0, m.start() - 40):m.start()])
            if b:
                articolo = b.group(1)
        articolo = re.sub(r"\s+", "", articolo) if articolo else None
        key = (tipo, numero, anno, _norm_art(articolo))
        if tipo and key not in seen:
            seen.add(key)
            refs.append({"tipo": tipo, "numero": numero, "anno": anno,
                         "articolo": articolo, "label": m.group(0).strip()})
    return refs


def _query_estremi(db: Path, anno: int, num: str, valid_tipi, articolo, limit: int) -> list[dict]:
    """Interroga UN db (principale o supplemento) per estremi. Stessa logica di filtro."""
    try:
        con = sqlite3.connect(f"file:{db}?immutable=1", uri=True, timeout=20)
    except sqlite3.Error:
        return []
    try:
        con.execute("PRAGMA busy_timeout=20000")
        rows = con.execute(
            "SELECT file, testo FROM chunks_fts WHERE chunks_fts MATCH ? LIMIT ?",
            (f"file:{int(anno)} AND file:{num}", max(1, int(limit)) * 8),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()

    out: list[dict] = []
    for file, testo in rows:
        e = _estremi(file)
        if e.get("anno") != int(anno) or str(e.get("numero")) != num:
            continue                                   # token-match casuale: scarta
        if valid_tipi is not None and e.get("tipo") not in valid_tipi:
            continue                                   # tipo diverso (es. legge vs DM)
        if articolo is not None and _norm_art(e.get("articolo")) != _norm_art(articolo):
            continue                                   # articolo diverso (loose: '25-septies'≡'25septies')
        out.append({**e, "citazione": citazione(e), "testo": testo})
        if len(out) >= limit:
            break
    return out


def find_by_estremi(anno: int, numero: str, tipo: Optional[str] = None,
                    articolo: Optional[str] = None, limit: int = 3) -> list[dict]:
    """Cerca una norma per estremi (anno, numero) — per VERIFICARE un riferimento citato
    nel deliverable. Filtra per `tipo` (alias-aware: 'decreto_ministeriale' ≡ 'dm') così
    una norma confabulata ('DM 143/2013' quando esiste solo L. 143/2013) NON viene
    verificata. Interroga il corpus PRINCIPALE poi, se non basta, il SUPPLEMENTO bundlato
    (norme aggiunte non ancora nel volume). Ritorna [] se nessuno dei due ha la norma."""
    if not anno or not numero:
        return []
    num = re.sub(r"\D", "", str(numero))
    if not num:
        return []
    valid_tipi = _TIPO_ALIASES.get(tipo) if tipo else None
    out: list[dict] = []
    for db in (_db_path(), _supp_path()):
        if db is None:
            continue
        out.extend(_query_estremi(db, anno, num, valid_tipi, articolo, limit - len(out)))
        if len(out) >= limit:
            break
    return out
